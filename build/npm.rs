use flate2::read::GzDecoder;
use semver::{Version, VersionReq};
use serde::Deserialize;
use std::{
    collections::{BTreeMap, HashSet},
    io::Cursor,
    path::Path,
};
use tar::Archive;

#[derive(Clone, Debug, Deserialize)]
struct RegistryMeta {
    versions: BTreeMap<String, VersionMeta>,
}

#[derive(Clone, Debug, Deserialize)]
struct VersionMeta {
    dist: Dist,
    #[serde(default)]
    dependencies: BTreeMap<String, String>,
}

#[derive(Clone, Debug, Deserialize)]
struct Dist {
    tarball: String,
}

async fn download_and_extract_tarball(
    client: &reqwest::Client, tarball_url: &str, dest_dir: &Path,
) -> Result<(), Box<dyn std::error::Error>> {
    let bytes = client.get(tarball_url).send().await?.bytes().await?;
    let cursor = Cursor::new(bytes);
    let gz = GzDecoder::new(cursor);
    let mut ar = Archive::new(gz);

    std::fs::create_dir_all(dest_dir)?;
    for entry in ar.entries()? {
        let mut e = entry?;
        let path = e.path()?;
        let rel = path.strip_prefix("package").unwrap_or(&path);
        let out_path = dest_dir.join(rel);

        if let Some(parent) = out_path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        e.unpack(out_path)?;
    }
    Ok(())
}

async fn fetch_registry_meta(
    client: &reqwest::Client, name: &str, spec: &str,
) -> Result<(String, VersionMeta), Box<dyn std::error::Error>> {
    let url = format!("https://registry.npmjs.org/{name}");
    let doc: RegistryMeta = client.get(&url).send().await?.json().await?;

    if let Some(vmeta) = doc.versions.get(spec) {
        return Ok((spec.to_string(), vmeta.clone()));
    }

    let req = VersionReq::parse(spec)?;
    let mut best: Option<(Version, String)> = None;
    for vstr in doc.versions.keys() {
        if let Ok(v) = Version::parse(vstr) {
            if req.matches(&v) {
                if let Some((best_v, _)) = &best {
                    if &v > best_v {
                        best = Some((v, vstr.clone()));
                    }
                } else {
                    best = Some((v, vstr.clone()));
                }
            }
        }
    }

    let (_, chosen_str) = best.ok_or_else(|| format!("No version of {name} satisfies range {spec}"))?;
    let chosen_meta = doc.versions.get(&chosen_str).unwrap().clone();
    Ok((chosen_str, chosen_meta))
}

pub async fn install_all_packages(
    client: &reqwest::Client, node_modules: &Path, roots: impl IntoIterator<Item = (String, String)>,
) -> Result<(), Box<dyn std::error::Error>> {
    use futures::{StreamExt, stream::FuturesUnordered};
    use std::{path::PathBuf, sync::Arc};
    use tokio::sync::{Mutex, Semaphore};

    std::fs::create_dir_all(node_modules)?;

    let client = Arc::new(client.clone());
    let node_modules = Arc::new(PathBuf::from(node_modules));
    let installed = Arc::new(Mutex::new(HashSet::<String>::new()));

    let max_concurrency = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(8)
        .max(4);

    let sem = Arc::new(Semaphore::new(max_concurrency));

    async fn process_one(
        client: Arc<reqwest::Client>, node_modules: Arc<PathBuf>, installed: Arc<Mutex<HashSet<String>>>,
        sem: Arc<Semaphore>, name: String, spec: String,
    ) -> Result<Vec<(String, String)>, Box<dyn std::error::Error>> {
        let _permit = sem.clone().acquire_owned().await?;

        let (version, vmeta) = fetch_registry_meta(&client, &name, &spec).await?;
        let key = format!("{name}@{version}");

        {
            let mut set = installed.lock().await;
            if !set.insert(key.clone()) {
                return Ok(vec![]);
            }
        }

        let dest = node_modules.join(&name);
        if dest.exists() {
            println!("{key} already exists, skipping download");
        } else {
            println!("Installing {key}");
            download_and_extract_tarball(&client, &vmeta.dist.tarball, &dest).await?;
        }

        Ok(vmeta.dependencies.into_iter().collect())
    }

    let mut tasks = FuturesUnordered::new();

    for (name, spec) in roots {
        tasks.push(process_one(
            client.clone(),
            node_modules.clone(),
            installed.clone(),
            sem.clone(),
            name,
            spec,
        ));
    }

    while let Some(res) = tasks.next().await {
        match res {
            Ok(deps) => {
                for (dep_name, dep_spec) in deps {
                    tasks.push(process_one(
                        client.clone(),
                        node_modules.clone(),
                        installed.clone(),
                        sem.clone(),
                        dep_name,
                        dep_spec,
                    ));
                }
            }
            Err(err) => eprintln!("Install task failed: {err}"),
        }
    }

    Ok(())
}

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::path::PathBuf;
use tokio::{fs, io::AsyncWriteExt};
use url::Url;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct CacheEntry {
    pub original_url: String,
    pub final_url: Option<String>,
}

fn url_to_filename(url: &Url) -> String {
    let mut hasher = Sha256::new();
    hasher.update(url.path().as_bytes());
    if let Some(q) = url.query() {
        hasher.update(b"?");
        hasher.update(q.as_bytes());
    }
    hex::encode(hasher.finalize())
}

fn metadata_path_for_domain(domain: &str) -> PathBuf {
    let p = PathBuf::from("./cache");
    p.join(domain).join("_metadata")
}

pub fn path_for(url: &Url) -> PathBuf {
    let filename = url_to_filename(url);
    let mut dir = PathBuf::from("./cache");

    dir.push(url.host_str().unwrap_or("unknown-host"));
    dir.join(filename)
}

async fn read_domain_metadata(domain: &str) -> std::io::Result<BTreeMap<String, CacheEntry>> {
    let metadata_path = metadata_path_for_domain(domain);
    match fs::read(&metadata_path).await {
        Ok(bytes) => postcard::from_bytes(&bytes).map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e)),
        Err(_) => Ok(BTreeMap::new()),
    }
}

async fn write_domain_metadata(domain: &str, metadata: &BTreeMap<String, CacheEntry>) -> std::io::Result<()> {
    let metadata_path = metadata_path_for_domain(domain);
    if let Some(parent) = metadata_path.parent() {
        fs::create_dir_all(parent).await?;
    }

    let bytes = postcard::to_allocvec(metadata).map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e))?;
    write_atomic(&metadata_path, &bytes).await
}

pub async fn cache_url(original_url: &Url, final_url: Option<&Url>, data: &[u8]) -> std::io::Result<PathBuf> {
    let cache_path = path_for(original_url);
    write_atomic(&cache_path, data).await?;

    if let Some(final_url) = final_url {
        if final_url != original_url {
            let domain = original_url.host_str().unwrap_or("unknown-host");
            let mut metadata = read_domain_metadata(domain).await?;

            let entry = CacheEntry {
                original_url: original_url.to_string(),
                final_url: Some(final_url.to_string()),
            };

            metadata.insert(original_url.to_string(), entry);
            write_domain_metadata(domain, &metadata).await?;
        }
    }

    Ok(cache_path)
}

pub async fn get_final_url(original_url: &Url) -> std::io::Result<Url> {
    let domain = original_url.host_str().unwrap_or("unknown-host");
    let metadata = read_domain_metadata(domain).await?;

    if let Some(entry) = metadata.get(&original_url.to_string()) {
        if let Some(final_url_str) = &entry.final_url {
            return Ok(Url::parse(final_url_str).unwrap_or_else(|_| original_url.clone()));
        }
    }

    Ok(original_url.clone())
}

pub async fn write_atomic(path: &PathBuf, bytes: &[u8]) -> std::io::Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).await?;
    }

    let tmp = path.with_extension("tmp");
    {
        let mut f = fs::File::create(&tmp).await?;
        f.write_all(bytes).await?;
        f.flush().await?;
    }

    Ok(fs::rename(&tmp, &path).await?)
}

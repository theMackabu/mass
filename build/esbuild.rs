use esbuild_client::{EsbuildServiceOptions, Format};
use flate2::read::GzDecoder;
use reqwest::Client;
use serde::Deserialize;
use std::error::Error;
use std::fs::File;
use std::io::Cursor;
use std::{collections::BTreeMap, fs};
use tar::Archive;

#[derive(Debug, Deserialize)]
struct Config {
    dependencies: BTreeMap<String, String>,
}

const ESBUILD_URL: &'static str = "https://registry.npmjs.org/esbuild/latest";
const DEPENDENCIES: &'static str = include_str!("../mass/server/pkg.toml");

pub async fn bundle_server() -> Result<(), Box<dyn Error>> {
    let o = std::path::PathBuf::from(std::env::var_os("OUT_DIR").unwrap());
    let m = std::path::PathBuf::from(std::env::var_os("CARGO_MANIFEST_DIR").unwrap());

    let resp = reqwest::get(ESBUILD_URL).await?;
    let body: serde_json::Value = resp.json().await?;

    let version = body["version"].as_str().unwrap();
    let esbuild_path = o.join(if cfg!(windows) { "esbuild.exe" } else { "esbuild" });

    if !esbuild_path.exists() {
        let platform = match (std::env::consts::OS, std::env::consts::ARCH) {
            ("macos", "x86_64") => "darwin-x64",
            ("macos", "aarch64") => "darwin-arm64",
            ("linux", "x86_64") => "linux-x64",
            ("linux", "aarch64") => "linux-arm64",
            ("linux", "arm") => "linux-arm",
            ("windows", "x86_64") => "win32-x64",
            ("windows", "aarch64") => "win32-arm64",
            ("windows", "x86") => "win32-ia32",
            other => {
                eprintln!("Unsupported platform: {:?}", other);
                std::process::exit(1);
            }
        };

        let tgz_url = format!(
            "https://registry.npmjs.org/@esbuild/{}/-/{}-{}.tgz",
            platform, platform, version
        );
        println!("Downloading {}", tgz_url);

        let client = Client::new();
        let bytes = client.get(&tgz_url).send().await?.bytes().await?;
        let cursor = Cursor::new(bytes);

        let tar = GzDecoder::new(cursor);
        let mut archive = Archive::new(tar);

        for entry in archive.entries()? {
            let mut entry = entry?;
            let path = entry.path()?;

            if path.to_string_lossy().ends_with("bin/esbuild") || path.to_string_lossy().ends_with("bin/esbuild.exe") {
                let mut file = File::create(&esbuild_path)?;
                std::io::copy(&mut entry, &mut file)?;

                #[cfg(unix)]
                {
                    use std::os::unix::fs::PermissionsExt;
                    let mut perms = file.metadata()?.permissions();
                    perms.set_mode(0o755);
                    std::fs::set_permissions(&esbuild_path, perms)?;
                }
            }
        }
    }

    let dist = m.join("mass/runtime/snapshot");
    let node_modules = m.join("mass/server/node_modules");

    let cfg: Config = toml::from_str(DEPENDENCIES)?;
    let roots = cfg.dependencies.into_iter().map(|(name, spec)| (name, spec));

    crate::npm::install_all_packages(&reqwest::Client::new(), &node_modules, roots).await?;

    let esbuild =
        esbuild_client::EsbuildService::new(esbuild_path, version, None, EsbuildServiceOptions::default()).await?;
    let flags = esbuild_client::EsbuildFlagsBuilder::default()
        .bundle(true)
        .minify(true)
        .format(Format::Esm)
        .build_with_defaults();

    let response = esbuild
        .client()
        .send_build_request(esbuild_client::protocol::BuildRequest {
            flags,
            entries: vec![(
                dist.join("server.min.js").to_string_lossy().into(),
                "mass/server/index.ts".into(),
            )],
            ..Default::default()
        })
        .await?;

    let output_files = response.unwrap().output_files.unwrap();
    let output_content = String::from_utf8(output_files[0].contents.clone())?;

    fs::create_dir_all(&dist)?;
    fs::write(dist.join("server.min.js"), output_content)?;

    Ok(())
}

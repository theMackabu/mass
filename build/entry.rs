mod esbuild;
mod npm;

use std::{env, error::Error};
include!("../mass/modules.rs");

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    if Ok("release".to_owned()) == env::var("PROFILE") {
        let o = std::path::PathBuf::from(std::env::var_os("CARGO_MANIFEST_DIR").unwrap());
        let snapshot_path = o.join("mass/runtime/snapshot");

        esbuild::bundle_server().await?;
        create_snapshot(snapshot_path.join("RUNTIME.bin"));

        println!("cargo:rerun-if-changed=../mass/worker");
        println!("cargo:rerun-if-changed=../mass/server");
        println!("cargo:rerun-if-changed=../mass/runtime");
        println!("cargo:rerun-if-changed=../mass/modules.rs");
    }

    Ok(())
}

fn create_snapshot(snapshot_path: std::path::PathBuf) {
    use deno_runtime::ops::bootstrap::SnapshotOptions;

    let snapshot_options = SnapshotOptions {
        ts_version: "5.9.2".to_string(),
        v8_version: deno_runtime::deno_core::v8::VERSION_STRING,
        target: std::env::var("TARGET").unwrap(),
    };

    deno_runtime::snapshot::create_runtime_snapshot(snapshot_path, snapshot_options, init_extension());
}

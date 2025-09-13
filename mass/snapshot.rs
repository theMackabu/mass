pub static RUNTIME: Option<&[u8]> = Some(include_bytes!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/mass/runtime/snapshot/RUNTIME.bin"
)));

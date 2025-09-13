mod loader;
mod modules;
mod snapshot;
mod stardust;

#[tokio::main]
async fn main() { let _ = stardust::start_runtime().await; }

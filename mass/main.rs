mod loader;
mod modules;
mod snapshot;
mod stardust;

#[tokio::main]
async fn main() {
    if let Err(error) = stardust::start_runtime().await {
        eprintln!("{error:?}");
    };
}

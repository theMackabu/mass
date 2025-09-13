use crate::loader;
use crate::modules;
use crate::snapshot;

use std::rc::Rc;
use std::sync::Arc;
use tokio::time::{Duration, timeout};

use deno_core::FastStaticString;
use deno_core::ModuleSpecifier;
use deno_core::PollEventLoopOptions;
use deno_core::error::CoreError;
use deno_resolver::npm::DenoInNpmPackageChecker;
use deno_resolver::npm::NpmResolver;
use deno_runtime::deno_permissions::PermissionsContainer;
use deno_runtime::permissions::RuntimePermissionDescriptorParser;
use deno_runtime::worker::MainWorker;
use deno_runtime::worker::WorkerOptions;
use deno_runtime::worker::WorkerServiceOptions;

const WORKER_CODE: FastStaticString = {
    const STR: deno_core::v8::OneByteConst =
        FastStaticString::create_external_onebyte_const(include_bytes!("worker/index.js"));
    FastStaticString::new(&STR)
};

async fn with_timeout<F, Fut, T>(f: F) -> Result<T, tokio::time::error::Elapsed>
where
    F: FnOnce() -> Fut,
    Fut: Future<Output = T>,
{
    timeout(Duration::from_millis(500), f()).await
}

pub async fn start_runtime() -> Result<(), CoreError> {
    let main_module = ModuleSpecifier::parse("file://server.dist.js").unwrap();
    let permission_desc_parser = Arc::new(RuntimePermissionDescriptorParser::new(sys_traits::impls::RealSys));

    let mut worker = MainWorker::bootstrap_from_options(
        &main_module,
        WorkerServiceOptions::<
            DenoInNpmPackageChecker,
            NpmResolver<sys_traits::impls::RealSys>,
            sys_traits::impls::RealSys,
        > {
            fs: Arc::new(deno_fs::RealFs),
            deno_rt_native_addon_loader: None,
            module_loader: Rc::new(loader::ExtendedModuleLoader),
            permissions: PermissionsContainer::allow_all(permission_desc_parser),
            blob_store: Default::default(),
            broadcast_channel: Default::default(),
            feature_checker: Default::default(),
            node_services: Default::default(),
            npm_process_state_provider: Default::default(),
            root_cert_store_provider: Default::default(),
            fetch_dns_resolver: Default::default(),
            shared_array_buffer_store: Default::default(),
            compiled_wasm_module_store: Default::default(),
            v8_code_cache: Default::default(),
        },
        WorkerOptions {
            extensions: modules::init_extension(),
            startup_snapshot: snapshot::RUNTIME,
            ..Default::default()
        },
    );

    worker
        .js_runtime
        .execute_script("_init", include_str!("worker/check.js"))
        .map_err(CoreError::from)?;

    let id = worker
        .js_runtime
        .load_main_es_module_from_code(&main_module, WORKER_CODE)
        .await?;

    if let Err(_) = with_timeout(|| worker.js_runtime.run_event_loop(PollEventLoopOptions::default())).await {
        eprintln!("JavaScript event loop timed out after 500ms");
    }

    worker.evaluate_module(id).await?;
    worker.run_event_loop(false).await?;

    Ok(())
}

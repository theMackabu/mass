mod cache;

use data_url::DataUrl;
use deno_error::JsErrorBox;
use tokio::fs;

use deno_core::{
    ModuleLoadResponse, ModuleLoader, ModuleSource, ModuleSourceCode, ModuleSpecifier, ModuleType, RequestedModuleType,
    ResolutionKind, futures::FutureExt,
};

#[derive(Debug, thiserror::Error, deno_error::JsError)]
#[class(inherit)]
#[error("Failed to load {specifier}")]
pub struct LoadFailedError {
    specifier: ModuleSpecifier,
    #[source]
    #[inherit]
    source: std::io::Error,
}

pub struct ExtendedModuleLoader;

impl ModuleLoader for ExtendedModuleLoader {
    fn resolve(&self, specifier: &str, referrer: &str, _kind: ResolutionKind) -> Result<ModuleSpecifier, JsErrorBox> {
        deno_core::resolve_import(specifier, referrer).map_err(JsErrorBox::from_err)
    }

    fn load(
        &self, module_specifier: &ModuleSpecifier, _maybe_referrer: Option<&ModuleSpecifier>, _is_dynamic: bool,
        requested_module_type: RequestedModuleType,
    ) -> ModuleLoadResponse {
        let module_specifier = module_specifier.clone();

        let future = async move {
            let mut redirect_module_url = None;

            let bytes = match module_specifier.scheme() {
                "http" | "https" => {
                    let cache_path = cache::path_for(&module_specifier);

                    if cache_path.exists() {
                        println!("loading {module_specifier}");

                        if let Ok(final_url) = cache::get_final_url(&module_specifier).await {
                            if final_url != module_specifier {
                                redirect_module_url = Some(final_url);
                            }
                        }

                        fs::read(&cache_path).await.map_err(|e| JsErrorBox::new("CacheError", e.to_string()))?
                    } else {
                        println!("fetching {module_specifier}");

                        let res = reqwest::get(module_specifier.clone()).await.map_err(|e| JsErrorBox::new("RequestError", e.to_string()))?;
                        let res = res.error_for_status().map_err(|e| JsErrorBox::new("HttpError", e.to_string()))?;

                        let final_url = res.url().clone();
                        let redirect_url = if final_url != module_specifier { Some(final_url.clone()) } else { None };
                        let body = res.bytes().await.map_err(|e| JsErrorBox::new("ResponseError", e.to_string()))?.to_vec();

                        if let Err(err) = cache::cache_url(&module_specifier, redirect_url.as_ref(), &body).await {
                            eprintln!("cache write failed for {}: {err}", module_specifier);
                        }

                        if let Some(redirect) = redirect_url {
                            redirect_module_url = Some(redirect);
                        }

                        body
                    }
                }

                "data" => {
                    let url = DataUrl::process(module_specifier.as_str()).map_err(|_| JsErrorBox::new("DataUrlError", "Not a valid data URL."))?;
                    let (bytes, _) = url.decode_to_vec().map_err(|_| JsErrorBox::new("DataUrlError", "Failed to decode data URL."))?;

                    bytes
                }

                "file" => {
                    let path = module_specifier
                        .to_file_path()
                        .map_err(|_| JsErrorBox::generic(format!("Provided module specifier \"{module_specifier}\" is not a file URL.")))?;

                    std::fs::read(path).map_err(|source| {
                        JsErrorBox::from_err(LoadFailedError {
                            specifier: module_specifier.clone(),
                            source,
                        })
                    })?
                }

                schema => {
                    return Err(JsErrorBox::new("SchemaError", format!("Invalid schema {}", schema)));
                }
            };

            let module_type = match module_specifier.scheme() {
                "file" => {
                    let path = module_specifier.to_file_path().unwrap();
                    if let Some(extension) = path.extension() {
                        let ext = extension.to_string_lossy().to_lowercase();
                        if ext == "json" {
                            ModuleType::Json
                        } else if ext == "wasm" {
                            ModuleType::Wasm
                        } else {
                            match &requested_module_type {
                                RequestedModuleType::Other(ty) => ModuleType::Other(ty.clone()),
                                RequestedModuleType::Text => ModuleType::Text,
                                RequestedModuleType::Bytes => ModuleType::Bytes,
                                _ => ModuleType::JavaScript,
                            }
                        }
                    } else {
                        ModuleType::JavaScript
                    }
                }
                _ => match requested_module_type {
                    RequestedModuleType::None => ModuleType::JavaScript,
                    RequestedModuleType::Json => ModuleType::Json,
                    RequestedModuleType::Text => ModuleType::JavaScript,
                    RequestedModuleType::Bytes => ModuleType::JavaScript,
                    RequestedModuleType::Other(_) => {
                        return Err(JsErrorBox::new("ModuleTypeError", "Import types other than JSON are not supported"));
                    }
                },
            };

            if module_specifier.scheme() == "file" && module_type == ModuleType::Json && requested_module_type != RequestedModuleType::Json {
                return Err(JsErrorBox::generic(
                    "Attempted to load JSON module without specifying \"type\": \"json\" attribute in the import statement.",
                ));
            }

            if let Some(redirect_module_url) = redirect_module_url {
                Ok(ModuleSource::new_with_redirect(
                    module_type,
                    ModuleSourceCode::Bytes(bytes.into_boxed_slice().into()),
                    &module_specifier,
                    &redirect_module_url,
                    None,
                ))
            } else {
                Ok(ModuleSource::new(module_type, ModuleSourceCode::Bytes(bytes.into_boxed_slice().into()), &module_specifier, None))
            }
        }
        .boxed_local();

        ModuleLoadResponse::Async(future)
    }
}

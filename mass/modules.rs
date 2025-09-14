use deno_core::{Extension, extension, op2};
use std::fs;
use std::path::Path;
use std::collections::HashMap;
use flate2::read::GzDecoder;
use tar::Archive;

#[op2(fast)]
fn op_pid() -> u32 { std::process::id() }

#[op2]
#[string]
fn op_extract_tar_gz(#[string] tar_gz_path: String, #[string] extract_to: String) -> Result<String, deno_core::error::AnyError> {
    let tar_file = fs::File::open(&tar_gz_path)?;
    let tar = GzDecoder::new(tar_file);
    let mut archive = Archive::new(tar);
    
    // Extract to specified directory
    archive.unpack(&extract_to)?;
    
    Ok(format!("Extracted {} to {}", tar_gz_path, extract_to))
}

#[op2]
#[serde]
fn op_analyze_repository(#[string] repo_path: String) -> Result<HashMap<String, serde_json::Value>, deno_core::error::AnyError> {
    let mut analysis = HashMap::new();
    
    // Analyze file structure
    let file_count = count_files_recursive(&repo_path)?;
    analysis.insert("file_count".to_string(), serde_json::Value::Number(file_count.into()));
    
    // Detect languages
    let languages = detect_languages(&repo_path)?;
    analysis.insert("languages".to_string(), serde_json::Value::Array(
        languages.into_iter().map(|lang| serde_json::Value::String(lang)).collect()
    ));
    
    // Find configuration files
    let config_files = find_config_files(&repo_path)?;
    analysis.insert("config_files".to_string(), serde_json::Value::Array(
        config_files.into_iter().map(|file| serde_json::Value::String(file)).collect()
    ));
    
    // Calculate repository size
    let repo_size = calculate_directory_size(&repo_path)?;
    analysis.insert("size_bytes".to_string(), serde_json::Value::Number(repo_size.into()));
    
    Ok(analysis)
}

#[op2]
#[string]
fn op_get_important_files_by_pattern(#[string] repo_path: String, #[bigint] max_files: u32) -> Result<String, deno_core::error::AnyError> {
    let mut important_files = Vec::new();

    // Priority patterns for important files (ordered by importance)
    let important_patterns = vec![
        // Config files (highest priority)
        "package.json", "Cargo.toml", "pyproject.toml", "requirements.txt",
        "go.mod", "pom.xml", "build.gradle", "composer.json",
        // Docker files
        "Dockerfile", "docker-compose.yml", ".env.example",
        // Documentation
        "README.md", "README.txt",
        // Entry points (glob patterns)
        "main.*", "index.*", "app.*", "server.*"
    ];

    // Scan directory for matching files
    for entry in fs::read_dir(&repo_path)? {
        let entry = entry?;
        let path = entry.path();

        if let Some(file_name) = path.file_name().and_then(|n| n.to_str()) {
            for pattern in &important_patterns {
                let matches = if pattern.contains("*") {
                    // Handle glob patterns like "main.*"
                    let prefix = pattern.replace("*", "");
                    file_name.starts_with(&prefix)
                } else {
                    // Exact match
                    file_name == *pattern
                };

                if matches {
                    // Read file content if it's text and not too large
                    if let Ok(metadata) = entry.metadata() {
                        if metadata.len() > 100_000 {  // Skip files > 100KB
                            important_files.push(format!("{}:[File too large: {} bytes]", file_name, metadata.len()));
                        } else if let Ok(content) = fs::read_to_string(&path) {
                            // Truncate very long content
                            let truncated_content = if content.len() > 5000 {
                                format!("{}...\n[Content truncated - {} total chars]", &content[..5000], content.len())
                            } else {
                                content
                            };
                            important_files.push(format!("{}:{}", file_name, truncated_content));
                        }
                    }

                    if important_files.len() >= max_files as usize {
                        break;
                    }
                }
            }
            if important_files.len() >= max_files as usize {
                break;
            }
        }
    }

    Ok(important_files.join("\n---FILE_SEPARATOR---\n"))
}

#[op2]
#[string]
fn op_get_important_files(#[string] repo_path: String, #[serde] file_paths: Vec<String>) -> Result<String, deno_core::error::AnyError> {
    let mut important_files = Vec::new();
    let repo_path = Path::new(&repo_path);

    for file_path in file_paths {
        let full_path = repo_path.join(&file_path);

        if !full_path.exists() {
            continue;
        }

        if full_path.is_file() {
            if let Ok(metadata) = fs::metadata(&full_path) {
                // Skip very large files (>500KB for LLM processing)
                if metadata.len() > 500_000 {
                    important_files.push(format!("{}:[File too large: {} bytes]", file_path, metadata.len()));
                    continue;
                }

                // Try to read file content
                match fs::read_to_string(&full_path) {
                    Ok(content) => {
                        // For very long content, we'll handle truncation later in the token counting logic
                        important_files.push(format!("{}:{}", file_path, content));
                    },
                    Err(_) => {
                        // If we can't read as text, it might be binary
                        important_files.push(format!("{}:[Binary file - {} bytes]", file_path, metadata.len()));
                    }
                }
            }
        }
    }

    Ok(important_files.join("\n---FILE_SEPARATOR---\n"))
}

#[op2]
#[string]
fn op_cleanup_temp_directory(#[string] temp_dir: String) -> Result<String, deno_core::error::AnyError> {
    if Path::new(&temp_dir).exists() {
        fs::remove_dir_all(&temp_dir)?;
        Ok(format!("Cleaned up temporary directory: {}", temp_dir))
    } else {
        Ok("Directory does not exist".to_string())
    }
}

// Helper functions
fn count_files_recursive(dir_path: &str) -> Result<u64, std::io::Error> {
    let mut count = 0;
    
    fn visit_dir(dir: &Path, count: &mut u64) -> Result<(), std::io::Error> {
        if dir.is_dir() {
            for entry in fs::read_dir(dir)? {
                let entry = entry?;
                let path = entry.path();
                
                // Skip common directories to ignore
                if let Some(dir_name) = path.file_name().and_then(|n| n.to_str()) {
                    if matches!(dir_name, "node_modules" | "target" | ".git" | "__pycache__" | "dist" | "build") {
                        continue;
                    }
                }
                
                if path.is_dir() {
                    visit_dir(&path, count)?;
                } else {
                    *count += 1;
                }
            }
        }
        Ok(())
    }
    
    visit_dir(Path::new(dir_path), &mut count)?;
    Ok(count)
}

fn detect_languages(repo_path: &str) -> Result<Vec<String>, std::io::Error> {
    let mut languages = std::collections::HashSet::new();
    
    fn scan_directory(dir: &Path, languages: &mut std::collections::HashSet<String>) -> Result<(), std::io::Error> {
        for entry in fs::read_dir(dir)? {
            let entry = entry?;
            let path = entry.path();
            
            if path.is_dir() {
                if let Some(dir_name) = path.file_name().and_then(|n| n.to_str()) {
                    if !matches!(dir_name, "node_modules" | "target" | ".git" | "__pycache__") {
                        scan_directory(&path, languages)?;
                    }
                }
            } else if let Some(extension) = path.extension().and_then(|ext| ext.to_str()) {
                match extension {
                    "js" | "mjs" | "jsx" => { languages.insert("JavaScript".to_string()); }
                    "ts" | "tsx" => { languages.insert("TypeScript".to_string()); }
                    "py" => { languages.insert("Python".to_string()); }
                    "rs" => { languages.insert("Rust".to_string()); }
                    "go" => { languages.insert("Go".to_string()); }
                    "java" => { languages.insert("Java".to_string()); }
                    "cpp" | "cc" | "cxx" => { languages.insert("C++".to_string()); }
                    "c" => { languages.insert("C".to_string()); }
                    "cs" => { languages.insert("C#".to_string()); }
                    "php" => { languages.insert("PHP".to_string()); }
                    "rb" => { languages.insert("Ruby".to_string()); }
                    _ => {}
                }
            }
        }
        Ok(())
    }
    
    scan_directory(Path::new(repo_path), &mut languages)?;
    Ok(languages.into_iter().collect())
}

fn find_config_files(repo_path: &str) -> Result<Vec<String>, std::io::Error> {
    let mut config_files = Vec::new();
    let config_patterns = vec![
        "package.json", "Cargo.toml", "pyproject.toml", "requirements.txt",
        "go.mod", "pom.xml", "build.gradle", "Dockerfile", "docker-compose.yml"
    ];
    
    for entry in fs::read_dir(repo_path)? {
        let entry = entry?;
        let path = entry.path();
        
        if let Some(file_name) = path.file_name().and_then(|n| n.to_str()) {
            if config_patterns.contains(&file_name) {
                config_files.push(file_name.to_string());
            }
        }
    }
    
    Ok(config_files)
}

fn calculate_directory_size(dir_path: &str) -> Result<u64, std::io::Error> {
    let mut total_size = 0;
    
    fn visit_dir(dir: &Path, total: &mut u64) -> Result<(), std::io::Error> {
        for entry in fs::read_dir(dir)? {
            let entry = entry?;
            let path = entry.path();
            
            if path.is_dir() {
                if let Some(dir_name) = path.file_name().and_then(|n| n.to_str()) {
                    if !matches!(dir_name, "node_modules" | "target" | ".git" | "__pycache__") {
                        visit_dir(&path, total)?;
                    }
                }
            } else if let Ok(metadata) = entry.metadata() {
                *total += metadata.len();
            }
        }
        Ok(())
    }
    
    visit_dir(Path::new(dir_path), &mut total_size)?;
    Ok(total_size)
}

extension!(
    stardust,
    ops = [
        op_pid,
        op_extract_tar_gz,
        op_analyze_repository,
        op_get_important_files,
        op_get_important_files_by_pattern,
        op_cleanup_temp_directory
    ],
    esm_entry_point = "ext:stardust/mass/runtime/entry.js",
    esm = ["mass/runtime/entry.js", "mass/runtime/snapshot/server.min.js"],
);

pub fn init_extension() -> Vec<Extension> { vec![stardust::init()] }

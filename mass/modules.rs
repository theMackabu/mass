use deno_core::{Extension, extension, op2};

#[op2(fast)]
fn op_pid() -> u32 { std::process::id() }

extension!(
    stardust,
    ops = [op_pid],
    esm_entry_point = "ext:stardust/mass/runtime/entry.js",
    esm = ["mass/runtime/entry.js", "mass/runtime/snapshot/server.min.js"],
);

pub fn init_extension() -> Vec<Extension> { vec![stardust::init()] }

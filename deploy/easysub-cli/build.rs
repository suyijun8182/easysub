fn main() {
    println!("cargo:rerun-if-env-changed=EASYSUB_PAYLOAD");
    if let Ok(path) = std::env::var("EASYSUB_PAYLOAD") {
        println!("cargo:rerun-if-changed={path}");
    } else {
        // 本地只验证逻辑；发布构建必须显式提供真实 payload。
        let path =
            std::path::PathBuf::from(std::env::var_os("OUT_DIR").unwrap()).join("empty.tar.gz");
        std::fs::write(&path, []).unwrap();
        println!("cargo:rustc-env=EASYSUB_PAYLOAD={}", path.display());
    }
}

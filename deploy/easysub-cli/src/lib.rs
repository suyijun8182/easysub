use anyhow::{bail, ensure, Context, Result};
use flate2::read::GzDecoder;
use sha2::{Digest, Sha256};
use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::path::{Component, Path, PathBuf};

pub const PAYLOAD: &[u8] = include_bytes!(env!("EASYSUB_PAYLOAD"));
pub const MAGIC: &[u8; 16] = b"EASYSUB_PAYLOAD1";

pub fn random_secret() -> Result<String> {
    let mut bytes = [0u8; 32];
    getrandom::fill(&mut bytes).map_err(|e| anyhow::anyhow!("无法生成安全随机数：{e}"))?;
    Ok(hex::encode(bytes))
}

pub fn safe_absolute(path: &Path) -> Result<()> {
    let text = path.to_string_lossy();
    ensure!(
        path.is_absolute() && path.parent().is_some(),
        "必须使用专用的绝对路径"
    );
    ensure!(
        text.chars()
            .all(|c| c.is_alphanumeric() || "/\\:_-.".contains(c)),
        "路径包含不支持的字符"
    );
    ensure!(
        !path
            .components()
            .any(|c| matches!(c, Component::ParentDir | Component::CurDir)),
        "路径不能包含 .. 或 ."
    );
    ensure!(
        !["/", "/var", "/var/lib", "/etc", "/opt", "/usr", "/home", "/root", "/tmp"]
            .contains(&text.as_ref()),
        "不能使用系统目录"
    );
    Ok(())
}

pub fn safe_join(root: &Path, relative: &Path) -> Result<PathBuf> {
    ensure!(!relative.is_absolute(), "归档不能包含绝对路径");
    let mut result = root.to_path_buf();
    for part in relative.components() {
        match part {
            Component::Normal(p) => result.push(p),
            Component::CurDir => (),
            _ => bail!("归档路径越界"),
        }
    }
    Ok(result)
}

fn safe_link(root: &Path, base: &Path, target: &Path) -> Result<()> {
    ensure!(!target.is_absolute(), "归档链接不能指向绝对路径");
    let mut location = base.to_path_buf();
    for part in target.components() {
        match part {
            Component::Normal(p) => location.push(p),
            Component::CurDir => (),
            Component::ParentDir => {
                ensure!(location != root, "归档链接越界");
                location.pop();
            }
            _ => bail!("归档链接越界"),
        }
    }
    ensure!(location.starts_with(root), "归档链接越界");
    Ok(())
}

pub fn unpack(payload: &[u8], destination: &Path) -> Result<String> {
    ensure!(
        !payload.is_empty(),
        "此二进制未嵌入运行时，请使用正式发布产物"
    );
    fs::create_dir_all(destination)?;
    let mut archive = tar::Archive::new(GzDecoder::new(payload));
    for entry in archive.entries()? {
        let mut entry = entry?;
        let path = entry.path()?.into_owned();
        let full = safe_join(destination, &path)?;
        let kind = entry.header().entry_type();
        ensure!(
            kind.is_file() || kind.is_dir() || kind.is_symlink() || kind.is_hard_link(),
            "归档包含不支持的设备文件"
        );
        if let Some(target) = entry.link_name()? {
            let base = if kind.is_hard_link() {
                destination
            } else {
                full.parent().context("无效链接")?
            };
            safe_link(destination, base, &target)?;
        }
        entry.set_mask(0o7000);
        ensure!(entry.unpack_in(destination)?, "归档路径越界");
    }
    let version = fs::read_to_string(destination.join("VERSION"))?
        .trim()
        .to_owned();
    ensure!(
        !version.is_empty()
            && version.len() < 64
            && version
                .chars()
                .all(|c| c.is_ascii_alphanumeric() || ".-".contains(c)),
        "版本号无效"
    );
    for file in [
        "python/bin/python3",
        "app/app/main.py",
        "frontend_dist/index.html",
    ] {
        ensure!(destination.join(file).is_file(), "运行时缺少 {file}");
    }
    Ok(version)
}

// CI 在现有内嵌 gzip 后记录偏移与校验和，升级读取新文件，无需执行它。
pub fn payload_from_binary(binary: &[u8]) -> Result<&[u8]> {
    ensure!(binary.len() >= 64, "升级文件缺少 payload 索引");
    let footer = &binary[binary.len() - 64..];
    ensure!(&footer[48..] == MAGIC, "升级文件格式无效");
    let offset = usize::try_from(u64::from_le_bytes(footer[..8].try_into()?))?;
    let length = usize::try_from(u64::from_le_bytes(footer[8..16].try_into()?))?;
    let end = offset.checked_add(length).context("payload 长度溢出")?;
    ensure!(end <= binary.len() - 64 && length > 0, "payload 越界");
    let payload = &binary[offset..end];
    ensure!(
        Sha256::digest(payload).as_slice() == &footer[16..48],
        "payload SHA256 校验失败"
    );
    Ok(payload)
}

pub fn write_env(path: &Path, data: &Path, bind: &str, port: u16) -> Result<()> {
    safe_absolute(data)?;
    bind.parse::<std::net::IpAddr>()
        .context("监听地址必须是 IP 地址")?;
    ensure!(port != 0, "端口不能为 0");
    fs::create_dir_all(path.parent().context("env 路径无效")?)?;
    let mut options = OpenOptions::new();
    options.write(true).create_new(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.mode(0o600);
    }
    let mut file = match options.open(path) {
        Ok(file) => file,
        Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => return Ok(()),
        Err(e) => return Err(e.into()),
    };
    writeln!(file, "JWT_SECRET={}\nEASYSUB_DB=sqlite\nTZ=Asia/Shanghai\nPORT={port}\nBIND={bind}\nDATA_DIR={}\nPYTHONDONTWRITEBYTECODE=1", random_secret()?, data.display())?;
    file.sync_all()?;
    Ok(())
}

pub fn read_env(path: &Path) -> Result<Vec<(String, String)>> {
    Ok(fs::read_to_string(path)?
        .lines()
        .filter(|l| !l.starts_with('#'))
        .filter_map(|line| {
            line.split_once('=')
                .map(|(k, v)| (k.to_owned(), v.to_owned()))
        })
        .collect())
}

pub fn unit(data: &Path) -> Result<String> {
    safe_absolute(data)?;
    Ok(format!("[Unit]\nDescription=EasySub 订阅管理\nAfter=network.target\n\n[Service]\nType=simple\nUser=easysub\nGroup=easysub\nWorkingDirectory=/opt/easysub/current\nEnvironmentFile=/etc/easysub/easysub.env\nEnvironment=PYTHONPATH=/opt/easysub/current/app\nEnvironment=PYTHONDONTWRITEBYTECODE=1\nExecStart=/opt/easysub/current/python/bin/python3 -m uvicorn app.main:app --host ${{BIND}} --port ${{PORT}}\nNoNewPrivileges=yes\nProtectSystem=strict\nReadWritePaths={}\nPrivateTmp=yes\nRestart=on-failure\n\n[Install]\nWantedBy=multi-user.target\n", data.display()))
}

pub trait UpgradeOps {
    fn stop(&mut self) -> Result<()>;
    fn switch(&mut self, release: &Path) -> Result<()>;
    fn start(&mut self) -> Result<()>;
    fn healthy(&mut self) -> Result<()>;
}

pub trait Host {
    fn user_exists(&mut self) -> Result<bool>;
    fn execute(&mut self, program: &str, arguments: &[&str]) -> Result<()>;
}

pub fn provision_user(host: &mut impl Host, data: &Path) -> Result<()> {
    if !host.user_exists()? {
        host.execute(
            "useradd",
            &[
                "--system",
                "--user-group",
                "--home-dir",
                "/nonexistent",
                "--shell",
                "/usr/sbin/nologin",
                "easysub",
            ],
        )?;
    }
    host.execute(
        "chown",
        &[
            "-R",
            "easysub:easysub",
            data.to_str().context("数据路径编码无效")?,
        ],
    )?;
    host.execute(
        "chmod",
        &["700", data.to_str().context("数据路径编码无效")?],
    )
}

pub fn upgrade(ops: &mut impl UpgradeOps, old: &Path, new: &Path) -> Result<()> {
    ops.stop()?;
    let result = (|| {
        ops.switch(new)?;
        ops.start()?;
        ops.healthy()
    })();
    if let Err(error) = result {
        // 回滚前先停止失败的新进程，避免旧版和新版同时占用数据。
        ops.stop()
            .context("升级失败，停止新服务失败，需要人工恢复")?;
        ops.switch(old)
            .context("升级失败，恢复旧链接失败，需要人工恢复")?;
        ops.start().context("旧版本重启失败，需要人工恢复")?;
        ops.healthy().context("旧版本健康检查失败，需要人工恢复")?;
        bail!("升级失败，已回滚旧版本：{error:#}");
    }
    Ok(())
}

pub fn http_healthy(host: &str, port: u16) -> Result<()> {
    use std::net::{SocketAddr, TcpStream};
    use std::time::Duration;
    let address: SocketAddr = format!(
        "{}:{port}",
        if host.contains(':') {
            format!("[{host}]")
        } else {
            host.to_owned()
        }
    )
    .parse()?;
    let mut stream = TcpStream::connect_timeout(&address, Duration::from_secs(1))?;
    stream.set_read_timeout(Some(Duration::from_secs(1)))?;
    stream.write_all(
        format!("GET /api/health HTTP/1.0\r\nHost: localhost\r\nConnection: close\r\n\r\n")
            .as_bytes(),
    )?;
    let mut response = String::new();
    stream.take(16384).read_to_string(&mut response)?;
    let body = response
        .split_once("\r\n\r\n")
        .map(|(_, b)| b.replace(' ', ""))
        .unwrap_or_default();
    ensure!(
        (response.starts_with("HTTP/1.1 200") || response.starts_with("HTTP/1.0 200"))
            && body.contains("\"configured\":true")
            && body.contains("\"status\":\"ok\""),
        "服务尚未就绪"
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn paths_reject_traversal_and_system_directories() {
        let root = tempdir().unwrap();
        assert!(safe_join(root.path(), Path::new("../secret")).is_err());
        assert!(safe_join(root.path(), &root.path().join("absolute")).is_err());
        assert_eq!(
            safe_join(root.path(), Path::new("app/main.py")).unwrap(),
            root.path().join("app/main.py")
        );
        assert!(safe_link(root.path(), root.path(), Path::new("../../secret")).is_err());
        assert!(safe_link(
            root.path(),
            &root.path().join("python/bin"),
            Path::new("../lib/python3")
        )
        .is_ok());
        for path in ["/", "/var", "/etc", "/tmp", "../data"] {
            assert!(safe_absolute(Path::new(path)).is_err());
        }
    }

    #[test]
    fn env_secret_is_long_and_existing_env_is_preserved() {
        let root = tempdir().unwrap();
        let data = root.path().join("data");
        let path = root.path().join("etc/easysub.env");
        write_env(&path, &data, "0.0.0.0", 8000).unwrap();
        let first = fs::read_to_string(&path).unwrap();
        assert!(
            read_env(&path)
                .unwrap()
                .iter()
                .find(|(k, _)| k == "JWT_SECRET")
                .unwrap()
                .1
                .len()
                >= 32
        );
        write_env(&path, &data, "127.0.0.1", 9000).unwrap();
        assert_eq!(fs::read_to_string(path).unwrap(), first);
    }

    #[test]
    fn service_matches_snapshot() {
        assert_eq!(
            unit(Path::new(if cfg!(windows) {
                "C:/var/lib/easysub"
            } else {
                "/var/lib/easysub"
            }))
            .unwrap()
            .replace("C:/var", "/var"),
            include_str!("../tests/unit.snapshot")
        );
    }

    #[derive(Default)]
    struct Fake {
        current: PathBuf,
        running: bool,
        fail_new: bool,
        switches: Vec<PathBuf>,
    }
    impl UpgradeOps for Fake {
        fn stop(&mut self) -> Result<()> {
            self.running = false;
            Ok(())
        }
        fn switch(&mut self, p: &Path) -> Result<()> {
            self.current = p.to_owned();
            self.switches.push(p.to_owned());
            Ok(())
        }
        fn start(&mut self) -> Result<()> {
            self.running = true;
            Ok(())
        }
        fn healthy(&mut self) -> Result<()> {
            ensure!(
                !(self.fail_new && self.current == Path::new("new")),
                "模拟健康检查失败"
            );
            Ok(())
        }
    }

    #[test]
    fn failed_upgrade_rolls_back_and_restarts_old_version() {
        let mut fake = Fake {
            fail_new: true,
            ..Default::default()
        };
        assert!(upgrade(&mut fake, Path::new("old"), Path::new("new")).is_err());
        assert_eq!(fake.current, Path::new("old"));
        assert!(fake.running);
        assert_eq!(
            fake.switches,
            vec![PathBuf::from("new"), PathBuf::from("old")]
        );
        let mut fake = Fake::default();
        upgrade(&mut fake, Path::new("old"), Path::new("new")).unwrap();
        assert_eq!(fake.current, Path::new("new"));
    }

    #[test]
    fn binary_index_detects_corruption_and_bounds() {
        let mut bytes = b"ELF-payload".to_vec();
        bytes.extend(4u64.to_le_bytes());
        bytes.extend(7u64.to_le_bytes());
        bytes.extend(Sha256::digest(b"payload"));
        bytes.extend(MAGIC);
        assert_eq!(payload_from_binary(&bytes).unwrap(), b"payload");
        bytes[4] ^= 1;
        assert!(payload_from_binary(&bytes).is_err());
        let end = bytes.len() - 64;
        bytes[end..end + 8].copy_from_slice(&u64::MAX.to_le_bytes());
        assert!(payload_from_binary(&bytes).is_err());
    }

    #[test]
    fn payload_extracts_required_layout_and_rejects_external_links() {
        use flate2::{write::GzEncoder, Compression};
        let make = |escape: bool| {
            let gzip = GzEncoder::new(Vec::new(), Compression::default());
            let mut archive = tar::Builder::new(gzip);
            for (path, body) in [
                ("VERSION", "2.1.0\n"),
                ("python/bin/python3", "python"),
                ("app/app/main.py", "app"),
                ("frontend_dist/index.html", "网页"),
            ] {
                let mut header = tar::Header::new_gnu();
                header.set_size(body.len() as u64);
                header.set_mode(0o755);
                header.set_cksum();
                archive
                    .append_data(&mut header, path, body.as_bytes())
                    .unwrap();
            }
            if escape {
                let mut header = tar::Header::new_gnu();
                header.set_entry_type(tar::EntryType::Symlink);
                header.set_size(0);
                header.set_mode(0o777);
                archive
                    .append_link(&mut header, "python/escape", "../../secret")
                    .unwrap();
            }
            archive.into_inner().unwrap().finish().unwrap()
        };
        let root = tempdir().unwrap();
        assert_eq!(
            unpack(&make(false), &root.path().join("valid")).unwrap(),
            "2.1.0"
        );
        assert!(unpack(&make(true), &root.path().join("invalid")).is_err());
        assert!(unpack(&[], &root.path().join("empty")).is_err());
    }

    #[test]
    fn linux_provisioning_uses_mock_host_and_propagates_failures() {
        struct MockHost {
            existing: bool,
            calls: Vec<String>,
            fail: bool,
        }
        impl Host for MockHost {
            fn user_exists(&mut self) -> Result<bool> {
                Ok(self.existing)
            }
            fn execute(&mut self, program: &str, _: &[&str]) -> Result<()> {
                ensure!(!self.fail, "模拟系统命令失败");
                self.calls.push(program.to_owned());
                Ok(())
            }
        }
        let mut host = MockHost {
            existing: false,
            calls: vec![],
            fail: false,
        };
        provision_user(&mut host, Path::new("data")).unwrap();
        assert_eq!(host.calls, vec!["useradd", "chown", "chmod"]);
        host.existing = true;
        host.calls.clear();
        provision_user(&mut host, Path::new("data")).unwrap();
        assert_eq!(host.calls, vec!["chown", "chmod"]);
        host.fail = true;
        assert!(provision_user(&mut host, Path::new("data")).is_err());
    }
}

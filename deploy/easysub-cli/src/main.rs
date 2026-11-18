use anyhow::{ensure, Context, Result};
use clap::{Parser, Subcommand};
use easysub::*;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{Duration, Instant};

const ROOT: &str = "/opt/easysub";
const ENV: &str = "/etc/easysub/easysub.env";
const UNIT: &str = "/etc/systemd/system/easysub.service";

#[derive(Parser)]
#[command(
    name = "easysub",
    about = "EasySub 安装、运行与维护工具",
    disable_version_flag = true
)]
struct Cli {
    #[command(subcommand)]
    command: Action,
}

#[derive(Subcommand)]
enum Action {
    #[command(about = "安装并启动服务，需要 root")]
    Install {
        #[arg(long, default_value_t = 8000, help = "监听端口")]
        port: u16,
        #[arg(long, default_value = "0.0.0.0", help = "监听 IP 地址")]
        bind: String,
        #[arg(long, default_value = "/var/lib/easysub", help = "专用数据目录")]
        data: PathBuf,
    },
    #[command(about = "从已校验的新二进制升级，失败自动回滚")]
    Upgrade {
        #[arg(long, help = "新二进制文件")]
        from_file: PathBuf,
    },
    #[command(about = "卸载服务，默认保留数据与配置")]
    Uninstall {
        #[arg(long, help = "确认后清除数据和配置")]
        purge: bool,
    },
    #[command(about = "在前台运行，无需 systemd")]
    Run,
    #[command(about = "查看运行状态、版本与数据库")]
    Status,
    #[command(about = "查看二进制版本")]
    Version,
}

fn command(program: &str, args: &[&str]) -> Result<()> {
    ensure!(
        Command::new(program)
            .args(args)
            .status()
            .with_context(|| format!("无法执行 {program}"))?
            .success(),
        "命令执行失败：{program}"
    );
    Ok(())
}

struct LinuxHost;
impl Host for LinuxHost {
    fn user_exists(&mut self) -> Result<bool> {
        Ok(Command::new("id").arg("easysub").output()?.status.success())
    }
    fn execute(&mut self, program: &str, arguments: &[&str]) -> Result<()> {
        command(program, arguments)
    }
}

fn require_root() -> Result<()> {
    let result = Command::new("id").arg("-u").output()?;
    ensure!(
        result.status.success() && String::from_utf8_lossy(&result.stdout).trim() == "0",
        "此命令需要 root，请使用 sudo"
    );
    Ok(())
}

#[cfg(unix)]
fn symlink(target: &Path, link: &Path) -> Result<()> {
    std::os::unix::fs::symlink(target, link)?;
    Ok(())
}
#[cfg(not(unix))]
fn symlink(_: &Path, _: &Path) -> Result<()> {
    anyhow::bail!("此操作仅支持 Linux")
}

fn switch_link(release: &Path) -> Result<()> {
    let temporary = Path::new(ROOT).join("current.next");
    if temporary.symlink_metadata().is_ok() {
        fs::remove_file(&temporary)?;
    }
    symlink(release, &temporary)?;
    fs::rename(temporary, Path::new(ROOT).join("current"))?;
    Ok(())
}

fn settings() -> Result<(PathBuf, String, u16)> {
    let env = read_env(Path::new(ENV))?;
    let get = |key: &str| env.iter().find(|(k, _)| k == key).map(|(_, v)| v.clone());
    let data = PathBuf::from(get("DATA_DIR").context("env 缺少 DATA_DIR")?);
    safe_absolute(&data)?;
    let bind = get("BIND").unwrap_or_else(|| "0.0.0.0".into());
    bind.parse::<std::net::IpAddr>()?;
    let port = get("PORT").context("env 缺少 PORT")?.parse::<u16>()?;
    Ok((data, bind, port))
}

fn wait_health(bind: &str, port: u16) -> Result<()> {
    let host = match bind {
        "0.0.0.0" => "127.0.0.1",
        "::" => "::1",
        _ => bind,
    };
    let started = Instant::now();
    loop {
        if http_healthy(host, port).is_ok() {
            return Ok(());
        }
        ensure!(
            started.elapsed() < Duration::from_secs(60),
            "60 秒内健康检查未通过"
        );
        std::thread::sleep(Duration::from_millis(500));
    }
}

struct Service {
    bind: String,
    port: u16,
}
impl UpgradeOps for Service {
    fn stop(&mut self) -> Result<()> {
        command("systemctl", &["stop", "easysub"])
    }
    fn start(&mut self) -> Result<()> {
        command("systemctl", &["start", "easysub"])
    }
    fn switch(&mut self, release: &Path) -> Result<()> {
        switch_link(release)
    }
    fn healthy(&mut self) -> Result<()> {
        wait_health(&self.bind, self.port)
    }
}

fn prepare(payload: &[u8], data: &Path, releases: &Path) -> Result<PathBuf> {
    fs::create_dir_all(releases)?;
    let suffix = random_secret()?[..12].to_owned();
    let stage = releases.join(format!(".stage-{suffix}"));
    let result = (|| {
        let version = unpack(payload, &stage)?;
        ensure!(
            !stage.join("data").exists() && stage.join("data").symlink_metadata().is_err(),
            "payload 不应包含数据目录"
        );
        symlink(data, &stage.join("data"))?;
        let release = releases.join(format!("{version}-{suffix}"));
        fs::rename(&stage, &release)?;
        Ok(release)
    })();
    if result.is_err() && stage.is_dir() {
        fs::remove_dir_all(stage)?;
    }
    result
}

fn install(port: u16, bind: String, data: PathBuf) -> Result<()> {
    require_root()?;
    ensure!(
        !Path::new(UNIT).exists() && !Path::new(ROOT).join("current").exists(),
        "已经安装，请使用 upgrade"
    );
    safe_absolute(&data)?;
    bind.parse::<std::net::IpAddr>()
        .context("监听地址必须是 IP 地址")?;
    ensure!(port != 0, "端口不能为 0");
    ensure!(
        !data.starts_with(ROOT) && !data.starts_with("/etc/easysub"),
        "数据必须独立于程序和配置目录"
    );
    fs::create_dir_all(&data)?;
    let data = data.canonicalize()?;
    safe_absolute(&data)?;
    ensure!(
        !data.starts_with(ROOT) && !data.starts_with("/etc/easysub"),
        "解析后的数据路径越界"
    );
    // 不覆盖卸载时留下的 env，也不将原有服务切换到另一个数据目录。
    if Path::new(ENV).exists() {
        ensure!(
            settings()?.0 == data,
            "保留的 env 使用其他数据目录，请用原 --data 重新安装"
        );
    }
    let release = prepare(PAYLOAD, &data, &Path::new(ROOT).join("releases"))?;
    write_env(Path::new(ENV), &data, &bind, port)?;
    fs::write(data.join(".easysub-data"), b"EasySub\n")?;
    provision_user(&mut LinuxHost, &data)?;
    fs::write(UNIT, unit(&data)?)?;
    switch_link(&release)?;
    command("systemctl", &["daemon-reload"])?;
    command("systemctl", &["enable", "--now", "easysub"])?;
    let (_, actual_bind, actual_port) = settings()?;
    wait_health(&actual_bind, actual_port)?;
    println!(
        "安装成功，访问 http://{}:{} 。首次注册的账号即为管理员，请尽快注册。",
        actual_bind, actual_port
    );
    Ok(())
}

fn upgrade_file(file: PathBuf) -> Result<()> {
    require_root()?;
    let (data, bind, port) = settings()?;
    let old = fs::read_link(Path::new(ROOT).join("current"))?;
    let releases = Path::new(ROOT).join("releases");
    let old = old.canonicalize()?;
    ensure!(
        old.starts_with(releases.canonicalize()?),
        "当前 release 链接越界"
    );
    let bytes = fs::read(file)?;
    let new = prepare(payload_from_binary(&bytes)?, &data, &releases)?;
    let result = upgrade(&mut Service { bind, port }, &old, &new);
    if result.is_ok() {
        for entry in fs::read_dir(&releases)? {
            let path = entry?.path();
            if path != old
                && path != new
                && path.is_dir()
                && !path.symlink_metadata()?.file_type().is_symlink()
            {
                ensure!(
                    path.canonicalize()?.starts_with(releases.canonicalize()?),
                    "清理 release 路径越界"
                );
                fs::remove_dir_all(path)?;
            }
        }
        println!("升级成功，已保留当前与上一个 release，数据与 env 未覆盖。");
    } else if new.is_dir() {
        // 回滚失败时保留新目录，供人工恢复和诊断。
        if fs::read_link(Path::new(ROOT).join("current")).ok().as_ref() == Some(&old) {
            fs::remove_dir_all(new)?;
        }
    }
    result
}

fn uninstall(purge: bool) -> Result<()> {
    require_root()?;
    let (data, _, _) = settings()?;
    if purge {
        let resolved = data.canonicalize()?;
        safe_absolute(&resolved)?;
        ensure!(
            resolved == data && data.join(".easysub-data").is_file(),
            "数据路径未通过清理校验"
        );
        ensure!(
            !data.starts_with(ROOT) && !data.starts_with("/etc/easysub"),
            "数据目录越界"
        );
        println!(
            "将永久删除 {} 和 /etc/easysub；输入 yes 确认：",
            data.display()
        );
        let mut input = String::new();
        io::stdin().read_line(&mut input)?;
        ensure!(input.trim() == "yes", "已取消清除");
    }
    command("systemctl", &["disable", "--now", "easysub"])?;
    fs::remove_file(UNIT)?;
    command("systemctl", &["daemon-reload"])?;
    ensure!(
        Path::new(ROOT).canonicalize()? == Path::new(ROOT),
        "安装目录不能是外部链接"
    );
    fs::remove_dir_all(ROOT)?;
    if purge {
        fs::remove_dir_all(data)?;
        ensure!(
            Path::new("/etc/easysub").canonicalize()? == Path::new("/etc/easysub"),
            "配置目录越界"
        );
        fs::remove_dir_all("/etc/easysub")?;
    }
    if Path::new("/usr/local/bin/easysub").exists() {
        fs::remove_file("/usr/local/bin/easysub")?;
    }
    println!(
        "卸载完成{}。",
        if purge {
            "，已清除数据和配置"
        } else {
            "，已保留数据和配置"
        }
    );
    Ok(())
}

fn foreground() -> Result<()> {
    let (release, env) = if Path::new(ROOT).join("current").is_dir() && Path::new(ENV).is_file() {
        (Path::new(ROOT).join("current"), read_env(Path::new(ENV))?)
    } else {
        let cwd = std::env::current_dir()?;
        let data = cwd.join("easysub-data");
        fs::create_dir_all(&data)?;
        let runtime = cwd.join(".easysub-runtime");
        let release = runtime.join(env!("CARGO_PKG_VERSION"));
        if !release.join("VERSION").is_file() {
            ensure!(!release.exists(), "本地运行时目录不完整，请先移走后重试");
            let staged = prepare(PAYLOAD, &data.canonicalize()?, &runtime)?;
            fs::rename(staged, &release)?;
        }
        let env_path = data.join("easysub.env");
        write_env(&env_path, &data.canonicalize()?, "0.0.0.0", 8000)?;
        (release, read_env(&env_path)?)
    };
    let get = |key: &str, default: &str| {
        std::env::var(key)
            .ok()
            .or_else(|| env.iter().find(|(k, _)| k == key).map(|(_, v)| v.clone()))
            .unwrap_or_else(|| default.into())
    };
    let mut child = Command::new(release.join("python/bin/python3"));
    child
        .current_dir(&release)
        .envs(env.clone())
        .env("PYTHONPATH", release.join("app"));
    child.args([
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        &get("BIND", "0.0.0.0"),
        "--port",
        &get("PORT", "8000"),
    ]);
    #[cfg(unix)]
    {
        use std::os::unix::process::CommandExt;
        Err(child.exec().into())
    }
    #[cfg(not(unix))]
    {
        ensure!(child.status()?.success(), "服务运行失败");
        Ok(())
    }
}

fn status() -> Result<()> {
    let (data, _, _) = settings()?;
    let version = fs::read_to_string(Path::new(ROOT).join("current/VERSION"))?;
    let config = fs::read_to_string(data.join("db_config.json")).unwrap_or_default();
    println!(
        "当前版本：{}\n数据目录：{}\n数据库：{}",
        version.trim(),
        data.display(),
        if config.contains("\"sqlite\"") {
            "SQLite"
        } else {
            "MySQL / 尚未初始化"
        }
    );
    let state = Command::new("systemctl")
        .args(["is-active", "easysub"])
        .output()?;
    println!(
        "服务状态：{}",
        String::from_utf8_lossy(&state.stdout).trim()
    );
    Ok(())
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    if let Action::Version = cli.command {
        println!("EasySub {}", env!("CARGO_PKG_VERSION"));
        return Ok(());
    }
    ensure!(
        cfg!(target_os = "linux"),
        "运行仅支持 glibc ≥ 2.17 的 Linux，不支持 Alpine"
    );
    match cli.command {
        Action::Install { port, bind, data } => install(port, bind, data),
        Action::Upgrade { from_file } => upgrade_file(from_file),
        Action::Uninstall { purge } => uninstall(purge),
        Action::Run => foreground(),
        Action::Status => status(),
        Action::Version => unreachable!(),
    }
}

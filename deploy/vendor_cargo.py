"""仅 CI：按 Cargo.lock 下载并校验 crate，随后所有 cargo 调用均离线。"""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tomllib
import urllib.request


def main():
    crate = Path(__file__).resolve().parent / 'easysub-cli'
    vendor = crate / 'vendor'
    vendor.mkdir(exist_ok=True)
    lock = tomllib.loads((crate / 'Cargo.lock').read_text())
    for package in lock['package']:
        if 'source' not in package:
            continue
        assert package['source'].startswith('registry+'), '不支持未校验的 Git 依赖'
        name, version = package['name'], package['version']
        with urllib.request.urlopen(f'https://static.crates.io/crates/{name}/{name}-{version}.crate', timeout=60) as source:
            content = source.read()
        assert hashlib.sha256(content).hexdigest() == package['checksum'], f'{name} 校验失败'
        with tarfile.open(fileobj=io.BytesIO(content)) as archive:
            archive.extractall(vendor, filter='data')
        directory = vendor / f'{name}-{version}'
        files = {str(p.relative_to(directory)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*') if p.is_file()}
        (directory / '.cargo-checksum.json').write_text(json.dumps({'package': package['checksum'], 'files': files}))
    config = crate / '.cargo'
    config.mkdir(exist_ok=True)
    (config / 'config.toml').write_text('[source.crates-io]\nreplace-with = "vendored-sources"\n[source.vendored-sources]\ndirectory = "vendor"\n')


if __name__ == '__main__':
    main()

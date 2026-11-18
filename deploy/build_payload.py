"""仅 CI：校验固定 Python 运行时，安装目标平台 wheel，再生成内嵌 payload。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request


def main():
    root = Path(__file__).resolve().parent.parent
    arch = sys.argv[1]
    lock = json.loads((root / 'deploy/python-version.lock').read_text())
    work = root / 'artifacts' / arch
    work.mkdir(parents=True, exist_ok=True)
    archive = work / 'python.tar.gz'
    urllib.request.urlretrieve(lock[arch]['url'], archive)
    assert hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest() == lock[arch]['sha256'], 'Python SHA256 不匹配'
    payload = work / 'payload'
    payload.mkdir()
    with tarfile.open(archive) as source:
        source.extractall(payload, filter='data')
    packages = payload / 'python/lib/python3.12/site-packages'
    # 两种架构都按 glibc 2.17 基线取 wheel，禁止源码回退。
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--platform', f'manylinux2014_{arch}',
                    '--implementation', 'cp', '--python-version', '3.12', '--only-binary=:all:',
                    '--target', str(packages), '-r', str(root / 'backend/requirements.txt'),
                    '-c', str(root / 'deploy/wheels.constraints')], check=True)
    shutil.copytree(root / 'backend/app', payload / 'app/app', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(root / 'frontend/dist', payload / 'frontend_dist')
    version = next(line.split('"')[1] for line in (root / 'backend/app/routers/system.py').read_text(encoding='utf-8').splitlines() if line.startswith('APP_VERSION ='))
    (payload / 'VERSION').write_text(version + '\n')
    with tarfile.open(work / 'payload.tar.gz', 'w:gz') as target:
        for name in ['python', 'app', 'frontend_dist', 'VERSION']:
            target.add(payload / name, arcname=name)


if __name__ == '__main__':
    main()

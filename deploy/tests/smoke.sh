#!/usr/bin/env bash
# 只在 Linux CI 中运行；aarch64 由 binfmt/QEMU 执行。
set -euo pipefail
arch=$1
case "$arch" in x86_64) platform=linux/amd64 ;; aarch64) platform=linux/arm64 ;; *) exit 1 ;; esac
for image in ubuntu:20.04 debian:12; do
  docker run --rm -i --platform "$platform" -v "$PWD/release:/assets:ro" "$image" bash -s -- "$arch" <<'CONTAINER'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl libstdc++6 libcrypt1 tzdata
mkdir -p /work
cd /work
/assets/easysub-linux-"$1" run > /tmp/easysub.log 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true; cat /tmp/easysub.log' EXIT
for attempt in {1..60}; do
  if curl -fsS http://127.0.0.1:8000/api/health > health.json && grep -q '"configured":true' health.json; then
    curl -fsS http://127.0.0.1:8000/ > /dev/null
    cat health.json
    exit 0
  fi
  kill -0 "$pid"
  sleep 1
done
exit 1
CONTAINER
done

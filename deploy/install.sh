#!/usr/bin/env bash
# 下载并校验发布产物；Rust 安装器不访问网络。
set -euo pipefail
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo '请使用 sudo bash 运行安装脚本。' >&2
  exit 1
fi
case "$(uname -m)" in
  x86_64|amd64) arch=x86_64 ;;
  aarch64|arm64) arch=aarch64 ;;
  *) echo '仅支持 x86_64 和 aarch64。' >&2; exit 1 ;;
esac
if ! getconf GNU_LIBC_VERSION >/dev/null 2>&1; then
  echo '需要 glibc ≥ 2.17，不支持 Alpine。' >&2
  exit 1
fi
glibc=$(getconf GNU_LIBC_VERSION | awk '{print $2}')
if [[ $(printf '%s\n' 2.17 "$glibc" | sort -V | head -n1) != 2.17 ]]; then
  echo '需要 glibc ≥ 2.17。' >&2; exit 1
fi
if [[ ${1:-} == --upgrade ]]; then shift; fi
temporary=$(mktemp -d)
trap 'rm -rf -- "$temporary"' EXIT
api='https://api.github.com/repos/suyijun8182/easysub/releases/latest'
# 先固定 release 地址，避免 latest 在两次下载之间发生变化。
release=$(curl --fail --silent --show-error --location --proto '=https' "$api" | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -n1)
[[ "$release" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo '无法确定发布版本。' >&2; exit 1; }
base="https://github.com/suyijun8182/easysub/releases/download/$release"
asset="easysub-linux-$arch"
curl -fSL --proto '=https' "$base/$asset" -o "$temporary/$asset"
curl -fSL --proto '=https' "$base/SHA256SUMS" -o "$temporary/SHA256SUMS"
(
  cd "$temporary"
  awk -v name="$asset" '$2==name && $1 ~ /^[0-9a-f]+$/ && length($1)==64 {print}' SHA256SUMS > selected.sha256
  [[ $(wc -l < selected.sha256) -eq 1 ]] || { echo '校验清单无效。' >&2; exit 1; }
  sha256sum --check selected.sha256
)
chmod 755 "$temporary/$asset"
if [[ -e /opt/easysub/current && -x /usr/local/bin/easysub ]]; then
  /usr/local/bin/easysub upgrade --from-file "$temporary/$asset"
else
  "$temporary/$asset" install "$@"
fi
# 只有安装或升级健康检查成功，才替换维护命令。
install -m 755 "$temporary/$asset" /usr/local/bin/easysub.next
mv -f /usr/local/bin/easysub.next /usr/local/bin/easysub

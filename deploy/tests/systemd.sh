#!/usr/bin/env bash
set -euo pipefail
docker build -f deploy/tests/systemd.Dockerfile -t easysub-systemd-test .
container=$(docker run -d --privileged --cgroupns=host --security-opt seccomp=unconfined \
  --tmpfs /run --tmpfs /run/lock -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
  -v "$PWD/release:/assets:ro" -v "$PWD/backend/tests:/tests:ro" easysub-systemd-test)
trap 'docker exec "$container" journalctl -u easysub --no-pager || true; docker rm -f "$container" >/dev/null' EXIT
docker exec -i "$container" bash -s <<'CONTAINER'
set -euo pipefail
for attempt in {1..30}; do
  [[ $(systemctl is-system-running || true) =~ ^(running|degraded)$ ]] && break
  sleep 1
done
install -m 755 /assets/easysub-linux-x86_64 /usr/local/bin/easysub
easysub install --bind 127.0.0.1
# 重复安装必须失败且不能覆盖 env。
sha256sum /etc/easysub/easysub.env > /tmp/env.sha256
if easysub install; then exit 1; fi
sha256sum --check /tmp/env.sha256
python=/opt/easysub/current/python/bin/python3
"$python" - <<'PY'
import json, urllib.request, urllib.parse
base='http://127.0.0.1:8000'
def request(path, data, token=None, form=False):
    body=urllib.parse.urlencode(data).encode() if form else json.dumps(data).encode()
    headers={'Content-Type': 'application/x-www-form-urlencoded' if form else 'application/json'}
    if token: headers['Authorization']='Bearer '+token
    with urllib.request.urlopen(urllib.request.Request(base+path,body,headers)) as response: return json.load(response)
request('/api/auth/register', {'username':'ci-admin','email':'ci@example.com','password':'test-password-ci'})
token=request('/api/auth/login',{'username':'ci-admin','password':'test-password-ci'},form=True)['access_token']
sub=request('/api/subscriptions',{'name':'upgrade-preserves-data','next_renewal_date':'2027-01-31','start_date':'2027-01-31'},token)
open('/tmp/sub-id','w').write(str(sub['id']))
PY
easysub upgrade --from-file /assets/easysub-linux-x86_64
sha256sum --check /tmp/env.sha256
test "$(find /opt/easysub/releases -mindepth 1 -maxdepth 1 -type d | wc -l)" -eq 2
"$python" - <<'PY'
import sqlite3
with sqlite3.connect('/var/lib/easysub/easysub.db') as db:
    assert db.execute("select name, billing_anchor_day from subscriptions where id=?",(open('/tmp/sub-id').read(),)).fetchone()==('upgrade-preserves-data',31)
PY
# 在真实 data 软链接下检查图标的路径边界。
cd /opt/easysub/current
PYTHONPATH=/tests:/opt/easysub/current/app "$python" -m unittest test_data_symlink -v
easysub status
easysub uninstall
test -f /var/lib/easysub/easysub.db
test -f /etc/easysub/easysub.env
test ! -e /opt/easysub
CONTAINER

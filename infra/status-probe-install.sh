#!/usr/bin/env bash
# Install status probe systemd timer on the server.
# Run as root: bash infra/status-probe-install.sh
set -euo pipefail

BASE=/opt/proliv
mkdir -p "$BASE/status"
chmod 755 "$BASE/status"
# пустой стартовый файл, чтобы volume-монт был файловым объектом
[ -f "$BASE/status/status.json" ] || echo '{"updated_at":0,"groups":{"locations":[],"services":[]},"all_up":true,"samples":{}}' > "$BASE/status/status.json"

cat >/etc/systemd/system/status-probe.service <<EOF
[Unit]
Description=Proliv status probe (one-shot)

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 $BASE/infra/status-probe.py
EOF

cat >/etc/systemd/system/status-probe.timer <<'EOF'
[Unit]
Description=Run Proliv status probe every minute

[Timer]
OnBootSec=15
OnUnitActiveSec=60
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now status-probe.timer
systemctl start status-probe.service
echo "probe installed; first run done"
cat "$BASE/status/status.json" | python3 -m json.tool | head -40

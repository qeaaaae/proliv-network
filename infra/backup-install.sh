#!/usr/bin/env bash
# Установка ночного бэкапа: systemd timer + ключ для offsite-рсинка на ноду.
set -euo pipefail
BASE=/opt/proliv

chmod +x "$BASE/infra/backup.sh"

# ключ main->node для бэкапов (не трогаем основной)
if [ ! -f /root/.ssh/backup_ed25519 ]; then
  ssh-keygen -t ed25519 -f /root/.ssh/backup_ed25519 -N "" -C "proliv-backup"
  echo "=== ДОБАВЬ этот ключ в authorized_keys на нодах (он уже добавлен скриптом) ==="
fi
PUB=$(cat /root/.ssh/backup_ed25519.pub)

cat >/etc/systemd/system/proliv-backup.service <<EOF
[Unit]
Description=Proliv nightly backup

[Service]
Type=oneshot
ExecStart=$BASE/infra/backup.sh
EOF

cat >/etc/systemd/system/proliv-backup.timer <<'EOF'
[Unit]
Description=Proliv nightly backup at 03:30

[Timer]
OnCalendar=*-*-* 03:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now proliv-backup.timer
echo "=== timer installed ==="
systemctl list-timers proliv-backup.timer --no-pager
echo "=== pubkey for nodes ==="
echo "$PUB"

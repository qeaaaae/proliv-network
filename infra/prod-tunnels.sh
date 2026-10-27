#!/usr/bin/env bash
# Proliv prod: cloudflared quick-tunnels (temporary, until domain).
#   edge  -> 127.0.0.1:8090  (caddy split: /tg/webhook -> bot, rest -> backend)
#   app   -> 127.0.0.1:8082  (cabinet / Telegram Mini App)
#   site  -> 127.0.0.1:8080  (landing)
# Run on server as root:  bash infra/prod-tunnels.sh install
# URLs land in /opt/proliv/infra/tunnel-urls.env via tunnel-url-sync.timer.
set -euo pipefail

BASE=/opt/proliv/infra
URLS_FILE=$BASE/tunnel-urls.env

install_cloudflared() {
  if command -v cloudflared >/dev/null 2>&1; then
    echo "cloudflared already installed: $(cloudflared --version 2>&1 | head -1)"
    return
  fi
  arch=$(dpkg --print-architecture 2>/dev/null || uname -m)
  case "$arch" in
    amd64|x86_64) cf_arch=amd64 ;;
    arm64|aarch64) cf_arch=arm64 ;;
    *) echo "unsupported arch: $arch" >&2; exit 1 ;;
  esac
  curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${cf_arch}" \
    -o /usr/local/bin/cloudflared
  chmod +x /usr/local/bin/cloudflared
  echo "installed: $(cloudflared --version 2>&1 | head -1)"
}

write_units() {
  cat >/etc/systemd/system/cloudflared@.service <<'EOF'
[Unit]
Description=cloudflared quick tunnel to 127.0.0.1:%i
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/local/bin/cloudflared tunnel --no-autoupdate --protocol http2 --url http://127.0.0.1:%i
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

  cat >/etc/systemd/system/tunnel-url-sync.service <<EOF
[Unit]
Description=Sync trycloudflare URLs into proliv env
After=network-online.target

[Service]
Type=oneshot
ExecStart=$BASE/tunnel-url-sync.sh
EOF

  cat >/etc/systemd/system/tunnel-url-sync.timer <<'EOF'
[Unit]
Description=Poll trycloudflare URLs

[Timer]
OnBootSec=20
OnUnitActiveSec=30
Persistent=true

[Install]
WantedBy=timers.target
EOF

  systemctl daemon-reload
}

cmd=${1:-install}
case "$cmd" in
  install)
    install_cloudflared
    write_units
    for p in 8090 8082 8080; do
      systemctl enable --now "cloudflared@${p}.service"
    done
    systemctl enable --now tunnel-url-sync.timer
    echo "tunnels starting; URLs will appear in $URLS_FILE"
    ;;
  urls)
    cat "$URLS_FILE" 2>/dev/null || echo "no URLs yet"
    ;;
  stop)
    for p in 8090 8082 8080; do systemctl disable --now "cloudflared@${p}.service" || true; done
    systemctl disable --now tunnel-url-sync.timer || true
    ;;
  *)
    echo "usage: $0 {install|urls|stop}" >&2; exit 1 ;;
esac

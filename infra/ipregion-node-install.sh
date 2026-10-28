#!/usr/bin/env bash
# Run as root on a VPN node: bash ipregion-node-install.sh
# Geo check of the node IP (github.com/vernette/ipregion) every 6h -> /opt/ipregion/last.json.
# status-probe on main reads the file over SSH and the bot renders it in /nodes.
set -euo pipefail
BASE=/opt/ipregion
mkdir -p "$BASE"

missing=()
command -v jq >/dev/null || missing+=(jq)
command -v nslookup >/dev/null || missing+=(dnsutils)
command -v column >/dev/null || missing+=(bsdmainutils)
command -v curl >/dev/null || missing+=(curl)
if ((${#missing[@]})); then
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${missing[@]}"
fi

curl -fsSL https://ipregion.vrnt.xyz -o "$BASE/ipregion.sh"
chmod 755 "$BASE/ipregion.sh"

cat >"$BASE/run.sh" <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
cd /opt/ipregion
./ipregion.sh -j -4 >last.json.tmp 2>/dev/null </dev/null
if jq -e '.results.primary | length > 0' last.json.tmp >/dev/null 2>&1; then
  mv last.json.tmp last.json
else
  rm -f last.json.tmp
  exit 1
fi
EOF
chmod 755 "$BASE/run.sh"

cat >/etc/systemd/system/ipregion.service <<EOF
[Unit]
Description=Proliv ipregion geo check
After=network-online.target

[Service]
Type=oneshot
ExecStart=$BASE/run.sh
EOF

cat >/etc/systemd/system/ipregion.timer <<'EOF'
[Unit]
Description=Proliv ipregion geo check every 6h

[Timer]
OnBootSec=5min
OnUnitActiveSec=6h
RandomizedDelaySec=10min

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now ipregion.timer
systemctl start ipregion.service
jq -c '{ipv4, primary: (.results.primary | length), custom: (.results.custom | length)}' "$BASE/last.json"

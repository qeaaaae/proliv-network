#!/usr/bin/env bash
set -u
echo "=== landing container mounts ==="
docker inspect proliv-landing --format '{{json .Mounts}}' | python3 -m json.tool 2>/dev/null | grep -E 'Source|Destination' || docker inspect proliv-landing --format '{{.Mounts}}'
echo
docker inspect proliv-landing --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
echo "=== landing html root ==="
docker exec proliv-landing sh -c 'ls /usr/share/nginx/html 2>/dev/null | head; nginx -T 2>/dev/null | grep -E "root|listen" | head -10' 2>/dev/null
echo "=== caddy config on main ==="
grep -vE '^\s*#|^\s*$' /opt/proliv/infra/Caddyfile* 2>/dev/null | head -40
echo "=== subpage container mounts ==="
docker inspect remnawave-subscription-page --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}' 2>/dev/null || docker ps --format '{{.Names}}' | grep -i sub

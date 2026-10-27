#!/bin/bash
set -x
cd /opt/proliv

# 1. cloudflared + 3 ??????????????
bash infra/prod-tunnels.sh install

# 2. ???????????? ?????????????? minishop (backend image covers bot/worker/migrate)
cd /opt/proliv/shop
docker build -f deploy/docker/Dockerfile --target backend \
  --build-arg REMNAWAVE_MINISHOP_BUILD_TAG=v3.8.3 \
  --build-arg REMNAWAVE_MINISHOP_BUILD_COMMIT=727c2387 \
  --build-arg REMNAWAVE_MINISHOP_BRANCH=main \
  --build-arg REMNAWAVE_MINISHOP_BUILD_PROVENANCE=custom \
  -t 3252a8/remnawave-minishop-backend:latest . 2>&1 | tail -5

docker build -f deploy/docker/Dockerfile --target frontend \
  --build-arg REMNAWAVE_MINISHOP_BUILD_TAG=v3.8.3 \
  --build-arg REMNAWAVE_MINISHOP_BUILD_COMMIT=727c2387 \
  --build-arg REMNAWAVE_MINISHOP_BRANCH=main \
  --build-arg REMNAWAVE_MINISHOP_BUILD_PROVENANCE=custom \
  -t 3252a8/remnawave-minishop-frontend:latest . 2>&1 | tail -5

echo "=== tunnel URLs ==="
sleep 8
cat /opt/proliv/infra/tunnel-urls.env 2>/dev/null || journalctl -u 'cloudflared@*' -o cat --since '-2 min' | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -5
echo "=== DONE ==="


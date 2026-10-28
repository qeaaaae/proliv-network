#!/usr/bin/env bash
for ct in application/grpc text/plain application/octet-stream; do
  echo "--- POST CT=$ct ---"
  curl -s -i --max-time 15 -X POST 'https://ee.proliv-network.xyz/api/xhttp' -H "Content-Type: $ct" --data-binary 'x' | head -5
done
echo '--- chunked ---'
curl -s -i --max-time 15 -X POST 'https://ee.proliv-network.xyz/api/xhttp' -H 'Content-Type: application/grpc' -H 'Transfer-Encoding: chunked' --data-binary 'x' | head -5

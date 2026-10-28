#!/usr/bin/env bash
for h in de.proliv-network.xyz uk.proliv-network.xyz ee-src.proliv-network.xyz ee.proliv-network.xyz; do
  ip=$(python3 -c "import socket;print(socket.gethostbyname('$h'))" 2>/dev/null)
  echo "--- $h ($ip) ---"
  timeout 8 bash -c "echo > /dev/tcp/$h/443" && echo 'TCP 443 OK' || echo 'TCP 443 FAIL'
  r=$(echo | timeout 10 openssl s_client -connect "$h:443" -servername "$h" 2>/dev/null | grep -c 'BEGIN CERTIFICATE')
  echo "TLS handshake certs received: $r"
done

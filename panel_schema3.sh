#!/bin/bash
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
for p in /api/docs-json /api/reference/openapi.json /api/swagger /scalar /api/scalar /api-json/openapi.json; do
  c=$(curl -s -o /tmp/t -w "%{http_code}" -H "Authorization: Bearer $JWT" "http://127.0.0.1:3443$p")
  s=$(wc -c < /tmp/t)
  t=$(head -c 60 /tmp/t | tr -d '\n')
  echo "$p -> $c (${s}b) [$t]"
done

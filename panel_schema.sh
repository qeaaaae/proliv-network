#!/bin/bash
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
for path in /api/docs /api/openapi.json /api-json /docs-json /api/swagger.json /api/reference; do
  code=$(curl -s -o /tmp/schema_try -w "%{http_code}" -H "Authorization: Bearer $JWT" "http://127.0.0.1:3443$path")
  size=$(wc -c < /tmp/schema_try 2>/dev/null)
  echo "$path -> $code ($size bytes)"
  if [ "$code" = "200" ] && [ "$size" -gt 1000 ]; then
    cp /tmp/schema_try /tmp/openapi.json
    echo "SAVED to /tmp/openapi.json"
    break
  fi
done

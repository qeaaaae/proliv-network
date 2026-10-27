#!/bin/bash
JWT=$(tr -d '[:space:]' < /root/.panel-jwt)
curl -s -H "Authorization: Bearer $JWT" http://127.0.0.1:3443/scalar -o /tmp/scalar.html
grep -oE '"(url|content|specUrl)"[^,}]*|openapi[^"< ]*' /tmp/scalar.html | head -15

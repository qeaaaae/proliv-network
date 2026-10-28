#!/usr/bin/env bash
docker exec remnawave sh -c "grep -oE '.{0,60}TELEGRAM_ID.{0,160}' /opt/app/dist/app.js | head -4"
echo '--- header templating ---'
docker exec remnawave sh -c "grep -oE '.{0,250}customResponseHeaders.{0,250}' /opt/app/dist/app.js | grep -iE 'templat|replace|render|format' | head -3"

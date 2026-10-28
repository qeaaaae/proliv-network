#!/usr/bin/env bash
cd /opt/app
grep -oE ".{200}sockoptParams.{400}" dist/app.js | head -3
echo "====="
grep -oE ".{100}muxParams.{300}" dist/app.js | head -2

#!/usr/bin/env bash
set -uo pipefail
cd /tmp
python3 - <<'PY'
import zipfile, os
os.makedirs('/tmp/xray-bin', exist_ok=True)
zipfile.ZipFile('/tmp/xray.zip').extract('xray', '/tmp/xray-bin')
os.chmod('/tmp/xray-bin/xray', 0o755)
print('extracted')
PY
/tmp/xray-bin/xray version | head -2

#!/usr/bin/env bash
R=/var/lib/docker/rootfs/overlayfs/9743afaecf0ed3f2d6cf96a7fc4943ca69c10c16f71243224a9072593ea2d4b3/opt/app/dist/node_modules/@remnawave/backend-contract/build/backend/api/routes.js
[ -f "$R" ] || R=$(find /var/lib/docker/rootfs/overlayfs -name routes.js -path '*backend-contract*' 2>/dev/null | head -1)
echo "ROUTES: $R"
grep -oE "'[^']*'" "$R" | grep -iE 'template|subscr|xray|host' | sort -u | head -50

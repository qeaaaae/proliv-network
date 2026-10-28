#!/usr/bin/env bash
R=/var/lib/docker/rootfs/overlayfs/9743afaecf0ed3f2d6cf96a7fc4943ca69c10c16f71243224a9072593ea2d4b3/opt/app/dist/node_modules/@remnawave/backend-contract/build/backend/api/routes.js
wc -l "$R"
grep -n -iE 'template' "$R" | head -20
echo '==='
grep -n -iE 'subscription' "$R" | head -20

#!/usr/bin/env bash
F=/var/lib/docker/rootfs/overlayfs/9743afaecf0ed3f2d6cf96a7fc4943ca69c10c16f71243224a9072593ea2d4b3/opt/app/dist/node_modules/@remnawave/backend-contract/build/backend/commands/nodes/update.command.js
grep -oE 'activeInbounds[^,;]{0,200}' "$F" | head -3
echo '---full schema names---'
grep -oE "[a-zA-Z]+:u_\.z\." "$F" | sort -u | head -40
echo '--- profile-modification schema ---'
F2=/var/lib/docker/rootfs/overlayfs/9743afaecf0ed3f2d6cf96a7fc4943ca69c10c16f71243224a9072593ea2d4b3/opt/app/dist/node_modules/@remnawave/backend-contract/build/backend/commands/nodes/bulk-actions/profile-modification.command.js
cat "$F2" | head -60

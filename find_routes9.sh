#!/usr/bin/env bash
D=/var/lib/docker/rootfs/overlayfs/9743afaecf0ed3f2d6cf96a7fc4943ca69c10c16f71243224a9072593ea2d4b3/opt/app/dist/node_modules/@remnawave/backend-contract/build/backend/api
grep -rn 'SUBSCRIPTION_TEMPLATE_CONTROLLER\|SUBSCRIPTION_TEMPLATE_ROUTES' $D --include='*.js' -l | head
grep -oE "SUBSCRIPTION_TEMPLATE_CONTROLLER[^,;]*" $D/controllers.js 2>/dev/null | head -3
grep -oE "SUBSCRIPTION_TEMPLATE_ROUTES[^}]*}" $D/controllers.js 2>/dev/null | head -5
echo "=== controllers.js template section ==="
grep -n -iE 'template' $D/controllers.js | head -20

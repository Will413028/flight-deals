#!/bin/sh
set -eu
hook="$(git rev-parse --git-path hooks)/pre-push"
printf '#!/bin/sh\nexec scripts/check.sh\n' > "$hook"
chmod +x "$hook"
echo "installed $hook"

#!/bin/bash
set -e

# This entrypoint ensures any provided command runs via a shell
# so environment variables like $PORT are expanded correctly.

if [ "$#" -gt 0 ]; then
  cmd="$*"
else
  cmd="./start.sh"
fi

echo "🔑 ENTRYPOINT executing: $cmd"
exec /bin/bash -lc "$cmd"

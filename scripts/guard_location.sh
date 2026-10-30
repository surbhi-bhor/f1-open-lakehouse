#!/usr/bin/env bash
# Bind mounts from /mnt/c (the Windows drive) run several times slower than from the WSL filesystem.
dir="${1:?usage: guard_location.sh <dir>}"
case "$dir" in
  /mnt/*)
    echo "repo must live inside the WSL filesystem (~/...), not under /mnt/: $dir" >&2
    exit 1
    ;;
esac

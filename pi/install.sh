#!/usr/bin/env bash
set -euo pipefail

# Must run with sudo
if [[ $EUID -ne 0 ]]; then
    echo "run with sudo" >&2
    exit 1
fi

# Get the directory of the install.sh script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define paths to config files
BOOT=/boot/firmware 
[[ -d $BOOT ]] || BOOT=/boot
CONFIG="$BOOT/config.txt"
CMDLINE="$BOOT/cmdline.txt"

# One time backups
cp -n "$CONFIG" "$CONFIG.orig"
cp -n "$Cmdline" "$CMDLINE.orig"




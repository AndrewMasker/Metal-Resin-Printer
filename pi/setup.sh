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
cp -n "$CMDLINE" "$CMDLINE.orig"

# Include the lmm_printer config.txt into the actual config.txt
INCLUDE_NAME="lmm_printer_config.txt"
install -m 644 "$DIR/config.txt" "$BOOT/$INCLUDE_NAME"
if ! grep -qxF "include $INCLUDE_NAME" "$CONFIG"; then
    printf '\n[all]\ninclude %s\n' "$INCLUDE_NAME" >> "$CONFIG"
fi

# Replace cmdline.text with the modified version
read -r line < "$CMDLINE"
new=""
for arg in $line; do
    while read -r change _ || [[ -n $change ]]; do
        [[ -z $change || $change == \#* ]] && continue
        [[ ${arg%%=*} == ${change%%=*} ]] && continue 2
        [[ $change == '!'* ]] && remove="${change#!}" && [[ $arg == $remove ]] && continue 2
    done < "$DIR/cmdline_change.txt"
    new+=" $arg"
done
while read -r change _ || [[ -n $change ]]; do
    [[ -z $change || $change == \#* || $change == '!'* ]] && continue
    new+=" $change"
done < "$DIR/cmdline_change.txt"
[[ $new == *root=* ]] || { echo "cmdline looks wrong. Not writing: $new" >&2; exit 1; }
echo "${new# }" > "$CMDLINE"

# Display driver install and reload
BUILD="$(mktemp -d)"
trap 'rm -rf "$BUILD"' EXIT
python3 "$DIR/tools/mipi-dbi-cmd" "$BUILD/panel.bin" "$DIR/panel.txt"
install -m 644 "$BUILD/panel.bin" "/lib/firmware/panel.bin"
if [[ -d /sys/module/panel_mipi_dbi ]]; then
    modprobe -r panel_mipi_dbi && modprobe panel_mipi_dbi || echo "Display driver busy, reboot to apply panel.bin" >&2
fi

# Commands that must be run to ensure everything works properly
systemctl disable hciuart 2>/dev/null || true

# Ensuring apt installed packages are installed
APT_LIST="$(python3 - "$DIR/../pyproject.toml" <<'PY'
import sys , tomllib
with open(sys.argv[1] , "rb") as f:
    data = tomllib.load(f)
for pckg in data.get("tool" , {}).get("lmm_printer" , {}).get("apt_pckgs" , []):
    print(pckg)
PY
)"
mapfile -t APT_PCKGS < <(printf '%s' "$APT_LIST")
if (( ${#APT_PCKGS[@]} )); then
    apt-get update
    apt-get install -y "${APT_PCKGS[@]}"
fi

sudo -u "$SUDO_USER" python3 -m venv --system-site-packages "$DIR/../.venv"
sudo -u "$SUDO_USER" "$DIR/../.venv/bin/pip" install -e "$DIR/.."

echo "If this is the first install or you updated config.txt or cmdline.txt, you must reboot the pi. Else you can continue."

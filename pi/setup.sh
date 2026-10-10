#!/usr/bin/env bash
set -euo pipefail
trap 'echo "FAILED at line $LINENO: $BASH_COMMAND" >&2' ERR
trap 'rm -f "${RENDERED:-}"; rm -rf "${BUILD:-}"' EXIT

# Must run with sudo
if [[ $EUID -ne 0 ]]; then
    echo "run with sudo" >&2
    exit 1
fi
: "${SUDO_USER:?Even if you are root you must run with sudo.}"

# Get the directory of the install.sh script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
echo "APT packages installed."

sudo -u "$SUDO_USER" python3 -m venv --system-site-packages "$DIR/../.venv"
echo ".venv created."

sudo -u "$SUDO_USER" "$DIR/../.venv/bin/pip" install -e "$DIR/.."
echo "packages installed from pyproject.toml"

# Define paths to config files
BOOT=/boot/firmware 
[[ -d $BOOT ]] || BOOT=/boot
CONFIG="$BOOT/config.txt"
CMDLINE="$BOOT/cmdline.txt"
 
# One time backups
cp -n "$CONFIG" "$CONFIG.orig"
cp -n "$CMDLINE" "$CMDLINE.orig"
echo "Backups were created or already exist."

# Render the config.txt based on values in config.yaml
CFG="$DIR/../config/${1:-config.yaml}" # Uses the first argument passed as name for config file, else uses config.yaml
RENDERED="$(mktemp)"
python3 - "$CFG" "$DIR/config.txt" > "$RENDERED" <<'PY'
import re , sys , yaml
with open(sys.argv[1]) as f:
    cfg = yaml.safe_load(f)

def lookup(match):
    node = cfg
    for key in match.group(1).split("."):
        node = node[key]
    return str(node)

with open(sys.argv[2]) as f:
    rendered = re.sub(r"\{\{\s*([\w.]+)\s*\}\}" , lookup , f.read())
    print(rendered , end = "")
PY
echo "Rendered config.txt"

# Include the lmm_printer config.txt into the actual config.txt
INCLUDE_NAME="lmm_printer_config.txt"
install -m 644 "$RENDERED" "$BOOT/$INCLUDE_NAME"
if ! grep -qxF "include $INCLUDE_NAME" "$CONFIG"; then
    printf '\n[all]\ninclude %s\n' "$INCLUDE_NAME" >> "$CONFIG"
fi
echo "Included lmm_printer config.txt into pi config.txt."

# Replace cmdline.text with the modified version
read -r line < "$CMDLINE" || true
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
echo "cmdline.txt has been replaced with the modified version."

# Display driver install and reload
BUILD="$(mktemp -d)"
python3 "$DIR/tools/mipi-dbi-cmd" "$BUILD/panel.bin" "$DIR/panel.txt"
install -m 644 "$BUILD/panel.bin" "/lib/firmware/panel.bin"
if [[ -d /sys/module/panel_mipi_dbi ]]; then
    modprobe -r panel_mipi_dbi && modprobe panel_mipi_dbi || echo "DISPLAY DRIVER BUSY, REBBOT TO APPLY panel.bin" >&2
fi
echo "Display driver has been installed."

# Commands that must be run to ensure everything works properly
systemctl disable hciuart 2>/dev/null || true
echo "Required commands have been run."

echo "If this is the first install or you updated config.txt or cmdline.txt, you must reboot the pi. Else you can continue."

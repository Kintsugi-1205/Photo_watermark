#!/bin/zsh
cd "$(dirname "$0")" || exit 1

python3 watermark.py --type text

echo
echo "Done. Press Enter to close this window."
read

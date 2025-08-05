#!/bin/bash

APP_NAME="MyTkApp"
MAIN_SCRIPT="main.py"
ICON_FILE="icon.png"  # Optional: replace with your icon file or remove --icon line if not needed

# Install pyinstaller if not present
pip show pyinstaller &>/dev/null || pip install pyinstaller

# Build
pyinstaller --noconfirm --onefile --windowed \
  --name "$APP_NAME" \
  --icon="$ICON_FILE" \
  "$MAIN_SCRIPT"

# Move to release folder
mkdir -p release
mv dist/$APP_NAME release/

echo "✅ Build complete: ./release/$APP_NAME"


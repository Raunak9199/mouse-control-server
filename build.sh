#!/bin/bash

APP_NAME="MouseControlServer"
MAIN_SCRIPT="new_mouse_server.py"
ICON_FILE="mouse.jpg"

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


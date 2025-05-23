#!/bin/bash
set -euo pipefail

# --- Configuration ---

# Where to install the Python script (so it becomes globally available).
INSTALL_SCRIPT="/usr/local/bin/welcometomaibloom"

# Directory to host the custom logo.
LOGO_INSTALL_DIR="/usr/local/share/welcometomaibloom"

# Destination for the desktop entry on your Desktop.
DESKTOP_DEST="$HOME/Desktop/welcometomaibloom.desktop"

# --- Step 0: Verify Source Files ---

if [ ! -f "welcometomaibloom.py" ]; then
    echo "Error: welcometomaibloom.py not found in the current directory."
    exit 1
fi

if [ ! -f "logo.png" ]; then
    echo "Warning: logo.png not found. The desktop entry will have no custom icon."
    ICON_ENTRY=""
else
    ICON_ENTRY="Icon=$LOGO_INSTALL_DIR/logo.png"
fi

# --- Step 1: Install the Python Script ---

echo "Installing welcometomaibloom.py to $INSTALL_SCRIPT..."
sudo cp welcometomaibloom.py "$INSTALL_SCRIPT"
sudo chmod +x "$INSTALL_SCRIPT"

# --- Step 2: Install the Logo (if provided) ---

if [ -n "$ICON_ENTRY" ]; then
    echo "Installing logo.png to $LOGO_INSTALL_DIR..."
    sudo mkdir -p "$LOGO_INSTALL_DIR"
    sudo cp logo.png "$LOGO_INSTALL_DIR/logo.png"
fi

# --- Step 3: Write the Desktop Entry File Directly to the Desktop ---

echo "Writing desktop entry file to $DESKTOP_DEST..."
mkdir -p "$HOME/Desktop"
cat <<EOF > "$DESKTOP_DEST"
[Desktop Entry]
Type=Application
Name=Welcome to Mai Bloom!
Comment=Customize your OS with the Mai Bloom Welcome App
Exec=$INSTALL_SCRIPT
$ICON_ENTRY
Terminal=false
Categories=Utility;Application;
EOF

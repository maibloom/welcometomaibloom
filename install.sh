#!/bin/bash
set -euo pipefail

# --- Configuration ---

# Where to install the Python script so it will be globally available.
INSTALL_SCRIPT="/usr/local/bin/welcometomaibloom"

# Directory for the custom logo.
LOGO_INSTALL_DIR="/usr/local/share/welcometomaibloom"

# Temporary location for the .desktop file.
TEMP_DESKTOP="/tmp/welcometomaibloom.desktop"

# Destination on the user's desktop.
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

# --- Step 3: Write the Desktop Entry File ---

echo "Writing desktop entry file..."
cat <<EOF > "$TEMP_DESKTOP"
[Desktop Entry]
Type=Application
Name=Welcome to Mai Bloom!
Comment=Customize your OS with the Mai Bloom Welcome App
Exec=$INSTALL_SCRIPT
$ICON_ENTRY
Terminal=false
Categories=Utility;Application;
EOF

# --- Step 4: Install the Desktop Entry ---

echo "Copying the desktop entry to your Desktop..."
mkdir -p "$HOME/Desktop"
cp "$TEMP_DESKTOP" "$DESKTOP_DEST"

echo "Installation complete!"
echo "You can now launch the Mai Bloom Welcome App from the Desktop or by running:"
echo "   $INSTALL_SCRIPT"

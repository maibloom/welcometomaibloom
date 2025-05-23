#!/bin/bash
set -euo pipefail

# Determine the directory where the script is located
SCRIPT_DIR="$(dirname "$(realpath "$0")")"

# List of required files and validate their existence
REQUIRED_FILES=("welcometomaibloom.py" "welcometomaibloom.desktop" "logo.png")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$SCRIPT_DIR/$file" ]; then
        echo "Error: Required file '$file' not found in '$SCRIPT_DIR'" >&2
        exit 1
    fi
done

# Create the necessary directories:
# - Application files: /usr/bin/welcometomaibloom (for executables)
# - Desktop entry: /usr/share/applications
# - Supporting resources: /usr/share/welcometomaibloom (for images and other assets)
sudo mkdir -p /usr/bin/welcometomaibloom
sudo mkdir -p /usr/share/applications
sudo mkdir -p /usr/share/welcometomaibloom

# Set permissions and copy the Python executable
chmod +x "$SCRIPT_DIR/welcometomaibloom.py"
sudo cp "$SCRIPT_DIR/welcometomaibloom.py" /usr/bin/welcometomaibloom/

# Copy the logo to the appropriate shared resource folder instead of the binary directory
sudo cp "$SCRIPT_DIR/logo.png" /usr/share/welcometomaibloom/

# Adjust the desktop file permissions if needed and copy it
chmod +x "$SCRIPT_DIR/welcometomaibloom.desktop"
sudo cp "$SCRIPT_DIR/welcometomaibloom.desktop" /usr/share/applications/

# Determine the current user for desktop placement by checking SUDO_USER
if [[ -n "${SUDO_USER:-}" ]]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    USER_HOME="$HOME"
fi

# Check if the Desktop directory exists, then copy the .desktop file there for convenience
DESKTOP_DIR="$USER_HOME/Desktop"
if [ -d "$DESKTOP_DIR" ]; then
    cp "$SCRIPT_DIR/welcometomaibloom.desktop" "$DESKTOP_DIR/"
else
    echo "Warning: Desktop directory not found for user. Skipping desktop icon installation."
fi

# Update the desktop database so that the new application is registered
sudo update-desktop-database /usr/share/applications

echo "Installation completed!"

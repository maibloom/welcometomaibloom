#!/bin/bash
set -euo pipefail
sudo chmod +x *
sudo mkdir -p /usr/local/bin/welcometomaibloom
sudo mkdir -p /usr/local/share/welcometomaibloom
sudo mkdir -p /usr/share/applications/
chmod +x welcometomaibloom.desktop
chmod +x welcometomaibloom.py
sudo cp welcometomaibloom.py /usr/local/bin/welcometomaibloom
sudo cp logo.png /usr/local/share/welcometomaibloom/logo.png
sudo sed -i 's|Icon=/usr/local/bin/welcometomaibloom/logo.png|Icon=/usr/local/share/welcometomaibloom/logo.png|' welcometomaibloom.desktop
sudo cp welcometomaibloom.desktop /usr/share/applications/
if [[ -n "${SUDO_USER:-}" ]]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    USER_HOME="$HOME"
fi
sudo cp welcometomaibloom.desktop "$USER_HOME/Desktop"
sudo update-desktop-database /usr/share/applications/
echo "Installation completed!"

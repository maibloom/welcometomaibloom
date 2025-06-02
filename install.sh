#!/bin/bash
set -euo pipefail

USER_HOME=$(eval echo "~${SUDO_USER}")
sudo chmod +x welcometomaibloom.py
sudo mkdir -p /usr/local/bin/welcometomaibloom
sudo cp welcometomaibloom.py /usr/local/bin/welcometomaibloom/
sudo cp logo.png /usr/local/bin/welcometomaibloom/
sudo cp welcometomaibloom.desktop /usr/share/applications/
sudo cp welcometomaibloom.desktop "$USER_HOME/Desktop/"
sudo -u "$SUDO_USER" chmod +x "$USER_HOME/Desktop/welcometomaibloom.desktop"
sudo update-desktop-database /usr/share/applications/
echo "Installation completed!"

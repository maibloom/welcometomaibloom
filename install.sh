#!/bin/bash
set -euo pipefail

sudo chmod +x *
sudo cp welcometomaibloom.py /usr/local/bin/welcometomaibloom
sudo cp logo.png /usr/local/bin/welcometomaibloom

sudo cp welcometomaibloom.desktop /usr/share/applications/
sudo update-desktop-database /usr/share/applications/

echo "Installation completed!"

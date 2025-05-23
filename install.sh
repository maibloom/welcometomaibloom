#!/usr/bin/env bash
set -euo pipefail

APP_NAME=welcometomaibloom
INSTALL_DIR=/opt/$APP_NAME
BIN_LINK=/usr/bin/$APP_NAME
ICON_SIZE=256x256
ICON_DIR=/usr/share/icons/hicolor/$ICON_SIZE/apps
DESKTOP_DIR=/usr/share/applications

# 1. Build install dirs
sudo mkdir -p "$INSTALL_DIR"
sudo mkdir -p "$ICON_DIR"
sudo mkdir -p "$DESKTOP_DIR"

# 2. Make only your app files executable
chmod +x welcometomaibloom.py

# 3. Copy app files
sudo cp welcometomaibloom.py "$INSTALL_DIR/$APP_NAME"
sudo cp logo.png "$ICON_DIR/$APP_NAME.png"

# 4. Install wrapper script
cat << 'EOF' | sudo tee "$INSTALL_DIR/$APP_NAME-wrapper" > /dev/null
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/$APP_NAME" "$@"
EOF
sudo chmod +x "$INSTALL_DIR/$APP_NAME-wrapper"

# 5. Symlink into /usr/bin
sudo ln -sf "$INSTALL_DIR/$APP_NAME-wrapper" "$BIN_LINK"

# 6. Install .desktop
sed \
  -e "s|Exec=.*|Exec=$BIN_LINK|" \
  -e "s|Icon=.*|Icon=$APP_NAME|" \
  welcometomaibloom.desktop \
  | sudo tee "$DESKTOP_DIR/$APP_NAME.desktop" > /dev/null \
&& sudo chmod +x "$DESKTOP_DIR/$APP_NAME.desktop"

# 7. Update desktop database (if available)
if command -v update-desktop-database &> /dev/null; then
  sudo update-desktop-database "$DESKTOP_DIR"
fi

# 8. Optionally copy to user’s Desktop
if [[ -n "${SUDO_USER:-}" ]]; then
  USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
  USER_HOME="$HOME"
fi

if [[ -d "$USER_HOME/Desktop" ]]; then
  cp "$DESKTOP_DIR/$APP_NAME.desktop" "$USER_HOME/Desktop/"
  chmod +x "$USER_HOME/Desktop/$APP_NAME.desktop"
  chown "$SUDO_USER":"$SUDO_USER" "$USER_HOME/Desktop/$APP_NAME.desktop"
fi

echo "Installation of $APP_NAME complete!"
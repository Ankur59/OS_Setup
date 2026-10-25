#!/bin/sh
# Installs chatter-fix as a background service that starts on every boot.
set -e
[ "$(id -u)" -eq 0 ] || { echo "Run with: sudo ./install.sh"; exit 1; }
cd "$(dirname "$0")"
python3 -c "import evdev" || apt-get install -y python3-evdev
install -m 755 chatter-fix.py /usr/local/bin/chatter-fix
install -m 644 chatter-fix.service /etc/systemd/system/chatter-fix.service
systemctl daemon-reload
systemctl enable chatter-fix.service
systemctl restart chatter-fix.service
sleep 1
systemctl --no-pager status chatter-fix.service | head -15
echo
echo "Installed. Logs:      journalctl -u chatter-fix -f"
echo "Remove completely:    sudo ./uninstall.sh"

#!/bin/sh
# Stops chatter-fix and removes every file it installed.
set -e
[ "$(id -u)" -eq 0 ] || { echo "Run with: sudo ./uninstall.sh"; exit 1; }
systemctl disable --now chatter-fix.service 2>/dev/null || true
rm -f /etc/systemd/system/chatter-fix.service /usr/local/bin/chatter-fix
rm -f /etc/rsyslog.d/00-drop-hid-spam.conf /etc/systemd/journald.conf.d/size.conf
systemctl daemon-reload
systemctl restart rsyslog systemd-journald
echo "chatter-fix removed. Keyboard is back to its original behaviour."

#!/bin/sh
# Installs chatter-fix as a background service that starts on every boot.
set -e
[ "$(id -u)" -eq 0 ] || { echo "Run with: sudo ./install.sh"; exit 1; }
cd "$(dirname "$0")"
python3 -c "import evdev" || apt-get install -y python3-evdev
install -m 755 chatter-fix.py /usr/local/bin/chatter-fix
install -m 644 chatter-fix.service /etc/systemd/system/chatter-fix.service

# Safety nets: a keyboard dongle stuck in a bad state can make the kernel
# print "control queue full" tens of thousands of times a second, which
# once filled the whole disk through syslog/kern.log. Never write that
# message to /var/log, and keep the journal small no matter what.
cat > /etc/rsyslog.d/00-drop-hid-spam.conf <<'EOF'
# Written by chatter-fix/install.sh: never log this kernel flood.
:msg, contains, "control queue full" stop
EOF
mkdir -p /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/size.conf <<'EOF'
# Written by chatter-fix/install.sh: cap the journal so it can't fill the disk.
[Journal]
SystemMaxUse=500M
EOF
systemctl restart rsyslog systemd-journald

systemctl daemon-reload
systemctl enable chatter-fix.service
systemctl restart chatter-fix.service
sleep 1
systemctl --no-pager status chatter-fix.service | head -15
echo
echo "Installed. It runs silently (no logs)."
echo "Remove completely:    sudo ./uninstall.sh"

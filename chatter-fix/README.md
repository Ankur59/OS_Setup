# chatter-fix

Drops the phantom second press of the **E** key on the Hydra 10
keyboard, which sometimes registers one press twice ("key chatter").
Works in both modes: 2.4 GHz dongle (`3554:fa09`, "Compx Hydra 10") and
wired (`258a:010c`, "BY Tech Hydra 10").

A press of E that arrives within 50 ms of the previous E release is
treated as chatter and dropped. Real double presses ("seen", "free") are
slower than that and pass through. Every other key, the laptop keyboard
and the mouse are untouched. If the service stops or crashes, the
keyboard goes back to normal on its own.

It only reads from the keyboard and never sends anything to it, so the
Caps/Num lock lights on the Hydra may stay off (the locks themselves work).
Earlier versions mirrored those lights both ways, which could loop while
the keyboard slept and flood the kernel log with "control queue full"
until the disk was full. The service is silent: it writes no logs.

## Install (starts on every boot)

```bash
sudo ./install.sh
```

Besides the service, this adds two safety nets so a log flood can never
fill the disk again: `/etc/rsyslog.d/00-drop-hid-spam.conf` (drops
"control queue full" from syslog/kern.log) and
`/etc/systemd/journald.conf.d/size.conf` (journal capped at 500 MB).

## Check

```bash
systemctl status chatter-fix
```

To see what it does, stop the service and run it by hand with `--verbose`:

```bash
sudo systemctl stop chatter-fix
sudo ./chatter-fix.py --verbose
```

## Tune

Measure the gap of the unwanted press (stop the service first):

```bash
sudo systemctl stop chatter-fix
sudo ./chatter-fix.py --monitor
```

Then change `--threshold-ms` (and `--keys`, e.g. `--keys KEY_E KEY_R`) in
`/etc/systemd/system/chatter-fix.service` and run:

```bash
sudo systemctl daemon-reload && sudo systemctl restart chatter-fix
```

## Uninstall

```bash
sudo ./uninstall.sh
```

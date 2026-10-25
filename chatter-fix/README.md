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

## Install (starts on every boot)

```bash
sudo ./install.sh
```

## Check / logs

```bash
systemctl status chatter-fix
journalctl -u chatter-fix -f
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

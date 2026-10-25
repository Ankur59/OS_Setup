#!/usr/bin/env python3
"""
chatter-fix: drop the phantom second press of a key that "chatters"
(registers twice) on the Hydra 10 keyboard, wireless or wired.

How it works
  * Finds the keyboard's input devices by USB id: 3554:fa09 ("Compx
    Hydra 10", 2.4 GHz dongle) or 258a:010c ("BY Tech Hydra 10", cable).
  * Grabs them exclusively and re-emits key events through a virtual
    keyboard (uinput), so the rest of the system sees a normal keyboard.
  * For the chosen keys only (default: E), a press that arrives within
    --threshold-ms of that key's previous release is treated as chatter
    and dropped, together with its matching release.

Safety
  * Every other key, and the laptop's built-in keyboard, are untouched.
  * If this program stops or crashes for any reason, the kernel releases
    the grab automatically and the keyboard works exactly as before.
  * Unplugging/replugging the dongle is handled (rescans every 2 s).
  * Nothing is ever sent TO the keyboard. Caps/Num lock LEDs are not
    mirrored: the old two-way LED mirroring (real keyboard <-> virtual
    keyboard) could loop while the keyboard was asleep, flooding the
    kernel log with "control queue full" until the disk filled up.
  * Silent by default: nothing is logged unless --verbose is given.

Modes
  chatter-fix.py                 run the filter (needs root)
  chatter-fix.py --monitor       only watch and print timings for the
                                 chosen keys, no filtering (needs root)
"""

import argparse
import logging
import os
import selectors
import signal
import sys
import time

import evdev
from evdev import InputDevice, UInput, ecodes

KEYBOARD_IDS = {
    (0x3554, 0xFA09),  # Compx Hydra 10 (2.4 GHz dongle)
    (0x258A, 0x010C),  # BY Tech Hydra 10 (wired)
}
VIRTUAL_NAME_PREFIX = "chatter-fix: "
RESCAN_SECONDS = 2.0
KEY_PRESS, KEY_RELEASE = 1, 0

log = logging.getLogger("chatter-fix")


class Debouncer:
    """Decides, per key event, whether it should reach the system."""

    def __init__(self, keys, threshold_s):
        self.keys = keys
        self.threshold_s = threshold_s
        self.last_release = {}   # key code -> timestamp of last release
        self.suppressed = set()  # keys whose current press was dropped

    def allow(self, code, value, t):
        if code not in self.keys:
            return True

        if value == KEY_PRESS:
            last = self.last_release.get(code)
            gap = None if last is None else t - last
            if gap is not None and 0 <= gap < self.threshold_s:
                self.suppressed.add(code)
                log.debug("dropped %s press, %.1f ms after release",
                          ecodes.KEY[code], gap * 1000)
                return False
            return True

        if value == KEY_RELEASE:
            # Recording dropped releases too keeps a whole burst of
            # bounces inside the window instead of just the first one.
            self.last_release[code] = t
            if code in self.suppressed:
                self.suppressed.discard(code)
                return False
            return True

        # Autorepeat (value 2): only pass it for a press we let through.
        return code not in self.suppressed


# Event types never copied to the virtual keyboard. SYN is implicit, FF
# needs a feedback loop we don't provide, REP would make the kernel add
# its own repeats on top of the forwarded ones, and LED is left out so the
# desktop has no LEDs to write to the virtual keyboard and the real
# keyboard's LED echoes are never fed back in.
SKIPPED_TYPES = (ecodes.EV_SYN, ecodes.EV_FF, ecodes.EV_REP, ecodes.EV_LED)


def capabilities_for_virtual(dev):
    caps = dev.capabilities(absinfo=True)
    for t in SKIPPED_TYPES:
        caps.pop(t, None)
    return caps


def wait_until_no_keys_held(dev, timeout_s=5.0):
    """Grabbing while a key is held would leave that key stuck down."""
    deadline = time.monotonic() + timeout_s
    while dev.active_keys() and time.monotonic() < deadline:
        time.sleep(0.05)


class FilteredDevice:
    def __init__(self, dev, debouncer):
        self.dev = dev
        self.debouncer = debouncer
        self.ui = UInput(capabilities_for_virtual(dev),
                         name=VIRTUAL_NAME_PREFIX + dev.name,
                         phys="chatter-fix/" + (dev.phys or dev.path))
        wait_until_no_keys_held(dev)
        dev.grab()

    def pump_input(self):
        for ev in self.dev.read():
            if ev.type == ecodes.EV_LED:
                continue
            if ev.type == ecodes.EV_KEY and not self.debouncer.allow(
                    ev.code, ev.value, ev.timestamp()):
                continue
            self.ui.write_event(ev)

    def close(self):
        for action in (self.dev.ungrab, self.dev.close, self.ui.close):
            try:
                action()
            except OSError:
                pass


def find_keyboard_devices(keys):
    found = []
    for path in evdev.list_devices():
        try:
            dev = InputDevice(path)
        except OSError:
            continue
        info = dev.info
        if ((info.vendor, info.product) in KEYBOARD_IDS
                and not dev.name.startswith(VIRTUAL_NAME_PREFIX)
                and keys & set(dev.capabilities().get(ecodes.EV_KEY, []))):
            found.append(dev)
        else:
            dev.close()
    return found


def run_filter(keys, threshold_s):
    debouncer = Debouncer(keys, threshold_s)
    sel = selectors.DefaultSelector()
    active = {}         # device path -> FilteredDevice
    failed_paths = set()

    def drop(path):
        fd = active.pop(path, None)
        if fd is None:
            return
        try:
            sel.unregister(fd.dev)
        except (KeyError, ValueError, OSError):
            pass
        fd.close()
        log.info("released %s", path)

    def rescan():
        for dev in find_keyboard_devices(keys):
            if dev.path in active:
                dev.close()
                continue
            try:
                fd = FilteredDevice(dev, debouncer)
            except OSError as e:
                if dev.path not in failed_paths:
                    log.warning("could not take over %s (%s): %s",
                                dev.path, dev.name, e)
                    failed_paths.add(dev.path)
                dev.close()
                continue
            failed_paths.discard(dev.path)
            active[dev.path] = fd
            sel.register(fd.dev, selectors.EVENT_READ, dev.path)
            log.info("filtering %s (%s)", dev.path, dev.name)

    log.info("keys: %s, threshold: %.0f ms",
             ", ".join(ecodes.KEY[k] for k in sorted(keys)), threshold_s * 1000)
    try:
        next_scan = 0.0
        while True:
            now = time.monotonic()
            if now >= next_scan:
                rescan()
                next_scan = now + RESCAN_SECONDS
            for key, _ in sel.select(timeout=RESCAN_SECONDS):
                path = key.data
                fd = active.get(path)
                if fd is None:
                    continue
                try:
                    fd.pump_input()
                except BlockingIOError:
                    pass
                except OSError as e:  # dongle unplugged, etc.
                    log.info("lost %s: %s", path, e)
                    drop(path)
    finally:
        for path in list(active):
            drop(path)


def run_monitor(keys):
    devices = find_keyboard_devices(keys)
    if not devices:
        sys.exit("Hydra 10 keyboard not found (is the dongle or cable plugged in?)")
    sel = selectors.DefaultSelector()
    for dev in devices:
        sel.register(dev, selectors.EVENT_READ)
        print(f"watching {dev.path} ({dev.name})")
    print("Press the problem key slowly, one press at a time. Ctrl+C to stop.\n"
          "A 'press' line with a small gap right after a release is chatter.\n")
    last_release = {}
    while True:
        for key, _ in sel.select():
            for ev in key.fileobj.read():
                if ev.type != ecodes.EV_KEY or ev.code not in keys or ev.value == 2:
                    continue
                t = ev.timestamp()
                name = ecodes.KEY[ev.code]
                if ev.value == KEY_PRESS:
                    last = last_release.get(ev.code)
                    gap = f"{(t - last) * 1000:8.1f} ms after last release" if last else ""
                    print(f"{name} press    {gap}")
                else:
                    last_release[ev.code] = t
                    print(f"{name} release")


def parse_keys(names):
    keys = set()
    for name in names:
        name = name.upper()
        if not name.startswith("KEY_"):
            name = "KEY_" + name
        code = ecodes.ecodes.get(name)
        if code is None:
            raise argparse.ArgumentTypeError(f"unknown key: {name}")
        keys.add(code)
    return keys


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--keys", nargs="+", default=["KEY_E"],
                   help="keys to debounce, e.g. --keys e r  (default: KEY_E)")
    p.add_argument("--threshold-ms", type=float, default=50,
                   help="drop a press this soon after the previous release (default: 50)")
    p.add_argument("--monitor", action="store_true",
                   help="only print timings, don't filter")
    p.add_argument("--verbose", action="store_true",
                   help="log what the filter does (silent otherwise)")
    args = p.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")
    else:
        logging.disable(logging.CRITICAL)
    try:
        keys = parse_keys(args.keys)
    except argparse.ArgumentTypeError as e:
        p.error(str(e))

    if os.geteuid() != 0:
        sys.exit("Needs root to read the keyboard: run with sudo.")

    # Turn SIGTERM (systemctl stop) into a normal exit so cleanup runs.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        if args.monitor:
            run_monitor(keys)
        else:
            run_filter(keys, args.threshold_ms / 1000)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

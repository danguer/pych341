import sys
import logging
from pych341.ch341 import CH341EppMem
from pych341.gpio import GPIOHandler, GPIOPin, GPIOLevel

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(filename)s::%(funcName)s %(message)s",
)

logger = logging.getLogger(__name__)

dev = CH341EppMem()
logger.info("Creating handler")
handler = GPIOHandler(dev)

# All input pins: GPIOPin values strictly less than ADDR (0x8000)
input_pins = {pin: False for pin in GPIOPin if pin.value < GPIOPin.ADDR}

# Build a lookup: lowercase pin name → GPIOPin
pin_by_name = {pin.name.lower(): pin for pin in input_pins}

while True:
    try:
        print("commands: write <pin_name> on|off  |  read")
        line = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        break

    if line.startswith("write "):
        parts = line.split()
        if len(parts) != 3 or parts[2] not in ("on", "off"):
            print("usage: write <pin_name> on|off")
            continue
        pin_name, state_str = parts[1], parts[2]
        if pin_name not in pin_by_name:
            print(f"unknown pin: {pin_name!r}. valid pins: {', '.join(pin_by_name)}")
            continue
        input_pins[pin_by_name[pin_name]] = state_str == "on"
        active = [(pin, GPIOLevel.HIGH) for pin, state in input_pins.items() if state]
        for pin, _ in active:
            handler.set_output(pin)

        handler.write(active)

    elif line == "read":
        for pin in input_pins:
            handler.set_input(pin)

        pins = handler.read()
        names = ", ".join(p.name for p in pins) if pins else "(none)"
        print(f"pins: {names}")

import sys
import logging
from pych341.ch341 import CH341EppMem
from pych341.spi import SPIHandler, SPIBitMode
from pych341.gpio import GPIOHandler
from time import sleep

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(filename)s::%(funcName)s %(message)s",
)

logger = logging.getLogger(__name__)

dev = CH341EppMem()
logger.info("Creating handler")
handler = SPIHandler(dev, SPIBitMode.MSB)
handler_gpio = GPIOHandler(dev)
base_i = 0
while True:
    # there is no such thing as CS under SPI handling
    # but if you want there is a quick method to toggle
    # pins D0-D5
    # for the blue board D0=CS0, D1=CS1 and D2=CS2
    # so this is just a quick example on how to toggle pins
    handler_gpio.write_d0d5(0)
    for i in range(7):
        mask = 1 << i
        logger.info("Writing gpio d0-d5: 0x%02x", mask)
        handler_gpio.write_d0d5(mask)
        sleep(0.5)

    data = bytes([i for i in range(base_i, base_i + 8)])
    logger.info("Writing data: %s", data.hex())
    data_read = handler.write(data)
    logger.info("Got data: %s", data_read.hex())
    base_i += 8
    if base_i >= 256:
        base_i = 0

    sleep(1)

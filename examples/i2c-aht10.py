import sys
import logging
from pych341.ch341 import CH341EppMem
from pych341.i2c import I2CHandler
from time import sleep

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(filename)s::%(funcName)s %(message)s",
)

logger = logging.getLogger(__name__)

# following are examples for AHT10
address = 0x38


def read_status(handler: I2CHandler) -> int:
    handler.begin_transmission(address)
    handler.write(0x71)
    # send data but not send stop
    handler.end_transmission(False)

    # read data
    handler.request_from(address, 1)
    while not handler.available():
        pass

    return handler.read()


def sensor_trigger_measurement(handler: I2CHandler):
    handler.begin_transmission(address)
    handler.write(0xAC)
    handler.write(0x33)
    handler.write(0x00)
    handler.end_transmission()


def read_sensor_data(handler: I2CHandler) -> tuple[int, float, float]:
    handler.request_from(address, 6)
    while handler.available() < 6:
        pass

    status = handler.read()

    # humidity is 20 bits
    uint_humidity = (handler.read() << 12) | (handler.read() << 4)

    # read temporary byte that have low 4 bits of humidity and high 4 bits of temperature
    tmp = handler.read()
    uint_humidity |= tmp >> 4

    # read temperature (20 bits)
    uint_temperature = ((tmp & 0xF) << 16) | (handler.read() << 8) | handler.read()

    # convert into float values, section 6 of the datasheet
    humidity = uint_humidity * 100.0 / 1048576.0
    temperature = (uint_temperature * 200.0) / 1048576.0 - 50.0

    return status, humidity, temperature


dev = CH341EppMem()
logger.info("Creating handler")
handler = I2CHandler(dev)
logger.info("Checking device's status")
status = read_status(handler)
logger.info("Status: %02X", status)

# for now avoid to check if needs warmup or not

while True:
    # send command to trigger meaurement
    sensor_trigger_measurement(handler)
    # sleep few ms to wait for measurement to be ready
    sleep(0.08)

    status, humidity, temperature = read_sensor_data(handler)
    logger.info(
        "Status: %02X, Humidity: %.2f%%, Temperature: %.2fC",
        status,
        humidity,
        temperature,
    )

    sleep(5)

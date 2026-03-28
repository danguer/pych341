from enum import IntEnum
import struct
from .ch341 import CH341DeviceBase
from .utils import get_formatted_hex
import logging

logger = logging.getLogger(__name__)


class I2CSpeed(IntEnum):
    I2C_SPEED_20K = 0  # low rate 20KHz
    I2C_SPEED_50K = 4  # 50KHz
    I2C_SPEED_100K = 1  # standard rate 100KHz
    I2C_SPEED_200K = 5  # 200KHz
    I2C_SPEED_400K = 2  # fast rate 400KHz
    I2C_SPEED_750K = 3  # high rate 750KHz
    I2C_SPEED_1M = 6  # 1MHz
    I2C_SPEED_2M = 7  # 2MHz


class I2CCmd(IntEnum):
    MODE_STREAM = 0xAA
    START = 0x74
    STOP = 0x75
    END = 0x00
    DIR_OUT = 0x80
    DIR_IN = 0xC0
    SETTING = 0x60


class I2CHandler:
    def __init__(
        self,
        device: CH341DeviceBase,
        speed: I2CSpeed = I2CSpeed.I2C_SPEED_100K,
    ):
        self.device = device
        self.buffer_tx_data = bytearray()
        self.buffer_rx_data = bytearray()
        self.buffer_rx_index = 0

        # send commands
        cmd = (
            I2CCmd.MODE_STREAM,
            I2CCmd.SETTING | speed,
            I2CCmd.END,
        )
        self.device.write(cmd)

    # api inspired by Arduino Wire library
    def begin_transmission(self, address: int):
        # shift left to make room for read/write bit
        self.buffer_tx_data += struct.pack("B", address << 1)

    def end_transmission(self, send_stop: bool = True):
        cmd = bytearray()
        cmd.append(I2CCmd.MODE_STREAM)
        cmd.append(I2CCmd.START)
        cmd.append(I2CCmd.DIR_OUT | len(self.buffer_tx_data))
        cmd += self.buffer_tx_data

        if send_stop:
            cmd.append(I2CCmd.STOP)

        cmd.append(I2CCmd.END)

        logger.debug("RX DATA: %s", get_formatted_hex(self.buffer_tx_data))
        self.buffer_tx_data = bytearray()
        logger.debug("Write CMD: %s", get_formatted_hex(cmd))
        self.device.write(cmd)

    def write(self, byte: int):
        self.buffer_tx_data += struct.pack("B", byte)

    def request_from(self, address: int, length: int):
        cmd = (
            I2CCmd.MODE_STREAM,
            I2CCmd.START,
            # send address
            I2CCmd.DIR_OUT | 1,
            (address << 1) | 0x01,  # set read bit ,
            I2CCmd.DIR_IN | length,
            I2CCmd.STOP,
            I2CCmd.END,
        )

        self.device.write(cmd)
        data = self.device.read(length)
        self.buffer_rx_data += data
        logger.debug("Read CMD: %s", get_formatted_hex(cmd))
        logger.debug("Read data: %s", get_formatted_hex(data))

    def available(self) -> int:
        return len(self.buffer_rx_data) - self.buffer_rx_index

    def read(self) -> int:
        if self.buffer_rx_index >= len(self.buffer_rx_data):
            raise ValueError("No more data available")

        byte = self.buffer_rx_data[self.buffer_rx_index]
        self.buffer_rx_index += 1

        # drain buffer if all data has been read
        if self.buffer_rx_index >= len(self.buffer_rx_data):
            self.buffer_rx_data = bytearray()
            self.buffer_rx_index = 0

        return byte

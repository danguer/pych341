from enum import IntEnum
from typing import Tuple, List
import struct

from .ch341 import CH341DeviceBase
from .utils import get_formatted_hex
import logging

logger = logging.getLogger(__name__)


class GPIOCmd(IntEnum):
    OUTPUT = 0xA1
    INPUT = 0xA0
    CMD_W0 = 0xA6

    # fmt: off
    UIO_STREAM     = 0xAB
    UIO_DIR        = 0x40
    UIO_OUT        = 0x80
    UIO_STREAM_END = 0x20
    # fmt: on


class GPIOLevel(IntEnum):
    LOW = 0
    HIGH = 1


class GPIOPin(IntEnum):
    # bits 0-7
    GPIO_0 = 0x1
    GPIO_1 = 0x2
    GPIO_2 = 0x4
    GPIO_3 = 0x8
    GPIO_4 = 0x10
    GPIO_5 = 0x20
    GPIO_6 = 0x40
    GPIO_7 = 0x80

    # bits 8-15
    # fmt: off
    ERR    = 0x100
    PEMP   = 0x200
    INT    = 0x400
    SLCT   = 0x800
    # TODO what is PIN 12
    WAIT   = 0x2000
    # DS pin
    READ   = 0x4000
    # AS pin
    ADDR   = 0x8000

    # bits 16-23
    RESET  = 0x10000    # OUTPUT, NOT WORKING
    WRITE  = 0x20000    # OUTPUT
    SCL    = 0x40000    # OUTPUT
    # TODO what is PIN 19-28

    # bits 24-31
    SDA    = 0x20000000 # OUTPUT
    # TODO in theory there should be 32 GPIO possible pins
    # that is why also enable is 8 bits
    # fmt: on


WriteData = Tuple[GPIOPin, GPIOLevel]


class GPIOHandler:
    def __init__(self, device: CH341DeviceBase):
        self.device = device
        self.reset()

    def reset(self):
        self.enable = self.direction = 0

    def _set_enable(self, pin: GPIOPin):
        # according to library:
        # BIT0 High :	effect on Bit15~8 of DATA OUT
        # BIT1 High :	effect on Bit15~8 of DIR
        # BIT2 High :	effect on Bit7~0 of DATA OUT
        # BIT3 High :	effect on Bit7~0 of DIR
        # BIT4 High :	effect on Bit23~16 of DATA OUT
        # NOT mentioned but...
        # BIT5 High :	effect on Bit23~16 of DIR
        # BIT6 High :	effect on Bit31~24 of DATA OUT
        # BIT7 High :	effect on Bit31~24 of DIR

        if pin.value & 0xFF:
            self.enable |= 0xC
        elif pin.value & 0xFF00:
            self.enable |= 0x3
        elif pin.value & 0xFF0000:
            self.enable |= 0x10
        elif pin.value & 0xFF000000:
            # there is no BIT7 as always is output
            self.enable |= 0x40

    def set_output(self, pin: GPIOPin):
        self.direction |= pin.value
        self._set_enable(pin)

    def set_input(self, pin: GPIOPin):
        self.direction &= ~pin.value
        self._set_enable(pin)

    def write_d0d5(self, data: int):
        # there is a special command for writing only d0-d5 mask
        cmd = bytearray()
        cmd.append(GPIOCmd.UIO_STREAM)
        cmd.append(GPIOCmd.UIO_DIR | 0x3F)  # set d0-d5 as output
        cmd.append(GPIOCmd.UIO_OUT | (data & 0x3F))  # send data
        cmd.append(GPIOCmd.UIO_STREAM_END)

        logger.debug("Write CMD: %s", get_formatted_hex(cmd))
        self.device.write(cmd)

    def write(self, data: List[WriteData]):
        data_out = 0
        for pin, level in data:
            if level == GPIOLevel.HIGH:
                data_out |= pin.value

        cmd = bytearray()
        cmd.append(GPIOCmd.OUTPUT)
        cmd.append(0x6A)

        logger.debug("Enable bits: %02X", self.enable)

        # first is enable bits
        cmd += struct.pack("B", self.enable)
        # next goes in the same order as enable bits, needs to send all

        # bits 15~8
        cmd += struct.pack("B", (data_out >> 8) & 0xFF)
        cmd += struct.pack("B", (self.direction >> 8) & 0xFF)

        # bits 7~0
        cmd += struct.pack("B", data_out & 0xFF)
        cmd += struct.pack("B", self.direction & 0xFF)

        # bits 23~16
        cmd += struct.pack("B", (data_out >> 16) & 0xFF)
        cmd.append(0x00)  # direction is always output

        # bits 31~24
        cmd += struct.pack("B", (data_out >> 24) & 0xFF)
        cmd.append(0x00)  # direction is always output

        logger.debug("Write CMD: %s", get_formatted_hex(cmd))
        self.device.write(cmd)

    def _get_pins_for_byte(
        self,
        pins: list,
        byte: int,
        shift_bits: int = 0,
    ) -> List[GPIOPin]:
        if shift_bits:
            byte = byte << shift_bits

        for i in range(8):
            shift = shift_bits + i
            mask = 1 << shift
            if byte & mask:
                try:
                    pins.append(GPIOPin(mask))
                except ValueError:
                    pass

    def read(self) -> List[GPIOPin]:
        cmd = bytearray()
        cmd.append(GPIOCmd.INPUT)
        self.device.write(cmd)

        data = self.device.read(6)
        pins = []
        self._get_pins_for_byte(pins, data[0])
        self._get_pins_for_byte(pins, data[1], 8)

        # data[2] and data[3] are output pins, others are unknown
        logger.debug("GOT DATA: %s, pins: %s", get_formatted_hex(data), pins)

        return pins

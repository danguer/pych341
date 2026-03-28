import usb.core
import usb.util
from abc import ABC
import logging

logger = logging.getLogger(__name__)


class CH341DeviceBase(ABC):
    def _init_device(self, id_product: int):
        dev = usb.core.find(idVendor=0x1A86, idProduct=id_product)
        if dev is None:
            raise ValueError("CH34x device is not connected")

        self.device = dev
        self.timeout = 100
        self.ep_out: usb.core.Endpoint = None
        self.ep_in: usb.core.Endpoint = None
        interface_number = None

        for cfg in dev:
            for intf in cfg:
                for ep in intf:
                    # check if is out or in
                    if (
                        usb.util.endpoint_direction(ep.bEndpointAddress)
                        == usb.util.ENDPOINT_OUT
                        and usb.util.endpoint_type(ep.bmAttributes)
                        == usb.util.ENDPOINT_TYPE_BULK
                    ):
                        self.ep_out = ep
                        interface_number = intf.bInterfaceNumber
                        logger.info("Found OUT endpoint: %s", ep)
                    elif (
                        usb.util.endpoint_direction(ep.bEndpointAddress)
                        == usb.util.ENDPOINT_IN
                        and usb.util.endpoint_type(ep.bmAttributes)
                        == usb.util.ENDPOINT_TYPE_BULK
                    ):
                        self.ep_in = ep
                        interface_number = intf.bInterfaceNumber
                        logger.info("Found IN endpoint: %s", ep)

        if not self.ep_out or not self.ep_in:
            raise ValueError("Failed to find endpoints for device")

        # remove kernel driver if needed
        if dev.is_kernel_driver_active(interface_number):
            logger.debug("Detaching kernel driver from interface %d", interface_number)
            dev.detach_kernel_driver(interface_number)

    def write(self, data: bytes) -> int:
        ret = self.ep_out.write(data, self.timeout)
        if ret != len(data):
            logger.error("Failed to write data to device")
            raise ValueError("Failed to write data to device")

        return ret

    def read(self, size: int) -> bytes:
        return bytes(self.ep_in.read(size, self.timeout))


class CH341EppMem(CH341DeviceBase):
    def __init__(self):
        self._init_device(0x5512)

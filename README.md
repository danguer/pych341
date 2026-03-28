# CH341 and Python

The goal of this project is to use a CH341 board (blue board) with Python and to learn a bit of
USB programming. The datasheet is not very helpful, but there is some source code available
(which also references the CH347, making it more confusing).
This chip has been reverse engineered extensively, so there are good examples around, but so far only
in C. This project uses Python to provide a simpler way to test and experiment.

Each protocol is isolated in its own module under `src/pych341`:
- `ch341.py` handles USB discovery and communication
- `gpio.py`, `i2c.py`, and `spi.py` handle GPIO (`D0-D7` input/output pins), I2C, and SPI respectively

For now this is more a proof-of-concept than anything (it won't check for overflows for example)

## Running examples

Simple way is to create a venv, install requirements and run from top folder:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# run examples
PYTHONPATH=`pwd`/src python3 examples/spi-echo.py
```

## udev Permissions

Create the following file: `/etc/udev/rules.d/99-ch341-udev.rules`
```
ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="55*", MODE:="0666", ENV{ID_MM_DEVICE_IGNORE}="1", ENV{ID_MM_PORT_IGNORE}="1"
```

restart udev:
```
udevadm control --reload-rules && udevadm trigger
```

This will allow to run the examples without being superuser

## Resources:
* [Datasheet](https://www.wch-ic.com/downloads/CH341DS1_PDF.html) no data about USB communication
* [Linux Examples](https://github.com/WCHSoftGroup/ch34x_mphsi_master_linux) usb communication in linux
* [Driver and Kernel module](https://github.com/WCHSoftGroup/ch341par_linux)
* [Old Driver and Kernel module with source code](https://github.com/zoobab/ch341-parport)
* [Linux Driver](https://github.com/frank-zago/ch341-i2c-spi-gpio)
* [CH341 Resources](https://github.com/boseji/CH341-Store)
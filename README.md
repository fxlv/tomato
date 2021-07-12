# tomato


## Development and Testing

The script is meant to be run on a RaspberryPi and with an Arduino board connected.
Therefore these two conditions have to be accounted for.

In order to develop on a non RPi, you need to simulate a virtual serial port and mock the GPIO interface.
GPIO mocking is done in the script during import time, however for serial port you could use [PyVirtualSerialPorts](https://github.com/ezramorris/PyVirtualSerialPorts).

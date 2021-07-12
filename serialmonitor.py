import serial
import random
import time
import datetime
import os
import click
from loguru import logger
import sys
import json
import subprocess

try:
    import RPi.GPIO as GPIO
except:
    # support for developing and testing outside of RPI environment
    import Mock.GPIO as GPIO

last_pump_time = None

def set_up_logger(debug=False, log_file_name="tomato.log"):
    logger.remove()  # remove the default logger output
    logger.add(log_file_name, rotation="10 MB", retention="1 week", compression="zip")  # always log to a file
    logger.add(sys.stderr, level="WARNING")
    logger.info("Logging started")
    if debug:
        logger.add(sys.stdout, level="DEBUG")
        logger.debug("DEBUG Logging started.")

def zabbix_sender(settings, value):
    zabbix_server = settings["zabbix_server_name"]
    zabbix_server_port = settings["zabbix_server_port"]
    zabbix_host_name = settings["zabbix_host_name"]
    zabbix_item_name = settings["zabbix_item_name"]
    command = ["zabbix_sender", "-z", zabbix_server, "-p", zabbix_server_port, "-s", f"\"{zabbix_host_name}\"", "-k", zabbix_item_name, "-o", str(value), "-vv"]
    logger.debug(f"Sending: {command}")
    subprocess.run(command)


def pump(settings, pump_time=2):
    now = datetime.datetime.now()
    global last_pump_time
    logger.debug(f"Preparing to pump. Last pump time {last_pump_time}")
    pump_pin = settings["pump_pin"]
    if last_pump_time:
        if ( now - last_pump_time ).total_seconds() < 1200:
            logger.debug("Not enough time passed since last watering")
            zabbix_sender(settings, 0)
            return 0
    last_pump_time= datetime.datetime.now()
    zabbix_sender(settings, 1)
    logger.debug(f"Setting pump pin {pump_pin} to HIGH")
    GPIO.output(pump_pin, GPIO.HIGH)
    time.sleep(pump_time);
    logger.debug("sleep")
    time.sleep(pump_time);
    GPIO.output(pump_pin, GPIO.LOW)
    logger.debug("Pump complete")
    zabbix_sender(settings, 1)
    time.sleep(3)

def timer_logic():
    logger.warning("serial closed, that is not good, falling back to primitive timer approach")
    if not last_pump_time:
        logger.debug("we have never pumped? ok, let' s do it")
        pump(2)
    now = datetime.datetime.now()
    delta = now - last_pump_time
    delta = delta.total_seconds()
    if delta > 300:
        logger.debug("Too long without water")
        pump()


def load_settings_from_file():
    if os.path.exists("settings.json"):
        with open("settings.json") as settings_file:
            settings = json.load(settings_file)
            return settings
    return None

def set_up_gpio(settings):
    logger.debug("Setting up GPIO")
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(settings["pump_pin"], GPIO.OUT)
    GPIO.output(settings["pump_pin"], GPIO.LOW)

@click.command()
@click.option("--debug", is_flag=True, default=False, help="Print DEBUG log to screen")
def main(debug):
    settings = load_settings_from_file()
    set_up_logger(debug)
    set_up_gpio(settings)
    last_successful_serial_comm = None
    startup_time = datetime.datetime.now()

    ser = serial.Serial(settings["serial_port"], 9600, timeout=3)
    while True:
        d_startup = (datetime.datetime.now() - startup_time).total_seconds()
        if not last_successful_serial_comm and d_startup > 35:
            logger.warning("No success communicating over serial for over 15sec, falling back to timer logic")

        if ser.is_open:
            logger.debug("Serial port is open")
            line = ser.read(50)
            line = line.decode("utf-8")
            line = line.split("\r\n")
            # if multiple lines were read, use the first one
            if len(line)>1:
                line = line[0]
            # extract the overflow and soil_moisture_level reading, which are whitespace delimeted
            logger.debug(f"Line: {line}")
            if isinstance(line, str):
                line = line.split(" ")
                logger.debug(f"Line extracted: {line}")
            else:
                continue
                ## something wrong was read from serial, skip it
            # now we have something like this: ['Digital:0', 'soil_moisture_level:256']
            # we further extract the values of overflow and soil_moisture_level
            try:
                # soil_moisture_level water_tank_level overflow
                logger.debug(f"Line: {line}")
                if not isinstance(line, list):
                    logger.debug("Line is not a list, ignoring")
                    overflow = 0
                    soil_moisture_level = 0
                    water_tank_level = 0
                    continue
                soil_moisture_level = int(line[0])
                water_tank_level = int(line[1])
                overflow = int(line[2])


                last_successful_serial_comm = datetime.datetime.now()
                logger.debug("Writing stats to info files")
                with open("/tmp/soil.info", "w") as soilfile:
                    soilfile.write(str(soil_moisture_level))
                with open("/tmp/water_tank.info", "w") as watertankfile:
                    watertankfile.write(str(water_tank_level))
                with open("/tmp/overflow.info", "w") as overflowfile:
                    overflowfile.write(str(overflow))

            except (IndexError):
                logger.warning("Could not extract values, ignoring")
                overflow = 0
                soil_moisture_level = 0
                water_tank_level = 0

            if int(overflow) == 0:
                logger.debug("No overflow detected")
                if water_tank_level < 50:
                    logger.warning(f"Water is low: {water_tank_level}")
                else:
                    if soil_moisture_level < settings["max_humidity"]:
                        if soil_moisture_level < settings["desired_humidity"]:
                            logger.debug(f"Moisture below the desired value: ({soil_moisture_level}), watering")
                            pump(settings, 6)
                        elif soil_moisture_level > settings["desired_humidity"]:
                            logger.info(f"Moisture is above the desired humidity ({soil_moisture_level}), but below max. Minimum watering.")
                            pump(settings, 2)
                    else:
                        logger.info(f"Moisture above max humidity: {soil_moisture_level}")
            else:
                logger.warning(f"Overflow detected (overflow == {overflow})")
        else:
            timer_logic()

if __name__ == "__main__":
    main()




        


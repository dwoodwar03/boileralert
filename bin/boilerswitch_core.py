#!/usr/bin/env python3

import time
import logging
import logging.handlers

from alert import Alert
from config import Config
from gpio import Monitor

def run_checker(config_file):

    cfg = Config(config_file)

    # Variables
    last_month = time.localtime().tm_mday  # Current Day of month as read on previous cycle.  Used to trigger Daily Stats reset.
    last_hour = time.localtime().tm_hour  # Current Hour as read on previous cycle.  Used to trigger logging of stats.

    # Configure Logging
    my_logger = logging.getLogger("MyLogger")
    my_logger.setLevel(logging.DEBUG)

    handler = logging.handlers.SysLogHandler(address='/dev/log')

    my_logger.addHandler(handler)

    log_format = '%(filename)s: %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(fmt=log_format))

    monitor = Monitor(cfg.gpio_pin, my_logger)
    alerter = Alert(cfg)

    # Set Last Pin State to current Pin State
    # This avoids a mail being sent every time the program restarts. (Not normally a problem unless a error condition occurs where the
    # program constantly restarts)
    last_pin_state = monitor.get_reading()
    my_logger.info(f"Program Starting.....")
    my_logger.info(f"-- with Pin State of        {last_pin_state}")
    my_logger.info(f"-- with timeframe of        {3600 / 3600} Hours") # TODO CONFIG
    my_logger.info(f"-- max emails per timeframe {14}") # TODO CONFIG
    my_logger.info(f"-- Time between checks      {cfg.sleep_time}   Seconds")
    my_logger.info(f"-- Recipients               {cfg.sendto}")

    while True:
        pin_state = monitor.get_reading()
        month = time.localtime().tm_mday
        hour  = time.localtime().tm_hour

        if pin_state:
            # Button is not pressed
            if last_pin_state != pin_state:
                my_logger.info("Boiler Fault Cleared")
                alerter.send_clear()
        else:
            # Button is pressed
            if last_pin_state != pin_state:
                my_logger.info("Boiler Fault ACTIVE")
                alerter.send_fault()

        if last_hour != hour:
            monitor.log_stats()

        if last_month != month:
            monitor.reset_daily_stats()

        last_pin_state = pin_state
        last_hour = hour
        last_month = month

        time.sleep(cfg.sleep_time)

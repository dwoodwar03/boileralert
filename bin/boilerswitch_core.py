#!/usr/bin/env python3

import time
import logging
import logging.handlers

import gpio

from alert import Alert
from config import Config

def run_checker(config_file):

    cfg = Config(config_file)

    # Variables
    last_month = time.localtime().tm_mday  # Current Day of month as read on previous cycle.  Used to trigger Daily Stats reset.
    last_hour = time.localtime().tm_hour  # Current Hour as read on previous cycle.  Used to trigger logging of stats.

    # Metrics measured from start of run.
    run_stats = {
        "reads": 0,         # Number of reads performed.
        "clear": 0,         # Number of reads showing no fault.
        "fault": 0,         # Number of reads showing a fault.
        "misread": 0,       # Number of reads which appear to be misread.
        "misread1st": 0,    # Number of misreads where first read is misread.
    }

    # Metrics measured from midnight.
    daily_stats = {
        "reads": 0,         # Number of reads performed.
        "clear": 0,         # Number of reads showing no fault.
        "fault": 0,         # Number of reads showing a fault.
        "misread": 0,       # Number of reads which appear to be misread.
        "misread1st": 0,    # Number of misreads where first read is misread.
    }

    # Configure Logging
    my_logger = logging.getLogger("MyLogger")
    my_logger.setLevel(logging.DEBUG)

    handler = logging.handlers.SysLogHandler(address='/dev/log')

    my_logger.addHandler(handler)

    log_format = '%(filename)s: %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(fmt=log_format))

    gpio.init_board(cfg.gpio_pin)
    alerter = Alert(cfg)

    # Set Last Pin State to current Pin State
    # This avoids a mail being sent every time the program restarts. (Not normally a problem unless a error condition occurs where the
    # program constantly restarts)
    last_pin_state = gpio.get_reading(cfg.gpio_pin, None, run_stats, daily_stats, my_logger)
    my_logger.info(f"Program Starting.....")
    my_logger.info(f"-- with Pin State of        {last_pin_state}")
    my_logger.info(f"-- with timeframe of        {3600 / 3600} Hours") # TODO CONFIG
    my_logger.info(f"-- max emails per timeframe {14}") # TODO CONFIG
    my_logger.info(f"-- Time between checks      {cfg.sleep_time}   Seconds")

    my_logger.info(f"-- Recipients               {cfg.sendto}")

    while True:
        pin_state = gpio.get_reading(cfg.gpio_pin, last_pin_state, run_stats, daily_stats, my_logger)
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
            my_logger.info(f"STATS0: From Start    - Reads: {run_stats['reads']} - Clear: {run_stats['clear']} - Fault {run_stats['fault']} - Misread {run_stats['misread']} - Misread1st {run_stats['misread1st']}")
            my_logger.info(f"STATS1: From Midnight - Reads: {daily_stats['reads']} - Clear: {daily_stats['clear']} - Fault {daily_stats['fault']} - Misread {daily_stats['misread']} - Misread1st {daily_stats['misread1st']}")

        if last_month != month:
            daily_stats = {
                "reads": 0,  # Number of reads performed.
                "clear": 0,  # Number of reads showing no fault.
                "fault": 0,  # Number of reads showing a fault.
                "misread": 0,  # Number of reads which appear to be misread.
                "misread1st": 0,  # Number of misreads where first read is misread.
            }

        last_pin_state = pin_state
        last_hour = hour
        last_month = month

        time.sleep(cfg.sleep_time)


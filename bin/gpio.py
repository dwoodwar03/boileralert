import time
import logging
import RPi.GPIO as GPIO



class Monitor:
    def __init__(self, gpio_pin, my_logger: logging.Logger):

        self.gpio_pin = gpio_pin
        self.logger = my_logger
        # Metrics measured from start of run.
        self.run_stats = {
            "reads": 0,  # Number of reads performed.
            "clear": 0,  # Number of reads showing no fault.
            "fault": 0,  # Number of reads showing a fault.
            "misread": 0,  # Number of reads which appear to be misread.
            "misread1st": 0,  # Number of misreads where first read is misread.
        }

        # Metrics measured from midnight.
        self.daily_stats = {
            "reads": 0,  # Number of reads performed.
            "clear": 0,  # Number of reads showing no fault.
            "fault": 0,  # Number of reads showing a fault.
            "misread": 0,  # Number of reads which appear to be misread.
            "misread1st": 0,  # Number of misreads where first read is misread.
        }

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def get_reading(self, last_pin_state):
        # In order to avoid false readings possibly due to cross talk...
        # 4 readings are taken a short time apart, they all need to show a fault
        # in order to read as a fault.
        # global Reads, Clear, Fault, Misread, Misread1st
        # global DailyReads, DailyClear, DailyFault, DailyMisread, DailyMisread1st

        p1 = GPIO.input(self.gpio_pin)
        time.sleep(0.05)
        p2 = GPIO.input(self.gpio_pin)
        time.sleep(0.05)
        p3 = GPIO.input(self.gpio_pin)
        time.sleep(0.05)
        p4 = GPIO.input(self.gpio_pin)

        self.run_stats["reads"] += 1
        self.daily_stats["reads"] += 1

        true_reading = p1 | p2 | p3 | p4  # No Fault shows as 1 (Any read as 1 Causes no fault reading)
        mis_reading_detect = p1 & p2 & p3 & p4  # Any read as 0 shows as fault, but this is used to detect misreads
        # as all 4 reading should be the same.

        return_reading = true_reading

        if true_reading and mis_reading_detect:  # Both types of measurements agree on no fault.
            self.run_stats["clear"] += 1
            self.daily_stats["clear"] += 1

        elif true_reading != mis_reading_detect:  # Both types of measurements disagree on no fault.
            self.run_stats["misread"] += 1
            self.daily_stats["misread"] += 1

            if p1 == 0:
                self.run_stats["misread1st"] += 1
                self.daily_stats["misread1st"] += 1

            return_reading = last_pin_state  # A misread should not be detected as a no alarm, as misreads can happen (rarely) when circuit closed.
            self.logger.debug(f"{p1} {p2} {p3} {p4} -- MISREAD")

        else:  # Otherwise must be true fault (p1 -> p4 show 0)
            self.run_stats["fault"] += 1
            self.daily_stats["fault"] += 1
            # self.logger.debug(f"{p1} {p2} {p3} {p4} -- FAULT")

        return return_reading

    def log_stats(self):
        self.logger.info(
            f"STATS0: From Start    - Reads: {self.run_stats['reads']} - Clear: {self.run_stats['clear']} - Fault {self.run_stats['fault']} - Misread {self.run_stats['misread']} - Misread1st {self.run_stats['misread1st']}")
        self.logger.info(
            f"STATS1: From Midnight - Reads: {self.daily_stats['reads']} - Clear: {self.daily_stats['clear']} - Fault {self.daily_stats['fault']} - Misread {self.daily_stats['misread']} - Misread1st {self.daily_stats['misread1st']}")

    def reset_daily_stats(self):
        self.daily_stats = {
            "reads": 0,  # Number of reads performed.
            "clear": 0,  # Number of reads showing no fault.
            "fault": 0,  # Number of reads showing a fault.
            "misread": 0,  # Number of reads which appear to be misread.
            "misread1st": 0,  # Number of misreads where first read is misread.
        }
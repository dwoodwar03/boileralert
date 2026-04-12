import time
import logging
import RPi.GPIO as GPIO

def init_board(gpio_pin):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def get_reading(gpio_pin, last_pin_state, run_stats: dict, daily_stats: dict, my_logger: logging.Logger):
    # In order to avoid false readings possibly due to cross talk...
    # 4 readings are taken a short time apart, they all need to show a fault
    # in order to read as a fault.
    # global Reads, Clear, Fault, Misread, Misread1st
    # global DailyReads, DailyClear, DailyFault, DailyMisread, DailyMisread1st

    p1 = GPIO.input(gpio_pin)
    time.sleep(0.05)
    p2 = GPIO.input(gpio_pin)
    time.sleep(0.05)
    p3 = GPIO.input(gpio_pin)
    time.sleep(0.05)
    p4 = GPIO.input(gpio_pin)

    run_stats["reads"] += 1
    daily_stats["reads"] += 1

    true_reading = p1 | p2 | p3 | p4  # No Fault shows as 1 (Any read as 1 Causes no fault reading)
    mis_reading_detect = p1 & p2 & p3 & p4  # Any read as 0 shows as fault, but this is used to detect misreads
    # as all 4 reading should be the same.

    return_reading = true_reading

    if true_reading and mis_reading_detect:  # Both types of measurements agree on no fault.
        run_stats["clear"] += 1
        daily_stats["clear"] += 1

    elif true_reading != mis_reading_detect:  # Both types of measurements disagree on no fault.
        run_stats["misread"] += 1
        daily_stats["misread"] += 1

        if p1 == 0:
            run_stats["misread1st"] += 1
            daily_stats["misread1st"] += 1

        return_reading = last_pin_state  # A misread should not be detected as a no alarm, as misreads can happen (rarely) when circuit closed.
        my_logger.debug(f"{p1} {p2} {p3} {p4} -- MISREAD")

    else:  # Otherwise must be true fault (p1 -> p4 show 0)
        run_stats["fault"] += 1
        daily_stats["fault"] += 1
        # my_logger.debug(f"{p1} {p2} {p3} {p4} -- FAULT")

    return return_reading

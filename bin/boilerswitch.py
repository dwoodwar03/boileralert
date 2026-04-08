#!/usr/bin/env python3

# Install Instructions
#   sudo apt install python3-rpi.gpio
#   sudo apt install python3-venv
#   cd ~
#   mkdir venvs
#   cd venvs
#   python3 -m venv boilerswitch
#   . ./boilerswitch/bin/activate
#   pip install ratelimit
#   pip install rpi.gpio
#
#   cd ~/repos/ecofuels/boilerswitch
#   cp ./etc/systemd/system/boilerswitch.service /etc/systemd/system/boilerswitch.service
#           logrotate
#           rsyslog
#           restart rsyslog
#   sudo systemctl daemon-reload
#   sudo systemctl enable boilerswitch
#   sudo systemctl start boilerswitch
#   sudo usermod -a -G gpio dwoodwar

import time
import logging
import logging.handlers
import smtplib
import platform

import RPi.GPIO as GPIO

from ratelimit import limits, RateLimitException, sleep_and_retry

# Constants
BUTTONPIN = 40
ONE_HOUR = 60*60  # Seconds in 1 Hour
MAILS = 14        # Max number of mails generated per ONE_HOUR
SLEEPTIME = 2     # Number of Seconds beteen checkinh the status of the relay.

RECIPIENTSMTP = ["User1@example.com", "User2@example.com"]
RECIPIENTHEADER = "User1 <User1@example.com>, User2 <User2@example.com>"

# Variables
LastPinState = None
LastMonth = time.localtime().tm_mday    # Current Day of month as read on previous cycle.  Used to trigger Daily Stats reset.
LastHour  = time.localtime().tm_hour    # Current Hour as read on previous cycle.  Used to trigger logging of stats.

    # Metrics measured from start of run.
Reads = 0               # Number of reads performed.
Clear = 0               # Number of reads showing no fault.
Fault = 0               # Number of reads showing a fault.
Misread = 0             # Number of reads which appear to be misread.
Misread1st = 0          # Number of misreads where first read is misread.

    # Metrics measured from midnight.
DailyReads = 0
DailyClear = 0
DailyFault = 0
DailyMisread = 0
DailyMisread1st = 0

# Functions
@sleep_and_retry
@limits(calls=MAILS, period=ONE_HOUR)
def sendmail(Fault=False):
    subjectFault = "in error"
    subjectClear = "RESET"
    messageFault = "An error has occurred on the Fox biomass boiler"
    messageClear = "The error has been RESET on the Fox biomass boiler"
    if Fault:
        subjectStatus = subjectFault
        messageStatus = messageFault
    else:
        subjectStatus = subjectClear
        messageStatus = messageClear
    
    senderAddress = f"{platform.node()}@exampleSener.co.uk"
    message = f"""From: Biomass Boiler <{senderAddress}>
To: {RECIPIENTHEADER}
Subject: Biomass Boiler {messageStatus}

{messageStatus}.

"""

    smtps = smtplib.SMTP("localhost")
    smtps.ehlo()
    smtps.starttls()
    smtps.sendmail(senderAddress, RECIPIENTSMTP, message)
    smtps.quit()

def getreading():
    # In order to avoid false readings possibly due to cross talk...
    # 4 readings are taken a short time apart, they all need to show a fault
    # in order to read as a fault.
    global Reads, Clear, Fault, Misread, Misread1st
    global DailyReads, DailyClear, DailyFault, DailyMisread, DailyMisread1st

    p1 = GPIO.input(BUTTONPIN)
    time.sleep(0.05)
    p2 = GPIO.input(BUTTONPIN)
    time.sleep(0.05)
    p3 = GPIO.input(BUTTONPIN)
    time.sleep(0.05)
    p4 = GPIO.input(BUTTONPIN)

    Reads += 1
    DailyReads +=1

    TrueReading      = p1 | p2 | p3 | p4    # No Fault shows as 1 (Any read as 1 Causes no fault reading)
    MisReadingDetect = p1 & p2 & p3 & p4    # Any read as 0 shows as fault, but this is used to detect misreads
                                            # as all 4 reading should be the same.
    
    ReturnReading = TrueReading

    if TrueReading and MisReadingDetect:    # Both types of measurements agree on no fault. 
        Clear +=1
        DailyClear +=1

    elif TrueReading != MisReadingDetect:   # Both types of measurements disagree on no fault.     
        Misread +=1
        DailyMisread +=1
        if p1 == 0:
            Misread1st += 1
            DailyMisread1st += 1
        
        ReturnReading = LastPinState        # A misread should not be detected as a no alarm, as misreads can happen (rarely) when circuit closed.
        my_logger.debug(f"{p1} {p2} {p3} {p4} -- MISREAD")

    else:                                   # Otherwise must be true fault (p1 -> p4 show 0)
        Fault += 1
        DailyFault += 1
        #my_logger.debug(f"{p1} {p2} {p3} {p4} -- FAULT")

    return ReturnReading

# Configure Logging
my_logger = logging.getLogger("MyLogger")
my_logger.setLevel(logging.DEBUG)

handler = logging.handlers.SysLogHandler(address = '/dev/log')

my_logger.addHandler(handler)

log_format = '%(filename)s: %(levelname)s - %(message)s'
handler.setFormatter(logging.Formatter(fmt=log_format))

GPIO.setmode(GPIO.BOARD)
GPIO.setup(BUTTONPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set Last Pin State to current Pin State
# This avoids a mail being sent every time the program restarts. (Not normally a problem unless a error condition occurs where the 
# program constantly restarts)
LastPinState = getreading()
my_logger.info(f"Program Starting.....") 
my_logger.info(f"-- with Pin State of        {LastPinState}")
my_logger.info(f"-- with timeframe of        {ONE_HOUR/3600} Hours")
my_logger.info(f"-- max emails per timeframe {MAILS}")
my_logger.info(f"-- Time between checks      {SLEEPTIME}   Seconds")

my_logger.info(f"-- Recipients               {RECIPIENTSMTP}")

while True:
    PinState = getreading()
    Month = time.localtime().tm_mday
    Hour  = time.localtime().tm_hour

    if PinState:
        # Button is not pressed
        if LastPinState != PinState:
            my_logger.info("Boiler Fault Cleared")
            sendmail(Fault=False)

    else:
        # Button is pressed
        if LastPinState != PinState:
            my_logger.info("Boiler Fault ACTIVE")
            sendmail(Fault=True)
            

    if LastHour != Hour:
        my_logger.info(f"STATS0: From Start    - Reads: {Reads} - Clear: {Clear} - Fault {Fault} - Misread {Misread} - Misread1st {Misread1st}")
        my_logger.info(f"STATS1: From Midnight - Reads: {DailyReads} - Clear: {DailyClear} - Fault {DailyFault} - Misread {DailyMisread} - Misread1st {DailyMisread1st}")

    if LastMonth != Month:
        DailyReads = 0
        DailyClear = 0
        DailyFault = 0
        DailyMisread = 0
        DailyMisread1st = 0

    LastPinState = PinState
    LastHour = Hour
    LastMonth = Month
    
    time.sleep(SLEEPTIME)


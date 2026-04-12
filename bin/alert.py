"""
Manages sending of emails.
"""

import smtplib

from email.message import EmailMessage
from ratelimit import limits, RateLimitException, sleep_and_retry

import config

# Constants
MAILS = 14        # Max number of mails generated per ONE_HOUR
ONE_HOUR = 60*60  # Seconds in 1 Hour

class Alert:
    def __init__(self, cfg: config.Config):
        self.smtp_server = cfg.server
        self.sender_address = cfg.sender_address
        self.sender_full_name = cfg.sender_full_name
        self.envelope_sendto = cfg.envelope_sendto
        self.from_full = f"{cfg.sender_full_name} <{cfg.sender_address}>"

        self.fault_subject = cfg.fault_subject
        self.fault_message = cfg.fault_message
        self.clear_subject = cfg.clear_subject
        self.clear_message = cfg.clear_message

    def send_fault(self):
        self.sendmail(self.fault_subject, self.fault_message)

    def send_clear(self):
        self.sendmail(self.clear_subject, self.clear_message)

    @sleep_and_retry
    @limits(calls=MAILS, period=ONE_HOUR)
    def sendmail(self, subject, message):
        smtp = smtplib.SMTP(self.smtp_server)

        email = EmailMessage()
        email.set_content(message, subtype="plain")
        email["To"] = self.envelope_sendto
        email["From"] = self.from_full
        email["Subject"] = subject
        smtp.send_message(email)

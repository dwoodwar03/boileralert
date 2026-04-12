#!/usr/bin/env python3

"""
Manage the configuration file
"""

import platform
import yaml

class Config:
    """
    Manage the configuration file for the DailyReport application
    """

    def __init__(self, config_file):
        self._cfg = yaml.safe_load(open(config_file))
        self.server = self._cfg['mail']['server']
        self.sendto = [email for _, email in self._cfg['mail']['send_to']]
        self.sleep_time = self._cfg['monitoring']['sleep_time_secs']
        self.gpio_pin = self._cfg['monitoring']['gpio_pin']
        self.fault_subject = self._cfg['messaging']['fault_subject']
        self.fault_message = self._cfg['messaging']['fault_message']
        self.clear_subject = self._cfg['messaging']['clear_subject']
        self.clear_message = self._cfg['messaging']['clear_message']
        self.sender_address = f"{platform.node().split(".")[0]}@{self._cfg['mail']['sender_domain']}"
        self.sender_full_name = self._cfg['mail']['sender_full_name']

    @property
    def envelope_sendto(self):
        content = ""
        seperator = ""
        for full_name, email in self._cfg['mail']['send_to']:
            content += f"{seperator}{full_name} <{email}>"
            seperator = ", "
        return content

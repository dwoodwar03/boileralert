#!/usr/bin/env python3

"""
Application to send email alerts upon faults being detected on a connected boiler.
Faults detected when short of pins is detected.
Reset messages are also sent
"""

import argparse

from boilerswitch_core import run_checker

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="/etc/boilerswitch.yaml", help="Custom location of config file")
    args = parser.parse_args()

    run_checker(args.config)

if __name__ == "__main__":
    main()

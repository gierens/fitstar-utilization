#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

from time import sleep
import argparse
import argcomplete
import os
import sys

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


URL = 'https://www.fit-star.de'
WAIT_DELAY = 20


def init_browser():
    # options = webdriver.ChromeOptions()
    # options.add_argument('--ignore-certificate-errors')
    return webdriver.Chrome()  # options=options)


def init_browser_wait(browser, wait_delay):
    return WebDriverWait(browser, wait_delay)


def close_browser(browser):
    browser.quit()


def setup_parser():
    parser = argparse.ArgumentParser(
        description="""
        FitStar Utilization is a script for pulling utilization data from the
        FitStar website and inserting those data in an InfluxDB.
        """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('-u',
                        '--url',
                        type=str,
                        default=URL,
                        help="URL of the FitStar website's main page",
                        )
    return parser


def parse_args(parser):
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    return args


def main():
    parser = setup_parser()
    args = parse_args(parser)

    browser = init_browser()
    wait = init_browser_wait(browser, WAIT_DELAY)

    browser.get(args.url)
    sleep(5)

    close_browser(browser)


if __name__ == '__main__':
    main()

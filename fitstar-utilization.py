#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

from time import sleep
from datetime import datetime
import argparse
import argcomplete
import os
import sys

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

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


def create_new_tab(browser, name):
    browser.execute_script(f"window.open('about:blank', '{name}');")


def switch_to_tab(browser, name):
    browser.switch_to.window(name)


def open_in_new_tab(browser, name, url):
    create_new_tab(browser, name)
    switch_to_tab(browser, name)
    browser.get(url)


def close_tab(browser, name):
    switch_to_tab(browser, name)
    browser.close()


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

    # open main page
    browser.get(args.url)

    # save cookie settings
    save_settings_button: WebElement = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@aria-label='Einstellungen speichern']")))
    print('save settings button clickable')
    save_settings_button.click()
    print('save settings button clicked')

    # click studios dropdown
    studios_downdown_trigger: WebElement = browser.find_element_by_xpath(
        "//a[contains(@class, 'studios') and " +
        "contains(@class, 'dropdownTrigger')]")
    print('found studios downdown trigger')
    studios_downdown_trigger.click()
    print('open studios dropdown')

    # find studio list
    studios_row: WebElement = browser.find_element_by_xpath(
        "//ul[contains(@class, 'row-studios')]")
    print('found studio list')

    # find studio links
    studio_links: list[WebElement] = studios_row.find_elements_by_xpath('.//a')
    studio_urls: list[str] = list(dict.fromkeys([link.get_attribute('href')
                                                for link in studio_links]))

    # loop through studio pages
    main_tab_name: str = browser.window_handles[0]
    for studio_url in studio_urls:
        studio_name: str = studio_url.split('/')[-1]
        open_in_new_tab(browser, studio_name, studio_url)
        try:
            utilization_text: WebElement = browser.find_element_by_xpath(
                '//strong[@id="fs-livedata-percentage"]')
            now = datetime.now()
            print(studio_name, utilization_text.text, now)
            # TODO insert data into InfluxDB
        except NoSuchElementException:
            print(f'{studio_name} no data')
        close_tab(browser, studio_name)
        switch_to_tab(browser, main_tab_name)

    close_browser(browser)


if __name__ == '__main__':
    main()

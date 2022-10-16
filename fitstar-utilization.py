#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

from datetime import datetime
import argparse
import argcomplete
import sys
from influxdb import InfluxDBClient
from logging import (debug, info, error, warning, DEBUG, INFO, WARN, ERROR)
from colorlog import ColoredFormatter, StreamHandler, getLogger

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

URL = 'https://www.fit-star.de'
WAIT_DELAY = 20

LOG_LEVELS: dict[int, int] = {
    0: ERROR,
    1: WARN,
    2: INFO,
    3: DEBUG,
}


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


def setup_logging(args: argparse.Namespace) -> None:
    """
    Setup the logging.

    Parameters
    ----------
    args : argparse.Namespace
        The argparse namespace containing the parsed arguments.

    Returns
    -------

    See Also
    --------

    Example
    -------
    >>> setup_logging(args)
    """
    logformat = '%(log_color)s%(asctime)s %(levelname)-8s %(message)s'
    formatter = ColoredFormatter(
        logformat,
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    handler = StreamHandler()
    handler.setFormatter(formatter)
    logger = getLogger()
    logger.addHandler(handler)
    logger.setLevel(LOG_LEVELS[args.verbosity])


def setup_parser():
    parser = argparse.ArgumentParser(
        description="""
        FitStar Utilization is a script for pulling utilization data from the
        FitStar website and inserting those data in an InfluxDB.
        """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('-U',
                        '--url',
                        type=str,
                        default=URL,
                        help="URL of the FitStar website's main page",
                        )
    parser.add_argument('-f',
                        '--filter',
                        type=str,
                        help=("Substring filter for the studio names" +
                              " (examples: muenchen or berlin-moabit)"),
                        )
    # TODO maybe argument for creating influxdb database
    parser.add_argument('-H',
                        '--host',
                        type=str,
                        default='localhost',
                        help="InfluxDB hostname, FQDN or IP address",
                        )
    parser.add_argument('-P',
                        '--port',
                        type=int,
                        default=8086,
                        help="InfluxDB port",
                        )
    parser.add_argument('-u',
                        '--username',
                        type=str,
                        default='root',
                        help="InfluxDB username",
                        )
    parser.add_argument('-p',
                        '--password',
                        type=str,
                        default='root',
                        help="InfluxDB password",
                        )
    parser.add_argument('-S',
                        '--ssl',
                        action='store_true',
                        help="Use SSL for InfluxDB connection",
                        )
    parser.add_argument('-V',
                        '--verify-ssl',
                        action='store_true',
                        help="Verify SSL certificate for InfluxDB connection",
                        )
    parser.add_argument('-v',
                        '--verbose',
                        dest='verbosity',
                        action='count',
                        default=0,
                        help='''Verbosity, can be given multiple times to set
                             the log level (0: error, 1: warn, 2: info, 3:
                             debug)''',
                        )
    return parser


def parse_args(parser):
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    return args


def main():
    parser = setup_parser()
    args = parse_args(parser)
    setup_logging(args)

    # connect to InfluxDB
    try:
        influx = InfluxDBClient(host=args.host,
                                port=args.port,
                                username=args.username,
                                password=args.password,
                                ssl=args.ssl,
                                verify_ssl=args.verify_ssl,
                                )
    except Exception as e:
        error(f"Could not connect to InfluxDB: {e}")
        sys.exit(1)

    # create and switch to database
    # this also checks if we are properly connected and authorized
    try:
        influx.create_database('fitstar')
        influx.switch_database('fitstar')
    except Exception as e:
        error(f"Could not create or switch to database: {e}")
        sys.exit(1)

    # initialize browser
    browser = init_browser()
    wait = init_browser_wait(browser, WAIT_DELAY)

    # open main page
    browser.get(args.url)

    # save cookie settings
    save_settings_button: WebElement = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@aria-label='Einstellungen speichern']")))
    debug('save settings button clickable')
    save_settings_button.click()
    debug('save settings button clicked')

    # click studios dropdown
    studios_downdown_trigger: WebElement = browser.find_element_by_xpath(
        "//a[contains(@class, 'studios') and " +
        "contains(@class, 'dropdownTrigger')]")
    debug('found studios downdown trigger')
    studios_downdown_trigger.click()
    debug('open studios dropdown')

    # find studio list
    studios_row: WebElement = browser.find_element_by_xpath(
        "//ul[contains(@class, 'row-studios')]")
    debug('found studio list')

    # find studio links
    studio_links: list[WebElement] = studios_row.find_elements_by_xpath('.//a')
    debug('retrieved studio urls')
    studio_urls: list[str] = list(dict.fromkeys([link.get_attribute('href')
                                                for link in studio_links]))
    studio_names: list[str] = [studio_url.split('/')[-1]
                               for studio_url in studio_urls]
    studios = dict(zip(studio_names, studio_urls))

    # loop through studio pages
    data = []
    main_tab_name: str = browser.window_handles[0]
    for studio_name, studio_url in studios.items():
        if args.filter and args.filter not in studio_name:
            info(f"skipping studio {studio_name} due to filter")
            continue
        debug(f'open studio site of {studio_name}')
        open_in_new_tab(browser, studio_name, studio_url)
        try:
            utilization_text: WebElement = browser.find_element_by_xpath(
                '//strong[@id="fs-livedata-percentage"]')
            utilization = int(utilization_text.text.replace('%', ''))
            now = datetime.now()
            timestamp = round(now.timestamp())
            info(f'{studio_name}: {utilization}% at {now}')
            data.append(f'utilization,studio={studio_name} ' +
                        f'utilization={utilization} {timestamp}')
        except NoSuchElementException:
            warning(f'no data for {studio_name}')
        debug(f'close studio site of {studio_name}')
        close_tab(browser, studio_name)
        switch_to_tab(browser, main_tab_name)

    # close browser
    close_browser(browser)

    # insert data into InfluxDB
    influx.write_points(data, time_precision='s', protocol='line',
                        batch_size=10000)

    # close InfluxDB connection
    influx.close()


if __name__ == '__main__':
    main()

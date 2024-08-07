# pylint: disable=broad-exception-caught

import logging
import random
import time

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

BASE_URL = 'https://instagram.com/'


def type_with_delay(input_field, text):
    for char in text:
        input_field.send_keys(char)
        time.sleep(random.uniform(0.1, 0.5))


def _get_value_from_page(soup, key: str) -> str:
    """Extract the value from the page for the defined button 'key'."""
    
    def _is_key_match(element, key: str) -> bool:
        """Checks if the key matches the text in the element"""
        normalized_key = key.strip().lower()
        btn_text = element.get_text(strip=True).lower()

        return normalized_key in btn_text

    def _extract_value(element) -> str:
        """Extracts and returns the numeric value from the <button> element."""
        span = element.find('span')
        span_span = span.find('span')

        if span_span:
            value = span_span.text.strip()
            logging.info("Extracted value: %s", value)

            number_string = value.replace(',', '').replace('.', '').replace('M', '000000')
            logging.info("Number string: %s", number_string)

            return int(number_string) if number_string else 0

        return 0

    def find_element_by_tag(tag: str):
        for element in soup.find_all(tag):
            if _is_key_match(element, key):
                return _extract_value(element)
        return 0


    # Try to find the value in <button>, <a>, and <div> tags
    for tag in ['button', 'a', 'div']:
        logging.info("Trying to find element with key '%s' in '%s' tags", key, tag)
        value = find_element_by_tag(tag)

        if value > 0:
            logging.info("Found element with key '%s' in '%s' tag - value: %s", key, tag, value)
            return value

    logging.info("Failed to find element with key '%s'", key)
    return 0


class InstagramCrawler:
    def __init__(self, driver: WebDriver):
        self.driver = driver

    def login(self, username: str, password: str):
        logging.info("Log in to Instagram with user '%s'", username)
        
        self.driver.get(BASE_URL)
        time.sleep(random.uniform(10, 15))
        
        try:
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Phone number, username or email address']"))
            )
            
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Password']"))
            )
            
        except Exception as e:
            logging.debug("An error occurred while crawling: %s", str(e))
            logging.info("The login input fields are not present. Probably the user is already loged in.")
            return
        
        type_with_delay(username_input, username)
        time.sleep(random.uniform(1, 3))

        type_with_delay(password_input, password)
        time.sleep(random.uniform(0.1, 0.5))

        password_input.send_keys(Keys.RETURN)
        logging.info("Successfully logged in to Instagram.")


    def crawl(self, name: str, profile: str) -> str:
        """Crawl data for a team from Instagram."""
        logging.info("Crawling data for '%s' from '%s'", name, BASE_URL + profile)
        
        # open a new tab
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(BASE_URL + profile)

        try:
            # Wait for the profile page to load and for a specific element to be present
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.TAG_NAME, 'button'))  # Wait for the body tag to be present
            )

            # Get the page source after the page has rendered
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Assuming get_value_from_page is defined elsewhere
            follower = _get_value_from_page(soup, 'followers')
            posts = _get_value_from_page(soup, 'posts')

            result = {
                "profile": profile,
                "follower": follower,
                "posts": posts
            }

            logging.info("Result: %s", result)

        except Exception as e:
            logging.error("An error occurred while crawling: %s", str(e))
            result = {
                "profile": profile,
                "follower": 0,
                "posts": 0
            }
        

        # close the tab
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        return [name, result]


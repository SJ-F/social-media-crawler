import logging
import requests
import re
import json

from bs4 import BeautifulSoup

from utils.user_agents import get_random_user_agent

BASE_URL = 'https://facebook.com/'

def get_dummy_data(url: str) -> int:
    """Return dummy data based on the provided URL."""
    if url == "https://facebook.com/ifmrazorbacks":
        follower = 8500

    elif url == "https://facebook.com/allgaeucomets":
        follower = 9700

    else:
        follower = 0

    return follower


class FacebookCrawler:
    def __init__(self, session: requests.Session):
        self.session = session

    def crawl(self, name: str, profile: str) -> str:
        """Crawl data for a team from Facebook."""
        self.session.headers.update({'User-Agent': get_random_user_agent()})
        
        logging.info("Crawling data for '%s' from '%s'", name, BASE_URL + profile)
        return

        response = self.session.get(BASE_URL + profile)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            print(soup)

            result = {
            }

            logging.info("Result: %s", result)
            return json.dumps(result, ensure_ascii=False)

        logging.error("Failed to retrieve '%s'. Status code: %d", BASE_URL + profile, response.status_code)
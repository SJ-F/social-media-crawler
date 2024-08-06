import logging
import requests
import re
import json

from bs4 import BeautifulSoup

from utils.user_agents import get_random_user_agent

BASE_URL = 'https://instagram.com/'

def get_dummy_data(url: str) -> tuple:
    """Return dummy data based on the provided URL."""
    if url == "https://instagram.com/ifmrazorbacks":
        follower = 6900
        posts = 890

    elif url == "https://instagram.com/allgaeucomets":
        follower = 6350
        posts = 840

    else:
        follower = 0
        posts = 0

    return follower, posts


class InstagramCrawler:
    def __init__(self, session: requests.Session):
        self.session = session

    def crawl(self, name: str, profile: str) -> str:
        """Crawl data for a city from Wikipedia."""
        self.session.headers.update({'User-Agent': get_random_user_agent()})
        
        logging.info("Crawling data for '%s' from '%s'", name, BASE_URL + profile)
        status_code = 200

        if status_code == 200:
            follower, posts = get_dummy_data(BASE_URL + profile)

            result = {
                "profile": profile,
                "follower": follower,
                "posts": posts
            }

            logging.info("Result: %s", result)
            return json.dumps(result, ensure_ascii=False)

        logging.error("Failed to retrieve '%s'. Status code: %d", BASE_URL + profile, status_code)
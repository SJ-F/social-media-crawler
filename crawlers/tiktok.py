import logging
import requests
import re
import json

from bs4 import BeautifulSoup

from utils.user_agents import get_random_user_agent

BASE_URL = 'https://tiktok.com/'

def get_dummy_data() -> tuple:
    """Return dummy data based on the provided URL."""
    follower = 0
    posts = 0

    return follower, posts


class TiktokCrawler:
    def __init__(self, session: requests.Session):
        self.session = session

    def crawl(self, name: str, profile: str) -> str:
        """Crawl data for a profile from TikTok."""
        self.session.headers.update({'User-Agent': get_random_user_agent()})
        
        logging.info("Crawling data for '%s' from '%s'", name, BASE_URL + profile)
        status_code = 200

        if status_code == 200:
            follower, posts = get_dummy_data()

            result = {
                "profile": profile,
                "follower": follower,
                "posts": posts
            }

            logging.info("Result: %s", result)
            return json.dumps(result, ensure_ascii=False)

        logging.error("Failed to retrieve '%s'. Status code: %d", BASE_URL + profile, status_code)
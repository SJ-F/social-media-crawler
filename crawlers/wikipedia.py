import logging
import requests
import re
import json

from bs4 import BeautifulSoup

from utils.user_agents import get_random_user_agent

BASE_URL = 'https://de.wikipedia.org/wiki/'

def _is_key_match(td, key: str) -> bool:
    """Checks if the key matches the text in the <td> or any <a> tags within it."""
    return (re.match(r'^\s*' + re.escape(key) + r'\s*$', td.get_text(strip=True)) or
            any(re.match(r'^\s*' + re.escape(key.rstrip(':')) + r'\s*$', a.get_text(strip=True)) for a in td.find_all('a')))

def _extract_value(td) -> int:
    """Extracts and returns the numeric value from the <td> element."""
    value = td.find_next_sibling('td').text.split(' ')[0]
    number_string = value.replace('\u00a0Einwohner', '').replace('.', '')
    return int(number_string) if number_string else 0

def _get_value_from_table(soup, key: str) -> int:
    """Extracts a numeric value from a Wikipedia table based on the provided key."""
    for td in soup.find_all('td'):
        if _is_key_match(td, key):
            return _extract_value(td)
    return 0

class WikipediaCrawler:
    def __init__(self, session: requests.Session):
        self.session = session

    def crawl(self, city: str, url: str) -> str:
        """Crawl data for a city from Wikipedia."""
        self.session.headers.update({'User-Agent': get_random_user_agent()})
        
        logging.info("Crawling data for '%s' from '%s'", city, BASE_URL + url)
        response = self.session.get(BASE_URL + url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            population = _get_value_from_table(soup, 'Einwohner:')
            population_density = _get_value_from_table(soup, 'Bevölkerungsdichte:')

            result = {
                "name": city,
                "population": population,
                "population_density": population_density
            }

            logging.info("Result: %s", result)
            return json.dumps(result, ensure_ascii=False)

        logging.error("Failed to retrieve '%s'. Status code: %d", BASE_URL + url, response.status_code)
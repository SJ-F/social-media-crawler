# pylint: disable=broad-exception-caught

import os
import logging
import json
import time
import random
from dataclasses import dataclass
from datetime import datetime


import requests

from crawlers.wikipedia import WikipediaCrawler
from utils.time_format import split_seconds_into_hours_minutes_and_seconds as time_string

# Constants
DATA_DIR_NAME = 'data'
LOCATION_DIR_NAME = 'locations'
CONFIG_FILE_NAME = 'config.json'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class Location:
    """Data class to represent a location with its name and Wikipedia URL."""
    name: str
    wikipedia: str


class ConfigHandler:
    """Class to handle configuration loading and validation."""

    def __init__(self, file_path: str):
        self.locations: list[Location] = []
        self.min_delay_in_seconds: int = 0
        self.max_delay_in_seconds: int = 0
        self.load_config(file_path)

    def __str__(self) -> str:
        locations_str = (
            "Locations to crawl:\n\t- " +
            "\n\t- ".join(str(location) for location in self.locations)
        )

        delay_str = (
            f"Delay between crawls: {self.min_delay_in_seconds} - "
            f"{self.max_delay_in_seconds} seconds"
        )
        return delay_str + "\n" + locations_str

    def load_config(self, file_name: str):
        """Load configuration from a JSON file."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, file_name)

        with open(file_path, 'r', encoding='utf-8') as file:
            config = json.load(file)

        self.min_delay_in_seconds = self.validate_config_value(
                                            config.get('min_delay_in_seconds'),
                                            "Minimum delay")

        self.max_delay_in_seconds = self.validate_config_value(
                                        config.get('max_delay_in_seconds'),
                                        "Maximum delay")

        self.load_locations(config.get('locations', []))

    def validate_config_value(self, value, name: str) -> int:
        """Validate a configuration value."""
        if value is None:
            raise ValueError(f"{name} not found - crawling aborted.")
        return value

    def load_locations(self, locations_data: list):
        """Load locations from the configuration data."""
        if not locations_data:
            raise ValueError("No locations found - crawling aborted.")

        for location in locations_data:
            name = location.get('name')
            wikipedia = location.get('wikipedia')
            if not name or not wikipedia:
                logging.error("Location '%s': name or Wikipedia not found - crawling skipped.",
                                name)
            else:
                self.locations.append(Location(name, wikipedia))


def idle_to_hide_crawling_bot(config: ConfigHandler):
    """Wait a random time between two requests to hide crawling bot."""
    time_to_idle = int(random.uniform(config.min_delay_in_seconds, config.max_delay_in_seconds))
    logging.info("Waiting for %d seconds before the next request...", time_to_idle)
    time.sleep(time_to_idle)


def crawl_wikipedia(session: requests.Session, name: str, url: str):
    """Crawl data for a single location from Wikipedia."""
    crawler = WikipediaCrawler(session)

    try:
        return crawler.crawl(name, url)
    except Exception as e:
        logging.error("Error crawling data for location '%s': %s", name, str(e))
        return None


def log_crawling_progress(crawling_durations: list, config: ConfigHandler):
    """Log the progress of the crawling process."""
    locations_left_for_crawling = len(config.locations) - len(crawling_durations)
    logging.info("%s/%s locations crawled.", len(crawling_durations), len(config.locations))

    if crawling_durations:
        avg_duration = sum(crawling_durations) / len(crawling_durations)
        time_left = int(locations_left_for_crawling * avg_duration)
        if time_left > 0:
            logging.info("Remaining runtime: %s", time_string(time_left))


def save_crawled_data(crawled_data: list):
    """Save all location data to a JSON file."""
    current_date = datetime.now().strftime("%Y%m%d")
    file_name = f"{current_date}_locations_crawl.json"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, DATA_DIR_NAME, LOCATION_DIR_NAME, file_name)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(crawled_data, f, ensure_ascii=False, indent=4)
    logging.info("Crawled location data saved to '%s'.", file_path)


def crawl_locations(session: requests.Session, config: ConfigHandler):
    """Crawl data from Wikipedia for all locations defined in the config."""
    crawling_durations = []
    crawled_data = []

    random.shuffle(config.locations)
    for location in config.locations:
        start_time = time.time()

        location_data = crawl_wikipedia(session, location.name, location.wikipedia)
        if location_data:
            crawled_data.append(json.loads(location_data))

        idle_to_hide_crawling_bot(config)

        duration = time.time() - start_time
        crawling_durations.append(duration)

        log_crawling_progress(crawling_durations, config)

    save_crawled_data(crawled_data)


def main():
    """Main function to load config and start crawling."""
    current_config = ConfigHandler(CONFIG_FILE_NAME)
    current_session = requests.Session()

    crawl_locations(current_session, current_config)


if __name__ == "__main__":
    main()

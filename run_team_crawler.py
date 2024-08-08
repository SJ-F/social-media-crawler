# pylint: disable=broad-exception-caught

import os
import logging
import json
import time
import random
from dataclasses import dataclass, field
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from crawlers.instagram import InstagramCrawler
from utils.user_agents import get_random_user_agent

# Constants
DATA_DIR_NAME = 'data'
TEAM_DIR_NAME = 'teams'
CONFIG_FILE_NAME = 'debug-config.json'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class SocialMedia:
    """Data class to hold social media links for a team."""
    instagram: str
    facebook: str
    youtube: str
    tiktok: str


@dataclass
class Team:
    """Data class to represent a sports team."""
    name: str
    sport: str
    league: str
    division: str
    location: str
    social_media: SocialMedia = field(default_factory=SocialMedia)


class ConfigHandler:
    """Class to handle configuration loading and validation."""

    def __init__(self, file_path: str):
        self.teams: list[Team] = []
        self.min_delay_in_seconds: int = 0
        self.max_delay_in_seconds: int = 0
        self.load_config(file_path)

    def __str__(self) -> str:
        teams_str = "Teams to crawl:\n\t- " + "\n\t- ".join(str(team)
                                                            for team in self.teams)

        delay_str = (
            f"Delay between crawls: {self.min_delay_in_seconds} - "
            f"{self.max_delay_in_seconds} seconds"
        )

        return delay_str + "\n" + teams_str

    def load_config(self, file_name: str):
        """Load configuration from a JSON file."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, file_name)

        with open(file_path, 'r', encoding='utf-8') as file:
            current_config = json.load(file)

        self.min_delay_in_seconds = self.validate_config_value(
                                        current_config.get('min_delay_in_seconds'),
                                        "Minimum delay")

        self.max_delay_in_seconds = self.validate_config_value(
                                        current_config.get('max_delay_in_seconds'),
                                        "Maximum delay")

        self.load_teams(current_config.get('teams', []))

    def validate_config_value(self, value, name: str) -> int:
        """Validate a configuration value."""
        if value is None:
            raise ValueError(f"{name} not found - crawling aborted.")
        return value

    def load_teams(self, teams_data: list):
        """Load teams from the configuration data."""
        if not teams_data:
            raise ValueError("No teams found - crawling aborted.")

        for team in teams_data:
            team_data_object = Team(
                name=team.get('name'),
                sport=team.get('sport'),
                league=team.get('league'),
                division=team.get('division'),
                location=team.get('location'),
                social_media=SocialMedia(
                    instagram=team.get('social_media', {}).get('instagram'),
                    facebook=team.get('social_media', {}).get('facebook'),
                    youtube=team.get('social_media', {}).get('youtube'),
                    tiktok=team.get('social_media', {}).get('tiktok')
                )
            )

            if not team_data_object.name or not team_data_object.sport:
                logging.error("Team '%s': name or sport not found - crawling skipped.",
                                team_data_object.name
                            )
                continue

            self.teams.append(team_data_object)


def idle_to_hide_crawling_bot(current_config: ConfigHandler):
    """Wait a random time between two requests to hide crawling bot."""
    time_to_idle = int(random.uniform(current_config.min_delay_in_seconds,
                                      current_config.max_delay_in_seconds))

    logging.info("Waiting for %d seconds before the next request...", time_to_idle)
    time.sleep(time_to_idle)


def save_crawled_data(crawled_data: list):
    """Save all crawled team data to a JSON file."""
    current_date = datetime.now().strftime("%Y%m%d")
    file_name = f"{current_date}_teams_crawl.json"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, DATA_DIR_NAME, TEAM_DIR_NAME, file_name)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(crawled_data, f, ensure_ascii=False, indent=4)
    logging.info("Crawled team data saved to '%s'.", file_path)


def crawl_instagram(current_driver: WebDriver, current_config: ConfigHandler):
    """Crawl data from Instagram for all teams defined in the config."""
    crawled_instagram_data = []

    crawler = InstagramCrawler(current_driver)
    crawler.login("ralph.boehm.1", "hiwqo2-famced-Jajwur")

    random.shuffle(current_config.teams)
    for team in current_config.teams:
        if team.social_media.instagram:
            crawled_data = crawler.crawl(team.name, team.social_media.instagram)
            crawled_instagram_data.append(crawled_data)
            idle_to_hide_crawling_bot(current_config)

    return crawled_instagram_data


def main():
    """Main function to load config and start crawling."""
    config = ConfigHandler(CONFIG_FILE_NAME)

    user_profile_path = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default")
    logging.info("Using user profile path: %s", user_profile_path)

    chrome_options = Options()
    chrome_options.add_argument(f"user-agent={get_random_user_agent()}")
    chrome_options.add_argument(f"user-data-dir={user_profile_path}")

    chrome_service = Service('./_chromedriver/chromedriver')
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    driver.delete_all_cookies()

    try:
        crawled_data = crawl_instagram(driver, config)
        save_crawled_data(crawled_data)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

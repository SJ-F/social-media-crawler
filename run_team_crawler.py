import os
import logging
import json
import time
import random
import requests

from dataclasses import dataclass, field
from datetime import datetime

from crawlers.instagram import InstagramCrawler
from crawlers.facebook import FacebookCrawler
from crawlers.youtube import YoutubeCrawler
from crawlers.tiktok import TiktokCrawler
from utils.time_format import split_seconds_into_hours_minutes_and_seconds as time_string

DATA_DIR_NAME = 'data'
LOCATION_DIR_NAME = 'teams'
CONFIG_FILE_NAME = 'debug-config.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class SocialMedia:
    instagram: str
    facebook: str
    youtube: str
    tiktok: str

@dataclass
class Team:
    name: str
    sport: str
    league: str
    division: str
    location: str
    social_media: SocialMedia = field(default_factory=SocialMedia)

class ConfigHandler:
    def __init__(self, file_path: str):
        self.teams = []
        self.min_delay_in_seconds = 0
        self.max_delay_in_seconds = 0
        self.load_config(file_path)

    def __str__(self) -> str:
        teams_str = "Teams to crawl:\n\t- " + "\n\t- ".join(str(team) for team in self.teams)
        delay_str = f"Delay between crawls: {self.min_delay_in_seconds} - {self.max_delay_in_seconds} seconds"
        return delay_str + "\n" + teams_str

    def load_config(self, file_name: str):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, file_name)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            config = json.load(file)

        self.min_delay_in_seconds = self.validate_config_value(config.get('min_delay_in_seconds'), "Minimum delay")
        self.max_delay_in_seconds = self.validate_config_value(config.get('max_delay_in_seconds'), "Maximum delay")
        self.load_teams(config.get('teams', []))

    def validate_config_value(self, value, name: str):
        if value is None:
            raise ValueError(f"{name} not found - crawling aborted.")
        return value

    def load_teams(self, teams_data):
        if not teams_data:
            raise ValueError("No teams found - crawling aborted.")

        for team in teams_data:
            name = team.get('name')
            sport = team.get('sport')
            if not name or not sport:
                logging.error("Team '%s': name or sport not found - crawling for this location skipped.", name)
                continue  # Skip to the next team if name or sport is missing
            
            league = team.get('league', None)
            division = team.get('division', None)
            location = team.get('location', None)

            social_media = team.get('social_media', {})
            instagram = social_media.get('instagram', None)
            facebook = social_media.get('facebook', None)
            youtube = social_media.get('youtube', None)
            tiktok = social_media.get('tiktok', None)
            
            new_team = Team(name, sport, league, division, location, SocialMedia(instagram, facebook, youtube, tiktok))
            self.teams.append(new_team)


def idle_to_hide_crawling_bot(config: ConfigHandler):
    """Wait a random time between two requests to hide crawling bot."""
    time_to_idle = int(random.uniform(config.min_delay_in_seconds, config.max_delay_in_seconds))
    logging.info("Waiting for %d seconds before the next request...", time_to_idle)
    time.sleep(time_to_idle)


def crawl_social_media(session: requests.Session, team: Team):
    """Crawl data for all social media profiles of a team."""
    crawled_data = {}

    for platform, profile in team.social_media.__dict__.items():
        if profile:
            try:
                crawler_class = {
                    'instagram': InstagramCrawler,
                    'facebook': FacebookCrawler,
                    'youtube': YoutubeCrawler,
                    'tiktok': TiktokCrawler
                }[platform]

                crawler = crawler_class(session)
                crawled_data[platform] = json.loads(crawler.crawl(team.name, profile))

            except Exception as e:
                logging.error("Error crawling data from %s for profile '%s': %s", platform.capitalize(), profile, str(e))
    
    return crawled_data


def crawl_teams(session: requests.Session, config: ConfigHandler):
    """Crawl data from Wikipedia for all locations defined in the config."""
    crawling_durations = []
    crawled_data = []

    for team in config.teams:
        start_time = time.time()

        team_data = {
            "name": team.name,
            "sport": team.sport,
            "league": team.league,
            "division": team.division,
            "location": team.location,
        }

        # actual crawling happens here
        # =====================================================================
        team_data.update(crawl_social_media(session, team))
        crawled_data.append(team_data)

        idle_to_hide_crawling_bot(config)
        # =====================================================================

        duration = time.time() - start_time
        crawling_durations.append(duration)

        locations_left_for_crawling = len(config.teams) - len(crawling_durations)
        logging.info("%s/%s locations crawled.", len(crawling_durations), len(config.teams))

        if crawling_durations:
            avg_duration = sum(crawling_durations) / len(crawling_durations)
            time_left = int(locations_left_for_crawling * avg_duration)
            if time_left > 0:
                logging.info("Remaining runtime: %s", time_string(time_left))

    # Save all location data to a JSON file
    current_date = datetime.now().strftime("%Y%m%d")
    file_name = f"{current_date}_teams_crawl.json"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, DATA_DIR_NAME, LOCATION_DIR_NAME, file_name)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(crawled_data, f, ensure_ascii=False, indent=4)
    logging.info("crawled location data saved to '%s'.", file_path)

# Load the config file and start crawling
config = ConfigHandler(CONFIG_FILE_NAME)

session = requests.Session()
crawl_teams(session, config)
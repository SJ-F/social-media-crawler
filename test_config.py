import logging
import json
from collections import Counter

def load_config(file_path):
    with open(file_path) as f:
        return json.load(f)

def get_names(elements):
    return [element['name'] for element in elements]

def get_team_locations(teams):
    return [team['location'] for team in teams]

def find_duplicates(names):
    location_counts = Counter(names)
    return [name for name, count in location_counts.items() if count > 1]

def validate_names(config, element_type):
    names = get_names(config[element_type])
    duplicates = find_duplicates(names)

    if not duplicates:
        logging.info("Config includes %s unique %s." % (len(names), element_type))
    else:
        logging.warning("Config includes %s %s from which %s are included at least twice." % (len(names), element_type, len(duplicates)))
        logging.warning("Duplicate %s found: %s"% (element_type, duplicates))

    return list(set(names))

def validate_team_locations(config, locations):
    team_locations = get_team_locations(config['teams'])
    duplicates = find_duplicates(team_locations)

    if not duplicates:
        logging.info("Config includes %s unique team-hometowns." % (len(team_locations)))
    else:
        logging.info("Config includes %s team-hometowns from which %s are included at least twice." % (len(locations), len(duplicates)))
        logging.info("Duplicate team-hometowns found: %s"% (duplicates))

    # Check if each team location is included in locations
    missing_team_locations = [location for location in team_locations if location not in locations]
    if missing_team_locations:
        logging.warning("The following team hometowns are not included in the fetched locations: %s" % (missing_team_locations))
    else:
        logging.info("All team hometowns are included in the fetched locations.")

    # Check if each location has a corresponding team location
    missing_locations = [location for location in locations if location not in team_locations]
    if missing_locations:
        logging.warning("The following locations do not have corresponding team hometown: %s" % (missing_locations))
    else:
        logging.info("No location is fetched without a corresponding team hometown.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    config = load_config('config.json')

    locations = validate_names(config, 'locations')
    teams = validate_names(config, 'teams')

    validate_team_locations(config, locations)
import logging
import json
from collections import Counter

def load_config(file_path):
    """Load configuration from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_names(elements):
    """Extract names from a list of elements."""
    return [element['name'] for element in elements]

def get_team_locations(current_teams):
    """Get locations of teams from the configuration."""
    return [team['location'] for team in current_teams]

def find_duplicates(names):
    """Find duplicate names in a list."""
    location_counts = Counter(names)
    return [name for name, count in location_counts.items() if count > 1]

def validate_names(current_config, element_type):
    """Validate names in the configuration and log duplicates."""
    names = get_names(current_config[element_type])
    duplicates = find_duplicates(names)

    if not duplicates:
        logging.info("Config includes %s unique %s.", len(names), element_type)
    else:
        logging.warning("Config includes %s %s from which %s are included at least twice.",
                            len(names),
                            element_type,
                            len(duplicates)
                        )

        logging.warning("Duplicate %s found: %s",
                            element_type,
                            duplicates
                        )

    return list(set(names))

def validate_team_locations(current_config, current_locations):
    """Validate team locations against fetched locations and log discrepancies."""
    team_locations = get_team_locations(current_config['teams'])
    duplicates = find_duplicates(team_locations)

    if not duplicates:
        logging.info("Config includes %s unique hometowns.", len(team_locations))
    else:
        logging.info("Config includes %s hometowns from which %s are included at least twice.",
                        len(current_locations),
                        len(duplicates)
                    )

        logging.info("Duplicate team-hometowns found: %s",
                        duplicates
                    )

    # Check if each team location is included in locations
    missing_team_locations = [location
                                for location in team_locations
                                if location not in current_locations
                            ]

    if missing_team_locations:
        logging.warning("The following hometowns are not included in the fetched locations: %s",
                            missing_team_locations
                        )
    else:
        logging.info("All hometowns are included in the fetched locations.")

    # Check if each location has a corresponding team location
    missing_locations = [location
                            for location in current_locations
                            if location not in team_locations
                        ]

    if missing_locations:
        logging.warning("The following locations do not have corresponding hometown: %s",
                            missing_locations
                        )
    else:
        logging.info("No location is fetched without a corresponding hometown.")


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

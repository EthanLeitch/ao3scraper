# This module contains important constants used in ao3scraper, and is imported by most files.

from os import path
from os import environ
from platformdirs import user_data_dir, user_config_dir
from datetime import datetime
from importlib import metadata
from yaml import load, Loader

# Custom modules
import ao3scraper.file_validator as file_validator

# Set important constants!
APP_NAME = "ao3scraper"
APP_AUTHOR = "EthanLeitch"
APP_VERSION = metadata.version(APP_NAME)
ALEMBIC_VERSION = 'ca2dfefaf0b6'

DATA_PATH = path.join(user_data_dir(APP_NAME, APP_AUTHOR)) + "/"
CONFIG_PATH = path.join(user_config_dir(APP_NAME, APP_AUTHOR)) + "/"

DATABASE_FILE_PATH = DATA_PATH + "fics.db"
CONFIG_FILE_PATH = CONFIG_PATH + "config.yaml"

# Set DATABASE_FILE_PATH environment variable for alembic
environ.setdefault("DATABASE_FILE_PATH", DATABASE_FILE_PATH)

CONFIG_TEMPLATE = """
# Formatting of table
max_row_length: 120
warnings: false
stale_threshold: 60
stale_styles: deep_sky_blue4
updated_styles: '#ffcc33 bold'

# Column attributes
table_template:
- column: title
  name: Title
  styles: magenta
- column: $chapters
  name: Chapters
  styles: green
- column: date_updated
  name: Last updated
  styles: cyan
- column: status
  name: Status
  styles: violet
"""

"""
Currently this list is only avaliable by fetching an instance of a Work's metadata (AO3.Work.metadata).
This is done in construct_list.py
'id' has been excluded from this list to prevent conflicts with the SQLAlchemy primary_key. 
"""
TABLE_COLUMNS = ['date_edited', 'date_published', 'date_updated', 'bookmarks', 'categories', 'nchapters', 'characters', 'complete', 'comments', 'expected_chapters', 'fandoms', 'hits', 'kudos', 'language', 'rating', 'relationships', 'restricted', 'status', 'summary', 'tags', 'title', 'warnings', 'words', 'collections', 'authors', 'series', 'chapter_titles']
CUSTOM_COLUMNS = ['$chapters', '$latest_chapter']

# Check that config.yaml and fics.db exist
file_validator.main()

# Load user's custom preferences from config.yaml
with open(CONFIG_FILE_PATH, 'r') as file:
    config_file = load(file, Loader=Loader)

# Load each preference as a constant variable
MAX_ROW_LENGTH = config_file['max_row_length']
WARNINGS = config_file['warnings']
STALE_THRESHOLD = config_file['stale_threshold']
STALE_STYLES = config_file['stale_styles']
UPDATED_STYLES = config_file['updated_styles']
TABLE_TEMPLATE = config_file['table_template']

# Check that all the columns listed in the config file are valid
for i in TABLE_TEMPLATE:
    if i['column'] not in TABLE_COLUMNS and i['column'] not in CUSTOM_COLUMNS:
        print(f"{i['column']} is not a valid column.")

# Other constants
MARKER = "# Enter one url on each line to add it to the database. This line will not be recorded."

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
NOW = datetime.now()
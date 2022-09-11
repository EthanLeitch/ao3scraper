# This module contains important constants used in ao3scraper, and is imported by most files.

from os import path
from tkinter.tix import COLUMN
from platformdirs import user_data_dir, user_config_dir
from datetime import datetime
from configparser import ConfigParser
from importlib import metadata

# Custom modules
import file_validator

APP_NAME = "ao3scraper"
APP_AUTHOR = "EthanLeitch"
APP_VERSION = metadata.version(APP_NAME)

DATABASE_PATH = path.join(user_data_dir(APP_NAME, APP_AUTHOR)) + "/"
CONFIG_PATH = path.join(user_config_dir(APP_NAME, APP_AUTHOR)) + "/"

DATABASE_FILE_PATH = DATABASE_PATH + "fics.db"
CONFIG_FILE_PATH = CONFIG_PATH + "config.ini"

CONFIG_TEMPLATE = """[main]
highlight_stale_fics = yes
stale_threshold = 60
"""

"""
Currently this list is only avaliable by fetching an instance of a Work's metadata (AO3.Work.metadata).
'id' has been excluded from this list to prevent conflicts with the SQLAlchemy primary_key. 
"""
TABLE_COLUMNS = ['date_edited', 'date_published', 'date_updated', 'bookmarks', 'categories', 'nchapters', 'characters', 'complete', 'comments', 'expected_chapters', 'fandoms', 'hits', 'kudos', 'language', 'rating', 'relationships', 'restricted', 'status', 'summary', 'tags', 'title', 'warnings', 'words', 'collections', 'authors', 'series', 'chapter_titles']

# Check that config.ini and fics.db exist
file_validator.main()

# Load user's custom preferences from config.ini
config_file = ConfigParser()
config_file.read(CONFIG_FILE_PATH)

HIGHLIGHT_STALE_FICS = config_file.get('main', 'highlight_stale_fics')
STALE_THRESHOLD = config_file.getint('main', 'stale_threshold')

# Other constants
MARKER = "# Enter one url on each line to add it to the database. This line will not be recorded."

# DATE_FORMAT = "%Y-%m-%d" 
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
NOW = datetime.now()
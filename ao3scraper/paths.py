from os import path
from platformdirs import *


APP_NAME = "ao3scraper"
APP_AUTHOR = "EthanLeitch"

DATABASE_PATH = path.join(user_data_dir(APP_NAME, APP_AUTHOR)) + "/"
CONFIG_PATH = path.join(user_config_dir(APP_NAME, APP_AUTHOR)) + "/"

print(DATABASE_PATH)
print(CONFIG_PATH)

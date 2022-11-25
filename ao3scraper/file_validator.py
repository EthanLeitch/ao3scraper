# This module validates that MySQL database (fics.db) and the config file (config.yaml) exist, if not, it creates them.

import sqlite3
from os import path
import pathlib
from yaml import dump, Dumper

# Import custom modules
import constants

def main():
    # Create config file if config file does not exist
    if not path.exists(constants.CONFIG_FILE_PATH):
        print("No config file found. Creating new config file...")

        pathlib.Path(constants.CONFIG_PATH).mkdir(parents=True, exist_ok=True)
        
        with open(constants.CONFIG_FILE_PATH, 'w') as file:
            # Convert CONFIG_TEMPLATE to yaml, and disable the alphabetical key sorting done by yaml.dump
            config_file_dump = dump(constants.CONFIG_TEMPLATE, Dumper=Dumper, sort_keys=False)
            # Write to file
            file.write(config_file_dump)
            pass

        print("Config file created.")
        print("You can change configuration options in config.yaml")

    # Create database file if database does not exist
    if not path.exists(constants.DATABASE_FILE_PATH):
        print("No database found. Creating new database...")

        pathlib.Path(constants.DATA_PATH).mkdir(parents=True, exist_ok=True)
 
        # Connect to database
        connection = sqlite3.connect(constants.DATABASE_FILE_PATH)

        cursor = connection.cursor()

        cursor.execute("CREATE TABLE fics (id INTEGER)")
        for column in constants.TABLE_COLUMNS:
            cursor.execute(f"ALTER TABLE fics ADD {column} TEXT")

        connection.commit()
        connection.close()

        print("Database created.\n")
        exit()

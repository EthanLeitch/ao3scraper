# This module validates that MySQL database (fics.db) and the config file (config.ini) exist, if not, it creates them.

import sqlite3
from os import path
import pathlib

# Import custom modules
import constants

def main():
    # Create config file if config file does not exist
    if not path.exists(constants.CONFIG_FILE_PATH):
        print("No config file found. Creating new config file...")

        pathlib.Path(constants.CONFIG_PATH).mkdir(parents=True, exist_ok=True)
        
        with open(constants.CONFIG_FILE_PATH, 'w') as file:
            file.write(constants.CONFIG_TEMPLATE)
            pass

        print("Config file created.")
        print("You can change configuration options in config.ini")

    # Create database file if database does not exist
    if not path.exists(constants.DATABASE_FILE_PATH):
        print("No database found. Creating new database...")

        pathlib.Path(constants.DATABASE_PATH).mkdir(parents=True, exist_ok=True)
 
        # Connect to database
        connection = sqlite3.connect(constants.DATABASE_FILE_PATH)

        cursor = connection.cursor()
        cursor.execute("CREATE TABLE fics (url TEXT, title TEXT, chapters TEXT, updated TEXT)")

        connection.commit()
        connection.close()

        print("Database created.\n")
        exit()

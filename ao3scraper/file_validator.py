# This module validates that MySQL database (fics.db) and the config file (config.yaml) exist, if not, it creates them.

import sqlite3
from os import path
import pathlib
#from yaml import dump, Dumper
from ruamel.yaml import YAML

from sqlite3 import OperationalError
from alembic.config import Config
from alembic import command
import uuid
from shutil import copy

# Import custom modules
import ao3scraper.constants as constants

def main():
    # Create config file if config file does not exist
    if not path.exists(constants.CONFIG_FILE_PATH):
        print("No config file found. Creating new config file...")

        pathlib.Path(constants.CONFIG_PATH).mkdir(parents=True, exist_ok=True)
        
        with open(constants.CONFIG_FILE_PATH, 'w') as file:
            # Convert CONFIG_TEMPLATE to yaml, and disable the alphabetical key sorting done by yaml.dump
            #config_file_dump = dump(constants.CONFIG_TEMPLATE, Dumper=Dumper, sort_keys=False)
            yaml = YAML()
            template = yaml.load(constants.CONFIG_TEMPLATE)
            # Write to file
            yaml.dump(template, file)
            #file.write(yaml.dump(template))
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

        # Create fics table
        cursor.execute("CREATE TABLE fics (id INTEGER)")
        for column in constants.TABLE_COLUMNS:
            cursor.execute(f"ALTER TABLE fics ADD {column} TEXT")
            
        # Create metadata table
        cursor.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num));")
        query = f"INSERT INTO alembic_version VALUES ('{constants.ALEMBIC_VERSION}');"
        cursor.execute(query)

        connection.commit()
        connection.close()

        print("Database created.\n")
    
    validate_database()

def validate_database():
    # A new database has NOT been created, so we must validate the existing one.
    # Connect to database
    connection = sqlite3.connect(constants.DATABASE_FILE_PATH)
    cursor = connection.cursor()

    # Retrive version_num
    try:
        cursor.execute("SELECT version_num FROM alembic_version;")
        version_num = [item[0] for item in cursor.fetchall()]
        version_num = version_num[0]
    except OperationalError:
        print(f"The local database version could not be verified. It may be a legacy version.")
        upgrade_database()
    except IndexError:
        print("The local database version entry does not exist. This may be because of a previous database migration that failed.")
        exit()

    if version_num != constants.ALEMBIC_VERSION:
        print(f"ao3scraper is on database revision {constants.ALEMBIC_VERSION}, but the local database is on revision {version_num}.")
        upgrade_database()
    
def upgrade_database():
    print("Would you like to migrate to the version supported by ao3scraper? (y/n)")
    
    choice = input(" > ").lower()
    if choice == 'y':
        backup_db_name = "fics_backup_" + str(uuid.uuid4().hex) + ".db"
        backup_db_path = path.join(constants.DATA_PATH, 'backups', backup_db_name)

        pathlib.Path(path.join(constants.DATA_PATH, 'backups')).mkdir(parents=False, exist_ok=True)
        print(f"Saving backup of current database to {backup_db_path}")
        copy(constants.DATABASE_FILE_PATH, backup_db_path)

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, constants.ALEMBIC_VERSION)
        quit()
    else:
        # Quitting is the safest option, as ao3scraper doesn't do error handling for the database very well.
        quit()
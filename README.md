# ao3scraper
A python webscraper that scrapes AO3 for fanfiction data, stores it in a database, and highlights entries when they are updated.

![Fanfics Table](https://i.ibb.co/80r9vwR/Fanfic-Table.png)

*Table with an updated entry highlighted.*

## Installation
Install required packages with:

    poetry install

## Usage
    Usage: python3 ao3scraper [OPTIONS]

    Options:
    -s, --scrape          Launches scraping mode.
    -c, --cache           Prints the last scraped table.
    -l, --list            Lists all entries in the database.
    -a, --add TEXT        Adds a single url to the database.
    --add-urls            Opens a text file to add multiple urls to the database.
    -d, --delete INTEGER  Deletes an entry from the database.
    -v, --version         Display version of ao3scraper and other info.
    --help                Show this message and exit.

## Configuration
ao3scraper is ridiculously customisable, and most aspects of the program can be modified from here.
To find the configuration file location, run `python3 ao3scraper -v`.

ao3scraper uses [rich](https://rich.readthedocs.io/en/stable/style.html)'s styling. To disable any styling options, replace the styling value with 'none'.

Fics have many attributes that are not displayed by default. To add these columns, create a new option under table_template, like so:
```yaml
table_template:
- column: characters # The specified attribute
  name: Characters :) # This is what the column will be labelled as
  styles: none # Rich styling
```
A complete list of attributes can be found [on the wiki](https://github.com/EthanLeitch/ao3scraper/wiki/Fic-Attributes/).

## Migrating the database
If you're updating from a legacy version of ao3scraper (before 1.0.0), move `fics.db` to the data location. 
This can be found by running `python3 ao3scraper -v`.
The migration wizard will then prompt you to upgrade your database. 
If you accept, a backup of the current `fics.db` will be created in `/backups`, and migration will proceed.

## Contributing
Contributions are always appreciated. Submit a pull request with your suggested changes!

## Acknowledgements
ao3scraper would not be possible without the existence of [ao3_api](https://github.com/ArmindoFlores/ao3_api/) and the work of its [contributors](https://github.com/ArmindoFlores/ao3_api/graphs/contributors).
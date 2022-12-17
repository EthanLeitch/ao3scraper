# ao3scraper
A python webscraper that scrapes AO3 for fanfiction data, stores it in a database, and highlights entries when they are updated.

![Fanfics Table](https://i.ibb.co/hgS7BmW/fanfics-table.png)

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

## Contributing
Contributions are always appreciated. Submit a pull request with your suggested changes!

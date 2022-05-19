# Web scraping
# from multiprocessing import connection
import requests
from requests.exceptions import Timeout
from bs4 import BeautifulSoup

# Sqlite handling and validation 
import sqlite3
import os.path

# Formatting
from rich.console import Console
from rich.table import Table
from rich.progress import track

import click

# Setup fic_array item constants
URL_POS = 0
TITLE_POS = 1
CHAPTER_POS = 2
LAST_UPDATED_POS = 3

MARKER = "# Enter one url on each line to add it to the database. This line will not be recorded."

# Create columns of rich table
table = Table(title="Fanfics")

table.add_column("Index", justify="left", style="#bcbcbc", no_wrap=True)
table.add_column("Title", style="magenta")
table.add_column("Chapter", style="green")
table.add_column("Last updated", justify="left", style="cyan", no_wrap=True)

# Create database file if database does not exist
if not os.path.exists("fics.db"):
    print("No database found. Creating new database...")

    # Connect to database
    connection = sqlite3.connect("fics.db")

    cursor = connection.cursor()
    cursor.execute("CREATE TABLE fics (url TEXT, title TEXT, chapters TEXT, updated TEXT)")

    connection.commit()
    connection.close()

    print("Database created.\n")
    exit()


# Start click command
@click.command()
@click.option('--scrape', '-s', is_flag=True, help='Launches scraping mode.')
@click.option('--list', '-l', is_flag=True, help='Lists all entries in the database.')
@click.option('--add', '-a', help='Adds a single url to the database.')
@click.option('--add-urls', is_flag=True, help='Opens a text file to add multiple urls to the database.')
@click.option('--delete', '-d', help='Deletes an entry from the database.', type=int)
def main(scrape, add, add_urls, list, delete):
    if scrape:
        scrape_urls()
    elif list:
        construct_rich_table()
    elif add:
        add_url_single(add)
    elif add_urls:
        add_url_multiple()
    elif delete:
        delete_entry(delete)
    else:
        with click.Context(main, info_name='ao3scraper.py') as ctx:
            click.echo(main.get_help(ctx))

    connection.close()
    exit()


def scrape_urls():
    # Check if AO3 is online / accessible
    print("Checking if AO3 servers are online...")
    try:
        requests.get("https://archiveofourown.org", timeout=10)
    except Timeout:
        print("Could not connect to AO3 servers. (timed out)")
        exit()
    else:
        print("Contacted servers successfully.")

    # Handle each url
    for item in track(fic_table, description="Fetching data from AO3..."):
        # Fetch all external chapter values of URLS
        web_tags = get_tags(item[URL_POS], item)

        # Get item index
        item_index = str(fic_table.index(item) + 1) + "."

        # 4xx and 5xx error checking
        if isinstance(web_tags, int):
            table.add_row(item_index,
                          "[link=" + item[URL_POS] + "]" + str(web_tags) + " ERROR WHEN FETCHING INFORMATION[/link]",
                          item[CHAPTER_POS], item[LAST_UPDATED_POS], style="red")
            continue

        # Check if url has local tags: title, chapters, last updated
        if None in item:
            table.add_row(item_index, "[link=" + item[URL_POS] + "]" + web_tags[0] + "[/link]", web_tags[1],
                          web_tags[2])
        else:
            # Compare each web chapter value to each local chapter value
            if int(web_tags[1].split("/")[0]) > int(item[CHAPTER_POS].split("/")[0]):
                table.add_row("[#ffcc33][bold]" + item_index,
                              "[#ffcc33][bold][link=" + item[URL_POS] + "]" + web_tags[0] + "[/link]",
                              "[#ffcc33][bold]" + web_tags[1],
                              "[#ffcc33][bold]" + web_tags[2])
            else:
                table.add_row(item_index, "[link=" + item[URL_POS] + "]" + web_tags[0] + "[/link]", web_tags[1],
                              web_tags[2])

        # Write item information to database
        # here be black magic and code arcane
        target_entry = fic_table[fic_table.index(item)]

        cursor.execute(
            "UPDATE fics SET title = \"" + web_tags[0] + "\", chapters = \"" + web_tags[1] + "\", updated = \"" +
            web_tags[2] + "\" WHERE url = \"" + target_entry[URL_POS] + "\";")
        connection.commit()

    # Print rich table
    print()
    console.print(table)


# Function to fetch all online tags for one URL
def get_tags(url, item):
    page = requests.get(url)

    # 4xx and 5xx Error Detection
    if not page.ok:
        """
        console.print()
        console.print(page.status_code, "Error!", style="red", highlight=False)
        console.print("URL responsible:", item[URL_POS], style="red")
        """
        return page.status_code
        # continue would work here? but not in a loop

    soup = BeautifulSoup(page.content, "html.parser")

    # Return tags in order: title, chapters, last updated.
    return [soup.find_all(class_="title heading")[0].string.strip(),
            soup.find_all(class_="chapters")[1].string,
            soup.find_all(class_="status")[1].string]


def construct_rich_table():
    # Refresh table entries
    cursor.execute("SELECT * FROM fics")
    fic_table = cursor.fetchall()

    for item in fic_table:
        """
        item_id = str(item[1])
        item_id = item_id.split("archiveofourown.org/works/")[1] # Remove everything before and including this str
        item_id = item_id.split("/", 1)[0] # Remove everything after and including this string
        """

        # Get item index
        item_index = str(fic_table.index(item) + 1) + "."

        # Check if title field is empty
        if item[TITLE_POS] is None:
            table.add_row(item_index, "[link=" + item[URL_POS] + "]FIC DATA NOT YET SCRAPED[/link]", item[CHAPTER_POS],
                          item[LAST_UPDATED_POS])
        else:
            # table.add_row(str(fic_table.index(item) + 1) + ". [link=" + item[1] + "]" + item_id + "[/link]",
            # item[0], item[2], item[3])
            table.add_row(item_index, "[link=" + item[URL_POS] + "]" + item[TITLE_POS] + "[/link]", item[CHAPTER_POS],
                          item[LAST_UPDATED_POS])

    # Print rich table
    print()
    console.print(table)


def add_url_multiple():
    message = click.edit(MARKER + '\n')
    if message is not None:
        message_lines = message.split(MARKER, 1)[1].rstrip('\n').lstrip('\n')
        url_to_parse = message_lines.split('\n')

        for item in url_to_parse:
            if str(fic_table).find(item) != -1:
                print(item, "already in database.")
                continue
            cursor.execute("INSERT INTO fics (url) VALUES ('" + str(item) + "');")
            connection.commit()
            print("Added " + url_to_parse[url_to_parse.index(item)])  # improve this logic

    construct_rich_table()


def add_url_single(entry):
    if str(fic_table).find(entry) != -1:
        print(entry, "already in database.")
    else:
        cursor.execute("INSERT INTO fics (url) VALUES ('" + entry + "');")
        connection.commit()
        print("Added " + entry)

    construct_rich_table()


def delete_entry(entry):
    try:
        # here be black magic and code arcane
        target_entry = fic_table[(entry - 1)]   
        cursor.execute("DELETE FROM fics WHERE url = '" + target_entry[URL_POS] + "';")
        # cursor.execute("DELETE FROM fics WHERE rowid = " + entry + ";")
    except IndexError:
        print("Number out of index range.")
        exit()
    connection.commit()
    print("Deleted entry number " + str(entry))

    construct_rich_table()


if __name__ == "__main__":
    # Connect to database
    connection = sqlite3.connect("fics.db")
    cursor = connection.cursor()

    # Create table
    cursor.execute("SELECT * FROM fics")
    fic_table = cursor.fetchall()

    console = Console()

    main()

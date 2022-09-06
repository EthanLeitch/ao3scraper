# The main program for ao3scraper.

# Web scraping
import requests
from requests.exceptions import Timeout
from bs4 import BeautifulSoup

# Formatting
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.style import Style

# Other modules
import sqlite3
import click
from datetime import datetime

# Custom modules
import constants

# Setup fic_array item constants
URL_POS = 0
TITLE_POS = 1
CHAPTER_POS = 2
LAST_UPDATED_POS = 3

# Setup rich styles
stale_style = Style(color="deep_sky_blue4", bold=True)
updated_style = Style(color="#ffcc33", bold=True)

# Create columns of rich table
table = Table(title="Fanfics")
table.add_column("Index", justify="left", style="#bcbcbc", no_wrap=True)
table.add_column("Title", style="magenta")
table.add_column("Chapter", style="green")
table.add_column("Last updated", justify="left", style="cyan", no_wrap=True)

# Connect to database
connection = sqlite3.connect(constants.DATABASE_FILE_PATH)
cursor = connection.cursor()

# Load table
cursor.execute("SELECT * FROM fics")
fic_table = cursor.fetchall()

console = Console()


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
    for count, item in enumerate(track(fic_table, description="Fetching data from AO3...")):
        # Fetch all external chapter values of URLS
        web_tags = get_tags(item[URL_POS])

        # Get item index
        item_index = count + 1

        # 4xx and 5xx error checking - checks whether get_items returns an int. If so, it's a 5xx or 4xx error.
        if isinstance(web_tags, int):
            add_row(item_index, item[URL_POS], f"{web_tags} ERROR WHEN FETCHING INFORMATION",
                    item[CHAPTER_POS], item[LAST_UPDATED_POS], "red")
            continue

        # Check if url has local tags: title, chapters, last updated
        if None in item:
            add_row(item_index, item[URL_POS], web_tags["title"], web_tags["chapters"], web_tags["last updated"])
        else:
            # Compare each web chapter value to each local chapter value
            web_chapter = int(web_tags["chapters"].split("/")[0])
            local_chapter = int(item[CHAPTER_POS].split("/")[0])

            if web_chapter > local_chapter:
                add_row(item_index, item[URL_POS], web_tags["title"], f"""{web_tags["chapters"]} (+{web_chapter - local_chapter})""", web_tags["last updated"], updated_style)
            else:
                # Turn upload date of fic into correct format 
                then = datetime.strptime(web_tags["last updated"], constants.DATE_FORMAT)
                if constants.HIGHLIGHT_STALE_FICS and (constants.NOW - then).days > constants.STALE_THRESHOLD:
                    add_row(item_index, item[URL_POS], web_tags["title"], web_tags["chapters"], web_tags["last updated"], stale_style)
                else:
                    add_row(item_index, item[URL_POS], web_tags["title"], web_tags["chapters"], web_tags["last updated"])

        # Write item information to database
        target_entry = fic_table[count]

        # Must be triple-quotations in case fic title has quotation marks which will mess up the SQL statement
        cursor.execute(f"""UPDATE fics SET title = "{web_tags["title"]}", chapters = "{web_tags["chapters"]}", updated = "{web_tags["last updated"]}" WHERE url = "{target_entry[URL_POS]}";""")
        connection.commit()

    # Print rich table
    print()
    console.print(table)


def add_url_multiple():
    message = click.edit(constants.MARKER + '\n')
    if message is not None:
        message_lines = message.split(constants.MARKER, 1)[1].rstrip('\n').lstrip('\n')
        urls_to_parse = message_lines.split('\n')

        for count, item in enumerate(urls_to_parse):
            if str(fic_table).find(item) != -1:
                print(item, "already in database.")
                continue
            cursor.execute(f"INSERT INTO fics (url) VALUES ('{str(item)}');")
            connection.commit()
            print("Added " + urls_to_parse[count])

    construct_rich_table()


def add_url_single(entry):
    if str(fic_table).find(entry) != -1:
        print(entry, "already in database.")
    else:
        cursor.execute(f"INSERT INTO fics (url) VALUES ('{entry}');")
        connection.commit()
        print("Added", entry)

    construct_rich_table()


def delete_entry(entry):
    try:
        # here be black magic and code arcane
        target_entry = fic_table[(entry - 1)]
        cursor.execute(f"DELETE FROM fics WHERE url = '{target_entry[URL_POS]}';")
        # cursor.execute("DELETE FROM fics WHERE rowid = " + entry + ";")
    except IndexError:
        print("Number out of index range.")
        exit()
    connection.commit()
    print("Deleted entry number", str(entry))

    construct_rich_table()


# Function to fetch all online tags for one URL
def get_tags(url):
    page = requests.get(url)

    # 4xx and 5xx Error Detection
    if not page.ok:
        return page.status_code

    soup = BeautifulSoup(page.content, "html.parser")

    # Return tags in order: title, chapters, last updated.
    return {
        "title": soup.find_all(class_="title heading")[0].string.strip(),
        "chapters": soup.find_all(class_="chapters")[1].string,
        "last updated": soup.find_all(class_="status")[1].string
    }


def construct_rich_table():
    # Refresh table entries
    cursor.execute("SELECT * FROM fics")
    fic_table = cursor.fetchall()

    for count, item in enumerate(fic_table):
        # Get item index
        item_index = str(count + 1)

        # Check if title field is empty
        if item[TITLE_POS] is None:
            add_row(item_index, item[URL_POS], "FIC DATA NOT YET SCRAPED", item[CHAPTER_POS], item[LAST_UPDATED_POS])
        else:
            # Turn upload date of fic into correct format 
            then = datetime.strptime(item[LAST_UPDATED_POS], constants.DATE_FORMAT)
            if constants.HIGHLIGHT_STALE_FICS and (constants.NOW - then).days > constants.STALE_THRESHOLD:
                add_row(item_index, item[URL_POS], item[TITLE_POS], item[CHAPTER_POS], item[LAST_UPDATED_POS], stale_style)
            else:
                add_row(item_index, item[URL_POS], item[TITLE_POS], item[CHAPTER_POS], item[LAST_UPDATED_POS])

    # Print rich table
    print()
    console.print(table)


def add_row(index, url, title, chapter, last_updated, styling=""):
    table.add_row(f"{index}.", f"[link={url}]{title}[/link]", chapter, last_updated, style=styling)


if __name__ == "__main__":
    main()

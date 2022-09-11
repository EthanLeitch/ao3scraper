# The main program for ao3scraper.

# Web scraping
import requests
from requests.exceptions import Timeout, ConnectionError
from concurrent.futures import ThreadPoolExecutor

# Formatting
from rich.console import Console
from rich.table import Table
from rich.style import Style
from rich.progress import Progress

# Other modules
import AO3
import click
from pprint import pprint
from deepdiff import DeepDiff
from dictdiffer import diff
from datetime import datetime

# Custom modules
import constants
import database

# Setup rich styles
stale_style = Style(color="deep_sky_blue4", bold=True)
updated_style = Style(color="#ffcc33", bold=True)

# Create columns of rich table
table = Table(title="Fanfics")
table.add_column("Index", justify="left", style="#bcbcbc", no_wrap=True)
table.add_column("Title", style="magenta")
table.add_column("Chapters", style="green")
table.add_column("Last updated", justify="left", style="cyan", no_wrap=True)
console = Console()

# Read database
fic_ids = database.get_fic_ids()
local_fics = database.get_all_fics()

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

    exit()


def scrape_urls():
    """
    # Check if AO3 is online / accessible
    print("Checking if AO3 servers are online...")
    try:
        requests.get("https://archiveofourown.org", timeout=10)
    except Timeout:
        print("Could not reach AO3 servers. (Timeout)")
        exit()
    except ConnectionError:
        print("Could not reach AO3 servers. (ConnectionError)")
        exit()
    else:
        print("Contacted servers successfully.")
    """
    
    external_fics = []

    # The load_fic function that each thread performs
    def load_fic(id):
        try:
            # Fetch fic's metadata
            fic = AO3.Work(id).metadata
            external_fics.append(fic)

        except Exception as e:
            # print(f"{e} {id}")
            external_fics.append({'Exception': e, 'id': id})
            progress.update(progress_bar, advance=1)
        
        progress.update(progress_bar, advance=1)
    
    # Track and create thread pool
    with Progress() as progress:
        progress_bar = progress.add_task("Fetching data from AO3...", total=len(fic_ids))

        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(load_fic, fic_ids)

    # Handle adding of each fic
    for count, fic in enumerate(external_fics):
        add_row(fic, count)

        if 'Exception' in fic:
            continue

        """
        difference = DeepDiff(local_fics[count], external_fics[count])
        pprint(difference)
        print("=========================================================")
        """

        # Convert every datatype to STRING so it can be stored in the database.
        for keys in fic:
            fic[keys] = str(fic[keys])

        # Update database
        database.update_fic(fic, fic['id'])

    # Print rich table
    print()
    console.print(table)


def add_url_multiple():
    message = click.edit(constants.MARKER + '\n')

    if message is not None:
        message_lines = message.split(constants.MARKER, 1)[1].rstrip('\n').lstrip('\n')
        urls_to_parse = message_lines.split('\n')

        for count, item in enumerate(urls_to_parse):
            entry_id = AO3.utils.workid_from_url(item)
            if entry_id == None:
                print(f"{item} is not a valid url.")
            elif str(entry_id) in fic_ids:
                print(item, "already in database.")
            else:
                database.add_fic(entry_id)
                print("Added " + urls_to_parse[count])

    construct_rich_table()


def add_url_single(entry):
    entry_id = AO3.utils.workid_from_url(entry)

    if entry_id == None:
        print(f"{entry} is not a valid url.")
    elif str(entry_id) in fic_ids:
        print(f"{entry_id} already in database.")
    else:
        database.add_fic(entry_id)
        print("Added", entry)

    construct_rich_table()


def delete_entry(entry):
    try:
        # Decrease entry by one because Python arrays start at 0.
        target_entry = local_fics[(entry - 1)]
        database.delete_fic(target_entry['id'])
    except IndexError:
        print("Number out of index range.")
        exit()
    print("Deleted entry number", str(entry))

    construct_rich_table()


def construct_rich_table(read_again=True):
    if read_again is True:
        # Read database again
        local_fics = database.get_all_fics()

    for count, fic in enumerate(local_fics):
        add_row(fic, count)

    # Print rich table
    print()
    console.print(table)


def add_row(fic, count, styling=""):
    # Offset index by 1 because Python arrays start at 0.
    index = str(count + 1)

    # Create link for fic
    fic_link = f"https://archiveofourown.org/works/{fic['id']}" 

    # If key 'Exception' in fic, display error information.
    if 'Exception' in fic:
        table.add_row(f"{index}.", f"[link={fic_link}]ERROR: {fic['Exception']}[/link]", style="red")
        return

    # Check if title field is empty. If it is, we assume that the fic has not yet been scraped.
    if fic['title'] is None:
        table.add_row(f"{index}.", f"[link={fic_link}]FIC DATA NOT YET SCRAPED[/link]", style=styling)
        return

    if fic['expected_chapters'] is None:
        fic['expected_chapters'] = '?'

    # Turn upload date of fic into correct format 
    then = datetime.strptime(fic['date_updated'], constants.DATE_FORMAT)

    if constants.HIGHLIGHT_STALE_FICS and (constants.NOW - then).days > constants.STALE_THRESHOLD:
        table.add_row(f"{index}.", f"[link={fic_link}]{fic['title']}[/link]", f"{fic['nchapters']}/{fic['expected_chapters']}", str(fic['date_updated']), style=stale_style)
    else:
        table.add_row(f"{index}.", f"[link={fic_link}]{fic['title']}[/link]", f"{fic['nchapters']}/{fic['expected_chapters']}", str(fic['date_updated']), style=styling)


if __name__ == "__main__":
    main()

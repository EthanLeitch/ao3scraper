# The main program for ao3scraper.

# Web scraping
import requests
from requests.exceptions import Timeout, ConnectionError
from concurrent.futures import ThreadPoolExecutor

# Formatting
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

# Other modules
import AO3
import click
from datetime import datetime
import copy

# Custom modules
import constants
import database

# Create columns of rich table
table = Table(title="Fanfics")
table.add_column("Index")

args = []
for i in constants.TABLE_TEMPLATE:
    table.add_column(i["name"], style=i["styles"])
    args.append(i["column"])

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
@click.option('--version', '-v', is_flag=True, help='Display version of ao3scraper and other info.')
def main(scrape, add, add_urls, list, delete, version):
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
    elif version:
        print(
            f"Version: {constants.APP_VERSION}\n"
            f"Database location: {constants.DATABASE_PATH}\n"
            f"Config location: {constants.CONFIG_PATH}\n"
        )
        console.print("Made with :heart: by [link=https://github.com/EthanLeitch]Ethan Leitch[/link].")
    else:
        with click.Context(main, info_name='ao3scraper.py') as ctx:
            click.echo(main.get_help(ctx))


def scrape_urls():
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
    
    # Create array of None that will be replaced later depending on the thread's index.
    external_fics = [None for fic in fic_ids]

    # The load_fic function that each thread performs
    def load_fic(id):
        try:
            # Fetch fic's metadata
            fic = AO3.Work(id).metadata
            
            # Place each fic in correct array position. NOTE: This may not be particularly efficient as the entire list is enumerated by each thread.
            for count, item in enumerate(fic_ids):
                if fic["id"] == item:
                    external_fics[count] = fic

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
        for value in fic:
            # If type of entry is list, store it as comma-seperated string (e.g. "foo, bar").
            if type(fic[value]) is list:
                fic[value] = ", ".join(fic[value])
        
        if type(local_fics[count]['nchapters']) is type(None):
            add_row(fic, count)
        elif int(fic['nchapters']) > int(local_fics[count]['nchapters']):
            add_row(fic, count, styling=constants.UPDATED_STYLES)
        else:
            add_row(fic, count)

        if 'Exception' in fic:
            continue

        # Convert each value into string so it can be stored in the database.
        for value in fic:
            # If type of entry is list, store it as comma-seperated string (e.g. "foo, bar").
            if type(fic[value]) is list:
                fic[value] = ", ".join(fic[value])
            else:
                # Else, convert datatype to string.
                fic[value] = str(fic[value])

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
    elif str(entry_id) in str(fic_ids):
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
    # Copy the fic object so that changes made here are local, and not written to the database.
    fic = copy.copy(fic)

    # Offset index by 1 because Python arrays start at 0.
    index = str(count + 1)

    # Create AO3 link for fic
    fic_link = f"https://archiveofourown.org/works/{fic['id']}" 

    # If key 'Exception' in fic, display error information.
    if 'Exception' in fic:
        table.add_row(f"{index}.", f"[link={fic_link}]ERROR: {fic['Exception']}[/link]", style="red")
        return

    # Check if title field is empty. If it is, we assume that the fic has not yet been scraped.
    if fic['title'] is None:
        table.add_row(f"{index}.", f"[link={fic_link}]FIC DATA NOT YET SCRAPED[/link]", style=styling)
        return

    # Converting expected_chapters from None to '?' makes the "Chapters" column look nicer.
    if fic['expected_chapters'] is None or fic['expected_chapters'] == "None":
        fic['expected_chapters'] = '?'

    # Turn upload date of fic into correct format 
    then = datetime.strptime(fic['date_updated'], constants.DATE_FORMAT)

    # Strip leading and trailing whitespace from fic summaries.
    fic['summary'] = fic['summary'].strip()
    
    # Shorten date string from YYYY-MM-DD XX:XX:XX to YYYY-MM-DD.
    fic['$date_updated'] = fic['date_updated'][:-9]

    # Get chapters as nchapters/expected_chapters
    fic['$chapters'] = f"{fic['nchapters']}/{fic['expected_chapters']}"

    # Get latest chapter
    fic['$latest_chapter'] = fic['chapter_titles'][-1]

    # new_args = [fic[i] for i in args]
    new_args = []
    for count, zipped in enumerate(zip(args, constants.TABLE_TEMPLATE)):
        if constants.TABLE_TEMPLATE[count]['column'] == 'title':
            new_args.append(f"[link={fic_link}]{fic['title']}[/link]")
        else:
            new_args.append(fic[constants.TABLE_TEMPLATE[count]['column']])
    new_args.insert(0, f"{index}.")
    
    if constants.HIGHLIGHT_STALE_FICS and (constants.NOW - then).days > constants.STALE_THRESHOLD:
        table.add_row(*new_args, style=constants.STALE_STYLES)
    else:
        table.add_row(*new_args, style=styling)


if __name__ == "__main__":
    main()

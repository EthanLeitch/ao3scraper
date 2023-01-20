# The main program for ao3scraper.

# Core modules
import AO3
import click

# Web scraping
import requests
from requests.exceptions import Timeout, ConnectionError
from concurrent.futures import ThreadPoolExecutor

# Formatting
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich.traceback import install
install()

# Other modules
from datetime import datetime
import copy
import pickle
import warnings

# Custom modules
import ao3scraper.constants as constants
import ao3scraper.database as database

# Create columns of rich table
table = Table(title="Fanfics", show_lines=True)
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
@click.option('--cache', '-c', is_flag=True, help='Prints the last scraped table.')
@click.option('--list', '-l', is_flag=True, help='Lists all entries in the database.')
@click.option('--add', '-a', help='Adds a single url to the database.')
@click.option('--add-urls', is_flag=True, help='Opens a text file to add multiple urls to the database.')
@click.option('--delete', '-d', help='Deletes an entry from the database.', type=int)
@click.option('--version', '-v', is_flag=True, help='Display version of ao3scraper and other info.')
def main(scrape, cache, list, add, add_urls, delete, version):
    if scrape:
        scrape_urls()
    elif cache:
        print_cached_table()
    elif list:
        construct_rich_table(list)
    elif add:
        add_url_single(add)
    elif add_urls:
        add_url_multiple()
    elif delete:
        delete_entry(delete)
    elif version:
        print(
            f"Version: {constants.APP_VERSION}\n"
            f"Data location: {constants.DATA_PATH}\n"
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
            # Setup custom warning format
            def custom_formatwarning(msg, *args, **kwargs):
                if constants.WARNINGS:
                    return f"(Work: {id}) Warning: {str(msg)}\n"
                return ""

            warnings.formatwarning = custom_formatwarning

            # Fetch fic's metadata
            fic = AO3.Work(id).metadata

            # Place each fic in correct array position. NOTE: This may not be particularly efficient as the entire list is enumerated by each thread.
            for count, item in enumerate(fic_ids):
                if fic["id"] == item:
                    external_fics[count] = fic

        except Exception as e:
            # print(f"{e} {id}")
            for count, local_id in enumerate(fic_ids):
                if id == local_id:
                    if type(e) is AttributeError:
                        e = "The work might be restricted (AttributeError)"

                    external_fics[count] = ({'Exception': str(e), 'id': id})
            
            progress.update(progress_bar, advance=1)
        
        progress.update(progress_bar, advance=1)
    
    # Track and create thread pool
    with Progress() as progress:
        progress_bar = progress.add_task("Fetching data from AO3...", total=len(fic_ids))

        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(load_fic, fic_ids)

    # Handle adding of each fic
    for count, fic in enumerate(external_fics):
        
        if 'Exception' in fic:
            add_row(fic, count)
            continue

        for value in fic:
            # If type of entry is list, store it as comma-seperated string (e.g. "foo, bar").
            if type(fic[value]) is list:
                fic[value] = ", ".join(fic[value])
            
        # Strip leading and trailing whitespace from fic summaries.
        fic['summary'] = fic['summary'].strip()
        
        if type(local_fics[count]['nchapters']) is type(None):
            add_row(fic, count)
        elif int(fic['nchapters']) > int(local_fics[count]['nchapters']):
            add_row(fic, count, styling=constants.UPDATED_STYLES)
        else:
            add_row(fic, count)

        # Convert every value into string so it can be stored in the database.
        for value in fic:
            fic[value] = str(fic[value])
        #fic = [str(fic[value]) for fic[value] in fic]

        # Update database
        database.update_fic(fic, fic['id'])

    # Print rich table
    print()
    console.print(table)

    table.title = "Fanfics (cached)"

    with open(constants.DATA_PATH + "table.pickle", 'wb') as file:
        pickle.dump(table, file, protocol=pickle.HIGHEST_PROTOCOL)


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


def print_cached_table():
    with open(constants.DATA_PATH + "table.pickle", 'rb') as file:
        table_cached = pickle.load(file)
        print()
        console.print(table_cached)


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

    # Check if title or date_published field is empty. If it is, we assume that the fic has not yet been scraped.
    if fic['title'] is None or fic['date_published'] is None:
        table.add_row(f"{index}.", f"[link={fic_link}]FIC DATA NOT YET SCRAPED[/link]", style=styling)
        return

    # Converting expected_chapters from None to '?' makes the "Chapters" column look nicer.
    if fic['expected_chapters'] is None or fic['expected_chapters'] == "None":
        fic['expected_chapters'] = '?'
    
    # Turn upload date of fic into correct format 
    then = datetime.strptime(fic['date_updated'], constants.DATE_FORMAT)

    # Shorten date strings from YYYY-MM-DD XX:XX:XX to YYYY-MM-DD.
    fic['date_published'] = fic['date_published'][:-9]
    fic['date_edited'] = fic['date_edited'][:-9]
    fic['date_updated'] = fic['date_updated'][:-9]

    # Set $chapters to nchapters/expected_chapters (+difference)
    if styling == constants.UPDATED_STYLES:
        difference = int(fic['nchapters']) - int(local_fics[count]['nchapters'])
        fic['$chapters'] = f"{fic['nchapters']}/{fic['expected_chapters']} (+{difference})"
    else:
        fic['$chapters'] = f"{fic['nchapters']}/{fic['expected_chapters']}"

    # Get latest chapter title
    fic['$latest_chapter'] = fic['chapter_titles'][-1]

    # Trim every element to max_row_length
    for data in fic:
        if isinstance(fic[data], str):
            fic[data] = (fic[data][:constants.MAX_ROW_LENGTH].strip() + '...') if len(fic[data]) > constants.MAX_ROW_LENGTH else fic[data]

    new_args = []
    for count, zipped in enumerate(zip(args, constants.TABLE_TEMPLATE)):
        if constants.TABLE_TEMPLATE[count]['column'] == 'title':
            new_args.append(f"[link={fic_link}]{fic['title']}[/link]")
        else:
            new_args.append(fic[constants.TABLE_TEMPLATE[count]['column']])
    new_args.insert(0, f"{index}.")
    
    if (constants.NOW - then).days > constants.STALE_THRESHOLD:
        table.add_row(*new_args, style=constants.STALE_STYLES)
    else:
        table.add_row(*new_args, style=styling)


if __name__ == "__main__":
    main()

# Web scraping
from multiprocessing import connection
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

# Create columns of rich table
table = Table(title="Fanfics")

table.add_column("Index", justify="left", style="red", no_wrap=True)
table.add_column("Title", style="magenta")
table.add_column("Last updated", style="cyan", no_wrap=True)
table.add_column("Chapter", justify="left", style="green")

# Create database file if database does not exist
if not os.path.exists("fics.db"):
    print("No database found. Creating new database...")

    # Connect to database
    connection = sqlite3.connect("fics.db")

    cursor = connection.cursor()
    cursor.execute("CREATE TABLE fics (title TEXT, url TEXT, updated TEXT, chapters TEXT)")
    
    connection.commit()
    connection.close()

    print("Database created.\n")

# Start click command
@click.command()
@click.option('--scan', '-s', is_flag=True, help='Launches scanning mode.')
@click.option('--list', '-l', is_flag=True, help='Lists all entries in the database.')
@click.option('--add', '-a', is_flag=True, help='Opens a text file to add multiple urls to the database.')
#@click.option('--add', '-a', help='Adds a single url to the database.')
#@click.option('--add-urls', is_flag=True, help='Opens a text file to add multiple urls to the database.')
@click.option('--delete', '-d', help='Deletes an entry from the database.')

def main(scan, add, list, delete):
    if scan:
        scan_urls()
    elif list:
        construct_rich_table()
    elif add:
        add_urls()
    elif delete:
        delete_entry(delete)
    else:
        with click.Context(main, info_name='ao3scraper.py') as ctx:
            click.echo(main.get_help(ctx))

    #print()
    #console = Console()
    #console.print(table)
            
    connection.close()
    exit()


def scan_urls():
    # Check if AO3 is online / accessible
    print("Checking if AO3 servers are online...")
    try:
        requests.get("https://archiveofourown.org", timeout=10)
    except Timeout:
        print("Could not connect to AO3 servers. (timed out)")
        exit()
    else:
        print("Contacted servers successfully.")

    for item in fic_table:
        print(item[1])

def construct_rich_table():
    # Refresh table entries
    cursor.execute("SELECT * FROM fics")
    fic_table = cursor.fetchall()

    for item in fic_table:

            #item_id = str(item[1])
            #item_id = item_id.split("archiveofourown.org/works/")[1] # Remove everything before and including this string
            #item_id = item_id.split("/", 1)[0] # Remove everything after and including this string

            # Check if url field is empty
            if item[0] == None:
                table.add_row(str(fic_table.index(item) + 1) + ".", "[link=" + item[1] + "]FIC NOT YET SCANNED[/link]", item[2], item[3])
            else:
                # table.add_row(str(fic_table.index(item) + 1) + ". [link=" + item[1] + "]" + item_id + "[/link]", item[0], item[2], item[3])
                table.add_row(str(fic_table.index(item) + 1) + ".", "[link=" + item[1] + "]" + item[0] + "[/link]", item[2], item[3])

    print()
    console = Console()
    console.print(table)

def add_urls():
    MARKER = "# Enter one url on each line to add it to the database. This line will not be recorded."
    message = click.edit(MARKER + '\n')
    if message is not None:
        message_lines = message.split(MARKER, 1)[1].rstrip('\n').lstrip('\n')
        url_to_parse = message_lines.split('\n')
        
        for i in url_to_parse:
            cursor.execute("INSERT INTO fics (url) VALUES ('" + str(i) + "');")
            connection.commit()
            print("Added " + url_to_parse[url_to_parse.index(i)]) # fix

    construct_rich_table()

def delete_entry(entry):
    try:
        target_entry = fic_table[(int(entry) - 1)] # black magic fuckery, consider using rowid
        cursor.execute("DELETE FROM fics WHERE url = '" + target_entry[1] + "';")
    except IndexError:
        print("Number out of index range.")
        exit()
    #cursor.execute("DELETE FROM fics WHERE rowid = " + entry + ";")
    connection.commit()
    print("Deleted entry number " + entry)

    construct_rich_table()


if __name__ == "__main__":
    # Connect to database
    connection = sqlite3.connect("fics.db")
    cursor = connection.cursor()

    # Create table
    cursor.execute("SELECT * FROM fics")
    fic_table = cursor.fetchall()

    main()

"""
# Function to fetch all online tags for one URL
def get_tags(url):
    page = requests.get(url)

    # 4xx and 5xx Error Detection
    if not page.ok:
        print(page.status_code, "Error!")
        print("URL responsible: ", i["url"])
        pass

    soup = BeautifulSoup(page.content, "html.parser")

    # Return tags in order: title, last updated, chapters
    return[soup.find_all(class_="title heading")[0].string.strip(),
           soup.find_all(class_="status")[1].string,
           soup.find_all(class_="chapters")[1].string]


# Handle each url
for i in track(urls, description="Fetching data from AO3..."):
    # Fetch all external chapter values of URLS
    web_tags = get_tags(i["url"])

    # Check if url has local tags: title, last updated, chapters
    if "title" and "updated" and "chapters" not in i:
        table.add_row(web_tags[1], "[link=" + i["url"] + "]" + web_tags[0] + "[/link]", web_tags[2])
    else:
        # Compare each local chapter value to each web chapter value
        if int(web_tags[2].split("/")[0]) > int(i["chapters"].split("/")[0]):
            table.add_row("[#ffcc33][bold]" + web_tags[1],
                          "[#ffcc33][bold][link=" + i["url"] + "]" + web_tags[0] + "[/link]",
                          "[#ffcc33][bold]" + web_tags[2])
        else:
            table.add_row(web_tags[1], "[link=" + i["url"] + "]" + web_tags[0] + "[/link]", web_tags[2])

    # Update url information
    i["title"] = web_tags[0]
    i["updated"] = str(web_tags[1])
    i["chapters"] = str(web_tags[2])

    # Write to yaml file
    with open("fics.yaml", "w") as file:
        yaml.dump(config, file)
    file.close()
"""
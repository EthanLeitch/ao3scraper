# Web scraping
import requests
from requests.exceptions import Timeout
from bs4 import BeautifulSoup

# YAML handling and validation 
import yaml
import os.path

# Formatting
from rich.console import Console
from rich.table import Table
from rich.progress import track

# Template for the yaml file this program uses to retrieve fic urls.
YAML_TEMPLATE = """
# add fics by replacing these example urls
# you can add as many as you'd like, but the program will take longer to run!
# do NOT modify updated or chapter values unless you know what you"re doing - the program will probably break

---
fics:
- url: https://archiveofourown.org/works/FIC_ID
- url: https://archiveofourown.org/works/FIC_ID
"""

# Create rich table
table = Table(title="Fanfics")

table.add_column("Last updated", justify="left", style="cyan", no_wrap=True)
table.add_column("Title", style="magenta")
table.add_column("Chapter", justify="left", style="green")

# Check if yaml file exists
if not os.path.exists("fics.yaml"):
    print("Creating new config file...")

    # Create yaml file if yaml file does not exist
    yaml_file = open("fics.yaml", "w")
    yaml_file.write(YAML_TEMPLATE)
    yaml_file.close()

    print("Config file created.")
    print("Add your fanfic URLs to fics.yaml to use this program.")
    exit()
else:
    print("Found config file.")

# Fetch all local chapter values of URLS
with open("fics.yaml", "r") as file:
    config = yaml.safe_load(file)
try:
    urls = config["fics"]
except TypeError:
    print("Error loading config file.")
    exit()
file.close()

# Check if AO3 is online / accessible
print("Checking if AO3 servers are online...")
try:
    requests.get("https://archiveofourown.org", timeout=10)
except Timeout:
    print("Could not connect to AO3 servers. (timed out)")
    exit()
else:
    print("Contacted servers successfully.")


# Function to fetch all online tags for one URL
def get_tags(url):
    page = requests.get(url)

    # 4xx and 5xx Error Detection
    if not page.ok:
        print(page.status_code, "Error!")
        print("URL responsible: ", i["url"])
        pass

    soup = BeautifulSoup(page.content, "html.parser")

    """
    Extract title of page
    page_title = soup.title.text
    print("Fetched: ", page_title.strip())
    """

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
        table.add_row(web_tags[1], web_tags[0], web_tags[2])
    else:
        # Compare each local chapter value to each web chapter value
        if int(web_tags[2].split("/")[0]) > int(i["chapters"].split("/")[0]):
            table.add_row("[#ffcc33][bold]" + web_tags[1],
                          "[#ffcc33][bold][link=" + i["url"] + "]" + web_tags[0] + "[/link]",
                          "[#ffcc33][bold]" + web_tags[2])
        else:
            table.add_row(web_tags[1], web_tags[0], web_tags[2])

    # Update url information
    i["title"] = web_tags[0]
    i["updated"] = str(web_tags[1])
    i["chapters"] = str(web_tags[2])

    # Write to yaml file
    with open("fics.yaml", "w") as file:
        yaml.dump(config, file)
    file.close()

print()
console = Console()
console.print(table)

import requests
from bs4 import BeautifulSoup
import re

# pattern = re.compile('\/tag\/([^?]+)\?source')
second_tag_pattern = re.compile('\"\_\_ref\"\:\"Tag\:([^"]+)')

# Make a GET request to the URL
url = "https://medium.com/verve-up/the-bewildering-and-sexist-history-of-womens-pockets-1edf3a98117"
response = requests.get(url)

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")
print(str(soup))
print(second_tag_pattern.findall(str(soup)))
# Find the tags of interest by inspecting the HTML source code
#tags = soup.find_all("div", {"class": "on di er oo op oq bd b be z bi or"})
tags = soup.find_all("div")

# Extract the text of each tag and store it in a list
tag_list = [tag.text for tag in tags]

# Print the list of tags
#print(tag_list)

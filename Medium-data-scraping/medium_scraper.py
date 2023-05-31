import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import datetime
from datetime import timedelta
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")
import re

tag_pattern = re.compile('\/tag\/([^?]+)\?source')
second_tag_pattern = re.compile('\"\_\_ref\"\:\"Tag\:([^"]+)')


# Will implement this to work with a given keyword / tag
# and amount of articles to be retrieved 

def init_db(conn, cur, clean_db = False):
    # Use this only if you want to empty the entire schema, which
    # at this case is only 1 table basically. Not sure if the commit is needed in here
    # but just in case it might be a problem it is done.
    if clean_db:
        cur.execute("""DROP TABLE IF EXISTS articles""")
        cur.execute("""DROP TABLE IF EXISTS medium_authors""")
        conn.commit()

    #Table to store the users and their information only, 
    #the relationship will be through the user_id.
    #Ultimately it is possible for a large amount of articles,
    #to have 1 user linked to a couple of articles
    cur.execute("""CREATE TABLE IF NOT EXISTS medium_authors (
        author_id INTEGER PRIMARY KEY AUTOINCREMENT,
        author TEXT,
        author_url TEXT,
        UNIQUE(author_id, author)
    )""")

    conn.commit()

    #Main table to store the articles information
    #For now there really isn't any benefit to create additoinal
    #table for the articles, as there is no one-to-many or many-to-many
    #relationship in here, so no need to include additional complexity
    #for querying afterwards
    cur.execute("""CREATE TABLE IF NOT EXISTS articles (
        article_id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_name TEXT,
        author_link TEXT,
        article_title TEXT,
        article_subtitle TEXT,
        article_url TEXT,
        article_claps INTEGER,
        read_time INTEGER,
        responses INTEGER,
        date_created TEXT,
        sections_num INTEGER,
        section_titles TEXT,
        paragraphs_num INTEGER,
        paragraphs TEXT,
        tag TEXT,
        UNIQUE(article_id, article_title)               
    )""")

    conn.commit()

    cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS pk_article_id ON articles (article_id ASC)""")
    cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS pk_author_id ON medium_authors (author_id ASC)""")
    conn.commit()

def convert_num(str_num):
    """
    A function to put a "0" prefix if the returning day/month is single digit
    This is needed as the URL does not work with a single digit months/days
    """
    if len(str_num) < 2:
        str_num = '0' + str_num
    return str_num

def get_article_content(url, tag_pattern=tag_pattern,second_tag_pattern = second_tag_pattern):
    """
    Function to extract article content specific information with a given URL
    Returning 4 objects in total
    section_titles_num - section titles total number from the article 
    section_titles - actual section titles 
    paragraphs_num - paragraphs number 
    paragraphs - paragraphs - actual article content
    """
    article_page = requests.get(url, verify=False)
    article_page_soup = BeautifulSoup(article_page.text, 'html.parser')

    tags = tag_pattern.findall(str(article_page_soup))
    tags = set(tags + second_tag_pattern.findall((str(article_page_soup))))


    sections = article_page_soup.find_all('section')

    section_titles = []
    paragraphs = []

    for section in sections:
        all_paragraphs = section.find_all('p')
        for p in all_paragraphs:
            paragraphs.append(p.text)
        
        titles = section.find_all('h1')
        for title in titles:
            section_titles.append(title.text)
        
    paragraphs_num = len(paragraphs)
    section_titles_num = len(section_titles)

    return section_titles_num, section_titles, paragraphs_num, paragraphs, tags

def substract_day(str_date):
    """
    Script to substract 1 day and return the current date, YYYY, MM, DD as strings.
    """
    yyyy = int(str_date[0:4])
    mm = str_date[5:7]
    if mm[0] == "0": 
        mm = mm[1]
    dd = str_date[8:]
    if dd[0] == "0":
        dd = dd[1]
    mm = int(mm)
    dd = int(dd)

    date = datetime.date(yyyy, mm, dd)

    date_substracted = date - timedelta(days=1)

    #This should always use 2 digits for the month and day, so no need to transform
    date_substracted = date_substracted.strftime("%Y-%m-%d")

    yyyy = date_substracted[0:4]
    mm = date_substracted[5:7]
    dd = date_substracted[8:]

    return yyyy, mm, dd

def scrape(conn, cur, year, month, day, keyword, amount):
    #init
    cnt = 0
    current_date = f'{year}-{month}-{day}'
    number_of_vast_days = 0

    articles_list = []

    #A while loop will work for us to take that much articles info
    # to match the specified amount in the beginning
    # URL is being build in this loop and the dates taking T-1 is at the end of it.
    while True:

        url = f'https://medium.com/tag/{keyword}/archive/{year}/{month}/{day}'
        
        response = requests.get(url, verify=False)
        page = response.text
        soup = BeautifulSoup(page, 'html.parser')

        articles = soup.find_all("div", class_="postArticle postArticle--short js-postArticle js-trackPostPresentation js-trackPostScrolls")
        if len(articles) == 0:
            number_of_vast_days += 1
        if number_of_vast_days > 30:
            break
        for article in tqdm(articles, desc=f'{year}-{month}-{day}'):

            #Extracting all the needed information from the current article
            article_title = article.find("h3", class_="graf--title")
            if article_title:
                article_title = article_title.text

            article_url = article.find_all("a")[3]['href'].split('?')[0]
            article_subtitle = article.find("h4", class_="graf--subtitle")
            if article_subtitle:
                article_subtitle = article_subtitle.text
            else:
                article_subtitle = ""
            
            author_url = article.find('div', class_='postMetaInline u-floatLeft u-sm-maxWidthFullWidth')
            author_url = author_url.find('a')['href']
            author = author_url.split("@")[-1]

            #We store our unique autors in a set
            # unique_authors.add(author)

            claps = article.find('button', class_='button button--chromeless u-baseColor--buttonNormal js-multirecommendCountButton u-disablePointerEvents')
            if claps:
                #We make sure that we take the int and not something like 3.7K
                claps = int("".join([x for x in claps.text if x.isdigit()]))
            else:
                claps = 0
            
            try:
                read_time = article.find("span", class_="readingTime")['title']
                read_time = int(read_time.split()[0])
            except:
                read_time = -1
            
            responses = article.find('a', class_='button button--chromeless u-baseColor--buttonNormal')
            if responses:
                responses = int(responses.text.split()[0])
            else:
                responses = 0

            titles_num, titles, paragraphs_num, paragraphs,tags = get_article_content(article_url)
            titles = ", ".join(titles)
            paragraphs = ", ".join(paragraphs)
            tags = ', '.join(tags)

            #First insert the current author in the authors table

            #Get the current author unique ID from the DB
            # conn_cursor.execute("SELECT author_id FROM medium_authors WHERE author = ?", (author,))
            # author_id = int(conn_cursor.fetchone()[0])


            # This worth to be used only if the logic is being extended
            # As of now there isn't really any value added if we init this object, 
            # also the object itself is having quite simple build and nothing to
            # give us any serious benefits.
            # If the logic is being enhanced and maybe some properties to be applied
            # this can definetely take in place

            # current_article = Article(author, 
            #                         author_url, 
            #                         article_title, 
            #                         article_subtitle, 
            #                         article_url, 
            #                         claps, 
            #                         read_time, 
            #                         responses, 
            #                         current_date, 
            #                         titles_num, 
            #                         titles, 
            #                         paragraphs_num, 
            #                         paragraphs)


            articles_list.append(
                (author,
                 author_url,
                 article_title,
                 article_subtitle,
                 article_url,
                 claps,
                 read_time,
                 responses,
                 current_date,
                 titles_num,
                 titles,
                 paragraphs_num,
                 paragraphs,
                 tags)
            )
            cnt += 1
            # print('added one')
            # print(cnt)

            if cnt == amount:
                break
        
        if cnt == amount:
            break
        #Substract 1 day from the date and continue to scrape data
        # until the amount is reached.
        year, month, day = substract_day(current_date)
        current_date = f'{year}-{month}-{day}'

    sql_articles = """
                INSERT OR IGNORE INTO articles (
                    author_name,
                    author_link,
                    article_title,
                    article_subtitle,
                    article_url,
                    article_claps,
                    read_time,
                    responses,
                    date_created,
                    sections_num,
                    section_titles,
                    paragraphs_num,
                    paragraphs,
                    tag         
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )"""

    cur.executemany(sql_articles, articles_list)
    num_inserted = cur.rowcount
    print(cur.rowcount, "records inserted!")
    conn.commit()
    #Once everything is ready we better close the db connection
    # and thats all folks.

    return num_inserted, current_date

if __name__ == "__main__":
    #connection and cursor
    conn = sqlite3.connect("medium_articles.db")
    cur = conn.cursor()

    #clean db
    init_db(conn, cur, clean_db=True)

    # set current date
    year = str(time.localtime()[0])
    month = convert_num(str(time.localtime()[1]))
    day = convert_num(str(time.localtime()[2] - 1))

    with open('tags.txt', encoding='utf-8') as f:
        tags = f.read().splitlines()
    tags = {tag: {'year': year, 'month': month, 'day': day, 'num': 0}
            for tag in tags if tag}
    tag_list = list(tags.keys())

    for i in range(20):
        for tag in tags:
            print(tag.lower())
            num_inserted, current_date = scrape(conn,
                                                cur,
                                                tags[tag]['year'],
                                                tags[tag]['month'],
                                                tags[tag]['day'],
                                                tag,
                                                10)
            new_year, new_month, new_day = substract_day(current_date)
            tags[tag]['year'] = new_year
            tags[tag]['month'] = new_month
            tags[tag]['day'] = new_day
            tags[tag]['num'] += num_inserted

    conn.close()

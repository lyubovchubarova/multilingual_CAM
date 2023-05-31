import sqlite3

conn = sqlite3.connect('medium_articles.db')

c = conn.cursor()
c.execute("SELECT * FROM medium_authors")

print("Distinct Authors")
for row in  c.fetchall():
    print(row)

c.execute("SELECT article_id, author_id, article_title, article_subtitle, article_url, article_claps, read_time, responses, date_created FROM articles")

print("Articles")
for row in c.fetchall():
    print(row)

conn.close()



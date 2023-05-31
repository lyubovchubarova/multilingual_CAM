import sqlite3
import spacy

nlp = spacy.load("fr_core_news_sm")

conn = sqlite3.connect("medium_articles.db")
cur = conn.cursor()

# cur.execute("""
#     SELECT tag from articles
# """)

# all_tags = cur.fetchall()

# unique_tags = set()

# for tags in all_tags:
#     for tag_group in tags:
#         tag_group = tag_group.split(', ')
#         for tag in tag_group:
#             unique_tags.add(tag)


# with open('unique_tags_fr.txt', 'w', encoding='utf-8') as f:
#     for tag in sorted(list(unique_tags)):
#         f.write(tag+'\n')


cur.execute("""
    SELECT paragraphs from articles
""")

all_paragraphs = cur.fetchall()

cur.execute("""
    SELECT section_titles from articles
""")

section_titles = cur.fetchall()

sentences = []

from tqdm import tqdm

for par_groups in tqdm(all_paragraphs):
    sentences_groups = par_groups[0]
    doc = nlp(sentences_groups)
    for sent in doc.sents:
        sentences.append(sent.text)

for par_groups in tqdm(section_titles):
    sentences_groups = par_groups[0]
    doc = nlp(sentences_groups)
    for sent in doc.sents:
        sentences.append(sent.text)

with open('fr_sentences.txt', 'w', encoding='utf-8') as f:
    for elem in sentences:
        f.write(elem+'\n')
# unique_tags = set()

# for tags in all_tags:
#     for tag_group in tags:
#         tag_group = tag_group.split(', ')
#         for tag in tag_group:
#             unique_tags.add(tag)


# with open('unique_tags_fr.txt', 'w', encoding='utf-8') as f:
#     for tag in sorted(list(unique_tags)):
#         f.write(tag+'\n')
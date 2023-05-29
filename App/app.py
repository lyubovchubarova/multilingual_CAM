from flask import Flask
from flask import render_template, request
from search.utils_and_types import (INDEX_NAME_EN, INDEX_NAME_FR, INDEX_NAME_RU, prepare_sentences_to_present, 
                                    count_scores_for_answer_presentation, count_collection_similarity, translate_word,
                                    receive_better_and_worse_sentences, link_construction)
from transformers import BertForSequenceClassification, BertTokenizer
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch
from PyMultiDictionary import MultiDictionary

dictionary = MultiDictionary()

from search.es_actions import create_index, index_text

tokenizer = BertTokenizer.from_pretrained("bert-base-multilingual-cased")
model = BertForSequenceClassification.from_pretrained("App\search\mbert-pretrained")

embeddings_getter = SentenceTransformer('distiluse-base-multilingual-cased-v1')


es_client = Elasticsearch(hosts=["http://127.0.0.1:9200"])

create_index(index=INDEX_NAME_EN, es_client=es_client)
create_index(index=INDEX_NAME_FR, es_client=es_client)
create_index(index=INDEX_NAME_RU, es_client=es_client)

with open(r'App\data\en.txt', 'r', encoding='utf-8') as f:
    eng_data = f.read().splitlines()

with open(r'App\data\fr.txt', 'r', encoding='utf-8') as f:
    fr_data = f.read().splitlines()

with open(r'App\data\ru.txt', 'r', encoding='utf-8') as f:
    ru_data = f.read().splitlines()

index_text(texts=eng_data, index=INDEX_NAME_EN, es_client=es_client)
index_text(texts=fr_data, index=INDEX_NAME_FR, es_client=es_client)
index_text(texts=ru_data, index=INDEX_NAME_RU, es_client=es_client)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('query_form.html')

@app.route('/comparison', methods = ['GET'])
def results():

    obj1 = request.args.get('obj1')
    obj2 = request.args.get('obj2')
    target_language = request.args.get('language')

    better_sentences, worse_sentences = receive_better_and_worse_sentences(obj1=obj1,
                                                                           obj2=obj2,
                                                                           language=target_language,
                                                                           es_client=es_client)
    
    obj1_percent, obj2_percent = count_scores_for_answer_presentation(better_sentences, worse_sentences)

    #count_for_other_languages
    

    languages_utils_dict = {}

    languages = ['en', 'ru', 'fr']
    languages.remove(target_language)
    for language in languages:
        languages_utils_dict[language] = {}
        languages_utils_dict[language]['obj1'] = translate_word(obj1,
                                                      target_language,
                                                        language).lower()
        languages_utils_dict[language]['obj2'] = translate_word(obj2,
                                                      target_language,
                                                        language).lower()
        
        languages_utils_dict[language]['link'] = link_construction(languages_utils_dict[language]['obj1'],
                                                                   languages_utils_dict[language]['obj2'],
                                                                   language)

        print(languages_utils_dict[language])
        
        languages_utils_dict[language]['fullname'] = 'English' if language == 'en'\
                                                        else 'French' if language == 'fr'\
                                                            else 'Russian'

        better_sentences_cur, worse_sentences_cur = receive_better_and_worse_sentences(obj1=languages_utils_dict[language]['obj1'],
                                                                           obj2=languages_utils_dict[language]['obj2'],
                                                                           language=language,
                                                                           es_client=es_client)
        
        score_cosine_better = count_collection_similarity(sentences1=better_sentences,
                                                          sentences2=better_sentences_cur,
                                                          model=embeddings_getter)
        score_cosine_worse = count_collection_similarity(sentences1=worse_sentences,
                                                          sentences2=worse_sentences_cur,
                                                          model=embeddings_getter)
        
        languages_utils_dict[language]['score'] = (score_cosine_better + score_cosine_worse) / 2
    print(languages_utils_dict)

    return render_template('query_form_with_results.html',
                           obj1=obj1,
                           obj1_percent=obj1_percent,
                           better_sentences=prepare_sentences_to_present(better_sentences, obj1, obj2),
                           obj2=obj2,
                           obj2_percent=obj2_percent,
                           worse_sentences = prepare_sentences_to_present(worse_sentences, obj1, obj2),
                           languages_utils_dict=[languages_utils_dict[language]
                                                 for language in languages_utils_dict
                                                 if languages_utils_dict[language]["score"] < 0.95])

if __name__ == '__main__':
    import os
    app.run(debug=True, port = int(os.environ.get("PORT", 5000)))


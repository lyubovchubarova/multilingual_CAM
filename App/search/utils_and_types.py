from dataclasses import dataclass, field
import numpy as np
from markupsafe import Markup
from sentence_transformers import util
from transformers import BertForSequenceClassification, BertTokenizer
from .es_actions import query_question

import translators as ts

import nltk
nltk.download('punkt')
from nltk.stem.snowball import SnowballStemmer

snowball_en = SnowballStemmer("english")
snowball_fr = SnowballStemmer("french")
snowball_ru = SnowballStemmer("russian")


INDEX_NAME_EN = "english_sentences"
INDEX_NAME_FR = "french_sentences"
INDEX_NAME_RU = "russian_sentences"
language_index_dict = {'en': INDEX_NAME_EN,
                        'fr': INDEX_NAME_FR,
                        'ru': INDEX_NAME_RU}

tokenizer = BertTokenizer.from_pretrained("bert-base-multilingual-cased")
model = BertForSequenceClassification.from_pretrained("App\search\mbert-pretrained")

def get_stem(object_to_stem, language):
    # First Word tokenization
    nltk_tokens = nltk.word_tokenize(object_to_stem)
    # #Next find the roots of the word
    object_wildcard = []
    for w in nltk_tokens:
        if language=='en':
            stem = snowball_en.stem(w)
        elif language=='fr':
            stem = snowball_fr.stem(w)
        elif language == 'ru':
            stem = snowball_ru.stem(w)
        object_wildcard.append(stem+"*")
    return " ".join(object_wildcard)

def construct_search_query(obj1: str, obj2: str, language: str):
    first_order = get_stem(obj1, language) + ' ' + get_stem(obj2, language)
    second_order = get_stem(obj2, language) + ' ' + get_stem(obj1, language)
    final_query = f'({first_order} OR {second_order})'
    return final_query

# def construct_link_and_text_to_display(languages_utils_dict):
#     new_dict = {language: languages_utils_dict[language]
#                 for language in languages_utils_dict
#                 if languages_utils_dict[language]["score"] < 0.95}
#     if new_dict:
#         link = ''
#         for language in new_dict:
#             link += f'<a href="/{}" class="alert-link">{{ language.fullname  }}</a>'
#             pass
#     else:
#         return ' '

def count_scores_for_answer_presentation(better_sentences: list, worse_sentences: list):
    better_count = sum(sentence.final_score for sentence in better_sentences)
    worse_count = sum(sentence.final_score for sentence in worse_sentences)

    score_obj1 = round(better_count / (better_count+worse_count), 1) * 100
    score_obj2 = 100 - score_obj1

    return score_obj1, score_obj2

def count_collection_similarity(sentences1: list,
                                sentences2: list,
                                model):
    embeddings1 = sum(model.encode([sentence.text for sentence in sentences1], convert_to_tensor=True))/len(sentences1)
    embeddings2 = sum(model.encode([sentence.text for sentence in sentences2], convert_to_tensor=True))/len(sentences2)
    cosine_scores = util.cos_sim(embeddings1, embeddings2)

    return cosine_scores.detach().numpy()[0][0]


def prepare_sentences_to_present(sentences: list, obj1: str, obj2: str):
    prepared_sentences = []

    for sentence in sentences:
        prepared_sentence = sentence.text\
                            .replace(obj1.title(), f'<span class="first-obj">{obj1.title()}</span>')\
                            .replace(obj1.lower(), f'<span class="first-obj">{obj1.lower()}</span>')\
                            .replace(obj1.upper(), f'<span class="first-obj">{obj1.upper()}</span>')\
                            .replace(obj2.title(), f'<span class="second-obj">{obj2.title()}</span>')\
                            .replace(obj2.lower(), f'<span class="second-obj">{obj2.lower()}</span>')\
                            .replace(obj2.upper(), f'<span class="second-obj">{obj2.upper()}</span>')
        prepared_sentences.append(Markup(prepared_sentence))

    return prepared_sentences

def translate_word(word: str, from_language: str, to_language: str):
    return ts.translate_text(word, from_language=from_language, to_language=to_language)

def link_construction(obj1: str, obj2: str, language: str):
    return f"comparison?obj1={obj1}&obj2={obj2}&language={language}"

@dataclass   
class Sentence():
    text: str
    obj1: str
    obj2: str
    es_score: float
    es_max_score: float
    label: str = field(init=False, repr=False)
    classifier_score: float = field(init=False, repr=False)
    final_score: float = field(init=False, repr=False)

    @staticmethod
    def classify(obj1: str, obj2: str, sent : str, tokenizer=tokenizer, model=model):
        tokens = tokenizer(obj1 + ' [SEP] ' + obj2 + ' [SEP] ' + sent, truncation=True, padding=True, return_tensors='pt')
        logits = model(**tokens).logits
        logits = logits.cpu().detach().numpy()
        preds = np.argmax(logits)
        return preds, logits[0][preds]
    
    @staticmethod
    def get_final_score(classifier_score: float, 
              es_score: float,
              es_max_score: float,
              gamma: float = 0.8,
              delta: float = 0.1) -> float:
        if classifier_score >= gamma:
            return es_score + es_max_score
        else:
            return es_score * delta

    def __post_init__(self):
        labels_dict = {0: "WORSE", 1: "BETTER", 2: "NONE"}
        self.label, self.classifier_score = self.classify(obj1=self.obj1,
                                                           obj2=self.obj2,
                                                           sent=self.text)
        self.label = labels_dict[self.label]

        self.final_score = self.get_final_score(classifier_score=self.classifier_score,
                                                es_score=self.es_score,
                                                es_max_score = self.es_max_score)
        

def receive_better_and_worse_sentences(obj1: str, obj2: str, language: str, es_client):
    """Function that takes two objects, search for 
    relevant sentences in corpus and returns two lists:
    in which first object is BETTER that second one and otherwise."""

    hits = query_question(text=construct_search_query(obj1, obj2, language), 
                          index=language_index_dict[language],
                          es_client=es_client,
                          )
    
    max_sent_score = max(hit["_score"] for hit in hits)

    sentences = [Sentence(text=hit["_source"]["sentence"],
                          obj1=obj1,
                          obj2=obj2,
                          es_score=hit["_score"],
                          es_max_score=max_sent_score)
                for hit in hits]
    
    better_sentences = []
    worse_sentences = []

    for sentence in sentences:
        if sentence.label == "BETTER":
            if sentence.text.lower().find(obj1.lower()) < sentence.text.lower().find(obj2.lower()):
                better_sentences.append(sentence)
            elif sentence.text.lower().find(obj1.lower()) > sentence.text.lower().find(obj2.lower()):
                worse_sentences.append(sentence)
        elif sentence.label == "WORSE":
            if sentence.text.lower().find(obj1.lower()) < sentence.text.lower().find(obj2.lower()):
                worse_sentences.append(sentence)
            elif sentence.text.lower().find(obj1.lower()) > sentence.text.lower().find(obj2.lower()):
                better_sentences.append(sentence)


    better_sentences = sorted(better_sentences, key= lambda x: x.final_score, reverse=True)
    worse_sentences = sorted(worse_sentences, key= lambda x: x.final_score, reverse=True)

    return better_sentences, worse_sentences
from tqdm import tqdm

def create_index(es_client, index) -> None:

    es_client.indices.delete(index=index, ignore=404)
    
    if index == "french_sentences":
        es_client.indices.create(

            index=index,

            ignore=400,

            body={
                "settings": {
                "analysis": {
                "filter": {
                    "galician_stop": {
                    "type":       "stop",
                    "stopwords":  "_galician_" 
                    },
                    "galician_keywords": {
                    "type":       "keyword_marker",
                    "keywords":   ["exemplo"] 
                    },
                    "galician_stemmer": {
                    "type":       "stemmer",
                    "language":   "galician"
                    }
                },
                "analyzer": {
                    "rebuilt_galician": {
                    "tokenizer":  "standard",
                    "filter": [
                        "lowercase",
                        "galician_stop",
                        "galician_keywords",
                        "galician_stemmer"
                    ]
                    }
                }
                }
            },
                "mappings": {
                    
                    "properties": {
                        "sentence": {
                            "type": "text",
                            "analyzer": "rebuilt_galician",
                            "search_analyzer": "rebuilt_galician"
                        }

                    }

                }
            }

        )
    elif index == "russian_sentences":
        es_client.indices.create(

            index=index,

            ignore=400,

            body={
                "settings": {
                "analysis": {
                "filter": {
                    "russian_stop": {
                    "type":       "stop",
                    "stopwords":  "_russian_" 
                    },
                    "russian_keywords": {
                    "type":       "keyword_marker",
                    "keywords":   ["пример"] 
                    },
                    "russian_stemmer": {
                    "type":       "stemmer",
                    "language":   "russian"
                    }
                },
                "analyzer": {
                    "rebuilt_russian": {
                    "tokenizer":  "standard",
                    "filter": [
                        "lowercase",
                        "russian_stop",
                        "russian_keywords",
                        "russian_stemmer"
                    ]
                    }
                }
                }
            },
                "mappings": {
                    
                    "properties": {
                        "sentence": {
                            "type": "text",
                            "analyzer": "rebuilt_russian",
                            "search_analyzer": "rebuilt_russian"
                        }

                    }

                }
            }

        )
    
    elif index == "english_sentences":

        es_client.indices.create(

            index=index,

            ignore=400,

            body={
                "settings": {
                "analysis": {
                "filter": {
                    "english_stop": {
                    "type":       "stop",
                    "stopwords":  "_english_" 
                    },
                    "english_keywords": {
                    "type":       "keyword_marker",
                    "keywords":   ["example"] 
                    },
                    "english_stemmer": {
                    "type":       "stemmer",
                    "language":   "english"
                    },
                    "english_possessive_stemmer": {
                    "type":       "stemmer",
                    "language":   "possessive_english"
                    }
                },
                "analyzer": {
                    "rebuilt_english": {
                    "tokenizer":  "standard",
                    "filter": [
                        "english_possessive_stemmer",
                        "lowercase",
                        "english_stop",
                        "english_keywords",
                        "english_stemmer"
                    ]
                    }
                }
                }
            },
                "mappings": {
                    
                    "properties": {
                        "sentence": {
                            "type": "text",
                            "analyzer": "rebuilt_english",
                            "search_analyzer": "rebuilt_english"
                        }

                    }

                }
            }

        )


def index_text(texts, index, es_client) -> None:
    for text in tqdm(texts, desc=index):

        sentence = text
        data = {

                "sentence": sentence

            }

        res = es_client.index(
                index=index,
                body=data
            )
        
def query_question(text, index, es_client):
    es_result = es_client.search(
        index=index,
        body={
            "from": 0,
            "query": {
              "query_string": {
                "query":text,
                "fields": ["sentence"],
                "analyze_wildcard": True,
              },
              
            },
            
        }
    )
    
    hits = es_result["hits"]["hits"]

    return hits
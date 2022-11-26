from nltk.tokenize.punkt import PunktSentenceTokenizer
import pandas as pd
from textblob import TextBlob
import glob    
import numpy as np
import json

def word_sentiment_extract(sentence, word):
    if word in sentence.lower():
        blob = TextBlob(sentence)
        sentiment = blob.sentiment.polarity
    else:
        sentiment = 0

    return sentiment

def extract_sentiment(file_path, words):
    sentiment_df = pd.DataFrame(columns=['Word', 'Sentence', 'Polarity'])
    tokenizer = PunktSentenceTokenizer()

    with open(file_path, "r") as f:
        sections = json.loads(f.read())

    for section_name in sections:
        if sections[section_name] is None:
            continue

        sentences = tokenizer.tokenize(str(sections[section_name]))

        for word in words:
            for sentence in sentences:
                polar = word_sentiment_extract(sentence, word)
                if polar != 0:
                    sentiment_df.loc[len(sentiment_df.index)] = [word, sentence, polar]

    return sentiment_df
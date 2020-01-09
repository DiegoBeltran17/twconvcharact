import logging
import pandas as pd
from nltk.tokenize import TweetTokenizer


def conversation_filter(ds, only_roots=False):
    logging.info('extract conversations with 2 or more tweets')
    conv = ds[(ds.num_replies>1)]
    logging.info(f'num conversatins with 2 or more tweets: {conv.shape[0]}')
    gconv = conv.groupby('conversation_id').agg({'screen_name': 'nunique', 'id': 'count'})
    gconv = gconv.reset_index()
    gconv.rename(columns={'screen_name': 'num_users', 'id': 'num_tweets'}, inplace=True)
    conv = conv.merge(gconv, on='conversation_id')
    conv=conv[(conv.num_users>1)]
    logging.info(f'num conversatins with 2 or more users: {conv.shape[0]}')

    if only_roots==True:
        conv = conv[(conv.in_reply_to_status_id.isnull())]
    return conv


tknzr = TweetTokenizer()

def extract_status_feats(tweet):
    tokens= tknzr.tokenize(tweet)
    num_urls=0
    num_hashtags=0
    num_mentions=0
    for t in tokens:
        if t.startswith('http'):
            num_urls+=1
        if t.startswith('#'):
            num_hashtags+=1
        if t.startswith('@'):
            num_mentions+=1
    num_tokens = len(tokens) - (num_urls+num_hashtags+num_mentions)
    return num_urls, num_hashtags, num_mentions, num_tokens
    
def extract_feats(row):
    num_urls,num_hashtags,num_mentions,num_tokens = extract_status_feats(row['text'])
    row['has_media']  = 0 if pd.isnull(row['media_url']) else 1
    row['num_urls']=num_urls - row['has_media']
    row['num_hashtags']=num_hashtags
    row['num_mentions']=num_mentions
    row['num_tokens'] =num_tokens
    return row

def build_content_features(ds):  
    ds = ds.apply(lambda r: extract_feats(r), axis=1)
    return ds

def test_build_content_features():
    s='Gaby bonita https://t.co/bAnSHsEi9g @conadisecu @vinizeta'
    return extract_status_feats(s)

from nltk.stem import WordNetLemmatizer 
from nltk.stem.snowball import SnowballStemmer
import nltk
import re

en_stemmer = SnowballStemmer("english")
es_stemmer = SnowballStemmer("spanish")

def tweet_text_only(text):
    #print('tokenizing...')
    #remove mentions, hashtags, urls
    text = re.sub(r"(?:\@|#|https?\://)\S+", "", text)
    text = re.sub("(\d+).?(\d*)\s*(km|mi|k)","xdist",text)
    text = re.sub("(\d+)\s*(h):(\d+)\s*(m):?(\d*)\s*(s)","xtime",text)
    text = re.sub("(\d+)\s*(h|m):?(\d*)\s*(s)","xtime",text)
    text = re.sub("[^a-zA-Z ]","",text)
    text = re.sub(r'\b\w{1,2}\b',' ',text)
    #tokens = nltk.word_tokenize(text)
    tokens= tknzr.tokenize(text)
    #tokens = [es_stemmer.stem(en_stemmer.stem(t)) for t in tokens]
    return tokens

def extract_tweet_text_only(row):
    tokens = tweet_text_only(row['text'])
    row['text_only']=' '.join(tokens)
    row['text_only_num_tokens'] = len(tokens)
    return row

def build_tweet_text_only(ds):  
    ds = ds.apply(lambda r: extract_tweet_text_only(r), axis=1)
    return ds

def test_tweet_text_only():
    s='Gaby bonita https://t.co/bAnSHsEi9g @conadisecu @vinizeta'
    return tweet_text_only(s)

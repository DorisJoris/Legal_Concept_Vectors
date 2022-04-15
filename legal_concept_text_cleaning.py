# -*- coding: utf-8 -*-
#%% Imports

import re 
import numpy as np
from legal_concept_resources import abbreviations

#%% Funtions 
def split_text_into_sentences(text):
    text = re.sub("[!?]",".",text)
    
    while text.find("..") > -1:
        text = text.replace("..",".")
    
    # "."-exceptions
    exceptions_list = abbreviations
    
    month_list = ["januar", "februar", "marts", "april", "maj", "juni",
             "juli", "august", "september", "oktober", "november", "december"]
    
    for i in range(0,10):
        for month in month_list:
            date = f"{i}. {month}"
            replacement = f"{i}%% {month}"
            text = text.replace(date,replacement)
    
    for exception in exceptions_list:
        text = text.replace(exception[0],exception[1])
       
    pkt_instances = []
    pkt_instances = pkt_instances + re.findall("[0-9]\. pkt", text)
    pkt_instances = pkt_instances + re.findall("[0-9]\. og [0-9]", text)
    pkt_instances = pkt_instances + re.findall("[0-9]\., [0-9]", text)
    
    number_instances = re.findall("[0-9]\. ", text)
    pkt_instances = pkt_instances + number_instances
    
    pkt_replacements = []
    for instance in pkt_instances:
        pkt_replacements.append(instance.replace('.','%%'))
    
    for i in range(0,len(pkt_replacements)):
        text = text.replace(pkt_instances[i],pkt_replacements[i])
        
    sentence_end = re.findall("%% [A-Z]", text) + re.findall("%% §", text)
    sentence_end_dot = [x.replace("%%",".") for x in sentence_end] 
    
    for i in range(0,len(sentence_end)):
        text = text.replace(sentence_end[i], sentence_end_dot[i])
    
    text = text.replace('jf.','jf%%')
    
    
    # reversing "."-exceptions after split
    sentence_list = []
    while text.find('.') > 0:
        sentence_text = text[0:text.find('.')+1]
        
        for exception in exceptions_list:
            sentence_text = sentence_text.replace(exception[1],exception[0])
        
        for i in range(0,10):
            for month in month_list:
                date = f"{i}%% {month}"
                replacement = f"{i}. {month}"
                sentence_text = sentence_text.replace(date,replacement)
        
        for i in range(0,len(pkt_replacements)):
            sentence_text = sentence_text.replace(pkt_replacements[i],pkt_instances[i])
        
        text = text[text.find('.')+1:len(text)]
        
        sentence_list.append(sentence_text)
        
    if text.find('.') < 1 and len(text)>0:
        sentence_text = text
        
        for exception in exceptions_list:
            sentence_text = sentence_text.replace(exception[1],exception[0])
        
        for i in range(0,10):
            for month in month_list:
                date = f"{i}%% {month}"
                replacement = f"{i}. {month}"
                sentence_text = sentence_text.replace(date,replacement)
                
        for i in range(0,len(pkt_replacements)):
            sentence_text = sentence_text.replace(pkt_replacements[i],pkt_instances[i])
                  
        sentence_list.append(sentence_text)
    return sentence_list

def get_sentence_bow_meanvector(sentence_raw_text, stopwords, word_embeddings):
    raw_text = sentence_raw_text.lower()
    for exception in abbreviations:
        raw_text = raw_text.replace(exception[0], '')
    
    raw_text_clean = re.sub('[^a-zæøå ]+', '', raw_text)
    
    words = []
    for word in raw_text_clean.split():
        if word not in stopwords:
            words.append(word)
    
    bow = dict()
    oov_list = list()
    word_vector_sum = np.array([0]*word_embeddings.vector_size, dtype='float32')
    word_count = 0
    for word in words:
        try:
            word_vector = word_embeddings[word]
            word_vector_sum += word_vector
            word_count += 1
            if word in bow.keys():
                bow[word] += 1
            else:
                bow[word] = 1
        except:
            word_vector = None
            oov_list.append(word)
        
    if word_count > 0:
        word_vector_mean = word_vector_sum/word_count
    else:
        word_vector_mean = None
    
    sentence_dict = {'bow':bow,
                     'bow_meanvector':word_vector_mean,
                     'oov_list':oov_list,
                     'text':sentence_raw_text}
    return sentence_dict


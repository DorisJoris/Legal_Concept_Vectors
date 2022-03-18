# -*- coding: utf-8 -*-
"""
Created on Fri Mar 18 11:05:58 2022

@author: bejob
"""

#%% Import
import pickle
from danlp.models.embeddings  import load_wv_with_gensim

from legal_concept_extractor import get_law_document_dict


#%% App
if __name__ == "__main__":
    
    #funktionærloven
    url = 'https://www.retsinformation.dk/api/document/eli/lta/2017/1002'
    #barselsloven
    url = 'https://www.retsinformation.dk/api/document/eli/lta/2021/235'
    #lov om tidsbegrænset anslttekse
    url = 'https://www.retsinformation.dk/api/document/eli/lta/2008/907'
    
    word_embeddings = load_wv_with_gensim('conll17.da.wv')
    
    with open("stopord.txt","r", encoding="UTF-8") as sw_file:
        stopwords = [line.strip() for line in sw_file]
        
    law_document_dict = get_law_document_dict(url, stopwords, word_embeddings)

    
    
    # save data    
    with open("test_law_document.p", 'wb') as pickle_file:
        pickle.dump(law_document_dict, pickle_file)
    
    

    #open data
    with open("test_paragraph_propert_list.p", "r") as pickle_file:
        opened_paragraph_property_list = pickle.load(pickle_file)     

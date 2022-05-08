# -*- coding: utf-8 -*-

#%% Import
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from danlp.models.embeddings  import load_wv_with_gensim
from gensim.models import Word2Vec
from gensim.models.callbacks import CallbackAny2Vec
from word2vec_word_embeddings import callback


import legal_concept_extractor_MAIN 
import legal_concept_database

from tabulate import tabulate
    
#%% App
if __name__ == "__main__":
    
    #word_embeddings = load_wv_with_gensim('conll17.da.wv')
    word_embeddings = Word2Vec.load("models/word2vec_100_CBOW_w5_mc2_version8.model")
    
    with open("stopord.txt","r", encoding="UTF-8") as sw_file:
        stopwords = [line.strip() for line in sw_file]
    
    
    ## LBK-documents
    #funktionærloven
    url1 = 'https://www.retsinformation.dk/api/document/eli/lta/2017/1002'
    test_database = legal_concept_database.lc_database(url1, stopwords, word_embeddings)
    
    #lov om finansiel virksomhed (Ram explosion)
    #url4 = 'https://www.retsinformation.dk/api/document/eli/lta/2022/406'
    #test_database.add_retsinfo_doc(url4)
    
    
    
#%% Add documents
if __name__ == "__main__":    
    url_list = [
         'https://www.retsinformation.dk/api/document/eli/lta/2021/235', #barselsloven
         'https://www.retsinformation.dk/api/document/eli/lta/2008/907', #lov om tidsbegrænset ansaettelse
         'https://www.retsinformation.dk/api/document/eli/lta/2022/336', #lov om investeringsforeninger m.v.
         'https://www.retsinformation.dk/api/document/eli/lta/2016/193', #Bekendtgørelse af lov om aftaler og andre retshandler på formuerettens område
         'https://www.retsinformation.dk/api/document/eli/lta/2013/1457', #Lov om forbrugeraftaler
        'https://www.retsinformation.dk/api/document/eli/lta/2021/1284',#Bekendtgørelse af lov om indkomstskat for personer m.v.
        'https://www.retsinformation.dk/api/document/eli/lta/2021/25' #Bekendtgørelse af lov om godkendte revisorer og revisionsvirksomheder (revisorloven)1)
        ]
    
    for url in url_list:
        test_database.add_retsinfo_doc(url)
  
#test_database.add_retsinfo_doc('https://www.retsinformation.dk/api/document/eli/lta/2021/25')
#%%
if __name__ == "__main__":
    
    test_database.concept_bow_vector_init()
    
    #print(len(test_database.external_ref))
    #print(test_database.concept_count())
    test_database.connect_ext_ref()  
    
    test_database.calculate_concept_vector(aver_dist_threshold = 0.1)
    test_database.calculate_concept_bow()
    
    test_database.get_vector_dfs()
    
    # cbowm_df = test_database.concept_bow_meanvector_df
    # cv_df = test_database.concept_vector_df
    # bm_df = test_database.bow_meanvector_df
    
    example_lc = test_database.random_lc()
    example_lc = test_database.legal_concepts['LBK nr 336 af 11/03/2022']
    
    with open("databases/test_database.p", "wb") as pickle_file:
        pickle.dump(test_database, pickle_file) 




    


    


    
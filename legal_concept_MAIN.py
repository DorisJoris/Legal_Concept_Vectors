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
        'https://www.retsinformation.dk/api/document/eli/lta/2021/25', #Bekendtgørelse af lov om godkendte revisorer og revisionsvirksomheder (revisorloven)1)
        'https://www.retsinformation.dk/api/document/eli/lta/2010/240', #Ansættelsesbevisloven
        'https://www.retsinformation.dk/api/document/eli/lta/2021/242', #Afskrivningsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2018/1070', #Erstatningsansvarsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2022/956', #Erhvervsuddannelsesloven
        'https://www.retsinformation.dk/api/document/eli/lta/2021/824', #Kildeskatteloven
        'https://www.retsinformation.dk/api/document/eli/lta/2011/645', #Ligebehandlingsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2019/156', #Ligelønsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2022/866', #Markedsføringsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2021/1853', #Købeloven
        'https://www.retsinformation.dk/api/document/eli/lta/2014/332', #Kommissionsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2015/1123', #lov om forbrugerbeskyttelse ved erhvervelse af fast ejendom m.v.
        'https://www.retsinformation.dk/api/document/eli/lta/2021/510', #lov om formidling af fast ejendom m.v.
        'https://www.retsinformation.dk/api/document/eli/lta/2022/866', #Markedsføringsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2014/459', #Renteloven
        'https://www.retsinformation.dk/api/document/eli/lta/2021/242', #Afskrivningsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2015/47', #Boafgiftsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2019/132', #Ejendomsavancebeskatningsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2019/984', #Erhvervsfondsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2014/1175', #Etableringskontoloven
        'https://www.retsinformation.dk/api/document/eli/lta/2020/1590', #Ejendomsværdiskatteloven
        'https://www.retsinformation.dk/api/document/eli/lta/2020/2020', #Fondsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2021/743', #Fusionsskatteloven
        'https://www.retsinformation.dk/api/document/eli/lta/2014/433', #Forvaltningsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2015/48', #Opkrævnings- og inddrivelsesloven
        'https://www.retsinformation.dk/api/document/eli/lta/2019/353', #Konkursskatteloven
        'https://www.retsinformation.dk/api/document/eli/lta/2021/1735', #Ligningsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2013/349', #Ombudsmandsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2019/1121', #Retssikkerhedsloven
        'https://www.retsinformation.dk/api/document/eli/lta/2019/774', #Ægtefælleloven
        'https://www.retsinformation.dk/api/document/eli/lta/2021/251', #Selskabsskatteloven
        
        
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
    example_lc = test_database.legal_concepts['Stk. 4._§ 10._LBK nr 1284 af 14/06/2021']
    
    with open("databases/w2v_database.p", "wb") as pickle_file:
        pickle.dump(test_database, pickle_file) 




    


    


    
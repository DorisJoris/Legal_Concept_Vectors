# -*- coding: utf-8 -*-

#%% Import
import pickle
import numpy as np

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
    word_embeddings = Word2Vec.load("models/word2vec_300_CBOW_w5_mc2_version6.model")
    
    with open("stopord.txt","r", encoding="UTF-8") as sw_file:
        stopwords = [line.strip() for line in sw_file]
    
    
    ## LBK-documents
    #funktionærloven
    url1 = 'https://www.retsinformation.dk/api/document/eli/lta/2017/1002'
    test_database = legal_concept_database.lc_database(url1, stopwords, word_embeddings)
    
    #barselsloven
    url2 = 'https://www.retsinformation.dk/api/document/eli/lta/2021/235'
    test_database.add_retsinfo_doc(url2)
   
    #lov om tidsbegrænset ansaettelse
    url3 = 'https://www.retsinformation.dk/api/document/eli/lta/2008/907'
    test_database.add_retsinfo_doc(url3)
    
    #lov om finansiel virksomhed (Ram explosion)
    #url4 = 'https://www.retsinformation.dk/api/document/eli/lta/2022/406'
    #test_database.add_retsinfo_doc(url4)
    
    #lov om investeringsforeninger m.v.
    url5 = 'https://www.retsinformation.dk/api/document/eli/lta/2022/336'
    test_database.add_retsinfo_doc(url5)
    
    print(len(test_database.external_ref))
    print(test_database.concept_count())
    test_database.connect_ext_ref()
    test_idf = test_database.word_idf    
    
    test_database.calculate_concept_vector()
    test_database.calculate_concept_bow()
    
    example_lc = test_database.random_lc()


#%% Description of funktionærloven §1    
    test_input = "En funktionær er en lønmodtager, som primært er ansat inden for handel- og kontorområdet. Du kan også være funktionær, hvis du udfører lagerarbejde eller tekniske og kliniske ydelser."

    test_database.get_input_sentence_dicts(test_input)
    
    test_input_sentence_dicts = test_database.input_sentence_dicts
    
    test_database.calculate_min_dist()
    test_min_dist = test_database.input_min_dist

    vec_tekniske = word_embeddings['tekniske']
    vec_teknisk = word_embeddings['teknisk']
    vec_beskyttelsesbestemmelserne = word_embeddings['beskyttelsesbestemmelserne']
    
    np.linalg.norm(vec_tekniske-vec_teknisk)
    np.linalg.norm(vec_tekniske-vec_beskyttelsesbestemmelserne)
    

#%% "Person A er bogholder."
    test_input = "Person A er bogholder."
    
    test_database.get_input_sentence_dicts(test_input)

    test_input_sentence_dicts = test_database.input_sentence_dicts
    
    test_database.calculate_min_dist()
    test_min_dist = test_database.input_min_dist
    
    vec_bogholder = word_embeddings['bogholder']
    vec_funktionaer = word_embeddings['funktionær']
    vec_kontorarbejde = word_embeddings['kontorarbejde']
    vec_nyansatte = word_embeddings['nyansatte']
    vec_ferieydelse = word_embeddings['ferieydelse']
    
    np.linalg.norm(vec_bogholder-vec_funktionaer)
    np.linalg.norm(vec_bogholder-vec_kontorarbejde)
    np.linalg.norm(vec_bogholder-vec_nyansatte)
    np.linalg.norm(vec_bogholder-vec_ferieydelse)
    
    
    
    
#%%     
    ## LOV-documents  Both need work!!!
    #lov om brug af køberet eller tegningsret til aktier m.v.
    url4 = 'https://www.retsinformation.dk/api/document/eli/lta/2004/309'   
    l_o_kr_tr_a = legal_concept_extractor_MAIN.get_law_document_dict(url4, stopwords, word_embeddings)

    #Lov om ret til orlov og dagpenge ved barsel (barselloven)
    url5 = 'https://www.retsinformation.dk/api/document/eli/lta/2006/566'
    l_o_dp_v_b = legal_concept_extractor_MAIN.get_law_document_dict(url5, stopwords, word_embeddings)
    
    
    
   
    
    
    # save data    
    with open("test_database.p", "wb") as pickle_file:
        pickle.dump(test_database, pickle_file)
    
    

    #open data
    with open("test_database.p", "rb") as pickle_file:
        opened_test_database = pickle.load(pickle_file)     

    opend_example_lc = opened_test_database.random_lc()

    
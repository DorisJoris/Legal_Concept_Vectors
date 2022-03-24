# -*- coding: utf-8 -*-
"""
Created on Fri Mar 18 11:05:58 2022

@author: bejob
"""

#%% Import
import pickle
import numpy as np
import random
from danlp.models.embeddings  import load_wv_with_gensim

from legal_concept_extractor import get_law_document_dict

#%% Concept_vector initializer (only based on the children)
def concept_vector_init(document_dict,hierachical_label_list): #The heirachical_label_list should be sorted lowest to highest hierachy.
    new_document_dict = document_dict    
    for label in hierachical_label_list:
        for legal_concept_key in new_document_dict['legal_concepts'].keys():
            if label in new_document_dict['legal_concepts'][legal_concept_key]['labels']:
                parent_bow = new_document_dict['legal_concepts'][legal_concept_key]['bow']
                sum_of_child_vec = np.array([0]*word_embeddings.vector_size, dtype='float32')
                n_of_child = 0
                
                for neighbour in new_document_dict['legal_concepts'][legal_concept_key]['neighbours']:
                    if neighbour['type'] == 'child':
                        child_id = neighbour['neighbour']
                        child_vec = new_document_dict['legal_concepts'][child_id]['concept_vector']
                        child_bow = new_document_dict['legal_concepts'][child_id]['bow']
                        if type(child_vec) == np.ndarray:
                            sum_of_child_vec = sum_of_child_vec + child_vec
                            n_of_child += 1
                        
                        for word in child_bow.keys():
                            if word in parent_bow.keys():
                                parent_bow[word] += child_bow[word]
                            else:
                                parent_bow[word] = child_bow[word]

                if n_of_child > 0:        
                    new_document_dict['legal_concepts'][legal_concept_key]['concept_vector'] = sum_of_child_vec/n_of_child
                    new_document_dict['legal_concepts'][legal_concept_key]['bow_meanvector'] = sum_of_child_vec/n_of_child
                    
                    new_document_dict['legal_concepts'][legal_concept_key]['bow'] = parent_bow
                    new_document_dict['legal_concepts'][legal_concept_key]['concept_bow'] = parent_bow
                
    return new_document_dict

#%% Concept_vector calculator (iterative calculation the mean of all neighbours for every concept)    
    
def concept_vector_calculator(document_dict, aver_dist_threshold):
    new_document_dict = document_dict
    aver_dist_prior_ultimo_concept_vector = 10
    n_concept_vector = len(new_document_dict['legal_concepts'].keys())
    iteration_count = 0
    while aver_dist_prior_ultimo_concept_vector > aver_dist_threshold:
        iteration_count += 1
        sum_dist_prior_ultimo_concept_vector = 0
        legal_concept_keys = list(new_document_dict['legal_concepts'].keys())
        random.shuffle(legal_concept_keys)
        for legal_concept_key in legal_concept_keys:
            prior_concept_vector = new_document_dict['legal_concepts'][legal_concept_key]['concept_vector']
            
            sum_of_neighbours_vec = np.array([0]*word_embeddings.vector_size, dtype='float32')
            n_of_neighbours = 0
            
            for neighbour in new_document_dict['legal_concepts'][legal_concept_key]['neighbours']:
                neighbour_id = neighbour['neighbour']
                neighbour_vec = new_document_dict['legal_concepts'][neighbour_id]['concept_vector']
                
                if type(neighbour_vec) == np.ndarray:
                    sum_of_neighbours_vec = sum_of_neighbours_vec + neighbour_vec
                    n_of_neighbours += 1
                
            if n_of_neighbours > 0:        
                ultimo_concept_vector = sum_of_neighbours_vec/n_of_neighbours
                
                sum_dist_prior_ultimo_concept_vector += np.linalg.norm(prior_concept_vector-ultimo_concept_vector)
                
                new_document_dict['legal_concepts'][legal_concept_key]['concept_vector'] = ultimo_concept_vector
            
        aver_dist_prior_ultimo_concept_vector = sum_dist_prior_ultimo_concept_vector/n_concept_vector
       
    print(iteration_count)
    return new_document_dict

#%% concept bow calculator
def concept_bow_calculator(document_dict):
    new_document_dict = document_dict

    legal_concept_keys = list(new_document_dict['legal_concepts'].keys())
    random.shuffle(legal_concept_keys)
    for legal_concept_key in legal_concept_keys:
        
        new_concept_bow = new_document_dict['legal_concepts'][legal_concept_key]['bow']
        neighbourhood = new_document_dict['legal_concepts'][legal_concept_key]['neighbours']
        
        neighbourhood_bow = dict()
        
        for neighbour in neighbourhood:
            neighbour_id = neighbour['neighbour']
            neighbour_bow = new_document_dict['legal_concepts'][neighbour_id]['bow']
            for word in neighbour_bow.keys():
                if word in neighbourhood_bow.keys():
                    neighbourhood_bow[word][0] = neighbourhood_bow[word][0]*neighbourhood_bow[word][1]
                    neighbourhood_bow[word][1] += 1
                    neighbourhood_bow[word][0] = (neighbourhood_bow[word][0] + neighbour_bow[word])/neighbourhood_bow[word][1]
                else:
                    neighbourhood_bow[word] = [neighbour_bow[word],1]
        
        for word in neighbourhood_bow.keys():
            if word not in new_concept_bow.keys():
                new_concept_bow[word] = neighbourhood_bow[word][0]                
        
        new_document_dict['legal_concepts'][legal_concept_key]['bow'] = document_dict['legal_concepts'][legal_concept_key]['bow']                                 
        new_document_dict['legal_concepts'][legal_concept_key]['concept_bow'] = new_concept_bow             
    
    return new_document_dict


#%% App
if __name__ == "__main__":
    
    word_embeddings = load_wv_with_gensim('conll17.da.wv')
    
    with open("stopord.txt","r", encoding="UTF-8") as sw_file:
        stopwords = [line.strip() for line in sw_file]
    
    law_hierachical_label_list = ['list','stk','paragraf','chapter','lov']  
    
    
    #funktionærloven
    url1 = 'https://www.retsinformation.dk/api/document/eli/lta/2017/1002'
    funktionaerloven = get_law_document_dict(url1, stopwords, word_embeddings)
    funktionaerloven = concept_vector_init(funktionaerloven,law_hierachical_label_list)
    funktionaerloven = concept_vector_calculator(funktionaerloven, 0.001)
    funktionaerloven = concept_bow_calculator(funktionaerloven)
    
    #barselsloven
    url2 = 'https://www.retsinformation.dk/api/document/eli/lta/2021/235'
    barselsloven = get_law_document_dict(url2, stopwords, word_embeddings)
    barselsloven = concept_vector_init(barselsloven,law_hierachical_label_list)
    
    #lov om tidsbegrænset ansaettelse
    url3 = 'https://www.retsinformation.dk/api/document/eli/lta/2008/907'
    l_o_tb_a = get_law_document_dict(url3, stopwords, word_embeddings)
    l_o_tb_a = concept_vector_init(l_o_tb_a,law_hierachical_label_list)
        
    

    
    
    # save data    
    with open("test_law_document.p", 'wb') as pickle_file:
        pickle.dump(funktionaerloven, pickle_file)
    
    

    #open data
    with open("test_paragraph_propert_list.p", "r") as pickle_file:
        opened_paragraph_property_list = pickle.load(pickle_file)     

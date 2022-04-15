# -*- coding: utf-8 -*-
"""
Created on Fri Mar 18 11:05:58 2022

@author: bejob
"""

#%% Import

import numpy as np
import random
import copy

#%% Concept_vector initializer (only based on the children)
def concept_vector_init(document_dict, hierachical_label_list, word_embeddings): #The heirachical_label_list should be sorted lowest to highest hierachy.
       
    for label in hierachical_label_list:
        for legal_concept_key in document_dict['legal_concepts'].keys():
            if label in document_dict['legal_concepts'][legal_concept_key]['labels']:
                parent_bow = document_dict['legal_concepts'][legal_concept_key]['bow']
                parent_concept_bow = document_dict['legal_concepts'][legal_concept_key]['concept_bow']
                sum_of_child_vec = np.array([0]*word_embeddings.vector_size, dtype='float32')
                n_of_child = 0
                
                for neighbour in document_dict['legal_concepts'][legal_concept_key]['neighbours']:
                    if neighbour['type'] == 'child':
                        child_id = neighbour['neighbour']
                        child_vec = document_dict['legal_concepts'][child_id]['concept_vector']
                        child_bow = document_dict['legal_concepts'][child_id]['bow']
                        if type(child_vec) == np.ndarray:
                            sum_of_child_vec = sum_of_child_vec + child_vec
                            n_of_child += 1
                        
                        for word in child_bow.keys():
                            if word in parent_bow.keys():
                                parent_bow[word] += child_bow[word]
                            else:
                                parent_bow[word] = child_bow[word]
                                
                            if word in parent_concept_bow.keys():
                                parent_concept_bow[word] += child_bow[word]
                            else:
                                parent_concept_bow[word] = child_bow[word]

                if n_of_child > 0:        
                    document_dict['legal_concepts'][legal_concept_key]['concept_vector'] = sum_of_child_vec/n_of_child
                    document_dict['legal_concepts'][legal_concept_key]['bow_meanvector'] = sum_of_child_vec/n_of_child
                    
                    document_dict['legal_concepts'][legal_concept_key]['bow'] = parent_bow
                    document_dict['legal_concepts'][legal_concept_key]['concept_bow'] = parent_concept_bow
                
    return document_dict

  

#%% Concept_vector calculator (iterative calculation the mean of all neighbours for every concept)    
    
def concept_vector_calculator(legal_concepts, aver_dist_threshold, word_embeddings):
    aver_dist_prior_ultimo_concept_vector = 1000
    n_concept_vector = len(legal_concepts.keys())
    iteration_count = 0
    neighbours_not_found = []
    while aver_dist_prior_ultimo_concept_vector > aver_dist_threshold:
        iteration_count += 1
        sum_dist_prior_ultimo_concept_vector = 0
        legal_concept_keys = list(legal_concepts.keys())
        random.shuffle(legal_concept_keys)
        for legal_concept_key in legal_concept_keys:
            prior_concept_vector = legal_concepts[legal_concept_key]['concept_vector']
            
            sum_of_neighbours_vec = np.array([0]*word_embeddings.vector_size, dtype='float32')
            n_of_neighbours = 0
            
            for neighbour in legal_concepts[legal_concept_key]['neighbours']:
                neighbour_id = neighbour['neighbour']
                try:
                    neighbour_vec = legal_concepts[neighbour_id]['concept_vector']
                    if type(neighbour_vec) == np.ndarray:
                        sum_of_neighbours_vec = sum_of_neighbours_vec + neighbour_vec
                        n_of_neighbours += 1
                except:
                    if neighbour_id not in neighbours_not_found:
                        neighbours_not_found.append(neighbour_id)
                
            if n_of_neighbours > 0:        
                ultimo_concept_vector = sum_of_neighbours_vec/n_of_neighbours
                
                sum_dist_prior_ultimo_concept_vector += np.linalg.norm(prior_concept_vector-ultimo_concept_vector)
                
                legal_concepts[legal_concept_key]['concept_vector'] = ultimo_concept_vector
            
        aver_dist_prior_ultimo_concept_vector = sum_dist_prior_ultimo_concept_vector/n_concept_vector
       
    print(f"{iteration_count} numbers of iteration where needed to calculate the concept vectors.") 
    print(f"The applied average distance threshold was {aver_dist_threshold}.")
    print("The following neighbour ID's could not be found:")
    for not_found_id in neighbours_not_found:
        print(not_found_id)
    return legal_concepts

#%% concept bow calculator
def concept_bow_calculator(legal_concepts, word_embeddings):
    candidat_keys = list(legal_concepts.keys())
    
    candidat_change_count = {}
    iteration_count = 0
    neighbours_not_found = []
    while len(candidat_keys) > 0:
        for key in candidat_keys:
            if key not in candidat_change_count.keys():
                candidat_change_count[key] = {'cb_len':len(legal_concepts[key]['concept_bow']),'cb_unchanged':0}
                
            neighbourhood = legal_concepts[key]['neighbours']
            
            neighbourhood_bow = dict()
            neighbourhood_size = len(neighbourhood)
            
            for neighbour in neighbourhood:
                neighbour_id = neighbour['neighbour']
                try:
                    neighbour_bow = legal_concepts[neighbour_id]['concept_bow']
                    for word in neighbour_bow.keys():
                        if word in neighbourhood_bow.keys():
                            neighbourhood_bow[word] = neighbourhood_bow[word] + (neighbour_bow[word]/neighbourhood_size)
                        else:
                            neighbourhood_bow[word] = neighbour_bow[word]/neighbourhood_size
                            
                except:
                    if neighbour_id not in neighbours_not_found:
                        neighbours_not_found.append(neighbour_id)
            
            for word in neighbourhood_bow.keys():
                if word in legal_concepts[key]['concept_bow'].keys():
                    if (legal_concepts[key]['concept_bow'][word] + neighbourhood_bow[word]) > (1/neighbourhood_size):
                        legal_concepts[key]['concept_bow'][word] = (legal_concepts[key]['concept_bow'][word] + neighbourhood_bow[word])*0.5
                        if word in legal_concepts[key]['bow'].keys():
                            legal_concepts[key]['concept_bow'][word] = legal_concepts[key]['concept_bow'][word] + (legal_concepts[key]['bow'][word]*0.5)
                else:
                    if neighbourhood_bow[word] > (1/neighbourhood_size):
                        legal_concepts[key]['concept_bow'][word] = (neighbourhood_bow[word]*0.5)
                    
            if len(legal_concepts[key]['concept_bow']) == candidat_change_count[key]['cb_len']:
                candidat_change_count[key]['cb_unchanged'] += 1
            else:
                candidat_change_count[key]['cb_len'] = len(legal_concepts[key]['concept_bow'])
                
            if candidat_change_count[key]['cb_unchanged'] == 2:
                candidat_keys.remove(key)
        
        iteration_count += 1
    
    for key in legal_concepts:
        max_cb_value = max(legal_concepts[key]['concept_bow'].values())
        concept_bow_meanvec = np.array([0]*word_embeddings.vector_size, dtype='float32')
        sum_of_weights = 0
        for word in legal_concepts[key]['concept_bow'].keys():
            legal_concepts[key]['concept_bow'][word] = legal_concepts[key]['concept_bow'][word]/max_cb_value
            concept_bow_meanvec = concept_bow_meanvec + (word_embeddings[word] * legal_concepts[key]['concept_bow'][word])
            sum_of_weights += legal_concepts[key]['concept_bow'][word]
            
        legal_concepts[key]['concept_bow_meanvector'] = concept_bow_meanvec/sum_of_weights
            
    print(f"{iteration_count} numbers of iteration where needed to calculate the concept bow.")
    print("The following neighbour ID's could not be found:")
    for not_found_id in neighbours_not_found:
        print(not_found_id)
    return legal_concepts



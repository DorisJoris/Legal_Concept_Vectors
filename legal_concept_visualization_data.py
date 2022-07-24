# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 18:07:25 2022

@author: bejob
"""
#%% import
import pickle
import numpy as np
import pandas as pd
import random
import re
import json

from dash import Dash, dcc, html, Input, Output, dash_table, no_update
import dash_bootstrap_components as dbc
import plotly.express as px


from sklearn.manifold import MDS
from sklearn.neighbors import NearestNeighbors

from datetime import datetime

import legal_concept_text_cleaning as lc_text_cleaning
import legal_concept_wmd


#%% input convertion
def calculate_input_bow_meanvector(input_dict, database):
    input_dict['input_bow'] = dict()
    input_dict['input_bow_meanvector'] = np.array([0]*database.word_embeddings.vector_size, dtype='float32')
    input_dict['input_oov_list'] = []
    
    for sentence_dict in input_dict['sentence_dicts']:
        try:
            input_dict['input_bow_meanvector'] += sentence_dict['input_bow_meanvector']
        except:
            continue
        input_dict['input_oov_list'] = input_dict['input_oov_list'] + sentence_dict['oov_list']
        for word in sentence_dict['input_bow']:
            if word in input_dict['input_bow'].keys():
                input_dict['input_bow'][word] += sentence_dict['input_bow'][word]
            else:
                input_dict['input_bow'][word] = sentence_dict['input_bow'][word]
    input_dict['input_bow_meanvector'] = input_dict['input_bow_meanvector']/len(input_dict['sentence_dicts']) 
    
    return input_dict

#%% 
def calculate_min_dist(input_dict, database, nbrs_cbowm, nbrs_cv):
    
    bow_types = [('wmd_concept_bow','concept_bow', 'reverse_wmd_concept_bow', 'weighted_reverse_wmd_concept_bow', 'weighted_wmd_concept_bow'),
                 ('wmd_bow', 'bow', 'reverse_wmd_bow', 'weighted_reverse_wmd_bow', 'weighted_wmd_bow')]
    
    max_level = database.concept_bow_meanvector_df['level'].max()
    
    
    search_vector = input_dict['input_bow_meanvector']
    
    cbowm_distances, cbowm_neighbours = nbrs_cbowm.kneighbors(search_vector.reshape(1,-1))
    cv_distances, cv_neighbours = nbrs_cv.kneighbors(search_vector.reshape(1,-1))
    
    # documents = [
    #     ('LBK nr 1002 af 24/08/2017','Bekendtgørelse af lov om retsforholdet mellem arbejdsgivere og funktionærer'),
    #     ('LBK nr 235 af 12/02/2021','Bekendtgørelse af lov om ret til orlov og dagpenge ved barsel (barselsloven)'),
    #     ('LBK nr 907 af 11/09/2008','Bekendtgørelse af lov om tidsbegrænset ansættelse'),
    #     ('LBK nr 336 af 11/03/2022','Bekendtgørelse af lov om investeringsforeninger m.v.'),
    #     ('LBK nr 193 af 02/03/2016','Bekendtgørelse af lov om aftaler og andre retshandler på formuerettens område'),
    #     ('LOV nr 1457 af 17/12/2013','Lov om forbrugeraftaler'),
    #     ('LBK nr 1284 af 14/06/2021','Bekendtgørelse af lov om indkomstskat for personer m.v. (personskatteloven)'),
    #     ('LBK nr 25 af 08/01/2021','Bekendtgørelse af lov om godkendte revisorer og revisionsvirksomheder (revisorloven)')
    #     ]
    
    input_dict['input_min_dist'] = {
        'concept_vector':dict(),
        'concept_bow_meanvector':dict(),
        'wmd_concept_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'wmd_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'reverse_wmd_concept_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'reverse_wmd_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'weighted_reverse_wmd_concept_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'weighted_reverse_wmd_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'weighted_wmd_concept_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'weighted_wmd_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            }
        }
    
    for i in range(10):
        key = f"{i+1}. closest"
        input_dict['input_min_dist']['concept_vector'][key] = (database.concept_vector_df.iloc[cv_neighbours[0][i]].name,
                                                               cv_distances[0][i])
        input_dict['input_min_dist']['concept_bow_meanvector'][key] = (database.concept_bow_meanvector_df.iloc[cbowm_neighbours[0][i]].name,
                                                               cbowm_distances[0][i])
    
    
    for bow_type in bow_types:
        changed = False
        for level in range(max_level+1):
            search_df = database.concept_bow_meanvector_df[database.concept_bow_meanvector_df.level == level]
            if input_dict['input_min_dist'][bow_type[0]]['1. closest'][0] != '':
                 search_parent_one = input_dict['input_min_dist'][bow_type[0]]['1. closest'][0]
                 search_parent_two = input_dict['input_min_dist'][bow_type[0]]['2. closest'][0]
                 search_parent_three = input_dict['input_min_dist'][bow_type[0]]['3. closest'][0]
                 search_df = search_df[(search_df.parent == search_parent_one) | 
                                       (search_df.parent == search_parent_two) |
                                       (search_df.parent == search_parent_three)]
            changed = False    
            for key in search_df.index.values.tolist():
            
                try:
                    wmd_dict = legal_concept_wmd.wmd(input_dict['input_bow'], 
                                                     database.legal_concepts[key][bow_type[1]], 
                                                     database.word_embeddings,
                                                     database.word_idf)
                    
                    if wmd_dict[0]['wmd'] <= input_dict['input_min_dist'][bow_type[0]]['1. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[0]]['3. closest'] = input_dict['input_min_dist'][bow_type[0]]['2. closest']
                        input_dict['input_min_dist'][bow_type[0]]['2. closest'] = input_dict['input_min_dist'][bow_type[0]]['1. closest']
                        input_dict['input_min_dist'][bow_type[0]]['1. closest'] = (
                            str(key),
                            wmd_dict[0]
                            )
                        changed = True
                        
                    elif wmd_dict[0]['wmd'] <=  input_dict['input_min_dist'][bow_type[0]]['2. closest'][1]['wmd']:  
                        input_dict['input_min_dist'][bow_type[0]]['3. closest'] = input_dict['input_min_dist'][bow_type[0]]['2. closest']
                        input_dict['input_min_dist'][bow_type[0]]['2. closest'] = (
                            str(key),
                            wmd_dict[0]
                            )
                        changed = True
                        
                    elif wmd_dict[0]['wmd'] <=  input_dict['input_min_dist'][bow_type[0]]['3. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[0]]['3. closest'] =  (
                            str(key),
                            wmd_dict[0]
                            )
                        changed = True
                    
                    if wmd_dict[1]['wmd'] <= input_dict['input_min_dist'][bow_type[2]]['1. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[2]]['3. closest'] = input_dict['input_min_dist'][bow_type[2]]['2. closest']
                        input_dict['input_min_dist'][bow_type[2]]['2. closest'] = input_dict['input_min_dist'][bow_type[2]]['1. closest']
                        input_dict['input_min_dist'][bow_type[2]]['1. closest'] = (
                            str(key),
                            wmd_dict[1]
                            )
                        changed = True
                        
                    elif wmd_dict[1]['wmd'] <=  input_dict['input_min_dist'][bow_type[2]]['2. closest'][1]['wmd']:  
                        input_dict['input_min_dist'][bow_type[2]]['3. closest'] = input_dict['input_min_dist'][bow_type[2]]['2. closest']
                        input_dict['input_min_dist'][bow_type[2]]['2. closest'] = (
                            str(key),
                            wmd_dict[1]
                            )
                        changed = True
                        
                    elif wmd_dict[1]['wmd'] <=  input_dict['input_min_dist'][bow_type[2]]['3. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[2]]['3. closest'] =  (
                            str(key),
                            wmd_dict[1]
                            )
                        changed = True
                        
                    if wmd_dict[2]['wmd'] <= input_dict['input_min_dist'][bow_type[3]]['1. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[3]]['3. closest'] = input_dict['input_min_dist'][bow_type[3]]['2. closest']
                        input_dict['input_min_dist'][bow_type[3]]['2. closest'] = input_dict['input_min_dist'][bow_type[3]]['1. closest']
                        input_dict['input_min_dist'][bow_type[3]]['1. closest'] = (
                            str(key),
                            wmd_dict[2]
                            )
                        changed = True
                        
                    elif wmd_dict[2]['wmd'] <=  input_dict['input_min_dist'][bow_type[3]]['2. closest'][1]['wmd']:  
                        input_dict['input_min_dist'][bow_type[3]]['3. closest'] = input_dict['input_min_dist'][bow_type[3]]['2. closest']
                        input_dict['input_min_dist'][bow_type[3]]['2. closest'] = (
                            str(key),
                            wmd_dict[2]
                            )
                        changed = True
                        
                    elif wmd_dict[2]['wmd'] <=  input_dict['input_min_dist'][bow_type[3]]['3. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[3]]['3. closest'] =  (
                            str(key),
                            wmd_dict[2]
                            )
                        changed = True 
                        
                    if wmd_dict[3]['wmd'] <= input_dict['input_min_dist'][bow_type[4]]['1. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[4]]['3. closest'] = input_dict['input_min_dist'][bow_type[4]]['2. closest']
                        input_dict['input_min_dist'][bow_type[4]]['2. closest'] = input_dict['input_min_dist'][bow_type[4]]['1. closest']
                        input_dict['input_min_dist'][bow_type[4]]['1. closest'] = (
                            str(key),
                            wmd_dict[3]
                            )
                        changed = True
                        
                    elif wmd_dict[3]['wmd'] <=  input_dict['input_min_dist'][bow_type[4]]['2. closest'][1]['wmd']:  
                        input_dict['input_min_dist'][bow_type[4]]['3. closest'] = input_dict['input_min_dist'][bow_type[4]]['2. closest']
                        input_dict['input_min_dist'][bow_type[4]]['2. closest'] = (
                            str(key),
                            wmd_dict[3]
                            )
                        changed = True
                        
                    elif wmd_dict[3]['wmd'] <=  input_dict['input_min_dist'][bow_type[4]]['3. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[4]]['3. closest'] =  (
                            str(key),
                            wmd_dict[3]
                            )
                        changed = True
                except:
                    pass
                
            if changed == False:
                break
        
        
        # for b in [0,2,3,4]:
        #     winners = []
        #     for key in input_dict['input_min_dist'][bow_type[b]].keys():
        #         winners.append(input_dict['input_min_dist'][bow_type[b]][key][0])
        #     # doc_nr = 0
            # for doc in documents:
            #     if doc[0] not in winners:
            #         doc_nr += 1
            #         wmd_dict = legal_concept_wmd.wmd(input_dict['input_bow'], 
            #                                          database.legal_concepts[doc[0]][bow_type[1]], 
            #                                          database.word_embeddings,
            #                                          database.word_idf)
            #         if b == 0:
            #             wmd_nr = 0
            #         else:
            #             wmd_nr = b-1
            #         input_dict['input_min_dist'][bow_type[b]][f'Other legal doc {doc_nr}'] = (str(doc[0]),wmd_dict[wmd_nr])
                        
            
    return input_dict

#%% 2d distance preserving plotter
def two_d_distance_preserving_plotter(list_of_points, list_of_distances):
    """
    Parameters
    ----------
    list_of_points : list of numpy array
        Should be a list of numpy arrays of equal lenght.
        The first numpy array will be the focus point and the others will be the neighbours.
    
    list_of_distances : list of int
        Should be a list of distances between the points and the focus point.

    Returns
    -------
    None.

    """
    dim = len(list_of_points[0])
    
    new_focus_point = np.array([0,0])
    new_neighbour_points = list()
    
    for a in range(1,len(list_of_points)):
        x = random.uniform(-1,1)
        y = random.uniform(-1,1)
        new_neighbour_point = np.array([x,y])
        

        goal_dist = (list_of_distances[a]/dim)*2
            
        start_dist = np.linalg.norm(new_focus_point-new_neighbour_point)
        
        new_x = new_neighbour_point[0]+(((new_focus_point[0]-new_neighbour_point[0])/start_dist)*((start_dist-goal_dist))) 
        new_y = new_neighbour_point[1]+(((new_focus_point[1]-new_neighbour_point[1])/start_dist)*((start_dist-goal_dist))) 
        new_neighbour_point = np.array([new_x,new_y])
        
        new_neighbour_points.append(new_neighbour_point)
    
        
    
    
    for k in range(4):    
        for i in range(1,len(list_of_points)):
            focus_neighbour_point = list_of_points[i]
            new_focus_neighbour_point = new_neighbour_points[i-1]
            
            for j in range(1,len(list_of_points)):
                if i == j:
                    continue
                else:
                    neighbour_point = list_of_points[j]
                    
                    goal_dist = (np.linalg.norm(focus_neighbour_point-neighbour_point)/dim)*2
                    start_dist = np.linalg.norm(new_focus_neighbour_point-new_neighbour_points[j-1])
                    
                    if start_dist != 0:
                        new_x = new_neighbour_points[j-1][0]+(((new_focus_neighbour_point[0]-new_neighbour_points[j-1][0])/start_dist)*((start_dist-goal_dist))) 
                        new_y = new_neighbour_points[j-1][1]+(((new_focus_neighbour_point[1]-new_neighbour_points[j-1][1])/start_dist)*((start_dist-goal_dist))) 
                        new_neighbour_points[j-1] = np.array([new_x,new_y])
                    else:
                        new_x = new_neighbour_points[j-1][0]+(((new_focus_neighbour_point[0]-new_neighbour_points[j-1][0]))*((start_dist-goal_dist))) 
                        new_y = new_neighbour_points[j-1][1]+(((new_focus_neighbour_point[1]-new_neighbour_points[j-1][1]))*((start_dist-goal_dist))) 
                        new_neighbour_points[j-1] = np.array([new_x,new_y])
                    
                    
            for g in range(1,len(list_of_points)):
                
                goal_dist = (list_of_distances[g]/dim)*2
                    
                start_dist = np.linalg.norm(new_focus_point-new_neighbour_points[g-1])
                
                new_x = new_neighbour_points[g-1][0]+(((new_focus_point[0]-new_neighbour_points[g-1][0])/start_dist)*((start_dist-goal_dist))) 
                new_y = new_neighbour_points[g-1][1]+(((new_focus_point[1]-new_neighbour_points[g-1][1])/start_dist)*((start_dist-goal_dist))) 
                new_neighbour_points[g-1] = np.array([new_x,new_y])
            
        
    
    return [new_focus_point]+new_neighbour_points

#%% Create visualization dataframe

def get_visual_df(input_dict, database):
    distance_labels = ['concept_bow_meanvector',
                       'concept_vector',
                       'reverse_wmd_bow',
                       'reverse_wmd_concept_bow',
                       'weighted_reverse_wmd_bow',
                       'weighted_reverse_wmd_concept_bow',
                       'weighted_wmd_bow',
                       'weighted_wmd_concept_bow',
                       'wmd_bow',
                       'wmd_concept_bow']
    
    # documents = [
    #     ('LBK nr 1002 af 24/08/2017','Bekendtgørelse af lov om retsforholdet mellem arbejdsgivere og funktionærer'),
    #     ('LBK nr 235 af 12/02/2021','Bekendtgørelse af lov om ret til orlov og dagpenge ved barsel (barselsloven)'),
    #     ('LBK nr 907 af 11/09/2008','Bekendtgørelse af lov om tidsbegrænset ansættelse'),
    #     ('LBK nr 336 af 11/03/2022','Bekendtgørelse af lov om investeringsforeninger m.v.'),
    #     ('LBK nr 193 af 02/03/2016','Bekendtgørelse af lov om aftaler og andre retshandler på formuerettens område'),
    #     ('LOV nr 1457 af 17/12/2013','Lov om forbrugeraftaler'),
    #     ('LBK nr 1284 af 14/06/2021','Bekendtgørelse af lov om indkomstskat for personer m.v. (personskatteloven)'),
    #     ('LBK nr 25 af 08/01/2021','Bekendtgørelse af lov om godkendte revisorer og revisionsvirksomheder (revisorloven)')
    #     ]
    
    visual_dfs = dict()
    
    zero_vector = np.array([0]*database.word_embeddings.vector_size, dtype='float32')
    for label in distance_labels:
        lc_names = [input_dict['id'],'Zero vector']
        list_of_points = [input_dict['input_bow_meanvector'],
                          zero_vector]
        
        list_of_types = ['Input','Zero']
        list_of_types_two = ['Text', 'Vector']
        list_of_raw_text = [input_dict['full_text'],'']
        list_of_word_pair_ranks = [0,0]
        list_of_bow_size = [sum(input_dict['input_bow'].values()),0]
        
        list_of_distances = [0,
                             np.linalg.norm(input_dict['input_bow_meanvector']-zero_vector)]
        
        for key in input_dict['input_min_dist'][label].keys():
            tup = input_dict['input_min_dist'][label][key]
            lc_names.append(tup[0].replace('§ ', '§\xa0'))
            if label == 'concept_vector':
                list_of_points.append(database.legal_concepts[tup[0].replace('§ ', '§\xa0')]['concept_vector'])
                list_of_bow_size.append(sum(database.legal_concepts[tup[0].replace('§ ', '§\xa0')]['concept_bow'].values()))
            else:
                list_of_points.append(database.legal_concepts[tup[0].replace('§ ', '§\xa0')]['concept_bow_meanvector'])
                
                if label in ['concept_bow_meanvector',
                                   'reverse_wmd_concept_bow',
                                   'weighted_reverse_wmd_concept_bow',
                                   'weighted_wmd_concept_bow',
                                   'wmd_concept_bow']:
                    list_of_bow_size.append(sum(database.legal_concepts[tup[0].replace('§ ', '§\xa0')]['concept_bow'].values()))
                else:
                    list_of_bow_size.append(sum(database.legal_concepts[tup[0].replace('§ ', '§\xa0')]['bow'].values()))
            list_of_types.append(key)
            list_of_types_two.append('Legal concept')
            raw_text = database.legal_concepts[tup[0].replace('§ ', '§\xa0')]['raw_text']
            raw_text = re.sub('  ', ' ', raw_text)
            list_of_raw_text.append(raw_text)
            list_of_word_pair_ranks.append(0)
                        
            if type(tup[1]) != dict:
                list_of_distances.append(tup[1])
            else:
                list_of_distances.append(tup[1]['wmd'])
                traveldistances = sorted(input_dict['input_min_dist'][label][key][1]['travel_distance_pairs'], key=lambda tup: tup[2])
                rank = 1
                for traveldistance in traveldistances[0:10]:
                    if traveldistance[0] not in lc_names:
                        lc_names.append(traveldistance[0])
                        vector = database.word_embeddings[traveldistance[0]]
                        list_of_points.append(vector)
                        list_of_types.append('Input')
                        list_of_types_two.append('word')
                        list_of_raw_text.append(traveldistance[0])
                        list_of_word_pair_ranks.append(rank)
                        dist = np.linalg.norm(input_dict['input_bow_meanvector']-vector)
                        list_of_distances.append(dist)
                        list_of_bow_size.append(1)
                    if traveldistance[1] not in lc_names:
                        lc_names.append(traveldistance[1])
                        vector = database.word_embeddings[traveldistance[1]]
                        list_of_points.append(vector)
                        list_of_types.append(key)
                        list_of_types_two.append('word')
                        list_of_raw_text.append(traveldistance[1])
                        list_of_word_pair_ranks.append(rank)
                        dist = np.linalg.norm(input_dict['input_bow_meanvector']-vector)
                        list_of_distances.append(dist)
                        list_of_bow_size.append(1)
                    rank += 1
                for traveldistance in traveldistances[-10:]:
                    if traveldistance[0] not in lc_names:
                        lc_names.append(traveldistance[0])
                        vector = database.word_embeddings[traveldistance[0]]
                        list_of_points.append(vector)
                        list_of_types.append('Input')
                        list_of_types_two.append('word')
                        list_of_raw_text.append(traveldistance[0])
                        list_of_word_pair_ranks.append(rank)
                        dist = np.linalg.norm(input_dict['input_bow_meanvector']-vector)
                        list_of_distances.append(dist)
                        list_of_bow_size.append(1)
                    if traveldistance[1] not in lc_names:
                        lc_names.append(traveldistance[1])
                        vector = database.word_embeddings[traveldistance[1]]
                        list_of_points.append(vector)
                        list_of_types.append(key)
                        list_of_types_two.append('word')
                        list_of_raw_text.append(traveldistance[1])
                        list_of_word_pair_ranks.append(rank)
                        dist = np.linalg.norm(input_dict['input_bow_meanvector']-vector)
                        list_of_distances.append(dist)
                        list_of_bow_size.append(1)
                    rank += 1
        
        # if label == 'concept_vector' or label == 'concept_bow_meanvector':
        #     doc_nr = 0
        #     for doc in documents:
        #         if doc not in lc_names:
        #             doc_nr += 1
        #             lc_names.append(doc[0])
        #             if label == 'concept_vector':
        #                 vector = database.legal_concepts[doc[0]]['concept_vector']
        #                 list_of_points.append(vector)
        #             else:
        #                 vector = database.legal_concepts[doc[0]]['concept_bow_meanvector']
        #                 list_of_points.append(vector)
                   
        #             list_of_types.append(f'Other legal doc {doc_nr}')
        #             list_of_types_two.append('Legal concept')
        #             #list_of_raw_text.append(doc[1])
        #             raw_text = database.legal_concepts[doc[0]]['raw_text']
        #             raw_text = re.sub('  ', ' ', raw_text)
        #             list_of_raw_text.append(raw_text)
        #             list_of_word_pair_ranks.append(0)
        #             dist = np.linalg.norm(input_dict['input_bow_meanvector']-vector)
        #             list_of_distances.append(dist)
        #             list_of_bow_size.append(sum(database.legal_concepts[tup[0].replace('§ ', '§\xa0')]['concept_bow'].values()))
        
        
        xy_df = pd.DataFrame(two_d_distance_preserving_plotter(list_of_points, list_of_distances),
                             columns = ['X','Y'])
        label_df = pd.DataFrame()
        label_df['Name'] = lc_names
        label_df['Neighbour type'] = list_of_types
        label_df['Point type'] = list_of_types_two
        label_df['Text'] = list_of_raw_text
        label_df['wordpair rank'] = list_of_word_pair_ranks
        label_df['Distance to input'] = list_of_distances
        label_df['BoW size'] = list_of_bow_size
        label_df = pd.concat([label_df, xy_df], axis =1)
        
        visual_dfs[label] = label_df
    return visual_dfs


#%% Get input sentence dict
def get_input_sentence_dicts(text, text_id, database):
    start=datetime.now()
    dimmension = database.word_embeddings.vector_size
    
    nbrs_cbowm = NearestNeighbors(n_neighbors=10, algorithm='ball_tree').fit(database.concept_bow_meanvector_df.iloc[:,0:dimmension]) 
    nbrs_cv = NearestNeighbors(n_neighbors=10, algorithm='ball_tree').fit(database.concept_vector_df.iloc[:,0:dimmension])

      
    input_dict = dict()
    input_dict['id'] = text_id
    input_dict['full_text'] = text
    input_sentences = lc_text_cleaning.split_text_into_sentences(text)
    
    wordfreq = database.doc_wordfreq.loc[:,database.doc_wordfreq.columns != 'parent_doc'].notnull().sum()
    N = len(database.doc_wordfreq)

    
    input_dict['sentence_dicts'] = []
    for sentence in input_sentences:
        sentence_dict = lc_text_cleaning.get_sentence_bow_meanvector(sentence,
                                                                      database.stopwords,
                                                                      database.word_embeddings,
                                                                      wordfreq,
                                                                      N)
        #sentence_dict = calculate_min_dist(sentence_dict, database, nbrs_cbowm, nbrs_cv)
        
        input_dict['sentence_dicts'].append(sentence_dict)
    
    input_dict = calculate_input_bow_meanvector(input_dict, database)
    
    # input_dict['cbowm_2d'] = database.pca_concept_bow_meanvector.transform(input_dict['input_bow_meanvector'].reshape(1,-1))
    # input_dict['cv_2d'] = database.pca_concept_vector.transform(input_dict['input_bow_meanvector'].reshape(1,-1))
    # input_dict['bm_2d'] = database.pca_bow_meanvector.transform(input_dict['input_bow_meanvector'].reshape(1,-1))
    
    input_dict = calculate_min_dist(input_dict, database, nbrs_cbowm, nbrs_cv)
    try:
        visual_dfs = get_visual_df(input_dict, database)
    except:
        visual_dfs = pd.DataFrame
    
    print(datetime.now()-start)
    return visual_dfs, input_dict

#%% 
def get_inputs_visual_dfs(input_list, database):
    input_visual_dfs = dict()
    for input_tup in input_list:
        visual_dfs, input_dict = get_input_sentence_dicts(input_tup[0], input_tup[1], database)
        input_visual_dfs[input_tup[1]] = (visual_dfs, input_dict)
        
    return input_visual_dfs

#%% Open database
if __name__ == "__main__":
    #open data
    with open("databases/test_database.p", "rb") as pickle_file:
        test_database = pickle.load(pickle_file) 
        
    example_lc = test_database.random_lc()



#%% Input text
if __name__ == "__main__":
    test_input_list = [("En funktionær er en lønmodtager, som primært er ansat "
                       +"inden for handel- og kontorområdet. " 
                       +"Du kan også være funktionær, hvis du udfører "
                       +"lagerarbejde eller tekniske og kliniske ydelser.",
                       "En funktionær er en lønmodtager... (Funktionærloven)"),#Funktionærloven -> https://www.frie.dk/find-svar/ansaettelsesvilkaar/funktionaerloven/#:~:text=En%20funktion%C3%A6r%20er%20en%20l%C3%B8nmodtager,arbejdstid%20er%20minimum%208%20timer.
                       
                       ("Der er en lang række fleksible muligheder - specielt for de forældre, "
                       +"som gerne vil vende tilbage til arbejdet efter for eksempel seks eller "
                       +"otte måneders orlov og gemme resten af orloven, til barnet er blevet lidt ældre. "
                       +"Eller for de forældre, der ønsker at dele orloven eller starte på arbejde på "
                       +"nedsat tid og dermed forlænge orloven. Fleksibiliteten forudsætter i de "
                       +"fleste tilfælde, at der er indgået en aftale med arbejdsgiveren.", 
                       "Der er en lang række fleksible... (Barselsloven)"),#Barselsloven -> https://bm.dk/arbejdsomraader/arbejdsvilkaar/barselsorlov/barselsorloven-hvor-meget-orlov-og-hvordan-kan-den-holdes/
                       
                       ("Når du er tidsbegrænset ansat, gælder der et princip om, at du ikke "
                       +"må forskelsbehandles i forhold til virksomhedens fastansatte, "
                       +"medmindre forskelsbehandlingen er begrundet i objektive forhold. "
                       +"Du har altså de samme rettigheder som de fastansatte.", 
                       "Når du er tidsbegrænset ansat... (Lov om tidsbegrænset ansættelse"),#Tidsbegrænset ansættelse -> https://sl.dk/faa-svar/ansaettelse/tidsbegraenset-ansaettelse
                       
                       ("Person A er bogholder.", 
                        "Person A er bogholder."),
                       
                       ("Bogholderen Anja venter sit første barn. Hendes termin nærmer sig med hastige skridt.",
                        "Bogholderen Anja venter første barn..."),
                       
                       ("Jan's kone er gravid. Han glæder sig meget til at være hjemmegående og bruge tid med hans søn.",
                        "Jan's kone er gravid..."),
                       
                       ("Den nye malersvend blev fyret efter en uge.",
                        "Den nye malersvend blev fyret efter en uge."),
                       
                       ("Den nye salgschef blev fyret efter en uge.", 
                        "Den nye salgschef blev fyret efter en uge.")
                       ]   
    
    
    


#%% create input_visual_dfs
if __name__ == "__main__":
#test_visual_dfs, test_input_dict = get_input_sentence_dicts(test_input_list[0][0], test_input_list[0][1], test_database)

    input_visual_dfs = get_inputs_visual_dfs(test_input_list, test_database)

#%% Save input_visual_dfs
if __name__ == "__main__":
    with open("visualization_data/input_visual_dfs_new.p", "wb") as pickle_file:
        pickle.dump(input_visual_dfs, pickle_file) 
    
    #with open("visualization_data/word_idf.p", "wb") as pickle_file:
    #    pickle.dump(test_database.word_idf, pickle_file) 
    
    #with open("visualization_data/stopwords_list.p", "wb") as pickle_file:
    #    pickle.dump(test_database.stopwords, pickle_file) 

#%% Open pickled input visual_dfs
if __name__ == "__main__":
    with open("visualization_data/input_visual_dfs.p", "rb") as pickle_file:
        input_visual_dfs = pickle.load(pickle_file) 

#%% plotly
if __name__ == "__main__":
    external_stylesheets = [dbc.themes.MINTY]
    app = Dash(__name__, external_stylesheets=external_stylesheets)
    
    tab_graph = dbc.Card(dbc.CardBody([
        dcc.Graph(id="graph"),
        html.P(['Selected point:']),
        html.P(id='text-print', style= {"width": "90%",
                                        "height": "150px",
                                        "padding": "2px",
                                        "margin-left":"5%",
                                        "margin-right":"5%",
                                        "border": "1px solid grey",
                                        "border-radius": "5px",
                                        "overflow-wrap": "break-word",
                                        "overflow": "scroll"
                                        })
        ]))
    
    tab_table = dbc.Card(dbc.CardBody([
        html.Div(id='table')
        ]))
    
    tab_latex = dbc.Card(dbc.CardBody([
        dbc.Row([
            dbc.Col(dbc.Label('Include columns:'),width=2),
            dbc.Col(dcc.Dropdown(id='latex_dropdown',multi=True))
            ]),
        dbc.Card(html.Div(id='latex'))
        ]))
    
    app.layout = dbc.Container([
        html.H1('Legal concept experiments'),
        dbc.Row([
            dbc.Col(dbc.Label('Select input:'),width=2),
            dbc.Col(dcc.Dropdown(
                id="input_select",
                options=list(input_visual_dfs.keys()),
                value=list(input_visual_dfs.keys())[0],
                multi=False
            )),
        ]),
        dbc.Row([
            dbc.Col(dbc.Label('Select distance measure:'),width=2),
            dbc.Col(dcc.Dropdown(
                id="distance_type",
                options=['concept_bow_meanvector',
                                   'concept_vector',
                                   'reverse_wmd_bow',
                                   'reverse_wmd_concept_bow',
                                   'weighted_reverse_wmd_bow',
                                   'weighted_reverse_wmd_concept_bow',
                                   'weighted_wmd_bow',
                                   'weighted_wmd_concept_bow',
                                   'wmd_bow',
                                   'wmd_concept_bow'],
                value='concept_bow_meanvector',
                multi=False
            )),
        ]),
        dbc.Row([
            dbc.Col(dbc.Label('Select neighbour type:'),width=2),
            dbc.Col(dcc.Dropdown(id='neighbour_dropdown',multi=True))
        ]),
        dbc.Row([
            dbc.Col(dbc.Label('Select point type:'),width=2),
            dbc.Col(dcc.Dropdown(id='document_dropdown',multi=True))
        ]),
        dbc.Tabs(
            [dbc.Tab(tab_graph, label='Graph'),
             dbc.Tab(tab_table, label='Table'),
             dbc.Tab(tab_latex, label='Latex table code')
                ]
            )
        
    ])
    
    @app.callback(
        Output('neighbour_dropdown','options'),
        Output('neighbour_dropdown','value'),
        Output('document_dropdown','options'),
        Output('document_dropdown','value'),
        Input("input_select", "value"),
        Input("distance_type", "value"))
    def init_multi_dropdowns(input_option, dist_option):
        neighbour_values = input_visual_dfs[input_option][0][dist_option]['Neighbour type'].unique()
        doc_values = input_visual_dfs[input_option][0][dist_option]['Point type'].unique()
        
        return neighbour_values, neighbour_values, doc_values, doc_values
    
    @app.callback(
        Output("table", "children"),
        Input("input_select", "value"),
        Input("distance_type", "value"),
        Input('graph', 'clickData'),
        Input('neighbour_dropdown','value'),
        Input('document_dropdown','value'))
    def update_table(input_option, dist_option, clickData, neighbour_options, doc_options):
        
        output_df = input_visual_dfs[input_option][0][dist_option]
        output_df = output_df[output_df['Neighbour type'].isin(neighbour_options)]
        output_df = output_df[output_df['Point type'].isin(doc_options)]
    
        
        table_df = output_df[['Name','Neighbour type','Point type','Distance to input']]
        
        if clickData == None:
            return dash_table.DataTable(table_df.to_dict('records'), 
                                      [{"name": i, "id": i} for i in table_df.columns],
                                      style_cell={'textAlign': 'left'},
                                      sort_action="native",
                                      sort_mode="multi"
                                          ) 
        else:
            filter_query = '{Name} = "' +clickData['points'][0]['text'] +'"'
            print(filter_query)
            return dash_table.DataTable(table_df.to_dict('records'), 
                                      [{"name": i, "id": i} for i in table_df.columns],
                                      style_cell={'textAlign': 'left'},
                                      sort_action="native",
                                      sort_mode="multi",
                                      style_data_conditional=[{
                                          'if': {
                                              'filter_query': filter_query,
                                              'column_id': 'Name'
                                          },
                                          'backgroundColor': 'tomato',
                                          'color': 'white'
                                      },
                                          {
                                          'if': {
                                              'filter_query': filter_query,
                                              'column_id': 'Neighbour type'
                                          },
                                          'backgroundColor': 'tomato',
                                          'color': 'white'
                                      },
                                          {
                                          'if': {
                                              'filter_query': filter_query,
                                              'column_id': 'Point type'
                                          },
                                          'backgroundColor': 'tomato',
                                          'color': 'white'
                                      },
                                          {
                                          'if': {
                                              'filter_query': filter_query,
                                              'column_id': 'Distance to input'
                                          },
                                          'backgroundColor': 'tomato',
                                          'color': 'white'
                                      }
                                  ]
                                          ) 
    
    
    
    
    @app.callback(
        Output("graph", "figure"),
        Input("input_select", "value"),
        Input("distance_type", "value"),
        Input('neighbour_dropdown','value'),
        Input('document_dropdown','value'))
    def update_bar_chart(input_option, dist_option, neighbour_options, doc_options):
        
        output_df = input_visual_dfs[input_option][0][dist_option]
        output_df = output_df[output_df['Neighbour type'].isin(neighbour_options)]
        output_df = output_df[output_df['Point type'].isin(doc_options)]
        
        fig = px.scatter(output_df, 
                         x="X", y="Y", 
                         text="Name", 
                         hover_data=['Name','Distance to input'], 
                         color= 'Neighbour type',
                         color_discrete_sequence=px.colors.qualitative.Dark24,
                         symbol = 'Point type'
                         )
        fig.update_traces(textposition='top center')
        fig.update_layout(legend={'title_text':''})
        fig.update_layout(yaxis_visible=False, yaxis_showticklabels=False,
                          xaxis_visible=False, xaxis_showticklabels=False)
        fig.update_layout({
                        'plot_bgcolor': 'rgba(0, 0, 0, 0.1)',
                        'legend_bgcolor': 'rgba(0, 0, 0, 0.1)',
                        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
                            })
        
        
       
        return fig
    
    @app.callback(
        Output("graph", "clickData"),
        Input("input_select", "value"))
    def rest_clickdata(input_option):
        return None
    
    
    @app.callback(
        Output('text-print', 'children'),
        Input('graph', 'clickData'),
        Input("input_select", "value"),
        Input("distance_type", "value"))
    def display_click_data(clickData,input_option, dist_option):
        
        output_df = input_visual_dfs[input_option][0][dist_option]
        
        if clickData == None:
            search_name = "Name: " + output_df.loc[0,'Name']
            search_type = "Type: " + output_df.loc[0,'Neighbour type']
            text = [search_name,  html.Br(), search_type,  html.Br(), output_df.loc[0,'Text']]
        else:
            search_name = clickData['points'][0]['text']
            search_type = list(output_df.loc[output_df.index[output_df['Name'] == search_name], 'Neighbour type'])[0]
            text = list(output_df.loc[output_df['Name'] == search_name, 'Text'])[0]
            text = ["Name: " + search_name,  html.Br(),"Type: " + search_type,  html.Br(), text]
            
           
        return text
    
    @app.callback(
        Output('latex_dropdown','options'),
        Output('latex_dropdown','value'),
        Input("input_select", "value"),
        Input("distance_type", "value"))
    
    def init_latex_dropdown(input_option, dist_option):
        
        columns = list(input_visual_dfs[input_option][0][dist_option].columns)
    
        return columns, columns    
    
    @app.callback(
        Output('latex', 'children'),
        Input("input_select", "value"),
        Input("distance_type", "value"),
        Input('neighbour_dropdown','value'),
        Input('document_dropdown','value'),
        Input('latex_dropdown','value'))
    def display_latex_code(input_option, dist_option, neighbour_options, doc_options, columns):
        
        output_df = input_visual_dfs[input_option][0][dist_option]
        output_df = output_df[output_df['Neighbour type'].isin(neighbour_options)]
        output_df = output_df[output_df['Point type'].isin(doc_options)]
        
        output_df = output_df[[c for c in output_df.columns if c in columns]]
        
        latex_code = output_df.to_latex(index=False,
                                        caption=(f'{input_option} + {dist_option}'),
                                        label='tab:add label',
                                        float_format="%.4f")
        
        latex_list = list()
        for line in latex_code.split("\n"):
            latex_list.append(line)
            latex_list.append(html.Br())
        return latex_list
    
        
    app.run_server(debug=False)
    
    
    
    
    
    #%% latex export
    if __name__ == "__main__":
        
        wmd_bow_1_td_pairs_df = pd.DataFrame(sorted(input_dict['input_min_dist']['wmd_bow']['1. closest'][1]['travel_distance_pairs'], key=lambda tup: tup[2]),
                                             columns=['Input word','Legal concept word','Distance'])
    
        print(wmd_bow_1_td_pairs_df.to_latex(index=False,
                                             caption=('Travel distance pairs of the 1. closets legal concept BOW for the WMD.'),
                                             label='wmd_bow_1_td_pais',
                                             float_format="%.4f"))   
    
        test_latex = input_visual_dfs['En funktionær er en lønmodtager... (Funktionærloven)'][0]['concept_bow_meanvector'].to_latex(index=False,
                                        caption=(''),
                                        label='tab:add label',
                                        float_format="%.4f")
        test_latex_list = test_latex.split("\n")
        
        
        
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 16:31:43 2022

@author: bejob
"""

#%% import 
import pickle
import pandas as pd

from legal_concept_visualization_data import get_input_sentence_dicts

#%% Open pickled bert database


with open("databases/w2v_database.p", "rb") as pickle_file:
    test_database = pickle.load(pickle_file)    
    
    
#%% import gold standard dataset

gold_std_df = pd.read_csv('Test dataset.csv')

in_database = list()
for index, row in gold_std_df.iterrows():
    key = row['Target'].replace('§\\xa0','§\xa0')
    try:
        test_database.legal_concepts[key]
        in_database.append(True)
    except:
        in_database.append(False)
        
gold_std_df['In database'] = in_database

#%%

def concept_network_distance_score(concept_id_one, concept_id_two):
    concept_id_one_list = concept_id_one.split('_')
    concept_id_two_list = concept_id_two.split('_')
    
    network_dist = 10
    break_out_flag = False
    
    for i in range(len(concept_id_one_list)):
        for j in range(len(concept_id_two_list)):
            if concept_id_one_list[i:] == concept_id_two_list[j:]:
                network_dist = i+j
                break_out_flag = True
                break
        
        if break_out_flag:
            break
        
    if network_dist > 3:
        network_dist_score = 0
    else:
        network_dist_score = 3- network_dist
    
    return network_dist_score

#%%
concept_vector = list()
cv_dist_score = list()

reverse_wmd_concept_bow = list()
rwmd_dist_score = list()

wmd_concept_bow = list()
wmd_dist_score = list()

for index, row in gold_std_df.iterrows():
    target = row['Target'].replace('§\\xa0','§\xa0')
    visual_dfs, input_dict = get_input_sentence_dicts(row['Query text'], index, test_database)
    
    
    cv_closest = input_dict['input_min_dist']['concept_vector']['1. closest'][0]
    concept_vector.append(cv_closest)
    cv_dist_score.append(concept_network_distance_score(target, cv_closest))
    
    rwmd_closest = input_dict['input_min_dist']['reverse_wmd_concept_bow']['1. closest'][0]
    reverse_wmd_concept_bow.append(rwmd_closest)
    rwmd_dist_score.append(concept_network_distance_score(target, rwmd_closest))
    
    wmd_closest = input_dict['input_min_dist']['wmd_concept_bow']['1. closest'][0]
    wmd_concept_bow.append(wmd_closest)
    wmd_dist_score.append(concept_network_distance_score(target, wmd_closest))

gold_std_df['concept_vector'] = concept_vector
gold_std_df['cv_dist_score'] = cv_dist_score

gold_std_df['reverse_wmd_concept_bow'] = reverse_wmd_concept_bow
gold_std_df['rwmd_dist_score'] = rwmd_dist_score

gold_std_df['wmd_concept_bow'] = wmd_concept_bow
gold_std_df['wmd_dist_score'] = wmd_dist_score

#%% Test save

# with open("saved tests/w2v_gold_std_df.p", "wb") as pickle_file:
#     pickle.dump(gold_std_df, pickle_file)

gold_std_df.to_csv("saved tests/w2v_gold_std_df.csv")  
    
#%% Open test

# with open("saved tests/w2v_gold_std_df.p", "rb") as pickle_file:
#     gold_std_df = pickle.load(pickle_file)   
    
gold_std_df = pd.read_csv("saved tests/w2v_gold_std_df.csv")


#%%
cv_acc_score = gold_std_df['cv_dist_score'].sum()/len(gold_std_df)    
rwmd_acc_score = gold_std_df['rwmd_dist_score'].sum()/len(gold_std_df)    
wmd_acc_score = gold_std_df['wmd_dist_score'].sum()/len(gold_std_df)    

print(f'The concept vector accuracy is {cv_acc_score}')  
print(f'The reverse word mover distance accuracy is {rwmd_acc_score}')  
print(f'The word mover distance accuracy is {wmd_acc_score}')   
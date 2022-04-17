# -*- coding: utf-8 -*-
"""
Created on Sat Apr 16 10:18:36 2022

@author: bejob
"""

#%% Import


import pandas as pd
import copy

#%% Experiment

df = pd.DataFrame()

doc1 = {'hallo':1,'du':2}

new_row_bow = doc1
new_row_bow.update({'parent_doc':'funktionærlove'})
new_row_name = 'doc1'
new_row = pd.Series(new_row_bow,name=new_row_name)

df = df.append(new_row)

doc2 = {'du':1,'der':4}

new_row_bow = doc2
new_row_bow.update({'parent_doc':'funktionærlove'})
new_row_name = 'doc2'
new_row = pd.Series(new_row_bow,name=new_row_name)

df = df.append(new_row)

df2 = pd.DataFrame()

doc3 = {'du':1,'der':3,'jeg':1}
new_row_bow = doc3
new_row_bow.update({'parent_doc':'barselsloven'})
new_row_name = 'doc3'
new_row = pd.Series(new_row_bow,name=new_row_name)

df2 = df2.append(new_row)

df =df.append(df2)

df.notnull().sum()

wordfreq = df.loc[:,df.columns != 'parent_doc'].notnull().sum()


#%% doc wordfreq dataframe pandas
def add_to_doc_wordfreq_dataframe(legal_concept_dict):
    """Takes in a dictionary of all sentences and adds their bow and parent document name to the dataframe.
    Based on Pandas."""
    concept_count = len(legal_concept_dict.keys())
    progress = (1/concept_count)*100
    
    local_df = pd.DataFrame()
    for key in legal_concept_dict.keys():
        progress += (1/concept_count)*100
        print(f"\rDoc-Wordfreq-Dataframe creation: [{('#' * (int(progress)//5)) + ('_' * (20-(int(progress)//5)))}] ({int(progress//1)}%)", end='\r')
        if legal_concept_dict[key]['labels'][1] == 'sentence':
            local_lc_bow = copy.copy(legal_concept_dict[key]['concept_bow'])
            try:
                local_lc_bow.update({'parent_doc':legal_concept_dict[key]['parent'][-1]})
            except:
                local_lc_bow.update({'parent_doc':legal_concept_dict[key]['id']})
            lc_id = legal_concept_dict[key]['id']
            new_row = pd.Series(local_lc_bow,name=lc_id)
            local_df = local_df.append(new_row)
        
    return local_df
        

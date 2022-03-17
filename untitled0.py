# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 11:33:03 2022

@author: bejob
"""
# Initial comment:
# The purpose of this code is to extract and segment the text of a danish law into its subparts,  
# such as paragraphs, stk (sections of a paragraph) and so on and organize these in a neo4j database. 
# The code reuses code writen for Funktionærloven, LBK nr 1002 af 24/08/2017, and is applied to
# Barselsloven, LBK nr 235 af 12/02/2021
#%% Import

import urllib.request
import json
import copy
from retsgraph import create_node
from retsgraph import create_relation
from legal_concept_resources import abbreviations
from legal_concept_resources import lov_label_list
from legal_concept_resources import paragraph_label_list
from legal_concept_resources import stk_label_list
from legal_concept_resources import litra_label_list
from legal_concept_resources import nr_label_list
from legal_concept_resources import sentence_label_list
from legal_concept_resources import relative_stk_ref_cues
from legal_concept_resources import internal_ref_to_whole_law_cues

from bs4 import BeautifulSoup as bs

from legal_concept_extractor import law_property_gen as lce_law_property_gen

#%%




#%% CREATING litra + number + sentence nodes in neo4j    
if __name__ == "__main__":
    
    url = 'https://www.retsinformation.dk/api/document/eli/lta/2021/235'
    
    #Lov
    lov_soup, lov_property_dict, lov_name, lov_shortname = lce_law_property_gen(url)



for s in sentence_property_list:
    print('')
    print('Now?:')
    if input() == 'y':
        print('')
        print(s['parent'])
        print(s['raw_text'])
        
for s in stk_internal_ref_query_list:
    print('')
    print('Now?:')
    if input() == 'y':
        print('')
        print(s[0])
        print(s[1])

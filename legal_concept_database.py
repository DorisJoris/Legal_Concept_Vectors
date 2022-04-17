# -*- coding: utf-8 -*-
#%% Import
import random
import numpy as np
import pandas as pd
import copy

import legal_concept_extractor_MAIN as lc_em
import legal_concept_vector_calculator as lc_vc
import legal_concept_text_cleaning as lc_text_cleaning
import legal_concept_wmd
import legal_concept_tf_idf as lc_tf_idf

from legal_concept_resources import hierachical_label_list

#%% Database class

class lc_database:
    def __init__(self, init_url, stopwords, word_embeddings):
        self.hierachical_label_list = hierachical_label_list
        self.stopwords = stopwords
        self.word_embeddings = word_embeddings
        
        init_lc_doc = lc_em.get_law_document_dict(init_url, 
                                                    self.stopwords, 
                                                    self.word_embeddings)
        
        self.doc_wordfreq = pd.DataFrame()
        self.doc_wordfreq = self.doc_wordfreq.append(lc_tf_idf.add_to_doc_wordfreq_dataframe(init_lc_doc['legal_concepts']))
        
        wordfreq = self.doc_wordfreq.loc[:,self.doc_wordfreq.columns != 'parent_doc'].notnull().sum()
        N = len(self.doc_wordfreq)
        self.word_idf = np.log(N/(wordfreq+1))
        
        init_lc_doc = lc_vc.concept_vector_init(init_lc_doc, 
                                                    self.hierachical_label_list, 
                                                    self.word_embeddings,
                                                    self.word_idf)
        
        self.external_ref = init_lc_doc['external_ref']
        self.legal_concepts = init_lc_doc['legal_concepts']
        self.oov_list = init_lc_doc['oov_list']
    
    # Helper functions
    def concept_count(self):
        return len(self.legal_concepts)
    
    def random_lc(self):
        key = random.choice(list(self.legal_concepts.keys()))
        return self.legal_concepts[key]
    
    #Add new retsinfo documents
    def add_retsinfo_doc(self, url):
        to_be_added_doc = lc_em.get_law_document_dict(url, 
                                                        self.stopwords, 
                                                        self.word_embeddings)
        
        self.doc_wordfreq = self.doc_wordfreq.append(lc_tf_idf.add_to_doc_wordfreq_dataframe(to_be_added_doc['legal_concepts']))
        
        wordfreq = self.doc_wordfreq.loc[:,self.doc_wordfreq.columns != 'parent_doc'].notnull().sum()
        N = len(self.doc_wordfreq)
        self.word_idf = np.log(N/(wordfreq+1))
        
        to_be_added_doc = lc_vc.concept_vector_init(to_be_added_doc, 
                                                        self.hierachical_label_list, 
                                                        self.word_embeddings,
                                                        self.word_idf)
        
       
        
        self.legal_concepts.update(to_be_added_doc['legal_concepts'])
        
        for ref in to_be_added_doc['external_ref']:
            if ref not in self.external_ref:
                self.external_ref.append(ref)
                
        for oov_word in to_be_added_doc['oov_list']:
            if oov_word not in self.oov_list:
                self.oov_list.append(oov_word)
    
    # Conncet the external refs
    def connect_ext_ref(self):
        for ex_ref in self.external_ref:
            ref_instance = ex_ref[1]
            if ref_instance['parent_law'] in self.legal_concepts.keys():
                
                referee_key = ex_ref[0]['name']
                for parent in ex_ref[0]['parent']:
                    referee_key = referee_key + '_' + parent
                
                ref_keys = []    
                for ref in ref_instance['p_ref_list']:
                    parents = ref['partial_parent']
                    parents.append(ref_instance['parent_law'])
                    
                    for ref_name in ref['ref_names']:
                        # remember "i"-problem -> if ref_name[-2] =='i':
                        for key in self.legal_concepts.keys():
                            if ref_name == self.legal_concepts[key]['name']:
                                suspect = True
                                for parent in parents:
                                    if parent not in self.legal_concepts[key]['parent']:
                                        suspect = False
                                        break
                                if suspect == True:
                                    ref_keys.append(key)
                 
                for ref_key in ref_keys:
                    self.legal_concepts[referee_key]['neighbours'].append(
                        {'neighbour':ref_key,'type':'ref_to'})
                    self.legal_concepts[ref_key]['neighbours'].append(
                        {'neighbour':referee_key,'type':'ref_from'})
                
                self.external_ref.remove(ex_ref)
    
    # Calculate the concept vectors and bows
    def calculate_concept_vector(self, aver_dist_threshold = 0.01):
        self.legal_concepts = lc_vc.concept_vector_calculator(self.legal_concepts, 
                                                                aver_dist_threshold, 
                                                                self.word_embeddings)
        
    def calculate_concept_bow(self, min_tf_threshold = 0.08):
        
        wordfreq = self.doc_wordfreq.loc[:,self.doc_wordfreq.columns != 'parent_doc'].notnull().sum()
        N = len(self.doc_wordfreq)
        word_idf = np.log(N/(wordfreq+1))
        
        self.legal_concepts = lc_vc.concept_bow_calculator(self.legal_concepts,
                                                           min_tf_threshold,
                                                           self.word_embeddings,
                                                           word_idf)

    # Get search input        
    def get_input_sentence_dicts(self, text):
        self.input_text = text
        input_sentences = lc_text_cleaning.split_text_into_sentences(text)
        
        wordfreq = self.doc_wordfreq.loc[:,self.doc_wordfreq.columns != 'parent_doc'].notnull().sum()
        N = len(self.doc_wordfreq)

        
        self.input_sentence_dicts = []
        for sentence in input_sentences:
            sentence_dict = lc_text_cleaning.get_sentence_bow_meanvector(sentence,
                                                                         self.stopwords,
                                                                         self.word_embeddings,
                                                                         wordfreq,
                                                                         N)
            self.input_sentence_dicts.append(sentence_dict)
        
        self.calculate_input_bow_meanvector()
            
    def calculate_input_bow_meanvector(self):
        self.input_bow = dict()
        self.input_bow_meanvector = np.array([0]*self.word_embeddings.vector_size, dtype='float32')
        self.input_oov_list = []
        
        for sentence_dict in self.input_sentence_dicts:
            self.input_bow_meanvector += sentence_dict['bow_meanvector']
            self.input_oov_list = self.input_oov_list + sentence_dict['oov_list']
            for word in sentence_dict['bow']:
                if word in self.input_bow.keys():
                    self.input_bow[word] += sentence_dict['bow'][word]
                else:
                    self.input_bow[word] = sentence_dict['bow'][word]
        self.input_bow_meanvector = self.input_bow_meanvector/len(self.input_sentence_dicts)    
    
    # Find closest concept
                                                 
    def calculate_min_dist(self):
        
        self.input_min_dist = {
            'concept_vector':{
                '1. closest': ('',1000.00),
                '2. closest': ('',1000.00),
                '3. closest': ('',1000.00)
                },
            'concept_bow_meanvector':{
                '1. closest': ('',1000.00),
                '2. closest': ('',1000.00),
                '3. closest': ('',1000.00)
                },
            'wmd_concept_bow':{
                '1. closest': ('',{'wmd':1000.00}),
                '2. closest': ('',{'wmd':1000.00}),
                '3. closest': ('',{'wmd':1000.00})
                }
            }
        
        vector_types = ['concept_vector', 'concept_bow_meanvector']
        bow_types = [('wmd_concept_bow','concept_bow'),('wmd_bow', 'bow')]
        
        concept_count = self.concept_count()
        progress = (1/concept_count)*100
        
        
        for key in self.legal_concepts.keys():
            progress += (1/concept_count)*100
            print(f"\rDistance calculation: [{('#' * (int(progress)//5)) + ('_' * (20-(int(progress)//5)))}] ({int(progress//1)}%)", end='\r')
            
            for vector_type in vector_types:
                try:
                    concept_vector = copy.copy(self.legal_concepts[key][vector_type])
                    
                    distance_input_cv = np.linalg.norm(self.input_bow_meanvector-concept_vector)
                    
                    if distance_input_cv < self.input_min_dist[vector_type]['1. closest'][1]:
                        self.input_min_dist[vector_type]['3. closest'] = self.input_min_dist[vector_type]['2. closest']
                        self.input_min_dist[vector_type]['2. closest'] = self.input_min_dist[vector_type]['1. closest']
                        self.input_min_dist[vector_type]['1. closest'] = (
                            str(key),
                            float(distance_input_cv)
                            )
                        
                    elif distance_input_cv <  self.input_min_dist[vector_type]['2. closest'][1]:  
                        self.input_min_dist[vector_type]['3. closest'] = self.input_min_dist[vector_type]['2. closest']
                        self.input_min_dist[vector_type]['2. closest'] = (
                            str(key),
                            float(distance_input_cv)
                            )
                        
                    elif distance_input_cv <  self.input_min_dist[vector_type]['3. closest'][1]:
                        self.input_min_dist[vector_type]['3. closest'] =  (
                            str(key),
                            float(distance_input_cv)
                            )
                except:
                    pass
                            
            for bow_type in bow_types:
                try:
                    wmd_dict = legal_concept_wmd.wmd(self.input_bow, 
                                                     self.legal_concepts[key][bow_type[1]], 
                                                     self.word_embeddings)
                    
                    if wmd_dict['wmd'] < self.input_min_dist[bow_type[0]]['1. closest'][1]['wmd']:
                        self.input_min_dist[bow_type[0]]['3. closest'] = self.input_min_dist[bow_type[0]]['2. closest']
                        self.input_min_dist[bow_type[0]]['2. closest'] = self.input_min_dist[bow_type[0]]['1. closest']
                        self.input_min_dist[bow_type[0]]['1. closest'] = (
                            str(key),
                            wmd_dict
                            )
                        
                    elif wmd_dict['wmd'] <  self.input_min_dist[bow_type[0]]['2. closest'][1]['wmd']:  
                        self.input_min_dist[bow_type[0]]['3. closest'] = self.input_min_dist[bow_type[0]]['2. closest']
                        self.input_min_dist[bow_type[0]]['2. closest'] = (
                            str(key),
                            wmd_dict
                            )
                        
                    elif wmd_dict['wmd'] <  self.input_min_dist[bow_type[0]]['3. closest'][1]['wmd']:
                        self.input_min_dist[bow_type[0]]['3. closest'] =  (
                            str(key),
                            wmd_dict
                            )
                except:
                    pass
            
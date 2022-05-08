# -*- coding: utf-8 -*-
#%% Import
import random
import numpy as np
import pandas as pd
import copy
from sklearn.decomposition import PCA

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
        
        # init_lc_doc = lc_vc.concept_vector_init(init_lc_doc, 
        #                                             self.hierachical_label_list, 
        #                                             self.word_embeddings,
        #                                             self.word_idf)
        
        self.external_ref = init_lc_doc['external_ref']
        self.legal_concepts = init_lc_doc['legal_concepts']
        self.oov_list = init_lc_doc['oov_list']
        #self.input_list = []
    
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
        
        # to_be_added_doc = lc_vc.concept_vector_init(to_be_added_doc, 
        #                                                 self.hierachical_label_list, 
        #                                                 self.word_embeddings,
        #                                                 self.word_idf)
        
       
        
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
    
    def concept_bow_vector_init(self):
        self.legal_concepts = lc_vc.concept_vector_init(self.legal_concepts, 
                                                            self.hierachical_label_list, 
                                                            self.word_embeddings,
                                                            self.word_idf)
    
    # Calculate the concept vectors and bows
    def calculate_concept_vector(self, aver_dist_threshold = 30):
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
    
    # Calculate concept dfs
    def get_vector_dfs(self):
        columns = []
        for i in range(self.word_embeddings.vector_size):
            columns.append(f"Dim_{i+1}")
            
        self.concept_bow_meanvector_df = pd.DataFrame()
        self.concept_vector_df = pd.DataFrame()
        self.bow_meanvector_df = pd.DataFrame()
        
        for key in self.legal_concepts.keys():
            if type(self.legal_concepts[key]['parent']) != list:
                level = 0
                parents = self.legal_concepts[key]['parent']
            else:
                level = len(self.legal_concepts[key]['parent'])
                parents = self.legal_concepts[key]['parent']
            
            key_cbowm_df = pd.DataFrame([self.legal_concepts[key]['concept_bow_meanvector']], 
                                  index=[self.legal_concepts[key]['id']],
                                  columns=columns)
            key_cbowm_df['level'] = level
            key_cbowm_df['parent'] = '_'.join([str(item) for item in parents])
            
            self.concept_bow_meanvector_df = self.concept_bow_meanvector_df.append(key_cbowm_df)
            
            key_cv_df = pd.DataFrame([self.legal_concepts[key]['concept_vector']], 
                                  index=[self.legal_concepts[key]['id']],
                                  columns=columns)
            key_cv_df['level'] = level
            key_cv_df['parent'] = '_'.join([str(item) for item in parents])
            
            self.concept_vector_df = self.concept_vector_df.append(key_cv_df)
            
            
            word_vector_sum = np.array([0]*self.word_embeddings.vector_size, dtype='float32')
            word_count = 0
            for word in self.legal_concepts[key]['bow']:
                try:
                    word_vector = self.word_embeddings[word]
                    word_vector_sum += word_vector*self.legal_concepts[key]['bow'][word]
                    word_count += self.legal_concepts[key]['bow'][word]
                except:
                    word_vector = None
                
            if word_count > 0:
                word_vector_mean = word_vector_sum/word_count
                key_bm_df = pd.DataFrame([word_vector_mean], 
                                      index=[self.legal_concepts[key]['id']],
                                      columns=columns)
                key_bm_df['level'] = level
                key_bm_df['parent'] = '_'.join([str(item) for item in parents])
                
                self.bow_meanvector_df = self.bow_meanvector_df.append(key_bm_df)
            else:
                word_vector_mean = None
            
            
            
    #     self.get_PCAs()
        
    #     cbowm_pca_oupt = self.pca_concept_bow_meanvector.transform(self.concept_bow_meanvector_df.iloc[:,0:self.word_embeddings.vector_size])
    #     self.concept_bow_meanvector_df = pd.concat([self.concept_bow_meanvector_df,
    #                                                 pd.DataFrame(cbowm_pca_oupt,columns=("X","Y"),
    #                                                              index=self.concept_bow_meanvector_df.index)], 
    #                                                axis=1)
        
    #     cv_pca_oupt = self.pca_concept_vector.transform(self.concept_vector_df.iloc[:,0:self.word_embeddings.vector_size])
    #     self.concept_vector_df = pd.concat([self.concept_vector_df,
    #                                                 pd.DataFrame(cv_pca_oupt,columns=("X","Y"),
    #                                                              index=self.concept_vector_df.index)], 
    #                                                axis=1)
        
    #     bm_pca_oupt = self.pca_bow_meanvector.transform(self.bow_meanvector_df.iloc[:,0:self.word_embeddings.vector_size])
    #     self.bow_meanvector_df = pd.concat([self.bow_meanvector_df,
    #                                                 pd.DataFrame(bm_pca_oupt,columns=("X","Y"),
    #                                                              index=self.bow_meanvector_df.index)], 
    #                                                axis=1)
    
    # def get_PCAs(self):
    #     self.pca_concept_bow_meanvector = PCA(n_components = 2)
    #     self.pca_concept_bow_meanvector.fit(self.concept_bow_meanvector_df.iloc[:,0:self.word_embeddings.vector_size])
        
    #     self.pca_concept_vector = PCA(n_components = 2)
    #     self.pca_concept_vector.fit(self.concept_vector_df.iloc[:,0:self.word_embeddings.vector_size])
        
    #     self.pca_bow_meanvector = PCA(n_components = 2)
    #     self.pca_bow_meanvector.fit(self.bow_meanvector_df.iloc[:,0:self.word_embeddings.vector_size])
    
    # Get search input        
    
        
    
    
 
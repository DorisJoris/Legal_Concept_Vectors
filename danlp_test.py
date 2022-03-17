# -*- coding: utf-8 -*-
"""
Created on Sun Mar 13 22:09:41 2022

@author: bejob
"""

from danlp.models.embeddings  import load_wv_with_gensim

# Load with gensim
word_embeddings = load_wv_with_gensim('conll17.da.wv')

kbh = word_embeddings.wv['københavn']

# -*- coding: utf-8 -*-
"""
Created on Mon May  9 18:11:11 2022

@author: bejob
"""
import pandas as pd

sorted_test =sorted(input_dict['input_min_dist']['wmd_bow']['1. closest'][1]['travel_distance_pairs'], key=lambda tup: tup[2])

wmd_bow_1_td_pairs_df = pd.DataFrame(sorted(input_dict['input_min_dist']['wmd_bow']['1. closest'][1]['travel_distance_pairs'], key=lambda tup: tup[2]),
                                     columns=['input_word','legal_concept_word','distance'])

print(wmd_bow_1_td_pairs_df.to_latex(index=False,
                                     caption='Travel distance pairs of the 1. closets legal concept BOW for the WMD.',
                                     label='wmd_bow_1_td_pais')
      )

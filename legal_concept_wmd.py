#%% import
import numpy as np

#%% WMD function
def wmd(input_bow, lc_bow, word_embeddings):
    max_input_bow_value = max(input_bow.values())
    max_lc_bow_value = max(lc_bow.values())
    
    wmd = 0
    min_travel_distance_pairs = []
    
    for word in input_bow:
        input_word_vec = word_embeddings[word]
        word_min_travel_distance = 1000.000
        word_min_td_lc_word = ''
        for lc_word in lc_bow:
            lc_word_vec = word_embeddings[lc_word]
            current_travel_distance = np.linalg.norm(input_word_vec - lc_word_vec)
            current_travel_distance = current_travel_distance / (input_bow[word]/max_input_bow_value)
            current_travel_distance = current_travel_distance / (lc_bow[lc_word]/max_lc_bow_value)
            if current_travel_distance < word_min_travel_distance:
                word_min_travel_distance = current_travel_distance
                word_min_td_lc_word = lc_word
        
        wmd += word_min_travel_distance
        min_travel_distance_pairs.append((word,word_min_td_lc_word,word_min_travel_distance))
    
    return {'wmd':wmd/len(input_bow), 
            'travel_distance_pairs': min_travel_distance_pairs
            }
        
            
    
    
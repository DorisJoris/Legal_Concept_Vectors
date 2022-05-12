#%% import
import numpy as np

#%% WMD function
def wmd(input_bow, lc_bow, word_embeddings, idf):
    #max_input_bow_value = max(input_bow.values())
    #max_lc_bow_value = max(lc_bow.values())
    
    wmd = 0
    min_travel_distance_pairs = []
    
    weighted_wmd = 0
    weighted_min_travel_distance_pairs = []
    
    reverse_wmd = 0
    reverse_min_travel_distance_pairs= []
    
    weighted_reverse_wmd = 0
    weighted_reverse_min_travel_distance_pairs = []
    lc_idf_sum = 0
    
    for word in input_bow:
        input_word_vec = word_embeddings[word]
        word_min_travel_distance = 1000.000
        word_min_td_lc_word = ''
        

        
        for lc_word in lc_bow:
            lc_word_vec = word_embeddings[lc_word]
            current_travel_distance = np.linalg.norm(input_word_vec - lc_word_vec)
            #current_travel_distance = current_travel_distance / (input_bow[word]/max_input_bow_value)
            #current_travel_distance = current_travel_distance / (lc_bow[lc_word]/max_lc_bow_value)
            if current_travel_distance < word_min_travel_distance:
                word_min_travel_distance = current_travel_distance
                word_min_td_lc_word = lc_word
                lc_word_idf = idf[lc_word]
        
        wmd += word_min_travel_distance
        min_travel_distance_pairs.append((word,word_min_td_lc_word,word_min_travel_distance))
        
        lc_idf_sum += lc_word_idf
        weighted_wmd += word_min_travel_distance*lc_word_idf
        weighted_min_travel_distance_pairs.append((word,word_min_td_lc_word,word_min_travel_distance*lc_word_idf))
    
    reverse_lc_idf_sum = 0    
    for lc_word in lc_bow:
        lc_word_vec = word_embeddings[lc_word]
        lc_word_min_travel_distance = 1000.000
        weighted_lc_word_min_travel_distance = 1000.00
        lc_word_min_td_word = ''
        weighted_lc_word_min_td_word = ''
        lc_word_idf = idf[lc_word]

        
        for word in input_bow:
            input_word_vec = word_embeddings[word]
            current_travel_distance = np.linalg.norm(input_word_vec - lc_word_vec)
            weighted_current_travel_distance = np.linalg.norm(input_word_vec - lc_word_vec)*lc_word_idf
            
            if current_travel_distance < lc_word_min_travel_distance:
               lc_word_min_travel_distance = current_travel_distance
               lc_word_min_td_word = word
            
            if weighted_current_travel_distance < weighted_lc_word_min_travel_distance:
               weighted_lc_word_min_travel_distance = weighted_current_travel_distance
               weighted_lc_word_min_td_word = word
        
        reverse_wmd += lc_word_min_travel_distance
        reverse_min_travel_distance_pairs.append((lc_word_min_td_word,lc_word,lc_word_min_travel_distance))   
        
        reverse_lc_idf_sum += lc_word_idf
        weighted_reverse_wmd += weighted_lc_word_min_travel_distance
        weighted_reverse_min_travel_distance_pairs.append((weighted_lc_word_min_td_word,lc_word,weighted_lc_word_min_travel_distance))

    return ({'wmd':wmd/len(input_bow), 
            'travel_distance_pairs': min_travel_distance_pairs
            },
            {'wmd':reverse_wmd/len(lc_bow), 
             'travel_distance_pairs': reverse_min_travel_distance_pairs
             },
            {'wmd':weighted_reverse_wmd/reverse_lc_idf_sum, 
             'travel_distance_pairs': weighted_reverse_min_travel_distance_pairs
             },
            {'wmd':weighted_wmd/lc_idf_sum, 
                    'travel_distance_pairs': weighted_min_travel_distance_pairs
                    })
        
            
    
    
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
    weight_sum = 0
    weighted_weight_sum = 0
    
    input_bow_max = sum(input_bow.values())
    lc_bow_max =  sum(lc_bow.values())
    
    for word in input_bow:
        input_word_vec = word_embeddings[word]
        word_min_travel_distance = 1000.000
        word_min_td_lc_word = ''
        
        weighted_word_min_travel_distance = 1000.00
        weighted_word_min_td_lc_word = ''
        
        for lc_word in lc_bow:
            lc_word_vec = word_embeddings[lc_word]
            lc_word_idf = idf[lc_word]
            current_travel_distance = np.linalg.norm(input_word_vec - lc_word_vec)*(input_bow[word]/input_bow_max)*(lc_bow[lc_word]/lc_bow_max)
            weighted_current_travel_distance = np.linalg.norm(input_word_vec - lc_word_vec)*((input_bow[word]/input_bow_max))*((lc_bow[lc_word]/lc_bow_max)*lc_word_idf)
            
            if current_travel_distance < word_min_travel_distance:
                word_min_travel_distance = current_travel_distance
                word_min_td_lc_word = lc_word
                current_weight = (input_bow[word]/input_bow_max)*(lc_bow[lc_word]/lc_bow_max)
                acc_travel_distance = np.linalg.norm(input_word_vec - lc_word_vec)
                
            if weighted_current_travel_distance < weighted_word_min_travel_distance:
                weighted_word_min_travel_distance = weighted_current_travel_distance
                weighted_word_min_td_lc_word = lc_word
                current_weighted_weight = ((input_bow[word]/input_bow_max))*((lc_bow[lc_word]/lc_bow_max)*lc_word_idf)
                acc_travel_distance_w = np.linalg.norm(input_word_vec - lc_word_vec)
        
        wmd += word_min_travel_distance
        min_travel_distance_pairs.append((word,word_min_td_lc_word,word_min_travel_distance,acc_travel_distance))
        weight_sum +=  current_weight
        
        weighted_weight_sum += current_weighted_weight
        weighted_wmd += weighted_word_min_travel_distance
        weighted_min_travel_distance_pairs.append((word,weighted_word_min_td_lc_word,weighted_word_min_travel_distance,acc_travel_distance_w))
    
    reverse_weight_sum = 0 
    reverse_weighted_weight_sum = 0   
    for lc_word in lc_bow:
        lc_word_vec = word_embeddings[lc_word]
        lc_word_min_travel_distance = 1000.000
        weighted_lc_word_min_travel_distance = 1000.00
        lc_word_min_td_word = ''
        weighted_lc_word_min_td_word = ''
        lc_word_idf = idf[lc_word]

        
        for word in input_bow:
            input_word_vec = word_embeddings[word]
            current_travel_distance = np.linalg.norm(input_word_vec - lc_word_vec)*(input_bow[word]/input_bow_max)*(lc_bow[lc_word]/lc_bow_max)
            weighted_current_travel_distance = np.linalg.norm(input_word_vec - lc_word_vec)*((input_bow[word]/input_bow_max))*((lc_bow[lc_word]/lc_bow_max)*lc_word_idf)
            
            if current_travel_distance < lc_word_min_travel_distance:
               lc_word_min_travel_distance = current_travel_distance
               lc_word_min_td_word = word
               current_weight = (input_bow[word]/input_bow_max)*(lc_bow[lc_word]/lc_bow_max)
               acc_travel_distance = np.linalg.norm(input_word_vec - lc_word_vec)
            
            if weighted_current_travel_distance < weighted_lc_word_min_travel_distance:
               weighted_lc_word_min_travel_distance = weighted_current_travel_distance
               weighted_lc_word_min_td_word = word
               current_weighted_weight = ((input_bow[word]/input_bow_max))*((lc_bow[lc_word]/lc_bow_max)*lc_word_idf)
               acc_travel_distance_w = np.linalg.norm(input_word_vec - lc_word_vec)
        
        reverse_wmd += lc_word_min_travel_distance
        reverse_min_travel_distance_pairs.append((lc_word_min_td_word,lc_word,lc_word_min_travel_distance,acc_travel_distance))   
        reverse_weight_sum += current_weight
        
        reverse_weighted_weight_sum += current_weighted_weight
        weighted_reverse_wmd += weighted_lc_word_min_travel_distance
        weighted_reverse_min_travel_distance_pairs.append((weighted_lc_word_min_td_word,lc_word,weighted_lc_word_min_travel_distance,acc_travel_distance_w))

    return ({'wmd':wmd/weight_sum, 
            'travel_distance_pairs': min_travel_distance_pairs
            },
            {'wmd':reverse_wmd/reverse_weight_sum, 
             'travel_distance_pairs': reverse_min_travel_distance_pairs
             },
            {'wmd':weighted_reverse_wmd/reverse_weighted_weight_sum, 
             'travel_distance_pairs': weighted_reverse_min_travel_distance_pairs
             },
            {'wmd':weighted_wmd/weighted_weight_sum, 
                    'travel_distance_pairs': weighted_min_travel_distance_pairs
                    })
        
            
    
    
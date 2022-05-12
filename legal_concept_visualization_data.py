# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 18:07:25 2022

@author: bejob
"""
#%% import
import pickle
import numpy as np
import pandas as pd
import random
from dash import Dash, dcc, html, Input, Output
import plotly.express as px


from sklearn.manifold import MDS
from sklearn.neighbors import NearestNeighbors

from datetime import datetime

import legal_concept_text_cleaning as lc_text_cleaning
import legal_concept_wmd


#%% input convertion
def calculate_input_bow_meanvector(input_dict, database):
    input_dict['input_bow'] = dict()
    input_dict['input_bow_meanvector'] = np.array([0]*database.word_embeddings.vector_size, dtype='float32')
    input_dict['input_oov_list'] = []
    
    for sentence_dict in input_dict['sentence_dicts']:
        input_dict['input_bow_meanvector'] += sentence_dict['input_bow_meanvector']
        input_dict['input_oov_list'] = input_dict['input_oov_list'] + sentence_dict['oov_list']
        for word in sentence_dict['input_bow']:
            if word in input_dict['input_bow'].keys():
                input_dict['input_bow'][word] += sentence_dict['input_bow'][word]
            else:
                input_dict['input_bow'][word] = sentence_dict['input_bow'][word]
    input_dict['input_bow_meanvector'] = input_dict['input_bow_meanvector']/len(input_dict['sentence_dicts']) 
    
    return input_dict

#%% 
def calculate_min_dist(input_dict, database, nbrs_cbowm, nbrs_cv):
    
    bow_types = [('wmd_concept_bow','concept_bow', 'reverse_wmd_concept_bow', 'weighted_reverse_wmd_concept_bow', 'weighted_wmd_concept_bow'),
                 ('wmd_bow', 'bow', 'reverse_wmd_bow', 'weighted_reverse_wmd_bow', 'weighted_wmd_bow')]
    
    max_level = database.concept_bow_meanvector_df['level'].max()
    
    
    search_vector = input_dict['input_bow_meanvector']
    
    cbowm_distances, cbowm_neighbours = nbrs_cbowm.kneighbors(search_vector.reshape(1,-1))
    cv_distances, cv_neighbours = nbrs_cv.kneighbors(search_vector.reshape(1,-1))
    
   
    
    input_dict['input_min_dist'] = {
        'concept_vector':dict(),
        'concept_bow_meanvector':dict(),
        'wmd_concept_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'wmd_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'reverse_wmd_concept_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'reverse_wmd_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'weighted_reverse_wmd_concept_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'weighted_reverse_wmd_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'weighted_wmd_concept_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'weighted_wmd_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            }
        }
    
    for i in range(10):
        key = f"{i+1}. closest"
        input_dict['input_min_dist']['concept_vector'][key] = (database.concept_vector_df.iloc[cv_neighbours[0][i]].name,
                                                               cv_distances[0][i])
        input_dict['input_min_dist']['concept_bow_meanvector'][key] = (database.concept_vector_df.iloc[cv_neighbours[0][i]].name,
                                                               cv_distances[0][i])
    
    
    for bow_type in bow_types:
        changed = False
        for level in range(max_level+1):
            search_df = database.concept_bow_meanvector_df[database.concept_bow_meanvector_df.level == level]
            if input_dict['input_min_dist'][bow_type[0]]['1. closest'][0] != '':
                search_parent = input_dict['input_min_dist'][bow_type[0]]['1. closest'][0]
                search_df = search_df[search_df.parent == search_parent]
            changed = False    
            for key in search_df.index.values.tolist():
                try:
                    wmd_dict = legal_concept_wmd.wmd(input_dict['input_bow'], 
                                                     database.legal_concepts[key][bow_type[1]], 
                                                     database.word_embeddings,
                                                     database.word_idf)
                    
                    if wmd_dict[0]['wmd'] < input_dict['input_min_dist'][bow_type[0]]['1. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[0]]['3. closest'] = input_dict['input_min_dist'][bow_type[0]]['2. closest']
                        input_dict['input_min_dist'][bow_type[0]]['2. closest'] = input_dict['input_min_dist'][bow_type[0]]['1. closest']
                        input_dict['input_min_dist'][bow_type[0]]['1. closest'] = (
                            str(key),
                            wmd_dict[0]
                            )
                        changed = True
                        
                    elif wmd_dict[0]['wmd'] <  input_dict['input_min_dist'][bow_type[0]]['2. closest'][1]['wmd']:  
                        input_dict['input_min_dist'][bow_type[0]]['3. closest'] = input_dict['input_min_dist'][bow_type[0]]['2. closest']
                        input_dict['input_min_dist'][bow_type[0]]['2. closest'] = (
                            str(key),
                            wmd_dict[0]
                            )
                        changed = True
                        
                    elif wmd_dict[0]['wmd'] <  input_dict['input_min_dist'][bow_type[0]]['3. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[0]]['3. closest'] =  (
                            str(key),
                            wmd_dict[0]
                            )
                        changed = True
                    
                    if wmd_dict[1]['wmd'] < input_dict['input_min_dist'][bow_type[2]]['1. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[2]]['3. closest'] = input_dict['input_min_dist'][bow_type[2]]['2. closest']
                        input_dict['input_min_dist'][bow_type[2]]['2. closest'] = input_dict['input_min_dist'][bow_type[2]]['1. closest']
                        input_dict['input_min_dist'][bow_type[2]]['1. closest'] = (
                            str(key),
                            wmd_dict[1]
                            )
                        changed = True
                        
                    elif wmd_dict[1]['wmd'] <  input_dict['input_min_dist'][bow_type[2]]['2. closest'][1]['wmd']:  
                        input_dict['input_min_dist'][bow_type[2]]['3. closest'] = input_dict['input_min_dist'][bow_type[2]]['2. closest']
                        input_dict['input_min_dist'][bow_type[2]]['2. closest'] = (
                            str(key),
                            wmd_dict[1]
                            )
                        changed = True
                        
                    elif wmd_dict[1]['wmd'] <  input_dict['input_min_dist'][bow_type[2]]['3. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[2]]['3. closest'] =  (
                            str(key),
                            wmd_dict[1]
                            )
                        changed = True
                        
                    if wmd_dict[2]['wmd'] < input_dict['input_min_dist'][bow_type[3]]['1. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[3]]['3. closest'] = input_dict['input_min_dist'][bow_type[3]]['2. closest']
                        input_dict['input_min_dist'][bow_type[3]]['2. closest'] = input_dict['input_min_dist'][bow_type[3]]['1. closest']
                        input_dict['input_min_dist'][bow_type[3]]['1. closest'] = (
                            str(key),
                            wmd_dict[2]
                            )
                        changed = True
                        
                    elif wmd_dict[2]['wmd'] <  input_dict['input_min_dist'][bow_type[3]]['2. closest'][1]['wmd']:  
                        input_dict['input_min_dist'][bow_type[3]]['3. closest'] = input_dict['input_min_dist'][bow_type[3]]['2. closest']
                        input_dict['input_min_dist'][bow_type[3]]['2. closest'] = (
                            str(key),
                            wmd_dict[2]
                            )
                        changed = True
                        
                    elif wmd_dict[2]['wmd'] <  input_dict['input_min_dist'][bow_type[3]]['3. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[3]]['3. closest'] =  (
                            str(key),
                            wmd_dict[2]
                            )
                        changed = True 
                        
                    if wmd_dict[3]['wmd'] < input_dict['input_min_dist'][bow_type[4]]['1. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[4]]['3. closest'] = input_dict['input_min_dist'][bow_type[4]]['2. closest']
                        input_dict['input_min_dist'][bow_type[4]]['2. closest'] = input_dict['input_min_dist'][bow_type[4]]['1. closest']
                        input_dict['input_min_dist'][bow_type[4]]['1. closest'] = (
                            str(key),
                            wmd_dict[3]
                            )
                        changed = True
                        
                    elif wmd_dict[3]['wmd'] <  input_dict['input_min_dist'][bow_type[4]]['2. closest'][1]['wmd']:  
                        input_dict['input_min_dist'][bow_type[4]]['3. closest'] = input_dict['input_min_dist'][bow_type[4]]['2. closest']
                        input_dict['input_min_dist'][bow_type[4]]['2. closest'] = (
                            str(key),
                            wmd_dict[3]
                            )
                        changed = True
                        
                    elif wmd_dict[3]['wmd'] <  input_dict['input_min_dist'][bow_type[4]]['3. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[4]]['3. closest'] =  (
                            str(key),
                            wmd_dict[3]
                            )
                        changed = True
                except:
                    pass
                
            if changed == False:
                break
            
    return input_dict

#%% 2d distance preserving plotter
def two_d_distance_preserving_plotter(list_of_points, list_of_distances):
    """
    Parameters
    ----------
    list_of_points : list of numpy array
        Should be a list of numpy arrays of equal lenght.
        The first numpy array will be the focus point and the others will be the neighbours.
    
    list_of_distances : list of int
        Should be a list of distances between the points and the focus point.

    Returns
    -------
    None.

    """
    dim = len(list_of_points[0])
    
    new_focus_point = np.array([0,0])
    new_neighbour_points = list()
    
    for i in range(1,len(list_of_points)):
        x = random.uniform(-1,1)
        y = random.uniform(-1,1)
        new_neighbour_point = np.array([x,y])
        

        goal_dist = (list_of_distances[i]/dim)*2
            
        start_dist = np.linalg.norm(new_focus_point-new_neighbour_point)
        
        new_x = new_neighbour_point[0]+(((new_focus_point[0]-new_neighbour_point[0])/start_dist)*((start_dist-goal_dist))) 
        new_y = new_neighbour_point[1]+(((new_focus_point[1]-new_neighbour_point[1])/start_dist)*((start_dist-goal_dist))) 
        new_neighbour_point = np.array([new_x,new_y])
        
        new_neighbour_points.append(new_neighbour_point)
    
        
    
    
    for k in range(2):    
        for i in range(1,len(list_of_points)):
            focus_neighbour_point = list_of_points[i]
            new_focus_neighbour_point = new_neighbour_points[i-1]
            
            for j in range(1,len(list_of_points)):
                if i == j:
                    continue
                else:
                    neighbour_point = list_of_points[j]
                    
                    goal_dist = (np.linalg.norm(focus_neighbour_point-neighbour_point)/dim)*2
                    start_dist = np.linalg.norm(new_focus_neighbour_point-new_neighbour_points[j-1])
                    
                    if start_dist != 0:
                        new_x = new_neighbour_points[j-1][0]+(((new_focus_neighbour_point[0]-new_neighbour_points[j-1][0])/start_dist)*((start_dist-goal_dist))) 
                        new_y = new_neighbour_points[j-1][1]+(((new_focus_neighbour_point[1]-new_neighbour_points[j-1][1])/start_dist)*((start_dist-goal_dist))) 
                        new_neighbour_points[j-1] = np.array([new_x,new_y])
                    else:
                        new_x = new_neighbour_points[j-1][0]+(((new_focus_neighbour_point[0]-new_neighbour_points[j-1][0]))*((start_dist-goal_dist))) 
                        new_y = new_neighbour_points[j-1][1]+(((new_focus_neighbour_point[1]-new_neighbour_points[j-1][1]))*((start_dist-goal_dist))) 
                        new_neighbour_points[j-1] = np.array([new_x,new_y])
                    
                    
        for i in range(1,len(list_of_points)):
            
            goal_dist = (list_of_distances[i]/dim)*2
                
            start_dist = np.linalg.norm(new_focus_point-new_neighbour_points[i-1])
            
            new_x = new_neighbour_points[i-1][0]+(((new_focus_point[0]-new_neighbour_points[i-1][0])/start_dist)*((start_dist-goal_dist))) 
            new_y = new_neighbour_points[i-1][1]+(((new_focus_point[1]-new_neighbour_points[i-1][1])/start_dist)*((start_dist-goal_dist))) 
            new_neighbour_points[i-1] = np.array([new_x,new_y])
            
        
    
    return [new_focus_point]+new_neighbour_points

#%% Create visualization dataframe

def get_visual_df(input_dict, database):
    distance_labels = ['concept_bow_meanvector',
                       'concept_vector',
                       'reverse_wmd_bow',
                       'reverse_wmd_concept_bow',
                       'weighted_reverse_wmd_bow',
                       'weighted_reverse_wmd_concept_bow',
                       'weighted_wmd_bow',
                       'weighted_wmd_concept_bow',
                       'wmd_bow',
                       'wmd_concept_bow']
    
    visual_dfs = dict()
    
    
    for label in distance_labels:
        lc_names = ['text']
        list_of_points = [input_dict['input_bow_meanvector']]
        list_of_distances = [0]
        for key in input_dict['input_min_dist'][label].keys():
            tup = input_dict['input_min_dist'][label][key]
            lc_names.append(tup[0].replace('§ ', '§\xa0'))
            list_of_points.append(database.legal_concepts[tup[0].replace('§ ', '§\xa0')]['concept_vector'])
            if type(tup[1]) == dict:
                list_of_distances.append(tup[1]['wmd'])
            else:
                list_of_distances.append(tup[1])
        
        xy_df = pd.DataFrame(two_d_distance_preserving_plotter(list_of_points, list_of_distances),
                             columns = ['X','Y'])
        label_df = pd.DataFrame()
        label_df['names'] = lc_names
        label_df['distances'] = list_of_distances
        label_df = pd.concat([label_df, xy_df], axis =1)
        
        visual_dfs[label] = label_df
    return visual_dfs

#%% Get t-SNE

def get_visu_df(input_dict, database):
    input_label = "Input"
    input_id = input_dict['id']
    input_text = input_dict['full_text']
    input_dist = 0.0
    cbowm_list = [[input_label, input_id, input_text, input_dist]]
    
    input_bow_mean = input_dict['input_bow_meanvector']
    cbowm_vector_list = [list(input_bow_mean)]

    for neighbour in input_dict['input_min_dist']['concept_bow_meanvector']:
        neighbour_label = f"{neighbour} to input"
        neighbour_id = input_dict['input_min_dist']['concept_bow_meanvector'][neighbour][0]
        neighbour_text = database.legal_concepts[neighbour_id]['raw_text']
        neighbour_dist = input_dict['input_min_dist']['concept_bow_meanvector'][neighbour][1]
        neighbour_list = [neighbour_label, neighbour_id, neighbour_text, neighbour_dist]    
        cbowm_list.append(neighbour_list)
        
    
    
        neighbour_vector = list(database.legal_concepts[neighbour_id]['concept_bow_meanvector'])
        cbowm_vector_list.append(neighbour_vector)
    
    if len(input_dict['sentence_dicts']) > 1:
        sentence_count = 0
        for sentence in input_dict['sentence_dicts']:
            sentence_bow_mean = sentence['input_bow_meanvector']
            cbowm_vector_list.append(sentence_bow_mean)
            
            sentence_count += 1
            sentence_label = f"sentence {sentence_count}"
            sentence_text = sentence['text']
            sentence_dist = np.linalg.norm(input_bow_mean-sentence_bow_mean)
            cbowm_list.append([sentence_label, '', sentence_text, sentence_dist])
            
            for neighbour in sentence['input_min_dist']['concept_bow_meanvector']:
                neighbour_label = f"{neighbour} to sentence {sentence_count}"
                neighbour_id = sentence['input_min_dist']['concept_bow_meanvector'][neighbour][0]
                neighbour_text = database.legal_concepts[neighbour_id]['raw_text']
                neighbour_dist = sentence['input_min_dist']['concept_bow_meanvector'][neighbour][1]
                neighbour_list = [neighbour_label, neighbour_id, neighbour_text, neighbour_dist]    
                cbowm_list.append(neighbour_list)
            
                neighbour_vector = list(database.legal_concepts[neighbour_id]['concept_bow_meanvector'])
                cbowm_vector_list.append(neighbour_vector)
    
    cbowm_vectors_array = np.array(cbowm_vector_list)
    
    #cbowm_vectors_embedded = TSNE(n_components=2).fit_transform(cbowm_vectors_array)
    cbowm_vectors_embedded = MDS(n_components=2).fit_transform(cbowm_vectors_array)
    
    cbowm_df = pd.DataFrame(np.array(cbowm_list), columns=['label', 'id', 'text', 'distance'])
    cbowm_df = pd.concat([cbowm_df, pd.DataFrame(cbowm_vectors_embedded, columns=['X','Y'])], axis=1)
    #cv_list = 
    
    
    
    #wmd_bow_list =
    #wmd_concept_bow_list = 
    
    return cbowm_df, cbowm_vectors_embedded

#%% Get input sentence dict
def get_input_sentence_dicts(text, text_id, database):
    start=datetime.now()
    dimmension = database.word_embeddings.vector_size
    
    nbrs_cbowm = NearestNeighbors(n_neighbors=10, algorithm='ball_tree').fit(database.concept_bow_meanvector_df.iloc[:,0:dimmension]) 
    nbrs_cv = NearestNeighbors(n_neighbors=10, algorithm='ball_tree').fit(database.concept_vector_df.iloc[:,0:dimmension])

      
    input_dict = dict()
    input_dict['id'] = text_id
    input_dict['full_text'] = text
    input_sentences = lc_text_cleaning.split_text_into_sentences(text)
    
    wordfreq = database.doc_wordfreq.loc[:,database.doc_wordfreq.columns != 'parent_doc'].notnull().sum()
    N = len(database.doc_wordfreq)

    
    input_dict['sentence_dicts'] = []
    for sentence in input_sentences:
        sentence_dict = lc_text_cleaning.get_sentence_bow_meanvector(sentence,
                                                                      database.stopwords,
                                                                      database.word_embeddings,
                                                                      wordfreq,
                                                                      N)
        sentence_dict = calculate_min_dist(sentence_dict, database, nbrs_cbowm, nbrs_cv)
        
        input_dict['sentence_dicts'].append(sentence_dict)
    
    input_dict = calculate_input_bow_meanvector(input_dict, database)
    
    # input_dict['cbowm_2d'] = database.pca_concept_bow_meanvector.transform(input_dict['input_bow_meanvector'].reshape(1,-1))
    # input_dict['cv_2d'] = database.pca_concept_vector.transform(input_dict['input_bow_meanvector'].reshape(1,-1))
    # input_dict['bm_2d'] = database.pca_bow_meanvector.transform(input_dict['input_bow_meanvector'].reshape(1,-1))
    
    input_dict = calculate_min_dist(input_dict, database, nbrs_cbowm, nbrs_cv)
    
    visual_dfs = get_visual_df(input_dict, database)
    
    print(datetime.now()-start)
    return visual_dfs, input_dict

#%% Open database

#open data
with open("databases/test_database.p", "rb") as pickle_file:
    test_database = pickle.load(pickle_file) 
    
example_lc = test_database.random_lc()

#%% Input text
test_input_list = ["En funktionær er en lønmodtager, som primært er ansat "
                   +"inden for handel- og kontorområdet. " 
                   +"Du kan også være funktionær, hvis du udfører "
                   +"lagerarbejde eller tekniske og kliniske ydelser.", #Funktionærloven -> https://www.frie.dk/find-svar/ansaettelsesvilkaar/funktionaerloven/#:~:text=En%20funktion%C3%A6r%20er%20en%20l%C3%B8nmodtager,arbejdstid%20er%20minimum%208%20timer.
                   
                   "Der er en lang række fleksible muligheder - specielt for de forældre, "
                   +"som gerne vil vende tilbage til arbejdet efter for eksempel seks eller "
                   +"otte måneders orlov og gemme resten af orloven, til barnet er blevet lidt ældre. "
                   +"Eller for de forældre, der ønsker at dele orloven eller starte på arbejde på "
                   +"nedsat tid og dermed forlænge orloven. Fleksibiliteten forudsætter i de "
                   +"fleste tilfælde, at der er indgået en aftale med arbejdsgiveren.", #Barselsloven -> https://bm.dk/arbejdsomraader/arbejdsvilkaar/barselsorlov/barselsorloven-hvor-meget-orlov-og-hvordan-kan-den-holdes/
                   
                   "Når du er tidsbegrænset ansat, gælder der et princip om, at du ikke "
                   +"må forskelsbehandles i forhold til virksomhedens fastansatte, "
                   +"medmindre forskelsbehandlingen er begrundet i objektive forhold. "
                   +"Du har altså de samme rettigheder som de fastansatte.", #Tidsbegrænset ansættelse -> https://sl.dk/faa-svar/ansaettelse/tidsbegraenset-ansaettelse
                   
                   "Person A er bogholder.",
                   "Bogholderen Anja venter sit første barn. Hendes termin nærmer sig med hastige skridt.",
                   "Jan's kone er gravid. Han glæder sig meget til at være hjemmegående og bruge tid med hans søn.",
                   "Den nye malersvend blev fyret efter en uge.",
                   "Den nye salgschef blev fyret efter en uge."
                   ]   

#%%
visual_dfs, input_dict = get_input_sentence_dicts(test_input_list[4], 1, test_database)

visual_dfs = get_visual_df(input_dict, test_database)

with open("databases/visual_dfs.p", "wb") as pickle_file:
    pickle.dump(visual_dfs, pickle_file) 

#%%
with open("databases/visual_dfs.p", "rb") as pickle_file:
    visual_dfs = pickle.load(pickle_file)

#%% plotly


app = Dash(__name__)

app.layout = html.Div([
    html.H4('Analysis of Iris data using scatter matrix'),
    dcc.Dropdown(
        id="dropdown",
        options=['concept_bow_meanvector',
                           'concept_vector',
                           'reverse_wmd_bow',
                           'reverse_wmd_concept_bow',
                           'weighted_reverse_wmd_bow',
                           'weighted_reverse_wmd_concept_bow',
                           'weighted_wmd_bow',
                           'weighted_wmd_concept_bow',
                           'wmd_bow',
                           'wmd_concept_bow'],
        value='concept_bow_meanvector',
        multi=False
    ),
    dcc.Graph(id="graph"),
])


@app.callback(
    Output("graph", "figure"), 
    Input("dropdown", "value"))
def update_bar_chart(option):
    
    output_df = visual_dfs[option]
    
    fig = px.scatter(output_df, x="X", y="Y", hover_name="names", hover_data=['names','distances'])
    return fig


app.run_server(debug=False)





#%% latex export
if __name__ == "__main__":
    
    wmd_bow_1_td_pairs_df = pd.DataFrame(sorted(input_dict['input_min_dist']['wmd_bow']['1. closest'][1]['travel_distance_pairs'], key=lambda tup: tup[2]),
                                         columns=['Input word','Legal concept word','Distance'])

    print(wmd_bow_1_td_pairs_df.to_latex(index=False,
                                         caption=('Travel distance pairs of the 1. closets legal concept BOW for the WMD.'),
                                         label='wmd_bow_1_td_pais',
                                         float_format="%.4f"))   

    wmd_bow_df = pd.DataFrame(input_dict['input_min_dist']['wmd_bow'])#,
                                         #columns=['Legal conept','Word Mover Distance'])

    print(wmd_bow_1_td_pairs_df.to_latex(index=True,
                                         caption=('Top 3 closest according to WMD on the BOW'),
                                         label='wmd_bow',
                                         float_format="%.4f"))   
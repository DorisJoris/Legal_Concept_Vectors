# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 18:07:25 2022

@author: bejob
"""
#%% import
import pickle
import numpy as np
import pandas as pd

from dash import Dash, dcc, html, Input, Output
import plotly.express as px

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
    
    bow_types = [('wmd_concept_bow','concept_bow'),('wmd_bow', 'bow')]
    
    max_level = database.concept_bow_meanvector_df['level'].max()
    
    
    search_vector = input_dict['input_bow_meanvector']
    
    cbowm_distances, cbowm_neighbours = nbrs_cbowm.kneighbors(search_vector.reshape(1,-1))
    cv_distances, cv_neighbours = nbrs_cv.kneighbors(search_vector.reshape(1,-1))
    
    input_dict['input_min_dist'] = {
        'concept_vector':{
            '1. closest': (database.concept_vector_df.iloc[cv_neighbours[0][0]].name,cv_distances[0][0]),
            '2. closest': (database.concept_vector_df.iloc[cv_neighbours[0][1]].name,cv_distances[0][1]),
            '3. closest': (database.concept_vector_df.iloc[cv_neighbours[0][2]].name,cv_distances[0][2]),
            '4. closest': (database.concept_vector_df.iloc[cv_neighbours[0][3]].name,cv_distances[0][3]),
            '5. closest': (database.concept_vector_df.iloc[cv_neighbours[0][4]].name,cv_distances[0][4])
            },
        'concept_bow_meanvector':{
            '1. closest': (database.concept_bow_meanvector_df.iloc[cbowm_neighbours[0][0]].name,cbowm_distances[0][0]),
            '2. closest': (database.concept_bow_meanvector_df.iloc[cbowm_neighbours[0][1]].name,cbowm_distances[0][1]),
            '3. closest': (database.concept_bow_meanvector_df.iloc[cbowm_neighbours[0][2]].name,cbowm_distances[0][2]),
            '4. closest': (database.concept_bow_meanvector_df.iloc[cbowm_neighbours[0][3]].name,cbowm_distances[0][3]),
            '5. closest': (database.concept_bow_meanvector_df.iloc[cbowm_neighbours[0][4]].name,cbowm_distances[0][4])
            },
        'wmd_concept_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            },
        'wmd_bow':{
            '1. closest': ('',{'wmd':1000.00}),
            '2. closest': ('',{'wmd':1000.00}),
            '3. closest': ('',{'wmd':1000.00})
            }
        }
    
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
                                                     database.word_embeddings)
                    
                    if wmd_dict['wmd'] < input_dict['input_min_dist'][bow_type[0]]['1. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[0]]['3. closest'] = input_dict['input_min_dist'][bow_type[0]]['2. closest']
                        input_dict['input_min_dist'][bow_type[0]]['2. closest'] = input_dict['input_min_dist'][bow_type[0]]['1. closest']
                        input_dict['input_min_dist'][bow_type[0]]['1. closest'] = (
                            str(key),
                            wmd_dict
                            )
                        changed = True
                        
                    elif wmd_dict['wmd'] <  input_dict['input_min_dist'][bow_type[0]]['2. closest'][1]['wmd']:  
                        input_dict['input_min_dist'][bow_type[0]]['3. closest'] = input_dict['input_min_dist'][bow_type[0]]['2. closest']
                        input_dict['input_min_dist'][bow_type[0]]['2. closest'] = (
                            str(key),
                            wmd_dict
                            )
                        changed = True
                        
                    elif wmd_dict['wmd'] <  input_dict['input_min_dist'][bow_type[0]]['3. closest'][1]['wmd']:
                        input_dict['input_min_dist'][bow_type[0]]['3. closest'] =  (
                            str(key),
                            wmd_dict
                            )
                        changed = True
                except:
                    pass
                
            if changed == False:
                break
            
    return input_dict

#%% Create visualization dataframe

def cbowm_visual_df(input_dict, database):
    cbowm_df = database.concept_bow_meanvector_df.loc[:,'X':'Y']

    cbowm_df['name'] = cbowm_df.index
    
    cbowm_df['color'] = 'others'  
    cbowm_df['size'] = 1
    
    text_df = pd.DataFrame(input_dict['cbowm_2d'], 
                          index=['text'],
                          columns=['X','Y'])
    
    text_df['name'] = 'text'
    text_df['color'] = 'text'
    text_df['size'] = 3
    
    output_df = pd.DataFrame(text_df)
    
    
    neighbours = input_dict['input_min_dist']['concept_bow_meanvector']
    for key in neighbours:
        index = neighbours[key][0]
        cbowm_df.loc[index,'color'] = key
        cbowm_df.loc[index,'size'] = 3
    
    output_df = pd.concat([output_df,cbowm_df],axis=0)
    
    return output_df

#%% Get input sentence dict
def get_input_sentence_dicts(text, text_id, database):
    start=datetime.now()
    dimmension = database.word_embeddings.vector_size
    
    nbrs_cbowm = NearestNeighbors(n_neighbors=5, algorithm='ball_tree').fit(database.concept_bow_meanvector_df.iloc[:,0:dimmension]) 
    nbrs_cv = NearestNeighbors(n_neighbors=5, algorithm='ball_tree').fit(database.concept_vector_df.iloc[:,0:dimmension])
    
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
    
    input_dict['cbowm_2d'] = database.pca_concept_bow_meanvector.transform(input_dict['input_bow_meanvector'].reshape(1,-1))
    input_dict['cv_2d'] = database.pca_concept_vector.transform(input_dict['input_bow_meanvector'].reshape(1,-1))
    
    input_dict = calculate_min_dist(input_dict, database, nbrs_cbowm, nbrs_cv)
    print(datetime.now()-start)
    
    
    cbowm_output_df = cbowm_visual_df(input_dict, database)
    return cbowm_output_df

#%% Open database

#open data
with open("databases/test_database.p", "rb") as pickle_file:
    test_database = pickle.load(pickle_file) 

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
 
#%% plotly


app = Dash(__name__)

app.layout = html.Div([
    html.H4('Analysis of Iris data using scatter matrix'),
    dcc.Dropdown(
        id="dropdown",
        options=test_input_list,
        value=test_input_list[0],
        multi=False
    ),
    dcc.Graph(id="graph"),
])


@app.callback(
    Output("graph", "figure"), 
    Input("dropdown", "value"))
def update_bar_chart(text):
    text_id = 1
    cbowm_output_df = get_input_sentence_dicts(text, text_id, test_database)
    
    fig = px.scatter(cbowm_output_df, x="X", y="Y", color = "color", size = "size", hover_name="name", log_x=True)
    return fig


app.run_server(debug=False)


#%%     
if __name__ == "__main__":
    
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
    
    
    test_input_dict = get_input_sentence_dicts(test_input_list[3], 'text_1', test_database)
    
    n = 0
    for text in test_input_list:
        text_id = f"text_{n}"
        test_database.get_input_sentence_dicts(text, text_id)
        n += 1
    test_min_dist = test_database.input_list


   
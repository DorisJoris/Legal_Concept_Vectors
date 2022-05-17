# -*- coding: utf-8 -*-
"""
Created on Sat May 14 13:10:44 2022

@author: bejob
"""
#%% import
import pickle
import numpy as np
import pandas as pd
import random
import re
import json

from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px





#%% Open pickled input visual_dfs

with open("visualization_data/input_visual_dfs.p", "rb") as pickle_file:
    input_visual_dfs = pickle.load(pickle_file) 
    
with open("visualization_data/word_idf.p", "rb") as pickle_file:
    word_idf = pickle.load(pickle_file) 

with open("visualization_data/stopwords_list.p", "rb") as pickle_file:
    stopwords_list = pickle.load(pickle_file)     

#%% plotly
external_stylesheets = [dbc.themes.MINTY]
app = Dash(__name__, external_stylesheets=external_stylesheets)

tab_graph = dbc.Card(dbc.CardBody([
    dcc.Graph(id="graph"),
    html.P(['Selected point:']),
    html.P(id='text-print', style= {"width": "90%",
                                    "height": "150px",
                                    "padding": "2px",
                                    "margin-left":"5%",
                                    "margin-right":"5%",
                                    "border": "1px solid grey",
                                    "border-radius": "5px",
                                    "overflow-wrap": "break-word",
                                    "overflow": "scroll"
                                    })
    ]))

tab_table = dbc.Card(dbc.CardBody([
    html.Div(id='table')
    ]))

tab_latex = dbc.Card(dbc.CardBody([
    dbc.Row([
        dbc.Col(dbc.Label('Include columns:'),width=2),
        dbc.Col(dcc.Dropdown(id='latex_dropdown',multi=True))
        ]),
    dbc.Card(html.Div(id='latex'))
    ]))

app.layout = dbc.Container([
    html.H1('Legal concept experiments'),
    dbc.Row([
        dbc.Col(dbc.Label('Select input:'),width=2),
        dbc.Col(dcc.Dropdown(
            id="input_select",
            options=list(input_visual_dfs.keys()),
            value=list(input_visual_dfs.keys())[0],
            multi=False
        )),
    ]),
    dbc.Row([
        dbc.Col(dbc.Label('Select distance measure:'),width=2),
        dbc.Col(dcc.Dropdown(
            id="distance_type",
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
        )),
    ]),
    dbc.Row([
        dbc.Col(dbc.Label('Select neighbour type:'),width=2),
        dbc.Col(dcc.Dropdown(id='neighbour_dropdown',multi=True))
    ]),
    dbc.Row([
        dbc.Col(dbc.Label('Select point type:'),width=2),
        dbc.Col(dcc.Dropdown(id='document_dropdown',multi=True))
    ]),
    dbc.Tabs(
        [dbc.Tab(tab_graph, label='Graph'),
         dbc.Tab(tab_table, label='Table'),
         dbc.Tab(tab_latex, label='Latex table code')
            ]
        )
    
])

@app.callback(
    Output('neighbour_dropdown','options'),
    Output('neighbour_dropdown','value'),
    Output('document_dropdown','options'),
    Output('document_dropdown','value'),
    Input("input_select", "value"),
    Input("distance_type", "value"))
def init_multi_dropdowns(input_option, dist_option):
    neighbour_values = input_visual_dfs[input_option][0][dist_option]['Neighbour type'].unique()
    doc_values = input_visual_dfs[input_option][0][dist_option]['Point type'].unique()
    
    return neighbour_values, neighbour_values, doc_values, doc_values

@app.callback(
    Output("table", "children"),
    Input("input_select", "value"),
    Input("distance_type", "value"),
    Input('graph', 'clickData'),
    Input('neighbour_dropdown','value'),
    Input('document_dropdown','value'))
def update_table(input_option, dist_option, clickData, neighbour_options, doc_options):
    
    output_df = input_visual_dfs[input_option][0][dist_option]
    output_df = output_df[output_df['Neighbour type'].isin(neighbour_options)]
    output_df = output_df[output_df['Point type'].isin(doc_options)]

    
    table_df = output_df[['Name','Neighbour type','Point type','Distance to input']]
    
    if clickData == None:
        return dash_table.DataTable(table_df.to_dict('records'), 
                                  [{"name": i, "id": i} for i in table_df.columns],
                                  style_cell={'textAlign': 'left'},
                                  sort_action="native",
                                  sort_mode="multi"
                                      ) 
    else:
        filter_query = '{Name} = "' +clickData['points'][0]['text'] +'"'
        print(filter_query)
        return dash_table.DataTable(table_df.to_dict('records'), 
                                  [{"name": i, "id": i} for i in table_df.columns],
                                  style_cell={'textAlign': 'left'},
                                  sort_action="native",
                                  sort_mode="multi",
                                  style_data_conditional=[{
                                      'if': {
                                          'filter_query': filter_query,
                                          'column_id': 'Name'
                                      },
                                      'backgroundColor': 'tomato',
                                      'color': 'white'
                                  },
                                      {
                                      'if': {
                                          'filter_query': filter_query,
                                          'column_id': 'Neighbour type'
                                      },
                                      'backgroundColor': 'tomato',
                                      'color': 'white'
                                  },
                                      {
                                      'if': {
                                          'filter_query': filter_query,
                                          'column_id': 'Point type'
                                      },
                                      'backgroundColor': 'tomato',
                                      'color': 'white'
                                  },
                                      {
                                      'if': {
                                          'filter_query': filter_query,
                                          'column_id': 'Distance to input'
                                      },
                                      'backgroundColor': 'tomato',
                                      'color': 'white'
                                  }
                              ]
                                      ) 




@app.callback(
    Output("graph", "figure"),
    Input("input_select", "value"),
    Input("distance_type", "value"),
    Input('neighbour_dropdown','value'),
    Input('document_dropdown','value'))
def update_bar_chart(input_option, dist_option, neighbour_options, doc_options):
    
    output_df = input_visual_dfs[input_option][0][dist_option]
    output_df = output_df[output_df['Neighbour type'].isin(neighbour_options)]
    output_df = output_df[output_df['Point type'].isin(doc_options)]
    
    fig = px.scatter(output_df, 
                     x="X", y="Y", 
                     text="Name", 
                     hover_data=['Name','Distance to input'], 
                     color= 'Neighbour type',
                     color_discrete_sequence=px.colors.qualitative.Dark24,
                     symbol = 'Point type'
                     )
    fig.update_traces(textposition='top center')
    fig.update_layout(legend={'title_text':''})
    fig.update_layout(yaxis_visible=False, yaxis_showticklabels=False,
                      xaxis_visible=False, xaxis_showticklabels=False)
    fig.update_layout({
                    'plot_bgcolor': 'rgba(0, 0, 0, 0.1)',
                    'legend_bgcolor': 'rgba(0, 0, 0, 0.1)',
                    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
                        })
    
    
   
    return fig

@app.callback(
    Output("graph", "clickData"),
    Input("input_select", "value"))
def rest_clickdata(input_option):
    return None


@app.callback(
    Output('text-print', 'children'),
    Input('graph', 'clickData'),
    Input("input_select", "value"),
    Input("distance_type", "value"))
def display_click_data(clickData,input_option, dist_option):
    
    output_df = input_visual_dfs[input_option][0][dist_option]
    
    if clickData == None:
        search_name = "Name: " + output_df.loc[0,'Name']
        search_type = "Neighbour type: " + output_df.loc[0,'Neighbour type']
        
        text = output_df.loc[0,'Text']
        new_text_list = list()
        
        word_list = text.split()
        idf_list = list()
        for word in word_list:
            if re.sub('[^a-zæøå]+', '', word.lower()) in word_idf:
                idf_list.append(word_idf[re.sub('[^a-zæøå]+', '', word.lower())]) 
        
        if len(idf_list) > 1:
            max_idf = max(idf_list)
        else:
            max_idf = word_idf.max()
        
        for word in word_list:
            clean_word = re.sub('[^a-zæøå]+', '', word.lower())
            if clean_word in stopwords_list:
                new_text_list.append(html.Span(word+' ', style = {'color':'black', 'text-decoration': ' line-through'}))        
            elif clean_word in word_idf:
                red = 255*(word_idf[clean_word]/max_idf)
                alpha = (word_idf[clean_word]/max_idf)
                rgba = f"rgba({red},0,0,{alpha})"
                new_text_list.append(html.Span(word+' ', style = {'color':rgba}))
            else:
                new_text_list.append(html.Span(word+' ', style = {'color':'black'}))
                
        output_text = [search_name,  html.Br(), search_type,  html.Br()] + new_text_list
    else:
        search_name = clickData['points'][0]['text']
        search_type = list(output_df.loc[output_df.index[output_df['Name'] == search_name], 'Neighbour type'])[0]
        text = list(output_df.loc[output_df['Name'] == search_name, 'Text'])[0]
        
        new_text_list = list()
        
        word_list = text.split()
        idf_list = list()
        for word in word_list:
            if re.sub('[^a-zæøå]+', '', word.lower()) in word_idf:
                idf_list.append(word_idf[re.sub('[^a-zæøå]+', '', word.lower())])
                
        if len(idf_list) > 1:
            max_idf = max(idf_list)
        else:
            max_idf = word_idf.max()
            
        for word in word_list:
            clean_word = re.sub('[^a-zæøå]+', '', word.lower())
            if clean_word in stopwords_list:
                new_text_list.append(html.Span(word+' ', style = {'color':'black', 'text-decoration': ' line-through'}))        
            elif clean_word in word_idf:
                red = 255*(word_idf[clean_word]/max_idf)
                alpha = (word_idf[clean_word]/max_idf)
                rgba = f"rgba({red},0,0,{alpha})"
                new_text_list.append(html.Span(word+' ', style = {'color':rgba}))
            else:
                new_text_list.append(html.Span(word+' ', style = {'color':'black'}))
        
        
        output_text = ["Name: " + search_name,  html.Br(),"Neighbour type: " + search_type,  html.Br()] + new_text_list
        
       
    return output_text

@app.callback(
    Output('latex_dropdown','options'),
    Output('latex_dropdown','value'),
    Input("input_select", "value"),
    Input("distance_type", "value"))

def init_latex_dropdown(input_option, dist_option):
    
    columns = list(input_visual_dfs[input_option][0][dist_option].columns)

    return columns, columns    

@app.callback(
    Output('latex', 'children'),
    Input("input_select", "value"),
    Input("distance_type", "value"),
    Input('neighbour_dropdown','value'),
    Input('document_dropdown','value'),
    Input('latex_dropdown','value'))
def display_latex_code(input_option, dist_option, neighbour_options, doc_options, columns):
    
    output_df = input_visual_dfs[input_option][0][dist_option]
    output_df = output_df[output_df['Neighbour type'].isin(neighbour_options)]
    output_df = output_df[output_df['Point type'].isin(doc_options)]
    
    output_df = output_df[[c for c in output_df.columns if c in columns]]
    
    latex_code = output_df.to_latex(index=False,
                                    caption=(f'{input_option} + {dist_option}'),
                                    label='tab:add label',
                                    float_format="%.4f")
    
    latex_list = list()
    for line in latex_code.split("\n"):
        latex_list.append(line)
        latex_list.append(html.Br())
    return latex_list

    
app.run_server(debug=False)

# -*- coding: utf-8 -*-
"""
Created on Wed Feb  9 19:36:17 2022

@author: bejob
"""
# Initial comment:
# The purpose of this code is to extract and segment the text of a danish law into its subparts,  
# such as paragraphs, stk (sections of a paragraph) and so on and organize these in a neo4j database. 
# The code has been writen for Funktionærloven, LBK nr 1002 af 24/08/2017, and will need to be
# modified to be used on other sources of law. 
    
#%% Import
import urllib.request
import json
import copy
import re
import numpy as np


from retsgraph import create_node
from retsgraph import create_relation

from legal_concept_resources import abbreviations
from legal_concept_resources import lov_label_list
from legal_concept_resources import chapter_label_list
from legal_concept_resources import paragraph_label_list
from legal_concept_resources import stk_label_list
from legal_concept_resources import litra_label_list
from legal_concept_resources import nr_label_list
from legal_concept_resources import sentence_label_list
from legal_concept_resources import relative_stk_ref_cues
from legal_concept_resources import internal_ref_to_whole_law_cues
from legal_concept_resources import external_reference_cues

from bs4 import BeautifulSoup as bs


#%% Create lov node
# This function takes the url, in this case: 
    # https://www.retsinformation.dk/api/document/eli/lta/2017/1002
# to request a json-file containing some meta information about the law
# and the text of the law in a html-format.
# The funktion continues to generate a dictionary of the properties for the law that will
# be saved to the database. 

def law_property_gen(url):
    with urllib.request.urlopen(url) as page:
        data = json.loads(page.read().decode())

    lov_json = data[0]
    lov_html_end = lov_json['documentHtml'].find('<hr class="IKraftStreg">')
    lov_html = lov_json['documentHtml'][0:lov_html_end]
    lov_soup = bs(lov_html, 'html.parser')
    
    try:
        lov_name = lov_json["popularTitle"]
    except:
        lov_name = lov_json["title"]
    
    lov_property_dict = {"name":lov_name,
                        "shortName":lov_json["shortName"],
                        "title":lov_json["title"],
                        "date_of_publication":lov_json["metadata"][0]["displayValue"],
                        "ressort": lov_json["ressort"],
                        "id": lov_json["id"],
                        'html':lov_html,
                        'raw_text':lov_soup.text}
    
    lov_name = lov_property_dict['name']
    lov_shortname = lov_property_dict['shortName']
    return lov_soup, lov_property_dict, lov_name, lov_shortname

#%% Extract paragraph content -> generate paragraphs_raw_list
# This funktion takes a BeautifulSoup of the law-html and extract the included paragraphs.
# The html of this law is organized as a list of <p>-tags one for every subpart of the law.
# The beginning of a paragraph is indicated by a <p>-tag of the class: 'Paragraf'.
# Every following <p>-tag is then assumed to be a part of the same paragraph until a new <p>-tag
# of the class: 'Paragraf' is found.
# The paragraphs are organized into lists of <p>-tags, one for every paragraph.
# Only the main part of the law-text is taken into account. 
# The <p>-tag with the class: 'IkraftTeskt' is assumed to indicate the end of the main part.


    

def _paragraph_sorting_raw(lov_soup):
    pees = lov_soup.select('p')
    p_nr = 0
    paragraphs_raw_dict_list = []
    ch_nr = 0
    ch_name = ''
    for p in pees:
        if p['class'][0] == 'IkraftTekst':
            break
        if p['class'][0] == 'Kapitel':
            ch_nr += 1
            continue
        if p['class'][0] == 'KapitelOverskrift2':
            ch_name = p.text
            continue
        if p['class'][0] == 'Paragraf':
            p_nr += 1
            paragraphs_raw_dict_list.append({'paragraph_content':[],
                                             'paragraph_id': p_nr,
                                             'chapter_nr': ch_nr,
                                             'chapter_name': ch_name})
        if p_nr > 0:
            paragraphs_raw_dict_list[p_nr-1]['paragraph_content'].append(p)
    return paragraphs_raw_dict_list


def paragraph_property_gen(lov_soup, lov_shortname):
    paragraphs_raw_dict_list = _paragraph_sorting_raw(lov_soup)
    paragraph_property_list = []
    chapter_property_list = []
    p_nr = 0
    ch_nr = 0
    for p_dict in paragraphs_raw_dict_list:
        p = p_dict['paragraph_content']
        p_nr +=1
        name = p[0].find_all(attrs={"class": "ParagrafNr"})[0].string.replace('§ ', '§\xa0')
        if p_dict['chapter_nr']>0:
            parents = [f"Kapitel {p_dict['chapter_nr']}", lov_shortname]
            if ch_nr != p_dict['chapter_nr']:
                ch_nr = p_dict['chapter_nr']
                chapter_property_dict = {'name': f"Kapitel {p_dict['chapter_nr']}",
                                         'shortName': p_dict['chapter_name'],
                                         'position': p_dict['chapter_nr'],
                                         'parent': [lov_shortname]
                                         }
                chapter_property_list.append(chapter_property_dict)
        else:
            parents = [lov_shortname]
        
        paragraph_html = []
        paragraph_raw_text = ''
        for tag in p:
            paragraph_html.append(tag)
            paragraph_raw_text += tag.text
        
        if len(name) == 2:
            bold_tag_str = p[0].find_all(attrs={"class": "Bold"})[0].string
            if '(Udelades)' in paragraph_raw_text and '-' in bold_tag_str:
                p_start = ''
                p_end = ''
                is_start = True
                for l in bold_tag_str:
                    if l.isnumeric() and is_start == True:
                        p_start = p_start + l
                    elif l == '-':
                        is_start = False
                    elif l.isnumeric() and is_start == False:
                        p_end = p_end + l
                    else:
                        continue
                
                for i in range(int(p_start),int(p_end)+1):
                    name = f'§\xa0{i}.'
                    p_property_dict = {'name': name, 
                                       'position':p_nr,
                                       'html':paragraph_html,
                                       'raw_text':paragraph_raw_text,
                                       'parent': parents
                                       }
                    paragraph_property_list.append(p_property_dict)
                    p_nr += 1
        else: 
            p_property_dict = {'name': name, 
                               'position':p_nr,
                               'html':paragraph_html,
                               'raw_text':paragraph_raw_text,
                               'parent': parents
                               }
            
            paragraph_property_list.append(p_property_dict)
    return (paragraph_property_list, chapter_property_list)

def create_chapter_node(chapter_property_list):
    for chapter_property_dict in chapter_property_list:
        create_node(chapter_label_list, chapter_property_dict)
        
        node1_search_query = f"name: '{chapter_property_dict['name']}', parent: {chapter_property_dict['parent']}"
        node2_search_query = f"name: '{lov_name}', shortName: '{lov_property_dict['shortName']}'"
        create_relation(chapter_label_list[1],node1_search_query,
                        lov_label_list[1],node2_search_query,'part_of')


def create_paragraph_node(paragraph_property_list):
    for paragraph_property_dict in paragraph_property_list:
        html = ''
        for tag in paragraph_property_dict['html']:
            html = html + str(tag)
        
        paragraph_property_dict['html'] = html    
        create_node(paragraph_label_list, paragraph_property_dict)
        
        node1_search_query = f"name: '{paragraph_property_dict['name']}', parent: {paragraph_property_dict['parent']}"
        if len(paragraph_property_dict['parent']) == 1:
            node2_search_query = f"name: '{lov_name}', shortName: '{lov_property_dict['shortName']}'"
        if len(paragraph_property_dict['parent']) == 2:
            node2_search_query = f"name: '{paragraph_property_dict['parent'][0]}', parent: {paragraph_property_dict['parent'][1:]}"
        create_relation(paragraph_label_list[1],node1_search_query,
                        lov_label_list[0],node2_search_query,'part_of')

#%% Extract stk content -> generate paragraph_stk_raw_list
def _stk_sorting_raw(paragraph_property_list):
    paragraph_stk_raw_dict_list = []
    for p_dict in paragraph_property_list:
        p_content = p_dict['html']
        stk_parent = [p_dict['name']] + p_dict['parent']
        stk_nr = 0
        stk_in_paragraph_list = []
        for tag in p_content:
            if tag['class'][0] == 'Paragraf' or tag['class'][0] =='Stk2':
                stk_nr += 1
                stk_in_paragraph_list.append({'stk_content':[],
                                              'stk_nr': stk_nr,
                                              'parent': stk_parent})
            if stk_nr > 0:
                stk_in_paragraph_list[stk_nr-1]['stk_content'].append(tag)
        paragraph_stk_raw_dict_list.append(stk_in_paragraph_list)
    
    return paragraph_stk_raw_dict_list

def stk_property_gen(paragraph_property_list):
    paragraph_stk_raw_dict_list = _stk_sorting_raw(paragraph_property_list)
    stk_property_list = []
    for p in paragraph_stk_raw_dict_list:
        parents = p[0]['parent']
        
        for stk in p:
            stk_nr = stk['stk_nr']
            name = f'Stk. {stk_nr}.'
            stk_html = stk['stk_content']
            stk_raw_text = ''
            for tag in stk['stk_content']:
                stk_raw_text += tag.text
            
            stk_property_dict = {'name': name, 
                                 'position':stk_nr,
                                 'html':stk_html,
                                 'raw_text':stk_raw_text,
                                 'parent': parents
                                 }
            stk_property_list.append(stk_property_dict)
    return stk_property_list

    
def create_stk_node(stk_property_list):
    for stk_property_dict in stk_property_list:
        html = ''
        for tag in stk_property_dict['html']:
            html = html + str(tag)
        stk_property_dict['html'] = html   
        create_node(stk_label_list, stk_property_dict)
        
        node1_search_query = f"name: '{stk_property_dict['name']}', parent: {stk_property_dict['parent']}"
        node2_search_query = f"name: '{stk_property_dict['parent'][0]}', parent: {stk_property_dict['parent'][1:]}"
        create_relation(stk_label_list[1],node1_search_query,
            paragraph_label_list[1],node2_search_query,
                        'part_of')
        
#%% Litra, Nr and sentence nodes        
        
def _sentence_property_gen(tag, parents, tag_position):
    local_tag = copy.copy(tag)
    
    for span in local_tag.select('span'):
        span.extract()
    
    tag_raw_text = " " + local_tag.text
    
    # "."-exceptions
    exceptions_list = abbreviations
    
    month_list = ["januar", "februar", "marts", "april", "maj", "juni",
             "juli", "august", "september", "oktober", "november", "december"]
    
    for i in range(0,10):
        for month in month_list:
            date = f"{i}. {month}"
            replacement = f"{i}%% {month}"
            tag_raw_text = tag_raw_text.replace(date,replacement)
    
    for exception in exceptions_list:
        tag_raw_text = tag_raw_text.replace(exception[0],exception[1])
       
    pkt_instances = []
    pkt_instances = pkt_instances + re.findall("[0-9]\. pkt", tag_raw_text)
    pkt_instances = pkt_instances + re.findall("[0-9]\. og [0-9]", tag_raw_text)
    pkt_instances = pkt_instances + re.findall("[0-9]\., [0-9]", tag_raw_text)
    
    number_instances = re.findall("[0-9]\. ", tag_raw_text)
    pkt_instances = pkt_instances + number_instances
    
    pkt_replacements = []
    for instance in pkt_instances:
        pkt_replacements.append(instance.replace('.','%%'))
    
    for i in range(0,len(pkt_replacements)):
        tag_raw_text = tag_raw_text.replace(pkt_instances[i],pkt_replacements[i])
        
    sentence_end = re.findall("%% [A-Z]", tag_raw_text) + re.findall("%% §", tag_raw_text)
    sentence_end_dot = [x.replace("%%",".") for x in sentence_end] 
    
    for i in range(0,len(sentence_end)):
        tag_raw_text = tag_raw_text.replace(sentence_end[i], sentence_end_dot[i])
    
    tag_raw_text = tag_raw_text.replace('jf.','jf%%')
    
    # reversing "."-exceptions after split
    sentence_property_list = []
    sentence_count = 0
    while tag_raw_text.find('.') > 0:
        sentence_text = tag_raw_text[0:tag_raw_text.find('.')+1]
        for exception in exceptions_list:
            sentence_text = sentence_text.replace(exception[1],exception[0])
        
        for i in range(0,10):
            for month in month_list:
                date = f"{i}%% {month}"
                replacement = f"{i}. {month}"
                sentence_text = sentence_text.replace(date,replacement)
        
        for i in range(0,len(pkt_replacements)):
            sentence_text = sentence_text.replace(pkt_replacements[i],pkt_instances[i])
        
        tag_raw_text = tag_raw_text[tag_raw_text.find('.')+1:len(tag_raw_text)]
        sentence_count += 1
        sentence_property_dict = {'name': f'{sentence_count}. pkt.', 
                                 'position':tag_position+sentence_count,
                                 'html': '',
                                 'raw_text': sentence_text.replace(' \n','').replace('\n',''),
                                 'parent': parents
                                 }
        
        
        sentence_property_list.append(sentence_property_dict)
        
    if tag_raw_text.find('.') == -1 and len(tag_raw_text)>0:
        sentence_text = tag_raw_text
        for exception in exceptions_list:
            sentence_text = sentence_text.replace(exception[1],exception[0])
        
        for i in range(0,10):
            for month in month_list:
                date = f"{i}%% {month}"
                replacement = f"{i}. {month}"
                sentence_text = sentence_text.replace(date,replacement)
        
        for i in range(0,len(pkt_replacements)):
            sentence_text = sentence_text.replace(pkt_replacements[i],pkt_instances[i])
        
        sentence_count += 1
        sentence_property_dict = {'name': f'{sentence_count}. pkt.', 
                                 'position':tag_position+sentence_count,
                                 'html': '',
                                 'raw_text': sentence_text.replace(' \n','').replace('\n',''),
                                 'parent': parents
                                 }
        
        sentence_property_list.append(sentence_property_dict)
    return sentence_property_list


def _litra_nr_property_gen(tag, parents, tag_position):
    tag_html = str(tag)
    tag_raw_text = tag.text
    name = tag.find('span', attrs={'class': 'Liste1Nr'}).text
    tag_property_dict = {'name': name, 
                         'position':tag_position+1,
                         'html':tag_html,
                         'raw_text':tag_raw_text,
                         'parent': parents
                         }
    return tag_property_dict

def sentence_litra_nr_property_gen(stk_property_list):
    litra_property_list = []
    nr_property_list = []
    sentence_property_list = []
    
    for stk in stk_property_list:
        parents = [stk['name']] + stk['parent']
        
        stk_content = stk['html']
        tag_position = 0
            
        for tag in stk_content:
            if tag['class'][0] == 'Liste1':
                tag_property_dict = _litra_nr_property_gen(tag, 
                                                           parents, 
                                                           tag_position)
                tag_position += 1
                if tag_property_dict['name'][0:-1].isnumeric():
                    nr_property_list.append(tag_property_dict)
                else:
                    litra_property_list.append(tag_property_dict)
                    
                parent_list = [tag_property_dict['name']] + parents    
                new_sentence_property_list = _sentence_property_gen(tag, parent_list, 0)
                sentence_property_list = sentence_property_list + new_sentence_property_list
                
            else:
                
                new_sentence_property_list = _sentence_property_gen(tag,
                                                                    parents, 
                                                                    tag_position)
                sentence_property_list = sentence_property_list + new_sentence_property_list
                tag_position += len(new_sentence_property_list)

    return (litra_property_list,
            nr_property_list,
            sentence_property_list)
    

def create_litra_node(litra_property_list):
    for litra_property_dict in litra_property_list:
        create_node(litra_label_list, litra_property_dict)
        
        node1_search_query = f"name: '{litra_property_dict['name']}', parent: {litra_property_dict['parent']}"
        node2_search_query = f"name: '{litra_property_dict['parent'][0]}', parent: {litra_property_dict['parent'][1:]}"
        create_relation(litra_label_list[2],node1_search_query,
            stk_label_list[1],node2_search_query,
                        'part_of')

def create_nr_node(nr_property_list):
    for nr_property_dict in nr_property_list:
        create_node(nr_label_list, nr_property_dict)
        
        node1_search_query = f"name: '{nr_property_dict['name']}', parent: {nr_property_dict['parent']}"
        node2_search_query = f"name: '{nr_property_dict['parent'][0]}', parent: {nr_property_dict['parent'][1:]}"
        create_relation(nr_label_list[2],node1_search_query,
            stk_label_list[1],node2_search_query,
                        'part_of')
        
def create_sentence_node(sentence_property_list):
    for sentence_property_dict in sentence_property_list:
        create_node(sentence_label_list, sentence_property_dict)
        
        node1_search_query = f"name: '{sentence_property_dict['name']}', parent: {sentence_property_dict['parent']}"
        node2_search_query = f"name: '{sentence_property_dict['parent'][0]}', parent: {sentence_property_dict['parent'][1:]}"
        
        create_relation(sentence_label_list[1],node1_search_query,
            stk_label_list[0],node2_search_query,
                        'part_of')        

#%% Stk internal reference
def _get_sentence_pkt_ref_numbers(text):
    sentence_pkt_ref_numbers = []
    while text.find('. pkt.') != -1:
        p1 = re.search('[0-9]\., [0-9]\. og [0-9]\. pkt\.', text)
        p2 = re.search('[0-9]\. og [0-9]\. pkt\.', text)
        p3 = re.search('[0-9]\. pkt\.', text)
        if p1 != None:
           p_start = p1.start()
           p_end = p1.end()
           stk_numbers = [text[p_start],text[p2.start()],text[p3.start()]]
        else:
            if p2 != None:
                p_start = p2.start()
                p_end = p2.end()
                stk_numbers = [text[p_start],text[p3.start()]]
            else:
                if p3 != None:
                    p_start = p3.start()
                    p_end = p3.end()
                    stk_numbers = [text[p_start]]
                else:
                    break
        if text[p_start-2:p_start] == ', ' and text[p_start-3].isnumeric():
            text = text[p_end+1:]
        else:
            sentence_pkt_ref_numbers = sentence_pkt_ref_numbers + stk_numbers
            text = text[p_end+1:]
    return sentence_pkt_ref_numbers

def _stk_internal_query(ref, sentence_property_dict):
    node1_search_query = f"name: '{sentence_property_dict['name']}', parent: {sentence_property_dict['parent']}"
    node2_search_query = f"name: '{ref}. pkt.', parent: {sentence_property_dict['parent']}"
    return [node1_search_query, node2_search_query]

def _stk_internal_ref_dict(ref, sentence_property_dict):
    ref_from = {'name': sentence_property_dict['name'], 'parent': sentence_property_dict['parent']}
    ref_to = {'name': f'{ref}. pkt.', 'parent': sentence_property_dict['parent']}
    return {'ref_type': 'stk_internal', 'ref_from': ref_from, 'ref_to': ref_to}

def _get_stk_internal_ref_query(sentence_property_dict, sentence_list_ref):
    stk_internal_ref_query = []
    stk_internal_ref_dicts = []
    for ref in sentence_list_ref:
        stk_internal_ref_query.append(_stk_internal_query(ref, sentence_property_dict))
        stk_internal_ref_dicts.append(_stk_internal_ref_dict(ref, sentence_property_dict))
    return stk_internal_ref_query, stk_internal_ref_dicts

def stk_internal_references(sentence_property_list):
    stk_internal_ref_query_list = []
    stk_internal_ref_dict_list = []
    for sentence_property_dict in sentence_property_list:
        text = " " + sentence_property_dict['raw_text'].lower()
        sentence_pkt_ref_numbers = _get_sentence_pkt_ref_numbers(text)
        sentence_querys, stk_internal_ref_dicts = _get_stk_internal_ref_query(sentence_property_dict, sentence_pkt_ref_numbers)
        stk_internal_ref_query_list = stk_internal_ref_query_list + sentence_querys
        stk_internal_ref_dict_list = stk_internal_ref_dict_list + stk_internal_ref_dicts
    return stk_internal_ref_query_list, stk_internal_ref_dict_list

def create_stk_internal_ref_relations(stk_internal_ref_query_list):
    for querys in stk_internal_ref_query_list:
        create_relation(sentence_label_list[0],querys[0],
            sentence_label_list[0],querys[1],
                        'refers_to {type: "stk_internal"}')        

#%% Paragraph internal reference 
#i.e. one stk reference another in the same paragraph.
def _get_stk_nr_ref_numbers(number, nr_text):
    stk_nr_ref_numbers = [number]
    nr_number = ""
    nr_state = 'continue'
    j = -1
    while nr_state == 'continue':
        j += 1
        if nr_text[j].isnumeric():
            nr_number = nr_number + nr_text[j]
            continue
        elif nr_text[j:j+2] == ", ":
            stk_nr_ref_numbers.append(nr_number)
            nr_number = ""
            j = j+1
            continue
        elif nr_text[j:j+4] == " og ":
            stk_nr_ref_numbers.append(nr_number)
            nr_number = ""
            for s in nr_text[j+4:j+8]:
                if s.isnumeric():
                    nr_number = nr_number + s
                else:
                    stk_nr_ref_numbers.append(nr_number)
                    break            
            break
        elif nr_text[j:j+7] == " eller ":
            stk_nr_ref_numbers.append(nr_number)
            nr_number = ""
            for s in nr_text[j+7:j+10]:
                if s.isnumeric():
                    nr_number = nr_number + s
                else:
                    stk_nr_ref_numbers.append(nr_number)
                    break            
            break
        else:
            if len(nr_number) > 0:
                stk_nr_ref_numbers.append(nr_number)
            break
    return stk_nr_ref_numbers

def _get_stk_ref_numbers(text):
    stk_ref_numbers = []
    number = ""
    state = 'continue'
    i = -1
    while state == 'continue':
        i += 1
        if text[i].isnumeric():
            number = number + text[i]
            continue
        elif text[i:i+2] == ", ":
            if text[i+2:i+2+4] == "nr. ":
                nr_text = text[i+2+4:]
                number = _get_stk_nr_ref_numbers(number, nr_text)
                stk_ref_numbers.append(number)
                break
            #elif text[i+2:i+2+6] == "litra ":
            #    break
            else:
                stk_ref_numbers.append(number)
                number = ""
                i = i+1
                continue
        elif text[i:i+4] == " og ":
            stk_ref_numbers.append(number)
            number = ""
            for t in text[i+4:i+8]:
                if t.isnumeric():
                    number = number + t
                else:
                    if len(number) > 0:
                     stk_ref_numbers.append(number)
                    break
            break
        elif text[i:i+7] == " eller ":
            stk_ref_numbers.append(number)
            number = ""
            for s in text[i+7:i+10]:
                if s.isnumeric():
                    number = number + s
                else:
                    if len(number) > 0:
                     stk_ref_numbers.append(number)
                    break            
            break
        elif text[i] == '.' and text[i+1:i+1+5] == ' pkt.':
            stk_ref_numbers[-1] = stk_ref_numbers[-1] + ',' + number
            break
        elif text[i] == '-':
            start_nr = number
            end_nr = ""
            for j in range(1,6):
                if text[i+j].isnumeric():
                    end_nr = end_nr + text[i+j]
                elif text[i+j:i+j+4] == " og ":
                    number = ""
                    for t in text[i+j+4:i+j+8]:
                        if t.isnumeric():
                            number = number + t
                        else:
                            if len(number) > 0:
                             stk_ref_numbers.append(number)
                            break
                    break
                elif text[i+j:i+j+7] == " eller ":   
                    number = ""
                    for s in text[i+j+7:i+j+10]:
                        if s.isnumeric():
                            number = number + s
                        else:
                            if len(number) > 0:
                             stk_ref_numbers.append(number)
                            break            
                    break
                else:
                    break
            for k in range(int(start_nr),int(end_nr)+1):
                stk_ref_numbers.append(f"{k}")
            break
        else:
            if len(number) > 0:
               stk_ref_numbers.append(number) 
            break
    return stk_ref_numbers


# The following function finds explicit references to another stk in the same paragraph.
# These references are indicated by the use of the abbreciation "stk."
# The funktion returns a list of stk numbers that the text references explicitly.        
def _get_sentence_stk_ref_numbers(text):
    text = text.replace(' stk. ', ' stk.\xa0')
    sentence_stk_ref_numbers = []
    while text.find(' stk.\xa0') != -1:
        p = text.find(' stk.\xa0')
        if len(sentence_stk_ref_numbers) > 10:
            break
        if text[p-1].isnumeric() or text[p-2].isnumeric():
            text = text[p+6:]
        elif text[p+6].isnumeric() == False:
            text = text[p+6:]
        elif text[p-2].isalpha() and text[p-3] == ' ' and text[p-4].isnumeric():
            text = text[p+6:]
        else:
            sentence_stk_ref_numbers = sentence_stk_ref_numbers + _get_stk_ref_numbers(text[p+6:])
            text = text[p+6:]
    return sentence_stk_ref_numbers

def _internal_stk_query(ref, sentence_property_dict):
    node1_search_query = f"name: '{sentence_property_dict['name']}', parent: {sentence_property_dict['parent']}"
    parent_filter = [(sentence_property_dict['parent'].index(x)) for x in sentence_property_dict['parent'] if x.find('§') == 0][0]
    node2_search_query = f"name: 'Stk. {ref}.', parent: {sentence_property_dict['parent'][parent_filter:]}"
    return [node1_search_query, node2_search_query]

def _internal_stk_dict(ref, sentence_property_dict):
    ref_from = {'name': sentence_property_dict['name'], 'parent': sentence_property_dict['parent']}
    parent_filter = [(sentence_property_dict['parent'].index(x)) for x in sentence_property_dict['parent'] if x.find('§') == 0][0]
    ref_to = {'name': f'Stk. {ref}.', 'parent': sentence_property_dict['parent'][parent_filter:]}
    return {'ref_type': 'paragraph_internal', 'ref_from': ref_from, 'ref_to': ref_to}

def _internal_stk_nr_query(stk, nr, sentence_property_dict):
    node1_search_query = f"name: '{sentence_property_dict['name']}', parent: {sentence_property_dict['parent']}"
    parent_filter = [(sentence_property_dict['parent'].index(x)) for x in sentence_property_dict['parent'] if x.find('§') == 0][0]
    node2_parent_list = [f"Stk. {stk}."] + sentence_property_dict['parent'][parent_filter:]
    node2_search_query = f"name: '{nr})', parent: {node2_parent_list}"
    return [node1_search_query, node2_search_query]

def _internal_stk_nr_dict(stk, nr, sentence_property_dict):
    ref_from = {'name': sentence_property_dict['name'], 'parent': sentence_property_dict['parent']}
    parent_filter = [(sentence_property_dict['parent'].index(x)) for x in sentence_property_dict['parent'] if x.find('§') == 0][0]
    ref_to_parent_list = [f"Stk. {stk}."] + sentence_property_dict['parent'][parent_filter:]
    ref_to = {'name': f'{nr})', 'parent': ref_to_parent_list}
    return {'ref_type': 'paragraph_internal', 'ref_from': ref_from, 'ref_to': ref_to}

def _internal_stk_pkt_query(ref, sentence_property_dict):
    stk = ref[0:ref.find(',')]
    pkt = ref[ref.find(',')+1:]
    node1_search_query = f"name: '{sentence_property_dict['name']}', parent: {sentence_property_dict['parent']}"
    parent_filter = [(sentence_property_dict['parent'].index(x)) for x in sentence_property_dict['parent'] if x.find('§') == 0][0]
    node2_parent_list = [f"Stk. {stk}."] + sentence_property_dict['parent'][parent_filter:]
    node2_search_query = f"name: '{pkt}. pkt.', parent: {node2_parent_list}"
    return [node1_search_query, node2_search_query]

def _internal_stk_pkt_dict(ref, sentence_property_dict):
    stk = ref[0:ref.find(',')]
    pkt = ref[ref.find(',')+1:]
    ref_from = {'name': sentence_property_dict['name'], 'parent': sentence_property_dict['parent']}
    parent_filter = [(sentence_property_dict['parent'].index(x)) for x in sentence_property_dict['parent'] if x.find('§') == 0][0]
    ref_to_parent_list = [f"Stk. {stk}."] + sentence_property_dict['parent'][parent_filter:]
    ref_to = {'name': f'{pkt}. pkt.', 'parent': ref_to_parent_list}
    return {'ref_type': 'paragraph_internal', 'ref_from': ref_from, 'ref_to': ref_to}
    
def _get_paragraph_internal_ref_query(sentence_property_dict, sentence_stk_ref_numbers):
    sentence_internal_ref_query = []
    sentence_internal_ref_dicts = []
    for ref in sentence_stk_ref_numbers:
        if type(ref) == str:
            if ',' in ref:
                sentence_internal_ref_query.append(_internal_stk_pkt_query(ref, sentence_property_dict))
                sentence_internal_ref_dicts.append(_internal_stk_pkt_dict(ref, sentence_property_dict))
            else:
                sentence_internal_ref_query.append(_internal_stk_query(ref, sentence_property_dict))
                sentence_internal_ref_dicts.append(_internal_stk_dict(ref, sentence_property_dict))
        elif type(ref) == list:
            if ref[1].isnumeric():
                for nr in ref[1:]:
                    sentence_internal_ref_query.append(_internal_stk_nr_query(ref[0], nr, sentence_property_dict))
                    sentence_internal_ref_dicts.append(_internal_stk_nr_dict(ref[0], nr, sentence_property_dict))
    return sentence_internal_ref_query, sentence_internal_ref_dicts                 

def paragraph_internal_references(sentence_property_list):
    paragraph_internal_ref_query_list = []
    paragraph_internal_ref_dict_list = []
    for sentence_property_dict in sentence_property_list:
        text = " " + sentence_property_dict['raw_text'].lower()
        sentence_stk_ref_numbers = _get_sentence_stk_ref_numbers(text)
        sentence_querys, sentence_internal_ref_dicts = _get_paragraph_internal_ref_query(sentence_property_dict, sentence_stk_ref_numbers)
        paragraph_internal_ref_query_list = paragraph_internal_ref_query_list + sentence_querys
        paragraph_internal_ref_dict_list = paragraph_internal_ref_dict_list + sentence_internal_ref_dicts
    return paragraph_internal_ref_query_list, paragraph_internal_ref_dict_list
                

def create_paragraph_internal_ref_relations(paragraph_internal_ref_query_list):
    for querys in paragraph_internal_ref_query_list:
        create_relation(sentence_label_list[0],querys[0],
            sentence_label_list[0],querys[1],
                        'refers_to {type: "paragraph_internal"}')                    

#%% List internal reference

def _get_sentence_ref_litra(text):
    sentence_ref_litra = []
    while text.find(')') != -1:
        p = text.find(')')
        if text[p-1].isnumeric():
            text = text[p+1:]
        else:
            for i in range(1,p):
                if text[p-i] == ' ':
                    sentence_ref_litra.append(text[p-i+1:p+1])
                    break
            text = text[p+1:]
    return sentence_ref_litra
    
def _get_sentence_ref_number(text):
    sentence_ref_number = []
    while text.find(')') != -1:
        p = text.find(')')
        if text[p-1].isalpha():
            text = text[p+1:]
        else:
            for i in range(1,p):
                if text[p-i] == ' ':
                    sentence_ref_number.append(text[p-i+1:p+1])
                    break
            text = text[p+1:]
    return sentence_ref_number

def _list_internal_query(ref, sentence_property_dict):
    node1_search_query = f"name: '{sentence_property_dict['name']}', parent: {sentence_property_dict['parent']}"
    node2_search_query = f"name: '{ref}', parent: {sentence_property_dict['parent'][-3:]}"
    return [node1_search_query, node2_search_query]

def _list_internal_dict(ref, sentence_property_dict):
    ref_from = {'name': sentence_property_dict['name'], 'parent': sentence_property_dict['parent']}
    ref_to = {'name': ref, 'parent': sentence_property_dict['parent'][-3:]}
    return {'ref_type': 'list_internal', 'ref_from': ref_from, 'ref_to': ref_to}

def _get_list_internal_ref_query(sentence_property_dict, sentence_list_ref):
    list_internal_ref_query = []
    list_internal_ref_dicts = []
    for ref in sentence_list_ref:
        list_internal_ref_query.append(_list_internal_query(ref, sentence_property_dict))
        list_internal_ref_dicts.append(_list_internal_dict(ref, sentence_property_dict))
    return list_internal_ref_query, list_internal_ref_dicts

def list_internal_ref(sentence_property_list):
    list_internal_ref_query_list = []
    list_internal_ref_dict_list = []
    sentence_list_ref = []
    for sentence_property_dict in sentence_property_list:
        if sentence_property_dict['parent'][0].find(')') == 1:
            text = " " + sentence_property_dict['raw_text'].lower()
            if sentence_property_dict['parent'][0][0].isalpha():
                sentence_list_ref = _get_sentence_ref_litra(text)
            elif sentence_property_dict['parent'][0][0].isnumeric():
                sentence_list_ref = _get_sentence_ref_number(text)
            if len(sentence_list_ref)>0:
                sentence_querys, list_internal_ref_dicts = _get_list_internal_ref_query(sentence_property_dict, sentence_list_ref)
                list_internal_ref_query_list = list_internal_ref_query_list + sentence_querys
                list_internal_ref_dict_list = list_internal_ref_dict_list + list_internal_ref_dicts
        else:
            continue
        
    return list_internal_ref_query_list, list_internal_ref_dict_list
        
                    
def create_list_internal_ref_relations(list_internal_ref_query_list):
    for querys in list_internal_ref_query_list:
        create_relation(sentence_label_list[0],querys[0],
            sentence_label_list[0],querys[1],
                        'refers_to {type: "list_internal"}')  
            

#%% Relative paragraph internal references
# The following functions finds relativ references to another stk in the same paragraph.
# These are textual references to previous sections.
# The search words are found in relative_stk_ref_cues and are organized as a dict with the cue 
# and an indicator if a cue references only one or all other stk in a paragraph.  
def _check_for_relative_stk_ref(text):
    relative_ref_present = False
    for cue in relative_stk_ref_cues:
        if text.find(cue) > -1:
            relative_ref_present = True
    return relative_ref_present
        
def get_relative_ref_sets(sentence_property_list):
    relative_stk_ref_sets_list = []
    active_paragraph = ""
    stk_of_active_paragraph = []
    for sentence_property_dict in sentence_property_list:
        sentence_paragraph = sentence_property_dict['parent'][-2]
        sentence_stk = sentence_property_dict['parent'][-3]
        if sentence_paragraph != active_paragraph:
            active_paragraph = sentence_paragraph
            stk_of_active_paragraph = [sentence_stk]
        elif sentence_stk not in stk_of_active_paragraph:
            stk_of_active_paragraph.append(sentence_stk)
        
        if _check_for_relative_stk_ref(sentence_property_dict['raw_text'].lower()) is True:
            stk_of_active_paragraph.remove(sentence_stk)
            relative_stk_ref_sets_list.append([sentence_property_dict, stk_of_active_paragraph])
    return relative_stk_ref_sets_list

def _get_relative_stk_ref_dict(sentence_property_dict, ref_stk):
    ref_from = {'name': sentence_property_dict['name'], 'parent': sentence_property_dict['parent']}
    ref_to_parent_list = sentence_property_dict['parent'][-2:]
    ref_to = {'name': ref_stk, 'parent': ref_to_parent_list}
    return {'ref_type': 'paragraph_internal', 'ref_from': ref_from, 'ref_to': ref_to}

def get_relative_stk_ref_dict_list(relative_stk_ref_sets_list):
    relative_stk_ref_dict_list = []
    for relative_stk_ref_set in relative_stk_ref_sets_list:
        for ref_stk in relative_stk_ref_set[1]:
            relative_stk_ref_dict_list.append(_get_relative_stk_ref_dict(relative_stk_ref_set[0], ref_stk))
    return relative_stk_ref_dict_list


def _get_relative_stk_ref_query(sentence_property_dict, ref_stk):
    node1_search_query = f"name: '{sentence_property_dict['name']}', parent: {sentence_property_dict['parent']}"
    node2_parent_list = sentence_property_dict['parent'][-2:]
    node2_search_query = f"name: '{ref_stk}', parent: {node2_parent_list}"
    return [node1_search_query, node2_search_query]

def create_relative_stk_ref_relation(relative_stk_ref_sets_list):
    for relative_stk_ref_set in relative_stk_ref_sets_list:
        for ref_stk in relative_stk_ref_set[1]:
            querys = _get_relative_stk_ref_query(relative_stk_ref_set[0], ref_stk)
            create_relation(sentence_label_list[0],querys[0],
                sentence_label_list[0],querys[1],
                            'refers_to {type: "paragraph_internal"}')
               
#%% Specific paragraph references. References across the different paragraphs to specific paragraphs


def _get_single_ref_string(text): # Used both in _get_single_ref_dict() and _get_noncontinuous_ref_dict()
    ref_string = text[0:2]
    paragraph_string = text[0:2]
    stk_string = ""
    nr_string = ""
    pkt_string = ""
    searching = True
    i = 2
    while searching == True:
        if len(text)<3:
            break
        #paragraph
        elif text[i].isnumeric():
            ref_string = ref_string + text[i]
            paragraph_string = paragraph_string + text[i]
            i += 1
        elif re.fullmatch(" [a-z][ ,.]", text[i:i+3]) != None and re.fullmatch(" i lov", text[i:i+6]) == None:
            ref_string = ref_string + text[i:i+2]
            paragraph_string = paragraph_string + text[i:i+2]
            i += 2
        # stk
        elif re.fullmatch(", stk. [1-9]-[1-9]", text[i:i+10]) != None:
            ref_string = ref_string + text[i:i+10]
            start_stk = text[i:i+10][-3]
            end_stk = text[i:i+10][-1]
            for stk in range(int(start_stk),int(end_stk)+1):
                stk_string = stk_string + f'stk. {stk},'
            i += 10
        elif re.fullmatch(", stk. [1-9], [1-9] og [1-9]", text[i:i+16]) != None:
            ref_string = ref_string + text[i:i+16]
            stk_string = stk_string + text[i+2:i+16]
            i += 16
        elif re.fullmatch(", stk. [1-9], [1-9] eller [1-9]", text[i:i+19]) != None:
            ref_string = ref_string + text[i:i+19]
            stk_string = stk_string + text[i+2:i+19]
            i += 19
        elif re.fullmatch(", stk. [1-9] og [1-9]", text[i:i+13]) != None:
            ref_string = ref_string + text[i:i+13]
            stk_string = stk_string + text[i+2:i+13]
            i += 13
        elif re.fullmatch(", stk. [1-9] eller [1-9]", text[i:i+16]) != None:
            ref_string = ref_string + text[i:i+16]
            stk_string = stk_string + text[i+2:i+16]
            i += 16
        elif re.fullmatch(", stk. [1-9]", text[i:i+8]) != None:
            ref_string = ref_string + text[i:i+8]
            stk_string = stk_string + text[i+2:i+8]
            i += 8
        # nummer
        elif re.fullmatch(", nr. [1-9]-[1-9]", text[i:i+9]) != None:
            ref_string = ref_string + text[i:i+9]
            start_nr = text[i:i+9][-3]
            end_nr = text[i:i+9][-1]
            for nr in range(int(start_nr),int(end_nr)+1):
                nr_string = nr_string + f'nr. {nr},'
            i += 9
        elif re.fullmatch(", nr. [1-9], [1-9] og [1-9]", text[i:i+15]) != None:
            ref_string = ref_string + text[i:i+15]
            nr_string = nr_string + text[i+2:i+15]
            i += 15
        elif re.fullmatch(", nr. [1-9], [1-9] eller [1-9]", text[i:i+18]) != None:
            ref_string = ref_string + text[i:i+18]
            nr_string = nr_string + text[i+2:i+18]
            i += 18
        elif re.fullmatch(", nr. [1-9] og [1-9]", text[i:i+12]) != None:
            ref_string = ref_string + text[i:i+12]
            nr_string = nr_string + text[i+2:i+12]
            i += 12
        elif re.fullmatch(", nr. [1-9] eller [1-9]", text[i:i+15]) != None:
            ref_string = ref_string + text[i:i+15]
            nr_string = nr_string + text[i+2:i+15]
            i += 15
        elif re.fullmatch(", nr. [1-9]", text[i:i+7]) != None:
            ref_string = ref_string + text[i:i+7]
            nr_string = nr_string + text[i+2:i+7]
            i += 7
        # litra
        # Added later
        # pkt
        elif re.fullmatch(", [1-9]., [1-9]. og [1-9]. pkt.", text[i:i+19]) != None:
            ref_string = ref_string + text[i:i+19]
            pkt_string = pkt_string + text[i+2:i+19]
            i += 19
        elif re.fullmatch(", [1-9]., [1-9]. eller [1-9]. pkt.", text[i:i+22]) != None:
            ref_string = ref_string + text[i:i+22]
            pkt_string = pkt_string + text[i+2:i+22]
            i += 22
        elif re.fullmatch(", [1-9]. og [1-9]. pkt.", text[i:i+15]) != None:
            ref_string = ref_string + text[i:i+15]
            pkt_string = pkt_string + text[i+2:i+15]
            i += 15
        elif re.fullmatch(", [1-9]. eller [1-9]. pkt.", text[i:i+18]) != None:
            ref_string = ref_string + text[i:i+18]
            pkt_string = pkt_string + text[i+2:i+18]
            i += 18
        elif re.fullmatch(", [1-9]. pkt.", text[i:i+9]) != None:
            ref_string = ref_string + text[i:i+9]
            pkt_string = pkt_string + text[i+2:i+9]
            i += 9
        else:
            searching = False
            break
    return ref_string, paragraph_string, stk_string, nr_string, pkt_string 

def _get_single_ref_dict(p, text):
    try:
     ref_string, paragraph_string, stk_string, nr_string, pkt_string = _get_single_ref_string(text[p:])
    except:
        print(text[p:])
    partial_parent_list = []
    ref_names = []
    p_ref_list = []
    if len(pkt_string) > 0:
        for n in re.findall("[1-9]", pkt_string):
            ref_names.append(f"{n}. pkt.")
        
        if len(nr_string) > 0:
            nr_number = re.search("[1-9]",nr_string)[0]
            nr_name = f'{nr_number})'
            partial_parent_list.append(nr_name)
        
        if len(stk_string) > 0:
            stk_name = stk_string.replace('stk.', 'Stk.')
            partial_parent_list.append(stk_name+'.')
        if len(stk_string) == 0:
            stk_name = 'Stk. 1.'
            partial_parent_list.append(stk_name)
        
        partial_parent_list.append(paragraph_string.replace('§ ', '§\xa0')+'.')
    
    elif len(nr_string) > 0:
        for n in re.findall("[1-9]", nr_string):
            ref_names.append(f"{n})")
        
        if len(stk_string) > 0:
            stk_name = stk_string.replace('stk.', 'Stk.')
            partial_parent_list.append(stk_name+'.')
        if len(stk_string) == 0:
            stk_name = 'Stk. 1.'
            partial_parent_list.append(stk_name)
            
        partial_parent_list.append(paragraph_string.replace('§ ', '§\xa0')+'.')
    
    elif len(stk_string) > 0:
        for n in re.findall("[1-9]", stk_string):
            ref_names.append(f"Stk. {n}.")
            
        partial_parent_list.append(paragraph_string.replace('§ ', '§\xa0')+'.')
    
    else:
        ref_names.append(paragraph_string.replace('§ ', '§\xa0')+'.')
    
    p_refs = {
        "ref_names": ref_names,
        "partial_parent": partial_parent_list
        }
    
    p_ref_list.append(p_refs)
    single_ref_dict = {
        "ref_string": ref_string,
        "p_ref_list": p_ref_list,
        "ref_type": "single"
        }
    return single_ref_dict

def _get_continuous_ref_dict(p, text, paragraph_property_list):
    ref_string = '§§\xa0'
    start_p_nr = '§\xa0'
    is_start = True
    end_p_nr = '§\xa0'
    extra_ref_dict = None
    not_continuous = False
    search_text = text[p+3:]
    for i in range(0,len(search_text)):
        if search_text[i].isnumeric() and is_start == True:
            start_p_nr = start_p_nr + search_text[i]
            ref_string = ref_string + search_text[i]
        elif search_text[i].isnumeric() and is_start == False:
            end_p_nr = end_p_nr + search_text[i]
            ref_string = ref_string + search_text[i]
        elif search_text[i] =='-':
            ref_string = ref_string + search_text[i]
            start_p_nr = start_p_nr + '.'
            is_start = False
        elif search_text[i:i+7] == ' eller ' and is_start == False:
            ref_string = ref_string + ' eller '
            extra_ref_dict = _get_single_ref_dict(0, "§\xa0"+search_text[i+7:])
            ref_string = ref_string + extra_ref_dict['ref_string'][2:]
        elif search_text[i:i+4] == ' og ' and is_start == False:
            ref_string = ref_string + ' og '
            extra_ref_dict = _get_single_ref_dict(0, "§\xa0"+search_text[i+4:])
            ref_string = ref_string + extra_ref_dict['ref_string'][2:]
        else:
            if is_start == True:
               not_continuous = True 
            end_p_nr = end_p_nr + '.'
            break
    
    if not_continuous == True:
        return None
    if not_continuous == False:
        is_start = False
        continuous_ref_list = []
        for paragraph in paragraph_property_list:
            if paragraph['name'] == start_p_nr:
                is_start = True
                continuous_ref_list.append({
                    "ref_names": [paragraph['name']],
                    "partial_parent": []
                    })
                continue
            elif paragraph['name'] != start_p_nr and paragraph['name'] != end_p_nr and is_start == True:
                continuous_ref_list.append({
                    "ref_names": [paragraph['name']],
                    "partial_parent": []
                    })
                continue
            elif paragraph['name'] == end_p_nr:
                is_start = False
                continuous_ref_list.append({
                    "ref_names": [paragraph['name']],
                    "partial_parent": []
                    })
                if extra_ref_dict != None:
                    continuous_ref_list = continuous_ref_list + extra_ref_dict['p_ref_list']
                break
            else:
                continue                
            
        continuous_ref_dict = {
            "ref_string": ref_string,
            "p_ref_list": continuous_ref_list,
            "ref_type": "continuous"
            }
        return continuous_ref_dict
    
def _get_noncontinuous_ref_dict(p, text):
    ref_string = '§'
    noncontinuous_ref_list = []
    search_text = text[p:].replace('§ ', '§\xa0')
    state = 'continue'
    i = 1
    while state == 'continue':
        if len(search_text[i:]) == 1 and search_text[i:].isnumeric() == False:
            state = 'break'
            break
        if i > len(search_text)-1:
            state = 'break'
            break
        if re.fullmatch(' og ',search_text[i:i+4]) != None:
            ref_string = ref_string + ' o'
            i += 2
            continue
        if re.fullmatch(' eller ',search_text[i:i+7]) != None:
            ref_string = ref_string + ' elle'
            i += 5
            continue
        
        indi_ref_str, indi_p_str, indi_stk_str, indi_nr_str, indi_pkt_str = _get_single_ref_string(search_text[i:])
        
        if len(indi_ref_str) == 2:
            state = 'break'
            break
        
        partial_parent_list = []
        ref_names = []
        
        if len(indi_pkt_str) > 0:
            for n in re.findall("[1-9]", indi_pkt_str):
                ref_names.append(f"{n}. pkt.")
            
            if len(indi_nr_str) > 0:
                nr_number = re.search("[1-9]", indi_nr_str)[0]
                nr_name = f'{nr_number})'
                partial_parent_list.append(nr_name)
            
            if len(indi_stk_str) > 0:
                stk_name = indi_stk_str.replace('stk.', 'Stk.')
                partial_parent_list.append(stk_name)
            if len(indi_stk_str) == 0:
                stk_name = 'Stk. 1'
                partial_parent_list.append(stk_name)
            
            partial_parent_list.append(indi_p_str.replace('§ ', '§\xa0').replace(', ', '§\xa0').replace('g ', '§\xa0').replace('r ', '§\xa0')+'.')
        
        elif len(indi_nr_str) > 0:
            for n in re.findall("[1-9]", indi_nr_str):
                ref_names.append(f"{n})")
            
            if len(indi_stk_str) > 0:
                stk_name = indi_stk_str.replace('stk.', 'Stk.')
                partial_parent_list.append(stk_name)
            if len(indi_stk_str) == 0:
                stk_name = 'Stk. 1'
                partial_parent_list.append(stk_name)
                
            partial_parent_list.append(indi_p_str.replace('§ ', '§\xa0').replace(', ', '§\xa0').replace('g ', '§\xa0').replace('r ', '§\xa0')+'.')
        
        elif len(indi_stk_str) > 0:
            for n in re.findall("[1-9]", indi_stk_str):
                ref_names.append(f"Stk. {n}.")
                
            partial_parent_list.append(indi_p_str.replace('§ ', '§\xa0').replace(', ', '§\xa0').replace('g ', '§\xa0').replace('r ', '§\xa0')+'.')
        
        else:
            ref_names.append(indi_p_str.replace('§ ', '§\xa0').replace(', ', '§\xa0').replace('g ', '§\xa0').replace('r ', '§\xa0')+'.')
        
        indi_refs = {
            "ref_names": ref_names,
            "partial_parent": partial_parent_list
            }
        
        noncontinuous_ref_list.append(indi_refs)
        ref_string = ref_string + indi_ref_str.replace('§ ', '§\xa0')
        i = re.search(ref_string, search_text).end(0)
        
        
    noncontinuous_ref_dict = {
        "ref_string": ref_string,
        "p_ref_list": noncontinuous_ref_list,
        "ref_type": "noncontinuous"
        } 
    
    return noncontinuous_ref_dict 
    
# Get individual refs: A reference can either be to a single concept indicated by a " §"
#                       or to multiple concept indicated by a " §§".
#                       The later can either be a list of concepts or a continues range of paragraphs.    
def _get_individual_ref_dict(p, text, paragraph_property_list):
    if text[p-1:p+2] == ' §\xa0' and text[p+2].isnumeric():
        single_ref_dict = _get_single_ref_dict(p, text)
        individual_ref_dict = single_ref_dict
    
    elif text[p-1:p+3] == ' §§\xa0' and text[p+3].isnumeric():
        continuous_ref_dict = _get_continuous_ref_dict(p, text, paragraph_property_list)
        if  continuous_ref_dict != None:
            individual_ref_dict = continuous_ref_dict
                
        elif continuous_ref_dict == None:
            noncontinuous_ref_dict = _get_noncontinuous_ref_dict(p, text)
            individual_ref_dict = noncontinuous_ref_dict
            
    return individual_ref_dict
  
        
# Test for external refs
def _external_ref_present_in_sentence(text):
    external_refs_present = []
    for ref_cue in external_reference_cues:
        if ref_cue.lower() in text.lower():
            external_refs_present.append(ref_cue)
    return external_refs_present

# Get refernence 1. sub function! Preb text, call external_ref_present-function and get the internal sentence ref list.
def _get_sentence_paragraph_specific_ref_list(text, paragraph_property_list):
    search_text = text.replace('§ ', '§\xa0')
    search_text_external = text.replace('§ ', '§\xa0')
    sentence_paragraph_specific_ref_list = []
    
    potentially_external_ref_list = []
    
    external_refs_present = _external_ref_present_in_sentence(text)
    
    while search_text.find('§') != -1:
        p = search_text.find('§')
        individual_ref_dict = _get_individual_ref_dict(p, search_text, paragraph_property_list) # Here we are only geting references indicated by a "§"!!!
        if len(external_refs_present) == 0:
            new_start = re.search(individual_ref_dict['ref_string'], search_text).end(0)
            individual_ref_dict['parent_law'] = 'internal'
            sentence_paragraph_specific_ref_list.append(individual_ref_dict)
            search_text = search_text[new_start:]
    
        elif len(external_refs_present) != 0:
            ref_replacement = individual_ref_dict['ref_string'].replace(',','@@')
            search_text_external = search_text_external.replace(individual_ref_dict['ref_string'], ref_replacement)
            search_text_external = search_text_external.replace(', i lov','@@ i lov')
            potentially_external_ref_list.append(individual_ref_dict)
            new_start = re.search(individual_ref_dict['ref_string'], search_text).end(0)
            search_text = search_text[new_start:]
            
    search_text_external = search_text_external.replace(', §','@@ §')
    for external_ref_cue in external_refs_present:
        search_text_external = search_text_external.replace(f', i{external_ref_cue}',f'@@ i{external_ref_cue}') 
    search_text_external_split = re.split(',| efter | sammenholdt med ', search_text_external)
    
    for ref in potentially_external_ref_list:
        test_ref_string = ref['ref_string'].replace(',','@@')
        external = False
        for text_ex in search_text_external_split:
            if test_ref_string in text_ex:
                for external_ref_cue in external_refs_present:
                    if external_ref_cue.lower() in text_ex.lower():
                        ref['parent_law'] = external_ref_cue
                        
                        sentence_paragraph_specific_ref_list.append(ref)
                        
                        external = True
                        
        if external == False:
            refs_in_law_count = 0
            for ref_name in ref['p_ref_list']:
                for paragraph in paragraph_property_list:
                    if ref_name['ref_names'][0][0] =='§':
                        if ref_name['ref_names'][0] == paragraph['name']:
                            refs_in_law_count += 1
                    else:
                        if ref_name['partial_parent'][0] == paragraph['name']:
                            refs_in_law_count += 1
            
            if refs_in_law_count == len(ref['p_ref_list']):  
                ref['parent_law'] = 'internal'
                
                sentence_paragraph_specific_ref_list.append(ref)
            else:
                ref['parent_law'] = external_refs_present[0]
                sentence_paragraph_specific_ref_list.append(ref)
    return sentence_paragraph_specific_ref_list #Should be a list of all law internal references! 


# Get query sub function for getting parents.
def _get_ref_parent(ref_name, paragraph_property_list):
    for paragraph in paragraph_property_list:
        if ref_name == paragraph['name']:
            ref_parent = paragraph['parent']
    return ref_parent

# Get the law internal refs in every sentence
def _get_law_internal_ref_query(sentence_property_dict, ref_name, ref_parent):
    node1_search_query = f"name: '{sentence_property_dict['name']}', parent: {sentence_property_dict['parent']}"
    node2_search_query = f"name: '{ref_name}', parent: {ref_parent}"
    return [node1_search_query, node2_search_query]

def _get_law_internal_ref_dict(sentence_property_dict, ref_name, ref_parent):
    ref_from = {'name': sentence_property_dict['name'], 'parent': sentence_property_dict['parent']}
    ref_to = {'name': ref_name, 'parent': ref_parent}
    return {'ref_type': 'law_internal', 'ref_from': ref_from, 'ref_to': ref_to}

## Main function            
def paragraph_specific_references(sentence_property_list, paragraph_property_list):
    law_internal_paragraph_specific_ref_query_list = []
    law_internal_paragraph_specific_ref_dict_list = []
    law_external_paragraph_specific_ref_list = []
    for sentence_property_dict in sentence_property_list:
        text = " " + sentence_property_dict['raw_text'].lower()
        sentence_paragraph_specific_ref_list = _get_sentence_paragraph_specific_ref_list(text, paragraph_property_list) #geting references
        
        # Creating the query for every reference -> move to seperate function.
        for ref_instance in sentence_paragraph_specific_ref_list:
            if ref_instance['parent_law'] == 'internal':
                for ref in ref_instance['p_ref_list']:
                    for ref_name in ref['ref_names']:
                        if ref_name[-2] =='i':
                            ref_name_exist = False
                            for paragraph in paragraph_property_list:
                                
                                if ref_name == paragraph['name']:
                                    ref_name_exist = True
                            if ref_name_exist == False:
                                ref_name = ref_name[0:-3] + '.'
                        
                        if len(ref['partial_parent']) >0:
                            ref_name_exist = False
                            for paragraph in paragraph_property_list:
                                if ref['partial_parent'][-1] == paragraph['name']:
                                    ref_name_exist = True
                            if ref_name_exist == False:
                                continue
                            ref_parent = ref['partial_parent'] + _get_ref_parent(ref['partial_parent'][-1], paragraph_property_list)
                        else:
                            ref_name_exist = False
                            for paragraph in paragraph_property_list:
                                if ref_name == paragraph['name']:
                                    ref_name_exist = True
                            if ref_name_exist == False:
                                continue
                            ref_parent = _get_ref_parent(ref_name, paragraph_property_list)
                        ref_query = _get_law_internal_ref_query(sentence_property_dict, ref_name, ref_parent)
                        ref_dict = _get_law_internal_ref_dict(sentence_property_dict, ref_name, ref_parent)
                        law_internal_paragraph_specific_ref_query_list.append(ref_query)
                        law_internal_paragraph_specific_ref_dict_list.append(ref_dict)
            
            elif ref_instance['parent_law'] != 'internal':
                law_external_paragraph_specific_ref_list.append((sentence_property_dict, ref_instance))
                    
    return law_internal_paragraph_specific_ref_query_list, law_internal_paragraph_specific_ref_dict_list, law_external_paragraph_specific_ref_list
            
def create_law_internal_ref_relation(law_internal_ref_query_list):
    for law_internal_ref_set in law_internal_ref_query_list:
            create_relation(sentence_label_list[0],law_internal_ref_set[0],
                sentence_label_list[0],law_internal_ref_set[1],
                            'refers_to {type: "law_internal"}')            
        
#%% Internal references to the law as a whole.             

def internal_ref_to_whole_law(sentence_property_list):
    internal_ref_to_whole_law_list = []
    for sentence_property_dict in sentence_property_list:
        text = " " + sentence_property_dict['raw_text'].lower()
        for cue in internal_ref_to_whole_law_cues:
            if text.find(cue) > -1:
                internal_ref_to_whole_law_list.append([sentence_property_dict['name'], sentence_property_dict['parent']])
                break
    return internal_ref_to_whole_law_list

def get_internal_ref_to_whole_law_dict_list(internal_ref_to_whole_law_list, lov_name, lov_shortname):
    internal_ref_to_whole_law_dict_list = []
    for internal_ref_to_whole_law in internal_ref_to_whole_law_list:
            ref_from = {'name': internal_ref_to_whole_law[0], 'parent': internal_ref_to_whole_law[1]}
            ref_to = {'name': lov_name, 'shortName': lov_shortname}
            ref_dict = {'ref_type': 'law_internal', 'ref_from': ref_from, 'ref_to': ref_to}
            internal_ref_to_whole_law_dict_list.append(ref_dict)
    return internal_ref_to_whole_law_dict_list
    
def create_internal_ref_to_whole_law_relation(internal_ref_to_whole_law_list):
    for internal_ref_to_whole_law in internal_ref_to_whole_law_list:
            node1_search_query = f"name: '{internal_ref_to_whole_law[0]}', parent: {internal_ref_to_whole_law[1]}"
            node2_search_query = f"name: '{lov_name}', shortName: '{lov_shortname}'"
            create_relation(sentence_label_list[0],node1_search_query,
                sentence_label_list[0],node2_search_query,
                            'refers_to {type: "law_internal"}')               

#%% Get law_document_dict
def concatenate_lists(list_of_lists):
    output_list = []
    for l in list_of_lists:
        output_list = output_list + l
    return output_list

def _get_legal_concept_id(name, parent_list):
    lc_id = name
    for parent in parent_list:
        lc_id = lc_id + '_' + parent
    return lc_id
    
def _get_sentence_bow_meanvector(sentence_raw_text, stopwords, word_embeddings):
    raw_text = sentence_raw_text.lower()
    for exception in abbreviations:
        raw_text = raw_text.replace(exception[0], '')
    
    raw_text_clean = re.sub('[^a-zæøå ]+', '', raw_text)
    
    words = []
    for word in raw_text_clean.split():
        if word not in stopwords:
            words.append(word)
    
    bow = dict()
    oov_list = list()
    word_vector_sum = np.array([0]*word_embeddings.vector_size, dtype='float32')
    word_count = 0
    for word in words:
        try:
            word_vector = word_embeddings[word]
            word_vector_sum += word_vector
            word_count += 1
            if word in bow.keys():
                bow[word] += 1
            else:
                bow[word] = 1
        except:
            word_vector = None
            oov_list.append(word)
        
    if word_count > 0:
        word_vector_mean = word_vector_sum/word_count
    else:
        word_vector_mean = None
    return bow, word_vector_mean, oov_list

def _get_law_document_dict_raw(url):
    
    #Lov
    lov_soup, lov_property_dict, lov_name, lov_shortname = law_property_gen(url)
    
    #Paragraphs
    (paragraph_property_list, chapter_property_list) = paragraph_property_gen(lov_soup, lov_shortname)
    
    # Stk   
    stk_property_list = stk_property_gen(paragraph_property_list)
    
    #Litra, Nr and sentences
    (litra_property_list,
    nr_property_list,
    sentence_property_list) = sentence_litra_nr_property_gen(stk_property_list)

    #----------------------------------------------------------------------------                                                             
    ## References
    stk_internal_ref_query_list, stk_internal_ref_dict_list = stk_internal_references(sentence_property_list)
        
    paragraph_internal_references_query_list, paragraph_internal_ref_dict_list = paragraph_internal_references(sentence_property_list)

    relative_stk_ref_sets_list = get_relative_ref_sets(sentence_property_list) #only in funktionærloven
    relative_stk_ref_dict_list = get_relative_stk_ref_dict_list(relative_stk_ref_sets_list)
        
    list_internal_ref_query_list, list_internal_ref_dict_list = list_internal_ref(sentence_property_list) #only in funktionærloven

    (law_internal_paragraph_specific_ref_query_list,
     law_internal_paragraph_specific_ref_dict_list,
     law_external_paragraph_specific_ref_list) = paragraph_specific_references(sentence_property_list, paragraph_property_list)

    internal_ref_to_whole_law_list = internal_ref_to_whole_law(sentence_property_list)
    internal_ref_to_whole_law_dict_list = get_internal_ref_to_whole_law_dict_list(internal_ref_to_whole_law_list, lov_name, lov_shortname)
    
    # internal ref dict list
    internal_ref_dict_list = concatenate_lists([stk_internal_ref_dict_list,
                                                paragraph_internal_ref_dict_list,
                                                relative_stk_ref_dict_list,
                                                law_internal_paragraph_specific_ref_dict_list,
                                                internal_ref_to_whole_law_dict_list
                                                ])
                            
    #missing external references to document as a whole or chapters.
    
    law_document_dict_raw = {'law': lov_property_dict, 'law_label': lov_label_list,
                         'chapter': chapter_property_list, 'chapter_label': chapter_label_list,
                         'paragraph': paragraph_property_list, 'paragraph_label': paragraph_label_list,
                         'stk': stk_property_list, 'stk_label': stk_label_list,
                         'litra': litra_property_list, 'litra_label': litra_label_list,
                         'nr': nr_property_list, 'nr_label': nr_label_list,
                         'sentence': sentence_property_list, 'sentence_label': sentence_label_list,
                         'internal_ref': internal_ref_dict_list,
                         'external_ref': law_external_paragraph_specific_ref_list
                         }
    
    return law_document_dict_raw
    
def get_law_document_dict(url, stopwords, word_embeddings):
    law_document_dict_raw = _get_law_document_dict_raw(url)
    legal_concepts = {}
    
    # law
    law = law_document_dict_raw['law']
    law_id = _get_legal_concept_id(law['shortName'],[])
    new_law_property_dict = {
        'id': law_id,
        'name': law['name'],
        'shortName': law['shortName'],
        'title': law['title'],
        'date_of_publication': law['date_of_publication'],
        'ressort': law['ressort'],
        'retsinfo_id': law['id'],
        'url': url,
        'labels': law_document_dict_raw['law_label'],
        'bow': dict(),
        'bow_meanvector': np.array([0]*word_embeddings.vector_size, dtype='float32'),
        'concept_bow': dict(),
        'concept_vector': np.array([0]*word_embeddings.vector_size, dtype='float32'),
        'neighbours': []
        }
    
    legal_concepts[law_id] = new_law_property_dict
    
    # chapter
    chapter_list = law_document_dict_raw['chapter']
    for chapter in chapter_list:
        chapter_id = _get_legal_concept_id(chapter['name'],chapter['parent'])
        new_chapter_property_dict = {
            'id': chapter_id,
            'name': chapter['name'],
            'shortName': chapter['shortName'],
            'position': chapter['position'],
            'parent': chapter['parent'],
            'labels': law_document_dict_raw['chapter_label'],
            'bow': dict(),
            'bow_meanvector': np.array([0]*word_embeddings.vector_size, dtype='float32'),
            'concept_bow': dict(),
            'concept_vector': np.array([0]*word_embeddings.vector_size, dtype='float32')
            }
        
        parent_id = _get_legal_concept_id(chapter['parent'][0],chapter['parent'][1:])
        new_chapter_property_dict['neighbours'] = [{'neighbour':parent_id, 'type': 'parent'}]
        legal_concepts[parent_id]['neighbours'].append({'neighbour':chapter_id, 'type': 'child'})
        
        
        legal_concepts[chapter_id] = new_chapter_property_dict
    
    # paragraph
    paragraph_list = law_document_dict_raw['paragraph']
    for paragraph in paragraph_list:
        paragraph_id = _get_legal_concept_id(paragraph['name'],paragraph['parent'])
        new_paragraph_property_dict = {
            'id': paragraph_id,
            'name': paragraph['name'],
            'position': paragraph['position'],
            'parent': paragraph['parent'],
            'labels': law_document_dict_raw['paragraph_label'],
            'bow': dict(),
            'bow_meanvector': np.array([0]*word_embeddings.vector_size, dtype='float32'),
            'concept_bow': dict(),
            'concept_vector': np.array([0]*word_embeddings.vector_size, dtype='float32')
            }
        
        parent_id = _get_legal_concept_id(paragraph['parent'][0],paragraph['parent'][1:])
        new_paragraph_property_dict['neighbours'] = [{'neighbour':parent_id, 'type': 'parent'}]
        legal_concepts[parent_id]['neighbours'].append({'neighbour':paragraph_id, 'type': 'child'})
        
        legal_concepts[paragraph_id] = new_paragraph_property_dict
    
    # stk
    stk_list = law_document_dict_raw['stk']
    for stk in stk_list:
        stk_id = _get_legal_concept_id(stk['name'],stk['parent'])
        new_stk_property_dict = {
            'id': stk_id,
            'name': stk['name'],
            'position': stk['position'],
            'parent': stk['parent'],
            'labels': law_document_dict_raw['stk_label'],
            'bow': dict(),
            'bow_meanvector': np.array([0]*word_embeddings.vector_size, dtype='float32'),
            'concept_bow': dict(),
            'concept_vector': np.array([0]*word_embeddings.vector_size, dtype='float32')
            }
        
        parent_id = _get_legal_concept_id(stk['parent'][0],stk['parent'][1:])
        new_stk_property_dict['neighbours'] = [{'neighbour':parent_id, 'type': 'parent'}]
        legal_concepts[parent_id]['neighbours'].append({'neighbour':stk_id, 'type': 'child'})
        
        legal_concepts[stk_id] = new_stk_property_dict
        
    # litra
    litra_list = law_document_dict_raw['litra']
    for litra in litra_list:
        litra_id = _get_legal_concept_id(litra['name'],litra['parent'])
        new_litra_property_dict = {
            'id': litra_id,
            'name': litra['name'],
            'position': litra['position'],
            'parent': litra['parent'],
            'labels': law_document_dict_raw['litra_label'],
            'bow': dict(),
            'bow_meanvector': np.array([0]*word_embeddings.vector_size, dtype='float32'),
            'concept_bow': dict(),
            'concept_vector': np.array([0]*word_embeddings.vector_size, dtype='float32')
            }
        
        parent_id = _get_legal_concept_id(litra['parent'][0],litra['parent'][1:])
        new_litra_property_dict['neighbours'] = [{'neighbour':parent_id, 'type': 'parent'}]
        legal_concepts[parent_id]['neighbours'].append({'neighbour':litra_id, 'type': 'child'})
        
        legal_concepts[litra_id] = new_litra_property_dict
        
    # nr
    nr_list = law_document_dict_raw['nr']
    for nr in nr_list:
        nr_id = _get_legal_concept_id(nr['name'],nr['parent'])
        new_nr_property_dict = {
            'id': nr_id,
            'name': nr['name'],
            'position': nr['position'],
            'parent': nr['parent'],
            'labels': law_document_dict_raw['nr_label'],
            'bow': dict(),
            'bow_meanvector': np.array([0]*word_embeddings.vector_size, dtype='float32'),
            'concept_bow': dict(),
            'concept_vector': np.array([0]*word_embeddings.vector_size, dtype='float32')
            }
        
        parent_id = _get_legal_concept_id(nr['parent'][0],nr['parent'][1:])
        new_nr_property_dict['neighbours'] = [{'neighbour':parent_id, 'type': 'parent'}]
        legal_concepts[parent_id]['neighbours'].append({'neighbour':nr_id, 'type': 'child'})
        
        legal_concepts[nr_id] = new_nr_property_dict
        
    # sentence
    sentence_list = law_document_dict_raw['sentence']
    oov_list = list()
    for sentence in sentence_list:
        bow, meanvector, sentence_oov_list = _get_sentence_bow_meanvector(sentence['raw_text'], stopwords, word_embeddings)
        sentence_id = _get_legal_concept_id(sentence['name'],sentence['parent'])
        new_sentence_property_dict = {
            'id': sentence_id,
            'name': sentence['name'],
            'position': sentence['position'],
            'parent': sentence['parent'],
            'raw_text': sentence['raw_text'],
            'labels': law_document_dict_raw['sentence_label'],
            'bow': bow,
            'concept_bow': bow,
            'bow_meanvector': meanvector,
            'concept_vector': meanvector
            }
        
        oov_list = oov_list + sentence_oov_list
        
        parent_id = _get_legal_concept_id(sentence['parent'][0],sentence['parent'][1:])
        new_sentence_property_dict['neighbours'] = [{'neighbour':parent_id, 'type': 'parent'}]
        legal_concepts[parent_id]['neighbours'].append({'neighbour':sentence_id, 'type': 'child'})
        
        legal_concepts[sentence_id] = new_sentence_property_dict
        
    for ref in law_document_dict_raw['internal_ref']:
        ref_from_id = _get_legal_concept_id(ref['ref_from']['name'], ref['ref_from']['parent'])
        try:
            ref_to_id = _get_legal_concept_id(ref['ref_to']['name'], ref['ref_to']['parent'])
        except:
            ref_to_id =  ref['ref_to']['shortName']
        try:
            legal_concepts[ref_to_id]['neighbours'].append({'neighbour':ref_from_id, 'type': 'ref_from'})
            legal_concepts[ref_from_id]['neighbours'].append({'neighbour':ref_to_id, 'type': 'ref_to'})
        except:
            legal_concepts[ref_from_id]['neighbours'].append({'neighbour':ref_to_id, 'type': 'ref_to_UNKNOWN'})
    law_doc_dict = {
        'legal_concepts': legal_concepts,
        'external_ref': law_document_dict_raw['external_ref'],
        'oov_list': oov_list
        }
    
    return law_doc_dict
    
#%% CREATING litra + number + sentence nodes in neo4j      
if __name__ == "__main__":

    
    #funktionærloven
    url = 'https://www.retsinformation.dk/api/document/eli/lta/2017/1002'
    #barselsloven
    url = 'https://www.retsinformation.dk/api/document/eli/lta/2021/235'
    #lov om tidsbegrænset anslttekse
    url = 'https://www.retsinformation.dk/api/document/eli/lta/2008/907'
    
    #Lov
    lov_soup, lov_property_dict, lov_name, lov_shortname = law_property_gen(url)
    
    #Paragraphs
    (paragraph_property_list, chapter_property_list) = paragraph_property_gen(lov_soup, lov_shortname)
    
    # Stk   
    stk_property_list = stk_property_gen(paragraph_property_list)
    
    #Litra, Nr and sentences
    (litra_property_list,
    nr_property_list,
    sentence_property_list) = sentence_litra_nr_property_gen(stk_property_list)
                                                             
    ## References
    stk_internal_ref_query_list, stk_internal_ref_dict_list = stk_internal_references(sentence_property_list)
        
    paragraph_internal_ref_query_list, paragraph_internal_ref_dict_list = paragraph_internal_references(sentence_property_list)

    relative_stk_ref_sets_list = get_relative_ref_sets(sentence_property_list) #only in funktionærloven
    relative_stk_ref_dict_list = get_relative_stk_ref_dict_list(relative_stk_ref_sets_list)    
    
    list_internal_ref_query_list, list_internal_ref_dict_list = list_internal_ref(sentence_property_list) #only in funktionærloven

    (law_internal_paragraph_specific_ref_query_list,
     law_internal_paragraph_specific_ref_dict_list,
     law_external_paragraph_specific_ref_list) = paragraph_specific_references(sentence_property_list, paragraph_property_list)

    internal_ref_to_whole_law_list = internal_ref_to_whole_law(sentence_property_list)
    internal_ref_to_whole_law_dict_list = get_internal_ref_to_whole_law_dict_list(internal_ref_to_whole_law_list, lov_name, lov_shortname)
                                             
    
    #create nodes                                                         
    create_node(lov_label_list, lov_property_dict) # <- CREATING NODE in neo4j
    
    create_chapter_node(chapter_property_list) # <- CREATING NODES in neo4j
    create_paragraph_node(paragraph_property_list) # <- CREATING NODES in neo4j
    
    create_stk_node(stk_property_list) # <- CREATING NODES in neo4j
    
    create_litra_node(litra_property_list) # <- CREATING NODES in neo4j
    create_nr_node(nr_property_list) # <- CREATING NODES in neo4j
    create_sentence_node(sentence_property_list) # <- CREATING NODES in neo4j

    #create relations
    create_stk_internal_ref_relations(stk_internal_ref_query_list)

    create_paragraph_internal_ref_relations(paragraph_internal_references_query_list) #<- CREATING RELATIONS in neo4j
    
    create_relative_stk_ref_relation(relative_stk_ref_sets_list)    

    create_list_internal_ref_relations(list_internal_ref_query_list)

    create_law_internal_ref_relation(law_internal_paragraph_specific_ref_query_list)

    create_internal_ref_to_whole_law_relation(internal_ref_to_whole_law_list)



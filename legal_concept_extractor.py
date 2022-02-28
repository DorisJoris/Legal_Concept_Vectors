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
    lov_html = lov_json['documentHtml']
    lov_soup = bs(lov_html, 'html.parser')
    
    lov_property_dict = {"name":lov_json["popularTitle"],
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


    

def paragraph_sorting_raw(lov_soup):
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


def paragraph_property_gen(paragraphs_raw_dict_list):
    paragraph_property_list = []
    chapter_property_list = []
    p_nr = 0
    ch_nr = 0
    for p_dict in paragraphs_raw_dict_list:
        p = p_dict['paragraph_content']
        p_nr +=1
        name = p[0].find_all(attrs={"class": "ParagrafNr"})[0].string
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
        
        paragraph_html = ''
        paragraph_raw_text = ''
        for tag in p:
            paragraph_html += str(tag)
            paragraph_raw_text += tag.text
        
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
        create_node(paragraph_label_list, paragraph_property_dict)
        
        node1_search_query = f"name: '{paragraph_property_dict['name']}', parent: {paragraph_property_dict['parent']}"
        if len(paragraph_property_dict['parent']) == 1:
            node2_search_query = f"name: '{lov_name}', shortName: '{lov_property_dict['shortName']}'"
        if len(paragraph_property_dict['parent']) == 2:
            node2_search_query = f"name: '{paragraph_property_dict['parent'][0]}', parent: {paragraph_property_dict['parent'][1:]}"
        create_relation(paragraph_label_list[1],node1_search_query,
                        lov_label_list[0],node2_search_query,'part_of')

#%% Extract stk content -> generate paragraph_stk_raw_list
def stk_sorting_raw(paragraphs_raw_dict_list):
    paragraph_stk_raw_dict_list = []
    for p_dict in paragraphs_raw_dict_list:
        p_content = p_dict['paragraph_content']
        p_nr = p_dict['paragraph_id']
        ch_nr = p_dict['chapter_nr']
        stk_nr = 0
        stk_in_paragraph_list = []
        for tag in p_content:
            if tag['class'][0] == 'Paragraf' or tag['class'][0] =='Stk2':
                stk_nr += 1
                stk_in_paragraph_list.append({'stk_content':[],
                                              'stk_nr': stk_nr,
                                              'paragraph_id': p_nr,
                                              'chapter_nr': ch_nr})
            if stk_nr > 0:
                stk_in_paragraph_list[stk_nr-1]['stk_content'].append(tag)
        paragraph_stk_raw_dict_list.append(stk_in_paragraph_list)
    
    return paragraph_stk_raw_dict_list


def stk_property_gen(paragraph_stk_raw_dict_list):
    stk_property_list = []
    for p in paragraph_stk_raw_dict_list:
        p_name = p[0]['stk_content'][0].find_all(attrs={"class": "ParagrafNr"})[0].string
        
        #stk_nr = 0
        for stk in p:
            stk_nr = stk['stk_nr']
            name = f'Stk. {stk_nr}.'
            stk_html = ''
            stk_raw_text = ''
            for tag in stk['stk_content']:
                stk_html += str(tag)
                stk_raw_text += tag.text
            
            if stk['chapter_nr']>0:
                parents = [p_name, f"Kapitel {stk['chapter_nr']}", lov_shortname]
            else:
                parents = [p_name, lov_shortname]
            
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
    
    # "."-exeptions
    exeptions_list = abbreviations
    
    month_list = ["januar", "februar", "marts", "april", "maj", "juni",
             "juli", "august", "september", "oktober", "november", "december"]
    
    for i in range(0,10):
        for month in month_list:
            date = f"{i}. {month}"
            replacement = f"{i}%% {month}"
            tag_raw_text = tag_raw_text.replace(date,replacement)
    
    for exeption in exeptions_list:
        tag_raw_text = tag_raw_text.replace(exeption[0],exeption[1])
    
    re.findall("pkt[(%%)] [A-Z]",)
    
    pkt_instances = []
    pkt_instances = pkt_instances + re.findall("[0-9]. pkt", tag_raw_text)
    pkt_instances = pkt_instances + re.findall("[0-9]. og [0-9]", tag_raw_text)
    pkt_instances = pkt_instances + re.findall("[0-9]., [0-9]", tag_raw_text)
    
    number_instances = re.findall("[0-9]. ", tag_raw_text)
    pkt_instances = pkt_instances + number_instances
    
    pkt_replacements = []
    for instance in pkt_instances:
        pkt_replacements.append(instance.replace('.','%%'))
    
    for i in range(0,len(pkt_replacements)):
        tag_raw_text = tag_raw_text.replace(pkt_instances[i],pkt_replacements[i])
    
    # reversing "."-exeptions after split
    sentence_property_list = []
    sentence_count = 0
    while tag_raw_text.find('.') > 0:
        sentence_text = tag_raw_text[0:tag_raw_text.find('.')+1]
        for exeption in exeptions_list:
            sentence_text = sentence_text.replace(exeption[1],exeption[0])
        
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
                                 'raw_text': sentence_text,
                                 'parent': parents
                                 }
        sentence_property_list.append(sentence_property_dict)
        
    if tag_raw_text.find('.') == -1 and len(tag_raw_text)>0:
        sentence_text = tag_raw_text
        for exeption in exeptions_list:
            sentence_text = sentence_text.replace(exeption[1],exeption[0])
        
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
                                 'raw_text': sentence_text,
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

def sentence_litra_nr_property_gen(paragraph_stk_raw_dict_list):
    litra_property_list = []
    nr_property_list = []
    sentence_property_list = []
    
    for p in paragraph_stk_raw_dict_list:
        p_name = p[0]['stk_content'][0].find_all(attrs={"class": "ParagrafNr"})[0].string
        #stk_nr = 0
        
        for stk in p:
            stk_nr = stk['stk_nr']
            stk_name = f'Stk. {stk_nr}.'
            tag_position = 0
            
            if stk['chapter_nr']>0:
                parents = [stk_name, p_name, f"Kapitel {stk['chapter_nr']}", lov_shortname]
            else:
                parents = [stk_name, p_name, lov_shortname]
            
            for tag in stk['stk_content']:
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
                    
                    new_sentence_property_list = _sentence_property_gen(tag, parents, tag_position)
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
        p1 = re.search('[0-9]., [0-9]. og [0-9]. pkt.', text)
        p2 = re.search('[0-9]. og [0-9]. pkt.', text)
        p3 = re.search('[0-9]. pkt.', text)
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

def _get_stk_internal_ref_query(sentence_property_dict, sentence_list_ref):
    stk_internal_ref_query = []
    for ref in sentence_list_ref:
        stk_internal_ref_query.append(_stk_internal_query(ref, sentence_property_dict))
    return stk_internal_ref_query

def stk_internal_references(sentence_property_list):
    stk_internal_ref_query_list = [] 
    for sentence_property_dict in sentence_property_list:
        text = " " + sentence_property_dict['raw_text'].lower()
        sentence_pkt_ref_numbers = _get_sentence_pkt_ref_numbers(text)
        sentence_querys = _get_stk_internal_ref_query(sentence_property_dict, sentence_pkt_ref_numbers)
        stk_internal_ref_query_list = stk_internal_ref_query_list + sentence_querys
    return stk_internal_ref_query_list

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

def _internal_stk_nr_query(stk, nr, sentence_property_dict):
    node1_search_query = f"name: '{sentence_property_dict['name']}', parent: {sentence_property_dict['parent']}"
    parent_filter = [(sentence_property_dict['parent'].index(x)) for x in sentence_property_dict['parent'] if x.find('§') == 0][0]
    node2_parent_list = [f"Stk. {stk}."] + sentence_property_dict['parent'][parent_filter:]
    node2_search_query = f"name: '{nr})', parent: {node2_parent_list}"
    return [node1_search_query, node2_search_query]

def _internal_stk_pkt_query(ref, sentence_property_dict):
    stk = ref[0:ref.find(',')]
    pkt = ref[ref.find(',')+1:]
    node1_search_query = f"name: '{sentence_property_dict['name']}', parent: {sentence_property_dict['parent']}"
    parent_filter = [(sentence_property_dict['parent'].index(x)) for x in sentence_property_dict['parent'] if x.find('§') == 0][0]
    node2_parent_list = [f"Stk. {stk}."] + sentence_property_dict['parent'][parent_filter:]
    node2_search_query = f"name: '{pkt}. pkt.', parent: {node2_parent_list}"
    return [node1_search_query, node2_search_query]
    
def _get_paragraph_internal_ref_query(sentence_property_dict, sentence_stk_ref_numbers):
    sentence_internal_ref_query = []
    for ref in sentence_stk_ref_numbers:
        if type(ref) == str:
            if ',' in ref:
                sentence_internal_ref_query.append(_internal_stk_pkt_query(ref, sentence_property_dict))    
            else:
                sentence_internal_ref_query.append(_internal_stk_query(ref, sentence_property_dict))
        elif type(ref) == list:
            if ref[1].isnumeric():
                for nr in ref[1:]:
                    sentence_internal_ref_query.append(_internal_stk_nr_query(ref[0], nr, sentence_property_dict))
    return sentence_internal_ref_query                 

def paragraph_internal_references(sentence_property_list):
    paragraph_internal_ref_query_list = [] 
    for sentence_property_dict in sentence_property_list:
        text = " " + sentence_property_dict['raw_text'].lower()
        sentence_stk_ref_numbers = _get_sentence_stk_ref_numbers(text)
        sentence_querys = _get_paragraph_internal_ref_query(sentence_property_dict, sentence_stk_ref_numbers)
        paragraph_internal_ref_query_list = paragraph_internal_ref_query_list + sentence_querys
    return paragraph_internal_ref_query_list
                

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

def _get_list_internal_ref_query(sentence_property_dict, sentence_list_ref):
    list_internal_ref_query = []
    for ref in sentence_list_ref:
        list_internal_ref_query.append(_list_internal_query(ref, sentence_property_dict))
    return list_internal_ref_query

def list_internal_ref(sentence_property_list):
    list_internal_ref_query_list = []
    sentence_list_ref = []
    for sentence_property_dict in sentence_property_list:
        if sentence_property_dict['parent'][0].find(')') == 1:
            text = " " + sentence_property_dict['raw_text'].lower()
            if sentence_property_dict['parent'][0][0].isalpha():
                sentence_list_ref = _get_sentence_ref_litra(text)
            elif sentence_property_dict['parent'][0][0].isnumeric():
                sentence_list_ref = _get_sentence_ref_number(text)
            if len(sentence_list_ref)>0:
                sentence_querys = _get_list_internal_ref_query(sentence_property_dict, sentence_list_ref)
                list_internal_ref_query_list = list_internal_ref_query_list + sentence_querys
        else:
            continue
        
    return list_internal_ref_query_list
        
                    
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
               
#%% Law interal specific references. References across the different paragraphs to specific paragraphs

## get law internal single ref
def _get_law_int_spec_stk_ref(text):
    stk_list = []
    stk ='Stk. '
    for j in range(0,len(text)):
        if text[j].isnumeric():
            stk = stk + text[j]
        elif text[j] == ',': 
            stk = stk +'.'
            if stk[-2].isnumeric():
                stk_list.append(stk)
            stk = 'Stk. '
            continue
        elif text[j:j+4] == ' og ':
            stk = stk +'.'
            stk_list.append(stk)
            stk = 'Stk. '
            for letter in text[j+4:]:
                if letter.isnumeric():
                    stk = stk + letter
                else:
                    stk = stk +'.'
                    stk_list.append(stk)
                    break
        elif text[j] == ' ':
            continue
        else:
            stk = stk +'.'
            if stk[-2].isnumeric():
                stk_list.append(stk)
            break  
    return stk_list              

def _get_single_law_int_spec_ref(p, text):
    single_ref = []
    paragraph_nr = '§\xa0'
    search_text = text[p+2:]
    for i in range(0,len(search_text)):
        if search_text[i].isnumeric():
            paragraph_nr = paragraph_nr + search_text[i]
        elif search_text[i] == ' ':
            continue
        elif search_text[i].isalpha() and search_text[i+1].isalnum() == False:
            paragraph_nr = paragraph_nr + ' ' + search_text[i]
        elif search_text[i] == ',':
            if search_text[i+1:i+1+6] == ' stk.\xa0':
                paragraph_nr = paragraph_nr + '.'
                single_ref.append(paragraph_nr)
                single_ref.append(_get_law_int_spec_stk_ref(search_text[i+1+6:]))
                break
            else:
                paragraph_nr = paragraph_nr + '.'
                single_ref.append(paragraph_nr)
                break
        else:
            paragraph_nr = paragraph_nr + '.'
            single_ref.append(paragraph_nr)
            break
    return single_ref


## Get continuous list of ref
def _get_continuous_law_int_spec_ref(p, text, paragraph_property_list):
    start_p_nr = '§\xa0'
    is_start = True
    end_p_nr = '§\xa0'
    not_continuous = False
    search_text = text[p+3:]
    for i in range(0,len(search_text)):
        if search_text[i].isnumeric() and is_start == True:
            start_p_nr = start_p_nr + search_text[i]
        elif search_text[i].isnumeric() and is_start == False:
            end_p_nr = end_p_nr + search_text[i]
        elif search_text[i] =='-':
            start_p_nr = start_p_nr + '.'
            is_start = False
        else:
            if is_start == True:
               not_continuous = True 
            end_p_nr = end_p_nr + '.'
            break
    
    if not_continuous == True:
        return []
    if not_continuous == False:
        paragraph_ref_list = []
        for paragraph_dict in paragraph_property_list:
            
            if paragraph_dict['name'] == start_p_nr:
                start_position = paragraph_dict['position']            
            elif paragraph_dict['name'] == end_p_nr:
                end_position = paragraph_dict['position']
                break
            
        for paragraph_dict in paragraph_property_list:
            
            if paragraph_dict['position'] >= start_position and paragraph_dict['position'] <= end_position:
                paragraph_ref_list.append([paragraph_dict['name']])
             
        return paragraph_ref_list
    

## Noncontinuous list of ref.    
def _get_noncontinuous_law_int_spec__single_ref(text):
    single_ref = []
    paragraph_nr = '§\xa0'
    for j in range(0,len(text)):
        final_j = j
        if text[j].isnumeric():
            paragraph_nr = paragraph_nr + text[j]
        elif text[j] == '-':
            single_ref = []
            break
        elif text[j] == ' ':
            continue
        elif text[j].isalpha() and text[j+1].isalnum() == False:
            paragraph_nr = paragraph_nr + ' ' + text[j]
        elif text[j] == ',':
            if text[j+1:j+1+6] == ' stk.\xa0':
                stk_search_text = text[j+1+6:]
                paragraph_nr = paragraph_nr + '.'
                single_ref.append(paragraph_nr)
                stk_list = []
                stk ='Stk. '
                for s in range(0,len(stk_search_text)):
                    if stk_search_text[s].isnumeric():
                        stk = stk + stk_search_text[s]
                    elif stk_search_text[s] == ',': 
                        stk = stk +'.'
                        if stk[-2].isnumeric():
                            stk_list.append(stk)
                        stk = 'Stk. '
                        continue
                    elif stk_search_text[s:s+4] == ' og ':
                        stk = stk +'.'
                        stk_list.append(stk)
                        stk = 'Stk. '
                        t = 0
                        for letter in stk_search_text[s+4:]:
                            t += 1
                            if letter.isnumeric():
                                stk = stk + letter
                            else:
                                stk = stk +'.'
                                stk_list.append(stk)
                                break
                        
                        final_j += s + 4 + t
                        break
                    elif stk_search_text[s] == ' ':
                        continue
                    else:
                        stk = stk +'.'
                        if stk[-2].isnumeric():
                            stk_list.append(stk)
                        final_j += s
                        break
                single_ref.append(stk_list)
                break
            else:
                paragraph_nr = paragraph_nr + '.'
                single_ref.append(paragraph_nr)
                break
        else:
            paragraph_nr = paragraph_nr + '.'
            single_ref.append(paragraph_nr)
            break
    return (single_ref, final_j)

def _get_noncontinuous_law_int_spec_ref(p, text):
    noncontinuous_ref_list = []
    state = 'continue'
    search_text = text[p+3:]
    i = -1
    while state == 'continue':
        i += 1
        if i > len(search_text)-1:
            break
        elif search_text[i].isnumeric():
            (individual_ref, j)  = _get_noncontinuous_law_int_spec__single_ref(search_text[i:])
            if len(individual_ref) == 0:
                noncontinuous_ref_list = []
                state = 'break'
                break   
            i += j
            noncontinuous_ref_list.append(individual_ref)
            continue
        elif search_text[i] == ',':
            continue
        elif search_text[i] == 'g' and search_text[i+2].isnumeric():
            continue
        elif search_text[i] == ' ':
            continue
        else:
            state = 'break'
            break
   
    return noncontinuous_ref_list 
    

## Law internal refs
# Test for external refs
def _test_for_external_ref_prior_paragraph_sign(p, text):
    n_spaces = []
    for i in range(1,p):
        if text[p-i] == ' ':
            n_spaces.append(p-i)
        if len(n_spaces) == 2:
            break
    if len(n_spaces) < 2:
        return False
    elif ' lovens ' not in text[n_spaces[1]:n_spaces[0]+1] and 'lovens ' in text[n_spaces[1]:n_spaces[0]+1]:
        return True
    elif ' i lov om' in text[p+1:]:
        return True
    else:
        return False

# Get the law internal specific refs    
def _get_law_internal_specific_ref(p, text, paragraph_property_list):
    law_internal_spec_ref_list = []
    if text[p-1:p+2] == ' §\xa0' and text[p+2].isnumeric():
        single_ref = _get_single_law_int_spec_ref(p, text)
        law_internal_spec_ref_list.append(single_ref)
    
    elif text[p-1:p+3] == ' §§\xa0' and text[p+3].isnumeric():
        continuous_law_int_spec_ref_list = _get_continuous_law_int_spec_ref(p, text, paragraph_property_list)
        if  len(continuous_law_int_spec_ref_list) >0:
            law_internal_spec_ref_list = law_internal_spec_ref_list + continuous_law_int_spec_ref_list
        
        noncontinuous_law_int_spec_ref_list = _get_noncontinuous_law_int_spec_ref(p, text)
        
        if len(noncontinuous_law_int_spec_ref_list) >0:
            law_internal_spec_ref_list = law_internal_spec_ref_list + noncontinuous_law_int_spec_ref_list
            
    return law_internal_spec_ref_list
  
        
# Get the law internal refs in every sentence
def _get_law_internal_ref_query(sentence_property_dict, ref_name, ref_parent):
    node1_search_query = f"name: '{sentence_property_dict['name']}', parent: {sentence_property_dict['parent']}"
    node2_search_query = f"name: '{ref_name}', parent: {ref_parent}"
    return [node1_search_query, node2_search_query]


def _get_sentence_ref_list(text, paragraph_property_list):
    text = text.replace(' stk. ', ' stk.\xa0')
    sentence_ref_list = []
    while text.find('§') != -1:
        p = text.find('§')
        if _test_for_external_ref_prior_paragraph_sign(p, text) == True:
            text = text[p+2:]
        else:
            sentence_ref_list = _get_law_internal_specific_ref(p, text, paragraph_property_list)
            text = text[p+2:]
    return sentence_ref_list
            
def law_internal_references(sentence_property_list, paragraph_property_list):
    law_internal_ref_query_list = []
    for sentence_property_dict in sentence_property_list:
        text = " " + sentence_property_dict['raw_text'].lower()
        sentence_ref_list = _get_sentence_ref_list(text, paragraph_property_list)
        for ref in sentence_ref_list:
            if len(ref) == 0:
                continue
            elif len(ref) == 1:
                ref_name = ref[0]
                ref_parent = sentence_property_dict['parent'][-1:]
                ref_query = _get_law_internal_ref_query(sentence_property_dict, ref_name, ref_parent)
                law_internal_ref_query_list.append(ref_query)
            elif len(ref) > 1:
                for stk in ref[1]:
                    ref_name = stk
                    ref_parent =[ref[0],sentence_property_dict['parent'][-1]]
                    ref_query = _get_law_internal_ref_query(sentence_property_dict, ref_name, ref_parent)
                    law_internal_ref_query_list.append(ref_query)
                    
    return law_internal_ref_query_list
            
def create_law_internal_ref_relation(law_internal_ref_query_list):
    for law_internal_ref_set in law_internal_ref_query_list:
            create_relation(sentence_label_list[0],law_internal_ref_set[0],
                sentence_label_list[0],law_internal_ref_set[1],
                            'refers_to')            
        
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
 
def create_internal_ref_to_whole_law_relation(internal_ref_to_whole_law_list):
    for internal_ref_to_whole_law in internal_ref_to_whole_law_list:
            node1_search_query = f"name: '{internal_ref_to_whole_law[0]}', parent: {internal_ref_to_whole_law[1]}"
            node2_search_query = f"name: '{lov_name}', shortName: '{lov_shortname}'"
            create_relation(sentence_label_list[0],node1_search_query,
                sentence_label_list[0],node2_search_query,
                            'refers_to')               
        
#%% CREATING litra + number + sentence nodes in neo4j      
if __name__ == "__main__":
    
    #funktionærloven
    url = 'https://www.retsinformation.dk/api/document/eli/lta/2017/1002'
    #barselsloven
    url = 'https://www.retsinformation.dk/api/document/eli/lta/2021/235'
    
    #Lov
    lov_soup, lov_property_dict, lov_name, lov_shortname = law_property_gen(url)
    
    create_node(lov_label_list, lov_property_dict) # <- CREATING NODE in neo4j
    
    #Paragraphs
    paragraphs_raw_dict_list = paragraph_sorting_raw(lov_soup) 
    (paragraph_property_list, chapter_property_list) = paragraph_property_gen(paragraphs_raw_dict_list)
    
    create_chapter_node(chapter_property_list) # <- CREATING NODES in neo4j
    create_paragraph_node(paragraph_property_list) # <- CREATING NODES in neo4j
    
    # Stk
    paragraph_stk_raw_dict_list =  stk_sorting_raw(paragraphs_raw_dict_list)   
    stk_property_list = stk_property_gen(paragraph_stk_raw_dict_list)
    
    create_stk_node(stk_property_list) # <- CREATING NODES in neo4j
    
    #Litra, Nr and sentences
    (litra_property_list,
    nr_property_list,
    sentence_property_list) = sentence_litra_nr_property_gen(paragraph_stk_raw_dict_list)
    
    create_litra_node(litra_property_list) # <- CREATING NODES in neo4j
    create_nr_node(nr_property_list) # <- CREATING NODES in neo4j
    create_sentence_node(sentence_property_list) # <- CREATING NODES in neo4j

    
    ## References
    stk_internal_ref_query_list = stk_internal_references(sentence_property_list)
    
    paragraph_internal_references_query_list = paragraph_internal_references(sentence_property_list)

    create_paragraph_internal_ref_relations(paragraph_internal_references_query_list) #<- CREATING RELATIONS in neo4j

    relative_stk_ref_sets_list = get_relative_ref_sets(sentence_property_list)
    
    create_relative_stk_ref_relation(relative_stk_ref_sets_list)
    
    list_internal_ref_query_list = list_internal_ref(sentence_property_list)

    create_list_internal_ref_relations(list_internal_ref_query_list)

    law_internal_ref_query_list = law_internal_references(sentence_property_list, paragraph_property_list)
    
    create_law_internal_ref_relation(law_internal_ref_query_list)

    internal_ref_to_whole_law_list = internal_ref_to_whole_law(sentence_property_list)

    create_internal_ref_to_whole_law_relation(internal_ref_to_whole_law_list)



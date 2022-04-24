# -*- coding: utf-8 -*-
"""
Created on Sun Apr 10 11:29:55 2022

@author: bejob
"""

# This is the legal concept extraction code for LOV documents from retsinfomrationen.dk
#%% Import

import copy
import re


from legal_concept_resources import abbreviations

from bs4 import BeautifulSoup as bs

#%% Create lov node
# This function takes the url, in this case: 
    # https://www.retsinformation.dk/api/document/eli/lta/2017/1002
# to request a json-file containing some meta information about the law
# and the text of the law in a html-format.
# The funktion continues to generate a dictionary of the properties for the law that will
# be saved to the database. 

def law_property_gen(lov_json):
    lov_html = lov_json['documentHtml']
    full_soup = bs(lov_html, 'html.parser')
    
    lov_soup = full_soup.find(id='INDHOLD')
    
        
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
                        'html':str(lov_soup),
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

 
    

def _paragraph_sorting_raw(soup, ch_nr, ch_name, p_nr):
    para_tags = soup.select('div[class="PARAGRAF"]')
    paragraphs_raw_dict_list = []
    for tag in para_tags:
        p_nr += 1
        paragraphs_raw_dict_list.append({'paragraph_content': tag,
                                         'paragraph_id': p_nr,
                                         'chapter_nr': ch_nr,
                                         'chapter_name': ch_name})
    return paragraphs_raw_dict_list, p_nr

       
def paragraph_property_gen(lov_soup, lov_shortname):
    chapter_soups = lov_soup.select('div[class="KAPITEL"]')
    
    paragraph_property_list = []
    chapter_property_list = []
    p_nr = 0
    ch_nr = 0
    if len(chapter_soups) > 0:
        paragraphs_raw_dict_list = []
        for chapter_soup in chapter_soups:
            ch_nr += 1
            ch_name = chapter_soup.select('p[class="Kapiteloverskrift"]')[0].string
            chapter_property_dict = {'name': f"Kapitel {ch_nr}",
                                     'shortName': ch_name,
                                     'position': ch_nr,
                                     'parent': [lov_shortname]
                                     }
            chapter_property_list.append(chapter_property_dict)
            ch_paragraphs_raw_dict_list, p_nr = _paragraph_sorting_raw(chapter_soup, ch_nr, ch_name, p_nr)
            paragraphs_raw_dict_list = paragraphs_raw_dict_list + ch_paragraphs_raw_dict_list
    else:
        paragraphs_raw_dict_list, p_nr = _paragraph_sorting_raw(lov_soup, ch_nr, ch_name, p_nr)
    
    for p_dict in paragraphs_raw_dict_list:
        p = p_dict['paragraph_content']
        p_nr +=1
        p_name_str = p.select('p[class="Paragraftekst"]')[0].select('b')[0].string
        p_name_start = p_name_str.find('§')
        p_name_end = p_name_str.find('.')+1
        name = p_name_str[p_name_start:p_name_end].replace('§ ', '§\xa0')
        if p_dict['chapter_nr']>0:
            parents = [f"Kapitel {p_dict['chapter_nr']}", lov_shortname]
        else:
            parents = [lov_shortname]
        
        paragraph_html = str(p).replace('\r','').replace('\n','').replace('\t','')
        paragraph_raw_text = p.text.replace('\r','').replace('\n','').replace('\t','')
        while paragraph_html.find('  ') > 0:
            paragraph_html = paragraph_html.replace('  ',' ')
            paragraph_raw_text = paragraph_raw_text.replace('  ',' ')
        
        p_property_dict = {'name': name, 
                           'position':p_nr,
                           'html':paragraph_html,
                           'raw_text':paragraph_raw_text,
                           'parent': parents
                           }
            
        paragraph_property_list.append(p_property_dict)
        
    return (paragraph_property_list, chapter_property_list)

#%% Extract stk content -> generate paragraph_stk_raw_list
def _stk_sorting_raw(paragraph_property_list):
    paragraph_stk_raw_dict_list = []
    for p_dict in paragraph_property_list:
        p_content = bs(p_dict['html'], 'html.parser')
        stk_parent = [p_dict['name']] + p_dict['parent']
        stk_nr = 0
        stk_in_paragraph_list = []
        for tag in p_content.select('p'):
            if tag['class'][0] == 'Paragraftekst' or tag['class'][0] =='Stk':
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
                stk_raw_text += tag.text.replace('\r','').replace('\n','')
            
            stk_property_dict = {'name': name, 
                                 'position':stk_nr,
                                 'html':stk_html,
                                 'raw_text':stk_raw_text,
                                 'parent': parents
                                 }
            stk_property_list.append(stk_property_dict)
    return stk_property_list

    
#%% Litra, Nr and sentence nodes        
        
def _sentence_property_gen(raw_text, parents, tag_position):
    tag_raw_text = copy.copy(raw_text)
    
    
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
                                 'position':tag_position-1+sentence_count,
                                 'html': '',
                                 'raw_text': sentence_text.replace(' \n','').replace('\n',''),
                                 'parent': parents
                                 }
        
        
        sentence_property_list.append(sentence_property_dict)
        
    if tag_raw_text.find('.') == -1 and len(tag_raw_text)>0 and tag_raw_text != ' ':
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
    if tag['class'][0] == 'Aendringspunkt':
        if tag.b != None:
            tag.b.unwrap()
        if tag.span != None:
            tag.span.unwrap()
        tag_html = str(tag)
        tag_raw_text = tag.text[tag.text.find('.')+1:]
        name = tag.text[0:tag.text.find('.')].replace(' ','')+')'
    else:
        if tag.i != None:
            tag.i.extract()
        if tag.b != None:
            tag.b.extract()
        tag_html = str(tag)
        tag_raw_text = tag.text[tag.text.find(')')+1:]
        name = tag.text[0:tag.text.find(')')+1].replace(' ','')
    tag_property_dict = {'name': name, 
                         'position':tag_position,
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
            tag_position += 1
            if tag['class'][0] == 'Nummer' or tag['class'][0] == 'Litra' or tag['class'][0] == 'Aendringspunkt':
                tag_property_dict = _litra_nr_property_gen(tag, 
                                                           parents, 
                                                           tag_position)
                
                if tag_property_dict['name'][0:-1].isnumeric():
                    nr_property_list.append(tag_property_dict)
                else:
                    litra_property_list.append(tag_property_dict)
                    
                parent_list = [tag_property_dict['name']] + parents    
                new_sentence_property_list = _sentence_property_gen(tag_property_dict['raw_text'], parent_list, 1)
                sentence_property_list = sentence_property_list + new_sentence_property_list
                
            else:
                if tag.i != None:
                    tag.i.extract()
                if tag.b != None:
                    tag.b.extract()
                raw_text = tag.text
                new_sentence_property_list = _sentence_property_gen(raw_text,
                                                                    parents, 
                                                                    tag_position)
                sentence_property_list = sentence_property_list + new_sentence_property_list
                tag_position += len(new_sentence_property_list)

    return (litra_property_list,
            nr_property_list,
            sentence_property_list)

# -*- coding: utf-8 -*-
"""
Created on Sun Apr 10 11:32:06 2022

@author: bejob
"""
# This is the legal concept extraction code for LBK documents from retsinfomrationen.dk
#%% Import
import copy
import re
import urllib.request
import json
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
    lov_html_end = lov_json['documentHtml'].find('<hr class="IKraftStreg">')
    lov_html = lov_json['documentHtml'][0:lov_html_end]
    lov_soup = bs(lov_html, 'html.parser')
    
    for p in lov_soup.find_all("p",attrs={'class':'TekstGenerel'}):
        p.unwrap()
    
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
                        'html':lov_html}#,
                        #'raw_text':lov_soup.text}
    
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
    section_nr = 0
    section_name = ''
    ch_nr = 0
    ch_name = ''
    for p in pees:
        if p['class'][0] == 'IkraftTekst':
            break
        if p['class'][0] == 'Givet':
            break
        if p['class'][0] == 'Afsnit':
            section_nr += 1
            continue
        if p['class'][0] == 'AfsnitOverskrift':
            section_name = p.text
            continue
        if p['class'][0] == 'Kapitel':
            ch_nr += 1
            continue
        if p['class'][0] == 'KapitelOverskrift2':
            ch_name = p.text
            continue
        if p['class'][0] == 'ParagrafGruppeOverskrift':
            continue
        if p['class'][0] == 'Tekst2':
            continue
        if p['class'][0] == 'Paragraf':
            p_nr += 1
            paragraphs_raw_dict_list.append({'paragraph_content':[],
                                             'paragraph_id': p_nr,
                                             'section_nr': section_nr,
                                             'section_name': section_name,
                                             'chapter_nr': ch_nr,
                                             'chapter_name': ch_name})
        if p_nr > 0:
            paragraphs_raw_dict_list[p_nr-1]['paragraph_content'].append(p)
    return paragraphs_raw_dict_list


def paragraph_property_gen(lov_soup, lov_shortname):
    paragraphs_raw_dict_list = _paragraph_sorting_raw(lov_soup)
    paragraph_property_list = []
    section_property_list = []
    chapter_property_list = []
    p_nr = 0
    section_nr = 0
    ch_nr = 0
    for p_dict in paragraphs_raw_dict_list:
        p = p_dict['paragraph_content']
        p_nr +=1
        name = p[0].find_all(attrs={"class": "ParagrafNr"})[0].string.replace('§ ', '§\xa0')
        if p_dict['section_nr']>0:
            parents = [f"Afsnit {p_dict['section_nr']}", lov_shortname]
            if section_nr != p_dict['section_nr']:
                section_nr = p_dict['section_nr']
                section_property_dict = {'name': f"Afsnit {p_dict['section_nr']}",
                                         'shortName': p_dict['section_name'],
                                         'position': p_dict['section_nr'],
                                         'parent': [lov_shortname]
                                         }
                section_property_list.append(section_property_dict)
            if p_dict['chapter_nr']>0:
                if ch_nr != p_dict['chapter_nr']:
                    ch_nr = p_dict['chapter_nr']
                    chapter_property_dict = {'name': f"Kapitel {p_dict['chapter_nr']}",
                                             'shortName': p_dict['chapter_name'],
                                             'position': p_dict['chapter_nr'],
                                             'parent': parents
                                             }
                    chapter_property_list.append(chapter_property_dict)
                parents = [f"Kapitel {p_dict['chapter_nr']}"] + parents
        else:
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
                                       #'raw_text':paragraph_raw_text,
                                       'parent': parents
                                       }
                    paragraph_property_list.append(p_property_dict)
                    p_nr += 1
        else: 
            p_property_dict = {'name': name, 
                               'position':p_nr,
                               'html':paragraph_html,
                               #'raw_text':paragraph_raw_text,
                               'parent': parents
                               }
            
            paragraph_property_list.append(p_property_dict)
    return (paragraph_property_list, chapter_property_list, section_property_list)

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
                                 #'raw_text':stk_raw_text,
                                 'parent': parents
                                 }
            stk_property_list.append(stk_property_dict)
    return stk_property_list

    
#%% Litra, Nr and sentence nodes        
        
def _sentence_property_gen(tag, parents, tag_position):
    local_tag = copy.copy(tag)
    
    for span in local_tag.select('span'):
        span.extract()
    
    tag_raw_text = " " + local_tag.text
    
    #just to fix a typo in §193 stk. 5 in lov om investeringsforeninger m.v.
    tag_raw_text = tag_raw_text.replace("ophæves den 22. juli. 2014.", "ophæves den 22. juli 2014.")
    
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
    
    number_instances = re.findall("[0-9]\.", tag_raw_text)
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
        #if len(sentence_text.replace(' ','')) == 0:
        #    print(f"{parents}")
        if len(sentence_property_dict['raw_text']) == 0:
            print(parents)
            print(tag.text)
            print("----------------------------")
        sentence_property_list.append(sentence_property_dict)
    return sentence_property_list


def _litra_nr_property_gen(tag, parents, tag_position):
    tag_html = str(tag)
    #tag_raw_text = tag.text
    name = tag.find('span', attrs={'class': 'Liste1Nr'}).text
    tag_property_dict = {'name': name, 
                         'position':tag_position+1,
                         'html':tag_html,
                         #'raw_text':tag_raw_text,
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


#%% test App
if __name__ == "__main__":
    url = 'https://www.retsinformation.dk/api/document/eli/lta/2022/406'
    
    with urllib.request.urlopen(url) as page:
        data = json.loads(page.read().decode())
    
    lov_json = data[0]
    
    lov_soup, lov_property_dict, lov_name, lov_shortname = law_property_gen(lov_json)

    (paragraph_property_list, chapter_property_list, section_property_list) = paragraph_property_gen(lov_soup, lov_shortname)
    
    stk_property_list = stk_property_gen(paragraph_property_list)
    
    (litra_property_list,
    nr_property_list,
    sentence_property_list) = sentence_litra_nr_property_gen(stk_property_list)
    
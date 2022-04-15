# -*- coding: utf-8 -*-
#%% Import

import re

from legal_concept_resources import internal_ref_to_whole_law_cues
from legal_concept_resources import relative_stk_ref_cues
from legal_concept_resources import external_reference_cues



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
        if ref_cue[0].lower() in text.lower():
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
        search_text_external = search_text_external.replace(f', i{external_ref_cue[0]}',f'@@ i{external_ref_cue[0]}') 
    search_text_external_split = re.split(',| efter | sammenholdt med ', search_text_external)
    
    for ref in potentially_external_ref_list:
        test_ref_string = ref['ref_string'].replace(',','@@')
        external = False
        for text_ex in search_text_external_split:
            if test_ref_string in text_ex:
                for external_ref_cue in external_refs_present:
                    if external_ref_cue[0].lower() in text_ex.lower():
                        ref['parent_law'] = external_ref_cue[1] if len(external_ref_cue[1]) >0 else external_ref_cue[0]
                        
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
    return sentence_paragraph_specific_ref_list 


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
         
        
#%% References to the law as a whole.             

def ref_to_whole_law(sentence_property_list, law_external_paragraph_specific_ref_list):
    internal_ref_to_whole_law_list = []
    output_law_external_paragraph_specific_ref_list = law_external_paragraph_specific_ref_list
    for sentence_property_dict in sentence_property_list:
        text = " " + sentence_property_dict['raw_text'].lower()
        for cue in internal_ref_to_whole_law_cues:
            if text.find(cue) > -1:
                internal_ref_to_whole_law_list.append([sentence_property_dict['name'], sentence_property_dict['parent']])
                break
        for ex_cue in external_reference_cues:
            if text.find(ex_cue[0]) > -1:
                candidat = sentence_property_dict
                already_listed = False
                for ex_ref in law_external_paragraph_specific_ref_list:
                    if candidat == ex_ref[0]:
                        already_listed = True
                        break
                if already_listed is False:
                    ref_instance = {'p_ref_list':[], 
                                    'parent_law': ex_cue[1],
                                    'ref_string': ex_cue[0],
                                    'ref_type': 'law'}
                    output_law_external_paragraph_specific_ref_list.append((candidat, ref_instance))
    return internal_ref_to_whole_law_list, output_law_external_paragraph_specific_ref_list

def get_internal_ref_to_whole_law_dict_list(internal_ref_to_whole_law_list, lov_name, lov_shortname):
    internal_ref_to_whole_law_dict_list = []
    for internal_ref_to_whole_law in internal_ref_to_whole_law_list:
            ref_from = {'name': internal_ref_to_whole_law[0], 'parent': internal_ref_to_whole_law[1]}
            ref_to = {'name': lov_name, 'shortName': lov_shortname}
            ref_dict = {'ref_type': 'law_internal', 'ref_from': ref_from, 'ref_to': ref_to}
            internal_ref_to_whole_law_dict_list.append(ref_dict)
    return internal_ref_to_whole_law_dict_list
    
              


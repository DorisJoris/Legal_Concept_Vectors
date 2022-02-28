# -*- coding: utf-8 -*-
"""
Created on Sun Feb  6 15:06:01 2022

@author: bejob
"""

from neo4j import GraphDatabase
import logging
from neo4j.exceptions import ServiceUnavailable

class _RetsGraphPopulator:
    
    def __init__(self, uri, user, password):
        auth = (user, password)
        self.driver = GraphDatabase.driver(uri, auth=auth)
        
    def _close(self):
        self.driver.close()
        
    def _create_node(self, label_list, property_dict):
        with self.driver.session() as session:
            label_string = self._get_label_string(label_list)
            property_string = self._get_property_string(property_dict)
            session.write_transaction(
                self._create_node_tx, label_string, property_string)
            
    @staticmethod
    def _create_node_tx(tx, label_string, property_string):
            query = f'CREATE (n{label_string} {property_string})'
            tx.run(query, 
                   label_string=label_string, 
                   property_string=property_string)
            
    @staticmethod
    def _get_label_string(label_list):
        label_string =''
        for label in label_list:
            label_string = f"{label_string}:{label}"
        return label_string

    @staticmethod
    def _get_property_string(property_dict):
        property_string = ''
        for key in property_dict:
            if type(property_dict[key]) is list:
                property_string = f"{property_string},{key}: {property_dict[key]}"
            else:
                property_string = f"{property_string},{key}: '{property_dict[key]}'"
        return f"{{ {property_string[1:]} }}"
    
    def _create_relation(self, node1_label, node1_name, 
                            node2_label, node2_name, relation_label):
        with self.driver.session() as session:
            session.write_transaction(
                self._create_relation_tx, node1_label, node1_name, 
                                        node2_label, node2_name, relation_label)
    
    @staticmethod
    def _create_relation_tx(tx, 
                            node1_label, node1_search_query,
                            node2_label, node2_search_query,
                            relation_label):
        query = (
            f"MATCH (a:{node1_label} {{ {node1_search_query} }}) "
            f"MATCH (b:{node2_label} {{ {node2_search_query} }}) "
            f"CREATE (a)-[:{relation_label}]->(b) "
        )
        tx.run(query,
               node1_label=node1_label, node1_search_query=node1_search_query, 
               node2_label=node2_label, node2_search_query=node2_search_query, 
               relation_label=relation_label)

uri = "neo4j+s://9c3dbb51.databases.neo4j.io"
user = "neo4j"
password = "6lg2UmUQC3rcHzERuog-1XWcLGjFFQUxeQLsNKoS_V0"

def create_node(label_list, property_dict):
    rgp = _RetsGraphPopulator(uri, user, password)
    rgp._create_node(label_list, property_dict)
    
def create_relation(node1_label, node1_search_query, 
                        node2_label, node2_search_query, relation_label):
    rgp = _RetsGraphPopulator(uri, user, password)
    rgp._create_relation(node1_label, node1_search_query, 
                         node2_label, node2_search_query, relation_label)
#%%

if __name__ == "__main__":
    create_node(['test'],{'name':'testitest'})
                       
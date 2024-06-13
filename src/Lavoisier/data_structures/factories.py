#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 12:38:35 2022

@author: jotape42p
"""

from .ILCD1_structure import ILCD1Structure, OLCAILCD1Structure
from .ECS2_structure import ECS2Structure

class StructureFactory:
    
    _mapping = {
        'ILCD1': {
            None: ILCD1Structure,
            ('1', '1'): ILCD1Structure
            },
        'OLCAILCD1': {
            None: OLCAILCD1Structure,
            ('1', '1'): OLCAILCD1Structure
            },
        'ECS2': {
            None: ECS2Structure,
            ('2', '0'): ECS2Structure
            }
        }
    
    def __init__(self, output_name):
        self.map_struct = self._mapping.get(output_name, None)
        
    def get_structure(self, struct, version):
        if struct is None:
            return self.map_struct[version]
        else:
            return struct[version] # Structures are bound to versions
            

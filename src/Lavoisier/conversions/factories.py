#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 12:36:09 2022

@author: jotape42p
"""

from pathlib import Path

from .ILCD1_to_ILCD1_conversion import (
    ILCD1ToILCD1FieldMapping
    )
from .ECS2_to_ILCD1_conversion import (
    ECS2ToILCD1FieldMapping
)
from .ILCD1_to_ECS2_conversion import (
    ILCD1ToECS2FieldMapping
)

class MappingFactory:
    
    ef_mapping = {
        ('ecoinvent3.7', 'EF3.0'): Path("Mappings/ecs2_to_ilcd1_elementary_flows.json"),
        ('EF3.0', 'ecoinvent3.7'): Path("Mappings/ilcd1_to_ecs2_elementary_flows.json")
        }
    
    ef_default_files = {
        'EF3.0': {
            'flow property': "Lavoisier_Default_Files/ILCD_EF30_FlowProperties",
            'unit group': "Lavoisier_Default_Files/ILCD_EF30_UnitGroups",
            'elementary flow': "Lavoisier_Default_Files/ILCD_EF30_ElementaryFlows"
            },
        'ecoinvent3.7': {}
        }
    
    # The best here is to change the value in the file. Ex: version 2.0
    # TODO internalSchemaVersion can be 1.0 with ecoinvent 2.0 (Dont Know Why)
    default_mappings = {
        ('EcoSpold2', 'ILCD1'): {
            None: ECS2ToILCD1FieldMapping,
            ('1', '0'): ECS2ToILCD1FieldMapping,
            ('2', '0'): ECS2ToILCD1FieldMapping
            },
        ('ILCD1', 'EcoSpold2'): {
            None: ILCD1ToECS2FieldMapping,
            ('1', '1'): ILCD1ToECS2FieldMapping
            },
        ('OLCAILCD1', 'OLCAILCD1'): {
            None: ILCD1ToILCD1FieldMapping,
            ('1', '1'): ILCD1ToILCD1FieldMapping
            }
        }
    
    def __init__(self, names, efs): # It is only for the default option, so 'get' is used
        self.__names = names
        self._ef_mapping = self.ef_mapping.get(efs, None) # output
        self._ef_file_defaults = self.ef_default_files.get(efs[1], None)
        self._mapping_dict = self.default_mappings.get(names, None)
        
    def get_mapping(self, config, version):
        if config.mapping_class is None:
            if self._mapping_dict is None:
                raise ValueError(f"Default mapping does not exist for {self.__names[0]} to {self.__names[1]} conversion")
            self._mapping = self._mapping_dict[version]()
        else:
            self._mapping = config.mapping_class()
        
        if config.transfer_defaults:
            type(self._mapping)._default_elem_mapping = self._ef_mapping
            type(self._mapping)._default_files = self._ef_file_defaults
        
        return self._mapping
    

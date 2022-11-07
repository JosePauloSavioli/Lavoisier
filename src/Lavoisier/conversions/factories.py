#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 12:36:09 2022

@author: jotape42p
"""

from pathlib import Path

from .ECS2_to_ILCD1_conversion import (
    ECS2ToILCD1Amount,
    ECS2ToILCD1FieldMapping,
    ECS2ToILCD1UncertaintyConversion,
    ECS2ToILCD1VariableConversion,
    ECS2ToILCD1FlowConversion,
    ECS2ToILCD1IntermediateFlowConversion,
    ECS2ToILCD1QuantitativeObject,
    ECS2ToILCD1ElementaryFlowConversion,
    ECS2ToILCD1ParameterConversion,
    ECS2ToILCD1ReferenceConversion,
    ECS2ToILCD1ReviewConversion,
    ECS2ToILCD1ClassificationConversion
)
from .ILCD1_to_ECS2_conversion import (
    ILCD1ToECS2FieldMapping,
    ILCD1ToECS2ClassificationConversion,
    ILCD1ToECS2ReferenceConversion,
    ILCD1ToECS2SourceReferenceConversion,
    ILCD1ToECS2ContactReferenceConversion,
    ILCD1ToECS2FlowReferenceConversion,
    ILCD1ToECS2Amount,
    ILCD1ToECS2UncertaintyConversion,
    ILCD1ToECS2FlowConversion,
    ILCD1ToECS2VariableConversion,
    ILCD1ToECS2ReviewConversion
)
from ..data_structures import (
    ECS2ToILCD1DataNotConverted,
    ILCD1ToECS2DataNotConverted
)

class MappingFactory:
    
    def __init__(self, input_name, output_name, input_ef_version, output_ef_version):
        self.input_, self.input_ef = input_name, input_ef_version
        self.output, self.output_ef = output_name, output_ef_version
    
    def get_mapping(self, version):
        if self.input_ == 'EcoSpold2':
            if self.output == 'ILCD1':
                if version is None or (version[0] == '2' and version[1] == '0'): # Default is v2.0
                    ef_mapping = {
                        ('ecoinvent3.7', 'EF3.0'): Path("Mappings/ecs2_to_ilcd1_elementary_flows.json")
                        }.get((self.input_ef, self.output_ef))
                    df_file = {
                        'EF3.0': {
                            'flow property': "Lavoisier_Default_Files/ILCD_EF30_FlowProperties",
                            'unit group': "Lavoisier_Default_Files/ILCD_EF30_UnitGroups",
                            'elementary flow': "Lavoisier_Default_Files/ILCD_EF30_ElementaryFlows"
                            }
                        }.get(self.output_ef)
                    fm = ECS2ToILCD1FieldMapping(
                        ECS2ToILCD1Amount,
                        ECS2ToILCD1UncertaintyConversion,
                        ECS2ToILCD1VariableConversion,
                        ECS2ToILCD1FlowConversion,
                        ECS2ToILCD1IntermediateFlowConversion,
                        ECS2ToILCD1QuantitativeObject,
                        ECS2ToILCD1ElementaryFlowConversion,
                        ECS2ToILCD1ParameterConversion,
                        ECS2ToILCD1ReferenceConversion,
                        ECS2ToILCD1ReviewConversion,
                        ECS2ToILCD1ClassificationConversion,
                        ECS2ToILCD1DataNotConverted)
                    type(fm)._default_elem_mapping = ef_mapping
                    type(fm)._default_files = df_file
                    return fm
        elif self.input_ == 'ILCD1':
            if self.output == 'EcoSpold2':
                if version is None or (version[0] == '1' and version[1] == '1'): # Default is v1.1
                    ef_mapping = {
                        ('EF3.0', 'ecoinvent3.7'): Path("Mappings/ilcd1_to_ecs2_elementary_flows.json") # TODO
                        }.get((self.input_ef, self.output_ef))
                    df_file = {
                        'ecoinvent3.7': {}
                        }.get(self.input_ef)
                    fm = ILCD1ToECS2FieldMapping(
                        ILCD1ToECS2Amount,
                        ILCD1ToECS2UncertaintyConversion,
                        ILCD1ToECS2SourceReferenceConversion,
                        ILCD1ToECS2ContactReferenceConversion,
                        ILCD1ToECS2FlowReferenceConversion,
                        ILCD1ToECS2ReferenceConversion,
                        ILCD1ToECS2FlowConversion,
                        ILCD1ToECS2VariableConversion,
                        ILCD1ToECS2ClassificationConversion,
                        ILCD1ToECS2ReviewConversion,
                        ILCD1ToECS2DataNotConverted)
                    type(fm)._default_elem_mapping = ef_mapping
                    type(fm)._default_files = df_file
                    return fm
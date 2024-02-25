#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 12:14:49 2022

@author: jotape42p
"""

from collections.abc import Iterator
from typing import Any, Optional
from .abstractions import InputTemplate, OutputTemplate, AbstractDataclass
from .ILCD1_format import ILCD1Input, ILCD1Output
from .ECS2_format import ECS2Input, ECS2Output
from .utils import XMLStreamIterable
from ..data_structures import (
    ignore_limits,
    ILCD1Structure,
    ECS2Structure,
    OLCAILCD1Structure,
    StructureTemplate
)

class MappingConfig(AbstractDataclass):
    mapping_class: Any | None
    transfer_defaults: bool

class DefaultMappingConfig(MappingConfig):
    mapping_class = None # None = default used
    transfer_defaults = True

class InputConfig(AbstractDataclass):
    name: str
    ef_mapping: Optional[str]
    iterator: Iterator
    input_manager: InputTemplate
    # General Dataset Info is information for:
        # format filename -> to output
        # file version -> to conversion
        # other important information for conversion -> to mapping
    initial_info: dict
    add_options: dict

class ILCD1InputConfig(InputConfig):
    name = 'ILCD1'
    iterator = XMLStreamIterable
    input_manager = ILCD1Input
    initial_info = {
        "/processDataSet/processInformation/dataSetInformation/name/baseName": ('filename', lambda x: x['#text']),
        "/processDataSet/@version": ('version', lambda x: tuple(x.split('.'))[:2]),
        "/processDataSet/exchanges/exchange": (('mapping','_flow_internal_refs', 'list'), lambda x: (x['@dataSetInternalID'], x['referenceToFlowDataSet']['shortDescription']['#text']))
        }
    add_options = {}

class ECS2InputConfig(InputConfig):
    name = 'EcoSpold2'
    iterator = XMLStreamIterable
    input_manager = ECS2Input
    initial_info = {
        "/ecoSpold/activityDataset/activityDescription/activity/activityName": ('filename', lambda x: x['#text']),
        "/ecoSpold/childActivityDataset/activityDescription/activity/activityName": ('filename', lambda x: x['#text']),
        "/ecoSpold/activityDataset/administrativeInformation/fileAttributes/@defaultLanguage": (('mapping','_default_language'), lambda x: x),
        "/ecoSpold/activityDataset/administrativeInformation/fileAttributes/@internalSchemaVersion": ('version', lambda x: tuple(x.split('.'))[:2]), # Last is a default
        "/ecoSpold/childActivityDataset/administrativeInformation/fileAttributes/@defaultLanguage": (('mapping','_default_language'), lambda x: x),
        "/ecoSpold/childActivityDataset/administrativeInformation/fileAttributes/@internalSchemaVersion": ('version', lambda x: tuple(x.split('.'))[:2])
        }
    add_options = {
        "convert_properties": (True, 'mapping_option', lambda mapping, x: setattr(mapping, 'convert_properties', x)),
        "convert_system_review": (True, 'mapping_option', lambda mapping, x: setattr(mapping, 'convert_system_review', x))
        }
    
class OLCAILCD1InputConfig(ILCD1InputConfig):
    name = 'OLCAILCD1'


class OutputConfig(AbstractDataclass):
    name: str
    ef_mapping: Optional[str]
    output_manager: OutputTemplate
    output_structure: StructureTemplate # Can be None too, in this case the default is considered via factory methods
    add_options: dict
    hash_: str
    version: str = None
    
class ILCD1OutputConfig(OutputConfig):
    name = 'ILCD1'
    output_manager = ILCD1Output
    output_structure = {None: ILCD1Structure, ('1','1'): ILCD1Structure}
    hash_ = ''
    add_options = {
        "ignore_string_length_restrictions": (True, 'general_option', ignore_limits),
        "sum_same_elementary_amounts": (False, 'mapping_option', lambda mapping, x: setattr(mapping, 'sum_same_elementary_amounts', x)),
        "convert_parameterization": (True, 'mapping_option', lambda mapping, x: setattr(mapping, 'convert_parameterization', x))
        }

class ECS2OutputConfig(OutputConfig):
    name = 'EcoSpold2'
    output_manager = ECS2Output
    output_structure = {None: ECS2Structure, ('2','0'): ECS2Structure}
    hash_ = ''
    add_options = {
        "ignore_string_length_restrictions": (True, 'general_option', ignore_limits),
        "sum_same_elementary_amounts": (False, 'mapping_option', lambda mapping, x: setattr(mapping, 'sum_same_elementary_amounts', x)),
        "convert_user_data": (True, "mapping_option", lambda mapping, x: setattr(mapping, 'convert_user_data', x)),
        "use_master_data_properties": (True, "mapping_option", lambda mapping, x: setattr(mapping, 'use_master_data_properties', x))
        }

class OLCAILCD1OutputConfig(ILCD1OutputConfig):
    name = 'OLCAILCD1'
    output_structure = OLCAILCD1Structure
    
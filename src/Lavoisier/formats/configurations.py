#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 12:14:49 2022

@author: jotape42p
"""

from collections.abc import Iterator
from .ILCD1_format import ILCD
from .ECS2_format import ECS2
from .utils import AbstractDataclass, Dataset, XMLStreamIterable
from ..data_structures import (
    ignore_limits,
    ILCD1Structure,
    ECS2Structure,
    OLCAILCD1Structure
)

class InputConfig(AbstractDataclass):
    valid_extensions: tuple
    iterator: Iterator
    add_options: dict

class OutputConfig(AbstractDataclass):
    output_data: Dataset
    add_options: dict

class ECS2InputConfig(InputConfig):
    name = 'EcoSpold2'
    default_mapping = 'ecoinvent3.7'
    valid_extensions = (".spold", ".SPOLD")
    iterator = XMLStreamIterable
    general_dataset_info = {
        "/ecoSpold/activityDataset/administrativeInformation/fileAttributes/@defaultLanguage": (('mapping','_default_language'), lambda x: x),
        "/ecoSpold/activityDataset/administrativeInformation/fileAttributes/@internalSchemaVersion": ('version', lambda x: x.split('.')), # Last is a default
        "/ecoSpold/childActivityDataset/administrativeInformation/fileAttributes/@defaultLanguage": (('mapping','_default_language'), lambda x: x),
        "/ecoSpold/childActivityDataset/administrativeInformation/fileAttributes/@internalSchemaVersion": ('version', lambda x: x.split('.'))
        }
    add_options = {
        "convert_properties": (True, 'conversion_type', lambda mapping, x: setattr(mapping, 'convert_properties', x))
        }

class ILCD1InputConfig(InputConfig):
    name = 'ILCD1'
    default_mapping = 'EF3.0'
    valid_extensions = (".zip",".xml")
    iterator = XMLStreamIterable
    general_dataset_info = {
        "/processDataSet/processInformation/dataSetInformation/name/baseName": (('format','filename'), lambda x: x),
        "/processDataSet/@version": ('version', lambda x: x.split('.')),
        "/processDataSet/exchanges/exchange": (('mapping','_flow_internal_refs', 'list'), lambda x: (x['@dataSetInternalID'], x['referenceToFlowDataSet']['shortDescription']['#text']))
        }
    add_options = {
        }
    
class OLCAILCD1InputConfig(ILCD1InputConfig):
    name = 'OLCAILCD1'

class ILCD1OutputConfig(OutputConfig):
    name = 'ILCD1'
    default_mapping = 'EF3.0'
    output_data = ILCD
    output_structure = ILCD1Structure
    add_options = {
        "ignore_string_length_restrictions": (True, 'single_type', ignore_limits)
        }

class OLCAILCD1OutputConfig(ILCD1OutputConfig):
    name = 'OLCAILCD1'
    output_structure = OLCAILCD1Structure

class ECS2OutputConfig(OutputConfig):
    name = 'EcoSpold2'
    default_mapping = 'ecoinvent3.7'
    output_data = ECS2
    output_structure = ECS2Structure
    add_options = {
        "ignore_string_length_restrictions": (True, 'single_type', ignore_limits)
        }


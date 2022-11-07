#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 12:38:35 2022

@author: jotape42p
"""

from .ILCD1_structure import ILCD1Structure
from .ECS2_structure import ECS2Structure

class StructureFactory:
    
    def __init__(self, output_name):
        self.output = output_name
        
    def get_structure(self, version):
        if self.output == 'ILCD1':
            if version is None or (version[0] == '1' and version[1] == '1'): # Default is v1.1
                return ILCD1Structure
        elif self.output == 'ECS2':
            if version is None or (version[0] == '2' and version[1] == '0'): # Default is v2.0
                return ECS2Structure
            
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 03:43:11 2023

@author: jotape42p
"""

from abc import ABC, abstractmethod

class StructureTemplate(ABC):
    
    @abstractmethod
    def get_filename(self, hash_):
        pass
    
    @abstractmethod
    def get_dict(self):
        pass

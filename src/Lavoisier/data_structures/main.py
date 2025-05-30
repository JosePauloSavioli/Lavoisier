#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  7 04:29:27 2022

@author: jotape42p
"""

from .validators.general_validators import Validator
from copy import copy

### MAIN STRUCTURE CLASS

'''

TYPES of DATA
    Validator, DotDict (unique = True) and List of DotDicts (unique = False)

Validator 'key': can't return itself as a Validator class
    GETTER: get(key) [returns the Validator.end()]
    SETTER: .key = [direct attribution]
        
DotDict 'key':
    GETTER: get(key) [gets DotDict unique instance], .key [gets DotDict unique instance]
    SETTER: 
        key_instance = .key
        key_instance.other_key = value
        
List of DotDict 'key': No dot chain as it is ambiguous, two methods for this entry
    GETTER: get(key) [gets value], get_class(key) [gets an empty instance of the DotDict of the members] 
    SETTER: 
        key_instance = .get_class(key)()
        key_instance.other_key = value
        .key = key_instance [adds the instance to the list]

'''

# Credits for Curt Hagenlocher for core implementing such an elegant class
# https://stackoverflow.com/questions/3031219/recursively-access-dict-via-attributes-as-well-as-index-access

class DotDict(dict):

    def __new__(cls, value=None):
        # DotDicts can be received from __setitem__ and are automatically setted instead of setting every key
        if isinstance(value, DotDict): 
            return value
        else:
            return dict.__new__(cls)

    def __init__(self, value=None):

        if value is None or isinstance(value, DotDict):
            pass
        elif isinstance(value, dict):
            for key in value:
                self.__setitem__(key, value[key])
        # A DotDict class (not instance) can be received at __setitem__ and propagated to here
        elif issubclass(value.__class__, DotDict):
            raise TypeError('Received DotDict class instead of instance')
        else:
            raise TypeError('Expected dict')

    def __setitem__(self, key, value):
        
        key = key[1:] if key[0] in ('@', '#') else key
        
        if key in self.VALID:
            
            if not isinstance(value, list): # It is done so to be able to receive lists or normal inputs
                value = [value]
            
            for v in value:
                if super().get(key):
                    if self.VALID[key].get('unique', False):
                        raise ValueError(f'{key} of class {self.VALID[key]["type"]} has to be unique')
            
                if issubclass(self.VALID[key]['type'], Validator): # Validator fields
                    v = copy(dict(v)) if isinstance(v, DotDict) else copy(v)
                    super().__setitem__(key, super().get(key, self.VALID[key]['type']()).add(v))
                    
                else: # DotDict class or a list of them
                    super().__setitem__(key, super().get(key, []) + [self.VALID[key]['type'](v)])
        else:
            raise AttributeError(f'class {self.__class__.__name__} cannot accept attribute {key}')
            
    def get_class(self, key): 
        # When the field has 'type' DotDict and is not unique, this is the way to retrieve its class 
        found = self.VALID[key]['type']
        if issubclass(found, DotDict):
            if self.VALID[key].get('unique', False):
                raise KeyError(f"{key} is unique and cannot be retrieved via 'get_class' method. Use normal assignment to get its instance")
            return found
        else:
            raise KeyError(f"{key} is a Validator and cannot be retrieved via 'get_class' method. Use method 'get({key})' to return its value")
            
    def get(self, key, default=None):
        # Get method is overriden here for additional functionality regarding Validator fields and DotDict non-unique classes
        found = super().get(key, default)
        if found != default:
            if isinstance(found, Validator):
                return found.end()
            else:
                return found
        else:
            return default

    def __getitem__(self, key):
        # Get method only can receive calls from VALID keys
        if key == '__name__': # [!] Errors on the debugging of uncertainty (probably due to module import)
            return object()
        found = super().get(key, self.VALID[key]['type']())
        
        if isinstance(found, Validator):
            raise KeyError(f"{key} is a Validator and can only be assigned to. Use method 'get({key})' to return its value")
        elif self.VALID[key].get('unique', False):
            if not isinstance(found, list):
                super().__setitem__(key, [found])
            return super().get(key)[0]
        else:
            raise KeyError(f"{key} is a List of DotDicts and can only be assigned to. Use method 'get({key})' to return its value or use the method 'get_class({key})' to return its class")
        
    def get_dict(self):
        
        # Mandatory fields
        for key in {k: v for k, v in self.VALID.items() if v['mandatory']}:
            if key not in self:
                raise AttributeError(f'class {self.__class__.__name__} missing mandatory attribute {key}')
            
        def get_name(k, valid):
            pr = {'attribute': '@', 'nms:common': 'common:', 'text': '#'}
            k = k if 'xml_nms' not in valid else valid['xml_nms']+':'+k
            return k if 'xml_type' not in valid else pr.get(valid['xml_type'], valid['xml_type'].replace('nms:', '')+':')+k
        
        def get_value(valid, v):
            if isinstance(v, dict):
                return v.get_dict()
            elif isinstance(v, list):
                return list(map(lambda x: x.get_dict(), v))
            else:
                return v.end()
                
        # Ordering
        new = {get_name(k,self.VALID[k]):(v if self.VALID[k].get('xml_type')!='text' else str(v)) for k,v in sorted({k:get_value(self.VALID[k],v) for k,v in self.items()}.items(), key=lambda n:self.VALID[n[0]]['order'])}
        
        return new

    __setattr__, __getattr__ = __setitem__, __getitem__

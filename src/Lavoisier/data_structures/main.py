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
        if isinstance(value, cls): 
            return value
        return dict.__new__(cls)

    def __init__(self, value=None):
        if value is None or value is self:
            return
        if not isinstance(value, dict):
            # A DotDict class (not instance) can be received at __setitem__ and propagated to here
            raise TypeError("Expected dict")
        for key, value in value.items():
            if key == "@xmlns" or key.startswith("@xmlns:"):
                continue
            self[key] = value

    @staticmethod
    def _xml_name(key, valid):
        prefix = {"attribute": "@", "nms:common": "common:", "text": "#"}
        if "xml_nms" in valid:
            key = f"{valid['xml_nms']}:{key}"
        if "xml_type" in valid:
            key = prefix.get(valid["xml_type"], valid["xml_type"].replace("nms:", "")+":") + key
        return key

    def _key(self, key):
        if key in self.VALID:
            return key
        for name, valid in self.VALID.items():
            if self._xml_name(name, valid) == key:
                return name
        raise AttributeError(f"class {type(self).__name__} cannot accept attribute {key}")

    def __setitem__(self, key, value):
        key = self._key(key)
        valid = self.VALID[key]
        # It is done so to be able to receive lists or normal inputs
        values = value if isinstance(value, list) else [value]
        
        for value in values:
            if key in self and valid.get("unique", False):
                raise ValueError(f"{key} of class {valid['type']} has to be unique")

            if issubclass(valid["type"], Validator): # Validator fields
                value = copy(dict(value)) if isinstance(value, DotDict) else copy(value)
                current = super().get(key, valid["type"]())
                super().__setitem__(key, current.add(value))

            else:
                current = super().get(key, [])
                super().__setitem__(key, current + [valid["type"](value)])

    def __getitem__(self, key):
        # Get method only can receive calls from VALID keys
        valid = self.VALID[key]
        if issubclass(valid["type"], Validator):
            raise KeyError(f"{key} is a Validator and can only be assigned to. Use method 'get({key})' to return its value")
        if not valid.get("unique", False):
            raise KeyError(f"{key} is a List of DotDicts and can only be assigned to. Use method 'get({key})' to return its value or use the method 'get_class({key})' to return its class")
        
        if key not in self:
            super().__setitem__(key, [valid["type"]()])
        return super().__getitem__(key)[0]
    
    def __getattr__(self, key): # Uncertainty errors related to importing
        if key.startswith("__"):
            raise AttributeError(key)
        try:
            return self[key]
        except KeyError as error:
            raise AttributeError(str(error)) from error
            
    def get(self, key, default=None):
        # Get method is overriden here for additional functionality regarding Validator fields and DotDict non-unique classes
        if key not in self:
            return default

        found = super().__getitem__(key)
        if isinstance(found, Validator):
            return found.end()
        if self.VALID[key].get("unique", False):
            return found[0]
        return found
    
    def get_value(self, key, default=None):
        if key not in self:
            return default
        found = super().__getitem__(key)
        if isinstance(found, Validator):
            return found.value()
        if self.VALID[key].get("unique", False):
            return found[0]
        return found
    
    def get_class(self, key): 
        # When the field has 'type' DotDict and is not unique, this is the way to retrieve its class 
        found = self.VALID[key]['type']
        
        if not issubclass(found, DotDict):
            raise KeyError(f"{key} is a Validator and cannot be retrieved via 'get_class' method. Use method 'get({key})' to return its value")
        if self.VALID[key].get("unique", False):
            raise KeyError(f"{key} is unique and cannot be retrieved via 'get_class' method. Use normal assignment to get its instance")
            
        return found

    def get_dict(self):
        # Mandatory fields
        for key, valid in self.VALID.items():
            if valid["mandatory"] and key not in self:
                raise AttributeError(f"class {self.__class__.__name__} missing mandatory attribute {key}")
        
        def get_value(value):
            if isinstance(value, DotDict):
                return value.get_dict()
            elif isinstance(value, list):
                return [item.get_dict() for item in value]
            else:
                return value.end()
        
        values = {key: get_value(value) for key, value in self.items()}
        # Ordering
        return {
            self._xml_name(key, self.VALID[key]): (str(value) if self.VALID[key].get("xml_type") == "text" else value)
            for key, value in sorted(values.items(), key=lambda item: self.VALID[item[0]]["order"])
        }

    __setattr__ = __setitem__


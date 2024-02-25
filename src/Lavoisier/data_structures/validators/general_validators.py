#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 29 15:36:20 2023

@author: jotape42p
"""

import re
import datetime
from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from ..utils import text_to_list

### Addition methods

def _add(self, o):
    self._x = self._validate(o)
    return self

def list_add(self, o):
    if hasattr(self, '_x'):
        self._x = (self._x if isinstance(self._x, list) else [self._x]) + [self._validate(o)]
    else:
        self._x = self._validate(o)
    return self

def unique_list_add(self, o):
    self._x = [] if not hasattr(self, '_x') else self._x
    for n in self._validate(o): # for loop makes and entry ['1', '1'] result in only '1' being added to self._x
        if n not in self._x:
            self._x += [n]
    return self

def return_comparisson_add(func):
    def comparisson_add(self, o):
        if not hasattr(self, '_x'):
            self._x = self._validate(o)
        else:
            o = self._validate(o)
            if func(o, self._x):
                self._x = o
        return self
    return comparisson_add

def separator_add(self, o):
    if not hasattr(self, '_x'):
        self._x = self._validate(o)
    else:
        self._x += self.sep+self._validate(o)
    return self

### Main validator class

class Validator(ABC):
    @abstractmethod
    def _validate(self, x):
        pass
    def _end_validate(self):
        pass
    add = _add
    def end(self):
        self._end_validate()
        return self._x

### General validator classes

class Real(Validator):
    def _validate(self, x):
        try:
            x = float(x)
        except:
            raise TypeError(f'{self.__class__.__name__}: Expected a float, received {x} of type {type(x)}')
        return x

class Bool(Validator, ABC):
    VALID = ('true','false','True','False',1,0,'1','0',True,False)
    def _validate(self, x):
        if x not in self.VALID:
            raise ValueError(f'ECS2BOOL: {x} is not valid. Must be one of {", ".join([str(x) for x in self.VALID])}')
        return bool(x) if not isinstance(x, str) else x in ('1', 'true', 'True')

class Int(Validator):
    can_be_negative = False
    def _validate(self, x):
        try:
            x = int(x)
        except:
            raise TypeError(f'{self.__class__.__name__}: Expected an integer, received {x} of type {type(x)}')
        if not self.can_be_negative and x < 0:
            raise ValueError(f'{self.__class__.__name__}: Entry {x} is not valid. Must be positive')
        return x

def return_collection(_limits:set, _can_be_negative=False):
    class Collection(Int):
        can_be_negative = _can_be_negative
        limits = _limits
        def _validate(self, x):
            x = super()._validate(x)
            if not x in self.limits:
                raise ValueError(f'{self.__class__.__name__}: Entry {x} is not valid. Must be a number among {sorted(list(self.limits))}')
            return x
    return Collection

def return_limited_int(limit:int, func=lambda x,lim: x!=lim, add_func=_add):
    class LimitedInt(Int):
        add = add_func
        def _validate(self, x):
            x = super()._validate(x)
            if func(len(str(x)), limit) or x<0:
                raise ValueError(f'Int{limit}: Entry {x} is not valid. Must have only {limit} digit(s)')
            return x
    return LimitedInt

def return_pattern(pattern):
    class Pattern(Validator):
        def _validate(self, x):
            if not isinstance(x, str):
                raise TypeError(f'{self.__class__.__name__}: Expected a string, received {x} of type {type(x)}')
            if not re.match(pattern, x):
                raise ValueError(f'Pattern: Entry {x} is not valid for pattern {self.__class__.__name__}')
            return x
    return Pattern

UUID = return_pattern(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}')

class Date(Validator):
    def _validate(self, x):
        if not isinstance(x, str):
            raise TypeError(f'{self.__class__.__name__}: Expected a string, received {x} of type {type(x)}')
        try:
            x = datetime.datetime.fromisoformat(x.replace('Z', '+00:00'))
        except:
            raise ValueError(f'{self.__class__.__name__}: Entry {x} is not valid. Must be an ISO 8601 datetime')
        return x

class Str(Validator):
    def _validate(self, x):
        if not isinstance(x, str):
            raise TypeError(f'{self.__class__.__name__}: Expected a string, received {x} of type {type(x)}')
        return x

class _LimStr(Str):
    ignore_limit = False
    
def ignore_limits(value):
    _LimStr.ignore_limit = value
    
def return_limited_string(_limit, add_func=separator_add, _sep='; '):
    class LimitedString(_LimStr):
        add = add_func
        limit = _limit
        def __init__(self):
            self.sep = _sep
        def _end_validate(self):
            if self.limit:
                condition = len(self._x) <= self.limit if isinstance(self.limit, int) else self.limit[0] <= len(self._x) <= self.limit[1]
                if not condition and not self.ignore_limit:
                    raise ValueError(f'{self.__class__.__name__}: Entry with length {len(self._x)} is not valid. Must have length {"lower than" if isinstance(self.limit, int) else "between"} {self.limit}')
    return LimitedString

UnlimitedString = return_limited_string(100000000)

def return_enum(enum, list_=False): # licenseType can overwrite its value with double 'add' calls
    class Enumeration(Validator):
        add = _add if not list_ else unique_list_add
        def __init__(self):
            self._enum = enum
        def _validate(self, x):
            if not isinstance(x, (list, tuple, str)) or (isinstance(x, (list, tuple)) and not list_):
                raise TypeError(f'Enumeration: Expected a str, received {x} of type {type(x)}')
            s = x if isinstance(x, (list, tuple)) else [x]
            for y in s:
                if y not in self._enum:
                    raise ValueError(f'Enumeration: {y} is not valid. Must be one of: {", ".join(self._enum)}')
            return x if not list_ else s
    return Enumeration

class BasicDictString(Validator, ABC):
    
    _text = None
    _keys = ('#text',) # Only this keys are possible
    
    def __init__(self):
    	if hasattr(self._text(), 'sep'):
            self._sep = self._text().sep
    
    def change_sep(self, sep):
    	if hasattr(self._text(), 'sep'):
    	    self._sep = sep
    
    def get_text(self):
    	t = self._text()
    	if hasattr(self._text(), 'sep'):
            t.sep = self._sep	
    	return t
    
    def _key_check(self, n, x):
        if n not in x:
            raise KeyError(f'{self.__class__.__name__}: Key {n} not found in {x}')
    
    def _validate(self, x):
        if not isinstance(x, dict):
            raise TypeError(f'{self.__class__.__name__}: Expected a dict, recieved {x} of type {type(x)}')
        for key in x.keys():
            if key not in self._keys:
                raise KeyError(f"{self.__class__.__name__}: {key} can't be used as a valid key entrance for this class, use: {self._keys}")
        self._key_check('#text', x)
        x['#text'] = self.get_text().add(x['#text'])
        return x
    
    def _retrieve(self, x):
        n = []
        if not isinstance(x, list):
            x = [x]
        for l in x:
            r = self._validate(l)
            if r['#text']._x and not r['#text']._x.isspace():
                n.append(r)
        return n

    def _add(self, o, index=False, lang=False):
        condition = {
            (True, True): lambda x, y: x['@index'] == y['@index'] and x['@lang'] == y['@lang'],
            (True, False): lambda x, y: x['@index'] == y['@index']
            }.get((index, lang))
        for n in self._retrieve(o):
            for m in self._x:
                if condition(n, m):
                    self._x[self._x.index(m)]['#text'].add(n['#text']._x) # Can't call 'end' here yet
                    break
            else:
                self._x.append(n)
    
    @abstractmethod
    def add(self): pass
    
    def _end_validate(self, x): # _end_validate doesn't modify self._x, otherwise the end process cannot be done again
        n = []
        for s in x:
            t = s.pop('#text')
            if not type(t) in (Str, UnlimitedString):
                if isinstance(t.limit, tuple): l = t.limit[1]
                else: l = t.limit
            if not type(t) in (Str, UnlimitedString):
                if not t.ignore_limit and len(t._x) > l:
                    n.extend([s | {"#text": self.get_text().add(n).end()} for n in text_to_list(t._x, l)])
                else:
                    n.append(s | {"#text": t.end()})
            else:
                n.append(s | {"#text": t.end()})
        return n
    
    @abstractmethod
    def end(self): pass

class IndexedString(BasicDictString):
    
    _keys = ('@index', '#text')
    
    def _validate(self, x):
        x = super()._validate(x)
        self._key_check('@index', x)
        try:
            x['@index'] = int(x['@index'])
        except:
            raise ValueError(f'{self.__class__.__name__}: Expected an integer, received {x["@index"]} of type {type(x["@index"])}')
        return x
    
    def add(self, o):
        self._x = self._x if hasattr(self, '_x') else []
        self._add(o, True)
        return self
    
    def end(self): # Default when there is no need to wipe out a key (like index in multilang)
        x = deepcopy(sorted(self._x, key=lambda x:x['@index']))
        x = self._end_validate(x)
        return x

class MultiLangString(IndexedString): # One of each language

    _keys = ('@index', '@lang', '#text')
    
    def _validate(self, x):
        x = super()._validate(x)
        self._key_check('@lang', x)
        if not isinstance(x['@lang'], str) or not len(x['@lang']) == 2 :
            raise ValueError(f'{self.__class__.__name__}: {x["@lang"]} is not a valid language')
        return x
    
    def add(self, o):
        self._x = self._x if hasattr(self, '_x') else []
        self._add(o, True, True)
        return self
    
    def end(self):
        x = sorted(self._x, key=lambda x:x['@index'])
        d = defaultdict(str)
        for s in x:
            d[s['@lang']] += '\n'+s['#text']._x if d.get(s['@lang']) else s['#text']._x # Can't call 'end' here yet
        x = [{"@xml:lang": k, "#text": self.get_text().add(v)} for k, v in sorted(d.items())]
        x = self._end_validate(x)
        return x

class NoLangRestrictionMultiLangString(IndexedString): # Can have multiple of the same lang

    _keys = ('@index', '@lang', '#text')
    
    def _validate(self, x): # Same as MultiLang
        x = super()._validate(x)
        self._key_check('@lang', x)
        if not isinstance(x['@lang'], str) or not len(x['@lang']) == 2 :
            raise ValueError(f'{self.__class__.__name__}: {x["@lang"]} is not a valid language')
        return x 

    def add(self, o): # This is a standard add method for list but always return a list
        self._x = self._x if hasattr(self, '_x') else []
        for n in self._retrieve(o):
            self._x.append(n)
        return self

    def end(self):
        x = deepcopy(sorted(self._x, key=lambda x:x['@index']))
        x = [dict((k if k!='@lang' else '@xml:lang', v) for k, v in y.items() if k != '@index') for y in x]
        x = self._end_validate(x)
        return x

class IndexedMultiLangString(MultiLangString): # Index is maintained

    def end(self):
        x = deepcopy(sorted(self._x, key=lambda x:str(x['@index'])+str(x['@lang'])))
        x = [dict((k if k!='@lang' else '@xml:lang', v) for k, v in y.items()) for y in x]
        x = self._end_validate(x)
        return x
        

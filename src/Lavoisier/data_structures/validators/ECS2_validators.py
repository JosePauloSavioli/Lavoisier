#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 29 20:27:41 2023

@author: jotape42p
"""

from .general_validators import (
    _add,
    Real,
    Bool,
    Date,
    Str,
    BasicDictString,
    MultiLangString,
    IndexedString,
    IndexedMultiLangString,
    NoLangRestrictionMultiLangString,
    return_collection,
    return_pattern,
    return_limited_string,
    )
from copy import deepcopy

class Percent(Real): # Formatted as ddd.d
    def _validate(self, x):
        x = super()._validate(x)
        if x > 100:
            raise ValueError(f'Perc: Percentual value {x} higher than 100')
        elif x < 0:
            raise ValueError(f"Perc: Percentual value {x} can't be negative")
        return x
    def end(self):
        return str(f'{self._x:.1f}')

class Bool(Bool): # [OK] Anything can be a bool, so it is verified through a handful of cases
    def end(self):
        return 'true' if self._x else 'false'

InheritanceDepthINT = return_collection(set(range(-1,4)), _can_be_negative=True)
SourceTypeINT = return_collection(set(range(8)))
TypeINT = return_collection(set(range(1,4))) # Check
SpecialActivityTypeINT = return_collection(set(range(11)))
EnergyValuesINT = return_collection(set(range(3)))
TechnologyLevelINT = return_collection(set(range(6)))
DataPublishedInINT = return_collection(set(range(2)))
AccessRestrictedToINT = return_collection(set(range(3)))
PedigreeINT = return_collection(set(range(1,6)))
InputGroupIntermediateINT = return_collection({1,2,3,5})
OutputGroupIntermediateINT = return_collection({0,2,3,5})
InputGroupElementaryINT = return_collection({4})
OutputGroupElementaryINT = return_collection({4})

CASNumber = return_pattern(r'\d{1,6}-\d{2,2}-\d')

class Date(Date):
    def end(self):
        return self._x.strftime('%Y-%m-%d')

class CompleteDate(Date):
    def end(self):
        return self._x.strftime('%Y-%m-%dT%H:%M:%S')

ISOTwoLetterCode = return_limited_string(2, add_func=_add)
ISOThreeLetterCode = return_limited_string(3, add_func=_add)
Lang = return_limited_string((2,5), add_func=_add)
CompanyCode = return_limited_string(7, add_func=_add)
BaseString20 = return_limited_string(20)
BaseString30 = return_limited_string(30)
BaseString40 = return_limited_string(40)
BaseString80 = return_limited_string(80)
BaseString120 = return_limited_string(120)
BaseString255 = return_limited_string(255)
BaseString32000 = return_limited_string(32000)
UniqueBaseString30 = return_limited_string(30, add_func=_add)
UniqueBaseString40 = return_limited_string(40, add_func=_add)
UniqueBaseString80 = return_limited_string(80, add_func=_add)
ReviewString = return_limited_string(40, _sep='/')

# If the _add function is not added here, it assumes the separator_add function, which is not wanted
class VariableName(return_pattern(r'\w\S*'), return_limited_string(40, add_func=_add)):
    pass

class NamedString(BasicDictString):
    
    _keys = ('@name', '#text')
    _name_text = BaseString40
    def _add(self, o): pass
    
    def _retrieve(self, x):
        n = []
        if not isinstance(x, list):
            x = [x]
        _dupl = [] # Verify duplicated name inside x, like [{'@name':'lol'...}, {'@name':'lol'...}]
        for l in x:
            r = self._validate(l)
            if r['@name']._x in _dupl: 
                raise ValueError(f'{self.__class__.__name__}: Tried to add the same name {r["@name"]}')
            else: _dupl.append(deepcopy(r['@name']._x))
            if r['#text']._x and not r['#text']._x.isspace():
                n.append(r)
        return n

    def _validate(self, x):
        x = super()._validate(x)
        self._key_check('@name', x)
        for n in self._x:
            if n['@name']._x == x['@name']:
                raise ValueError(f'{self.__class__.__name__}: Tried to add the same name {x["@name"]}')
        x['@name'] = self._name_text().add(x['@name'])
        return x
    
    def add(self, o):
        self._x = self._x if hasattr(self, '_x') else []
        for n in self._retrieve(o):
            self._x.append(n)
        return self
    
    def end(self):
        x, m = [], {}
        for n in self._x:
            m['@name'] = n['@name']._x
            m['#text'] = n['#text']
            x.append(deepcopy(m))
        x = self._end_validate(x)
        return x
    
class NamedString32000(NamedString):
    _text = BaseString32000

class String20(MultiLangString):
    _text = BaseString20
class String40(MultiLangString):
    _text = BaseString40
class String80(MultiLangString):
    _text = BaseString80
class String120(MultiLangString):
    _text = BaseString120
class String255(MultiLangString):
    _text = BaseString255
class String32000(MultiLangString):
    _text = BaseString32000
class UniqueString40(MultiLangString):
    _text = UniqueBaseString40
class IndexedStringSTR(IndexedString):
    _text = Str
class IndexedString32000(IndexedMultiLangString):
    _text = BaseString32000
class String80_NLR(NoLangRestrictionMultiLangString):
    _text = BaseString80
    
    def end(self):
        x = deepcopy(sorted(self._x, key=lambda x:x['@index']))
        x = [dict((k if k!='@lang' else '@xml:lang', v) for k, v in y.items() if k != '@index') for y in x]
        x = [n for n in x if len(n['#text']._x) <= self._text.limit] # synonyms were getting to huge
        x = self._end_validate(x)
        return x

class ClassificationValueString120(NoLangRestrictionMultiLangString):
    _text = BaseString120
    def end(self):
        x = deepcopy(sorted(self._x, key=lambda x:x['@index']))
        x = [dict((k if k!='@lang' else '@xml:lang', v) for k, v in y.items() if k != '@index') for y in x]
        x = [x[-1]] if x else x # Only one entry is possible here; -1 is chosen because the complete classification is expected last
        x = super()._end_validate(x)[-1] if x else [] # This has to be done to assure that it is only one, x can be empty list
        return x

class ExchangeNameString80(NoLangRestrictionMultiLangString):
    _text = BaseString80
    def end(self):
        x = deepcopy(sorted(self._x, key=lambda x:x['@index']))
        x = [dict((k if k!='@lang' else '@xml:lang', v) for k, v in y.items() if k != '@index') for y in x]
        x = [x[0]] if x else x # Only one entry is possible here; 0 is chosen because the main name is expected first
        x = super()._end_validate(x)[0] if x else [] # This has to be done to assure that it is only one
        return x
    
class Name(NoLangRestrictionMultiLangString): # Activity Name is better off with only one option, not several separated by ', '
    _text = BaseString120
    def end(self):
        x = deepcopy(sorted(self._x, key=lambda x:x['@index']))
        x = [dict((k if k!='@lang' else '@xml:lang', v) for k, v in y.items() if k != '@index') for y in x]
        x = [x[0]] if x else x # [had error with name length] Only one entry is possible here; 0 is chosen because the main name is expected first
        x = super()._end_validate(x)[0] if x else [] # This has to be done to assure that it is only one
        return x
        

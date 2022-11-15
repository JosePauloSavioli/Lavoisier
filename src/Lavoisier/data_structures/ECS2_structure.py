#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 31 19:20:32 2022

@author: jotape42p
"""

import re, datetime
from abc import ABC, abstractmethod
from collections import defaultdict
from .utils import text_to_list
from .main import DotDict, Validator

class BOOL(Validator): # Anything can be a bool, so it is verified through a handful of cases
    VALID = ('true','false','True','False',1,0,'1','0',True,False)
    def _validate(self, x):
        if x not in self.VALID:
            raise ValueError(f'BOOL: {x} is not valid. Must be one of {", ".join([str(x) for x in self.VALID])}')
        return bool(x) if not isinstance(x, str) else x in ('1', 'true', 'True')
    def end(self):
        return 'true' if self._x else 'false'

class Real(Validator):
    def _validate(self, x):
        try:
            x = float(x)
        except:
            raise TypeError(f'{self.__class__.__name__}: Expected a float, received {x} of type {type(x)}')
        return x

class Percent(Real): # [!] Formatted as ddd.d
    def _validate(self, x):
        x = super()._validate(x)
        if x > 100:
            raise ValueError(f'Perc: Percentual value {x} higher than 100')
        return x
            
    def end(self):
        return str(f'{self._x:.1f}')

class INT(Validator, ABC):
    can_be_negative = False
    def _validate(self, x):
        try:
            x = int(x)
        except:
            raise TypeError(f'{self.__class__.__name__}: Expected an integer, received {x} of type {type(x)}')
        if not self.can_be_negative and x < 0:
            raise ValueError(f'{self.__class__.__name__}: Entry {x} is not valid. Must be positive')
        return x
    
class LimitedINT(INT, ABC):
    limits: set
    def _validate(self, x):
        x = super()._validate(x)
        if not x in self.limits:
            raise ValueError(f'{self.__class__.__name__}: Entry {x} is not valid. Must be a number among {sorted(list(self.limits))}')
        return x

class InheritanceDepthINT(LimitedINT):
    limits = set(range(-1,4))
    can_be_negative = True
    
class SourceTypeINT(LimitedINT):
    limits = set(range(8))
    
class TypeINT(LimitedINT):
    limits = set(range(1,4)) # Check

class SpecialActivityTypeINT(LimitedINT):
    limits = set(range(11))

class EnergyValuesINT(LimitedINT):
    limits = set(range(2))

class TechnologyLevelINT(LimitedINT):
    limits = set(range(6))

class DataPublishedInINT(LimitedINT):
    limits = set(range(2))
    
class AccessRestrictedToINT(LimitedINT):
    limits = set(range(3))

class PedigreeINT(LimitedINT):
    limits = set(range(1,6))

class InputGroupIntermediateINT(LimitedINT):
    limits = {1,2,3,5}

class OutputGroupIntermediateINT(LimitedINT):
    limits = {0,2,3,5}

class InputGroupElementaryINT(LimitedINT):
    limits = {4}

class OutputGroupElementaryINT(LimitedINT):
    limits = {4}

class Date(Validator):
    def _validate(self, x):
        if not isinstance(x, str):
            raise TypeError(f'{self.__class__.__name__}: Expected a string, received {x} of type {type(x)}')
        try:
            x = datetime.datetime.fromisoformat(x.replace('Z', '+00:00'))
        except:
            raise ValueError(f'{self.__class__.__name__}: Entry {x} is not valid. Must be an ISO 8601 datetime')
        return x
    def end(self):
        return self._x.strftime('%Y-%m-%d')

class CompleteDate(Date):
    def end(self):
        return self._x.strftime('%Y-%m-%dT%H:%M:%S')

class Pattern(Validator, ABC):
    def _validate(self, x):
        if not isinstance(x, str):
            raise TypeError(f'{self.__class__.__name__}: Expected a string, received {x} of type {type(x)}')
        if not re.match(self._pattern, x):
            raise ValueError(f'Pattern: Entry {x} is not valid for pattern {self.__class__.__name__}')
        return x
    
class UUID(Pattern):
    def __init__(self):
        self._pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'

class CASNumber(Pattern):
    def __init__(self):
        self._pattern = r'\d{1,6}-\d{2,2}-\d'

class STR(Validator):
    def _validate(self, x):
        if not isinstance(x, str):
            raise TypeError(f'{self.__class__.__name__}: Expected a string, received {x} of type {type(x)}')
        return x

class String(STR):
    def add(self, o, sep='\n'):
        if not hasattr(self, '_x'):
            self._x = self._validate(o)
        else:
            self._x += sep+self._validate(o)
        return self

class LimitedString(String):
    limit: int
    ignore_limit = False
    def _end_validate(self):
        condition = len(self._x) <= self.limit if isinstance(self.limit, int) else self.limit[0] <= len(self._x) <= self.limit[1]
        if not condition and not self.ignore_limit:
            raise ValueError(f'String: Entry {self._x} with length {len(self._x)} is not valid. Must have length lower than {self.limit}')

class UniqueLimitedString(LimitedString):
    def add(self, o):
        self._x = self._validate(o)
        return self

class ISOTwoLetterCode(LimitedString):
    limit = 2

class ISOThreeLetterCode(LimitedString):
    limit = 3

class Lang(LimitedString):
    limit = (2,5)

class CompanyCode(LimitedString):
    limit = 7

class BaseString20(LimitedString):
    limit = 20

class BaseString30(LimitedString):
    limit = 30

class UniqueBaseString30(UniqueLimitedString):
    limit = 30

class BaseString40(LimitedString):
    limit = 40

class UniqueBaseString40(UniqueLimitedString):
    limit = 40

class BaseString80(LimitedString):
    limit = 80
            
class BaseString120(LimitedString):
    limit = 120

class BaseString255(LimitedString):
    limit = 255

class BaseString32000(LimitedString):
    limit = 32000

class VariableName(Pattern, BaseString40):
    def __init__(self):
        self._pattern = r'\w\S*'

def ECS2_ignore_limits(value):
    LimitedString.ignore_limit = value

class BasicDictString(Validator, ABC):
    
    _text = None
    
    def _key_check(self, n, x):
        if n not in x:
            raise KeyError(f'{self.__class__.__name__}: Key {n} not found in {x}')
    
    def _validate(self, x):
        if not isinstance(x, dict):
            raise TypeError(f'{self.__class__.__name__}: Expected a dict, recieved {x} of type {type(x)}')
        self._key_check('#text', x)
        x['#text'] = self._text().add(x['#text'])
        return x
    
    def _retrieve(self, x):
        n = []
        if not isinstance(x, list):
            x = [x]
        for l in x:
            n.append(self._validate(l))
        return n

    def _add(self, o, index=False, lang=False, sep='; '):
        condition = {
            (True, True): lambda x, y: x['@index'] == y['@index'] and x['@lang'] == y['@lang'],
            (True, False): lambda x, y: x['@index'] == y['@index']
            }.get((index, lang))
        for n in self._retrieve(o):
            for m in self._x:
                if condition(n, m):
                    if not m['#text']._x or m['#text']._x.isspace() or not n['#text']._x or n['#text']._x.isspace(): _sep=''
                    else: _sep=sep
                    self._x[self._x.index(m)]['#text'].add(n['#text']._x, sep=_sep) # Can't call 'end' here yet
                    break
            else:
                self._x.append(n)
                
    def add(self, o, sep='; '):
        self._x = self._x if hasattr(self, '_x') else []
        self._add(o, sep=sep)
        return self
    
    def _end_validate(self, x): # _end_validate doesn't modify self._x, otherwise the end process cannot be done again
        n = []
        for s in x:
            t = s.pop('#text')
            if not type(t) is STR and len(t._x) > t.limit:
                n.extend([s | {"#text": self._text().add(n).end()} for n in text_to_list(t._x, t.limit)])
            else:
                n.append(s | {"#text": t.end()})
        return n
    
    @abstractmethod
    def end(self):
        pass

class NamedString(BasicDictString):
    
    _name_text = BaseString40
    
    def _validate(self, x):
        x = super()._validate(x)
        self._key_check('@name', x)
        for n in self._x:
            if n['@name'] == x['@name']:
                raise ValueError(f'{self.__class__.__name__}: Tried to add the same name {x["name"]}')
        x['@name'] = self._name_text().add(x['@name'])
        x['#text'] = self._text().add(x['#text'])
        return x
    
    def add(self, o):
        self._x = self._x if hasattr(self, '_x') else []
        for n in self._retrieve(o):
            self._x.append(n)
        return self
    
    def end(self):
        x, m = [], {}
        for n in self._x:
            m['@name'] = n['@name'].end()
            m['#text'] = n['#text'].end()
            x.append(m)
        return x

class IndexedString(BasicDictString):
    
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
    
    def end(self):
        x = sorted(self._x, key=lambda x:x['@index'])
        d = defaultdict(str)
        for s in x:
            d[s['@index']] += '\n'+s['#text']._x if d.get(s['@index']) else s['#text']._x # Can't call 'end' here yet
        x = [{"@index": k, "#text": self._text().add(v)} for k, v in d.items()]
        x = self._end_validate(x)
        return x
    
class MultiLangString(IndexedString, ABC):
    
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
        x = [{"@xml:lang": k, "#text": self._text().add(v)} for k, v in d.items()]
        x = self._end_validate(x)
        return x

class NoLangRestrictionMultiLangString(MultiLangString): # Can have multiple of the same lang
    
    def add(self, o):
        self._x = self._x if hasattr(self, '_x') else []
        for n in self._retrieve(o):
            self._x.append(n)
        return self
            
    def end(self):
        x = sorted(self._x, key=lambda x:x['@index'])
        for n in x:
            n['@xml:lang'] = n.pop('@lang')
            # n['#text'] = n['#text'].end()
            _ = n.pop('@index')
        x = self._end_validate(x)
        return x

class IndexedMultiLangString(MultiLangString):
    
    def end(self):
        x = sorted(self._x, key=lambda x:x['@index'])
        d = defaultdict(str)
        for s in x:
            d[(s['@index'], s['@lang'])] += '\n'+s['#text']._x if d.get((s['@index'], s['@lang'])) else s['#text']._x # Can't call 'end' here yet
        x = [{"@index": k[0], "@xml:lang": k[1], "#text": self._text().add(v)} for k, v in d.items()]
        x = self._end_validate(x)
        return x

class String20(MultiLangString):
    _text = BaseString20
    
class String40(MultiLangString):
    _text = BaseString40

class String80(MultiLangString):
    _text = BaseString80

class String80_NLR(NoLangRestrictionMultiLangString):
    _text = BaseString80

class String120(MultiLangString):
    _text = BaseString120

class ClassificationValueString120(String120):
    def end(self):
        x = super().end()
        return x[0] # Only one entry is possible here

class ExchangeNameString80(String80):
    def end(self):
        x = super().end()
        return x[0] # Only one entry is possible here
    
class Name(String120):
    def add(self, o, sep=', '):
        self._x = self._x if hasattr(self, '_x') else []
        self._add(o, sep=sep)
        return self

class String255(MultiLangString):
    _text = BaseString255

class String32000(MultiLangString):
    _text = BaseString32000

class IndexedStringSTR(IndexedString):
    _text = STR

class IndexedString32000(IndexedMultiLangString):
    _text = BaseString32000

class NamedString32000(NamedString):
    _text = BaseString32000

### Basic classes

class ECS2Uncertainty(DotDict):
    
    class __Lognormal(DotDict):
        
        VALID = {
            'a_meanValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
            'a_mu': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
            'a_variance': {'type': Real, 'mandatory': False, 'order': 0, 'unique': True}, # Not sure if it is mandatory
            'a_varianceWithPedigreeUncertainty': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
            }
        
    class __Normal(DotDict):
        
        VALID = {
            'a_meanValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
            'a_variance': {'type': Real, 'mandatory': False, 'order': 0, 'unique': True},
            'a_varianceWithPedigreeUncertainty': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
            }
    
    class __Triangular(DotDict):
        
        VALID = {
            'a_minValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
            'a_mostLikelyValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
            'a_maxValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
            }
    
    class __Uniform(DotDict):
        
        VALID = {
            'a_minValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
            'a_maxValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
            }
    
    class __Beta(DotDict):
        
        VALID = {
            'a_minValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
            'a_mostLikelyValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
            'a_maxValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
            }
    
    class __Gamma(DotDict):
        
        VALID = {
            'a_shape': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
            'a_scale': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
            'a_minValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
            }
    
    class __Binomial(DotDict):
        
        VALID = {
            'a_n': {'type': INT, 'mandatory': True, 'order': 0, 'unique': True},
            'a_p': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
            }
        
    class __Undefined(DotDict):
        
        VALID = {
            'a_minValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
            'a_maxValue': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
            'a_standardDeviation95': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
            }
    
    class __PedigreeMatrix(DotDict):
        
        VALID = {
            'a_reliability': {'type': PedigreeINT, 'mandatory': True, 'order': 0, 'unique': True},
            'a_completeness': {'type': PedigreeINT, 'mandatory': True, 'order': 0, 'unique': True},
            'a_temporalCorrelation': {'type': PedigreeINT, 'mandatory': True, 'order': 0, 'unique': True},
            'a_geographicalCorrelation': {'type': PedigreeINT, 'mandatory': True, 'order': 0, 'unique': True},
            'a_furtherTechnologyCorrelation': {'type': PedigreeINT, 'mandatory': True, 'order': 0, 'unique': True},
            }
    
    VALID = {
        'lognormal': {'type': __Lognormal, 'mandatory': False, 'order': 1, 'unique': True},
        'normal': {'type': __Normal, 'mandatory': False, 'order': 2, 'unique': True},
        'triangular': {'type': __Triangular, 'mandatory': False, 'order': 3, 'unique': True},
        'uniform': {'type': __Uniform, 'mandatory': False, 'order': 4, 'unique': True},
        'beta': {'type': __Beta, 'mandatory': False, 'order': 5, 'unique': True},
        'gamma': {'type': __Gamma, 'mandatory': False, 'order': 6, 'unique': True},
        'binomial': {'type': __Binomial, 'mandatory': False, 'order': 7, 'unique': True},
        'undefined': {'type': __Undefined, 'mandatory': False, 'order': 8, 'unique': True},
        'pedigreeMatrix': {'type': __PedigreeMatrix, 'mandatory': False, 'order': 9, 'unique': True},
        'comment': {'type': String32000, 'mandatory': False, 'order': 10, 'unique': False}
        }

class ECS2Source(DotDict):
    
    VALID = {
        'a_sourceId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE
        'a_sourceIdOverwrittenByChild': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True},
        'a_sourceContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'a_sourceYear': {'type': UniqueBaseString30, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE
        'a_sourceFirstAuthor': {'type': UniqueBaseString40, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE
        }

class ECS2QuantitativeReference(DotDict):
    
    VALID_NO_SOURCE = {
        'a_amount': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'a_mathematicalRelation': {'type': BaseString32000, 'mandatory': False, 'order': 0, 'unique': True},
        'a_isCalculatedAmount': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True},
        'comment': {'type': String32000, 'mandatory': False, 'order': 4, 'unique': False},
        'uncertainty': {'type': ECS2Uncertainty, 'mandatory': False, 'order': 3, 'unique': True}
        }
    
    VALID = ECS2Source.VALID | {
        'a_amount': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'a_mathematicalRelation': {'type': BaseString32000, 'mandatory': False, 'order': 0, 'unique': True},
        'a_isCalculatedAmount': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True},
        'comment': {'type': String32000, 'mandatory': False, 'order': 3, 'unique': False},
        'uncertainty': {'type': ECS2Uncertainty, 'mandatory': False, 'order': 4, 'unique': True}
        }
    
    VALID_PROP = ECS2Source.VALID | {
        'a_amount': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'a_mathematicalRelation': {'type': BaseString32000, 'mandatory': False, 'order': 0, 'unique': True},
        'a_isCalculatedAmount': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True},
        'comment': {'type': String32000, 'mandatory': False, 'order': 4, 'unique': False},
        'uncertainty': {'type': ECS2Uncertainty, 'mandatory': False, 'order': 3, 'unique': True}
        }
    
class ECS2QuantitativeReferenceWithUnit(DotDict):
    
    VALID = ECS2QuantitativeReference.VALID | {
        'a_variableName': {'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
        'a_unitId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'a_unitContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': ExchangeNameString80, 'mandatory': True, 'order': 1, 'unique': False},
        'unitName': {'type': String40, 'mandatory': True, 'order': 2, 'unique': False},
        }
    
    VALID_NO_SOURCE = ECS2QuantitativeReference.VALID_NO_SOURCE | { # Parameter doesn't have mandatoty unit id or name
        'a_variableName': {'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
        'a_unitId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'a_unitContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': ExchangeNameString80, 'mandatory': True, 'order': 1, 'unique': False},
        'unitName': {'type': String40, 'mandatory': False, 'order': 2, 'unique': False},
        }
    
    VALID_PROP = ECS2QuantitativeReference.VALID_PROP | { # Parameter doesn't have mandatoty unit id or name
        'a_variableName': {'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
        'a_unitId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'a_unitContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': ExchangeNameString80, 'mandatory': True, 'order': 1, 'unique': False},
        'unitName': {'type': String40, 'mandatory': False, 'order': 2, 'unique': False},
        }
    

class ECS2TextAndImage(DotDict):
    
    VALID = {
        'text': {'type': IndexedString32000, 'mandatory': False, 'order': 1, 'unique': False}, # Can't enumerate indexes beacuse this is separated
        'imageUrl': {'type': IndexedStringSTR, 'mandatory': False, 'order': 2, 'unique': False},
        'variable': {'type': NamedString32000, 'mandatory': False, 'order': 3, 'unique': False}
        }


class ECS2Classification(DotDict):
    
    VALID = {
        'a_classificationId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'a_classificationContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'classificationSystem': {'type': String255, 'mandatory': True, 'order': 1, 'unique': False},
        'classificationValue': {'type': ClassificationValueString120, 'mandatory': True, 'order': 2, 'unique': False}
        }

### Master data files

# xmlns="http://www.EcoInvent.org/UsedUserMasterData"
class ECS2UsedUserMasterData(DotDict):
    
    class __ActivityNameMaster(DotDict):
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': False}, # Double
            'name': {'type': String120, 'mandatory': True, 'order': 1, 'unique': False}
            }

    class __ClassificationSystemMaster(DotDict):
        
        class __ClassificationValue(DotDict):
            
            VALID = {
                'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'name': {'type': ClassificationValueString120, 'mandatory': True, 'order': 1, 'unique': False},
                'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
                }
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'a_type': {'type': TypeINT, 'mandatory': True, 'order': 0, 'unique': True}, # 1 = activity classification, 2 = product classification, 3 = activity and product classification
            'name': {'type': String255, 'mandatory': True, 'order': 1, 'unique': False},
            'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False},
            'classificationValue': {'type': __ClassificationValue, 'mandatory': True, 'order': 3, 'unique': False}
            }
    
    class __CompanyMaster(DotDict):
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'a_code': {'type': CompanyCode, 'mandatory': True, 'order': 0, 'unique': True},
            'a_website': {'type': BaseString255, 'mandatory': False, 'order': 0, 'unique': True},
            'name': {'type': String255, 'mandatory': False, 'order': 1, 'unique': False},
            'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
            }
        
    class __CompartmentMaster(DotDict):
        
        class __SubcompartmentMaster(DotDict):
            
            VALID = {
                'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'name': {'type': String40, 'mandatory': True, 'order': 1, 'unique': False},
                'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
                }
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'name': {'type': String40, 'mandatory': True, 'order': 1, 'unique': False},
            'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False},
            'subcompartment': {'type': __SubcompartmentMaster, 'mandatory': True, 'order': 3, 'unique': False}
            }
    
    class __ElementaryMaster(DotDict):
        
        class __Compartment(DotDict):
            
            VALID = {
                'a_subcompartmentId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_subcompartmentContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'compartment': {'type': String40, 'mandatory': True, 'order': 1, 'unique': False},
                'subcompartment': {'type': String40, 'mandatory': True, 'order': 2, 'unique': False}
                }
            
        class __Property(DotDict):
            
            VALID = ECS2QuantitativeReferenceWithUnit.VALID_PROP | {
                'a_propertyId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_propertyContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_isDefiningValue': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True}
                }
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'a_unitId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'a_unitContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
            'a_formula': {'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
            'a_casNumber': {'type': CASNumber, 'mandatory': False, 'order': 0, 'unique': True},
            'a_defaultVariableName': {'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
            'name': {'type': String120, 'mandatory': True, 'order': 1, 'unique': False},
            'unitName': {'type': String40, 'mandatory': True, 'order': 2, 'unique': False},
            'compartment': {'type': __Compartment, 'mandatory': True, 'order': 3, 'unique': False},
            'comment': {'type': String32000, 'mandatory': False, 'order': 4, 'unique': False},
            'synonym': {'type': String80_NLR, 'mandatory': False, 'order': 5, 'unique': False},
            'property': {'type': __Property, 'mandatory': False, 'order': 6, 'unique': False},
            'productInformation': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 7, 'unique': False}
            }
    
    class __GeographyMaster(DotDict):
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'a_longitude': {'type': Real, 'mandatory': False, 'order': 0, 'unique': True},
            'a_latitude': {'type': Real, 'mandatory': False, 'order': 0, 'unique': True},
            'a_ISOTwoLetterCode': {'type': ISOTwoLetterCode, 'mandatory': False, 'order': 0, 'unique': True},
            'a_ISOThreeLetterCode': {'type': ISOThreeLetterCode, 'mandatory': False, 'order': 0, 'unique': True},
            'a_uNCode': {'type': INT, 'mandatory': False, 'order': 0, 'unique': True}, # INT1
            'a_uNRegionCode': {'type': INT, 'mandatory': False, 'order': 0, 'unique': True},
            'a_uNSubregionCode': {'type': INT, 'mandatory': False, 'order': 0, 'unique': True},
            'name': {'type': String255, 'mandatory': True, 'order': 1, 'unique': False},
            'shortname': {'type': String40, 'mandatory': True, 'order': 2, 'unique': False},
            'comment': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 3, 'unique': False},
            # 'kml': {'type':}
            }
    
    class __IntermediateMaster(DotDict):
            
        class __Property(DotDict):
            
            VALID = ECS2QuantitativeReferenceWithUnit.VALID_PROP | {
                'a_propertyId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_propertyContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_isDefiningValue': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True}
                }
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'a_unitId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'a_unitContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
            'a_casNumber': {'type': CASNumber, 'mandatory': False, 'order': 0, 'unique': True},
            'a_defaultVariableName': {'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
            'name': {'type': String120, 'mandatory': True, 'order': 1, 'unique': False},
            'unitName': {'type': String40, 'mandatory': True, 'order': 2, 'unique': False},
            'classification': {'type': ECS2Classification, 'mandatory': False, 'order': 3, 'unique': False},
            'comment': {'type': String32000, 'mandatory': False, 'order': 4, 'unique': False},
            'synonym': {'type': String80_NLR, 'mandatory': False, 'order': 5, 'unique': False},
            'property': {'type': __Property, 'mandatory': False, 'order': 6, 'unique': False},
            'productInformation': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 7, 'unique': False}
            }
    
    class __LanguageMaster(DotDict):
        
        VALID = {
            'a_code': {'type': Lang, 'mandatory': True, 'order': 0, 'unique': True},
            'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
            }
    
    class __MacroEconomicScenarioMaster(DotDict):
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'name': {'type': String80, 'mandatory': True, 'order': 1, 'unique': False},
            'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
            }
    
    class __ParameterMaster(DotDict):
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'a_defaultVariableName': {'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
            'a_unitId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
            'a_unitContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
            'name': {'type': String80, 'mandatory': True, 'order': 1, 'unique': False},
            'unitName': {'type': String40, 'mandatory': False, 'order': 2, 'unique': False},
            'comment': {'type': String32000, 'mandatory': False, 'order': 3, 'unique': False}
            }
    
    class __PersonMaster(DotDict):
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'a_name': {'type': BaseString40, 'mandatory': True, 'order': 0, 'unique': True},
            'a_address': {'type': BaseString255, 'mandatory': False, 'order': 0, 'unique': True},
            'a_telephone': {'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
            'a_telefax': {'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
            'a_email': {'type': BaseString80, 'mandatory': True, 'order': 0, 'unique': True},
            'a_companyId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
            'a_companyContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
            'companyName': {'type': String255, 'mandatory': False, 'order': 1, 'unique': False}
            }
    
    class __PropertyMaster(DotDict):
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'a_defaultVariableName': {'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
            'a_unitId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
            'a_unitContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
            'name': {'type': String80, 'mandatory': True, 'order': 1, 'unique': False},
            'unitName': {'type': String40, 'mandatory': False, 'order': 2, 'unique': False},
            'comment': {'type': String32000, 'mandatory': False, 'order': 3, 'unique': False}
            }
    
    class __SourceMaster(DotDict):
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'a_sourceType': {'type': SourceTypeINT, 'mandatory': True, 'order': 0, 'unique': True},
            'a_year': {'type': BaseString30, 'mandatory': False, 'order': 0, 'unique': True},
            'a_volumeNo': {'type': INT, 'mandatory': False, 'order': 0, 'unique': True},
            'a_firstAuthor': {'type': BaseString40, 'mandatory': True, 'order': 0, 'unique': True},
            'a_additionalAuthors': {'type': BaseString255, 'mandatory': False, 'order': 0, 'unique': True},
            'a_title': {'type': BaseString255, 'mandatory': True, 'order': 0, 'unique': True},
            'a_shortName': {'type': BaseString80, 'mandatory': False, 'order': 0, 'unique': True},
            'a_pageNumbers': {'type': BaseString30, 'mandatory': False, 'order': 0, 'unique': True},
            'a_nameOfEditors': {'type': BaseString255, 'mandatory': False, 'order': 0, 'unique': True},
            'a_titleOfAnthology': {'type': BaseString255, 'mandatory': False, 'order': 0, 'unique': True},
            'a_placeOfPublications': {'type': BaseString32000, 'mandatory': False, 'order': 0, 'unique': True},
            'a_publisher': {'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
            'a_journal': {'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
            'a_issueNo': {'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
            'comment': {'type': String32000, 'mandatory': False, 'order': 1, 'unique': False}
            }
    
    class __SystemModelMaster(DotDict):
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'name': {'type': String120, 'mandatory': True, 'order': 1, 'unique': False},
            'shortname': {'type': String20, 'mandatory': True, 'order': 2, 'unique': False},
            'comment': {'type': String32000, 'mandatory': False, 'order': 3, 'unique': False}
            }
        
    class __TagMaster(DotDict):
        
        VALID = {
            'a_name': {'type': BaseString40, 'mandatory': True, 'order': 0, 'unique': True},
            'comment': {'type': String32000, 'mandatory': False, 'order': 1, 'unique': False}
            }
        
    class __UnitMaster(DotDict):
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'name': {'type': String40, 'mandatory': True, 'order': 1, 'unique': False},
            'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
            }
    
    class __ActivityIndexEntryMaster(DotDict):
        
        VALID = {
            'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True}, # OK
            'a_activityNameId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': False}, # OK
            'a_geographyId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True}, # OK
            'a_startDate': {'type': Date, 'mandatory': True, 'order': 0, 'unique': True},
            'a_endDate': {'type': Date, 'mandatory': True, 'order': 0, 'unique': True},
            'a_specialActivityType': {'type': SpecialActivityTypeINT, 'mandatory': True, 'order': 0, 'unique': True},
            'a_systemModelId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True}
            }
    
    VALID = {
        'activityName': {'type': __ActivityNameMaster, 'mandatory': False, 'order': 0, 'unique': False},
        'language': {'type': __LanguageMaster, 'mandatory': False, 'order': 1, 'unique': False},
        'geography': {'type': __GeographyMaster, 'mandatory': False, 'order': 2, 'unique': False},
        'systemModel': {'type': __SystemModelMaster, 'mandatory': False, 'order': 3, 'unique': False},
        'tag': {'type': __TagMaster, 'mandatory': False, 'order': 4, 'unique': False},
        'macroEconomicScenario': {'type': __MacroEconomicScenarioMaster, 'mandatory': False, 'order': 5, 'unique': False},
        'compartment': {'type': __CompartmentMaster, 'mandatory': False, 'order': 6, 'unique': False},
        'classificationSystem': {'type': __ClassificationSystemMaster, 'mandatory': False, 'order': 7, 'unique': False},
        'company': {'type': __CompanyMaster, 'mandatory': False, 'order': 8, 'unique': False},
        'person': {'type': __PersonMaster, 'mandatory': False, 'order': 9, 'unique': False},
        'source': {'type': __SourceMaster, 'mandatory': False, 'order': 10, 'unique': False},
        'units': {'type': __UnitMaster, 'mandatory': False, 'order': 11, 'unique': False},
        'parameter': {'type': __ParameterMaster, 'mandatory': False, 'order': 12, 'unique': False},
        'property': {'type': __PropertyMaster, 'mandatory': False, 'order': 13, 'unique': False},
        # 'context': {'type': __ContextMaster, 'mandatory': False, 'order': 4, 'unique': False},
        'elementaryExchange': {'type': __ElementaryMaster, 'mandatory': False, 'order': 14, 'unique': False},
        'intermediateExchange': {'type': __IntermediateMaster, 'mandatory': False, 'order': 15, 'unique': False},
        'activityIndexEntry': {'type': __ActivityIndexEntryMaster, 'mandatory': False, 'order': 16, 'unique': True},
        }


### Regular classes

class ECS2CustomExchange(DotDict):
    
    class __Property(DotDict):
        
        VALID = ECS2QuantitativeReferenceWithUnit.VALID_PROP | {
            'a_propertyId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
            'a_propertyContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
            'a_isDefiningValue': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True}
            }
    
    class __TransferCoefficient(DotDict):
        
        VALID = ECS2QuantitativeReference.VALID | {
            'a_exchangeId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True}
            }
    
    VALID = ECS2QuantitativeReferenceWithUnit.VALID | {
        'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'a_casNumber': {'type': CASNumber, 'mandatory': False, 'order': 0, 'unique': True},
        'a_pageNumbers': {'type': BaseString30, 'mandatory': False, 'order': 0, 'unique': True},
        'a_specificAllocationPropertyId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'a_specificAllocationPropertyIdOverwrittenByChild': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True},
        'a_specificAllocationPropertyContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'synonym': {'type': String80_NLR, 'mandatory': False, 'order': 5, 'unique': False},
        'property': {'type': __Property, 'mandatory': False, 'order': 6, 'unique': False},
        'transferCoefficient': {'type': __TransferCoefficient, 'mandatory': False, 'order': 7, 'unique': False},
        'tag': {'type': BaseString40, 'mandatory': False, 'order': 8, 'unique': False}
        }


class ECS2Structure:
        
    class ActivityDescription(DotDict):
        
        class __Activity(DotDict):
            
            VALID = {
                'a_id': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_activityNameId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': False}, # Actualy unique, but double entry
                'a_activityNameContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_parentActivityId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_parentActivityContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_inheritanceDepth': {'type': InheritanceDepthINT, 'mandatory': True, 'order': 0, 'unique': False}, # [DEFAULT] Actualy not mandatory but can be filled with default
                'a_type': {'type': TypeINT, 'mandatory': True, 'order': 0, 'unique': True},
                'a_specialActivityType': {'type': SpecialActivityTypeINT, 'mandatory': True, 'order': 0, 'unique': False}, # Actualy unique, but double entry
                'a_energyValues': {'type': EnergyValuesINT, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE [DEFAULT]
                'a_masterAllocationPropertyId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_masterAllocationPropertyIdOverwrittenByChild': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True},
                'a_masterAllocationPropertyContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_datasetIcon': {'type': STR, 'mandatory': False, 'order': 0, 'unique': True},
                'activityName': {'type': Name, 'mandatory': True, 'order': 1, 'unique': False},
                'synonym': {'type': String80_NLR, 'mandatory': False, 'order': 2, 'unique': False},
                'includedActivitiesStart': {'type': String32000, 'mandatory': False, 'order': 3, 'unique': False}, # If LCI, has to be "From cradle, including..."
                'includedActivitiesEnd': {'type': String32000, 'mandatory': False, 'order': 4, 'unique': False},
                'allocationComment': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 5, 'unique': True},
                'generalComment': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 6, 'unique': True},
                'tag': {'type': BaseString40, 'mandatory': False, 'order': 7, 'unique': False}
                }
    
        class __Geography(DotDict):
            
            VALID = {
                'a_geographyId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_geographyContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'shortname': {'type': String40, 'mandatory': True, 'order': 1, 'unique': False},
                'comment': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 2, 'unique': True}
                }
    
        class __Technology(DotDict):
            
            VALID = {
                'a_technologyLevel': {'type': TechnologyLevelINT, 'mandatory': True, 'order': 0, 'unique': False}, # DEFAULT
                'comment': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 1, 'unique': True}
                }
            
        class __TimePeriod(DotDict):
            
            VALID = {
                'a_startDate': {'type': Date, 'mandatory': True, 'order': 0, 'unique': True},
                'a_endDate': {'type': Date, 'mandatory': True, 'order': 0, 'unique': True},
                'a_isDataValidForEntirePeriod': {'type': BOOL, 'mandatory': True, 'order': 0, 'unique': False}, # Actualy unique, but double entry
                'comment': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 1, 'unique': True}
                }
            
        class __MacroEconomicScenario(DotDict):
            
            VALID = {
                'a_macroEconomicScenarioId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_macroEconomicScenarioContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'name': {'type': String80, 'mandatory': True, 'order': 1, 'unique': False},
                'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': True}
                }
        
        VALID = {
            'activity': {'type': __Activity, 'mandatory': True, 'order': 1, 'unique': True},
            'classification': {'type': ECS2Classification, 'mandatory': False, 'order': 2, 'unique': False},
            'geography': {'type': __Geography, 'mandatory': True, 'order': 3, 'unique': True},
            'technology': {'type': __Technology, 'mandatory': True, 'order': 4, 'unique': True},
            'timePeriod': {'type': __TimePeriod, 'mandatory': True, 'order': 5, 'unique': True},
            'macroEconomicScenario': {'type': __MacroEconomicScenario, 'mandatory': True, 'order': 6, 'unique': True},
            }
    
    class ModellingAndValidation(DotDict):
        
        class __Representativeness(DotDict):
            
            VALID = {
                'a_percent': {'type': Percent, 'mandatory': False, 'order': 0, 'unique': True},
                'a_systemModelId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_systemModelContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'systemModelName': {'type': String120, 'mandatory': True, 'order': 1, 'unique': False},
                'samplingProcedure': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False},
                'extrapolations': {'type': String32000, 'mandatory': False, 'order': 3, 'unique': False}
                }
            
        class __Review(DotDict):
            
            VALID = {
                'a_reviewerId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_reviewerContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_reviewerName': {'type': BaseString40, 'mandatory': True, 'order': 0, 'unique': True},
                'a_reviewerEmail': {'type': BaseString80, 'mandatory': True, 'order': 0, 'unique': True},
                'a_reviewDate': {'type': Date, 'mandatory': True, 'order': 0, 'unique': True},
                'a_reviewedMajorRelease': {'type': INT, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
                'a_reviewedMinorRelease': {'type': INT, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
                'a_reviewedMajorRevision': {'type': INT, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
                'a_reviewedMinorRevision': {'type': INT, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
                'details': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 1, 'unique': False},
                'otherDetails': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
                }
        
        VALID = {
            'representativeness': {'type': __Representativeness, 'mandatory': False, 'order': 1, 'unique': True},
            'review': {'type': __Review, 'mandatory': False, 'order': 2, 'unique': False}
            }
        
    class AdministrativeInformation(DotDict):
        
        class __DataEntryBy(DotDict):
            
            VALID = {
                'a_personId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_personContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_isActiveAuthor': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True},
                'a_personName': {'type': BaseString40, 'mandatory': True, 'order': 0, 'unique': True},
                'a_personEmail': {'type': BaseString80, 'mandatory': True, 'order': 0, 'unique': True}
                }
            
        class __DataGeneratorAndPublication(DotDict):
            
            VALID = {
                'a_personId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_personContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_personName': {'type': BaseString40, 'mandatory': True, 'order': 0, 'unique': True},
                'a_personEmail': {'type': BaseString80, 'mandatory': True, 'order': 0, 'unique': True},
                'a_dataPublishedIn': {'type': DataPublishedInINT, 'mandatory': False, 'order': 0, 'unique': True},
                'a_publishedSourceId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_publishedSourceIdOverwrittenByChild': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True},
                'a_publishedSourceContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_publishedSourceYear': {'type': BaseString30, 'mandatory': False, 'order': 0, 'unique': True},
                'a_publishedSourceFirstAuthor': {'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
                'a_isCopyrightProtected': {'type': BOOL, 'mandatory': True, 'order': 0, 'unique': True},
                'a_pageNumbers': {'type': BaseString30, 'mandatory': False, 'order': 0, 'unique': True},
                'a_accessRestrictedTo': {'type': AccessRestrictedToINT, 'mandatory': False, 'order': 0, 'unique': False}, # Double
                'a_companyId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': False}, # Can have duplicates
                'a_companyIdOverwrittenByChild': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True},
                'a_companyContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_companyCode': {'type': CompanyCode, 'mandatory': False, 'order': 0, 'unique': False} # Can have duplicates
                }
            
        class __FileAttributes(DotDict):
            
            class __RequiredContextReference(DotDict):
                
                VALID = {
                    'a_majorRelease': {'type': INT, 'mandatory': True, 'order': 0, 'unique': False}, # Double
                    'a_minorRelease': {'type': INT, 'mandatory': True, 'order': 0, 'unique': False}, # Double
                    'a_majorRevision': {'type': INT, 'mandatory': False, 'order': 0, 'unique': False}, # Double
                    'a_minorRevision': {'type': INT, 'mandatory': False, 'order': 0, 'unique': False}, # Double
                    'a_requiredContextId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                    'a_requiredContextFileLocation': {'type': STR, 'mandatory': False, 'order': 0, 'unique': True},
                    'requiredContextName': {'type': String80, 'mandatory': True, 'order': 1, 'unique': False}
                    }
            
            VALID = {
                'a_majorRelease': {'type': INT, 'mandatory': True, 'order': 0, 'unique': False}, # Double
                'a_minorRelease': {'type': INT, 'mandatory': True, 'order': 0, 'unique': False}, # Double
                'a_majorRevision': {'type': INT, 'mandatory': True, 'order': 0, 'unique': False}, # Double
                'a_minorRevision': {'type': INT, 'mandatory': True, 'order': 0, 'unique': False}, # Double
                'a_internalSchemaVersion': {'type': BaseString80, 'mandatory': False, 'order': 0, 'unique': True},
                'a_defaultLanguage': {'type': Lang, 'mandatory': False, 'order': 0, 'unique': True},
                'a_creationTimestamp': {'type': CompleteDate, 'mandatory': False, 'order': 0, 'unique': True},
                'a_lastEditTimestamp': {'type': CompleteDate, 'mandatory': False, 'order': 0, 'unique': True},
                'a_fileGenerator': {'type': BaseString255, 'mandatory': True, 'order': 0, 'unique': True},
                'a_fileTimestamp': {'type': CompleteDate, 'mandatory': True, 'order': 0, 'unique': True},
                'a_contextId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'contextName': {'type': String80, 'mandatory': False, 'order': 1, 'unique': False},
                'requiredContext': {'type': __RequiredContextReference, 'mandatory': False, 'order': 2, 'unique': False}
                }
        
        VALID = {
            'dataEntryBy': {'type': __DataEntryBy, 'mandatory': True, 'order': 1, 'unique': True},
            'dataGeneratorAndPublication': {'type': __DataGeneratorAndPublication, 'mandatory': True, 'order': 2, 'unique': True},
            'fileAttributes': {'type': __FileAttributes, 'mandatory': True, 'order': 3, 'unique': True}
            }
        
    class FlowData(DotDict):
        
        class __IntermediateExchange(ECS2CustomExchange, DotDict):
            
            VALID = ECS2CustomExchange.VALID | {
                'a_intermediateExchangeId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_intermediateExchangeContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_activityLinkId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_activityLinkIdOverwrittenByChild': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True},
                'a_activityLinkContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_productionVolumeAmount': {'type': Real, 'mandatory': False, 'order': 0, 'unique': True},
                'a_productionVolumeVariableName': {'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
                'a_productionVolumeMathematicalRelation': {'type': BaseString32000, 'mandatory': False, 'order': 0, 'unique': True},
                'a_productionVolumeSourceId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_productionVolumeSourceIdOverwrittenByChild': {'type': BOOL, 'mandatory': False, 'order': 0, 'unique': True},
                'a_productionVolumeSourceContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_productionVolumeSourceYear': {'type': BaseString30, 'mandatory': False, 'order': 0, 'unique': True},
                'a_productionVolumeSourceFirstAuthor': {'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
                'productionVolumeComment': {'type': String32000, 'mandatory': False, 'order': 9, 'unique': False},
                'productionVolumeUncertainty': {'type': ECS2Uncertainty, 'mandatory': False, 'order': 10, 'unique': True},
                'classification': {'type': ECS2Classification, 'mandatory': False, 'order': 11, 'unique': False},
                'inputGroup': {'type': InputGroupIntermediateINT, 'mandatory': False, 'order': 12, 'unique': True},
                'outputGroup': {'type': OutputGroupIntermediateINT, 'mandatory': False, 'order': 13, 'unique': True},
                }
            
        class __ElementaryExchange(DotDict):
            
            class __Compartment(DotDict):
                
                VALID = {
                    'a_subcompartmentId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                    'a_subcompartmentContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                    'compartment': {'type': String40, 'mandatory': True, 'order': 1, 'unique': False},
                    'subcompartment': {'type': String40, 'mandatory': True, 'order': 2, 'unique': False}
                    }
            
            VALID = ECS2CustomExchange.VALID | {
                'a_elementaryExchangeId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_elementaryExchangeContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_formula': {'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
                'compartment': {'type': __Compartment, 'mandatory': True, 'order': 9, 'unique': True},
                'inputGroup': {'type': InputGroupElementaryINT, 'mandatory': False, 'order': 10, 'unique': True},
                'outputGroup': {'type': OutputGroupElementaryINT, 'mandatory': False, 'order': 11, 'unique': True}
                }
            
        class __Parameter(DotDict):
            
            VALID = ECS2QuantitativeReferenceWithUnit.VALID_NO_SOURCE | {
                'a_parameterId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_parameterContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True}
                }
            
        class __ImpactIndicator(DotDict):
            
            VALID = {
                'a_impactIndicatorId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_impactIndicatorContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_impactMethodId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_impactMethodContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_impactCategoryId': {'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
                'a_impactCategoryContextId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
                'a_amount': {'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
                'impactMethodName': {'type': String120, 'mandatory': True, 'order': 1, 'unique': False},
                'impactCategoryName': {'type': String120, 'mandatory': True, 'order': 2, 'unique': False},
                'name': {'type': String120, 'mandatory': True, 'order': 3, 'unique': False},
                'unitName': {'type': String40, 'mandatory': True, 'order': 4, 'unique': False}
                }
        
        VALID = {
            'intermediateExchange': {'type': __IntermediateExchange, 'mandatory': True, 'order': 1, 'unique': False},
            'elementaryExchange': {'type': __ElementaryExchange, 'mandatory': False, 'order': 2, 'unique': False},
            'parameter': {'type': __Parameter, 'mandatory': False, 'order': 3, 'unique': False},
            'impactIndicator': {'type': __ImpactIndicator, 'mandatory': False, 'order': 4, 'unique': False}
            }
    
    def __init__(self):
        self.activityDescription = self.ActivityDescription()
        self.flowData = self.FlowData()
        self.modellingAndValidation = self.ModellingAndValidation()
        self.administrativeInformation = self.AdministrativeInformation()
        
        self.textAndImage = ECS2TextAndImage
        self.property = ECS2CustomExchange()
        
        self.userMaster = ECS2UsedUserMasterData()
        
        self.main_activity_type = 'activityDataset'
        
    def get_dict(self):
        # print('\n\n', self.userMaster.get_dict())
        return {
            'ecoSpold': {
                '@xmlns': 'http://www.EcoInvent.org/EcoSpold02',
                'activityDataset': { # self.main_activity_type [child datasets are not accept by ecoeditor]
                    'activityDescription': self.activityDescription.get_dict(),
                    'flowData': self.flowData.get_dict(),
                    'modellingAndValidation': self.modellingAndValidation.get_dict(),
                    'administrativeInformation': self.administrativeInformation.get_dict()
                    },
                'usedUserMasterData': {
                    '@xmlns': 'http://www.EcoInvent.org/UsedUserMasterData',
                    **self.userMaster.get_dict()
                    }
                }
            }

class LIST(Validator):
    def _validate(self, x):
        return x
    def add(self, o):
        if not isinstance(o, list):
            o = [o]
        if not hasattr(self, '_x'):
            self._x = self._validate(o)
        else:
            self._x.extend(self._validate(o))
        return self
    def end(self):
        return self._x

class ILCD1ToECS2DataNotConverted(DotDict):

    VALID = {
        'identifierOfSubDataSet': {'type': STR, 'mandatory': False},
        'complementingProcesses': {'type': LIST, 'mandatory': False},
        'functionalUnitOrOther': {'type': LIST, 'mandatory': False},
        'a_type': {'type': STR, 'mandatory': False},
        'a_latitudeAndLongitude': {'type': STR, 'mandatory': False},
        'subLocationOfOperationSupplyOrProduction': {'type': LIST, 'mandatory': False},
        'referenceToIncludedProcesses': {'type': LIST, 'mandatory': False},
        'LCIMethodPrinciple': {'type': STR, 'mandatory': False},
        'referenceToLCAMethodDetails': {'type': LIST, 'mandatory': False},
        'referenceToDataHandlingPrinciples': {'type': LIST, 'mandatory': False},
        'referenceToDataSource': {'type': LIST, 'mandatory': False},
        'annualSupplyOrProductionVolume': {'type': LIST, 'mandatory': False},
        'completeness': {'type': LIST, 'mandatory': False},
        'compliance': {'type': LIST, 'mandatory': False},
        'commissionerAndGoal': {'type': LIST, 'mandatory': False},
        'timeStamp': {'type': STR, 'mandatory': False},
        'referenceToDataSetFormat': {'type': LIST, 'mandatory': False},
        'referenceToConvertedOriginalDataSetFrom': {'type': LIST, 'mandatory': False},
        'referenceToDataSetUseApproval': {'type': LIST, 'mandatory': False},
        'dateOfLastRevision': {'type': STR, 'mandatory': False},
        'referenceToPrecedingDataSetVersion': {'type': LIST, 'mandatory': False},
        'permanentDataSetURI': {'type': STR, 'mandatory': False},
        'referenceToRegistrationAuthority': {'type': LIST, 'mandatory': False},
        'registrationNumber': {'type': STR, 'mandatory': False},
        'referenceToOwnershipOfDataSet': {'type': LIST, 'mandatory': False},
        'accessRestrictions': {'type': STR, 'mandatory': False},
    }

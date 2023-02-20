#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 29 20:27:53 2023

@author: jotape42p
"""

from .enumerations import Languages
from .general_validators import (
    list_add,
    return_comparisson_add,
    Date,
    UnlimitedString,
    MultiLangString,
    return_limited_int,
    return_limited_string,
    return_pattern
    )

Int1 = return_limited_int(1)
Int6 = return_limited_int(6, func=lambda x,y: x>y)
Int6List = return_limited_int(6, func=lambda x,y: x>y, add_func=list_add)
Year = return_limited_int(4)

Version = return_pattern(r'\d{2}\.\d{2}(\.\d{3})?')
GIS = return_pattern(r'\s*([\-+]?(([0-8]?\d)(\.\d*)?)|(90(\.0{0,2})?))\s*;\s*(([\-+]?(((1[0-7]\d)(\.\d*)?)|([0-9]\d(\.\d*)?)|(\d(\.\d*)?)|(180(\.[0]*)?))))\s*')

class DateTime(Date):
    def end(self):
        return self._x.isoformat()

class ReviewDateTime(DateTime):
    add = return_comparisson_add(lambda x,y: x.replace(tzinfo=None) > y.replace(tzinfo=None))

FT = UnlimitedString
String = return_limited_string((1,500))
NullableString = return_limited_string(500)
ST = return_limited_string(1000)
MatV = return_limited_string(50)

class MultiLang(MultiLangString):
    
    def _validate(self, x):
        x = super()._validate(x)
        if x['@lang'] not in Languages:
            raise ValueError(f'{self.__class__.__name__}: {x["@lang"]} is not a valid language')
        return x

class StringMultiLang(MultiLang):
    _text = String
class FTMultiLang(MultiLang):
    _text = FT
class STMultiLang(MultiLang):
    _text = ST

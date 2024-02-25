#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 29 20:46:08 2023

@author: jotape42p
"""

import pytest

from src.Lavoisier.data_structures.validators.general_validators import (
    _add,
    list_add,
    separator_add,
    Real,
    Bool,
    Int,
    return_collection,
    return_limited_int,
    UUID,
    Date,
    Str,
    UnlimitedString,
    return_limited_string,
    return_enum,
    IndexedString,
    MultiLangString,
    NoLangRestrictionMultiLangString,
    IndexedMultiLangString,
    # ignore_limits
    )
from src.Lavoisier.data_structures.validators.ILCD1_validators import (
    Version,
    GIS,
    DateTime,
    ReviewDateTime,
    MultiLang,
    StringMultiLang,
    FTMultiLang,
    STMultiLang
    )
from src.Lavoisier.data_structures.validators.ECS2_validators import (
    Percent,
    Bool as ECS2Bool,
    Date as ECS2Date,
    CASNumber,
    CompleteDate,
    VariableName,
    NamedString,
    ClassificationValueString120,
    ExchangeNameString80,
    Name
    )
from src.Lavoisier.data_structures.validators.enumerations import Languages

from collections import defaultdict
from datetime import datetime
from itertools import combinations, product
from copy import deepcopy # Essencial to duplicates since they alter the content from one to another, always use

IndexedString._text = UnlimitedString
MultiLangString._text = UnlimitedString
MultiLang._text = UnlimitedString
NoLangRestrictionMultiLangString._text = UnlimitedString
IndexedMultiLangString._text = UnlimitedString
NamedString._text = UnlimitedString

########## Single Input

# Real: normal, string, string and integer, string and zero, string and negative, integer, integer and zero, zero
_real = ((2.0,2.0),('2.0',2.0),('2',2.0),('0',0.0),('-2',-2.0),(2,2.0),(0,0.0),(0.0,0.0))

# ECS2 Percent: normal, higher decimal places
_ecs2perc = ((10.0,'10.0'),(23.67,'23.7'))

# Bool: all cases
_bool = (('true',True),('false',False),('True',True),('False',False),(1,True),(0,False),('1',True),('0',False),(True,)*2,(False,)*2)

# Int: normal, float, [NOT ABLE] float and string, float and zero, string, string and zero, zero
_int = ((2,2),(2.0,2),(0.0,0),('2',2),('0',0),(0,0))

# return_limited_int: normal, list_add, func + list_add
n = lambda x,lim: x!=lim
_lint = ((1,n,_add,0,0), (4,n,list_add,2002,2002), (6,lambda x,lim: x>lim,list_add,0,0))

# return_collections: single int, range, incomplete set, negative
_lcol = (({4},False,4,4), (set(range(1,4)),False,2,2), ({1,2,3,5},False,3,3), (set(range(-1,4)),True,-1,-1))

# return_limited_string: normal, add 
_lstr = ((30,separator_add,'lol','lol'),(30,_add,'lol','lol'))
    
# return_pattern: Patterns are verified using the pattern outputs (UUID, Version, etc)
# UUID: case
_uuid = ('4dfe5a1f-cd1a-4fb3-87bf-55bfc40e0818','4dfe5a1f-cd1a-4fb3-87bf-55bfc40e0818')

# Version: case
_version = ('00.00.000', '00.00.000')

# GIS: cases
_GIS = (("+42.42;-180",)*2,("0;0",)*2,("13.22 ; -3",)*2)

# VariableName: case
_varn = ('some_name','some_name')

# CASNumber: case
_cas = (('7732-18-5',)*2,('18540-29-9',)*2,('8007-40-7',)*2)

# Date, DateTime, CompleteDate and ReviewDateTime: normal, 2000, with hours, with Z
dtf_def = lambda x: datetime.fromisoformat(x).isoformat()
dtf_ecs2  = lambda x: datetime.fromisoformat(x).strftime('%Y-%m-%d')
cdtf_ecs2 = lambda x: datetime.fromisoformat(x).strftime('%Y-%m-%dT%H:%M:%S')

_def_dt = ('1981-04-05','2000-01-01','2019-08-19T13:47:30','2019-08-19T13:47:31Z'.replace('Z','+00:00'))
_dt_ilcd1 = zip(_def_dt, [dtf_def(x) for x in _def_dt])
_dt_ecs2 = zip(_def_dt, [dtf_ecs2(x) for x in _def_dt])
_cdt_ecs2 = zip(_def_dt, [cdtf_ecs2(x) for x in _def_dt])

# Enumerations: normal, list
_enum_n = (('en',)*2,('pt',)*2,('fr',)*2)
_enum_l = (('aa',['aa']),(['en', 'fr'],)*2,(['pt'],)*2,(['pt','pt'],['pt']))

# Str: normal, null
_str = (('a',)*2,('b',)*2,('',)*2)

# Dict String Types
indx = (1, 2, 3, 4, 5)
lang = ('ar', 'de', 'en', 'fr', 'pt')
text = ('', 'lol', 'lol1','lol2','lol3')

nm_gen = lambda n, t, sep='; ': {'@name': text[n], '#text': text[t] if isinstance(t, int) else sep.join([text[x] for x in t])}
in_gen = lambda i, t, sep='; ': {'@index': indx[i], '#text': text[t] if isinstance(t, int) else sep.join([text[x] for x in t])}
mt_gen = lambda l, i, t, sep='; ': {'@index': indx[i], '@lang': lang[l], '#text': text[t] if isinstance(t, int) else sep.join([text[x] for x in t])}
lg_gen = lambda l, t, sep='; ': {'@xml:lang': lang[l], '#text': text[t] if isinstance(t, int) else sep.join([text[x] for x in t])}
lgi_gen = lambda l, i, t, sep='; ': {'@index': indx[i], '@xml:lang': lang[l], '#text': text[t] if isinstance(t, int) else sep.join([text[x] for x in t])}

# String combinations
_base = (([],[]),)
_namedstr = _base + ((nm_gen(0,0),[]), (nm_gen(1,1),[nm_gen(1,1)]))
_indexstr = _base + ((in_gen(0,0),[]), (in_gen(0,1),[in_gen(0,1)]))
_multlstr = _base + ((mt_gen(0,0,0),[]), (mt_gen(0,0,1),[lg_gen(0,1)]))
_nolanstr = _base + ((mt_gen(0,0,0),[]), (mt_gen(0,0,1),[lg_gen(0,1)]))
_imlanstr = _base + ((mt_gen(0,0,0),[]), (mt_gen(0,0,1),[lgi_gen(0,0,1)]))


@pytest.mark.validator
@pytest.mark.single_input
@pytest.mark.parametrize('class_, type_, input_, validation_result',
                         [
                             *((Real, float, a, b) for a, b in deepcopy(_real)),
                             *((Percent, str, a, b) for a, b in deepcopy(_ecs2perc)),
                             *((Bool, bool, a, b) for a, b in deepcopy(_bool)),
                             *((ECS2Bool, str, a, 'true' if b else 'false') for a, b in deepcopy(_bool)),
                             *((Int, int, a, b) for a, b in deepcopy(_int)),
                             *((return_limited_int(a, func=b, add_func=c), int, d, e) for a, b, c, d, e in deepcopy(_lint)),
                             *((return_collection(a, b), int, c, d) for a, b, c, d in deepcopy(_lcol)),
                             *((return_limited_string(a, add_func=b), str, c, d) for a, b, c, d in deepcopy(_lstr)),
                             (UUID, str)+deepcopy(_uuid),
                             (Version, str)+deepcopy(_version),
                             *((GIS, str, a, b) for a, b in deepcopy(_GIS)),
                             (VariableName, str)+deepcopy(_varn),
                             *((CASNumber, str, a, b) for a, b in deepcopy(_cas)),
                             *((c, str, a, b) for a, b in deepcopy(_dt_ilcd1) for c in (DateTime, ReviewDateTime)),
                             *((ECS2Date, str, a, b) for a, b in deepcopy(_dt_ecs2)),
                             *((CompleteDate, str, a, b) for a, b in deepcopy(_cdt_ecs2)),
                             *((return_enum(Languages), str, a, b) for a, b in deepcopy(_enum_n)),
                             *((return_enum(Languages, list_=True), list, a, b) for a, b in deepcopy(_enum_l)),
                             *((Str, str, a, b) for a, b in deepcopy(_str)),
                             *((IndexedString, list, a, b) for a, b in deepcopy(_indexstr)),
                             *((MultiLangString, list, a, b) for a, b in deepcopy(_multlstr)),
                             *((MultiLang, list, a, b) for a, b in deepcopy(_multlstr)),
                             *((NoLangRestrictionMultiLangString, list, a, b) for a, b in deepcopy(_nolanstr)),
                             *((IndexedMultiLangString, list, a, b) for a, b in deepcopy(_imlanstr)),
                             *((NamedString, list, a, b) for a, b in deepcopy(_namedstr)),
                         ])
def test_single_input_validation(class_, type_, input_, validation_result):
    r = class_()
    a = r.add(input_).end()
    assert isinstance(a, type_)
    assert a == validation_result


########## Multi Input

# Real
_mreal = ([1.0,0,2.0],[1.0,0.0,2.0])

# ECS2 Percent
_mecs2perc = ([10.0,1.2345,23.67],['10.0','1.2','23.7'])

# Bool
_mbool = (['true',True,0],[True,True,False])
_mecs2bool = (['true',True,0],['true','true','false'])

# Int
_mint = ([2,3,4],[2,3,4])

# return_limited_int
_lmint = ((1,n,_add,[2,3,4],[2,3,4]),
          (4,n,list_add,[2002,2004,2005],[2002,[2002,2004],[2002,2004,2005]]),
          (6,lambda x,lim: x>lim,list_add,[0,1,2],[0,[0,1],[0,1,2]]))

# return_collection
_lmcol = (({4},False,[4,4],[4,4]), (set(range(1,4)),False,[2,1,3],[2,1,3]),
          ({1,2,3,5},False,[3,5,1],[3,5,1]), (set(range(-1,4)),True,[-1,2,3],[-1,2,3]))

# return_limited_string
_lmstr = ((30,separator_add,['lol','lol1','lol2'],['lol','lol; lol1','lol; lol1; lol2']),
          (30,_add,['lol','lol1','lol2'],['lol','lol1','lol2']))

# return_pattern
# UUID
_muuid = (['4dfe5a1f-cd1a-4fb3-87bf-55bfc40e0818', 'e7c8581b-39f5-4cb0-afa6-984822906bb7', 'c1d59f0f-1115-4fc0-8301-fca6e927679a'],
          ['4dfe5a1f-cd1a-4fb3-87bf-55bfc40e0818', 'e7c8581b-39f5-4cb0-afa6-984822906bb7', 'c1d59f0f-1115-4fc0-8301-fca6e927679a'])

# Version
_mversion = (['00.00.000','01.01.001','01.01.002'],
             ['00.00.000','01.01.001','01.01.002'])

# GIS
_mGIS = (["+42.42;-180","0;0","13.22 ; -3"],
         ["+42.42;-180","0;0","13.22 ; -3"])

# VariableName
_mvarn = (['some_name','some_other_name','lol'],
          ['some_name','some_other_name','lol'])

# CASNumber: case
_mcas = (['7732-18-5','18540-29-9','8007-40-7'],
         ['7732-18-5','18540-29-9','8007-40-7'])

# Date, DateTime, CompleteDate and ReviewDateTime
_mdt_def = (_def_dt, [dtf_def(x) for x in _def_dt])
_mdt_ecs2 = (_def_dt, [dtf_ecs2(x) for x in _def_dt])
_mcdt_ecs2 = (_def_dt, [cdtf_ecs2(x) for x in _def_dt])
_mrev1dt = (_def_dt[::-1], [dtf_def('2019-08-19T13:47:31Z'.replace('Z','+00:00'))]*4) # for the other way around of the review date (no substitution)

dtf_general = lambda x: datetime.fromisoformat(x)
_mdt_general = (_def_dt, [dtf_general(x) for x in _def_dt])

# return_enum
_menum_n = (['en','pt','pt'],['en','pt','pt'])
_menum_l = (['en','pt','pt'],[['en'],['en','pt'],['en','pt']]) # Covers duplicated entries

# Str
_mstr = (['a','b',''],['a','b',''])

# Multi strings

# IndexString: just @index and #text
    # Must have unique indexes by merging with '; ' separator in _add function
    # [in_gen(index, text)] [sort with index]
_index_str_example          = [[[{'@index':1, '#text':'lol'},
                                {'@index':1, '#text':'lol1'},
                                {'@index':2, '#text':'lol2'}]],
                               [[{'@index':1, '#text':'lol; lol1'},
                                {'@index':2, '#text':'lol2'}]]]
# MultiLangString [and MultiLang for ILCD1]: IndexString with @lang, deletes the @index after
    # Must have unique indexes and languages by merging with '; ' separator in _add function
    # Must have no indexes by merging the indexes under the same language with the '\n' separator
    # [mt_gen(lang, index, text)] [sort with index first and lang after]
_multlang_str_example      = [[[{'@index':1, '@lang':'en', '#text':'lol'}, 
                                {'@index':1, '@lang':'pt', '#text':'lol1'},
                                {'@index':2, '@lang':'en', '#text':'lol2'},
                                {'@index':1, '@lang':'pt', '#text':'lol3'}]],
                               [[{'@xml:lang':'en', '#text':'lol\nlol2'},
                                {'@xml:lang':'pt', '#text':'lol1; lol3'}]]]
# NoLangRestrictionMultiLangString: Multilang but the @lang is not used in joins
    # No _add function, so no '; ' separator
    # No need to merge languages, so no '\n' separator
    # Index is used for sorting and just 'popped'
    # [mt_gen(lang, index, text)] [sort with index first and lang after]
_nolang_str_example        = [[[{'@index':1, '@lang':'en', '#text':'lol'}, 
                                {'@index':1, '@lang':'pt', '#text':'lol1'},
                                {'@index':2, '@lang':'en', '#text':'lol2'},
                                {'@index':1, '@lang':'pt', '#text':'lol3'}]],
                               [[{'@xml:lang':'en', '#text':'lol'}, 
                                {'@xml:lang':'pt', '#text':'lol1'},
                                {'@xml:lang':'pt', '#text':'lol3'},
                                {'@xml:lang':'en', '#text':'lol2'}]]]
# IndexedMultiLangString: Multilang but with indexes
    # Same (index, lang) are merged at _add with the '; ' separator
    # As the indexes are maintained, there is no need to merge by unique language using '\n'
    # [mt_gen(lang, index, text)] [no joins] [sort with index first and lang after]
_indexmultilang_str_example = [[[{'@index':1, '@lang':'en', '#text':'lol'}, 
                                {'@index':1, '@lang':'pt', '#text':'lol1'},
                                {'@index':2, '@lang':'en', '#text':'lol2'},
                                {'@index':1, '@lang':'pt', '#text':'lol3'}]],
                               [[{'@index':1, '@xml:lang':'en', '#text':'lol'}, 
                                {'@index':1, '@xml:lang':'pt', '#text':'lol1; lol3'},
                                {'@index':2, '@xml:lang':'en', '#text':'lol2'}]]]
# Named String [ECS2]: Just IndexedString but use @name instead of @index
# Name [ECS2]: Just MultiLangString but the separator is ', ' instead of '; '

# All combinations of results for IndexedString
def _mi(inputs, func=in_gen):
    output=defaultdict(list)
    
    def add(j):
        if j[0] == 0 and j[-1] == 0: return # (0,0) is passed as it is ''
        output[j[0]] += [j[-1]]
    
    _out = []
    for i in inputs:
        if isinstance(i[0], tuple):
            for j in i: add(j)
        else: add(i)
     
        x = []
        for n in sorted(output.items()):
            x.append(func(*n))
        _out.append(x)
    
    return _out

# All combinations of results for MultiLangString
def _mm(inputs, func=mt_gen, sep='; '):
    output=defaultdict(list)
    
    def add(j):
        if j[0] == 0 and j[-1] == 0: return # (0,0) is passed as it is ''
        output[j[0],j[1]] += [j[-1]] # lang, index
    
    y = []
    for i in inputs:
        if isinstance(i[0], tuple):
            for j in i: add(j)
        else: add(i)
        
        _out = defaultdict(list)
        for n in sorted(output.items()):
            n = n[0]+(n[1],)
            x = func(*n, sep=sep)
            _out[x['@lang']].append(x)
        
        b = []
        for k,v in sorted(_out.items()):
            b.append({'@xml:lang':k, '#text': '\n'.join([n['#text'] for n in v])})
        y.append(b)
    
    return y

# All combinations of results for NoLangRestrictionMultiLangString
def _mn(inputs, func=lg_gen): # lg beacuse it doesn't have index
    
    def add(j):
        if j[0] == 0 and j[-1] == 0: return # (0,0) is passed as it is ''
        return [j[1], func(j[0], j[2])]
    
    _out = []
    x = []
    for i in inputs:
        if isinstance(i[0], tuple):
            for j in i: _out.append(add(j))
        else: _out.append(add(i))
        _out2 = [y for x,y in sorted(_out, key=lambda x:x[0])]
        x.append(deepcopy(_out2))
    
    return x

# All combinations of results for IndexedMultiLangString
def _mil(inputs, func=lgi_gen):
    output=defaultdict(list)
    
    def add(j):
        if j[0] == 0 and j[-1] == 0: return # (0,0) is passed as it is ''
        output[j[0],j[1]] += [j[-1]] # lang, index
        
    _out = []
    for i in inputs:
        if isinstance(i[0], tuple):
            for j in i: add(j)
        else: add(i)
        
        m = []
        for k,v in sorted(output.items(), key=lambda x:int(str(x[0][1])+str(x[0][0]))):
            n = (k[0], k[1], v)
            m.append(func(*n))
        _out.append(m)
    
    return _out

d2, d3 = [list(combinations([0,1,2,3,4], x)) for x in (2,3)]
l2, l3 = [list(combinations(d, x)) for d,x in ((d2,2),(d3,3))]
a2, a3 = [list(product(d, l)) for d,l in ((d2,l2),(d3,l3))]

def get_gen(a, func):
    n = []
    for x in a:
        o = []
        for y in x:
            if isinstance(y[0], tuple):
                m = []
                for z in y:
                    m.append(func(*z))
                o.append(m)
            else:
                o.append(func(*y))
        n.append(o)
    return n

_index_m = _base + tuple(zip(get_gen(a2, in_gen), [_mi(x) for x in a2]))
_multl_m = _base + tuple(zip(get_gen(a3, mt_gen), [_mm(x) for x in a3]))
_nolan_m = _base + tuple(zip(get_gen(a3, mt_gen), [_mn(x) for x in a3]))
_imlan_m = _base + tuple(zip(get_gen(a3, mt_gen), [_mil(x) for x in a3]))

# Named String
_mns = [[nm_gen(1,1), nm_gen(2,2), nm_gen(3,3)], [[nm_gen(1,1)],[nm_gen(1,1),nm_gen(2,2)],[nm_gen(1,1),nm_gen(2,2),nm_gen(3,3)]]]

# ClassificationValueString120 and ExchangeNameString80 and Name
_mfirstcv = [[[{'@index':3, '@lang':'en', '#text':'lol'}, 
             {'@index':4, '@lang':'pt', '#text':'lol1'},
             {'@index':2, '@lang':'en', '#text':'lol2'},
             {'@index':1, '@lang':'pt', '#text':'lol3'}]],
            [{'@xml:lang':'pt', '#text':'lol1'}]] # It is expected that no index is duplicated
_mfirsten = [[[{'@index':3, '@lang':'en', '#text':'lol'}, 
             {'@index':4, '@lang':'pt', '#text':'lol1'},
             {'@index':2, '@lang':'en', '#text':'lol2'},
             {'@index':1, '@lang':'pt', '#text':'lol3'}]],
            [{'@xml:lang':'pt', '#text':'lol3'}]] # It is expected that no index is duplicated

@pytest.mark.validator
@pytest.mark.multiple_input
@pytest.mark.parametrize('class_, inputs_',
                         [
                             (IndexedString, zip(*deepcopy(_index_str_example))),
                             (MultiLangString, zip(*deepcopy(_multlang_str_example))),
                             (MultiLang, zip(*deepcopy(_multlang_str_example))),
                             (NoLangRestrictionMultiLangString, zip(*deepcopy(_nolang_str_example))),
                             (IndexedMultiLangString, zip(*deepcopy(_indexmultilang_str_example))),
                             (Real, zip(*deepcopy(_mreal))),
                             (Percent, zip(*deepcopy(_mecs2perc))),
                             (Bool, zip(*deepcopy(_mbool))),
                             (ECS2Bool, zip(*deepcopy(_mecs2bool))),
                             (Int, zip(*deepcopy(_mint))),
                             *((return_limited_int(a, func=b, add_func=c), zip(d, e)) for a, b, c, d, e in deepcopy(_lmint)),
                             *((return_collection(a, b), zip(c, d)) for a, b, c, d in deepcopy(_lmcol)),
                             *((return_limited_string(a, add_func=b), zip(c, d)) for a, b, c, d in deepcopy(_lmstr)),
                             (UUID, zip(*deepcopy(_muuid))),
                             (Version, zip(*deepcopy(_mversion))),
                             (GIS, zip(*deepcopy(_mGIS))),
                             (VariableName, zip(*deepcopy(_mvarn))),
                             (CASNumber, zip(*deepcopy(_mcas))),
                             *((c, zip(*deepcopy(_mdt_def))) for c in (DateTime, ReviewDateTime)),
                             (ECS2Date, zip(*deepcopy(_mdt_ecs2))),
                             (Date, zip(*deepcopy(_mdt_general))),
                             (CompleteDate, zip(*deepcopy(_mcdt_ecs2))),
                             (ReviewDateTime, zip(*deepcopy(_mrev1dt))),
                             (return_enum(Languages), zip(*deepcopy(_menum_n))),
                             (return_enum(Languages, list_=True), zip(*deepcopy(_menum_l))),
                             (Str, zip(*deepcopy(_mstr))),
                             *((IndexedString, zip(a,b)) for a,b in deepcopy(_index_m)),
                             *((MultiLangString, zip(a,b)) for a,b in deepcopy(_multl_m)),
                             *((MultiLang, zip(a,b)) for a,b in deepcopy(_multl_m)),
                             *((NoLangRestrictionMultiLangString, zip(a,b)) for a,b in deepcopy(_nolan_m)),
                             *((IndexedMultiLangString, zip(a,b)) for a,b in deepcopy(_imlan_m)),
                             (NamedString, zip(*deepcopy(_mns))),
                             (ClassificationValueString120, zip(*deepcopy(_mfirstcv))),
                             (ExchangeNameString80, zip(*deepcopy(_mfirsten))),
                             (Name, zip(*deepcopy(_mfirsten))),
                             # Only in MultiLangStrings the correction per limit is done, for other, passing the limit would raise errors
                             (FTMultiLang, ((a, b) for a, b in (([{'@index': 1, '@lang': 'en', '#text': 'lol1 '*50},
                                                                 {'@index': 1, '@lang': 'en', '#text': 'lol2 '*50}],
                                                                [{'@xml:lang': 'en', '#text': 'lol1 '*50+'; '+'lol2 '*50}]),
                                                                ([{'@index': 1, '@lang': 'en', '#text': 'lol3 '*50},
                                                                 {'@index': 1, '@lang': 'en', '#text': 'lol4 '*50}],
                                                                [{'@xml:lang': 'en', '#text': 'lol1 '*50+'; '+'lol2 '*50+'; '+'lol3 '*50+'; '+'lol4 '*50}]),
                                                                ({'@index': 1, '@lang': 'en', '#text': 'loln '*500},
                                                                [{'@xml:lang': 'en', '#text': 'lol1 '*50+'; '+'lol2 '*50+'; '+'lol3 '*50+'; '+'lol4 '*50+'; '+'loln '*500}])
                                                                ))),
                             (StringMultiLang, ((a, b) for a, b in (([{'@index': 1, '@lang': 'en', '#text': 'lol1 '*50},
                                                                      {'@index': 1, '@lang': 'en', '#text': 'lol2 '*50}],
                                                                     [{'@xml:lang': 'en', '#text': 'lol1 '*50+';'},
                                                                      {'@xml:lang': 'en', '#text': 'lol2 '*49+'lol2'}]),
                                                                    ([{'@index': 1, '@lang': 'en', '#text': 'lol3 '*50},
                                                                      {'@index': 1, '@lang': 'en', '#text': 'lol4 '*50}],
                                                                     [{'@xml:lang': 'en', '#text': 'lol1 '*50+';'},
                                                                        {'@xml:lang': 'en',
                                                                         '#text': 'lol2 '*50+';'},
                                                                        {'@xml:lang': 'en',
                                                                         '#text': 'lol3 '*50+';'},
                                                                        {'@xml:lang': 'en', '#text': 'lol4 '*49+'lol4'}]),
                                                                    ({'@index': 1, '@lang': 'en', '#text': 'loln '*500},
                                                                     [{'@xml:lang': 'en', '#text': 'lol1 '*50+';'},
                                                                        {'@xml:lang': 'en',
                                                                         '#text': 'lol2 '*50+';'},
                                                                        {'@xml:lang': 'en',
                                                                         '#text': 'lol3 '*50+';'},
                                                                        {'@xml:lang': 'en',
                                                                         '#text': 'lol4 '*50+';'},
                                                                        *({'@xml:lang': 'en', '#text': 'loln '*89+'loln'},)*5,
                                                                        {'@xml:lang': 'en', '#text': 'loln '*48+'loln'}])
                                                                    ))),
                             (STMultiLang, ((a, b) for a, b in (([{'@index': 1, '@lang': 'en', '#text': 'lol1 '*50},
                                                                 {'@index': 1, '@lang': 'en', '#text': 'lol2 '*50}],
                                                                [{'@xml:lang': 'en', '#text': 'lol1 '*50+'; '+'lol2 '*50}]),
                                                                ([{'@index': 1, '@lang': 'en', '#text': 'lol3 '*50},
                                                                 {'@index': 1, '@lang': 'en', '#text': 'lol4 '*50}],
                                                                [{'@xml:lang': 'en', '#text': 'lol1 '*50+'; '+'lol2 '*50+'; '+'lol3 '*50+';'},
                                                                 {'@xml:lang': 'en', '#text': 'lol4 '*49+'lol4'}]),
                                                                ({'@index': 1, '@lang': 'en', '#text': 'loln '*500},
                                                                [{'@xml:lang': 'en', '#text': 'lol1 '*50+'; '+'lol2 '*50+'; '+'lol3 '*50+';'},
                                                                 {'@xml:lang': 'en',
                                                                     '#text': 'lol4 '*50+';'},
                                                                 *({'@xml:lang': 'en',
                                                                     '#text': 'loln '*189+'loln'},)*2,
                                                                 {'@xml:lang': 'en', '#text': 'loln '*118+'loln'}])
                                                                )))
                         ])
def test_multiple_input_validation(class_, inputs_):
    r = class_()
    # Take care as the inputs_ are really a generator and can be used once
    for input_, validation_result in inputs_:
        r = r.add(input_)
        assert r.end() == validation_result

########## Single Error

numeric_verification    = nv = ('', None, [1], {1: 2})
string_verification     = sv = (1, 1.0, None, [''], {'a': ''})
mtlang_verification     = mt = ('', 'plain_text', None, 1, 1.0)
enum_verification       = en = (1, 1.0, None, {'a': ''})

# Real
_etreal = nv
# ECS2 Percent [Value]
_evecs2perc = (101.0, -1.0)
# Bool and ECS2Bool
_evbool = nv
# Int
_evint = (-2,) # can_be_negative tested under collections
_etint = nv

# return_collection
_evrcol = (({4}, False, (-4,5)),
          (set(range(1,4)), False, (-1,4,0)),
          ({1,2,3,5}, False, (-1,4,0)),
          (set(range(-1,4)), True, (-2,4)))

# return_limited_int
_evrlint = ((1, n, _add, (-1,12)),
            (4, n, _add, (-1111,12,12345)),
            (6, lambda x,lim: x>lim, _add, (-111111,1234567)))

# return_pattern
_etpat = sv
# UUID
_evuuid = ('4dfe5a1f-cd1a-4fb3-87bf-55bfc40e081', 'lol') # fist one lacks a number
# Version
_evversion = ('1.00.000','01.1.001','01.0') # 01.01.02 is valid since the last 3 are not mandatory
# GIS
_evGIS = ('lol;lol','lol')
# VariableName
_evvarn = ('a'*41,) # len = 40
# CASNumber
_evcas = ('18540-2-9','8007-40-','lol')

# Date, DateTime, CompleteDate and ReviewDateTime
_etdate = sv
_evdate = ('lol','2000','99999','2009-13-01','1002-02-59','1002-02-01T25:40:20','1002-02-01T22:70:20','1002-02-01T22:40:70')

# Str
_etstr = sv

# return_limited_string
_evstr = ((3, _add, ('a'*4,)),
          ((1,5), _add, ('','a'*6)))

# return_enum
_etenum_n = en
_evenum_n = ('lol',)
_evenum_l = (['lol', 'en'],)

# Multi Strings
_etbasic_str = mt # For all cases

# IndexString
_ek1index_str = ({'@lang':'en', '#text':'lol'}, {'#text':'lol'}) # No index
_evindex_str = [{'@index':x, '#text':'lol'} for x in nv] # index is not an int
_ek2index_str = ({'@index':1, '@lang':'en', '#text':'lol'},) # other keys than the ones possible

# MultiLangString, MultiLang, NoLang and IndexedMultiLang, Name
_ek1multl_str = ({'@lang':'en', '#text':'lol'}, {'#text':'lol'}) # No index or lang
_evmultl_str = [{'@index':1, '@lang':x, '#text':'lol'} for x in sv+('lol',)] # len(str) > 2 is not possible
_ek2multl_str = ({'@name': 'lol', '@index':1, '@lang':'en', '#text':'lol'},) # other keys than the ones possible

# NamedString
_ek1named_str = ({'@lang':'en', '#text':'lol'}, {'#text':'lol'}) # No name
_evnamed_str = [[{'@name':'lol', '#text':'lol'}, {'@name':'lol', '#text':'lol'}]] # name can't be equal
_ek2named_str = ({'@index':1, '@lang':'en', '#text':'lol'},) # other keys than the ones possible

@pytest.mark.validator
@pytest.mark.single_input
@pytest.mark.parametrize('class_, error, input_',
                         [
                             (Real, TypeError, deepcopy(_etreal)),
                             (Percent, ValueError, deepcopy(_evecs2perc)),
                             *((c, ValueError, deepcopy(_evbool)) for c in (Bool, ECS2Bool)),
                             (Int, ValueError, deepcopy(_evint)),
                             (Int, TypeError, deepcopy(_etint)),
                             *((return_collection(a, b), ValueError, c) for a, b, c in deepcopy(_evrcol)),
                             *((return_limited_int(a, func=b, add_func=c), ValueError, d) for a, b, c, d in deepcopy(_evrlint)),
                             *((c, TypeError, deepcopy(_etpat)) for c in (UUID, Version, GIS, CASNumber, VariableName)),
                             (UUID, ValueError, deepcopy(_evuuid)),
                             (Version, ValueError, deepcopy(_evversion)),
                             (GIS, ValueError, deepcopy(_evGIS)),
                             (CASNumber, ValueError, deepcopy(_evcas)),
                             (VariableName, ValueError, deepcopy(_evvarn)),
                             *((c, TypeError, deepcopy(_etdate)) for c in (Date, ECS2Date, DateTime, CompleteDate)),
                             *((c, ValueError, deepcopy(_evdate)) for c in (Date, ECS2Date, DateTime, CompleteDate)),
                             (Str, TypeError, deepcopy(_etstr)),
                             *((return_limited_string(a, add_func=b), ValueError, c) for a, b, c in deepcopy(_evstr)),
                             (return_enum(Languages), TypeError, deepcopy(_etenum_n)),
                             (return_enum(Languages), ValueError, deepcopy(_evenum_n)),
                             (return_enum(Languages, list_=True), ValueError, deepcopy(_evenum_l)),
                             *((c, TypeError, deepcopy(_etbasic_str)) for c in (IndexedString,
                                                                                MultiLang,
                                                                                MultiLangString,
                                                                                NoLangRestrictionMultiLangString,
                                                                                IndexedMultiLangString,
                                                                                NamedString)),
                             (IndexedString, KeyError, deepcopy(_ek1index_str)),
                             (IndexedString, KeyError, deepcopy(_ek2index_str)),
                             (NamedString, KeyError, deepcopy(_ek1named_str)),
                             (NamedString, KeyError, deepcopy(_ek2named_str)),
                             (IndexedString, ValueError, deepcopy(_evindex_str)),
                             (NamedString, ValueError, deepcopy(_evnamed_str)),
                             *((c, KeyError, deepcopy(_ek1multl_str)) for c in (MultiLang,
                                                                               MultiLangString,
                                                                               NoLangRestrictionMultiLangString,
                                                                               IndexedMultiLangString)),
                             *((c, KeyError, deepcopy(_ek2multl_str)) for c in (MultiLang,
                                                                               MultiLangString,
                                                                               NoLangRestrictionMultiLangString,
                                                                               IndexedMultiLangString)),
                             *((c, ValueError, deepcopy(_evmultl_str)) for c in (MultiLang,
                                                                                 MultiLangString,
                                                                                 NoLangRestrictionMultiLangString,
                                                                                 IndexedMultiLangString))
                         ])
def test_single_input_validator_error(class_, error, input_):
    r = class_()
    for i in input_:
        with pytest.raises(error):
            r.add(i).end()

########## Multiple Inputs Errors

_evmstr = ((3, ('a', 'a'*3)),
          ((1,5), ('a', 'a'*7)))

@pytest.mark.validator
@pytest.mark.multiple_input
@pytest.mark.parametrize('class_, inputs_',
                         [
                             *((return_limited_string(a), b) for a, b in deepcopy(_evmstr)) # add_func is separator_add
                         ])
def test_multiple_input_validator_value_error(class_, inputs_):
    r = class_()
    for i, input_ in enumerate(inputs_):
        if i != len(inputs_)-1: # Only the last generates the error
            r = r.add(input_)
        else:
            with pytest.raises(ValueError):
                r.add(input_).end()

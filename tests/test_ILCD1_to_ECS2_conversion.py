#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 13:39:38 2022

@author: jotape42p
"""

import pytest
import math
from copy import deepcopy

from src.Lavoisier.conversions.ILCD1_to_ECS2_conversion import (
    ILCD1ToECS2UncertaintyConversion,
    ILCD1ToECS2VariableConversion,
    ILCD1ToECS2Amount,
    ILCD1ToECS2ReferenceConversion,
    ILCD1ToECS2ClassificationConversion,
    ILCD1ToECS2FlowConversion,
    ILCD1ToECS2BasicFieldMapping,
    ILCD1ToECS2ContactReferenceConversion,
    ILCD1ToECS2SourceReferenceConversion,
    ILCD1ToECS2FlowReferenceConversion,
    ILCD1ToECS2ReviewConversion,
    up
    )
from src.Lavoisier.conversions.utils import (
    uuid_from_string
)
from src.Lavoisier.data_structures.ECS2_structure import (
    ECS2Uncertainty,
    ECS2CustomExchange,
    ECS2Structure,
    ILCD1ToECS2DataNotConverted
    )
from src.Lavoisier.formats import (
    ILCD1Helper
)

# Cases possible inside ILCD
# Possible calls/instantiations inside the code
# Linear creation as bigger dicts are gathered from smaller dicts

# normal_init -> get_data -> WAIT CALL TO calculate -> Return
# comment_init -> Return
# for the time, do the 'comment' picking of arguments, but try to take it out after using not_converted

# Enters with the whole flow dict as it has the information

# When leading with interactions between classes, one must think about the testing and if an interaction would 
# need to retest everything from the previous classes (Amount has to test Uncertainty again due to its interaction)

### Uncertainty

meanAmount                  = ma = [-2.0, 0.0, 2.0, 1.0] # 1.0 for variables, negative accounts for lognormal negative entries too (that can happen)
resultingAmount             = ra = [-2.0, 0.0, 2.0, 20.0]
relativeStd                 = rstd = [0.75, 1.10, 1.67] # should not be negative or zero (0.75 for lognormal will result on positive even with negative log)
f                           = [1, 2]

# Undefined type actually means that information is not available

# pedigree (3,3,1,1,1), this does NOT calculate the uncertainty USING pedigree indexes, it only assumes that relativeStd is the variance with pedigree
ped = {
    '@reliability': 3,
    '@completeness': 3, 
    '@temporalCorrelation': 1,
    '@geographicalCorrelation': 1, 
    '@furtherTechnologyCorrelation': 1
    }

# comments
c1 = 'lol'
c2 = 'lol, Uncertainty Comment:\n'
c3 = 'lol, Uncertainty Comment:\nPedigree: (3,3,1,1,1)'
c4 = 'Uncertainty Comment:\nBasic Variance: 0.0006'
c5 = 'Uncertainty Comment:\nPedigree: (3,3,1,1,1)\nBasic Variance: 0.0006'
cn = [c1, c2, c3, c4, c5]
rescn = [
    {},
    {},
    {'pedigreeMatrix': ped},
    {'@variance': 0.0006},
    {'pedigreeMatrix': ped, '@variance': 0.0006}
    ]
rescn2 = [ # No variance for triangular or uniform
    {},
    {},
    {'pedigreeMatrix': ped},
    {},
    {'pedigreeMatrix': ped}
    ]

# comments used only for retrieving [not to be placed in generalComment]
cc1 = '\nNot Converted: [A-z]+ distribution with parameters ' # None
cc2 = "\nNot Converted: Beta distribution with parameters minValue=-1.0, mostLikelyValue=0.0, maxValue=1.0"
cc3 = "\nNot Converted: Gamma distribution with parameters shape=1.0, scale=0.0, minValue=-1.0"
cc4 = "\nNot Converted: Binomial distribution with parameters n=1, p=10.0"
cc5 = "lol, \nNot Converted: Undefined distribution with parameters minValue=-1.0, standardDeviation95=1.0, maxValue=0.0"
ccn = [cc1, cc2, cc3, cc4, cc5]
resccn = [None,
          {'@minValue': -1.0, '@mostLikelyValue': 0.0, '@maxValue': 1.0},
          {'@shape': 1.0, '@scale': 0.0, '@minValue': -1.0},
          {'@n': 1, '@p': 10.0},
          {'@minValue': -1.0, '@standardDeviation95': 1.0, '@maxValue': 0.0}]

# pré
pre1 = [{
    'meanAmount': a, # [SPEC]: lognormal with negative values
    'resultingAmount': b,
    'relativeStandardDeviation95In': c,
    'generalComment': {'@lang': 'en', '#text': d}
    } for a, b, c, d in zip(ma, ra, rstd, cn)]

pre2 = [{
    'meanValue': a,
    'resultingAmount': b,
    'generalComment': {'@lang': 'en', '#text': c}
    } for a, b, c in zip(ma, ra, cn)]

# normal init
normal = [x | {
    'minimumAmount': x['meanAmount']-2*x['relativeStandardDeviation95In'],
    'maximumAmount': x['meanAmount']+2*x['relativeStandardDeviation95In'],
    'uncertaintyDistributionType': 'normal'
    } for x in pre1]

resnorm1 = [{ # f = 1
    '@meanValue': a,
    '@variance': b, # The update will change the value if the comment has the variance
    '@varianceWithPedigreeUncertainty': b
    } | c for a, b, c in zip(ra * f[0], [(x * f[0] / 2) ** 2 for x in rstd], rescn)]

resnorm2 = [{ # f = 2
    '@meanValue': a,
    '@variance': b, # The update will change the value if the comment has the variance
    '@varianceWithPedigreeUncertainty': b
    } | c for a, b, c in zip(ra * f[1], [(x * f[1] / 2) ** 2 for x in rstd], rescn)]

lognormal = [x | {
    'minimumAmount': x['meanAmount']*x['relativeStandardDeviation95In']**2,
    'maximumAmount': x['meanAmount']/x['relativeStandardDeviation95In']**2,
    'uncertaintyDistributionType': 'log-normal'
    } for x in pre1]

reslogn1 = [{ # f doesn't change a lognormal
    '@mu': math.log(a) if a > 0 else 0.0,
    '@meanValue': a,
    '@variance': b, # The update will change the value if the comment has the variance
    '@varianceWithPedigreeUncertainty': b
    } | c for a, b, c in zip(ra * f[0], [math.log(math.sqrt(x))**2 for x in rstd], deepcopy(rescn))]

reslogn2 = [{ # f doesn't change a lognormal
    '@mu': math.log(a) if a > 0 else 0.0,
    '@meanValue': a,
    '@variance': b, # The update will change the value if the comment has the variance
    '@varianceWithPedigreeUncertainty': b
    } | c for a, b, c in zip(ra * f[1], [math.log(math.sqrt(x))**2 for x in rstd], deepcopy(rescn))]

triangular = [x | {
    'minimumAmount': x['resultingAmount']-2.0,
    'maximumAmount': x['resultingAmount']+2.0,
    'uncertaintyDistributionType': 'triangular'
    } for x in pre2]

restria1 = [{
    '@minValue': a,
    '@mostLikelyValue': b,
    '@maxValue': c,
    } | d for a, b, c, d in zip([(x-2.0) * f[0] for x in ra], ra, [(x+2.0) * f[0] for x in ra], rescn2)]

restria2 = [{
    '@minValue': a,
    '@mostLikelyValue': b,
    '@maxValue': c,
    } | d for a, b, c, d in zip([(x-2.0) * f[1] for x in ra], ra, [(x+2.0) * f[1] for x in ra], rescn2)]

uniform = [x | {
    'minimumAmount': x['resultingAmount']-2.0,
    'maximumAmount': x['resultingAmount']+2.0,
    'uncertaintyDistributionType': 'uniform'
    } for x in pre2]

resunif1 = [{
    '@minValue': a,
    '@maxValue': b,
    } | c for a, b, c in zip([(x-2.0) * f[0] for x in ra], [(x+2.0) * f[0] for x in ra], rescn2)]

resunif2 = [{
    '@minValue': a,
    '@maxValue': b,
    } | c for a, b, c in zip([(x-2.0) * f[1] for x in ra], [(x+2.0) * f[1] for x in ra], rescn2)]

# comment_init
undefined = {
    'meanAmount': 1.0,
    'resultingAmount': 1.0,
    'uncertaintyDistributionType': 'undefined',
    'generalComment': {'@lang': 'en', '#text': cc5}
    }

comment_ones = [{'generalComment': {'@lang': 'en', '#text': cc1}}] + [{
    'meanAmount': 1.0, # Doesn't need actualy
    'resultingAmount': 1.0, # Doesn't need actualy
    'generalComment': {'@lang': 'en', '#text': a}
    } for a in [cc2, cc3, cc4]] + [undefined]

# errors
kstd = {
    'uncertaintyDistributionType': 'log-normal'
    } # no standard deviation

kmin = {
    'uncertaintyDistributionType': 'triangular'        
    } # no minimum

kmax = {
    'uncertaintyDistributionType': 'uniform',
    'minimumValue': 1.0
    } # no maximum

@pytest.mark.uncertainty
@pytest.mark.parametrize('input_, mean, factor, dist, output', 
                         [
                         *((a, a['resultingAmount'], d, 'normal', b) for c, d in zip([resnorm1, resnorm2], f) for a, b in zip(normal, c)),
                         *((a, a['resultingAmount'], d, 'lognormal', b) for c, d in zip([deepcopy(reslogn1), deepcopy(reslogn2)], f) for a, b in zip(lognormal, c)),
                         *((a, a['resultingAmount'], d, 'triangular', b) for c, d in zip([restria1, restria2], f) for a, b in zip(triangular, c)),
                         *((a, a['resultingAmount'], d, 'uniform', b) for c, d in zip([resunif1, resunif2], f) for a, b in zip(uniform, c))
                         ]
                         )
def test_uncertainty_normal(input_, mean, factor, dist, output):
    
    r = ILCD1ToECS2UncertaintyConversion.normal_init(input_)
    field = ECS2Uncertainty()
    r.calculate(mean, factor, field)

    com = {**({'comment': [output.pop('comment')]} if output.get('comment') else {})}
    ped = {**({'pedigreeMatrix': [output.pop('pedigreeMatrix')]} if output.get('pedigreeMatrix') else {})}
    
    assert field.get_dict() == {dist: [output]} | com | ped
    
@pytest.mark.uncertainty
@pytest.mark.parametrize('input_, dist, output',
                         [
                         *((a, b, c) for a, b, c in zip(comment_ones, [None, 'beta', 'gamma', 'binomial', 'undefined'], resccn))
                         ]
                         )
def test_uncertainty_comment(input_, dist, output):
    
    r = ILCD1ToECS2UncertaintyConversion.init_from_comment(input_)
    
    if dist is None:
        assert r == None
    else:
        field = ECS2Uncertainty()
        r.calculate(None, None, field)
        
        com = {**({'comment': [output.pop('comment')]} if output.get('comment') else {})}
        
        assert field.get_dict() == {dist: [output]} | com

@pytest.mark.uncertainty
@pytest.mark.parametrize('input_, error', [
    (kstd, KeyError),
    (kmin, KeyError),
    (kmax, KeyError),
    ])
def test_uncertainty_error(input_, error):
    
    with pytest.raises(error):
        _ = ILCD1ToECS2UncertaintyConversion.normal_init(input_)

### Amount

# Cases of amount and unit texts [only the referenced in ILCD files] available in ILCD
amount = [1, 2, 3, 4, 5, 6]
units  = ['mol', 'kg', 'm3*a', 'm2*a', 'm2', 'kBq', 'm3', 'MJ', 'kg*a', 'Item(s)', 'EUR', 'EUR2005', 'dimensionless']
dims   = dict(zip(units, [{'[substance]': 1},
                          {'[mass]': 1},
                          {'[length]': 3, '[time]': 1},
                          {'[length]': 2, '[time]': 1},
                          {'[length]': 2},
                          {'[time]': -1}, # kilobecquerel
                          {'[length]': 3},
                          {'[length]': 2, '[mass]': 1, '[time]': -2},
                          {'[mass]': 1, '[time]': 1},
                          {'[item]': 1},
                          {'[currency]': 1},
                          {'[currency]': 1},
                          {}])) # ILCD does not consider dimensionality to get units

# Case with uncertainty lognormal, with dist = beta and dist = undefined and with unc = None
beta = comment_ones[1]
none = {
    'meanValue': 1,
    'resultingAmount': 1
    }

# Uncertainty calculate_unc test with unc cases
# simple property verification

# multiplication and division with all cases
mult_div = [up.Quantity(2, 'dimensionless'), up.Quantity(-2, 'kg')]

input_ = [x | {'resultingAmount': a} for a in amount for x in (lognormal[0], beta, undefined, none)]

ILCD1ToECS2Amount.uncertainty_conversion = ILCD1ToECS2UncertaintyConversion
    
@pytest.mark.amount
@pytest.mark.parametrize('input_, unit, calculate_unc_output', 
                         [
                             *((a, b, c) for a, c in zip(input_, [True, True, True, False]) for b in units)
                        ]
                         )
def test_amount(input_, unit, calculate_unc_output):
    r = ILCD1ToECS2Amount(input_['resultingAmount'], unit, input_)
    
    field = ECS2CustomExchange()
    r.calculate_unc(field)
    
    assert r.m == input_['resultingAmount']
    assert r._a == up.Quantity(input_['resultingAmount'], unit.replace('Item(s)', 'item'))
    assert r._f == f[0]
    assert r.dimensionality == dims[unit]
    assert hasattr(r, '_unc') == calculate_unc_output
    
    for md in mult_div:
        r.multiply(md)
        r.divide(md)
    
    field = ECS2Uncertainty()
    r.calculate_unc(field)
    
    assert r.m == input_['resultingAmount']
    assert r._a == up.Quantity(input_['resultingAmount'], unit.replace('Item(s)', 'item'))
    assert r._f == f[0]
    assert r.dimensionality == dims[unit]
    assert hasattr(r, '_unc') == calculate_unc_output

### Variables

# variable parameter start [has to be the first]
## name and o_name
## amount
## formula
## comment
## check _available_variables
## check _non_conform_variables

names = ['__name1', '_name2', 'name3', 'name4']
formula = [{'__name1*name3*name4': 'uc__name1*name3*name4'},
           {'_name2/__name1': 'uc_name2/uc__name1'},
           {'__name1+(name3+__name1)': 'uc__name1+(name3+uc__name1)'},
           {None:None}]
comments = ['lol', 'lol2', '[kg] lol', '[dimensionless]']
amount = 0.0

pre3 = [{
    'meanValue': amount, # [SPEC]: lognormal with negative values
    'relativeStandardDeviation95In': 1.0,
    'comment': {'@lang': 'en', '#text': c}
    } for c in comments]

vp = [{ # Maybe build a function to create log-normal dicts using x and use them here and in the lognormal
      '@name': a,
      'formula': b,
      'minimumValue': x['meanValue']*x['relativeStandardDeviation95In']**2,
      'maximumValue': x['meanValue']/x['relativeStandardDeviation95In']**2,
      'uncertaintyDistributionType': 'log-normal',
      } | x for a, b, x in zip(names, [list(x.keys())[0] for x in formula], pre3)]

res1 = [{
        'o_name': names[0],
        'name': 'uc__name1',
        '_non_conform_variables': {'__name1': 'uc__name1'},
        'amount': up.Quantity(amount, 'dimensionless'),
        'uncertainty': True,
        'unit': None,
        'formula': list(formula[0].keys())[0],
        'comment': 'lol'
        },
       {
        'o_name': names[1],
        'name': 'uc_name2',
        '_non_conform_variables': {'__name1': 'uc__name1', '_name2': 'uc_name2'},
        'amount': up.Quantity(amount, 'dimensionless'),
        'uncertainty': True,
        'unit': None,
        'formula': list(formula[1].keys())[0],
        'comment': 'lol2'
        },
       {
        'o_name': names[2],
        'name': 'name3',
        '_non_conform_variables': {'__name1': 'uc__name1', '_name2': 'uc_name2'},
        'amount': up.Quantity(amount, 'dimensionless'),
        'uncertainty': True,
        'unit': 'kg',
        'formula': list(formula[2].keys())[0],
        'comment': 'lol'
        },
       {
        'o_name': names[3],
        'name': 'name4',
        '_non_conform_variables': {'__name1': 'uc__name1', '_name2': 'uc_name2'},
        'amount': up.Quantity(amount, 'dimensionless'),
        'uncertainty': True,
        'unit': 'dimensionless',
        'formula': list(formula[3].keys())[0],
        'comment': ''
        }]

# get_variable start [has to be the second]
## use _available variables from before
## use _non_conform_variables to change the formula
## check new _available_variables with instances

# (input name, formula)
case2 = list(zip(names[:2], [list(x.values())[0] for x in formula[:2]]))

# create_parameter start [has to be the last]
## use _available variables from before
## use _non_conform_variables to change the formula
## No UnitId here due to inconsistencies

cp = [{ # name4 appears before
       'name': 'name4',
       '@parameterId': uuid_from_string('name4'),
       '@amount': 0.0,
       'unitName': {'@xml:lang': 'en', '#text': 'dimensionless'},
       '@variableName': 'name4',
       'uncertainty': {
           '@mu': 0.0,
           '@meanValue': 0.0,
           '@variance': 0.0, # The update will change the value if the comment has the variance
           '@varianceWithPedigreeUncertainty': 0.0
           },
       'comment': []
       },
      {
        'name': 'name3',
        '@parameterId': uuid_from_string('name3'),
        '@amount': 0.0,
        'unitName': 'kg',
        '@variableName': 'name3',
        '@mathematicalRelation': list(formula[2].values())[0],
        '@isCalculatedAmount': 'true',
        'uncertainty': {
            '@mu': 0.0,
            '@meanValue': 0.0,
            '@variance': 0.0, # The update will change the value if the comment has the variance
            '@varianceWithPedigreeUncertainty': 0.0
            },
        'comment': {'@xml:lang': 'en', '#text': 'lol'}
        }]

# Entering

s = ECS2Structure()
ILCD1ToECS2VariableConversion.amountClass = ILCD1ToECS2Amount
ILCD1ToECS2VariableConversion.parameter_holder = s.flowData
ILCD1ToECS2VariableConversion.master_field = s.userMaster

av_i = 0

@pytest.mark.variable
@pytest.mark.parametrize('input_, type_, res', [
    *((x, 1, y) for x, y in zip(deepcopy(vp), deepcopy(res1))),
    *((x, 2, y) for x, y in case2),
    *((None, 3, x) for x in cp)
    ])
def test_variable(input_, type_, res):
    
    nc = ILCD1ToECS2DataNotConverted()
    
    if type_ == 1:
        r = ILCD1ToECS2VariableConversion(input_, nc)
    
        global av_i
        av_i += 1
    
        assert list(ILCD1ToECS2VariableConversion._available_variables.keys()) == names[:av_i]
        for var in ('name', 'o_name', '_non_conform_variables', 'formula'):    
            assert getattr(r, var) == res[var]
        assert r.amount.a == res['amount']
        assert hasattr(r.amount, '_unc') == res['uncertainty']
        assert r.comment[0]['#text'] == res['comment']
        if res['unit']:
            assert r.unit == res['unit']
    
    elif type_ == 2:
        r = ILCD1ToECS2VariableConversion.get_variable(input_)
        
        assert ILCD1ToECS2VariableConversion._available_variables[input_]['used?'] == True
        assert ILCD1ToECS2VariableConversion._available_variables[input_]['self'].formula == res
        
    elif type_ == 3:
        r = ILCD1ToECS2VariableConversion.create_parameters()
        
        for entry in ILCD1ToECS2VariableConversion.parameter_holder.get('parameter'):
            if entry.get_dict()['name'] == res['name']:
                assert entry.get_dict() == res

### General reference

## Get file, test all cases of input from the reference
## id_, shortDescription and isConvertible

from pathlib import Path

ILCD1ToECS2ReferenceConversion.uuid_specs = ILCD1ToECS2BasicFieldMapping._uuid_conv_spec
ILCD1ToECS2ReferenceConversion.elem_flow_mapping = ILCD1ToECS2BasicFieldMapping._dict_from_file(Path("Mappings/ilcd1_to_ecs2_elementary_flows.json"), 'SourceFlowUUID')
ILCD1ToECS2ReferenceConversion.class_conversion = ILCD1ToECS2ClassificationConversion
ILCD1ToECS2ReferenceConversion._ilcd_root_path = './src/'

type_ = ['sources', 'contacts', 'flows']
version = ['00.00.000', '00.00.001', '00.00']
id_ = ['e6d7e2cf-8204-4069-bad3-f2cc57794d55',
       'e6d7e2cf-8204-4069-bad3-f2cc57794d55',
       'e6d7e2cf-8204-4069-bad3-f2cc57794d55']
uri = [lambda x: '', lambda x: '../'+x+'/e6d7e2cf-8204-4069-bad3-f2cc57794d55_00.00.001.xml', lambda x: '']

rf = [{
    '@type': lambda t: t[:-1] + ' data set',
    '@refObjectId': b,
    '@version': a,
    '@uri': c
    } for a, b, c in list(zip(deepcopy(version), deepcopy(id_), deepcopy(uri)))] + [
        {
            '@type': lambda t: 'flow data set',
            '@refObjectId': 'ca1d20a2-c6de-42d0-8a2a-34db3dca8147',
            '@version': '00.00',
            '@uri': lambda t: ''
            }
        ]
isconv = [True] * (len(rf) - 1) + [False]
res = ['lol2\n', 'lol3\n', 'lol1\n', None]

@pytest.mark.reference
@pytest.mark.parametrize('input_, type_, res, conv', [
    *((a, t, b, c) for a, b, c in list(zip(deepcopy(rf), deepcopy(res), deepcopy(isconv))) for t in deepcopy(type_))
    ])
def test_general_reference(input_, type_, res, conv):
    inp = deepcopy(input_)
    inp['@type'] = inp['@type'](type_)
    inp['@uri'] = inp['@uri'](type_)
    
    nc = ILCD1ToECS2DataNotConverted()
    ILCD1ToECS2ReferenceConversion.type_ = type_
    print(inp)
    r = ILCD1ToECS2ReferenceConversion(inp, nc)
    
    assert r.isConvertible == conv
    if conv:
        print(r.file.name)
        with open(r.file) as f:
            assert res == f.read()
    else:
        assert r.file is None

### Contact

ILCD1ToECS2ContactReferenceConversion.master_field = s.userMaster

case1cont = {
    '@type': 'contact data set',
    '@refObjectId': '3b0db486-77eb-46a0-9fea-34b069410e71',
    '@version': '01.00.001',
    '@uri': '../contacts/3b0db486-77eb-46a0-9fea-34b069410e71',
    'shortDescription': {'@lang': 'en', '#text': 'Someone'} # [!] Maybe it can have 2 or more
    }
res1cont = {
    '@personId': '35d091e9-38c2-4037-9efe-a73673c57123',
    '@personName': 'Someone',
    '@personEmail': 'someone@ecoinvent.org',
    '@isCopyrightProtected': 'true'
    }

@pytest.mark.contact
@pytest.mark.parametrize('input_, res', [(deepcopy(case1cont), deepcopy(res1cont))])
def test_contacts(input_, res):
    
    nc = ILCD1ToECS2DataNotConverted()
    dp = s.administrativeInformation.dataGeneratorAndPublication
    dp.isCopyrightProtected = 'true'
    r = ILCD1ToECS2ContactReferenceConversion(input_, nc,
                                              dp,
                                              {'id': 'personId',
                                               'name': 'personName',
                                               'email': 'personEmail'})
    r.get_contact()

    assert r.field.get_dict() == res

### Source

ILCD1ToECS2SourceReferenceConversion.master_field = s.userMaster

ex1 = {}
ex2 = {'id': 'publishedSourceId',
       'first_author': 'publishedSourceFirstAuthor',
       'year': 'publishedSourceYear',
       'page': 'pageNumbers'}

dgpr = {
    '@personId': '92f95dc4-28c2-4f20-a8c5-79700330f78b',
    '@personName': 's',
    '@personEmail': 's@gmail.com',
    '@isCopyrightProtected': 'true'
    }

c1 = [('92f95dc4-28c2-4f20-a8c5-79700330f78b', 'Normal source'),
      ('92f95dc4-28c2-4f20-a8c5-79700330f78c', 'Normal source'),
      ('92f95dc4-28c2-4f20-a8c5-79700330f78d', 'Normal source'),
      ('66c4a7f3-296e-4876-9133-4a0dcfd89df5', 'Image URL from '),
      ('66c4a7f3-296e-4876-9133-4a0dcfd89df5', 'Dataset Icon'),
      ('66c4a7f3-296e-4876-9133-4a0dcfd89df5', 'URI source that is difficult to know')]
uri_source = [False, False, False, False, False, True]

case1 = [{
    '@type': 'source data set',
    '@refObjectId': a,
    '@version': '01.00.001',
    '@uri': '../sources/'+a,
    'shortDescription': {'@lang': 'en', '#text': b} # [!] Maybe it can have 2 or more
    } for a, b in c1]

res1 = [{
    '@publishedSourceId': '9c08da7f-924e-4455-a312-37a346693cb5',
    '@publishedSourceFirstAuthor': 'Someone.',
    '@publishedSourceYear': '2018',
    '@pageNumbers': '12-49'
    } | dgpr,{
    '@publishedSourceId': '9c08da7f-924e-4455-a312-37a346693cb2',
    '@publishedSourceFirstAuthor': 'Someone.',
    '@publishedSourceYear': '2018'
    } | dgpr,{
    '@publishedSourceId': '9c08da7f-924e-4455-a312-37a346693cb3',
    '@publishedSourceFirstAuthor': 'Someone With No Year'
    } | dgpr,{
    'imageUrl': [{'@index': 1001, '#text': 'https://db3.ecoinvent.org/images/66c4a7f3-296e-4876-9133-4a0dcfd89df5'}] 
    },{
    '@datasetIcon': 'https://db3.ecoinvent.org/images/66c4a7f3-296e-4876-9133-4a0dcfd89df5' 
    },{
    'imageUrl': [{'@index': 1001, '#text': 'https://db3.ecoinvent.org/images/66c4a7f3-296e-4876-9133-4a0dcfd89df5'}] 
    }]

@pytest.mark.source
@pytest.mark.parametrize('input_, field, attrname, uri_source, res', [
    *((a, b, c, d, e) for a, b, c, d, e in zip(case1,
                                               [2, 2, 2, 1, 1, 1],
                                               [ex2, ex2, ex2, ex1, ex1, ex1],
                                               uri_source,
                                               res1))
    ])
def test_sources(input_, field, attrname, uri_source, res):
    
    ILCD1Helper.number = 1000
    
    s2 = ECS2Structure()
    
    if field == 1:
        act = s2.activityDescription.activity
        act.id = '9c08da7f-924e-4455-a312-37a346693cb3'
        act.activityNameId = '9c08da7f-924e-4455-a312-37a346693cb3'
        act.inheritanceDepth = 1
        act.type = 1
        act.specialActivityType = 1
        act.energyValues = 1
        act.activityName = {'@index': 1, '@lang': 'en', '#text': 'lol'}
        f  = {'imageUrl': s2.activityDescription.activity.generalComment,
               'datasetIcon': act}
    else:
        dgp = s2.administrativeInformation.dataGeneratorAndPublication
        dgp.personId = '92f95dc4-28c2-4f20-a8c5-79700330f78b'
        dgp.personName = 's'
        dgp.personEmail = 's@gmail.com'
        dgp.isCopyrightProtected = 'true'
        f  = {'regular': dgp}
    
    nc = ILCD1ToECS2DataNotConverted()
    r = ILCD1ToECS2SourceReferenceConversion(input_, nc, f, attrname, uri_source)
    r.get_source()
    
    if '@datasetIcon' in res:
        assert r.field.get_dict()['@datasetIcon'] == res['@datasetIcon']
    else:
        assert r.field.get_dict() == res

### Review

def set_TextAndImage(x):
    tai = s.textAndImage()
    setattr(tai, 'text', {'@index': 1001} | x)
    return tai

ILCD1ToECS2ReviewConversion._set_TextAndImage = set_TextAndImage
ILCD1ToECS2ReviewConversion.contact_ref_conversion = ILCD1ToECS2ContactReferenceConversion
ILCD1ToECS2ReviewConversion.review_holder = s.modellingAndValidation

com1 = ['nothing', 'Review Version: 1.2.3.4\nDate of Review: 2021-02-21\nsomething']
com1r = ['nothing', 'something']
com2 = ['lol1', 'lol2']

case1 = [{
    'reviewDetails': {'@lang': 'en', '#text': a},
    'otherReviewDetails': {'@lang': 'en', '#text': b},
    'referenceToNameOfReviewerAndInstitution': case1cont
    } for a, b in zip(com1, com2)]

ref = {
    '@reviewerId': '35d091e9-38c2-4037-9efe-a73673c57123',
    '@reviewerName': 'Someone',
    '@reviewerEmail': 'someone@ecoinvent.org'
    }

res1 = [{
    'details': [{'text': [{'@index': 1001, '@xml:lang': 'en', '#text': 'nothing'}]}],
    'otherDetails': [{'@xml:lang': 'en', '#text': 'lol1'}],
    '@reviewDate': '1900-01-01',
    '@reviewedMajorRelease': 1,
    '@reviewedMinorRelease': 0,
    '@reviewedMajorRevision': 1,
    '@reviewedMinorRevision': 0
    } | ref,{
    'details': [{'text': [{'@index': 1001, '@xml:lang': 'en', '#text': 'something'}]}],
    'otherDetails': [{'@xml:lang': 'en', '#text': 'lol2'}],
    '@reviewDate': '2021-02-21',
    '@reviewedMajorRelease': 1,
    '@reviewedMinorRelease': 2,
    '@reviewedMajorRevision': 3,
    '@reviewedMinorRevision': 4
    } | ref]
       
@pytest.mark.review
@pytest.mark.parametrize('input_, res', [
    *((c, r) for c, r in zip(case1, res1))
    ])
def test_review(input_, res):
    
    ILCD1Helper.number = 1000
    
    nc = ILCD1ToECS2DataNotConverted()
    r = ILCD1ToECS2ReviewConversion(input_, nc)
    
    assert r.field.get_dict() == res

### Classification

ILCD1ToECS2ClassificationConversion.class_holder = s.activityDescription
ILCD1ToECS2ClassificationConversion.master_field = s.userMaster
ILCD1ToECS2ClassificationConversion.class_mapping = ILCD1ToECS2BasicFieldMapping._dict_from_file(Path("Mappings/ilcd1_to_ecs2_classes.json"), 'SourceFlowUUID')

c1 = [{
      '@name': 'ISIC rev.4 ecoinvent',
      '@classes': '../classification_ISIC rev.4 ecoinvent.xml',
      'class': [{
          '@level': 0,
          '@classId': '3',
          '#text': 'C.Manufacturing'
          },{
          '@level': 1,
          '@classId': '3.16',
          '#text': '24:Manufacture of basic metals'
          },{
          '@level': 2,
          '@classId': '3.16.2',
          '#text': '242:Manufacture of basic precious and other non-ferrous metals'
          },{
          '@level': 3,
          '@classId': '3.16.2.1',
          '#text': '2420:Manufacture of basic precious and other non-ferrous metals'
          }]
      },{
      '@name': 'EcoSpold01Categories',
      '@classes': '../classification_EcoSpold01Categories',
      'class': [{
          '@level': 0,
          '@classId': '39.3',
          '#text': 'metals'
          },{
          '@level': 1,
          '@classId': '39.3',
          '#text': 'extraction'
          }]
      }]

res = [{
        '@classificationId': '6fe7bc2b-4be4-48f7-92b0-f27dea9053ce',
        'classificationSystem': [{'@xml:lang': 'en', '#text': 'ISIC rev.4 ecoinvent'}],
        'classificationValue': {'@xml:lang': 'en', '#text': '2420:Manufacture of basic precious and other non-ferrous metals'}
        },{
        '@classificationId': 'aeaec32d-b5a4-44e0-bb50-25c0f4fe3d37',
        'classificationSystem': [{'@xml:lang': 'en', '#text': 'EcoSpold01Categories'}],
        'classificationValue': {'@xml:lang': 'en', '#text': 'metals/extraction'}
        }]

@pytest.mark.classification
@pytest.mark.parametrize('input_, res', [
    *((a, b) for a, b in zip(c1, res))
    ])
def test_classification(input_, res):
    
    nc = ILCD1ToECS2DataNotConverted()
    r = ILCD1ToECS2ClassificationConversion(input_, nc)
    
    assert r.field.get_dict() == res

### Property -> Depends on the FlowDataSet file

ILCD1ToECS2FlowConversion.Property.amountClass = ILCD1ToECS2Amount
ILCD1ToECS2FlowConversion.Property.property_holder = s.property
ILCD1ToECS2FlowConversion.Property.master_field = s.userMaster

# Estipulate all cases
# Get all wanted answers
# Verify possible posterior uses 

# with uncertainty / content, water content, nope, energy || allocation
class F: # Mocking a flow
    _flow_internal_refs = {'0': 'lol', '1': 'lol2', '2': 'lol3'}
    class A:
        def __init__(self, u):
            self.u = u
    def __init__(self, u):
        self.amount = self.A(u)

isconv = [[True, True, False, True, True], [True]*3]
energy1 = ['GROSS']
energy2 = ['GROSS']

allocs = [{},
          {'allocation for lol': 44.32,
           'allocation for lol3': 55.68}
          ]

flow1 = F('kg')
case1 = [(1, '64b8e725-b0ba-4837-abb9-62dc0e7b9f6f', 'carbon content, fossil', 0.85),
        (2, '7ec8d70e-4ffc-4024-86b7-6141cc0a2bf5', 'water content', 0.6),
        (3, 'ca1d20a2-c6de-42d0-8a2a-34db3dca8147', 'not_convertible', 1),
        (4, '93a60a56-a3c8-14da-a746-0800200c9a66', 'heating value, gross', 0.5),
        (5, '085af809-5dc6-4920-aaa1-4ac493ae4af8', 'nitrogen content', 0.1)]

flow2 = F('m**3')
case2 = [(1, '64b8e725-b0ba-4837-abb9-62dc0e7b9f6f', 'carbon content, fossil', 0.85),
         (2, '7ec8d70e-4ffc-4024-86b7-6141cc0a2bf5', 'water content', 0.6),
         (3, '085af809-5dc6-4920-aaa1-4ac493ae4af8', 'nitrogen content', 0.1)]

unc = {
    'relativeStandardDeviation95In': 1.24,
    'minimumAmount': 0.84,
    'maximumAmount': 0.86,
    'uncertaintyDistributionType': 'log-normal',
    'generalComment': {'@lang': 'en', '#text': 'lol'}
}
uncres = {
    'uncertainty': [{
        'lognormal': [{ 
            '@mu': math.log(0.85),
            '@meanValue': 0.85,
            '@variance': math.log(math.sqrt(1.24))**2, # The update will change the value if the comment has the variance
            '@varianceWithPedigreeUncertainty': math.log(math.sqrt(1.24))**2
            }],
        }],
    'comment': [{'@xml:lang': 'en', '#text': 'lol'}]
    }

res1 = [('dimensionless', '577e242a-461f-44a7-922c-d8e1c3d2bf45', 'c74c3729-e577-4081-b572-a283d2561a75', 'carbon content, fossil', 0.85/0.4),
       ('dimensionless', '577e242a-461f-44a7-922c-d8e1c3d2bf45', 'a9358458-9724-4f03-b622-106eda248916', 'water content', 0.6/0.4),
       ('MJ', '980b811e-3905-4797-82a5-173f5568bc7e', 'd61b8768-8ef6-4a99-ae16-9e51f24ad5b5', 'heating value, gross', 0.5),
       ('kg/kg', '83ecd334-1b5b-4784-8938-6a0d0a9d8954', 'cf66b969-7413-4ee7-aaf1-8a3b47904836', 'concentration, nitrogen', 0.1), # No DRY MASS here
       ('kg', '487df68b-4994-4027-8fdc-a4dc298257b7', '67f102e2-9cb6-4d20-aa16-bf74d8a03326', 'wet mass', 1), # This 3 comes only after all the others
       ('kg', '487df68b-4994-4027-8fdc-a4dc298257b7', '3a0af1d6-04c3-41c6-a3da-92c4f61e0eaa', 'dry mass', 0.4),
       ('kg', '487df68b-4994-4027-8fdc-a4dc298257b7', '6d9e1462-80e3-4f10-b3f4-71febd6f1168', 'water in wet mass', 0.6),]

res2 = [('dimensionless', '577e242a-461f-44a7-922c-d8e1c3d2bf45', 'c74c3729-e577-4081-b572-a283d2561a75', 'carbon content, fossil', 0.85),
        ('dimensionless', '577e242a-461f-44a7-922c-d8e1c3d2bf45', 'a9358458-9724-4f03-b622-106eda248916', 'water content', 0.6),
        ('kg/m3', 'cacb6d36-694d-4e4f-9e79-6c9c73146839', 'f04a971d-f503-4ca0-b2b1-0ecd2e53ea61', 'mass concentration, nitrogen', 0.1),
        ('dimensionless', '577e242a-461f-44a7-922c-d8e1c3d2bf45', 'cb8b0f94-4e17-39af-bc82-ccbadb787443', 'allocation for lol', 44.32),
        ('dimensionless', '577e242a-461f-44a7-922c-d8e1c3d2bf45', '5d4ca38f-5723-3b21-9948-91d145e5d3ed', 'allocation for lol3', 55.68)]

c1 = [[c, {
    '@dataSetInternalId': a,
    'referenceToFlowPropertyDataSet': {
        '@type': 'flow property data set',
        '@refObjectId': b,
        '@version': '01.00.001',
        '@uri': '../flowproperties/'+b,
        'shortDescription': {'@lang': 'en', '#text': c} # [!] Maybe it can have 2 or more
        },
    'meanValue': d,
    }] for a, b, c, d in case1]
c1[0][1] = c1[0][1] | unc

c2 = [(c, {
    '@dataSetInternalId': a,
    'referenceToFlowPropertyDataSet': {
        '@type': 'flow property data set',
        '@refObjectId': b,
        '@version': '01.00.001',
        '@uri': '../flowproperties/'+b,
        'shortDescription': {'@lang': 'en', '#text': c} # [!] Maybe it can have 2 or more
        },
    'meanValue': d,
    }) for a, b, c, d in case2]

r1 = [{
    'unitName': [{'@xml:lang': 'en', '#text': a}],
    '@unitId': b,
    '@propertyId': c,
    'name': {'@xml:lang': 'en', '#text': d},
    '@amount': e
    } for a, b, c, d, e in res1]
r1[0] = r1[0] | uncres

r2 = [{
    'unitName': [{'@xml:lang': 'en', '#text': a}],
    '@unitId': b,
    '@propertyId': c,
    'name': {'@xml:lang': 'en', '#text': d},
    '@amount': e
    } for a, b, c, d, e in res2]

# all inits
@pytest.mark.property
@pytest.mark.parametrize('input_, alloc, flow, isconv, energy, res', [
    (c1, allocs[0], flow1, isconv[0], energy1, r1),
    (c2, allocs[1], flow2, isconv[1], energy2, r2),
    ])
def test_properties(input_, alloc, flow, isconv, energy, res):
    
    nc = ILCD1ToECS2DataNotConverted()
    r = {}
    for j, (name, i) in enumerate(input_):
        r[name] = ILCD1ToECS2FlowConversion.Property.normal_init(i, nc)
        assert r[name].isConvertible == isconv[j]
    
    assert ILCD1ToECS2FlowConversion.Property._energy == energy
    
    r = {k: v for k, v in r.items() if v.isConvertible}
    
    r = ILCD1ToECS2FlowConversion.Property.convert_properties(r, flow) # depends on flow
    
    flow_master = s.userMaster.get_class('intermediateExchange')()
    r.extend([ILCD1ToECS2FlowConversion.Property.allocation_init({'@lang': 'en', '#text': k}, v, flow_master) for k, v in alloc.items()])
    
    for i, p in enumerate(r):
        assert p.field.get_dict() == res[i]

### Flow

ILCD1ToECS2FlowConversion.uuid_specs = ILCD1ToECS2BasicFieldMapping._uuid_conv_spec
ILCD1ToECS2FlowConversion.compartment_mapping = ILCD1ToECS2BasicFieldMapping._default_compartment_mapping

ILCD1ToECS2FlowConversion.amountClass = ILCD1ToECS2Amount
ILCD1ToECS2FlowConversion.source_ref_conversion = ILCD1ToECS2SourceReferenceConversion
ILCD1ToECS2FlowConversion.variable_conversion = ILCD1ToECS2VariableConversion

ILCD1ToECS2FlowConversion.flow_holder = s.flowData
ILCD1ToECS2FlowConversion.master_field = s.userMaster

ILCD1ToECS2FlowConversion.uuid_process = 'ca1d20a2-c6de-42d0-8a2a-34db3dca8147'

ILCD1ToECS2FlowConversion._flow_internal_refs = {'0': 'lol', '1': 'lol2', '2': 'lol3'}

reff = [[], ['0'], ['0', '2']] # <- outputGroup [do flows three times]
group = ['Input', 'Output', 'Input'] # 0 and 1
dsi = ['0', '1', '2']
id_ = ['4f3622dd-ce6f-435e-9e4b-9cb1ef3f5656', '08a91e70-3ddc-11dd-9b5d-0050c2490048', '08a91e70-3ddc-11dd-91e5-111111111111']

allocs = [[],
          [{
          '@internalReferenceToCoProduct': 0,
          '@allocatedFraction': 44.32
          },
          {
          '@internalReferenceToCoProduct': 2,
          '@allocatedFraction': 55.68
          }], []]

flow = [{ # 3 cases, 1 with no conversion; variable not tested
        '@dataSetInternalID': a, # T reference
        'referenceToFlowDataSet': {
            '@type': 'flow data set',
            '@refObjectId': b, # id_
            '@version': '01.00.001',
            '@uri': '',
            'shortDescription': [{'@lang': 'en', '#text': 'lol'},
                                 {'@lang': 'de', '#text': 'lol2'}]
            },
        'exchangeDirection': c, # T group
        'allocations': {
            'allocation': d # T alloc_properties
            }
        } | normal[0] for a, b, c, d in zip(dsi, id_, group, allocs)] # for meanAmount and colleagues # OK amount / comment

# Verificação intermediária
info = [{
    'type': 'Waste flow',
    'name': [{'@lang': 'en', '#text': '1,1-dimethylcyclopentane'}],
    'synonym': [],
    'reference': '0'
    }, {
    'type': 'Elementary flow',
    'name': [{'@lang': 'en', '#text': 'asulam'}, {'@lang': 'de', '#text': 'lamasul'}],
    'CAS': '3337-71-1',
    'formula': '123456',
    'synonym': [{'@index': 0, '@lang': 'en', '#text': '4-Amino-benzolsulfonyl-methylcarbamat'},
                {'@index': 1, '@lang': 'en', '#text': 'AC-12057'},
                {'@index': 2, '@lang': 'en', '#text': 'AC1L2CQ3'},
                {'@index': 0, '@lang': 'de', '#text': '4-Amino-benzolsulfonyl-methylcarbamat'}],
    'reference': '0'
    }, None]
# Classification is verified in the classification conversion
isconv = [True, True, False]

# Verificação final (nova incerteza para o fator de multiplicação)
resnorm3 = { # f = 19.1
    '@meanValue': ra[0] * 19.1,
    '@variance': (rstd[0] * 19.1 / 2) ** 2, # The update will change the value if the comment has the variance
    '@varianceWithPedigreeUncertainty': (rstd[0] * 19.1 / 2) ** 2
    }
# Comentários precisam ser separados
rsn0 = deepcopy(resnorm1[0])

int1 = { # input/output groups differ as the reference flows are placed and the id changes as it has to be different inside the process
    '@id': '8ea99062-9af1-3b64-9f6d-f848a991a209',
    '@intermediateExchangeId': '41bae23f-237d-4ba6-9b1d-73d5f4baee55',
    '@amount': resnorm1[0]['@meanValue'],
    'name': {'@xml:lang': 'en', '#text': '1,1-dimethylcyclopentane'},
    'unitName': [{'@xml:lang': 'en', '#text': 'kg'}],
    '@unitId': '487df68b-4994-4027-8fdc-a4dc298257b7',
    'inputGroup': 5,
    'classification': [],
    'property': [],
    'uncertainty': [{'normal': [rsn0]}],
    'comment': [{'@xml:lang': 'en', '#text': 'lol'}]
    }
int2 = dict((k.replace('inputGroup', 'outputGroup'),v if v != 5 else 0) for k,v in deepcopy(int1).items()) | {'@id': '94fb687e-73d1-3b1d-9b54-c142d6b5dc13'}
int3 = deepcopy(int2) | {'@id': 'bb49abcd-8d38-3e17-9a32-e01e54511ec1'}

ele1 = {
    '@id': '26e57f2b-5b85-375f-aafe-42efe871c2cf',
    '@elementaryExchangeId': 'b6d0042d-0ef8-49ed-9162-a07ff1ccf750',
    '@amount': resnorm3['@meanValue'],
    'name': {'@xml:lang': 'en', '#text': 'coal, hard, unspecified, in ground'},
    'unitName': [{'@xml:lang': 'en', '#text': 'kg'}],
    '@unitId': '487df68b-4994-4027-8fdc-a4dc298257b7',
    '@casNumber': '3337-71-1',
    'synonym': [{'@xml:lang': 'en', '#text': '4-Amino-benzolsulfonyl-methylcarbamat'},
                {'@xml:lang': 'de', '#text': '4-Amino-benzolsulfonyl-methylcarbamat'},
                {'@xml:lang': 'en', '#text': 'AC-12057'},
                {'@xml:lang': 'en', '#text': 'AC1L2CQ3'}],
    '@formula': '123456',
    'outputGroup': 4,
    'compartment': [{
        '@subcompartmentId': '6a098164-9f04-4f65-8104-ffab7f2677f3',
        'compartment': [{'@xml:lang': 'en', '#text': 'natural resource'}],
        'subcompartment': [{'@xml:lang': 'en', '#text': 'in ground'}],
        }],
    'property': [],
    'uncertainty': [{'normal': [resnorm3]}],
    'comment': [{'@xml:lang': 'en', '#text': 'lol'}]
    }
ele2 = deepcopy(ele1) | {'@id': '1678c418-7b13-31b2-a1d9-a5f9151d9ae3'}
ele3 = deepcopy(ele1) | {'@id': '7364145d-bd8e-3f90-8d49-8c80c681dc45'}

res_flow = [[int1, ele1, None],
            [int2, ele2, None],
            [int3, ele3, None]]

@pytest.mark.flow
@pytest.mark.parametrize('input_, info, isconv, rf, res', [
    *((f, a, c, r, res) for r, re in zip(reff, res_flow) for f, a, c, res in zip(flow, info, isconv, re))
    ])
def test_flows(input_, info, isconv, rf, res):
    
    nc = ILCD1ToECS2DataNotConverted()
    ILCD1ToECS2FlowConversion._reference_flows = rf
    r1 = ILCD1ToECS2FlowConversion(input_, nc)
    
    _ = ILCD1ToECS2FlowReferenceConversion(input_['referenceToFlowDataSet'], nc, r1).get_flow()
    
    assert r1.isConvertible == isconv
    if isconv:
        assert r1.info == info
    
        assert sorted(r1.field.get_dict().keys()) == sorted(res.keys())
        for k, v in r1.field.get_dict().items():
            if k not in ("classification", "property"):
                assert v == res[k]

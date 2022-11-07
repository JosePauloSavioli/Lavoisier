#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 13:39:38 2022

@author: jotape42p
"""

import math
import logging
import pytest
import openturns as ot
from copy import deepcopy
from src.Lavoisier.conversions.ECS2_to_ILCD1_conversion import (
    ECS2ToILCD1Amount,
    ECS2ToILCD1ReferenceConversion,
    ECS2ToILCD1UncertaintyConversion,
    ECS2ToILCD1VariableConversion,
    ECS2ToILCD1ParameterConversion,
    ECS2ToILCD1FlowConversion,
    up # Has to be the same Registry
)
from src.Lavoisier.data_structures import (
    ILCD1Structure,
    ECS2ToILCD1DataNotConverted
)

from src.Lavoisier.conversions.units import pint_to_ilcd_fp
from src.Lavoisier.conversions.utils import uuid_from_uuid
from src.Lavoisier.formats import ILCD1Helper

uuid = 'd1488bd2-9cb5-44ff-b2f1-c71d4bcc69f6'

comment = {
    '@lang': 'en',
    '#text': 'some important comment that is here'
    }
comment2 = {
    '@lang': 'en',
    '#text': 'some important comment that is here 2'
    }
c1 = {'@lang': 'en', '#text': 'Uncertainty Comment:'}

pedigree_1 = {
    '@reliability': "4",
    '@completeness': "3",
    '@temporalCorrelation': "1",
    '@geographicalCorrelation': "3",
    '@furtherTechnologyCorrelation': "4"
    }
pedigree_1_comment = "Pedigree: (4,3,1,3,4)"
p1c = {'@lang': 'en', '#text': pedigree_1_comment}

pedigree_2 = {
    '@reliability': "1",
    '@completeness': "1",
    '@temporalCorrelation': "1",
    '@geographicalCorrelation': "1",
    '@furtherTechnologyCorrelation': "1"
    }
pedigree_2_comment = "Pedigree: (1,1,1,1,1)"
p2c = {'@lang': 'en', '#text': pedigree_2_comment}

###############################################################################

unc_lognormal_1 = { # Lognormal OK
    'lognormal': {
        '@meanValue': '0.0101242661016201', # TFloatNumber = xs:double
        '@mu': '-4.593',
        '@variance': '0.0006',
        '@varianceWithPedigreeUncertainty': '0.0493'
        },
    'pedigreeMatrix': pedigree_1,
    'comment': comment
    }
unc_lognormal_2 = deepcopy(unc_lognormal_1) # Lognormal Pedigree warning
unc_lognormal_2['pedigreeMatrix'] = pedigree_2
unc_lognormal_3 = deepcopy(unc_lognormal_1) # Lognormal negative mean warning
unc_lognormal_3['lognormal']['@meanValue'] = '-0.0101242661016201'
cvar0 = {'@lang': 'en', '#text': 'Basic Variance: 0.0006'}
cvar1 = '; Basic Variance: 0.0006'

unc_normal = {
    'normal': {
        '@meanValue': '-1',
        '@variance': '0.0006',
        '@varianceWithPedigreeUncertainty': '0.0493'
        },
    'pedigreeMatrix': pedigree_1,
    'comment': comment
    }

unc_triangular_1 = {
    'triangular': {
        '@minValue': '0',
        '@mostLikelyValue': '0.00574631326170398',
        '@maxValue': '0.00587'
        },
    'comment': comment
    }
unc_triangular_2 = deepcopy(unc_triangular_1)
unc_triangular_2['triangular']['@maxValue'] = '0.00537'
del unc_triangular_2['comment']

unc_uniform = {
    'uniform': {
        '@minValue': '0.001',
        '@maxValue': '0.07'
        },
    'pedigreeMatrix': pedigree_1
    }

unc_undefined = {
    'undefined': {
        '@minValue': '10',
        '@maxValue': '230',
        '@standardDeviation95': '100'
        },
    'pedigreeMatrix': pedigree_1,
    'comment': ''
    }

unc_beta = {
    'beta': {
        '@minValue': '0.0',
        '@mostLikelyValue': '0.25',
        '@maxValue': '0.5'
        }
    }
cbeta = {'@lang': 'en', '#text': "\nNot Converted: Beta distribution with parameters min=0.0, most frequent=0.25, max=0.5"}

unc_gamma = {
    'gamma': {
        '@shape': '0.02',
        '@scale': '0.00574631326170398',
        '@minValue': '0.0001'
        },
    'pedigreeMatrix': pedigree_1,
    }
cgamma = {'@lang': 'en', '#text': "\nNot Converted: Gamma distribution with parameters shape=0.02, scale=0.00574631326170398, min=0.0001"}

unc_binomial = {
    'binomial': {
        '@n': '10',
        '@p': '0.5'
        },
    'pedigreeMatrix': pedigree_1,
    'comment': comment
    }
cbinomial = {'@lang': 'en', '#text': "\nNot Converted: Binomial distribution with parameters n=10, p=0.5"}

@pytest.mark.uncertainty
@pytest.mark.parametrize('unc, type_, vars_, comment', [
    (unc_lognormal_1, 'lognormal', [('_var', 0.0493)], [c1, p1c, cvar0, comment]),
    (unc_normal, 'normal', [('_var', 0.0493)], [c1, p1c, cvar0, comment]),
    (unc_triangular_1, 'triangular', [('_min', 0), ('_max', 0.00587)], [c1, comment]),
    (unc_triangular_2, 'triangular', [('_min', 0), ('_max', 0.00537)], []),
    (unc_uniform, 'uniform', [('_min', 0.001), ('_max', 0.07)], [c1, p1c]),
    (unc_undefined, 'undefined', [('_min', 10), ('_max', 230), ('_std', 100)], [c1, p1c]),
    (unc_beta, 'beta', [], [c1, cbeta]),
    (unc_gamma, 'gamma', [], [c1, p1c, cgamma]),
    (unc_binomial, 'binomial', [], [c1, p1c, comment, cbinomial]),
    ])
def test_regular_uncertainty_input(unc, type_, vars_, comment):
    r = ECS2ToILCD1UncertaintyConversion(unc)
    assert r._type == type_
    for k,v in vars_:
        assert getattr(r, k) == v
    if comment:
        for i in range(len(r.comment)): # @index doesn't really matter here
            assert r.comment[i]['@lang'] == comment[i]['@lang']
            assert r.comment[i]['#text'] == comment[i]['#text']
    else:
        assert r.comment == []
    
@pytest.mark.uncertainty
@pytest.mark.parametrize('unc, log_msg', [
    (unc_lognormal_2, "\t\tUncertainty: Pedigree uncertainty does not match the variance. 0.0006 + 0 != 0.0493"),
    (unc_lognormal_3, "\t\tUncertainty: Lognormal uncertainty with negative geometric mean -0.0101242661016201"),
    (unc_triangular_2, "\t\tUncertainty: Triangular distribution with mode out of bounds: 0.0 > 0.00574631326170398 > 0.00537")
    ])
def test_logging_input(unc, log_msg, caplog):
    _ = ECS2ToILCD1UncertaintyConversion(unc)
    assert caplog.record_tuples == [("root", logging.WARNING, log_msg)]
    
s = ILCD1Structure()
fp = s.flow_property
vp = s.mathematicalRelations.get_class('variableParameter')
ex = s.exchanges.get_class('exchange')

zn = 1.9599639845 # z-factor for 95% for a lognormal

@pytest.mark.uncertainty
@pytest.mark.parametrize('unc, name, field, comment, com_res, type_', [
    (unc_lognormal_1, 'lognormal', fp, 'generalComment', [{'@xml:lang': 'en', '#text': '\n'.join([c1['#text'], comment['#text'], p1c['#text']+cvar1])}], 'Value'),
    (unc_lognormal_2, 'lognormal', vp, 'comment', [{'@xml:lang': 'en', '#text': '\n'.join([c1['#text'], comment['#text'], p2c['#text']+cvar1])}], 'Value'),
    (unc_lognormal_3, 'lognormal', ex, 'generalComment', [{'@xml:lang': 'en', '#text': '\n'.join([c1['#text'], comment['#text'], p1c['#text']+cvar1])}], 'Amount'),
    (unc_normal, 'normal', fp, 'generalComment', [{'@xml:lang': 'en', '#text': '\n'.join([c1['#text'], comment['#text'], p1c['#text']+cvar1])}], 'Value'),
    (unc_triangular_1, 'triangular', fp, 'generalComment', [{'@xml:lang': 'en', '#text': '\n'.join([c1['#text'], comment['#text']])}], 'Value'),
    (unc_triangular_2, 'triangular', fp, 'generalComment', None, 'Value'),
    (unc_uniform, 'uniform', fp, 'generalComment', [{'@xml:lang': 'en', '#text': '\n'.join([c1['#text'], p1c['#text']])}], 'Value'),
    (unc_undefined, 'undefined', fp, 'generalComment', [{'@xml:lang': 'en', '#text': '\n'.join([c1['#text'], p1c['#text']])}], 'Value'),
    (unc_beta, 'beta', fp, 'generalComment', [{'@xml:lang': 'en', '#text': '\n'.join([c1['#text'], cbeta['#text']])}], 'Value'),
    (unc_gamma, 'gamma', fp, 'generalComment', [{'@xml:lang': 'en', '#text': '\n'.join([c1['#text'], p1c['#text'], cgamma['#text']])}], 'Value'),
    (unc_binomial, 'binomial', fp, 'generalComment', [{'@xml:lang': 'en', '#text': '\n'.join([c1['#text'], comment['#text'], p1c['#text'], cbinomial['#text']])}], 'Value')
    ])
def test_get_uncertainty(unc, name, field, comment, com_res, type_):
    field = field()
    r = ECS2ToILCD1UncertaintyConversion(unc)
    nc = ECS2ToILCD1DataNotConverted()
    factor = 1000
    
    if name == 'lognormal':
        amount = float(unc['lognormal']['@meanValue'])
        r._calculate(amount*factor, factor).get_uncertainty(field, comment, not_converted=nc, type_=type_)
        a = ot.LogNormal(math.log(abs(amount)),
                         math.sqrt(float(unc['lognormal']['@varianceWithPedigreeUncertainty'])))
        a = a * factor
        
        # This is to be able to calculate the geometric mean (gmu) and geometric std (gstd) from the mean and std of lognormal
        gmu = math.exp(math.log(a.getMean()[0]) - math.log((a.getStandardDeviation()[0])**2 / (a.getMean()[0])**2 + 1) / 2)
        gstd = a.computeBilateralConfidenceInterval(0.95).getUpperBound()[0] / gmu
        
        # This is a correction from 2 to 1.96 which is the true z-value for 95%
        gsd95 = ((gstd**(1/zn))**2)
        
        assert abs(field.get('minimum'+type_)) == pytest.approx(gmu / gsd95, 0.000001)
        assert abs(field.get('maximum'+type_)) == pytest.approx(gmu * gsd95, 0.000001)
        assert field.get('relativeStandardDeviation95In') == pytest.approx(gsd95, 0.000001)
        
    elif name == 'normal':
        amount = float(unc['normal']['@meanValue'])
        r._calculate(amount*factor, factor).get_uncertainty(field, comment, not_converted=nc, type_=type_)
        a = ot.Normal(amount,
                      math.sqrt(float(unc['normal']['@varianceWithPedigreeUncertainty'])))
        a = a * factor
        
        std = a.getMean()[0] - a.computeBilateralConfidenceInterval(0.95).getLowerBound()[0]
        
        # This is a correction from 2 to 1.96 which is the true z-value for 95%
        std95 = (std/zn)*2
        
        assert field.get('minimum'+type_) == pytest.approx(a.getMean()[0] - std95, 0.000001)
        assert field.get('maximum'+type_) == pytest.approx(a.getMean()[0] + std95, 0.000001)
        assert field.get('relativeStandardDeviation95In') == pytest.approx(std95, 0.000001)
    
    elif name == 'triangular':
        amount = float(unc['triangular']['@mostLikelyValue'])
        max_ = float(unc['triangular']['@maxValue'])
        diff = 0 if max_ >= amount else (amount-max_)*factor
        r._calculate(amount*factor, factor).get_uncertainty(field, comment, not_converted=nc, type_=type_)
        a = ot.Triangular(float(unc['triangular']['@minValue']),
                          amount,
                          max_ if max_ >= amount else amount)
        a = a * factor
        
        min_ = a.getRange().getLowerBound()[0]
        max_ = a.getRange().getUpperBound()[0]
        
        assert field.get('minimum'+type_) == pytest.approx(min_, 0.000001)
        assert field.get('maximum'+type_) == pytest.approx(max_-diff, 0.000001)
        
    elif name == 'uniform':
        amount = ( float(unc['uniform']['@minValue']) + float(unc['uniform']['@maxValue']) ) / 2
        r._calculate(amount*factor, factor).get_uncertainty(field, comment, not_converted=nc, type_=type_)
        a = ot.Uniform(float(unc['uniform']['@minValue']),
                       float(unc['uniform']['@maxValue']))
        a = a * factor
        
        min_ = a.getRange().getLowerBound()[0]
        max_ = a.getRange().getUpperBound()[0]
        
        assert field.get('minimum'+type_) == pytest.approx(min_, 0.000001)
        assert field.get('maximum'+type_) == pytest.approx(max_, 0.000001)
    
    elif name == 'undefined':
        amount = ( float(unc['undefined']['@minValue']) + float(unc['undefined']['@maxValue']) ) / 2
        r._calculate(amount*factor, factor).get_uncertainty(field, comment, not_converted=nc, type_=type_)
        
        std95 = factor * (float(unc['undefined']['@standardDeviation95']))
        min_ = amount*factor - std95
        max_ = amount*factor + std95
        
        assert field.get('minimum'+type_) == pytest.approx(min_, 0.000001)
        assert field.get('maximum'+type_) == pytest.approx(max_, 0.000001)
        assert field.get('relativeStandardDeviation95In') == pytest.approx(std95, 0.000001)
        
    else:
        amount = 1
        r._calculate(amount*factor, factor).get_uncertainty(field, comment, not_converted=nc, type_=type_)
        
    assert field.get(comment) == com_res
    
ECS2ToILCD1Amount.uncertainty_conversion = ECS2ToILCD1UncertaintyConversion
ECS2ToILCD1Amount.variable_conversion = ECS2ToILCD1VariableConversion

@pytest.mark.amount
@pytest.mark.parametrize('unit, result, amount, factor', [
    ('kg/MJ', 'second ** 2 / meter ** 2', 1e-06, 1e-06),
    ('kWh/kWp', 'day', 0.041666666666666664, 0.041666666666666664),
    ('m2/unit', 'meter ** 2 / item', 1.0, 1.0),
    ('g/mol', 'kilogram / mole', 0.001, 0.001),
    ('kg/hour', 'kilogram / second', 0.0002777777777777778, 0.0002777777777777778),
    ('s', 'day', 1.1574074074074072e-05, 1.1574074074074072e-05),
    ('m2/kg', 'meter ** 2 / kilogram', 1, 1.0),
    ('m*year', 'meter * year', 1, 1.0),
    ('point score', 'point_score', 1, 1.0),
    ('person*km', 'item * kilometer', 1, 1.0),
    ('USD(2011)', 'EUR2000', 0.5684684684684684, 0.5684684684684684),
    ('month', 'day', 30.4375, 30.4375),
    ('l/kg', 'meter ** 3 / kilogram', 0.0010000000000000002, 0.0010000000000000002),
    ('kBq', 'kilobecquerel', 1, 1.0),
    ('m2/m3', '1 / meter', 1, 1.0),
    ('kg/kg', 'dimensionless', 1, 1.0),
    ('d/year', 'dimensionless', 0.0027378507871321013, 0.0027378507871321013),
    ('kg TAN/kg TAN', 'dimensionless', 1, 1.0),
    ('kWp', 'kilogram * meter ** 2 / second ** 3', 1000.0, 1000.0),
    ('kW', 'kilogram * meter ** 2 / second ** 3', 1000.0, 1000.0),
    ('l', 'meter ** 3', 0.0010000000000000002, 0.0010000000000000002),
    ('m2', 'meter ** 2', 1, 1.0),
    ('metric ton*km', 'kilometer * metric_ton', 1, 1.0),
    ('km/hour', 'meter / second', 0.2777777777777778, 0.2777777777777778),
    ('unit/kWh', 'item * second ** 2 / kilogram / meter ** 2', 2.7777777777777776e-07, 2.7777777777777776e-07),
    ('kg NH3-N', 'kilogram', 1.0, 1.0),
    ('Eq', 'kilogram', 0.001, 0.001),
    ('kg P/ha.year', 'kilogram * second / meter ** 2', 3155.7599999999998, 3155.7599999999998),
    ('m3/kWh', 'meter * second ** 2 / kilogram', 2.7777777777777776e-07, 2.7777777777777776e-07),
    ('K', 'kelvin', 1, 1.0),
    ('kJ/kg', 'meter ** 2 / second ** 2', 1000.0, 1000.0),
    ('m3', 'meter ** 3', 1, 1.0),
    ('kg/m2', 'kilogram / meter ** 2', 1, 1.0),
    ('kg/l', 'kilogram / meter ** 3', 999.9999999999999, 999.9999999999999),
    ('l/(h.m2)', 'meter / second', 2.7777777777777787e-07, 2.7777777777777787e-07),
    ('MJ', 'megajoule', 1, 1.0),
    ('m2*year', 'meter ** 2 * year', 1, 1.0),
    ('metric ton/(ha*year)', 'kilogram / meter ** 2 / second', 3.168808781402895e-09, 3.168808781402895e-09),
    ('kg/m3', 'kilogram / meter ** 3', 1, 1.0),
    ('dimensionless', 'dimensionless', 1, 1.0),
    ('kg/kWh', 'second ** 2 / meter ** 2', 2.7777777777777776e-07, 2.7777777777777776e-07),
    ('kg/(m2*year)', 'kilogram / meter ** 2 / second', 3.168808781402895e-08, 3.168808781402895e-08),
    ('MJ/kcal', 'dimensionless', 239.0057361376673, 239.0057361376673),
    ('guest night', 'item', 1, 1.0),
    ('kg/hp*h', 'second ** 2 / meter ** 2', 3.7250613599861886e-07, 3.7250613599861886e-07),
    ('kWh/s', 'kilogram * meter ** 2 / second ** 3', 3600000.0, 3600000.0),
    ('TEU', 'meter ** 3', 38.5, 38.5),
    ('kg PO4/ha', 'kilogram / meter ** 2', 0.0001, 0.0001),
    ('hour', 'day', 0.041666666666666664, 0.041666666666666664),
    ('m2/(m3/d)^2', 'second ** 2 / meter ** 4', 7464960000, 7464960000.0),
    ('hour/year', 'dimensionless', 0.00011407711613050422, 0.00011407711613050422),
    ('kg N/ha', 'kilogram / meter ** 2', 0.0001, 0.0001),
    ('mm/year', 'meter / second', 3.168808781402895e-11, 3.168808781402895e-11),
    ('m3/ha/year', 'meter / second', 3.168808781402895e-12, 3.168808781402895e-12),
    ('hour/ha', 'second / meter ** 2', 0.36, 0.36),
    ('kg/(kg vehicle*km)', '1 / meter', 0.001, 0.001),
    ('kg/m', 'kilogram / meter', 1, 1.0),
    ('kg', 'kilogram', 1, 1.0),
    ('kg/kg vehicle', 'dimensionless', 1.0, 1.0),
    ('kg N2O-N/kg NO3-N', 'dimensionless', 1.0, 1.0),
    ('units/m²', 'item / meter ** 2', 1, 1.0),
    ('km', 'meter', 1000.0, 1000.0),
    ('metric ton*day', 'kilogram * year', 2.73785078713, 2.73785078713),
    ('unit/MJ', 'item * second ** 2 / kilogram / meter ** 2', 1.0000000000000002e-06, 1.0000000000000002e-06),
    ('EUR2005basic', 'EUR2000', 0.9009009009009008, 0.9009009009009008),
    ('day', 'day', 1, 1),
    ('kWh', 'megajoule', 3.6, 3.6),
    ('BTU/kg', 'meter ** 2 / second ** 2', 1055.056, 1055.056),
    ('kg/seedling', 'kilogram / item', 1.0, 1.0),
    ('m3/PMH', 'meter ** 3 / PMH', 1, 1.0),
    ('kg NO3-N/ha.year', 'kilogram * second / meter ** 2', 3155.7599999999998, 3155.7599999999998),
    ('l/m3', 'dimensionless', 0.0010000000000000002, 0.0010000000000000002),
    ('kg/ha', 'kilogram / meter ** 2', 0.0001, 0.0001),
    ('kWh/year', 'kilogram * meter ** 2 / second ** 3', 0.11407711613050422, 0.11407711613050422),
    ('m3/head/yr', 'meter ** 3 / item / second', 3.168808781402895e-08, 3.168808781402895e-08),
    ('MJ/kWh', 'dimensionless', 0.2777777777777778, 0.2777777777777778),
    ('kg/(m3/d)^2', 'kilogram * second ** 2 / meter ** 6', 7464960000, 7464960000.0),
    ('MJ/(m3/d)^2', 'kilogram / meter ** 4', 7464960000000000.0, 7464960000000000.0),
    ('hour/m3', 'second / meter ** 3', 3600, 3600.0),
    ('metric ton/ha', 'kilogram / meter ** 2', 0.1, 0.1),
    ('m', 'meter', 1, 1.0),
    ('ha', 'meter ** 2', 10000, 10000.0),
    ('kWh/km', 'kilogram * meter / second ** 2', 3600.0, 3600.0),
    ('MW', 'kilogram * meter ** 2 / second ** 3', 1000000.0, 1000000.0),
    ('kg/(head.d)', 'kilogram / item / second', 1.1574074074074072e-05, 1.1574074074074072e-05),
    ('km*year', 'meter * year', 1000.0, 1000.0),
    ('kcal/kWh', 'dimensionless', 0.0011622222222222223, 0.0011622222222222223),
    ('m3/d', 'meter ** 3 / second', 1.1574074074074072e-05, 1.1574074074074072e-05),
    ('year', 'day', 365.25, 365.25),
    ('MJ/m3', 'kilogram / meter / second ** 2', 1000000.0, 1000000.0),
    ('kW/TEU', 'kilogram / meter / second ** 3', 25.974025974025977, 25.974025974025977),
    ('kg/s', 'kilogram / second', 1, 1.0),
    ('mm', 'meter', 0.001, 0.001),
    ('m3/(m3/d)^2', 'second ** 2 / meter ** 3', 7464960000, 7464960000.0),
    ('MJ/Nm3', 'kilogram ** 4 / meter / second ** 2', 0.001, 0.001),
    ('kcal', 'megajoule', 0.004184, 0.004184),
    ('MJ/kg', 'meter ** 2 / second ** 2', 1000000.0, 1000000.0),
    ('t*h/(MJ*mm)', 'second ** 3 / meter ** 3', 3600.0, 3600.0),
    ('t/day', 'kilogram / second', 0.011574074074074073, 0.011574074074074073),
    ('unit', 'item', 1, 1.0),
    ('unit/ha', 'item / meter ** 2', 0.0001, 0.0001),
    ('CHF2011', 'EUR2000', 0.672072072072072, 0.672072072072072),
    ('kg NOx/kg N2O', 'dimensionless', 1.0, 1.0),
    ('kg N2O-N/kg NH3-N', 'dimensionless', 1.0, 1.0),
    ('m2*K/W', 'kelvin * second ** 3 / kilogram', 1.0, 1.0),
    ('kg*day', 'kilogram * year', 0.00273785078, 0.00273785078),
    ('m2/year', 'meter ** 2 / second', 3.168808781402895e-08, 3.168808781402895e-08),
    ('kg/GJ', 'second ** 2 / meter ** 2', 1.0000000000000003e-09, 1.0000000000000003e-09),
    ('kg P2O5/ha', 'kilogram / meter ** 2', 0.0001, 0.0001),
    ('kg/unit', 'kilogram / item', 1.0, 1.0),
    ('% (obsolete)', 'fraction', 0.01, 0.01),
    ('PMH/m3', 'PMH / meter ** 3', 1, 1.0),
    ('l/m2', 'meter', 0.0010000000000000002, 0.0010000000000000002),
    ('EUR2005', 'EUR2000', 0.9009009009009008, 0.9009009009009008),
    ('OLD_MJ/kg', 'meter ** 2 / second ** 2', 1000000.0, 1000000.0),
    ('m3*year', 'meter ** 3 * year', 1, 1.0),
    ('m3/kg', 'meter ** 3 / kilogram', 1, 1.0),
    ('l/hour', 'meter ** 3 / second', 2.7777777777777787e-07, 2.7777777777777787e-07),
    ('kg/ha.yr', 'kilogram * second / meter ** 2', 3155.76, 3155.76),
    ('MJ*mm/(ha*h*yr)', 'kilogram * meter / second ** 4', 8.802246615008041e-13, 8.802246615008041e-13),
    ('kg/year', 'kilogram / second', 3.168808781402895e-08, 3.168808781402895e-08),
    ('m2/ha', 'dimensionless', 0.0001, 0.0001),
    ('kg N2O-N/kg N', 'dimensionless', 1.0, 1.0),
    ('m³/ha', 'meter', 0.0001, 0.0001),
    ])
def test_ECS2_to_ILCD_amount(unit, result, amount, factor):
    qtt = 3
    r = ECS2ToILCD1Amount(qtt, unit, unc_lognormal_1, (None, None), 'test')
    assert str(r.u) == result
    assert r.m == pytest.approx(amount * qtt)
    assert r.f == pytest.approx(factor)
    
    r = ECS2ToILCD1Amount(qtt, unit, unc_lognormal_1, (None, None), 'test', no_conversion_to_ilcd_unit=True)
    assert r.u == up.Quantity(1, ECS2ToILCD1Amount.unit_name_correction(unit)).u
    assert r.m == pytest.approx(qtt)
    assert r.f == 1
    
    qtt = 0
    r = ECS2ToILCD1Amount(qtt, unit, unc_lognormal_1, (None, None), 'test')
    assert str(r.u) == result
    assert r.m == pytest.approx(amount * qtt)
    assert r.f == pytest.approx(factor)

@pytest.mark.amount
@pytest.mark.uncertainty
@pytest.mark.parametrize('unit1, unc1, unit2, unc2', [
    ('kg PO4/ha', unc_lognormal_1, 'm2', unc_lognormal_1),
    ('kg PO4/ha', unc_normal, 'm2', unc_normal),
    ('kg PO4/ha', unc_lognormal_1, 'm2', unc_normal),
    ])
def test_unc_multiplication_and_division(unit1, unc1, unit2, unc2):
    r0 = ECS2ToILCD1Amount(1, unit1, unc1, (None, None), 'test')
    r2 = ECS2ToILCD1Amount(1, unit2, unc2, (None, None), 'test')
    
    r1 = ECS2ToILCD1Amount(1, unit1, unc1, (None, None), 'test')
    r1.multiply(r2)
    if unc1.get('lognormal') and unc2.get('lognormal'):
        a = ot.LogNormal(math.log(abs(r0.m)), math.sqrt(r0._unc._var))
        b = ot.LogNormal(math.log(abs(r2.m)), math.sqrt(r2._unc._var))
        c = a * b
        assert r1._unc._var == c.getParametersCollection()[0][1] ** 2
    else:
        assert not hasattr(r1, '_unc')
    assert r1.f == r0.f * r2.m
    assert r1.m == r0.m * r2.m
    assert r1.u == r0.u * r2.u

    r1 = ECS2ToILCD1Amount(1, unit1, unc1, (None, None), 'test')
    r1.divide(r2)
    if unc1.get('lognormal') and unc2.get('lognormal'):
        a = ot.LogNormal(math.log(abs(r0.m)), math.sqrt(r0._unc._var))
        b = ot.LogNormal(math.log(abs(r2.m)), math.sqrt(r2._unc._var))
        c = a / b
        assert r1._unc._var == c.getParametersCollection()[0][1] ** 2
    else:
        assert not hasattr(r1, '_unc')
    assert r1.f == r0.f / r2.m
    assert r1.m == r0.m / r2.m
    assert r1.u == r0.u / r2.u

ECS2ToILCD1Amount.add_flow_data({'d1488bd2-9cb5-44ff-b2f1-c71d4bcc69f7': (10, 100)})
ECS2ToILCD1VariableConversion.Formula.amountClass = ECS2ToILCD1Amount
amount = 3

math0 = "UnitConversion(4889, 'kilocalorie thermochemical', 'MJ')"
mathr0 = "(4889.0*__kilocalorie_thermochemical_to_MJ__)"
math1 = "10*40/200 + 10-2"
mathr1 = math1
math2 = "APV_RP* Ref('d1488bd2-9cb5-44ff-b2f1-c71d4bcc69f7')* Ref('d1488bd2-9cb5-44ff-b2f1-c71d4bcc69f7', 'ProductionVolume')"
mathr2 = "APV_RP* 10* 100"
math3 = "8358976000 * 5.60% * (1 - 10%) / 0.5"
mathr3 = "8358976000 * 5.60/ 100 * (1 - 10/ 100) / 0.5"
math4 = '1,45e-6*cement'
mathr4 = '1.45e-6*cement'

uv1 = '__kilocalorie_thermochemical_to_MJ__'
uv1v = 0.004184
uv2 = '__kg_PO4_per_ha_to_kg_per_m2__'
uv2v = 0.0001

com1 = [{'#text': '\nConversion from kilocalorie_thermochemical to MJ for UnitConversion formulas',
        '@xml:lang': 'en'}]
com2 = [{'#text': "\nConversion from kg_PO4_per_ha to kg_per_m2",
        '@xml:lang': 'en'}]
com = lambda u, n='\nsome regular comment': [{'#text': '['+u+']'+n+'\nUncertainty Comment:\nsome important comment that is here\nPedigree: (4,3,1,3,4); Basic Variance: 0.0006',
                 '@xml:lang': 'en'}]

unit_ = ('kg', 'kg PO4/ha')

nv = 'name_of_variable'

import re
@pytest.mark.amount
@pytest.mark.variable
@pytest.mark.parametrize('unit, type_, varname, varres, res, mathrel, mathres, unc, comment', [
    *[(u, 'test', vn, [vn], [amount], *n, [com(u.replace(' ','_').replace('/','_per_'))]) for u in unit_ for vn in (nv, None) for n in [
        (math1, [mathr1], unc_lognormal_1),
        (math2, [mathr2], unc_lognormal_1),
        (math3, [mathr3], unc_lognormal_1),
        (math4, [mathr4], unc_lognormal_1),
        (None, [None], unc_lognormal_1)]
    ],
    
    *[(u, 'test', vn[1], vn, [amount, uv1v],
        math0, [mathr0, None],
        unc_lognormal_1,
        [com(u.replace(' ','_').replace('/','_per_')), com1]) for u in unit_ for vn in ([nv, uv1],
                                                                                        [None, uv1])
    ],
    
    ('kg PO4/ha', 'flow', nv,
      [nv, nv+'__uc', uv2],
      [amount, amount*uv2v, uv2v], math1,
      [mathr1, "("+mathr1+")*"+uv2, None], 
      unc_lognormal_1, 
      [com('kg_PO4_per_ha',n=''), com('kg_per_m2'), com2]),
    ('kg PO4/ha', 'flow', None,
     ['Eq_fl_99__from'+uv2[1:], uv2],
      [amount*uv2v, uv2v], math2,
      ["("+mathr2+")*"+uv2, None], 
      unc_lognormal_1, 
      [com('kg_per_m2'), com2]),
    ('kg PO4/ha', 'flow', nv,
      [uv1, nv, nv+'__uc', uv2],
      [uv1v, amount, amount*uv2v, uv2v], math0,
      [None, mathr0, "("+mathr0+")*"+uv2, None],
      unc_lognormal_1,
      [com1, com('kg_PO4_per_ha',n=''), com('kg_per_m2'), com2]),
    ('kg PO4/ha', 'flow', None,
      [uv1, 'Eq_fl_99__from'+uv2[1:], uv2],
      [uv1v, amount*uv2v, uv2v], math0,
      [None, "("+mathr0+")*"+uv2, None],
      unc_lognormal_1,
      [com1, com('kg_per_m2'), com2]),
    ('kg PO4/ha', 'flow', None,
      [None, uv2],
      [amount*uv2v, uv2v], None,
      [str(amount)+'*'+uv2, None],
      unc_lognormal_1,
      [com('kg_per_m2'), com2]),
    
    ])
def test_variable(unit, type_, varname, varres, res, mathrel, mathres, unc, comment):
    
    s = ILCD1Structure()
    ECS2ToILCD1Amount.variable_holder= s.mathematicalRelations
    
    amount = 3
    
    r = ECS2ToILCD1Amount(amount, unit, unc, (varname, mathrel, [{'@index': 10, '@lang': 'en', '#text': 'some regular comment'}]), type_)
    
    assert r._var._name == varname if varname else 'Eq_'+type_+'_'+uuid.replace('-', '_')
    if hasattr(r, '_var'):
        assert r._var._math == mathrel
    
    r.construct_variable()
    v_par = s.mathematicalRelations.get('variableParameter', [])
        
    for i, v in enumerate(v_par):
        if not varres[i]:
            varres[i] = 'Eq_'+type_[:2]+'_99'
            if not mathrel:
                varres[i] = 'Eq_uv_99'
        assert re.sub(r'(Eq_[a-z]+_)[0-9]+', r'\1', v.get('a_name')) in [re.sub(r'(Eq_[a-z]+_)[0-9]+', r'\1', i) for i in varres]
        if mathrel:
            assert v.get('formula') in mathres
        assert v.get('meanValue') in res
        # assert v.get('comment') in comment

units_of_parameters = {
    'g/mol',
    'kg/ha',
    'dimensionless',
    'kg N2O-N/kg N',
    'kg/hp*h',
    'kg/(m3/d)^2',
    'kg',
    'm3/kWh',
    'kg/kg',
    'hour/ha',
    'ha',
    'kg/MJ',
    'unit',
    'kWh',
    'kg/m3',
    'm3',
    'kg/(head.d)',
    'm2',
    'kg NOx/kg N2O',
    'mm',
    'l/kg',
    'm2/unit',
    'year',
    'm2/(m3/d)^2',
    'MJ/kg',
    'kg/ha.yr',
    'MJ',
    'kg/kg vehicle',
    'm2/year',
    'm2/kg',
    'kg/m',
    'kW',
    'kg/hour',
    'metric ton/ha',
    'm3/kg',
    'PMH/m3',
    'kg/kWh',
    'kg/unit',
    '% (obsolete)',
    'kg N2O-N/kg NO3-N',
    'kW/TEU',
    'kg/l',
    'kWh/km',
    'm',
    'kg/m2',
    'kg N/ha',
    'm³/ha',
    'kg N2O-N/kg NH3-N',
    'unit/kWh',
    'l',
    'km',
    'kg/(m2*year)',
    'm3/ha/year',
    'km/hour',
    'm3/head/yr',
    'l/m2',
    'MJ/kWh',
    'units/m²',
    'MJ/kcal',
    'm3/PMH',
    'hour/year',
    'm2/m3',
    'metric ton/(ha*year)',
    'kg P2O5/ha',
    'day',
    'hour/m3',
    'kg/year',
    'm3/d',
    'kg NO3-N/ha.year',
    't*h/(MJ*mm)',
    'mm/year',
    'MW',
    'm3/(m3/d)^2',
    'l/hour',
    'kg P/ha.year',
    'kg/(kg vehicle*km)',
    'month',
    'kWh/kWp',
    'd/year',
    'MJ/(m3/d)^2',
    'kWh/year',
    'USD(2011)',
    'hour',
    'MJ/m3',
    'l/m3',
    'kg PO4/ha',
    'MJ*mm/(ha*h*yr)',
    'm2/ha',
    'kcal',
    'BTU/kg',
    'kg TAN/kg TAN',
    't/day',
    'unit/ha',
    'kcal/kWh',
    'unit/MJ',
    'kg NH3-N',
    'kJ/kg',
    'kg/seedling',
    'l/(h.m2)',
    }

parameter = {
    'name': {'@lang': 'en', '#text': 'some_parameter_name'},
    'unitName': {'@lang': 'en', '#text': 'unit/ha'},
    'uncertainty': unc_lognormal_1,
    'comment': {'@index': 1} | comment,
    '@parameterId': uuid,
    "@parameterContextId": uuid[:-1] + 'f',
    "@variableName": 'variable_name', # optional
    "@mathematicalRelation": "444*10",
    "@isCalculatedAmount": "true",
    "@amount": 10.0,
    "@unitId": uuid[:-2] + 'a3',
    "@unitContextId": uuid[:-3] + 'fae'
    }

general_parameter = lambda x: {
    'name': {'@lang': 'en', '#text': 'general_parameter'},
    'unitName': {'@lang': 'en', '#text': x},
    'uncertainty': unc_lognormal_1,
    'comment': {'@index': 1} | comment,
    '@parameterId': uuid,
    "@variableName": 'variable_name_for_general', # optional
    "@amount": 10.0,
    "@unitId": uuid[:-2] + 'a3',
    }

# list of names, list of unitNames
parameter2 = {
    'name': [{'@lang': 'en', '#text': 'some_parameter_name'}, {'@lang': 'en', '#text': 'some_other_parameter_name'}],
    'unitName': [{'@lang': 'en', '#text': 'kg/seedling'}, {'@lang': 'en', '#text': 'kJ/kg'}],
    'comment': [{'@index': 1} | comment, {'@index': 1} | comment2],
    "@mathematicalRelation": "444*10",
    '@parameterId': uuid,
    "@amount": 10.0
    }

# No unit name
parameter3 = parameter2.copy()
del parameter3['unitName']
del parameter3['@mathematicalRelation']
del parameter3['comment']

@pytest.mark.parameter
@pytest.mark.parametrize('par, unit_res, name_res', [
    (parameter, (['unit/ha'], uuid[:-2] + 'a3'), 'variable_name'),
    (parameter2, (['kg/seedling', 'kJ/kg'], None), 'Eq_pa_1'),
    (parameter3, ([], None), None),
    *((general_parameter(x), ([x], uuid[:-2] + 'a3'), 'variable_name_for_general_'+str(i)) for i, x in enumerate(units_of_parameters))])
def test_parameter(par, unit_res, name_res):
    s = ILCD1Structure()
    ECS2ToILCD1Amount.variable_holder = s.mathematicalRelations
    ECS2ToILCD1Amount.variable_conversion = ECS2ToILCD1VariableConversion
    ECS2ToILCD1Amount._equation_counter = 1
    ECS2ToILCD1ParameterConversion.amountClass = ECS2ToILCD1Amount
    
    r = ECS2ToILCD1ParameterConversion(par, ECS2ToILCD1DataNotConverted)
    
    assert r.units == unit_res
    
    r.amount.construct_variable()
    
    v_ = s.mathematicalRelations.get('variableParameter', [])
    if name_res:
        if len(v_) == 1:
            v = v_[0]
            assert v.get('a_name') in name_res
            if par.get('@mathematicalRelation'):
                assert v.get('formula') == '444*10'
            assert v.get('meanValue') == 10.0*r.amount.f
            if v.get('comment'):
                unit = f"{r.amount.u:~}".replace(" ", "").replace("/", "_per_").replace("**", "").replace("*", "_times_").replace(".", "_")
                assert re.match(r'\['+unit+r'\]', v.get('comment')[0]['#text'])
                assert 'some important comment that is here' in v.get('comment')[0]['#text']
    else:
        assert len(v_) == 0

property_info = [
    ('cc822f1f-6251-4250-b2be-21fa2f03eef6','amount 1 of flow in kg','kg',''),
    ('83d7ec8e-268c-4b90-b0d5-24d42c802e68','EcoSpold01Allocation_other_78','','other allocation 78 used in EcoSpold01 datasets'),
    ('abc78955-bd5f-4b1a-9607-0448dd75ebf2','mass concentration, titanium','kg/m3','Mass concentration of Titanium.    (CAS 007440-32-6)'),
    ('d22b84cd-c54a-412d-b852-aa2c90ab876b','EcoSpold01Allocation_undefined_28','','undefined allocation 28 used in EcoSpold01 datasets'),
    ('271062b1-ed7c-4874-839c-c1ae0f664c86','molding efficiency','dimensionless','1 kg of this process equals 0.994 kg of injection moulded plastics.'),
    ('7c33fa83-dbc9-43c3-85c2-a5bdb058c37d','ash content','kg',''),
    ('ebe8ff0d-a0b5-44d0-b437-4ef85a2a6284','EcoSpold01Allocation_undefined_153','','undefined allocation 153 used in EcoSpold01 datasets'),
    ('56f09738-8225-4bdc-91d2-39ee6328f0ee','silver content','dimensionless','silver content on a dry matter basis'),
    ('e38c9209-6934-4445-b180-675bcbd5ad7a','concentration, potassium','kg/kg','potassium content on a fresh matter basis'),
    ('86fe199e-c71b-4600-97ba-dc3b76f9a1f0','UVEK_absolute_amount_1','dimensionless',''),
    ('6393c14b-db78-445d-a47b-c0cb866a1b25','carbon content, non-fossil','dimensionless','biogene carbon content on a dry matter basis'),
    ('608190bf-8f74-4f8e-8544-f25377accf4d','thallium content','dimensionless','thallium content on a dry matter basis'),
    ('8930f8b6-1c5b-4fe8-926a-93ded8daa1a6','EcoSpold01Allocation_undefined_72','','undefined allocation 72 used in EcoSpold01 datasets'),
    ('92b141b7-4672-42e8-8dad-501879d7fac3','concentration of amount 5','dimensionless',''),
    ('a5e4ea62-2953-4633-9572-f8a2cd5c4616','EcoSpold01Allocation_other_101','','other allocation 101 used in EcoSpold01 datasets'),
    ('a2047b68-9196-4f4f-8192-99f79898fa47','EcoSpold01Allocation_undefined_169','','undefined allocation 169 used in EcoSpold01 datasets'),
    ('01e07f2d-bdf2-4331-b944-f58f4e337ff5','EcoSpold01Allocation_other_51','','other allocation 51 used in EcoSpold01 datasets'),
    ('e5336a01-901a-47f6-ab7e-7e94cf0963db','EcoSpold01Allocation_undefined_32','','undefined allocation 32 used in EcoSpold01 datasets'),
    ('9b811dd0-7ba9-49a5-b70e-b28f7220dfe4','EcoSpold01Allocation_undefined_105','','undefined allocation 105 used in EcoSpold01 datasets'),
    ('c8ebc911-268a-4dfe-a426-73e1e35b587a','mass concentration, dissolved nitrite NO2 as N','kg/m3','Mass concentration of dissolved nitrite NO2 (CAS 014797-65-0) as N. Note that dissolved and particulate N are optional yet desirable specifications of total nitrogen.'),
    ('beb07321-4679-4806-9466-0ff808375075','EcoSpold01Allocation_physical_1','','physical allocation 1 used in EcoSpold01 datasets'),
    ('16f50929-1dac-435a-b86e-81ceb7684424','alloy additives','kg',''),
    ('9909d836-d0a3-45ed-a8d6-62f5febc763e','EcoSpold01Allocation_undefined_21','','undefined allocation 21 used in EcoSpold01 datasets'),
    ('e70c55d1-b081-484b-9e7b-0e4743d6f8d4','EcoSpold01Allocation_other_16','','other allocation 16 used in EcoSpold01 datasets'),
    ('98df467a-bc03-4056-abea-cbc3ac1a44ba','nitrogen oxides emissions tier T2 for hp < 175','kg/hp*h',''),
    ('8b574e85-ff07-46bf-a753-f1271299dcf7','mass concentration, nickel','kg/m3','Mass concentration of Nickel.    (CAS 007440-02-0)'),
    ('16bd8b23-46d6-442a-8822-b8475dedb616','EcoSpold01Allocation_other_124','','other allocation 124 used in EcoSpold01 datasets'),
    ('8daf1327-bd94-4903-8e7b-5fe7731a259b','radium content','dimensionless','radium content on a dry matter basis'),
    ('b838627a-7ccc-469e-9954-a126ca812316','EcoSpold01Allocation_other_86','','other allocation 86 used in EcoSpold01 datasets'),
    ('ffcba73f-cd14-4beb-8932-600894c9d56d','carbon monoxide emissions tier T0 for hp < 100','kg/hp*h',''),
    ('3be25089-59c3-4f04-a5f6-9a50bf2e9e61','nitrogen oxides emissions tier T3B-T4-T4A for hp < 100','kg/hp*h',''),
    ('42d12e16-78e4-4baf-8604-50c3aff19cdb','EcoSpold01Allocation_other_102','','other allocation 102 used in EcoSpold01 datasets'),
    ('964f8b50-ce16-4364-835a-a3db5fb760b0','lifetime','year',''),
    ('f3e31d48-0d60-4189-b967-fcda256ac8ba','nitrogen oxides emissions tier T4A-T4B for hp < 11','kg/hp*h',''),
    ('ed0f7fbe-11a4-4abd-916c-d6f5d73e8558','EcoSpold01Allocation_other_106','','other allocation 106 used in EcoSpold01 datasets'),
    ('d01683bd-aa77-46d1-85f8-23d429e022ee','EcoSpold01Allocation_other_115','','other allocation 115 used in EcoSpold01 datasets'),
    ('7f3410da-b91e-40d8-9545-ab269ff66900','mass concentration, sulfur','kg/m3','Mass concentration of sulfur as S (Stot.). (CAS 007704-34-9)'),
    ('af807f71-eafe-407e-95dd-7364e40e6684','nitrogen oxides emissions tier T1 for hp < 300','kg/hp*h',''),
    ('0d342ebd-54f8-46fb-b3c0-24b20efb158a','SAM_activityLink_9','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('999af43a-1a83-4231-ba3c-600b1941b3a0','palladium content','dimensionless','palladium content on a dry matter basis'),
    ('d95d853b-53a9-43e5-9c12-acc4a4ae6c7f','EcoSpold01Allocation_other_36','','other allocation 36 used in EcoSpold01 datasets'),
    ('df4806ae-ba84-4d5a-b809-2fa81c31e120','carbon monoxide emissions tier T0-T1 for hp < 50','kg/hp*h',''),
    ('b6dc8a47-8e61-4a71-b39d-dd3bcb970bbe','fat (total lipid) content','kg',''),
    ('84e59b0f-ecb6-4dac-b8d6-be1cf2b1d184','EcoSpold01Allocation_undefined_91','','undefined allocation 91 used in EcoSpold01 datasets'),
    ('fcc233d5-ea53-4b90-9e2c-5624032a4b95','concentration, magnesium','kg/kg','magnesium content on a fresh matter basis'),
    ('fb2ccf7c-73c6-4d43-a3c7-26fda1423f18','neon content','dimensionless','neon content on a dry matter basis'),
    ('98549452-463c-463d-abee-a95c2e01ade3','mass concentration, Kjeldahl Nitrogen as N','kg/m3','Mass concentration of total Kjeldahl (TKN) as N. Note that dissolved Kjeldahl Nitrogen is an optional yet desirable specification of total Kjeldahl Nitrogen. '),
    ('52b3af22-c508-4ad1-9d65-bd96ac52879e','fuel input in physical units, m3','m3',''),
    ('aaedfd5e-a9ce-4257-a015-93ef483fed8c','krypton content','dimensionless','krypton content on a dry matter basis'),
    ('77154d2e-4b05-48f2-a89a-789acd170497','mass concentration, aluminium','kg/m3','Mass concentration of Aluminium.    (CAS 007429-90-5)'),
    ('ada3f057-a72c-4580-b8e9-d957f30a813e','EcoSpold01Allocation_undefined_62','','undefined allocation 62 used in EcoSpold01 datasets'),
    ('b30a42e9-9e08-4294-94af-a3e0b23b03df','MARKET_OVERWRITE_AMOUNT_APOS','dimensionless','Defines the new amount of its exchange to be used in linking of the market for the APOS system model.'),
    ('33f96fe7-39da-47ca-837f-f2c311681d1b','zinc content','dimensionless','zinc content on a dry matter basis'),
    ('995afb89-8462-47bb-ae20-d7bd256259aa','EcoSpold01Allocation_other_85','','other allocation 85 used in EcoSpold01 datasets'),
    ('7027204d-5781-4ae1-9a40-271b808304eb','EcoSpold01Allocation_other_79','','other allocation 79 used in EcoSpold01 datasets'),
    ('fddd8dce-2ea3-4b65-8073-8b6aae6debe6','amount of non-specified waste to recycling','kg',''),
    ('4e0d51e1-8833-45e8-bd22-48292c8c93b8','mass concentration, krypton','kg/m3','Mass concentration of Krypton.    '),
    ('518585a8-3e59-43b9-b10a-162e44893921','lower heating value','MJ/Nm3','Net calorific value'),
    ('c3a9f78c-10b3-4889-9436-1ce2c2433372','EcoSpold01Allocation_undefined_49','','undefined allocation 49 used in EcoSpold01 datasets'),
    ('7404741f-fbd3-44a7-8c47-d9b236765428','non-process water, net','kg',''),
    ('296d723d-06e7-4bb1-9eec-dacf8375cc7b','nitrogen oxides emissions tier T4A-T4B for hp < 25','kg/hp*h',''),
    ('3a0030f4-0585-487f-84fb-c6f3fa283ade','mass concentration, tellurium','kg/m3','Mass concentration of Tellurium.    (CAS 013494-80-9)'),
    ('837d4c36-313c-4a5b-9953-bc1a6bd83d9c','EcoSpold01Allocation_other_139','','other allocation 139 used in EcoSpold01 datasets'),
    ('38b5d17a-5214-49d0-b0a6-af65118ae2e1','amount of non-specified waste to landfill','kg',''),
    ('44454aa6-3e54-4bb3-850c-9011a7257985','ruthenium content','dimensionless','ruthenium content on a dry matter basis'),
    ('a676fa01-ee71-4fb4-95e0-4a8ed308d356','amount of flow 4 in kg','kg',''),
    ('1222c4b8-3edb-4792-8538-ae5d5b4cbca2','EcoSpold01Allocation_undefined_108','','undefined allocation 108 used in EcoSpold01 datasets'),
    ('286bd819-5722-41b7-b4a2-cff94e76d4bf','EcoSpold01Allocation_other_105','','other allocation 105 used in EcoSpold01 datasets'),
    ('e2bffe98-8294-411e-9620-8be8ce95b65d','EcoSpold01Allocation_undefined_48','','undefined allocation 48 used in EcoSpold01 datasets'),
    ('8547e7fb-7bd9-4116-8b53-6bb6eb00375a','height, external','m',''),
    ('ae7467f9-7161-4cd1-91dd-0bc49ccef2e7','EcoSpold01Allocation_other_11','','other allocation 11 used in EcoSpold01 datasets'),
    ('303a1005-707a-45b4-b187-2f70145f2d9b','EcoSpold01Allocation_undefined_33','','undefined allocation 33 used in EcoSpold01 datasets'),
    ('8c823f28-a3c7-4970-80a3-2b830850a1d7','steel, fraction','',''),
    ('831cecb4-2de9-46fd-bbc5-22661e104beb','apparent wood density','kg/m3','wet mass/wet volume'),
    ('30f65a30-89d1-457b-a28a-63692feea6b4','EcoSpold01Allocation_undefined_73','','undefined allocation 73 used in EcoSpold01 datasets'),
    ('26ec2bdf-c4d7-4ed4-a751-5cfa97d2b26b','concentration, silver','kg/kg',''),
    ('0ac1017b-737e-4e10-9383-5419c65c16c7','carbon monoxide emissions tier T4A for hp < 50','kg/hp*h',''),
    ('b38d886d-3026-4a27-9b33-e661022dcf9b','literFuel_Input','l',''),
    ('79baac3d-9e62-45ef-8f41-440dea32f11f','mass concentration, thallium','kg/m3','Mass concentration of Thallium.    (CAS 007440-28-0)'),
    ('71a8b07c-84fb-4dea-a045-7a0950b7e95b','EcoSpold01Allocation_undefined_74','','undefined allocation 74 used in EcoSpold01 datasets'),
    ('1a3f7490-7944-4d5a-ae87-4133cd0f6eec','mass concentration, osmium','kg/m3','Mass concentration of Osmium.    (CAS 007440-04-2)'),
    ('560016f5-5d3b-4793-8e81-deb16d910180','EcoSpold01Allocation_other_52','','other allocation 52 used in EcoSpold01 datasets'),
    ('4594279a-e4ee-4e40-8dcd-48c8cdea1d94','EcoSpold01Allocation_undefined_112','','undefined allocation 112 used in EcoSpold01 datasets'),
    ('606b5765-2832-4924-a08e-c782f713047e','EcoSpold01Allocation_other_127','','other allocation 127 used in EcoSpold01 datasets'),
    ('41a012c8-bcde-4563-9ba1-a7ca1823d4b7','basic density','kg/m3',''),
    ('114d7baf-042e-43b3-9838-f92d4ddb4e69','EcoSpold01Allocation_other_74','','other allocation 74 used in EcoSpold01 datasets'),
    ('e83fa8a9-116e-40a0-a71b-8f31b26c2372','landfilled waste carbon','kg',''),
    ('fff34673-274f-485e-ae6a-d28781ad6e64','nitrogen oxides emissions tier T1 for hp < 100','kg/hp*h',''),
    ('23685f2b-904d-4f25-b53d-1e3d2cece12f','EcoSpold01Allocation_other_64','','other allocation 64 used in EcoSpold01 datasets'),
    ('d1af2cd4-c9d5-4c3a-af33-3d64deb37404','EcoSpold01Allocation_undefined_68','','undefined allocation 68 used in EcoSpold01 datasets'),
    ('25adf84a-588d-4014-bdac-cc6cc8ff294b','concentration of amount 3','dimensionless',''),
    ('bd750b75-af57-4583-919c-446baf1985f3','amount of exchange in kg 1','kg',''),
    ('4e7fc39f-34be-4e0b-8d2f-ae1d243cc800','fuel input, fraction','',''),
    ('4bae13cf-c514-4c36-b8be-672c815b4968','gas density','kg/l',''),
    ('81209399-cd11-422e-aa4d-d66acb4fa344','EcoSpold01Allocation_other_130','','other allocation 130 used in EcoSpold01 datasets'),
    ('a99e0167-8ba1-4768-8ffa-583416ad9f06','nitrogen oxides emissions tier T2 for hp < 300','kg/hp*h',''),
    ('2dd01d14-3b27-4a66-9308-2ab96e6bcbd0','mass concentration, zirconium','kg/m3','Mass concentration of Zirconium.    (CAS 007440-67-7)'),
    ('db0b4bbf-fd26-4ba2-b9de-0fd47476304f','lithium content','dimensionless','lithium content on a dry matter basis'),
    ('24ce2b3e-69c4-4578-852e-580473fb5953','yearly_distributed_amount','kg','Amount distributed per year, in kg'),
    ('ff8ff2b1-54a1-4336-807e-89b2981eb47a','utilization rate','dimensionless','The utilization rate represents a fraction of a lifetime of infrastructure, when the infrastructure is actually being used.'),
    ('e8e47ce2-af93-4f3e-99d2-1279f86f6d2c','EcoSpold01Allocation_undefined_95','','undefined allocation 95 used in EcoSpold01 datasets'),
    ('832bb926-0c7d-4b16-bf36-fc69665afe8b','platinum content','dimensionless','platinum content on a dry matter basis'),
    ('e9fa11a1-1011-421d-aa34-0544d767a632','titanium content','dimensionless','titanium content on a dry matter basis'),
    ('615315e1-6e9f-4ec8-ac46-d0c79b2dd640','EcoSpold01Allocation_other_117','','other allocation 117 used in EcoSpold01 datasets'),
    ('aae1dcfc-a4bd-4429-9446-8f99693fe9c5','EcoSpold01Allocation_undefined_148','','undefined allocation 148 used in EcoSpold01 datasets'),
    ('d856e58f-4fbb-4f18-97d0-eb44f7b5ed3f','heat of fuel used','MJ',''),
    ('ee301bc4-052a-40c2-a5d7-76fa6e429aa5','gold content','dimensionless','gold content on a dry matter basis'),
    ('eb730caf-f394-4e43-842d-bd85cef5f07d','EcoSpold01Allocation_physical_12','','physical allocation 12 used in EcoSpold01 datasets'),
    ('28841901-be10-4b4c-b077-228b4de6e7b1','mass concentration, xenon','kg/m3','Mass concentration of Xenon.    '),
    ('c092b78a-b16f-42e7-b27f-202a1059d47e','EcoSpold01Allocation_other_14','','other allocation 14 used in EcoSpold01 datasets'),
    ('2520c12c-a34f-40e5-ac7d-37a325d01311','basic wood density','','dry mass/wet volume'),
    ('1325d7f9-2fe2-4226-9304-ad9e5371e08f','mass concentration, scandium','kg/m3','Mass concentration of Scandium.    (CAS 007440-20-2)'),
    ('f576f1a0-d669-4063-9309-82c4af778bb4','gadolinium content','dimensionless','gadolinium content on a dry matter basis'),
    ('6d915647-22db-4999-a42d-afccf5bb4268','dross sent to landfill','kg',''),
    ('14ceb4c6-213a-4f9e-a591-ee22648fa6e4','amount from wellenstoff production in kg','kg',''),
    ('763a698f-54d7-4e2a-84a7-9cc8c0271b6a','mass concentration, fluorine','kg/m3','Mass concentration of Fluorine.    (CAS 007782-41-4)'),
    ('044617f2-c1d4-4592-94c6-bb325139e231','Organic Carbon content of soil','dimensionless','Organic Carbon content [-] of soil'),
    ('5b28943d-ebbc-4af9-8b6a-9b7eafc9bede','amount of exchange 3','kg',''),
    ('326f28c6-5976-4ae4-8a26-64fa1d3f6cad','EcoSpold01Allocation_undefined_109','','undefined allocation 109 used in EcoSpold01 datasets'),
    ('6f0a8b10-ca93-4754-a5a1-4d60b65defb9','yield','dimensionless',''),
    ('db895d84-1475-4019-b989-5d16cefbd9b7','amount of exchange in m³ 2','m3',''),
    ('4e2f4e10-6d62-464c-8142-cf5d8778480a','EcoSpold01Allocation_undefined_128','','undefined allocation 128 used in EcoSpold01 datasets'),
    ('67065577-4705-4ece-a892-6dd1d7ecd1e5','mass concentration, silicon','kg/m3','Mass concentration of Silicon.    (CAS 007440-21-3)'),
    ('f83aadf7-fcba-4734-82c2-3e2bd9b1dfdb','EcoSpold01Allocation_other_33','','other allocation 33 used in EcoSpold01 datasets'),
    ('57f4dc39-56ba-4ad1-b7e5-bbef25f37a5b','benzofluoranthene content','dimensionless',''),
    ('bdbf6a5a-e5e2-43ae-9ed6-2e550518516a','EcoSpold01Allocation_other_122','','other allocation 122 used in EcoSpold01 datasets'),
    ('af7ef4cd-d96f-411f-8566-60150fa08f4e','EcoSpold01Allocation_other_88','','other allocation 88 used in EcoSpold01 datasets'),
    ('290526be-8bd4-4e92-a2f7-4901481e40da','EcoSpold01Allocation_physical_11','','physical allocation 11 used in EcoSpold01 datasets'),
    ('31326064-33ba-4a7c-917c-ed5a91103b66','EcoSpold01Allocation_other_32','','other allocation 32 used in EcoSpold01 datasets'),
    ('8db6e12a-56be-4bfb-ae7f-5fed2c498b34','Slope length','m','Slope length  [m]'),
    ('0f205308-d33a-430b-b3ec-b62bef311f2f','mass concentration, particulate phophorus','kg/m3','Mass concentration of Particulate Phophorus as P. Note that dissolved and particulate P are optional yet desirable specifications of total phosphorous.'),
    ('de4b532b-fdfe-47f1-96f0-2f4a82cfcbd9','EcoSpold01Allocation_undefined_163','','undefined allocation 163 used in EcoSpold01 datasets'),
    ('6c4ba845-c575-4792-b9fc-7df54c9bcf86','prop','dimensionless',''),
    ('db0e2ab7-1a5a-43b6-8ded-96ae36c7a49f','EcoSpold01Allocation_undefined_154','','undefined allocation 154 used in EcoSpold01 datasets'),
    ('c0dd146d-4b11-4b59-bd42-01ab280d6342','mass concentration, lithium','kg/m3','Mass concentration of Lithium.    (CAS 007439-93-2)'),
    ('abdfa6a8-b697-498b-be2c-bbe92ce6736c','maximum gross weight','kg',''),
    ('5bf7a913-4ae2-4549-90ee-35488a8f8918','SAM_activityLink_8_scaling_factor','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('4e6ff13b-7bfb-4e66-8255-6b0b7dcc6de8','capacity [MW]','MW',''),
    ('b275a25e-3259-47e4-a877-f93576656920','UVEK_link_1','',''),
    ('f53a5dbc-3bd3-4570-adff-b00790ea3ffc','nitrogen content','dimensionless','nitrogen content on a dry matter basis'),
    ('24e28a50-1255-48cf-8bc8-581ce90bda66','nitrogen oxides emissions tier T2-T4A-T4B for hp < 11','kg/hp*h',''),
    ('1370615c-9f91-4164-9434-7379b2a03be6','amount of exchange in liters 2','l',''),
    ('c1e362e9-8fbe-4e99-8652-4e62961c3c64','Soil organic carbon','kg',''),
    ('514535fa-6fda-4ed5-9d35-e394b322b3d6','amount 4 of flow in kg','kg',''),
    ('8cc1f034-59e9-49cc-8a7c-453f8deb0018','EcoSpold01Allocation_other_7','','other allocation 7 used in EcoSpold01 datasets'),
    ('53c1ac85-70df-400f-809e-d4d793c6a88b','nitrogen oxides emissions tier T1 for hp < 600','kg/hp*h',''),
    ('28567adf-1d64-4588-a318-3c873280edb1','EcoSpold01Allocation_undefined_136','','undefined allocation 136 used in EcoSpold01 datasets'),
    ('cdfa4ef3-c3cb-4bcf-a8fa-ab6f8d5a3a3e','low heating value of hardcoal in Colombia','MJ/kg','This property represents the low heating value of hard coal in Colombia.'),
    ('21c609ec-3de0-4134-9a91-28c57a8e381c','nitrogen oxides emissions tier T4 for hp >= 750','kg/hp*h',''),
    ('6f22673c-9bf3-4e87-be4a-831bea37f824','Crop factor','dimensionless','Crop factor [-]'),
    ('2d73088a-7538-404b-9b80-4ec91528509c','fuel input in m3','m3',''),
    ('9b6a1396-d611-4015-aa8d-e071c9e7248a','nitrogen oxides emissions tier T2-T3-T4-T4N for hp < 300','kg/hp*h',''),
    ('229ac7df-a9f3-43cf-84c9-7f8141f3c951','EcoSpold01Allocation_undefined_152','','undefined allocation 152 used in EcoSpold01 datasets'),
    ('a860a6d7-80de-47dc-92ce-c7983a2689cb','oriented strand board content','dimensionless','fraction of oven dry mass'),
    ('bca4bb32-f701-46bb-ba1e-bad477c19f7f','mass concentration, chromium','kg/m3','Mass concentration of Chromium.    (CAS 007440-47-3)'),
    ('69394b67-d859-4887-a7a2-64dec0ecdbd8','concentration, lead','kg/kg',''),
    ('87188506-0cc4-4c15-ad37-ff5527f7af11','processing_efficiency','dimensionless',''),
    ('ad7781c7-5dc2-4421-b182-e1fd4cef7fa5','cadmium content','dimensionless','cadmium content on a dry matter basis'),
    ('22640fa6-4eec-426e-ad6a-dec3e440ec36','EcoSpold01Allocation_undefined_103','','undefined allocation 103 used in EcoSpold01 datasets'),
    ('843b09ba-1ffd-4535-a751-9e1b4ebd0d2b','EcoSpold01Allocation_other_118','','other allocation 118 used in EcoSpold01 datasets'),
    ('9fa0b3d1-ce8d-4991-bbf8-71eadc39321b','nitrogen oxides emissions tier T2 for hp < 600','kg/hp*h',''),
    ('66f07cc8-9cb2-4518-9042-9a72b4ac1d0c','aluminium hydroxide content','dimensionless','Based on the simplifying assumption that all aluminium is in Al(OH)3, since split between bauxite rich in Al(OH)3 and Al(OH)O is not known.'),
    ('8f14b33c-bc62-4c5b-96d9-6e92d3631eb2','EcoSpold01Allocation_physical_10','','physical allocation 10 used in EcoSpold01 datasets'),
    ('ff25f3c3-5f43-4ac0-bb13-d8ecc6fc7b75','terbium content','dimensionless','terbium content on a dry matter basis'),
    ('e31fd33a-ada5-43fb-8c23-94d48cccb29d','EcoSpold01Allocation_undefined_167','','undefined allocation 167 used in EcoSpold01 datasets'),
    ('5df87d0c-43fd-4c6b-936f-37c806debc2b','amount from Québec dataset in kg','kg',''),
    ('1e4dda32-af87-4ead-8b71-3609d387d11f','EcoSpold01Allocation_undefined_41','','undefined allocation 41 used in EcoSpold01 datasets'),
    ('35b99d19-d113-4eed-97aa-fa7bbbd77c27','Corresponding fuel use, transport, freight train','kg','kg per ton*km'),
    ('b8c88fc1-eed6-48d2-9737-e9dd8e212eb4','EcoSpold01Allocation_physical_5','','physical allocation 5 used in EcoSpold01 datasets'),
    ('2daa7f09-b2d2-4f14-9d50-b08899a1076f','carbon monoxide emissions tier T1-T2-T4 for hp >= 750','kg/hp*h',''),
    ('ff981578-530f-4ad0-8f60-f7509ccb11ff','ratio pf particulates greater than 10 microns','',''),
    ('4109b4cb-68d4-4c4a-a61c-cdb1d2c13530','amount of exchange 4','kg',''),
    ('fc26822f-6400-41a5-aac6-94b7088bdabe','suspended soilds, mass per volume','kg/m3','Suspended soilds in wastewater [kg/m3]'),
    ('ee73451f-d74d-44ad-9f78-728fec2faa06','Erosivity factor','metric ton/ha','The erosivity factor R represents the erosive force of rainfall and irrigation [MJ mm ha-1 h-1 yr-1]'),
    ('a689662b-5119-429c-ae85-6115df50e093','EcoSpold01Allocation_other_76','','other allocation 76 used in EcoSpold01 datasets'),
    ('6eb1f2f9-7e5b-46e3-a253-57b980994f9d','EcoSpold01Allocation_other_138','','other allocation 138 used in EcoSpold01 datasets'),
    ('f01d999e-26db-4042-ad47-9990a820b6c4','amount in multioutput activity_kBq','kBq',''),
    ('4304cee2-2cb3-4bb0-8482-de81b2434861','EcoSpold01Allocation_physical_6','','physical allocation 6 used in EcoSpold01 datasets'),
    ('b181bebd-539c-49bc-810e-9a443060afbc','thorium content','dimensionless','thorium content on a dry matter basis'),
    ('a8aa250d-d2d6-47a0-baac-d161806bf103','EcoSpold01Allocation_undefined_13','','undefined allocation 13 used in EcoSpold01 datasets'),
    ('3a0af1d6-04c3-41c6-a3da-92c4f61e0eaa','dry mass','kg',''),
    ('2c9df76e-6822-409a-9fac-424f6665184c','amount of refractory material sent to recycling','kg',''),
    ('4e5c60f3-b721-4f77-844a-c93d018c3172','EcoSpold01Allocation_undefined_1','','undefined allocation 1 used in EcoSpold01 datasets'),
    ('8068cdb4-245b-46ea-8a80-a0d984ba4bfd','EcoSpold01Allocation_other_81','','other allocation 81 used in EcoSpold01 datasets'),
    ('3ac16c15-0bf0-41a2-b6fe-a2a40185f82e','EcoSpold01Allocation_other_59','','other allocation 59 used in EcoSpold01 datasets'),
    ('bede81da-ba2e-4e0f-a917-e6047ac15221','amount in multioutput activity_kg','kg',''),
    ('a17f5864-6177-4619-82c5-3426c8c64e7d','gallium content','dimensionless','gallium content on a dry matter basis'),
    ('13706ab5-1a8c-42fd-8329-c93266943c87','EcoSpold01Allocation_undefined_16','','undefined allocation 16 used in EcoSpold01 datasets'),
    ('2d23d1bb-e137-4ade-83fc-fbd0421e6cd5','hydrogen content','dimensionless','hydrogen content on a dry matter basis'),
    ('e330c0ab-2554-429c-b388-5b96562c9720','length, external','m',''),
    ('533fe33f-450e-4af9-a442-c37e350b2226','input_kWh_silver','kWh',''),
    ('19859900-09d1-404d-a84a-dff37102a37a','EcoSpold01Allocation_undefined_126','','undefined allocation 126 used in EcoSpold01 datasets'),
    ('e54fd3af-358d-4e00-ac13-84426f7c2768','EcoSpold01Allocation_undefined_11','','undefined allocation 11 used in EcoSpold01 datasets'),
    ('6b32e857-0fd2-485a-8951-8ad6fbcb7fb8','polycyclic aromatic hydrocarbon content, total','dimensionless','content of total polycyclic aromatic hydrocarbon content on a dry mass basis'),
    ('0e8e0438-384e-42cc-824f-becb364d2222','nitrogen oxides emissions tier T2 for hp < 100','kg/hp*h',''),
    ('e1d5fa9f-0c99-4804-a34a-804ee04d3aba','Tillage factor','dimensionless','tillage factor [-]'),
    ('ddbab0d1-b156-41bc-98e5-fb680285d7cd','mass concentration, calcium','kg/m3','Mass concentration of Calcium.    (CAS 007440-70-2)'),
    ('6b8ec313-4e6f-4446-8ef5-c1ec6854bd62','percentage of associated gas','dimensionless',''),
    ('d8e26d77-fad5-4b31-b8ed-80e6920b5a5a','filter dust to landfill','kg',''),
    ('7506683f-91dc-4628-943d-e4b42c279d21','EcoSpold01Allocation_undefined_170','','undefined allocation 170 used in EcoSpold01 datasets'),
    ('c6cc9416-0127-478b-84bc-9d40a802686d','EcoSpold01Allocation_other_57','','other allocation 57 used in EcoSpold01 datasets'),
    ('19e1c0ab-ecab-42c3-b12d-ea30b3b7f33e','SAM_activityLink_3_scaling_factor','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('058d6d50-172b-4a8a-97da-0cee759eca7d','mass concentration, tungsten','kg/m3','Mass concentration of Tungsten.    (CAS 007440-33-7)'),
    ('09345cd3-5275-4440-8046-3ae837e4fcaf','corresponding fuel use, propane, furnace >100kW','MJ','Lower heating value of the fuel input related to the heat/electricity output'),
    ('92dbd49f-8cf0-4510-b9c0-6b90443b328e','rhodium content','dimensionless','rhodium content on a dry matter basis'),
    ('8f20e2c8-3485-42d1-9bc9-8cd3b1374788','fuel input in physical units, L','l',''),
    ('9ffcf8a4-1895-4009-b033-26d3c0ebffd6','amount of exchange in kg 2','kg',''),
    ('e1d2c19b-3a97-4f52-a83f-fe88400452c2','chromium content','dimensionless','chromium content on a dry matter basis'),
    ('350b57a1-2b58-49e8-96bd-c9a4be6b4625','lifetime capacity [unit]','unit',''),
    ('4119c81d-5650-4af0-bbaf-2f892b78946f','EcoSpold01Allocation_other_80','','other allocation 80 used in EcoSpold01 datasets'),
    ('f6f393da-d34f-470d-add4-bad3b3e2cf2e','EcoSpold01Allocation_undefined_23','','undefined allocation 23 used in EcoSpold01 datasets'),
    ('cdd48e4f-e361-4d58-a61b-a0e142786d03','maximum payload','kg',''),
    ('ee2d771f-6f0b-4ffc-a03d-e0afe2edd410','SAM_activityLink_10','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('b1e23c16-0199-4fd2-9c09-d89e1e0ef6c3','EcoSpold01Allocation_other_82','','other allocation 82 used in EcoSpold01 datasets'),
    ('afd66188-6460-4b90-a5ee-9ecb56c99574','SAM_activityLink_1_scaling_factor','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('395566da-d6f8-4f41-a799-f95234b3eb38','EcoSpold01Allocation_undefined_57','','undefined allocation 57 used in EcoSpold01 datasets'),
    ('c4c79eeb-95e1-43fb-b993-b6057296ddc5','EcoSpold01Allocation_undefined_160','','undefined allocation 160 used in EcoSpold01 datasets'),
    ('ae171669-ad44-43d5-9f0c-5dc6e17f1206','EcoSpold01Allocation_undefined_164','','undefined allocation 164 used in EcoSpold01 datasets'),
    ('71ff1af9-6834-46e8-b392-e73cbe898dae','mass concentration, ytterbium','kg/m3','Mass concentration of Ytterbium.    (CAS 007440-64-4)'),
    ('04f55b1f-14cd-4086-9814-d218f9dea04a','amount of flow 3 in kg','kg',''),
    ('d21c7c5c-b2c2-43ae-8575-c377cc0b0495','mass concentration, beryllium','kg/m3','Mass concentration of Beryllium.    (CAS 007440-41-7)'),
    ('4b0bcb7d-53b1-4f01-bc6b-ce85159b0576','EcoSpold01Allocation_undefined_60','','undefined allocation 60 used in EcoSpold01 datasets'),
    ('cf6fc65c-b941-4211-89c8-ec3aec00b076','mass concentration, rhenium','kg/m3','Mass concentration of Rhenium.    (CAS 007440-15-5)'),
    ('4bb300e0-9696-45a4-808a-d4ed4e52fa0f','EcoSpold01Allocation_other_9','','other allocation 9 used in EcoSpold01 datasets'),
    ('a102e6f8-ebc7-450b-a39b-794be96558b7','mass concentration, mercury','kg/m3','Mass concentration of Mercury.    (CAS 007439-97-6)'),
    ('66e996b5-5f7b-449f-8893-0b787af21d7e','cobalt content','dimensionless','cobalt content on a dry matter basis'),
    ('5ca5b0e5-f412-41ad-b61f-7cd72103ecd1','EcoSpold01Allocation_undefined_78','','undefined allocation 78 used in EcoSpold01 datasets'),
    ('9210d4a4-402c-475a-b354-94a8263632eb','mass concentration, thulium','kg/m3','Mass concentration of Thulium.    (CAS 007440-30-4)'),
    ('70da437b-65cd-498b-a980-7a6b8bc2f525','concentration, nickel','kg/kg','nickel content on a fresh matter basis'),
    ('d2c1650c-a56f-4936-84b5-c9de10c9a37f','EcoSpold01Allocation_physical_16','','physical allocation 16 used in EcoSpold01 datasets'),
    ('f9c05486-1c02-4621-af34-2145cecf0fb6','EcoSpold01Allocation_undefined_122','','undefined allocation 122 used in EcoSpold01 datasets'),
    ('0ce1f856-c01b-4276-8f07-3def6f240dd1','multiplicative factor','dimensionless',''),
    ('53338e64-f7ea-4948-b342-3fc6e3d3c302','weight','kg',''),
    ('6879600d-dc07-4c03-babf-7183432bcf54','EcoSpold01Allocation_undefined_137','','undefined allocation 137 used in EcoSpold01 datasets'),
    ('9b12772d-5204-4f46-86a6-0aa3e1670f6a','EcoSpold01Allocation_undefined_80','','undefined allocation 80 used in EcoSpold01 datasets'),
    ('3677f68f-7c83-4abf-a2e7-3f4215e2ef49','EcoSpold01Allocation_undefined_150','','undefined allocation 150 used in EcoSpold01 datasets'),
    ('2f258629-7e10-4856-ba63-3012eb7cf084','EcoSpold01Allocation_undefined_59','','undefined allocation 59 used in EcoSpold01 datasets'),
    ('af20a165-c287-4949-b0c5-faac84d03d37','EcoSpold01Allocation_other_42','','other allocation 42 used in EcoSpold01 datasets'),
    ('5a19a87d-4bb5-4f85-a7e5-9bbdfd55cf59','nitrogen oxides emissions tier T0-T1 for hp < 11','kg/hp*h',''),
    ('df06865b-1a20-480f-a3a1-ea494f96e566','EcoSpold01Allocation_other_126','','other allocation 126 used in EcoSpold01 datasets'),
    ('779537ad-2e38-4119-aa15-d49415136fdf','EcoSpold01Allocation_other_50','','other allocation 50 used in EcoSpold01 datasets'),
    ('f0e05731-4b64-4a8a-a216-a7ad908d76bc','mass concentration, holmium','kg/m3','Mass concentration of Holmium.    (CAS 007440-60-0)'),
    ('7f891aba-bd46-4618-87e2-ac51f35a5780','fraction > 10microns','dimensionless',''),
    ('6d02b77d-7f8b-438c-9394-334f995f99d8','carbon monoxide emissions tier T2-T4A-T4B for hp < 25','kg/hp*h',''),
    ('3aef92a8-1578-46ee-8ba4-aa4611bf95f3','EcoSpold01Allocation_undefined_14','','undefined allocation 14 used in EcoSpold01 datasets'),
    ('83f67a9e-bf78-4e0d-b1f0-5051a1fda9fe','molybdenum content','dimensionless','molybdenum content on a dry matter basis'),
    ('2586abb3-0f88-4e4d-9673-4ae55dc3b6ab','EcoSpold01Allocation_other_40','','other allocation 40 used in EcoSpold01 datasets'),
    ('b7876aa9-8d3d-41e0-9f87-6f483c6c5cb7','EcoSpold01Allocation_other_111','','other allocation 111 used in EcoSpold01 datasets'),
    ('de9e34f7-0567-4804-865f-0b7cfa558edd','EcoSpold01Allocation_other_37','','other allocation 37 used in EcoSpold01 datasets'),
    ('39b9c712-17bd-461c-902f-0c47168b3e0a','EcoSpold01Allocation_undefined_119','','undefined allocation 119 used in EcoSpold01 datasets'),
    ('db33417a-c3a6-4098-867c-eafeb8f8c72a','capacity [kg/s]','kg/s',''),
    ('95dc31b3-6bfb-421c-a502-a1a35d8ddee7','EcoSpold01Allocation_other_5','','other allocation 5 used in EcoSpold01 datasets'),
    ('1100f7b2-6d35-4ece-9f17-5fbea7282cd5','EcoSpold01Allocation_undefined_70','','undefined allocation 70 used in EcoSpold01 datasets'),
    ('a6270f3a-bfd4-4a69-81a0-25d23a963ad4','input_kg','kg',''),
    ('63169b0e-3ae8-40f0-a0a9-0418bff24943','EcoSpold01Allocation_other_116','','other allocation 116 used in EcoSpold01 datasets'),
    ('34e62ad8-9727-4505-abab-260d3df9a697','carbon monoxide emissions tier T4N for hp >= 750','kg/hp*h',''),
    ('8c3af736-c05e-49cf-b223-2d347054da3c','EcoSpold01Allocation_other_133','','other allocation 133 used in EcoSpold01 datasets'),
    ('829cf41b-3060-4fe5-a1ea-191a0a2c10cf','EcoSpold01Allocation_other_89','','other allocation 89 used in EcoSpold01 datasets'),
    ('edb5885b-2292-4889-9221-ab7012ea5595','mass concentration, ruthenium','kg/m3','Mass concentration of Ruthenium.    (CAS 007440-18-8)'),
    ('d388e0ab-8411-4347-8174-c5bf5fd14296','mass concentration, carbone dioxide','kg/m3',''),
    ('d1191f28-0cc9-4f82-9a26-bf49de106198','EcoSpold01Allocation_other_70','','other allocation 70 used in EcoSpold01 datasets'),
    ('a20fcb4b-9474-4d9b-95a9-fba913f6b38f','carbon monoxide emissions tier T1-T2-T4A for hp < 50','kg/hp*h',''),
    ('7ed11387-207c-424f-922f-1cb1d2bf8596','EcoSpold01Allocation_undefined_140','','undefined allocation 140 used in EcoSpold01 datasets'),
    ('6151c9e8-8d65-48e5-b2ab-eeb8615435b9','seeds per hectare','unit',''),
    ('f2f106e4-c191-4ee7-8c79-7576b3984bd2','carbon monoxide emissions tier T4-T4N for hp < 175','kg/hp*h',''),
    ('e092deec-37ab-4f20-ad74-1460544a9911','erbium content','dimensionless','erbium content on a dry matter basis'),
    ('76b0b954-ae61-4ac8-a585-700724fd53a6','mass concentration, germanium','kg/m3','Mass concentration of Germanium.    (CAS 007440-56-4)'),
    ('9732cce6-14fe-4ce3-8bc9-8aa10d8b0418','EcoSpold01Allocation_undefined_113','','undefined allocation 113 used in EcoSpold01 datasets'),
    ('5b66c906-de94-4a06-9037-498de5498f82','lifetime capacity','guest night',''),
    ('b3fdadf7-9e1d-42bd-b36c-1744c7565539','lifetime capacity [kg*day]','kg*day',''),
    ('7affb437-ad2b-4bf5-ae1b-93349e0f5dc0','sodium hydroxide-to-hydroxide mass ratio','dimensionless',''),
    ('33976f6b-2575-4410-8f60-d421bdf3e554','mass concentration, barium','kg/m3','Mass concentration of Barium.    (CAS 007440-39-3)'),
    ('7ec3f14a-712b-4942-bc38-1a8a425e8729','EcoSpold01Allocation_undefined_166','','undefined allocation 166 used in EcoSpold01 datasets'),
    ('cf406018-917d-47e0-acd1-1189ccaab60a','density loose','kg/m3',''),
    ('59d14f7c-d6ea-4770-af4a-aa3dd6538b98','xenon content','dimensionless','xenon content on a dry matter basis'),
    ('60dacb81-e92c-4f1e-bf85-0f30a9921e4c','EcoSpold01Allocation_undefined_37','','undefined allocation 37 used in EcoSpold01 datasets'),
    ('e9884091-48d5-4f2d-bcbd-555e5932232b','distance','km',''),
    ('0f9f07be-6c03-4d94-86eb-e220d361b3b3','EcoSpold01Allocation_undefined_111','','undefined allocation 111 used in EcoSpold01 datasets'),
    ('0ba7c468-731e-4251-96b5-d3f7cd2db260','EcoSpold01Allocation_undefined_24','','undefined allocation 24 used in EcoSpold01 datasets'),
    ('4c5edc32-2b79-49fc-a93f-7a9f7c2c15df','amount of flow 2 in kg','kg',''),
    ('16c618be-8539-4176-97f0-811bdfc03a55','SAM_activityLink_10_scaling_factor','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('7de227b7-59d4-4a2e-a3ba-a3d7b3d804e7','EcoSpold01Allocation_undefined_46','','undefined allocation 46 used in EcoSpold01 datasets'),
    ('e67802d9-321c-4494-a7b0-f769a634d6ca','EcoSpold01Allocation_undefined_134','','undefined allocation 134 used in EcoSpold01 datasets'),
    ('b142feef-d230-4376-aee7-919bbebed59a','mass concentration. lutetium','kg/m3','Mass concentration of Lutetium.    (CAS 007439-94-3)'),
    ('4c4768a0-58dd-45f8-a42a-e2a0b77d608e','weight with a refrigeration unit','kg',''),
    ('6d9e1462-80e3-4f10-b3f4-71febd6f1168','water in wet mass','kg','water content on a wet matter basis'),
    ('ed198fe4-89cf-4812-96c0-f65919df0c33','EcoSpold01Allocation_other_3','','other allocation 3 used in EcoSpold01 datasets'),
    ('f0b0d5bd-1c2f-4074-b5d9-d6253e73c0ce','EcoSpold01Allocation_other_60','','other allocation 60 used in EcoSpold01 datasets'),
    ('7526573b-0e79-48cd-b885-d569e46d33e0','nitrogen oxides emissions tier T1-T2 for hp < 50','kg/hp*h',''),
    ('f6c7ebbb-902a-412f-a55b-0743aea00238','sulfur content','dimensionless','sulfur content on a dry matter basis'),
    ('ed229b01-1b3f-4754-8871-5e88a83f3725','concentration, chromium','kg/kg','Concetration of chromium'),
    ('61205d13-4433-43f6-8b6f-dd76c2036618','EcoSpold01Allocation_other_20','','other allocation 20 used in EcoSpold01 datasets'),
    ('35fad4b2-1830-441c-98c2-187b3e9dc226','carbon monoxide emissions tier T1-T2 for hp < 11','kg/hp*h',''),
    ('bb2f5120-57f4-4ae3-95ea-89d571b526d1','no. of deformation strokes','dimensionless','for use in metal extrusion'),
    ('dcc3ffa8-8231-47b0-a652-e5829c72b995','EcoSpold01Allocation_undefined_102','','undefined allocation 102 used in EcoSpold01 datasets'),
    ('0c45ba75-5070-4fd4-968f-163df0719411','EcoSpold01Allocation_undefined_40','','undefined allocation 40 used in EcoSpold01 datasets'),
    ('aadaffec-6d71-44ab-8a63-53d67f5df6ff','amount 3 of flow in kg','kg',''),
    ('d717d3e6-7f87-4c07-b1af-9458e21efaa9','density argon','kg/m3',''),
    ('f661d089-6356-485a-bff5-834415dc83ae','EcoSpold01Allocation_undefined_142','','undefined allocation 142 used in EcoSpold01 datasets'),
    ('02927350-e86c-4e02-864d-eab353d94fa6','EcoSpold01Allocation_undefined_50','','undefined allocation 50 used in EcoSpold01 datasets'),
    ('60288f73-bc0d-4a55-8d77-a482bf9d3fbd','amount of exchange in kg 3','kg',''),
    ('4066a930-fa49-4c3b-97e5-b00beaed750c','EcoSpold01Allocation_other_98','','other allocation 98 used in EcoSpold01 datasets'),
    ('e213502c-b6b2-4e32-adaf-f29ba3b05709','MARKET_OVERWRITE_AMOUNT_CONSEQUENTIAL','dimensionless','Defines the new amount of its exchange to be used in linking of the market for the consequential system model.'),
    ('66664710-3b63-4c63-993a-31a4b858ba1e','EcoSpold01Allocation_undefined_135','','undefined allocation 135 used in EcoSpold01 datasets'),
    ('47619ea5-5df6-47aa-aa97-2a059063645b','amount of exchange in liters 4','l',''),
    ('fc3ab440-2345-47f3-90a5-faff131cf3ed','calculation property, unit','unit','A generic property to be defined individually in each dataset. For use in mathematical relations.'),
    ('e9164ff3-fd2d-4050-895d-0e0a42317be2','mass concentration, iodine','kg/m3','Mass concentration of Iodine.    (CAS 007553-56-2)'),
    ('89d6c9b8-5012-4a1e-8c32-211843d1136f','butanol input, volume','l',''),
    ('7acb6b78-3708-4660-a3fc-b0034d6c6caa','EcoSpold01Allocation_undefined_141','','undefined allocation 141 used in EcoSpold01 datasets'),
    ('a83c5198-6c63-4066-95c7-1907d7bcf348','EcoSpold01Allocation_undefined_114','','undefined allocation 114 used in EcoSpold01 datasets'),
    ('46d0892f-0324-4143-9bd6-1ffd9ed68c61','nitrogen oxides emissions tier T2-T4-T4A for hp < 75','kg/hp*h',''),
    ('e9688cbc-7400-457a-a936-5ab123ea326c','aluminium content','dimensionless','aluminium content on a dry matter basis'),
    ('a1f8e76d-b8da-4c1a-a852-efb768dcef38','carbon monoxide emissions tier T4-T4N for hp < 100','kg/hp*h',''),
    ('51d4e726-0f87-4c62-9f3a-4fd008143561','conversion factor m3 to MJ','','Used to remove duplicate conversion datasets'),
    ('5e4a4841-9282-4f36-a737-a1fbd1c38b8b','EcoSpold01Allocation_other_65','','other allocation 65 used in EcoSpold01 datasets'),
    ('2a256b0b-6003-4669-a3c1-1d3eba2de45e','mercury content','dimensionless','mercury content on a dry matter basis'),
    ('dc7524e0-95ac-4321-8a4c-de8580a4c75f','external scrap','kg',''),
    ('4da6c212-f8b0-49b0-9ec3-810b745d48d6','carbon monoxide emissions tier T1-T2-T3B for hp < 100','kg/hp*h',''),
    ('5ffa64c0-99a4-4a20-a1ec-4a7a4e9e0aac','EcoSpold01Allocation_other_55','','other allocation 55 used in EcoSpold01 datasets'),
    ('1ae79861-a8a8-4118-aa6b-eb93351f315b','mass concentration, radium','kg/m3','Mass concentration of Radium.    (CAS 007440-14-4)'),
    ('58dd6b6e-a0c7-46e6-9cd5-5d07de11a858','EcoSpold01Allocation_undefined_51','','undefined allocation 51 used in EcoSpold01 datasets'),
    ('3ef999eb-06c5-46b0-9055-a84283da67df','mass concentration, hafnium','kg/m3','Mass concentration of Hafnium.    (CAS 007440-58-6)'),
    ('3fda760d-9aba-4eb6-9ad2-95bb2ddc30b7','EcoSpold01Allocation_undefined_151','','undefined allocation 151 used in EcoSpold01 datasets'),
    ('51965208-0429-453c-b230-14ef7bec14c1','amount from Québec dataset in m³','m3',''),
    ('43e30a6f-82ee-4f81-b799-e835163c8dcd','tantalum content','dimensionless','tantalum content on a dry matter basis'),
    ('71f8f2c1-b495-4faa-b67f-ab4bf852ece7','EcoSpold01Allocation_other_91','','other allocation 91 used in EcoSpold01 datasets'),
    ('1dcfb203-7830-40b2-878d-13fc02a74051','barium content','dimensionless','barium content on a dry matter basis'),
    ('82a79813-89bc-46aa-b8c3-aa85b595365f','EcoSpold01Allocation_undefined_15','','undefined allocation 15 used in EcoSpold01 datasets'),
    ('b4d2d9e3-85dc-4ef0-8184-6af23c011c98','EcoSpold01Allocation_undefined_56','','undefined allocation 56 used in EcoSpold01 datasets'),
    ('19504644-f915-46a2-86e7-a02836ec7a6f','corresponding fuel use, in m3','m3',''),
    ('8900f7ba-3443-4cc9-8b48-353605a19da0','recovery rate','dimensionless',''),
    ('c3037e52-42ec-41bf-a3f2-f1a98f6355e5','EcoSpold01Allocation_other_135','','other allocation 135 used in EcoSpold01 datasets'),
    ('d2efbebc-9ec8-4ce3-aea4-f4353094f458','fraction, origin: fresh water','dimensionless','This property represent the fraction of the amount of the exchange which origin is fresh water.'),
    ('0a6b459a-0956-5c88-b9c7-f581ced2a622','polonium content','dimensionless','polonium content on a dry matter basis'),
    ('07e0a0da-2771-41d7-b6a4-0c4aad2e8302','boiling point','K',''),
    ('97f3bbfe-fa3a-4d05-9cb6-bb4b6379c5ef','phosphorus content','dimensionless','phosphorus content on a dry matter basis'),
    ('3b8cf819-ee90-47bd-953f-5bb13e87dbc3','carbon monoxide emissions tier T0-T1 for hp >= 100','kg/hp*h',''),
    ('8a8eec3f-2341-4834-a3ec-f73a6d57b571','EcoSpold01Allocation_other_100','','other allocation 100 used in EcoSpold01 datasets'),
    ('0650a63d-be1c-49b6-94c5-d0dc2acc35d6','iridium content','dimensionless','iridium content on a dry matter basis'),
    ('38f94dd1-d5aa-41b8-b182-c0c42985d9dc','price','EUR2005',''),
    ('422bd602-aed1-4d2e-9c47-b5ee2c277908','EcoSpold01Allocation_other_137','','other allocation 137 used in EcoSpold01 datasets'),
    ('ff58ccde-ca74-4793-aa27-5879089aaecf','carbon monoxide emissions tier T0-T1 for hp < 100','kg/hp*h',''),
    ('0189a8b3-ab31-4a48-9cba-e9d68c079f9e','annual production','kg',''),
    ('d1f4b69b-6bae-4303-8e95-5e97e2637aa2','input_kWh_gold','kWh',''),
    ('3db02346-808f-4eb6-9232-317a23c63484','EcoSpold01Allocation_undefined_7','','undefined allocation 7 used in EcoSpold01 datasets'),
    ('ab204d7a-a79b-4870-bb73-5969c0ed58e8','carbon monoxide emissions tier T1-T2 for hp < 100','kg/hp*h',''),
    ('e89aabea-22d5-42b0-b849-2b0d01ed3740','EcoSpold01Allocation_other_10','','other allocation 10 used in EcoSpold01 datasets'),
    ('1ddd3907-e24f-4b01-98ca-8ff1ca686c22','EcoSpold01Allocation_other_53','','other allocation 53 used in EcoSpold01 datasets'),
    ('ebfe771a-752d-4027-af95-e7342bc4cbeb','amount in multioutput activity_unit','unit',''),
    ('401351bc-2910-4dd5-b85c-9fca91d73913','nitrogen oxides emissions tier T2-T4-T4A for hp < 50','kg/hp*h',''),
    ('91a6ec9a-f0ae-4972-aaa0-0a96c6a7e718','EcoSpold01Allocation_other_103','','other allocation 103 used in EcoSpold01 datasets'),
    ('df8fa668-ec65-5049-b303-663c3d45a863','actinium content','dimensionless','actinium content on a dry matter basis'),
    ('ff888459-10c3-4700-afce-3a024aaf89cf','mass concentration, tin','kg/m3','Mass concentration of Tin.    (CAS 007440-31-5)'),
    ('22ca28a0-51e6-4f82-9ae7-b6c22a59abb9','helium content','dimensionless','helium content on a dry matter basis'),
    ('c8bd609b-f039-4f12-b181-84db2bbcfd2c','EcoSpold01Allocation_other_29','','other allocation 29 used in EcoSpold01 datasets'),
    ('34b5d0fc-9487-4870-bc43-eb2308fc11f3','Quebec production volume in m³','m3',''),
    ('2c6054e2-1714-4a92-9814-3a2b41dd4bae','oil content','dimensionless','oil content in seeds'),
    ('0d3538d1-56c3-43d6-bb53-bd55ac024914','recycled spent pot liner carbon','kg',''),
    ('a9e5f4bc-9946-4a4f-90c6-8c1083490dd6','carbon monoxide emissions tier T2-T3 for hp < 600','kg/hp*h',''),
    ('498924d9-17b0-4454-80dd-51adb77dedcb','EcoSpold01Allocation_physical_13','','physical allocation 13 used in EcoSpold01 datasets'),
    ('7e83fd10-c04d-4a80-8df2-a8bbcc268c4a','selenium content','dimensionless','selenium content on a dry matter basis'),
    ('a8f781cd-a263-4b55-8f81-027dd39438d0','oil/fat content','dimensionless',''),
    ('e6a9a337-e019-4455-94be-62addb6a1d92','fossil share of carbon','','Share ]0:1[ of the carbon which is of fossil origin.'),
    ('9162ac19-a45e-4c38-9f87-59bd2ea8dafb','SAM_activityLink_5','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('a0ec6973-5c70-4c84-805b-fbd057e27ee1','total length of network','km',''),
    ('27a52505-9924-4fee-93ed-49fea90d8688','EcoSpold01Allocation_other_75','','other allocation 75 used in EcoSpold01 datasets'),
    ('259dce5e-3697-47d3-ad0c-760256f31c13','EcoSpold01Allocation_undefined_85','','undefined allocation 85 used in EcoSpold01 datasets'),
    ('b84cee83-08cf-43e8-bbff-51a6857ae19c','EcoSpold01Allocation_other_26','','other allocation 26 used in EcoSpold01 datasets'),
    ('6090fa5e-f862-491b-90ca-4b7f8d5a2880','UVEK_absolute_amount_3','dimensionless',''),
    ('db9e4f42-3ef9-4e3c-a7d3-5fb4f3fc0aa6','EcoSpold01Allocation_other_48','','other allocation 48 used in EcoSpold01 datasets'),
    ('fdafa860-c059-437e-838d-9d151b2067b3','thulium content','dimensionless','thulium content on a dry matter basis'),
    ('24a8bbce-eab8-4ae2-9b58-b642dee66c0b','EcoSpold01Allocation_undefined_92','','undefined allocation 92 used in EcoSpold01 datasets'),
    ('6014982c-ef8e-4555-add0-14bc00bad6be','bulk density','kg/m3',''),
    ('2d2d6270-d512-4b0f-aa44-86241b4d6282','EcoSpold01Allocation_undefined_146','','undefined allocation 146 used in EcoSpold01 datasets'),
    ('a01597eb-34e2-4057-a7c7-e27bfdca34d1','lifetime capacity in m3','m3',''),
    ('8d67414b-dc45-4938-ae6a-c9504f26bcfd','pH','dimensionless','pH is a measure of acidity it is defined as -log10(c_H+) where c_H+ is the hydrogen ion concentration in moles per liter.'),
    ('19adc55b-324f-4ac5-b97d-a46b297fcf40','carbon monoxide emissions tier T4 for hp < 50','kg/hp*h',''),
    ('6c4a1198-e394-4244-b2c1-400f359251f5','rubidium content','dimensionless','rubidium content on a dry matter basis'),
    ('313804be-cbb6-43f8-ac27-100f8aed5d84','nitrogen oxides emissions tier T1 for hp < 750','kg/hp*h',''),
    ('48c987bb-3144-4872-b5c7-b1389c40be25','heating value, net','MJ','net (lower) heating (calorific) value'),
    ('72e34840-3564-4883-aaa8-3f9f3038547a','EcoSpold01Allocation_undefined_29','','undefined allocation 29 used in EcoSpold01 datasets'),
    ('d574cc22-07f2-4202-b564-1116ab197692','mass concentration, strontium','kg/m3','Mass concentration of Strontium.    (CAS 007440-24-6)'),
    ('4f8aa556-ee1c-4814-b38b-47dda55aa34a','Surface','m2',''),
    ('0850c7ed-99f8-4135-bfac-12371154b0e3','EcoSpold01Allocation_undefined_39','','undefined allocation 39 used in EcoSpold01 datasets'),
    ('9877c28a-4873-41f1-8d65-c27a7ef57f0c','nitrogen oxides emissions tier T1 for hp < 11','kg/hp*h',''),
    ('35d2e0b2-eca5-4897-a6af-b6d2e61a9079','scandium content','dimensionless','scandium content on a dry matter basis'),
    ('ad764b69-b9ef-4962-ac70-7002f030be6a','capacity factor','',''),
    ('effa47e4-3d54-4e54-8b92-223b790f544a','concentration, iron','kg/kg',''),
    ('07ee9fef-f0da-42f8-a9c4-c821c49c1525','lumber content','dimensionless','fraction of oven dry mass'),
    ('e2bdc7a2-bfb2-4db4-9fa2-12e46f767097','EcoSpold01Allocation_undefined_19','','undefined allocation 19 used in EcoSpold01 datasets'),
    ('8273c5ca-d440-4299-aadc-e059d6e56291','plant average daily flow rate','m3/d',''),
    ('90082cb2-a539-44a0-a9aa-19aab80d4cf8','EcoSpold01Allocation_other_62','','other allocation 62 used in EcoSpold01 datasets'),
    ('b4373c8a-ac59-401c-95a4-e3dac1acabf6','EcoSpold01Allocation_other_119','','other allocation 119 used in EcoSpold01 datasets'),
    ('b433e928-6e22-419c-8441-47f0d76bd28f','SAM_activityLink_3','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('a1305118-74a0-45c2-992f-58f9b8a9f111','chemical factory annual production','kg/year',''),
    ('da9aed81-4e0a-4a15-9d5e-27020d826a01','zirconium content','dimensionless','zirconium content on a dry matter basis'),
    ('6b7a7ccc-e7ea-42e4-8bfd-32e36ba2a6bc','hydraulic oil input','l',''),
    ('6225e729-27b9-488d-a5e9-85d853321433','EcoSpold01Allocation_physical_3','','physical allocation 3 used in EcoSpold01 datasets'),
    ('249183f5-61d4-4fe9-be48-0b36ed4818e2','EcoSpold01Allocation_other_1','','other allocation 1 used in EcoSpold01 datasets'),
    ('fce247fb-71dc-4d8c-aec4-a0e5e67eae6e','phenol resorcinol formaldehyde resin content','dimensionless','Phenol Resorcinol Formaldehyde Resin '),
    ('4131adc0-afda-4a73-b6b6-3ed9341ee3d9','volume','m3','volume'),
    ('d8551abf-da96-4429-846b-0973136b7d48','tin content','dimensionless','tin content on a dry matter basis'),
    ('6b2e1ace-3d42-4536-aed5-866ac1281364','capacity [kg]','kg',''),
    ('468e50e8-1960-4eba-bc1a-a9938a301694','mass concentration, chlorine','kg/m3','Mass concentration of Chlorine.    (CAS 007782-50-5)'),
    ('2f7030b9-bafc-4b43-8504-deb8b5044130','mass concentration, cobalt','kg/m3','Mass concentration of Cobalt.    (CAS 007440-48-4)'),
    ('82728b89-48ab-4da6-9bad-faeb8ce02d1a','samarium content','dimensionless','samarium content on a dry matter basis'),
    ('f1521c85-6126-40e4-9860-1f80a7a8568f','EcoSpold01Allocation_other_129','','other allocation 129 used in EcoSpold01 datasets'),
    ('c9d506f1-98dc-45d4-acb8-83095fb93317','EcoSpold01Allocation_physical_15','','physical allocation 15 used in EcoSpold01 datasets'),
    ('cd4e3d6c-9898-4181-ba4d-d5763dc7e1c5','EcoSpold01Allocation_other_31','','other allocation 31 used in EcoSpold01 datasets'),
    ('3228318b-a090-4377-a41d-9f6c5553d775','EcoSpold01Allocation_other_112','','other allocation 112 used in EcoSpold01 datasets'),
    ('53f505b2-ad50-4c64-a9d6-0d3e41fb3dd2','EcoSpold01Allocation_other_6','','other allocation 6 used in EcoSpold01 datasets'),
    ('de1bb1fa-ab42-4f56-881e-f10e5222cf63','EcoSpold01Allocation_other_13','','other allocation 13 used in EcoSpold01 datasets'),
    ('d33e6732-d2f8-4441-ba03-e39d4a1228a5','mass concentration. lanthanum','kg/m3','Mass concentration of Lanthanum.    (CAS 007439-91-0)'),
    ('11d072f8-37fc-41c2-80b2-ebba4f301b49','lifetime capacity [MJ]','MJ',''),
    ('7380cc82-aad6-48d1-889f-b9740ba700b0','nitrogen oxides emissions tier T4A for hp < 50','kg/hp*h',''),
    ('347a7539-bd46-41b1-a30d-4e087178a3d8','EcoSpold01Allocation_other_125','','other allocation 125 used in EcoSpold01 datasets'),
    ('548bf5c9-79f5-440f-bc40-2848976922d8','price CHF','CHF2011',''),
    ('3759d833-560a-4dbb-949e-afc63c0ade26','mass concentration, antimony','kg/m3','Mass concentration of Antimony.    (CAS 007440-36-0)'),
    ('dcdc6c7b-0b72-4174-bc90-f51ed66426d5','mass concentration, silver','kg/m3','Mass concentration of Silver.    (CAS 007440-22-4)'),
    ('1ced5983-2a7b-49af-b6cd-ad4ebaafba89','mass concentration, praseodymium','kg/m3','Mass concentration of Praseodymium.    (CAS 007440-10-0)'),
    ('cc72d858-3a21-481e-8013-55a53976ffc2','mass concentration, cerium','kg/m3','Mass concentration of Cerium.    (CAS 007440-45-1)'),
    ('004f9876-b7fe-4015-8f83-9e07edabe496','EcoSpold01Allocation_other_109','','other allocation 109 used in EcoSpold01 datasets'),
    ('88c9f622-8451-41aa-98b0-c56b191a7e0a','mass concentration, particulate nitrogen','kg/m3','Mass concentration of particulate nitrogen as N. Note that dissolved and particulate N are optional yet desirable specifications of total nitrogen.'),
    ('f077d584-a74d-4c13-a8d7-3019f500094d','EcoSpold01Allocation_other_49','','other allocation 49 used in EcoSpold01 datasets'),
    ('c35265a9-fd3e-468c-af8e-f4e020c38fc0','mass concentration, selenium','kg/m3','Mass concentration of Selenium.    (CAS 007782-49-2)'),
    ('d1299459-4bb3-4ae4-abaf-08c89bdc7e60','EcoSpold01Allocation_undefined_174','','undefined allocation 174 used in EcoSpold01 datasets'),
    ('b1771ea0-faaf-4533-ab0c-393afcee8cec','fraction of diesel sulfur converted to direct PM (hydrated sulfuric acid)','dimensionless',''),
    ('e5159f1c-ddbe-44bf-aed8-7e04acf81d88','EcoSpold01Allocation_other_71','','other allocation 71 used in EcoSpold01 datasets'),
    ('4bcd332d-d5c4-485a-9130-3288a532b1ad','carbon monoxide emissions tier T4A for hp < 75','kg/hp*h',''),
    ('7ce01fe9-39dd-42a8-b344-e752c1496469','EcoSpold01Allocation_other_108','','other allocation 108 used in EcoSpold01 datasets'),
    ('1a7e58fe-d385-4d24-81c1-a6f682823a3e','EcoSpold01Allocation_undefined_172','','undefined allocation 172 used in EcoSpold01 datasets'),
    ('ec1f2209-1f53-40d5-bc53-67f388c82f5a','lifetime capacity [kWh]','kWh',''),
    ('810c1049-45c3-4d1d-bbff-e0fdc578c812','carbon monoxide emissions tier T4A-T4B for hp < 25','kg/hp*h',''),
    ('b9f3db9b-532b-4e43-83a8-8fb5bfade2dc','amount 5 of flow in kg','kg',''),
    ('40a28310-9574-4867-88fb-623fa7ed1fa3','mass concentration, hydrogen','kg/m3','Mass concentration of Hydrogen.    (CAS 001333-74-0)'),
    ('e815f85f-4d19-4e15-99f3-4d9b0ed8b6fa','heating value, net, natural gas','MJ','net (lower) heating (calorific) value'),
    ('06084f11-50f4-4103-ae0a-0c8a1fcc810d','consumption ratio','dimensionless',''),
    ('ac040fce-c9ed-4623-b02a-e512fef4ad52','EcoSpold01Allocation_undefined_173','','undefined allocation 173 used in EcoSpold01 datasets'),
    ('d271dd60-df24-4dbe-b447-7f059810a0f3','mass concentration, samarium','kg/m3','Mass concentration of Samarium.    (CAS 007440-19-9)'),
    ('c9011148-2905-474e-a858-c88d6ca870f3','francium content','dimensionless','francium content on a dry matter basis'),
    ('68d5fb80-18a8-4b05-b9a4-42023b8501b4','length, internal','m',''),
    ('725ed395-49f1-49c7-8f70-ce49a6fed4a2','EcoSpold01Allocation_undefined_107','','undefined allocation 107 used in EcoSpold01 datasets'),
    ('f74d688f-15db-411c-af4e-5110e136ec21','sand content','kg',''),
    ('b00066a1-40f3-466c-9bf9-4be11256842e','Corresponding fuel use','MJ','Lower heating value of the fuel input related to the heat/electricity output'),
    ('1e51ca3c-5b6b-4678-93ef-8fc4f8745f76','EcoSpold01Allocation_undefined_159','','undefined allocation 159 used in EcoSpold01 datasets'),
    ('811ae1c4-da2e-481d-859a-4c3965e1c408','EcoSpold01Allocation_undefined_63','','undefined allocation 63 used in EcoSpold01 datasets'),
    ('932d75c9-e53e-46d7-832d-f04d77af4b91','EcoSpold01Allocation_undefined_3','','undefined allocation 3 used in EcoSpold01 datasets'),
    ('048152de-7c5a-4b26-bebd-82c4ceb2cb02','value per kg of bi-metal cable','dimensionless',''),
    ('e4d35ad5-61a9-4ebd-8ce0-9fb9da2648e9','EcoSpold01Allocation_undefined_132','','undefined allocation 132 used in EcoSpold01 datasets'),
    ('b89a34ce-476c-40b0-8f53-ddd40ab8dafe','EcoSpold01Allocation_undefined_34','','undefined allocation 34 used in EcoSpold01 datasets'),
    ('3b2fd7f9-ae48-4c20-8d0f-47bcf927fcb3','EcoSpold01Allocation_undefined_65','','undefined allocation 65 used in EcoSpold01 datasets'),
    ('d3c0b420-1906-478c-8812-acfe6bf40c2e','sodium content','dimensionless','sodium content on a dry matter basis'),
    ('6b90d16b-f20b-4b53-abc2-763f9455dc05','bromine content','dimensionless','bromine content on a dry matter basis'),
    ('0b27405b-3e4d-45aa-bb5c-3c52d2b04e0e','europium content','dimensionless','europium content on a dry matter basis'),
    ('40ca2c51-2da6-4351-bd4c-d6f181fc7d55','EcoSpold01Allocation_undefined_2','','undefined allocation 2 used in EcoSpold01 datasets'),
    ('7066bede-a01a-4110-b186-4743a0f7730e','nitrogen oxides emissions tier T4N for hp >= 750','kg/hp*h',''),
    ('fafd4e54-9910-4f24-9fe3-701b28eef4b4','bark','dimensionless',''),
    ('7f341c54-c96f-49ce-990a-b430fd22475a','EcoSpold01Allocation_undefined_43','','undefined allocation 43 used in EcoSpold01 datasets'),
    ('b7f03a47-0c8e-456b-ac0d-077ec06e3125','EcoSpold01Allocation_undefined_12','','undefined allocation 12 used in EcoSpold01 datasets'),
    ('291c5be3-dd62-4e12-a0bd-48c3e694169a','mass concentration, terbium','kg/m3','Mass concentration of Terbium.    (CAS 007440-27-9)'),
    ('0ab0dbcd-8b4a-409e-8766-f45a7758c3ff','EcoSpold01Allocation_undefined_31','','undefined allocation 31 used in EcoSpold01 datasets'),
    ('71661037-8aac-4af4-8d62-3b58ccda9232','EcoSpold01Allocation_undefined_38','','undefined allocation 38 used in EcoSpold01 datasets'),
    ('6b7d0b77-c97b-4a8a-b4c5-f70836484a84','mass concentration, neon','kg/m3','Mass concentration of Neon.    '),
    ('d4c9277c-c6fb-432a-8fd5-f2defbe4b86f','EcoSpold01Allocation_other_93','','other allocation 93 used in EcoSpold01 datasets'),
    ('3e1978a6-47f8-4e31-8a83-79053a0e715e','mass concentration, gold','kg/m3','Mass concentration of Gold.    (CAS 007440-57-5)'),
    ('60f67378-cd0b-4a8d-bd63-0df272aefdeb','carbohydrates content','kg',''),
    ('35ae1cd5-37e5-4c4f-b046-f516842eda2a','EcoSpold01Allocation_undefined_100','','undefined allocation 100 used in EcoSpold01 datasets'),
    ('4f2b3b64-2dac-4559-9341-da19c1afa7f6','nitrogen oxides emissions tier T3B for hp < 100','kg/hp*h',''),
    ('96b698b6-c826-4e63-96b0-d1d76033a220','EcoSpold01Allocation_undefined_17','','undefined allocation 17 used in EcoSpold01 datasets'),
    ('30fd0072-a0d4-4b5b-ad3e-dbd50a227ba5','protactinium content','dimensionless','protactinium content on a dry matter basis'),
    ('10516dfc-a6ee-4e9e-8a17-fbde71b06c26','EcoSpold01Allocation_other_23','','other allocation 23 used in EcoSpold01 datasets'),
    ('d61f95b4-20df-44f8-8463-3423cae2556f','SAM_activityLink_6_scaling_factor','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('dbbc1095-ca27-4acb-98ea-57a8b54f1d91','production in l','l',''),
    ('9a645b11-8a9d-4511-88fc-621d125289f6','EcoSpold01Allocation_undefined_104','','undefined allocation 104 used in EcoSpold01 datasets'),
    ('e1b325f9-e4c0-4f1c-9890-ec2bca244c65','carbon monoxide emissions tier T2-T3-T4-T4N for hp < 300','kg/hp*h',''),
    ('4a46fd19-afb1-4fb3-8328-ae1fc4449536','EcoSpold01Allocation_undefined_75','','undefined allocation 75 used in EcoSpold01 datasets'),
    ('a3ca4324-b23e-489e-a799-b50ef9ed2e4e','mass concentration, protactinium','kg/m3','Mass concentration of Protactinium.    (CAS 007440-05-3)'),
    ('58bf4a99-c7c9-4b49-ad40-70e8169a62ea','paint volatile content','',''),
    ('dc740682-03b7-4b24-808a-10d4ef17e7d3','fuel consumption tier T0-T1-T2-T4A-T4B for hp < 25','kg/hp*h',''),
    ('8e73d3fb-bb81-4c42-bfa6-8be4ff13125d','mass concentration, phophorus','kg/m3','Mass concentration of Phophorus as P (Ptot.)'),
    ('fcf35248-3b07-43b7-a75c-77821e0ab19a','EcoSpold01Allocation_undefined_36','','undefined allocation 36 used in EcoSpold01 datasets'),
    ('45980067-4a2b-4a7d-883a-8516902b1a62','amount from Québec dataset in MJ','MJ',''),
    ('b03c4941-1524-4dfb-a0e3-c3fd6fab8215','EcoSpold01Allocation_undefined_106','','undefined allocation 106 used in EcoSpold01 datasets'),
    ('fd4a3f9c-447a-4271-9195-f3f9cc396c80','EcoSpold01Allocation_undefined_79','','undefined allocation 79 used in EcoSpold01 datasets'),
    ('f9da385d-5b1b-4548-826c-0bf5892a9fd9','calcium content','dimensionless','calcium content on a dry matter basis'),
    ('769c39a4-0ea6-494c-8c8f-3938acb2dbdb','SAM_activityLink_6','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('c774b985-aed8-4506-8c14-2b831bbfed11','P to surface water','kg/ha','Average quantity of P lost through run-off for a land use category (kg P /(ha*a)).'),
    ('330a5eb3-668a-4c44-9a25-55aa7305c88d','EcoSpold01Allocation_undefined_71','','undefined allocation 71 used in EcoSpold01 datasets'),
    ('2544bcdb-ce26-42c3-a9d0-37e2e18a8e30','EcoSpold01Allocation_physical_8','','physical allocation 8 used in EcoSpold01 datasets'),
    ('529b8a40-49e8-49b7-bf59-bd73ea8c1d1e','carbon monoxide emissions tier T1-T2-T4A-T4B for hp <25','kg/hp*h',''),
    ('efe22a60-b1a3-4b33-a5ba-4bf575e0a889','mass concentration, DOC','kg/m3','Mass concentration of Dissolved Organic Carbon'),
    ('6b093a42-84fe-41a1-8488-0fb444a5cf9d','uranium content','dimensionless','uranium content on a dry matter basis'),
    ('67f102e2-9cb6-4d20-aa16-bf74d8a03326','wet mass','kg',''),
    ('9fbbd119-6566-48c5-8799-1ef8390afe57','EcoSpold01Allocation_undefined_30','','undefined allocation 30 used in EcoSpold01 datasets'),
    ('54947c59-30b5-466f-8eae-595f58f54cbd','consumption in litre','l',''),
    ('e54d7883-8b43-4495-a2f2-ca7c69d49887','ratio of particulates between 2.5 and 10 microns','',''),
    ('dbf41b1b-c7b8-4d5e-b39c-f858eb868df5','oxygen content','dimensionless','oxygen content on a dry matter basis'),
    ('a31d9aea-bef7-476a-94c0-4582718c0f6d','carbon monoxide emissions tier T2-T3-T4-T4N for hp < 175','kg/hp*h',''),
    ('7b6fda25-6ab2-4bac-a1b6-dab9ed7db5ca','mass of fuel used','kg',''),
    ('e770581e-3080-4b2e-a1ec-cf9aa78377b8','nitrogen oxides emissions tier T4N for hp < 750','kg/hp*h',''),
    ('23135e1c-92ca-4879-83f9-71bcf95dea7f','EcoSpold01Allocation_undefined_99','','undefined allocation 99 used in EcoSpold01 datasets'),
    ('810a2bc2-0de1-4332-89aa-eafdbe6fc932','mass concentration, chloride','kg/m3',''),
    ('ed2901df-615b-45bf-b5f3-2cf778a3d446','nitrogen oxides emissions tier T2-T3-T4-T4N for hp < 175','kg/hp*h',''),
    ('17b88d93-a3f3-48ae-8c77-650de3a251af','capacity, cargo','TEU',''),
    ('2382a305-44cb-479c-a43d-f759f7689a9d','concentration, cadmium','kg/kg',''),
    ('c5254bc1-7e74-4f1e-8921-80b338e2e6d7','amount of exchange in liters 3','l',''),
    ('9d8c0443-026b-43a8-aed1-fc43b49f0afb','amount of exchange in liters 1','l',''),
    ('fa091783-9951-4372-9150-35160f716a71','EcoSpold01Allocation_other_15','','other allocation 15 used in EcoSpold01 datasets'),
    ('a2253bbc-db70-4027-a460-2c56b53e0018','EcoSpold01Allocation_other_38','','other allocation 38 used in EcoSpold01 datasets'),
    ('49f298b4-6e60-42cf-ac6d-5777329a91df','fuel input in physical units, kg','kg',''),
    ('7cfec3bb-0507-4d1d-a025-fc88450cef2b','batch water','kg',''),
    ('8d27623b-147c-44e8-93cc-2183eac22991','mass concentration, manganese','kg/m3','Mass concentration of Manganese.    (CAS 007439-96-5)'),
    ('e4f645c2-c697-4d47-8736-f0b41a80c65e','EcoSpold01Allocation_undefined_88','','undefined allocation 88 used in EcoSpold01 datasets'),
    ('a622d668-8a3f-4a61-9577-a818b4ccbffc','input','l',''),
    ('6a0ca084-7700-4acb-8ba8-5c8d10c50f59','EcoSpold01Allocation_physical_4','','physical allocation 4 used in EcoSpold01 datasets'),
    ('eb54c995-48cc-49d1-979a-8c1a52deda79','chromium, fraction','',''),
    ('7b949c3e-35d1-48c6-8ae5-10b92368de6d','carbon monoxide emissions tier T4-T4N for hp < 750','kg/hp*h',''),
    ('4d06b121-d603-405e-a064-8b39e0ceceaa','nitrogen oxides emissions tier T4 for hp < 750','kg/hp*h',''),
    ('decbd998-dc69-4964-9f82-8b9d9ca93e91','mass concentration, oxygen','kg/m3','Mass concentration of Oxygen.    '),
    ('c9d84209-913c-4902-bffe-798448407898','EcoSpold01Allocation_undefined_84','','undefined allocation 84 used in EcoSpold01 datasets'),
    ('21fe24bc-edf6-4bb6-a71a-30e643781253','EcoSpold01Allocation_undefined_87','','undefined allocation 87 used in EcoSpold01 datasets'),
    ('d938c38f-1e5a-4e41-9412-e3bf0f0cc610','EcoSpold01Allocation_undefined_144','','undefined allocation 144 used in EcoSpold01 datasets'),
    ('7a3978ea-3e26-4329-bc8b-0915d58a7e6f','true value relation','dimensionless','property to calculate "true value" from'),
    ('546af016-497a-48a5-93e0-4a39bf33b7fb','carbon monoxide emissions tier T1-T2 for hp < 50','kg/hp*h',''),
    ('f767b36f-62bf-4458-b694-ecbefd2ab970','nickel content','dimensionless','nickel content on a dry matter basis'),
    ('62403f62-04a4-4089-b27d-f31c0f00d092','EcoSpold01Allocation_undefined_61','','undefined allocation 61 used in EcoSpold01 datasets'),
    ('6cc518c8-4769-40df-b2cf-03f9fe00b759','mass concentration, zinc','kg/m3','Mass concentration of Zinc.    (CAS 007440-66-6)'),
    ('d8364dfc-5753-4585-bf50-4d42b126f72d','iron content','dimensionless','iron content on a dry matter basis'),
    ('8cd87c78-b43c-41be-9dfa-6dcc15bcb3c9','protein content','dimensionless',''),
    ('7f205d52-d991-4d52-bb79-ed4798ca6e8c','carbon monoxide emissions tier T1-T2-T3B-T4A for hp <100','kg/hp*h',''),
    ('0fdc85f3-b7e0-4d20-bc52-f758761a1645','ratio of total particulates less than 2.5 microns','',''),
    ('4fa5130c-9ff7-4a05-8941-cbe85266294f','dysprosium content','dimensionless','dysprosium content on a dry matter basis'),
    ('1fbe4632-378a-43ce-a51c-58e1d133289b','mass concentration, bicarbonate','kg/m3',''),
    ('dc473aa5-c182-4e3b-90cf-93c470ca3f43','amount in multioutput activity_m','m',''),
    ('f555cb34-c896-4f5f-986b-573ae7c7e5da','EcoSpold01Allocation_other_18','','other allocation 18 used in EcoSpold01 datasets'),
    ('eedc98e4-11cd-4863-b1c5-5bbcc0cb7210','carbon monoxide emissions tier T2-T3-T4-T4N for hp < 600','kg/hp*h',''),
    ('0f5f7900-dedf-4c0c-a9a8-d8216c51243a','polyurethane content','dimensionless','fraction of oven dry mass'),
    ('9f7de17b-15e2-4772-b847-62192a8abdbd','EcoSpold01Allocation_undefined_26','','undefined allocation 26 used in EcoSpold01 datasets'),
    ('991c0653-1319-472b-8599-15da358b81e5','EcoSpold01Allocation_other_45','','other allocation 45 used in EcoSpold01 datasets'),
    ('00f02f43-6bb3-41d0-8493-ec203c3497eb','concentration of amount 2','dimensionless',''),
    ('80b802e4-85e4-4eae-aa79-69e9e2afb66e','nitrogen oxides emissions tier T2 for hp < 11','kg/hp*h',''),
    ('0b686a86-c506-4ad3-81fd-c3f39f05247d','mass concentration, vanadium','kg/m3','Mass concentration of Vanadium.    (CAS 007440-62-2)'),
    ('4e03eb8c-2993-40a4-a1a1-d3806db4406b','width, internal','m',''),
    ('f4c39daf-a980-48ec-a45b-54e8ebd2bed8','EcoSpold01Allocation_other_90','','other allocation 90 used in EcoSpold01 datasets'),
    ('0d632a6f-3bd4-4887-834b-bc887cb3a687','fuel input in physical units m3','m3',''),
    ('2fae93f0-1697-4ebe-a0c3-7b67bbb4d3f7','nitrogen oxides emissions tier T0 for hp < 11','kg/hp*h',''),
    ('9e2b3e28-796d-4d54-a54f-f6c1da1b5891','nitrogen oxides emissions tier T2-T3-T4-T4N for hp < 600','kg/hp*h',''),
    ('7de04612-7740-43a3-8740-bb0cfe45e52f','EcoSpold01Allocation_undefined_10','','undefined allocation 10 used in EcoSpold01 datasets'),
    ('89132086-b060-446b-98f0-e1aafb1312cf','nitrogen oxides emissions tier T0 for hp >= 100','kg/hp*h',''),
    ('995265a2-f2cb-4c12-a961-766eb34392b9','strontium content','dimensionless','strontium content on a dry matter basis'),
    ('9a08745d-e89e-477c-81a9-2ea81a44547c','concentration, copper','kg/kg',''),
    ('ad9d20d9-6a7c-450f-99b5-bfe21d720ee7','dinitrogen monoxide factor','kg/GJ',''),
    ('9dbeef2f-8d64-4c5a-86bb-8fa8ead229d2','carbon monoxide emissions tier T0 for hp < 25','kg/hp*h',''),
    ('67da83f9-a3de-4167-aed7-d26c01a0d054','UVEK_link_3','dimensionless',''),
    ('9676ed7d-a99c-40ed-9ff5-55081521ad8b','EcoSpold01Allocation_undefined_8','','undefined allocation 8 used in EcoSpold01 datasets'),
    ('3f469e9e-267a-4100-9f43-4297441dc726','COD, mass per volume','kg/m3','Chemical Oxygen Demand as O2'),
    ('61c2bb4e-3ad9-4489-bfce-14f67c31bc13','EcoSpold01Allocation_other_28','','other allocation 28 used in EcoSpold01 datasets'),
    ('6d4c39b3-4b5b-4d44-87dc-f7cf1e26a5ec','gross energy, feed per kg of dry mass','MJ/kg',''),
    ('e50220ad-77c2-41c6-9c4f-a4c99b5b633c','EcoSpold01Allocation_undefined_116','','undefined allocation 116 used in EcoSpold01 datasets'),
    ('ed52f355-d88d-4f6a-97ae-36de83cdaa6a','EcoSpold01Allocation_undefined_157','','undefined allocation 157 used in EcoSpold01 datasets'),
    ('6c393aad-7741-49f7-b407-61cd667cb86c','EcoSpold01Allocation_undefined_55','','undefined allocation 55 used in EcoSpold01 datasets'),
    ('630eb01c-d5ad-45b2-896f-9228a893e6d8','mass concentration, erbium','kg/m3','Mass concentration of Erbium.    (CAS 007440-52-0)'),
    ('062724be-7a9d-45a7-818d-322385e8f5f3','mass concentration, carbonate','kg/m3',''),
    ('52178bb1-123f-476f-b87b-0b0b220da342','EcoSpold01Allocation_undefined_98','','undefined allocation 98 used in EcoSpold01 datasets'),
    ('0ef3eed0-eca7-4d37-b474-e9beee14dfe9','calculation property, nacelle, kg','kg','Mass of nacelle materials in the 1.5MW turbine.  For use in mathematical relations.'),
    ('16592e34-982c-47b8-b9cf-a4b71ec9214e','mass concentration, carbonic acid','kg/m3',''),
    ('3cfb9179-6e58-4cf6-b0fb-3a853eaea89e','concentration','dimensionless',''),
    ('98f985da-d0b2-4325-af0c-9e421a2ba950','mass concentration, palladium','kg/m3','Mass concentration of Palladium.    (CAS 007440-05-3)'),
    ('253644d1-9ec6-4373-bda4-afbdd248d5b1','concentration, zinc','kg/kg',''),
    ('0d24d7d1-87b9-4575-924a-5964c4c50edd','amount from semichemical fluting production in kg','kg',''),
    ('8b49eeb7-9caf-4101-b516-eb0aef30d530','mass concentration, potassium','kg/m3','Mass concentration of Potassium.    (CAS 007440-09-7)'),
    ('4bf06399-d2f5-4f9a-98f6-bde57e0afd4d','amount 2 of flow in kg','kg',''),
    ('706d9439-c660-47d8-a3ea-088800b65910','used oil fraction emitted to soil','dimensionless',''),
    ('aa897226-0a91-40e5-aa05-4bae3b9e4213','mass concentration, molybdenum','kg/m3','Mass concentration of Molybdenum.    (CAS 007439-98-7)'),
    ('7fc0f949-7d08-4c6d-ab6a-2b82e6e50330','fluoranthene content','dimensionless',''),
    ('cf3f0fc4-84e7-45af-b082-b352b88ff15a','carbon monoxide emissions tier T1-T2-T4A-T4B for hp < 11','kg/hp*h',''),
    ('2452d3a4-7e76-4505-a62e-eeb514630ead','EcoSpold01Allocation_other_35','','other allocation 35 used in EcoSpold01 datasets'),
    ('d6594289-53bd-4e09-9d95-1ee65edc6659','EcoSpold01Allocation_undefined_133','','undefined allocation 133 used in EcoSpold01 datasets'),
    ('84916b80-bf93-4e20-9b7c-593aa9518d09','tungsten content','dimensionless','tungsten content on a dry matter basis'),
    ('bdfb2f07-5ec0-4c49-93c5-0e532c1b4a0f','EcoSpold01Allocation_undefined_66','','undefined allocation 66 used in EcoSpold01 datasets'),
    ('9c38ea07-adcd-4018-8636-eb32382f39a7','EcoSpold01Allocation_undefined_5','','undefined allocation 5 used in EcoSpold01 datasets'),
    ('cd180116-c2dd-4bb5-ad91-60e8aaade2dc','nitrogen oxides emissions tier T2-T4A-T4B for hp < 25','kg/hp*h',''),
    ('20c6f95d-f952-431e-ac28-ac47155a16e7','EcoSpold01Allocation_other_56','','other allocation 56 used in EcoSpold01 datasets'),
    ('883a9dc6-bbb5-418c-8d6e-7031e96028ef','organic carbon content','dimensionless',''),
    ('7c69446b-efb9-46e2-a4da-a12b78ca6395','carbon monoxide emissions tier T2-T3B-T4-T4A-T4N for hp < 100','kg/hp*h',''),
    ('bfe72a17-59bb-4529-957d-6a769c8ce324','kgFuel_Input','kg',''),
    ('0c75f510-65f5-4ea5-9bb9-66bebe529337','UVEK_link_2','dimensionless',''),
    ('1e4ef691-c7d3-49fc-9aee-6d77575a7b8a','mass concentration, dissolved sulfate SO4 as S','kg/m3','Mass concentration of dissolved sulfate SO4 (CAS 014808-79-8) as S. Note that dissolved and particulate S are optional yet desirable specifications of total sulfur.'),
    ('75e905a0-5ea1-48dc-af7f-88da015169b8','EcoSpold01Allocation_other_132','','other allocation 132 used in EcoSpold01 datasets'),
    ('4f461b9d-5a7b-4a46-8803-23f6df0dc522','mass concentration, dissolved nitrate NO3 as N','kg/m3','Mass concentration of dissolved nitrate NO3 (CAS 014797-55-8) as N. Note that dissolved and particulate N are optional yet desirable specifications of total nitrogen.'),
    ('99779f35-bd0d-41cd-82b6-281a85c6da0e','EcoSpold01Allocation_undefined_161','','undefined allocation 161 used in EcoSpold01 datasets'),
    ('f4818ed4-60c8-4d60-803f-be896e24ce99','carbon monoxide emissions tier T2-T4-T4N for hp >= 750','kg/hp*h',''),
    ('94b2be61-35f2-40fb-b9ab-636ae5a0415b','lanthanum content','dimensionless','lanthanum content on a dry matter basis'),
    ('be5dfbaa-19eb-4f09-adf1-3fded678ab01','Slope Factor','dimensionless',''),
    ('4688b15a-1220-4cb1-86bf-d4c9d6b23760','nitrogen oxides emissions tier T2-T3-T4-T4N for hp >= 600','kg/hp*h',''),
    ('15e75e26-3799-4c24-acef-9873a0b4342e','filter dust to recycling','kg',''),
    ('63eb8a6c-2447-462f-a65a-877d9be3da04','low calorific value','MJ/kg',''),
    ('38836621-9b7d-43dc-bf7f-467fca9acefa','EcoSpold01Allocation_physical_14','','physical allocation 14 used in EcoSpold01 datasets'),
    ('aac3d6fa-9551-46dc-a6bb-f36e338d5fca','EcoSpold01Allocation_other_24','','other allocation 24 used in EcoSpold01 datasets'),
    ('30f0aa15-2d50-4f09-af94-683b6dd68adc','arsenic content','dimensionless','arsenic content on a dry matter basis'),
    ('cbda3750-136f-40e9-a4db-0e6af46fecad','SAM_activityLink_2','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('d1fd6996-a265-45b6-8acd-339346beb003','width, external','m',''),
    ('56a4a73c-8f3c-4cf3-aaec-07be01672ec1','EcoSpold01Allocation_undefined_118','','undefined allocation 118 used in EcoSpold01 datasets'),
    ('1111ac7e-20df-4ab4-9e02-57821894372c','mass concentration, cadmium','kg/m3','Mass concentration of Cadmium.    (CAS 007440-43-9)'),
    ('eb8b2ca3-c5a8-4297-8a02-e068fb012a75','EcoSpold01Allocation_undefined_93','','undefined allocation 93 used in EcoSpold01 datasets'),
    ('50f1fc5b-3cab-432f-933c-341f91f6fe00','EcoSpold01Allocation_undefined_117','','undefined allocation 117 used in EcoSpold01 datasets'),
    ('bcd5fb37-3734-4b83-a22c-ec677e26f929','EcoSpold01Allocation_undefined_25','','undefined allocation 25 used in EcoSpold01 datasets'),
    ('0d5e8e13-4064-4e0b-b6a8-164149392621','regional dataset numerical value','dimensionless',''),
    ('7a555ebd-d9f6-467d-8753-edb2f6a98fe8','EcoSpold01Allocation_other_113','','other allocation 113 used in EcoSpold01 datasets'),
    ('9b950fc7-7379-4bdd-a53e-55806d601125','EcoSpold01Allocation_other_128','','other allocation 128 used in EcoSpold01 datasets'),
    ('fea328b8-4c94-4fed-8ccd-b277a7d1052b','EcoSpold01Allocation_undefined_115','','undefined allocation 115 used in EcoSpold01 datasets'),
    ('c99b7922-406a-4a2a-a5b5-cdc46b14ce2e','EcoSpold01Allocation_other_44','','other allocation 44 used in EcoSpold01 datasets'),
    ('65978016-5946-400f-9645-068280b4db0a','carbon monoxide emissions tier T1 for hp < 600','kg/hp*h',''),
    ('a72ff647-4e06-4418-b93e-34722c87d9a7','amount of exchange in MJ 1','MJ',''),
    ('9e2e8cd4-4f88-4c9c-a13e-4da2e37b27ce','carbon monoxide emissions tier T4-T4N for hp < 600','kg/hp*h',''),
    ('ffc1bcb9-0495-41a7-8b92-bd89cebfc814','nitrogen oxides emissions tier T0 for hp < 100','kg/hp*h',''),
    ('b9318792-45aa-407e-bf7d-150f5f878dd2','global dataset numerical value','dimensionless',''),
    ('b15297c5-5708-4ca2-9888-d455470f475c','EcoSpold01Allocation_undefined_54','','undefined allocation 54 used in EcoSpold01 datasets'),
    ('807a3833-37fa-4606-9023-25d4e9eb0158','mass concentration, caesium','kg/m3','Mass concentration of Caesium.    (CAS 007440-46-2)'),
    ('284c739e-be5f-4429-ab95-28f6dd710c4c','total polycyclic aromatic hydrocarbon content','dimensionless','content of total Polycyclic Aromatic Hydrocarbons (PAHs) on a dry mass basis'),
    ('c87bbc61-0fb1-4d7d-83e0-b5a44c6531ec','EcoSpold01Allocation_undefined_97','','undefined allocation 97 used in EcoSpold01 datasets'),
    ('d23caec2-9ca7-4042-a814-056f266e1e28','EcoSpold01Allocation_other_92','','other allocation 92 used in EcoSpold01 datasets'),
    ('878b9555-5b48-4be5-8a8b-e1cd408e880c','fibre (total dietary) content','kg',''),
    ('95b6afca-3c52-4db9-a5ec-194322f44408','working time','hour',''),
    ('4fb17587-2c03-4b4e-b38b-867cfd4bfae8','praseodymium content','dimensionless','praseodymium content on a dry matter basis'),
    ('d445b2d3-d259-423c-b027-7a133e1def80','EcoSpold01Allocation_other_46','','other allocation 46 used in EcoSpold01 datasets'),
    ('d61b8768-8ef6-4a99-ae16-9e51f24ad5b5','heating value, gross','MJ','gross (upper) heating (calorific) value'),
    ('b321f120-4db7-4e7c-a196-82a231023052','mass concentration, arsenic','kg/m3','Mass concentration of Arsenic.    (CAS 007440-38-2)'),
    ('fde57f9e-6fa5-4936-80a9-5b2bc1e5fd0b','yearly output','kg',''),
    ('434365cb-7be0-4674-b17b-ee4a9188b697','EcoSpold01Allocation_undefined_138','','undefined allocation 138 used in EcoSpold01 datasets'),
    ('28a73d20-406b-4feb-875f-3efbe7261aae','EcoSpold01Allocation_undefined_64','','undefined allocation 64 used in EcoSpold01 datasets'),
    ('35d16e49-9e29-4e1d-ac22-ea7f84fb76e1','mass concentration, gallium','kg/m3','Mass concentration of Gallium.    (CAS 007440-55-3)'),
    ('6b443a06-9cd3-4cb1-9a95-beaf31a11b9e','fraction between 2.5 and 10 microns','dimensionless',''),
    ('3f0217f2-0db6-4dfd-a5a6-8b50510328bd','nitrogen oxides emissions tier T1 for hp >= 750','kg/hp*h',''),
    ('d8d0d9e1-d98a-4adb-ad4d-de0bb2a1deb3','mass concentration, rhodium','kg/m3','Mass concentration of Rhodium.    (CAS 007440-16-6)'),
    ('e7451d8a-77af-44e0-86cf-ccd17ac84509','mass concentration, copper','kg/m3','Mass concentration of Copper.    (CAS 007440-50-8)'),
    ('2bc683e4-3780-4f00-8c1d-fd53e05cfde7','manganese content','dimensionless','manganese content on a dry matter basis'),
    ('a087148d-59f3-49ab-af35-66cda7e5e93d','nitrogen oxides emissions tier T0 for hp < 25','kg/hp*h',''),
    ('8a03c256-74ed-46b9-b8f6-39f907874a61','carbon monoxide emissions tier T0 for hp < 50','kg/hp*h',''),
    ('f6383e22-5ce5-47ae-92b2-10298dc92d7c','SAM_activityLink_9_scaling_factor','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('7913a35d-5838-4735-bd12-385408f700d0','amount 7 of flow in kg','kg',''),
    ('ed10c0cd-2920-4ace-bc7c-ba53ad7ddf84','EcoSpold01Allocation_other_22','','other allocation 22 used in EcoSpold01 datasets'),
    ('95b0aa67-9732-4444-902d-2b4c44998dec','UVEK_absolute_amount_2','dimensionless',''),
    ('4f98e802-4747-40e1-a886-4d6148cdf850','amount of flow 1 in kg','kg',''),
    ('1e32cfb3-9060-43fb-94f4-6977f03bb85d','SAM_activityLink_8','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('da1ed753-c185-4631-9cec-45d09fcec8f4','mass concentration, argon','kg/m3','Mass concentration of Argon.    (CAS 007440-37-1)'),
    ('fbc58d8d-0a4c-4eb0-a14a-fafef222bafc','lutetium content','dimensionless','lutetium content on a dry matter basis'),
    ('7d3c701a-e10d-4d29-87b8-267dd8d41927','EcoSpold01Allocation_undefined_9','','undefined allocation 9 used in EcoSpold01 datasets'),
    ('dba83ee6-9127-4c81-86c9-15e29987dcdf','vanadium content','dimensionless','vanadium content on a dry matter basis'),
    ('e7d14d44-9cda-4912-ac5c-4771ab7a0fcb','amount in multioutput activity_km','km',''),
    ('3a99e603-c18f-4832-a6d6-97d980c7fcea','amount of exchange 1','kg',''),
    ('d9bc2a4f-fe69-4fa9-9ad9-f3a8e0572cff','Erodibility factor','dimensionless','Erodibility factor [t h MJ-1 mm-1]. The erodibility of a soil corresponds to the difference in the eroded soil quantity between two soils under the same conditions (same rainfall, same slope, etc.) due to soil properties. It'),
    ('c2d8bd45-452a-4318-b841-cccdc7049829','EcoSpold01Allocation_other_2','','other allocation 2 used in EcoSpold01 datasets'),
    ('ed62dbf5-82e7-4432-ac6a-9be3172c41fd','mass concentration, gadolinium','kg/m3','Mass concentration of Gadolinium.    (CAS 007440-54-2)'),
    ('e3c6bebb-7017-44d3-b22f-fe48987fbaa0','EcoSpold01Allocation_physical_9','','physical allocation 9 used in EcoSpold01 datasets'),
    ('6e8e2e10-1f25-4c3a-86ab-502527befa39','carbon monoxide emissions tier T2-T4-T4A for hp < 50','kg/hp*h',''),
    ('0593a28f-a9d7-4dfd-85a7-bcf79cea50eb','SAM_activityLink_7_scaling_factor','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('ed9ccf89-0acb-4097-8f74-867ed82f5fd0','fraction, origin: salt water','dimensionless','This property represent the fraction of the amount of the exchange which origin is salt water.'),
    ('9f2ce7cd-fc18-492c-ba71-c63c237e3698','EcoSpold01Allocation_physical_7','','physical allocation 7 used in EcoSpold01 datasets'),
    ('081906a6-216f-464d-ab5f-a767a2b536bc','EcoSpold01Allocation_undefined_139','','undefined allocation 139 used in EcoSpold01 datasets'),
    ('405bdcc4-b4bb-45f6-81f7-e9b8bf6407f5','nitrogen oxides emissions tier T1-T2 for hp < 25','kg/hp*h',''),
    ('864f80ba-e9b3-45b5-a45b-2d5224c40487','EcoSpold01Allocation_other_27','','other allocation 27 used in EcoSpold01 datasets'),
    ('a9358458-9724-4f03-b622-106eda248916','water content','dimensionless','water content on a dry matter basis'),
    ('0132d97c-5f19-4397-9197-59ab801b10cf','copper content','dimensionless','copper content on a dry matter basis'),
    ('6e79b548-79d9-4068-b13c-0f77fa590478','EcoSpold01Allocation_other_99','','other allocation 99 used in EcoSpold01 datasets'),
    ('9adea776-5feb-432f-8f16-34d78ed99306','mass concentration, platinum','kg/m3','Mass concentration of Platinum.    (CAS 007440-06-4)'),
    ('4af77686-dcdd-4a5c-bfc4-a4eac0ab3f62','EcoSpold01Allocation_undefined_52','','undefined allocation 52 used in EcoSpold01 datasets'),
    ('a666085f-0157-4d46-abc2-a41c10e98a88','chromium layer thickness','m',''),
    ('e07a2fd9-0416-4c56-b9ea-45a3348f7494','EcoSpold01Allocation_other_131','','other allocation 131 used in EcoSpold01 datasets'),
    ('e8208ea6-40a7-45f7-9bd0-ac6bbca3aefd','concentration of amount 4','dimensionless',''),
    ('7050b4bb-1cdb-4fe3-91fd-21862c6be5cd','nitrogen oxides emissions tier T0-T1 for hp >= 100','kg/hp*h',''),
    ('7a6ab142-7599-49a1-8ce9-61ce26f37769','EcoSpold01Allocation_undefined_90','','undefined allocation 90 used in EcoSpold01 datasets'),
    ('9a89a755-a662-449e-beaf-886212ca1ef2','fuel consumption tier T0-T1-T2-T3-T4-T4N for hp >= 100','kg/hp*h',''),
    ('20a573bd-dd63-4957-951c-e32f73e487ff','EcoSpold01Allocation_undefined_147','','undefined allocation 147 used in EcoSpold01 datasets'),
    ('144b7189-5b7f-41f2-b823-b90fa553900f','EcoSpold01Allocation_undefined_171','','undefined allocation 171 used in EcoSpold01 datasets'),
    ('109c5b60-1da5-4be6-9076-b9b14fe97f6b','corresponding fuel use, natural gas','MJ','Lower heating value of the fuel input related to the heat/electricity output'),
    ('d7e67353-7adc-4e68-9c68-8a5bee2233f7','EcoSpold01Allocation_undefined_42','','undefined allocation 42 used in EcoSpold01 datasets'),
    ('f463eabb-a48e-48fa-a00c-ca661b91f476','active membrane surface per module unit','m2',''),
    ('64d9c14d-3dce-41de-bd87-2c8520e3f6d6','EcoSpold01Allocation_other_47','','other allocation 47 used in EcoSpold01 datasets'),
    ('c74c3729-e577-4081-b572-a283d2561a75','carbon content, fossil','dimensionless','fossil carbon content on a dry matter basis'),
    ('f8bff3e1-a9ee-4165-a4ab-82e783a1c3fc','EcoSpold01Allocation_undefined_123','','undefined allocation 123 used in EcoSpold01 datasets'),
    ('6c113912-2ae5-4dea-99ea-1f0ebfe39c31','mass concentration, tantalum','kg/m3','Mass concentration of Tantalum.    (CAS 007440-25-7)'),
    ('959b298e-1f02-4728-a118-68c2c4d70958','MARKET_OVERWRITE_PV_CUTOFF','dimensionless','Defines the new production volume amount of its exchange to be used in linking of the market for the cut-off system model.'),
    ('4d205f54-5f33-455c-a2bb-4650f1755e74','capacity','kWp','capacity of photovoltaic cells in kWp.'),
    ('4cf2bf35-aef7-4e83-a2e0-5640e0724a7d','carbon monoxide emissions tier T2-T3-T4-T4N for hp < 750','kg/hp*h',''),
    ('f863a012-aa6f-4d46-a954-97683346175f','EcoSpold01Allocation_other_84','','other allocation 84 used in EcoSpold01 datasets'),
    ('e8851fdc-aa2e-4468-b1ec-c23287af25d7','EcoSpold01Allocation_undefined_44','','undefined allocation 44 used in EcoSpold01 datasets'),
    ('adc73a30-b0fd-4c98-972f-fe0fdf7efe4e','carbon monoxide emissions tier T2-T4A-T4B for hp < 11','kg/hp*h',''),
    ('db2e27d1-47cd-4180-8416-4f79369de00c','EcoSpold01Allocation_undefined_6','','undefined allocation 6 used in EcoSpold01 datasets'),
    ('fb981a3e-2361-494b-957b-cd041c483c77','value per m of bi-metal cable','dimensionless',''),
    ('7f9ab53b-437c-40d7-8e8c-bebe1a01fb13','mass of a straw bale','kg',''),
    ('2f38f10d-a26d-436c-8984-7549d556e8b5','EcoSpold01Allocation_undefined_96','','undefined allocation 96 used in EcoSpold01 datasets'),
    ('bf6f662d-f9f1-4deb-b77d-51a6622402f3','MARKET_OVERWRITE_PV_APOS','dimensionless','Defines the new production volume amount of its exchange to be used in linking of the market for the APOS system model.'),
    ('2903bca6-1b3d-4ac5-87a4-b6701cfbbe42','consequential','','set to 1 for conditional exchanges to be used in consequential system model only'),
    ('168cb9d2-937c-4e9e-b942-b6d5c8227a50','concentration of solution','dimensionless',''),
    ('dd13a45c-ddd8-414d-821f-dfe31c7d2868','BOD5, mass per volume','kg/m3','Biological Oxygen Demand BOD5, as O2'),
    ('d8074a22-bdf0-4236-afa9-e76db339c3e6','EcoSpold01Allocation_other_34','','other allocation 34 used in EcoSpold01 datasets'),
    ('fe9f0d92-ecdf-4e72-bd20-fadd3b6175bf','germanium content','dimensionless','germanium content on a dry matter basis'),
    ('1a6c78a7-26c7-4ab2-a37d-2263b61ec22b','EcoSpold01Allocation_undefined_165','','undefined allocation 165 used in EcoSpold01 datasets'),
    ('6a158827-67f6-4c5e-ba04-3da10718fc21','mass concentration, niobium','kg/m3','Mass concentration of Niobium.    (CAS 007440-03-1)'),
    ('65c24baa-9097-4a84-a0fc-794923c31676','EcoSpold01Allocation_undefined_156','','undefined allocation 156 used in EcoSpold01 datasets'),
    ('7d0f119e-cbf4-451f-acc8-c14a4b9e72f9','EcoSpold01Allocation_other_114','','other allocation 114 used in EcoSpold01 datasets'),
    ('5dfc918a-0a0f-4bd5-a77c-ae3eb109fae7','transport distance','km',''),
    ('6e55762f-cd48-4b35-84d6-f7ad2e862f01','concentration of amount 6','dimensionless',''),
    ('c50751b6-e31f-473b-af99-664ad2ad6185','conversion factor kg to MJ','','Used to remove duplicate conversion datasets'),
    ('93bfda45-49f5-44bd-beb0-91b38dde4035','lifetime capacity [h]','hour','Total of operation hours expected; in case of forest machinery: total of productive machine hours.'),
    ('b0a4d18f-2eb1-4f63-96b3-b8ea31a42bb3','exergy','MJ','allocation factor for electricity (=1) vs. heat, where heat is calculated as the termodynamic mean temperature Tm = (Tfeed-Treturn)/ln(Tfeed/Treturn), relative to the application temperature (Tu, typically = 293 K), i.e. (Tm-Tu)/Tm'),
    ('0e73547d-0c62-48eb-9dca-d1c23d49c69d','EcoSpold01Allocation_undefined_20','','undefined allocation 20 used in EcoSpold01 datasets'),
    ('33c8d745-bc56-4705-baf0-cf6e6fda1956','fuel consumption tier T0-T1-T2-T3B-T4-T4A-T4N for hp < 100','kg/hp*h',''),
    ('a301a838-7975-4d89-9e74-8eb77ad03cd1','carbon content','dimensionless','carbon content on a dry matter basis (reserved; not for manual entry)'),
    ('ff7e0d7f-18bd-4f6c-887f-d779f3f0ed65','methane factor','kg/GJ',''),
    ('dd7e15dc-c438-43f7-9c0d-d0a627163cf1','silicon content','dimensionless','silicon content on a dry matter basis'),
    ('b1533882-7797-46d6-bfe3-77ef200d1227','total surface','m2',''),
    ('7e13079e-2728-41e8-a9af-b173dceaddac','Quebec production volume','kg',''),
    ('7feedb5e-96f4-4adf-a107-ba2096f05ec3','humus equivalent','kg','Humus building fraction expressed in kg per kg product on a FM basis. Humus denotes the converted, primary biomass from plants or animals in the ground. More information can be found in the documentation of the composting itself: "treatment of biowaste, industrial composting".  '),
    ('b62bf4de-86a1-4648-8623-c553991c7dc9','EcoSpold01Allocation_other_83','','other allocation 83 used in EcoSpold01 datasets'),
    ('f8a0423a-2b51-41e2-a98e-ec17597f6233','chromium layer reference thickness','m',''),
    ('246d7910-43ad-4505-91e1-21d1c0d7c784','EcoSpold01Allocation_undefined_22','','undefined allocation 22 used in EcoSpold01 datasets'),
    ('85022ccb-e5d3-4865-8730-89334b8cd6e7','fuel input in physical units, m3, natural gas','m3',''),
    ('e59c55b1-f643-49bb-9af9-5fc992c06a8f','EcoSpold01Allocation_other_97','','other allocation 97 used in EcoSpold01 datasets'),
    ('d4eb6078-d96f-4410-bb1d-cbf456c765ff','EcoSpold01Allocation_undefined_143','','undefined allocation 143 used in EcoSpold01 datasets'),
    ('1eee9a63-ae11-4351-9bad-e7251772cb6e','tcdd equivalents','dimensionless',''),
    ('539447de-c9c8-4834-a23f-d3c8568b8ae2','EcoSpold01Allocation_other_66','','other allocation 66 used in EcoSpold01 datasets'),
    ('f69a7705-e7e5-4f97-a971-ca2b3ccc9d7d','EcoSpold01Allocation_other_121','','other allocation 121 used in EcoSpold01 datasets'),
    ('c17faa2d-28c9-4a59-825d-88d11be40ddb','mass per seed','kg',''),
    ('a7e81e5c-d3b9-421c-bf6f-7cafcf911ab7','mass concentration, europium','kg/m3','Mass concentration of Europium.    (CAS 007440-53-1)'),
    ('ff13a5f2-9270-42ff-8382-740d57bfa05c','EcoSpold01Allocation_other_110','','other allocation 110 used in EcoSpold01 datasets'),
    ('01232ebc-8511-4da3-a1e6-267172e6f155','EcoSpold01Allocation_other_104','','other allocation 104 used in EcoSpold01 datasets'),
    ('5b7203d0-4a12-43e3-a2de-d9000584a5c6','mass concentration, yttrium','kg/m3','Mass concentration of Yttrium.    (CAS 007440-65-5)'),
    ('bca5eb23-9baa-4711-81f8-1e03d96c8102','volume of fuel used','l',''),
    ('0bdc13c6-4654-4548-bc4d-8b7458eeda42','length','km','length'),
    ('e4504511-88b5-4b01-a537-e049f056668c','mass concentration, bromine','kg/m3','Mass concentration of Bromine.    (CAS 007726-95-6)'),
    ('6bc8ac5e-cc4c-45fb-93dc-53c0e45091df','energy content','MJ','as gross calorific value (when relevant)'),
    ('b9bf7cb7-c8aa-4ae2-b679-6bad82feefc6','UVEK_absolute_amount2','dimensionless',''),
    ('ad626ff0-146c-48d1-98d6-8c490390e001','EcoSpold01Allocation_other_68','','other allocation 68 used in EcoSpold01 datasets'),
    ('0ccb96ff-84a4-4523-b559-dc6e98e59765','EcoSpold01Allocation_undefined_53','','undefined allocation 53 used in EcoSpold01 datasets'),
    ('73f50e9b-11aa-4ca5-b324-2597edfeaa65','mass concentration, francium','kg/m3','Mass concentration of Francium.    (CAS 007440-73-5)'),
    ('e06ea4a9-b99c-4ff6-86e2-17fa351ac134','N content','',''),
    ('a4607feb-b8df-4a6e-9a0f-e70088695bc4','EcoSpold01Allocation_other_54','','other allocation 54 used in EcoSpold01 datasets'),
    ('59d2bb6c-51c7-4751-bda0-6d435a69f3fe','amount of refractory material sent to landfill','kg',''),
    ('b41681b0-87c1-4333-8eae-045ec68fe0c2','mass concentration, thorium','kg/m3','Mass concentration of Thorium.    (CAS 007440-29-1)'),
    ('a547f885-601d-4d52-9bf9-60f0cef06269','mass concentration, TOC','kg/m3','Mass concentration of Total Organic Carbon'),
    ('2ae5ee8a-cb80-4ee5-848c-ad5357c6e7df','occupation period','year',''),
    ('cbffa34c-c6de-4836-abfe-c6b94b99655a','mass concentration, indium','kg/m3','Mass concentration of Indium.    (CAS 007440-74-6)'),
    ('dbede65d-d955-4192-9f07-73ecb5e6d1ae','mass concentration, rubidium','kg/m3','Mass concentration of Rubidium.    (CAS 007440-17-7)'),
    ('406ac421-4b23-4bd0-acfe-22a44578e532','EcoSpold01Allocation_undefined_86','','undefined allocation 86 used in EcoSpold01 datasets'),
    ('511ae34f-299d-4f34-a472-d437e2ea7f7f','EcoSpold01Allocation_other_120','','other allocation 120 used in EcoSpold01 datasets'),
    ('4ca9b2ce-21bb-41a2-8c4c-19df41af0469','lower heating value MJ per kg','MJ/kg','Net calorific value'),
    ('aefe9fab-ed23-4060-a35d-d24d5281926c','lifetime capacity [l]','l','lifetime capacity in litres'),
    ('dc86ba5b-cc49-4040-9645-f6918fe919d5','nitrogen oxides emissions tier T0-T1 for hp < 100','kg/hp*h',''),
    ('ca949a93-0642-4d1d-83bf-52faf10f2329','potassium content','dimensionless','potassium content on a dry matter basis'),
    ('06b0c4fd-a90c-4b96-90f6-95829bfcab14','nitrogen oxides emissions tier T1-T2-T4A for hp <50','kg/hp*h',''),
    ('d7ba3e4c-6cb7-4186-aabf-857f533b194a','EcoSpold01Allocation_other_136','','other allocation 136 used in EcoSpold01 datasets'),
    ('c0447419-7139-44fe-a855-ea71e2b78585','mass concentration, boron','kg/m3','Mass concentration of Boron.    (CAS 007440-42-8)'),
    ('b090c679-d67b-488d-9f54-71bad1e9b1d0','nitrogen oxides emissions tier T4-T4A for hp < 100','kg/hp*h',''),
    ('f404e699-76cc-4776-a4bc-9e1a3640d851','EcoSpold01Allocation_other_25','','other allocation 25 used in EcoSpold01 datasets'),
    ('d602c01c-a9ab-4386-b9a2-b38319179d02','carbon monoxide emissions tier T1-T2 for hp < 25','kg/hp*h',''),
    ('c62a1ea1-ed3d-45e5-add2-d1dcb98843c3','nitrogen oxides emissions tier T4-T4N for hp >= 750','kg/hp*h',''),
    ('4188c979-9024-41a0-9d68-94b267a06469','gravel content','kg',''),
    ('43c83d61-7081-4faf-989b-c178034cc876','mass concentration, dysprosium','kg/m3','Mass concentration of Dysprosium.    (CAS 007429-91-6)'),
    ('953c9d29-3204-42f1-9822-2974b2dfd5a3','EcoSpold01Allocation_undefined_27','','undefined allocation 27 used in EcoSpold01 datasets'),
    ('0d873051-437e-4394-b5b8-cd82d5980873','EcoSpold01Allocation_undefined_82','','undefined allocation 82 used in EcoSpold01 datasets'),
    ('270f325c-e5f8-4084-a41e-eb9cd29114f7','net heating value, per m3','MJ/m3',''),
    ('ea0dd556-455f-4524-b594-785505f1c0af','cerium content','dimensionless','cerium content on a dry matter basis'),
    ('e5287f92-be0a-4793-bb7f-6d22108ecb4b','total PAH emission to air','kg',''),
    ('4054bfa7-dfcb-452e-b1dd-810b9e981506','antimony content','dimensionless','antimont content on a dry matter basis'),
    ('26e0e131-cb29-4602-9cce-ecaaf1ffd8d4','mass concentration, bismuth','kg/m3','Mass concentration of Bismuth.    (CAS 007440-69-9)'),
    ('42a081fd-d0d5-4832-a237-a7b94c1f9849','EcoSpold01Allocation_physical_17','','physical allocation 17 used in EcoSpold01 datasets'),
    ('bf4d71d9-4301-4939-8a9d-36d8811b7db0','beryllium content','dimensionless','beryllium content on a dry matter basis'),
    ('7919c1a2-8164-4237-8af1-af7146afb24b','nitrogen oxides emissions tier T4N for hp < 100','kg/hp*h',''),
    ('5ec6019b-0773-4119-9d96-ed9355eaad80','mass concentration, neodymium','kg/m3','Mass concentration of Neodymium.    (CAS 007440-00-8)'),
    ('467149c7-9a5f-4947-ad45-2f87fee2a9a4','molecular weight','g/mol',''),
    ('3585f881-23f9-4dad-af40-5e9406a5abfd','percentage of non associated gas','dimensionless',''),
    ('72234199-6c37-4f1d-b083-0bcf85533bfe','EcoSpold01Allocation_other_30','','other allocation 30 used in EcoSpold01 datasets'),
    ('3a09cd24-bbfd-4d01-92e8-827b2773787a','EcoSpold01Allocation_other_63','','other allocation 63 used in EcoSpold01 datasets'),
    ('aafefdf9-e3dd-499b-8a80-e31ac7012586','capacity [l/hour]','l/hour','capacity in litres per hour'),
    ('3e002aac-fa7c-47da-a6bc-cfbda96fd86c','EcoSpold01Allocation_other_67','','other allocation 67 used in EcoSpold01 datasets'),
    ('e11d1534-e491-474a-b58b-4581101c5413','thermal efficiency','dimensionless',''),
    ('15c2d120-0e15-4c4d-af91-1c25d1661764','EcoSpold01Allocation_undefined_83','','undefined allocation 83 used in EcoSpold01 datasets'),
    ('a82977cb-e7f8-4168-ae9c-96df1d45cb37','dross sent to recycling','kg',''),
    ('65262335-c534-4b5b-89ac-1f265c522325','concentration of amount 1','dimensionless',''),
    ('8175120e-a5b7-4f19-afca-5620e9e4dd8b','mass concentration, particulate sulfur','kg/m3','Mass concentration of particulate sulfur as S. Note that dissolved and particulate S are optional yet desirable specifications of total sulfur.'),
    ('48b2521b-63f6-4121-9c3f-8edef7b31fc5','rhenium content','dimensionless','rhenium content on a dry matter basis'),
    ('985e782a-0a5c-4365-bc21-1d2850fce4bf','nitrogen oxides emissions tier T0-T1 for hp < 25','kg/hp*h',''),
    ('80230db9-528a-4b9e-b06e-4f01b0920a99','total particulates > 2.5microns','kg',''),
    ('f9ee3fab-385f-460e-8459-e6046ca756fc','input_kg_recycled','kg',''),
    ('7b656e1b-bc07-41cd-bad4-a5b51b6287da','mass concentration, sodium','kg/m3','Mass concentration of Sodium.    (CAS 007440-23-5)'),
    ('cc1ba8c4-aea0-4aed-af64-0642cf5ded2b','UVEK_relative_amount_1','dimensionless',''),
    ('5e38b3ed-7208-420d-ad2e-e05bffcdd563','total particulates','kg',''),
    ('138392d1-f279-4402-a018-b619fc1e5555','weight per length','kg/m',''),
    ('65387d28-9b09-44d2-9908-663c18b740a3','ytterbium content','dimensionless','ytterbium content on a dry matter basis'),
    ('22c3e383-753d-4c96-ab4a-3b9950ef7614','amount in mass units','',''),
    ('05576542-5285-4fdf-9fcd-9d5f944b32f2','EcoSpold01Allocation_other_8','','other allocation 8 used in EcoSpold01 datasets'),
    ('7fe01cf6-6e7b-487f-b37e-32388640a8a4','mass concentration, dissolved phosphate PO4 as P','kg/m3','Mass concentration of Dissolved Phosphate PO4 as P. Note that dissolved and particulate P are optional yet desirable specifications of total phosphorous.'),
    ('f04a971d-f503-4ca0-b2b1-0ecd2e53ea61','mass concentration, nitrogen','kg/m3','Mass concentration of nitrogen (Ntot.) as N'),
    ('eefd9359-1594-45a8-be13-c581b6fee728','EcoSpold01Allocation_undefined_101','','undefined allocation 101 used in EcoSpold01 datasets'),
    ('72ca3df5-6d2a-4a64-9fdf-d976136e4167','yttrium content','dimensionless','yttrium content on a dry matter basis'),
    ('658fd514-f333-41bf-81b9-98ac015b43e9','nitrogen oxides emissions tier T1 for hp < 175','kg/hp*h',''),
    ('8fb0d413-3344-467f-8049-ea40894b32ef','clay content','dimensionless',''),
    ('3ca17519-ac5d-4242-97f7-2625ceb5b671','EcoSpold01Allocation_other_77','','other allocation 77 used in EcoSpold01 datasets'),
    ('38583c32-c20b-4553-9152-b14b0bee1e61','lifetime capacity [kg]','kg',''),
    ('26da0224-0cb4-4e78-8755-64be70cbcb52','EcoSpold01Allocation_undefined_121','','undefined allocation 121 used in EcoSpold01 datasets'),
    ('cf66b969-7413-4ee7-aaf1-8a3b47904836','concentration, nitrogen','kg/kg','nitrogen content on a fresh matter basis'),
    ('94179908-3104-4f32-9b36-5e50501e4be5','calculation property, blade, kg','kg','Mass of material used for one blade in the 1.5MW turbine.  For use in mathematical relations.'),
    ('d09fc0a7-9dc8-40fd-937e-f1ab15be47be','EcoSpold01Allocation_other_123','','other allocation 123 used in EcoSpold01 datasets'),
    ('0118cc72-f22c-45d2-8e62-dce08e1d6328','SAM_activityLink_7','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('d833299f-a606-4dad-80eb-9fac17dd0859','EcoSpold01Allocation_undefined_35','','undefined allocation 35 used in EcoSpold01 datasets'),
    ('7980069a-3764-4d47-81b0-6cd0b79cc8f6','Organic Nitrogen content of soil','kg/ha','Organic nitrogen content of soil (kgN/ha)'),
    ('ec643dfa-488c-41a8-a2da-ea00b456cde6','amount of exchange 6','kg',''),
    ('6566d7d0-af6c-4a66-a46b-34b1452dd1e9','nitrogen oxides emissions tier T1-T2-T4A-T4B for hp < 25','kg/hp*h',''),
    ('a065b4fb-9367-467c-b25c-38002016bb75','EcoSpold01Allocation_undefined_67','','undefined allocation 67 used in EcoSpold01 datasets'),
    ('121bf55b-20e5-42f2-9958-99f22982d709','solution concentration','dimensionless','Concentration in weight percentage (%w/w)'),
    ('60c3b8b2-3a2c-40c3-8eed-5247844eb153','SAM_activityLink_4_scaling_factor','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('79662bf3-7b3a-4e94-b6a6-0e6c9ae89adc','amount of exchange in m³ 1','m3',''),
    ('51dcf8a2-7ad9-4291-b7dd-f7b89849443c','EcoSpold01Allocation_undefined_76','','undefined allocation 76 used in EcoSpold01 datasets'),
    ('42cc9ae9-84ac-432b-b166-51a2f7cc9d93','fat content','dimensionless','Fat content, on a wet mass basis. '),
    ('d52653e8-4f99-467d-8f0f-f8ac60334452','kgFuel_input_in_process','kg',''),
    ('a4d1b0a4-a4ef-429e-9fab-6dd6ea142c37','mass concentration, uranium','kg/m3','Mass concentration of Uranium.    (CAS 007440-61-1)'),
    ('17b34a51-0a5a-41c6-a8ed-42984b97ed14','EcoSpold01Allocation_other_12','','other allocation 12 used in EcoSpold01 datasets'),
    ('46971dec-a716-4891-a5b7-5bebce5f3cdf','lifetime capacity [metric ton*km]','metric ton*km',''),
    ('96ed1584-c74a-4a92-a7f7-07509a4cd4de','height, internal','m',''),
    ('c2c8d7c5-7fc6-4d64-8ec1-525bb4b3ea8e','Practice factor','dimensionless','Anti-erosion practice factor'),
    ('1ffacfb6-8f96-43fa-beac-844ad4444716','share of methane in biogas','',''),
    ('335fb25a-49eb-4a6c-8c28-9a19d16c9456','calculation property, kg','kg','A generic property to be defined individually in each dataset. For use in mathematical relations.'),
    ('cd5814c6-01ff-4fe8-b4bc-225084393eb2','argon content','dimensionless','argon content on a dry matter basis'),
    ('e4fc784a-adb7-4c77-95d6-89c42f28d61f','EcoSpold01Allocation_other_21','','other allocation 21 used in EcoSpold01 datasets'),
    ('71bc04b9-abfe-4f30-ab8f-ba654c7ad296','mass concentration, lead','kg/m3','Mass concentration of Lead.    (CAS 007439-92-1)'),
    ('4d60d7ca-8f4b-4d14-b137-3670858e48ca','mass concentration, dissolved Kjeldahl Nitrogen as N','kg/m3','Mass concentration of dissolved Kjeldahl (SKN) as N. Note that dissolved Kjeldahl Nitrogen is an optional yet desirable specification of total Kjeldahl Nitrogen.'),
    ('1b839039-4988-4fbd-8029-5425e2e77339','EcoSpold01Allocation_undefined_45','','undefined allocation 45 used in EcoSpold01 datasets'),
    ('78b47051-ce8b-45d7-9ad8-5bb0baa6945a','carbon monoxide emissions tier T4-T4N for hp < 300','kg/hp*h',''),
    ('204646c0-9155-4216-b173-15a807e22f4a','MARKET_OVERWRITE_PV_CONSEQUENTIAL','dimensionless','Defines the new production volume amount of its exchange to be used in linking of the market for the consequential system model.'),
    ('86937b4e-c531-4ce5-b65e-ce0d17d3ca27','holmium content','dimensionless','holmium content on a dry matter basis'),
    ('89f2bcc0-b713-49f1-9e9d-ca66df27a245','SAM_activityLink_4','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('e5b24656-da1b-4285-8c37-e090808f4e50','amount 6 of flow in kg','kg',''),
    ('f0606516-7150-4264-a0a2-d0b9e4510c55','EcoSpold01Allocation_other_17','','other allocation 17 used in EcoSpold01 datasets'),
    ('f2283db2-62e4-467f-b9ac-c4f45be563b4','carbon allocation','kg','carbon content per unit of product (reserved; not for manual entry)'),
    ('6d7b06d2-b4f1-498b-b64a-2ae98bb3ac9c','EcoSpold01Allocation_other_58','','other allocation 58 used in EcoSpold01 datasets'),
    ('e0f51918-7d89-491e-b736-37d7f6bc1cea','EcoSpold01Allocation_undefined_58','','undefined allocation 58 used in EcoSpold01 datasets'),
    ('2bf51b11-c178-4e01-ab8d-f8380195714e','EcoSpold01Allocation_undefined_4','','undefined allocation 4 used in EcoSpold01 datasets'),
    ('f08f0bdf-eb3f-437c-bc28-0106936805d7','EcoSpold01Allocation_undefined_18','','undefined allocation 18 used in EcoSpold01 datasets'),
    ('c28e1c5d-b4ea-49b8-a771-f08967d67bcd','amount in multioutput activity_m3','m3',''),
    ('5f7dde76-e912-4ba0-9d93-c0b57704c617','EcoSpold01Allocation_undefined_120','','undefined allocation 120 used in EcoSpold01 datasets'),
    ('4f60c7ef-e48a-4d14-bc2a-1be2dda6fae7','carbon monoxide emissions tier T0-T1 for hp < 25','kg/hp*h',''),
    ('bd75bdc0-2ceb-4569-8f30-a475eadd87a0','EcoSpold01Allocation_undefined_89','','undefined allocation 89 used in EcoSpold01 datasets'),
    ('104e722b-9fa8-4f23-8b14-433309420209','EcoSpold01Allocation_undefined_94','','undefined allocation 94 used in EcoSpold01 datasets'),
    ('d0772b6b-5119-4d80-a322-f66e775c9b8a','EcoSpold01Allocation_undefined_155','','undefined allocation 155 used in EcoSpold01 datasets'),
    ('e5507d89-78ad-4746-900c-b9afa5a62ea6','lead content','dimensionless','lead content on a dry matter basis'),
    ('de5f7231-dc8b-402a-a222-95341a848e0a','EcoSpold01Allocation_other_69','','other allocation 69 used in EcoSpold01 datasets'),
    ('84b2179e-d937-410e-bcee-0174569488f9','EcoSpold01Allocation_undefined_125','','undefined allocation 125 used in EcoSpold01 datasets'),
    ('a22e0fcb-dfa2-467e-910f-a8813dce8bf1','EcoSpold01Allocation_undefined_124','','undefined allocation 124 used in EcoSpold01 datasets'),
    ('4872685d-64bd-45ed-a734-bc9e3e30ab19','EcoSpold01Allocation_undefined_129','','undefined allocation 129 used in EcoSpold01 datasets'),
    ('a2ce22cd-25a9-4950-8f19-476e1d0621a8','Slope','dimensionless','Slope [-]'),
    ('dbc99b58-665c-4be0-a252-b09ac506d1ba','amount of exchange 2','kg',''),
    ('5858159f-978d-4b14-b791-bdee5eba4fc7','carbon monoxide emissions tier T1-T2-T3 for hp < 750','kg/hp*h',''),
    ('8aaa7771-015a-4c28-8291-afa3342dbfbe','tellurium content','dimensionless','tellurium content on a dry matter basis'),
    ('8dedb554-cb5f-4978-8949-de6d74c4f608','amount in multioutput activity_kWh','kWh',''),
    ('2e73af1a-a29d-4846-89bc-db9b9d434e77','silica dioxide','dimensionless','Silica concentration on mass'),
    ('a264a1a8-0ec9-4671-bc2d-336d5a0b99dd','dry wood density','kg/m3','kg dry matter/ dry volume'),
    ('10f1ba60-d686-4fec-a93a-97bf45e660b0','EcoSpold01Allocation_undefined_110','','undefined allocation 110 used in EcoSpold01 datasets'),
    ('d0a2c761-50ab-4c1d-a37b-525409640a76','indium content','dimensionless','indium content on a dry matter basis'),
    ('66d4c921-658a-4ba0-b190-c6e09e57d74a','chlorine content','dimensionless','chlorine content on a dry matter basis'),
    ('f44abd93-d0f0-4de7-b1e6-1383c463122f','carbon monoxide emissions tier T1-T2-T3 for hp < 175','kg/hp*h',''),
    ('29ec76bd-aebc-440d-b8ed-7872c971097b','SAM_activityLink_2_scaling_factor','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('7177ac92-75b5-423e-a5b4-71351af3b7c3','EcoSpold01Allocation_undefined_145','','undefined allocation 145 used in EcoSpold01 datasets'),
    ('e66d61f6-8287-4cf1-bb0c-f978ee5e34b3','bismuth content','dimensionless','bismuth content on a dry matter basis'),
    ('b86d456d-a1dc-4468-a20e-b6a3f4701e32','boron content','dimensionless','boron content on a dry matter basis'),
    ('d2f0e9ef-86d6-41e5-935d-4057a09ec71e','ammonium fraction of total nitrogen','dimensionless','This parameter expresses the fraction of ammonium (NH4-N) of total nitrogen (N tot)'),
    ('5bb5c59e-6af9-403c-b325-2d158cb5984a','EcoSpold01Allocation_other_134','','other allocation 134 used in EcoSpold01 datasets'),
    ('a91695f7-22e8-4b39-bd05-56aacab09a87','neodymium content','dimensionless','neodymium content on a dry matter basis'),
    ('da65cd51-f4e5-4f89-90ea-5c6e9779f6bc','EcoSpold01Allocation_undefined_47','','undefined allocation 47 used in EcoSpold01 datasets'),
    ('e0226a6a-2ba6-47df-8aa6-07f42ffa087d','EcoSpold01Allocation_undefined_131','','undefined allocation 131 used in EcoSpold01 datasets'),
    ('a88e1c23-984b-4d59-8689-9822b41ff482','EcoSpold01Allocation_undefined_127','','undefined allocation 127 used in EcoSpold01 datasets'),
    ('cea619b8-1a76-4680-8b55-cdf682a3b32a','concentration, calcium','kg/kg','calcium content on a fresh matter basis'),
    ('cbc4a2c2-1710-4e6c-9b90-e1e72819d7b9','mass concentration, dissolved organic nitrogen as N','kg/m3','Mass concentration of dissolved organic nitrogen as N. Note that dissolved and particulate N are optional yet desirable specifications of total nitrogen.'),
    ('39207e5f-d89c-4f9d-b9f5-70569d015cda','nitrogen oxides emissions tier T3 for hp < 750','kg/hp*h',''),
    ('c88931f1-9089-4ff2-b93c-e6331eb78d71','EcoSpold01Allocation_other_87','','other allocation 87 used in EcoSpold01 datasets'),
    ('27fb8fa1-3055-4c62-8421-7d9588a3216f','EcoSpold01Allocation_undefined_158','','undefined allocation 158 used in EcoSpold01 datasets'),
    ('e5235f58-2e90-4393-8a9f-5cdfd8bfaa06','EcoSpold01Allocation_other_94','','other allocation 94 used in EcoSpold01 datasets'),
    ('1f3c2d02-f345-4df9-ba6a-88cdeaa67923','fluorine content','dimensionless','fluorine content on a dry matter basis'),
    ('90f2e899-4b94-43d2-813a-b4d6774a58e2','amount in multioutput activity_MJ','MJ',''),
    ('d287cf13-5787-4aa6-a82f-de366eed6694','calculation property, kBq','kBq','A generic property to be defined individually in each dataset. For use in mathematical relations.'),
    ('bcc69ece-1795-4cd3-bd81-c8a9308f6568','nitrogen oxides emissions tier T3-T4 for hp < 750','kg/hp*h',''),
    ('c9432a3d-c8f4-5280-9ce2-3c41b0c9315d','astatine content','dimensionless','astatine content on a dry matter basis'),
    ('4f3b2a38-e536-4342-9f6e-18475450e980','EcoSpold01Allocation_undefined_77','','undefined allocation 77 used in EcoSpold01 datasets'),
    ('3cf40fcd-c607-4193-934c-5c181a3ab514','EcoSpold01Allocation_other_19','','other allocation 19 used in EcoSpold01 datasets'),
    ('d26c0a60-86aa-41c8-80ee-3acabc4a5095','mass concentration, magnesium','kg/m3','Mass concentration of Magnesium.    (CAS 007439-95-4)'),
    ('7c498a4f-11b7-4c31-911b-12566af4c8d3','nitrogen oxides emissions tier T2 for hp >= 600','kg/hp*h',''),
    ('0c9b0570-27f4-4781-9924-85a7740a1bd2','EcoSpold01Allocation_other_4','','other allocation 4 used in EcoSpold01 datasets'),
    ('adafb091-8daa-4bc9-b302-98aa221ff337','concentration, mercury','kg/kg','mercury content on a fresh matter basis'),
    ('db390f56-9eb4-4add-88c6-e5118e9cc074','fly ash content','kg',''),
    ('135d3658-e653-4468-81bf-705e68d7c400','m3Fuel_input','m3',''),
    ('deba4909-fdf0-46d7-80ec-733b9142b16b','EcoSpold01Allocation_other_96','','other allocation 96 used in EcoSpold01 datasets'),
    ('ebf21bca-b7cf-45d0-9d82-bfb80519a970','mass concentration, iron','kg/m3','Mass concentration of Iron.    (CAS 007439-89-6)'),
    ('ab96be65-11c6-448a-b083-e364e7adb654','carbon dioxide factor','kg/GJ','Factor describes the amount of CO2 released per GJ heat supplied. CO2 factors of fuels commonly used in cement production are available from WBCSD (www.wbcsdcement.org)'),
    ('bbf35356-1757-4287-a72c-ae2bb1753731','osmium content','dimensionless','osmium content on a dry matter basis'),
    ('e40445b1-8aba-4282-851d-9c2d28b1a5c1','density','kg/l',''),
    ('2d99e421-b9bd-4e09-98e4-f09478190a9b','concentration, sulfur','kg/kg',''),
    ('449f4414-9f9f-4b76-8bfb-f170052555ab','concentration, phosphorus','kg/kg','phosphorus content on a fresh matter basis'),
    ('bb1cec35-ac0f-4c4a-bfc2-b082a4fa2fad','laminated veneer lumber content','dimensionless','fraction of oven dry mass'),
    ('7b2f5f06-34ff-4fa9-b5ee-e92cb8f7c965','benzopyrene content','dimensionless',''),
    ('5fbe72b3-a70b-42fe-932b-1c17327e3fa6','SAM_activityLink_1','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('0704ad55-e63f-4311-a54b-ad95e990eb72','EcoSpold01Allocation_undefined_81','','undefined allocation 81 used in EcoSpold01 datasets'),
    ('02b086c7-28a4-4204-b05b-d63631245216','EcoSpold01Allocation_other_39','','other allocation 39 used in EcoSpold01 datasets'),
    ('2dec5fcb-b303-4bfa-8e30-0e043c523163','true value','dimensionless','allocation property applied in "true value" allocation'),
    ('d9e61a10-6a71-4771-9585-e30a943a7826','hafnium content','dimensionless','hafnium content on a dry matter basis'),
    ('dfe0e5ee-314c-4fac-9a75-c96aa63ec3b5','concentration, indium','kg/kg',''),
    ('f7fa53fa-ee5f-4a97-bcd8-1b0851afe9a6','mass concentration, dissolved ammonia NH4 as N','kg/m3','Mass concentration of dissolved ammonia NH4 (CAS 007664-41-7) as N. Note that dissolved and particulate N are optional yet desirable specifications of total nitrogen.'),
    ('83c8941a-5d08-467a-a7d3-cdad847e1229','EcoSpold01Allocation_other_72','','other allocation 72 used in EcoSpold01 datasets'),
    ('44bdf1b0-a30e-4c71-a14c-6f370e55ba5b','fibre content','kg',''),
    ('38e047b7-7355-4f63-ae04-578aec06bf5d','SAM_activityLink_5_scaling_factor','dimensionless','To be used only in special submissions in coordination with ecoinvent and the Swiss FOEN.'),
    ('65d960dc-084b-46d8-bf42-4a430a653840','EcoSpold01Allocation_undefined_168','','undefined allocation 168 used in EcoSpold01 datasets'),
    ('d0f77c24-4608-40a1-a7e0-779730dfdc5f','mass concentration, fluoride','kg/m3',''),
    ('32e869d7-4713-4f6a-ac6d-0c36bca0835e','EcoSpold01Allocation_undefined_69','','undefined allocation 69 used in EcoSpold01 datasets'),
    ('e37853ea-ee53-4007-b1a6-74e3647034a6','digestable energy content','MJ/kg',''),
    ('8d459bb4-ae16-4770-a6ea-91c5ac1cc63a','EcoSpold01Allocation_undefined_162','','undefined allocation 162 used in EcoSpold01 datasets'),
    ('f24cce94-ff02-44db-b218-898dc4af6ae9','amount of exchange 5','kg',''),
    ('1f45c101-983d-43ff-a576-9601b15e0c65','fraction, origin: unspecified','dimensionless','This property represent the fraction of the amount of the exchange which origin is unspecified.'),
    ('8aedc313-f49b-42cd-8d54-fc877ec03017','magnesium content','dimensionless','magnesium content on a dry matter basis'),
    ('beb4ff33-db6f-4c65-ab6e-a7c174e943df','P to groundwater','kg/ha','Average quantity of P leached to ground water for a land use category (kg P /(ha*a)).'),
    ('01a85263-fbbb-499d-8a0a-f4a0d222b98d','amount of exchange in liters 5','l',''),
    ('32a8b523-0717-4c21-acff-51115abbb17c','net heating value','MJ/kg',''),
    ('e040fda6-4362-4adc-b915-3001d93afee0','carbon monoxide emissions tier T4A-T4B for hp < 11','kg/hp*h',''),
    ('6b14b0c0-87b0-4be6-831a-bff2512917f8','EcoSpold01Allocation_physical_2','','physical allocation 2 used in EcoSpold01 datasets'),
    ('20f028ac-cf7b-4052-aa36-247fbf2a16e0','EcoSpold01Allocation_other_95','','other allocation 95 used in EcoSpold01 datasets'),
    ('90493e21-61bd-4ad8-bd6a-f3bc46186927','emitted fraction','dimensionless',''),
    ('bb9a3b0c-dc91-4f43-8116-ecb6fb546b8e','protein feed, 100% crude per kg of dry mass','kg/kg',''),
    ('4583f86d-51fa-4fda-9c75-7fba827532f5','caesium content','dimensionless','caesium content on a dry matter basis'),
    ('a76b7e12-e8cb-4bb8-9501-df77d4f1da24','emission ratio','kg/kg',''),
    ('f940250a-29c4-45f1-bc5f-669921b2c517','percentage of sour gas','dimensionless',''),
    ('593e94f2-8374-48ea-9f19-0feb93b8aeac','EcoSpold01Allocation_other_41','','other allocation 41 used in EcoSpold01 datasets'),
    ('1ca889cd-9595-40cf-bf82-1872ff37af54','EcoSpold01Allocation_other_61','','other allocation 61 used in EcoSpold01 datasets'),
    ('e629f248-28bc-40c8-a7e8-f1c216e7eb1d','mass concentration, iridium','kg/m3','Mass concentration of Iridium.    (CAS 007439-88-5)'),
    ('f6e8dc68-9e1a-498e-a384-f731aa70ba37','cement content','kg',''),
    ('41ca3038-3c06-4aa3-981a-5888bf9c926d','EcoSpold01Allocation_undefined_149','','undefined allocation 149 used in EcoSpold01 datasets'),
    ('9146a06e-098c-4d95-9271-fa8010af8fd5','EcoSpold01Allocation_other_107','','other allocation 107 used in EcoSpold01 datasets'),
    ('b3026066-b632-4c47-a27e-c13f4a3489fb','iodine content','dimensionless','iodine content on a dry matter basis'),
    ('019e98f2-e22d-4b04-8177-9ddb48528453','carbon monoxide emissions tier T1-T2-T3 for hp < 300','kg/hp*h',''),
    ('d8135201-fa30-4332-a051-7eddb3f8f8ed','niobium content','dimensionless','niobium content on a dry matter basis'),
    ('ac7d9506-e25f-488e-a086-b6b1547790b6','carbon monoxide emissions tier T0 for hp >= 100','kg/hp*h',''),
    ('5fc6d1c5-6338-475b-8ad3-58be3c88bc86','EcoSpold01Allocation_other_73','','other allocation 73 used in EcoSpold01 datasets'),
    ('73a0f9dc-7539-44f3-b81b-b51d922b8dd9','UVEK_relative_amount_2','dimensionless',''),
    ('2584546f-187b-4a1d-b246-0af9d354b46b','mass concentration, helium','kg/m3','Mass concentration of Helium.    '),
    ('4dc56c79-a0ca-491c-b26c-c7c0128bac04','EcoSpold01Allocation_other_43','','other allocation 43 used in EcoSpold01 datasets'),
    ('440b6d1d-f212-40a9-95e9-3c13d4d8d8b7','UVEK_relative_amount_3','dimensionless',''),
    ('c1c24c34-8cf5-4830-95fb-7035820ff1ba','primary aluminium','kg',''),
    ('5d5ee305-56e4-4407-9bd0-9faa261af1c1','EcoSpold01Allocation_undefined_130','','undefined allocation 130 used in EcoSpold01 datasets'),
    ('28ae4f88-0082-4417-ab92-98943eda1867','MARKET_OVERWRITE_AMOUNT_CUTOFF','dimensionless','Defines the new amount of its exchange to be used in linking of the market for the cut-off system model.')
    ]

sourceId = [
    (uuid, "Marcos", "2022"), 
    (None, None, None),
    (uuid[:-2]+'a3', "1234", "9000")
]

s = ILCD1Structure()
ref = s.reference

combinations = []
results = []
for id_, name, unit, com in property_info:
    ip = {
        'name': {'#text': name},
        'uncertainty': unc_lognormal_1,
        'comment': {'@lang': 'en', '#text': com},
        '@amount': 10,
        '@propertyId': id_,
        "@propertyContextId": uuid,
        "@variableName": 'variable_name',
        "@isDefiningValue": False,
        "@mathematicalRelation": '10*4+24',
        "@isCalculatedAmount": True,
        "@unitId": uuid,
        "@unitContextId": uuid,
        "@sourceIdOverwrittenByChild": False,
        "@sourceContextId": uuid,
        }
    if unit != '':
        ip['unitName'] = {'#text': unit}
        amount = ECS2ToILCD1Amount(10, unit, unc_lognormal_1, ('variable_name', '10*4+24'), 'property')
    else:
        amount = ECS2ToILCD1Amount(10, 'dimensionless', unc_lognormal_1, ('variable_name', '10*4+24'), 'property')

    op = {
        'is_considered': True if (id_ in pint_to_ilcd_fp or unit != '') else False,
        'has_ilcd_equivalent': True if id_ in pint_to_ilcd_fp else False,
        'amount': amount,
        'comment': com
        }
    for sid, sfa, sy in sourceId:
        if sid is not None:
            ip['@sourceId'] = sid
            ip['@sourceFirstAuthor'] = sfa
            ip['@sourceYear'] = sy
            ref_sc = ref()
            ref_sc.a_type = 'source data set'
            ref_sc.a_refObjectId = uuid_from_uuid(sid, b'_Lavosier_ECS2_/', 'to_ILCD1')
            ref_sc.a_version = '01.00.000'
            ref_sc.a_uri = '../sources/' + uuid_from_uuid(sid, b'_Lavosier_ECS2_/', 'to_ILCD1')
            ref_sc.c_shortDescription = ILCD1Helper.text_dict_from_text(1, ILCD1Helper.source_short_ref(sfa, sy, None))
            op['source_ref'] = ref_sc
        results.append(op)
        combinations.append(ip)

all_ = []
ECS2ToILCD1FlowConversion.Property._energy = 'gross calorific value'
ECS2ToILCD1FlowConversion.Property.ref_conversion = ECS2ToILCD1ReferenceConversion
ECS2ToILCD1ReferenceConversion.ref_field = ref
ECS2ToILCD1ReferenceConversion.save_dir = ''
ECS2ToILCD1ReferenceConversion.uuid_conv_spec = (b'_Lavosier_ECS2_/', 'to_ILCD1')
ECS2ToILCD1ReferenceConversion.default_files = {
    'flow property': "Lavoisier_Default_Files/ILCD_EF30_FlowProperties",
    'unit group': "Lavoisier_Default_Files/ILCD_EF30_UnitGroups"
    }

@pytest.mark.property
@pytest.mark.parametrize('prop, results', [(combinations[i], results[i]) for i in range(len(combinations))])
def test_property(prop, results):
    s = ILCD1Structure()
    _f = s.exchanges.get_class('exchange')()
    ECS2ToILCD1FlowConversion.Property.flow_property_field = s.flow_property
    ECS2ToILCD1FlowConversion.Property.amountClass = ECS2ToILCD1Amount
    
    
    r = ECS2ToILCD1FlowConversion.Property(prop,
                                           _f,
                                           ECS2ToILCD1DataNotConverted().get_class('flows')())
    
    assert results['is_considered'] == r.is_considered
    assert results['has_ilcd_equivalent'] == r.has_ilcd_equivalent
    assert results['amount'].a == r.amount.a
    assert results['amount'].f == r.amount.f
    
    assert _f.referencesToDataSource.get('referenceToDataSource')[0].get_dict() == results['source_ref'].get_dict()
    
    if results['has_ilcd_equivalent']:
        assert prop['@propertyId'] in pint_to_ilcd_fp

class FlowMocking:
    
    def __init__(self, unit, unc, type_):
        self.Property = ECS2ToILCD1FlowConversion.Property
        self.type_ = type_
        s = ILCD1Structure()
        self.field = s.exchanges.get_class('exchange')()
        self.not_converted = ECS2ToILCD1DataNotConverted().get_class('flows')()
        self.amount = ECS2ToILCD1Amount(10, unit, unc, (None, None), 'flow')

@pytest.mark.property
@pytest.mark.parametrize('flow', [
    FlowMocking(unit, unc, type_) for unit in ('l', 'metric ton', 'km', 'dozen', 'ha') for unc, type_ in ((unc_lognormal_1, 'log'), (unc_normal, 'normal'))
    ])
def test_property_results1(flow):
    
    pinfo = [
    ('3a0af1d6-04c3-41c6-a3da-92c4f61e0eaa', 'dry mass','kg', 'add'),
    ('abc78955-bd5f-4b1a-9607-0448dd75ebf2', 'mass concentration, titanium','kg/m3', 'amount'),
    ('56f09738-8225-4bdc-91d2-39ee6328f0ee', 'silver content','dimensionless', 'dry_mass'),
    ('e38c9209-6934-4445-b180-675bcbd5ad7a', 'concentration, potassium','kg/kg', 'amount'),
    ('6393c14b-db78-445d-a47b-c0cb866a1b25', 'carbon content, non-fossil','dimensionless', 'dry_mass'),
    ('964f8b50-ce16-4364-835a-a3db5fb760b0', 'lifetime', 'year', 'factor'),
    ('350b57a1-2b58-49e8-96bd-c9a4be6b4625', 'lifetime capacity [unit]','unit', 'factor'),
    ('5b66c906-de94-4a06-9037-498de5498f82', 'lifetime capacity','guest night', 'factor'),
    ('b3fdadf7-9e1d-42bd-b36c-1744c7565539', 'lifetime capacity [kg*day]','kg*day', 'factor'),
    ('48c987bb-3144-4872-b5c7-b1389c40be25', 'heating value, net','MJ', 'factor'),
    ('11d072f8-37fc-41c2-80b2-ebba4f301b49', 'lifetime capacity [MJ]','MJ', 'factor'),
    ('ec1f2209-1f53-40d5-bc53-67f388c82f5a', 'lifetime capacity [kWh]','kWh', 'factor'),
    ('93bfda45-49f5-44bd-beb0-91b38dde4035', 'lifetime capacity [h]','hour', 'factor'),
    ('6bc8ac5e-cc4c-45fb-93dc-53c0e45091df', 'energy content','MJ', 'factor'),
    ('aefe9fab-ed23-4060-a35d-d24d5281926c', 'lifetime capacity [l]','l', 'factor'),
    ('38583c32-c20b-4553-9152-b14b0bee1e61', 'lifetime capacity [kg]','kg', 'factor'),
    ('46971dec-a716-4891-a5b7-5bebce5f3cdf', 'lifetime capacity [metric ton*km]','metric ton*km', 'factor'),
    ('d61b8768-8ef6-4a99-ae16-9e51f24ad5b5', 'heating value, gross','MJ', 'factor'),
    ('38f94dd1-d5aa-41b8-b182-c0c42985d9dc', 'price','EUR2005', 'factor'),
    ('7a3978ea-3e26-4329-bc8b-0915d58a7e6f', 'true value relation','dimensionless', 'factor'),
    ('c74c3729-e577-4081-b572-a283d2561a75', 'carbon content, fossil','dimensionless', 'dry_mass'),
    ('6d9e1462-80e3-4f10-b3f4-71febd6f1168', 'water in wet mass','kg', 'factor'),
    ('67f102e2-9cb6-4d20-aa16-bf74d8a03326', 'wet mass','kg', 'add'),
    ('a9358458-9724-4f03-b622-106eda248916', 'water content','dimensionless', 'dry_mass')
    ]
    
    s = ILCD1Structure()
    _f = s.exchanges.get_class('exchange')()
    ECS2ToILCD1FlowConversion.Property.flow_property_field = s.flow_property
    ECS2ToILCD1FlowConversion.Property.amountClass = ECS2ToILCD1Amount

    properties = {}
    results = {}
    dm = 1
    for id_, name, unit, type_ in pinfo:
        ip = {
            'name': {'#text': name},
            'uncertainty': unc_lognormal_1,
            '@amount': 10,
            '@propertyId': id_,
            "@propertyContextId": uuid,
            "@variableName": 'variable_name',
            "@isDefiningValue": False,
            "@mathematicalRelation": '10*4+24',
            "@isCalculatedAmount": True,
            'unitName': {'#text': unit},
            "@unitId": uuid,
            "@unitContextId": uuid,
            "@sourceIdOverwrittenByChild": False,
            "@sourceContextId": uuid,
            }
        uid = pint_to_ilcd_fp.get(id_, None)
        ref_fp = ref()
        if uid is not None:
            
            ref_fp.a_type = 'flow property data set'
            ref_fp.a_refObjectId = uid[0]
            ref_fp.a_version = uid[-2]
            ref_fp.a_uri = '../flowproperties/' + uid[0]
            ref_fp.c_shortDescription = ILCD1Helper.text_dict_from_text(1, uid[-1])        
        amount = ECS2ToILCD1Amount(10, unit, unc_lognormal_1, (None, None), 'property')
        if type_ == 'factor':
            am = amount.m / flow.amount.f
        elif type_ == 'dry_mass':
            am = amount.m * dm
        elif type_ == 'amount':
            am = amount.m * flow.amount.m
        else:
            if name == 'dry mass':
                dm = 10 / flow.amount.f
            am = None # like dry mass, additionals || units actualy doesnt matter
        results[name] = {'ref': ref_fp,
                          'meanValue': am}
        properties[name] = ECS2ToILCD1FlowConversion.Property(ip,
                                                                _f,
                                                                ECS2ToILCD1DataNotConverted().get_class('flows')())

    props = ECS2ToILCD1FlowConversion.Property.get_ilcd_equivalent(properties, flow)
    
    for p in props:
        if props[p].is_considered and props[p].has_ilcd_equivalent:
            x = props[p].get_dict()
            assert isinstance(x['@dataSetInternalID'], int)
            assert x['referenceToFlowPropertyDataSet'] == [results[p]['ref'].get_dict()]
            assert x['meanValue'] == pytest.approx(results[p]['meanValue'], 0.00001)

@pytest.mark.property
@pytest.mark.parametrize('flow', [
    FlowMocking(unit, unc, type_) for unit in ('l', 'metric ton', 'km', 'dozen', 'ha') for unc, type_ in ((unc_lognormal_1, 'log'), (unc_normal, 'normal'))
    ])
def test_property_results2(flow):

    pinfo = [
    ('abc78955-bd5f-4b1a-9607-0448dd75ebf2', 'mass concentration, titanium','kg/m3', 'amount'),
    ('7c33fa83-dbc9-43c3-85c2-a5bdb058c37d', 'ash content','kg', 'factor'),
    ('56f09738-8225-4bdc-91d2-39ee6328f0ee', 'silver content','dimensionless', 'dry_mass'),
    ('e38c9209-6934-4445-b180-675bcbd5ad7a', 'concentration, potassium','kg/kg', 'amount'),
    ('6393c14b-db78-445d-a47b-c0cb866a1b25', 'carbon content, non-fossil','dimensionless', 'dry_mass'),
    ('964f8b50-ce16-4364-835a-a3db5fb760b0', 'lifetime','year', 'factor'),
    ('350b57a1-2b58-49e8-96bd-c9a4be6b4625', 'lifetime capacity [unit]','unit', 'factor'),
    ('5b66c906-de94-4a06-9037-498de5498f82', 'lifetime capacity','guest night', 'factor'),
    ('b3fdadf7-9e1d-42bd-b36c-1744c7565539', 'lifetime capacity [kg*day]','kg*day', 'factor'),
    ('48c987bb-3144-4872-b5c7-b1389c40be25', 'heating value, net','MJ', 'factor'),
    ('11d072f8-37fc-41c2-80b2-ebba4f301b49', 'lifetime capacity [MJ]','MJ', 'factor'),
    ('ec1f2209-1f53-40d5-bc53-67f388c82f5a', 'lifetime capacity [kWh]','kWh', 'factor'),
    ('93bfda45-49f5-44bd-beb0-91b38dde4035', 'lifetime capacity [h]','hour', 'factor'),
    ('6bc8ac5e-cc4c-45fb-93dc-53c0e45091df', 'energy content','MJ', 'factor'),
    ('aefe9fab-ed23-4060-a35d-d24d5281926c', 'lifetime capacity [l]','l', 'factor'),
    ('38583c32-c20b-4553-9152-b14b0bee1e61', 'lifetime capacity [kg]','kg', 'factor'),
    ('46971dec-a716-4891-a5b7-5bebce5f3cdf', 'lifetime capacity [metric ton*km]','metric ton*km', 'factor'),
    ('d61b8768-8ef6-4a99-ae16-9e51f24ad5b5', 'heating value, gross','MJ', 'factor'),
    ('38f94dd1-d5aa-41b8-b182-c0c42985d9dc', 'price','EUR2005', 'factor'),
    ('7a3978ea-3e26-4329-bc8b-0915d58a7e6f', 'true value relation','dimensionless', 'factor'),
    ('c74c3729-e577-4081-b572-a283d2561a75', 'carbon content, fossil','dimensionless', 'dry_mass'),
    ('6d9e1462-80e3-4f10-b3f4-71febd6f1168', 'water in wet mass','kg', 'factor'),
    ('a9358458-9724-4f03-b622-106eda248916', 'water content','dimensionless', 'dry_mass')
    ]
    
    s = ILCD1Structure()
    _f = s.exchanges.get_class('exchange')()
    ECS2ToILCD1FlowConversion.Property.flow_property_field = s.flow_property
    ECS2ToILCD1FlowConversion.Property.amountClass = ECS2ToILCD1Amount
    
    properties = {}
    results = {}
    for id_, name, unit, type_ in pinfo:
        ip = {
            'name': {'#text': name},
            'uncertainty': unc_lognormal_1,
            '@amount': 10,
            '@propertyId': id_,
            "@propertyContextId": uuid,
            "@variableName": 'variable_name',
            "@isDefiningValue": False,
            "@mathematicalRelation": '10*4+24',
            "@isCalculatedAmount": True,
            'unitName': {'#text': unit},
            "@unitId": uuid,
            "@unitContextId": uuid,
            "@sourceIdOverwrittenByChild": False,
            "@sourceContextId": uuid,
            }
        uid = pint_to_ilcd_fp.get(id_, None)
        if uid is not None:
            ref_fp = ref()
            ref_fp.a_type = 'flow property data set'
            ref_fp.a_refObjectId = uid[0]
            ref_fp.a_version = uid[-2]
            ref_fp.a_uri = '../flowproperties/' + uid[0]
            ref_fp.c_shortDescription = ILCD1Helper.text_dict_from_text(1, uid[-1])       
        amount = ECS2ToILCD1Amount(10, unit, unc_lognormal_1, (None, None), 'property')
        if type_ == 'factor':
            am = amount.m / flow.amount.f
        elif type_ == 'dry_mass':
            am = None
        elif type_ == 'amount':
            am = amount.m * flow.amount.m
        else:
            am = None # like dry mass, additionals || units actualy doesnt matter
        results[name] = {'ref': ref_fp,
                          'meanValue': am}
        properties[name] = ECS2ToILCD1FlowConversion.Property(ip,
                                                                _f,
                                                                ECS2ToILCD1DataNotConverted().get_class('flows')())

    props = ECS2ToILCD1FlowConversion.Property.get_ilcd_equivalent(properties, flow)
    
    for p in props:
        if props[p].is_considered and props[p].has_ilcd_equivalent:
            x = props[p].get_dict()
            assert isinstance(x['@dataSetInternalID'], int)
            assert x['referenceToFlowPropertyDataSet'] == [results[p]['ref'].get_dict()]
            assert x['meanValue'] == pytest.approx(results[p]['meanValue'], 0.00001)

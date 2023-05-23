#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  1 00:32:43 2022

@author: jotape42p
"""

import openturns as ot
from abc import ABC, abstractmethod
from pathlib import Path
from copy import copy
from collections import Counter, defaultdict
from itertools import chain
import os

from .utils import (
    uuid_from_uuid,
    uuid_from_string,
    ensure_list,
    FieldMapping,
    Print
)
from .units import (
    ilcd_to_ecs2_un,
    ilcd_to_ecs2_fp,
    units_def
)
from .data import (
    special_activity_,
    child_type_,
    time_period_,
    tech_,
    type_process_,
    system_model_1_,
    system_model_2_,
    status_publication_,
    restrictions_,
    access_,
    energy_
)

from ..formats import ILCD1Helper, ECS2Helper, XMLStreamIterable
from ..data_structures import ILCD1ToECS2DataNotConverted

import logging
import time
import re
import math
import pint
up = pint.UnitRegistry(Path(Path(__file__).parent, 'units.txt'))
up.define('@alias hour = h')
up.define('item = [item] = _ = Item = Items')
up.define('EUR2005 = [currency] = EUR_default')
up.define('fraction = [] = frac')
for u in units_def.values():
    up.define(u)

# __version__ = "Debug"

class ILCD1ToECS2UncertaintyConversion:

    @classmethod
    def normal_init(cls, x):
        self = cls()
        self._type = x['uncertaintyDistributionType'].replace(
            'log-normal', 'lognormal')

        # Get Comment
        self.comment = []
        for c in ensure_list(x.get('generalComment', {}), ensure_text=True):
            if 'Uncertainty Comment:\n' in c['#text']:
                # cc_ = c['#text'].split('Uncertainty Comment:\n')[0]
                c_ = c['#text'].split('Uncertainty Comment:\n')[-1]
                if 'Pedigree: (' in c_:
                    g = re.search(
                        r"(Pedigree: \(([0-9]{1},[0-9]{1},[0-9]{1},[0-9]{1},[0-9]{1})\))", c_).groups()
                    c_ = c_.replace(g[0], '')
                    self.pedigree = g[1]
                if 'Basic Variance: ' in c_:
                    g = re.search(r"(Basic Variance: ([0-9\.]+))", c_).groups()
                    c_ = c_.replace(g[0], '')
                    self.var = float(g[1])
                if (c_ and not c_.isspace()): # or (cc_ and not cc_.isspace()):
                    self.comment.append(ILCD1Helper.text_add_index(
                        {'@lang': c['@lang'], '#text': c_})) # The separator is included already
            # else:
            #     self.comment.append(ILCD1Helper.text_add_index(c))

        # Get basic data
        self._get_data(x)
        return self

    def _get_data(self, x):
        if self._type in ('normal', 'lognormal'):
            if "relativeStandardDeviation95In" not in x:
                raise KeyError(f"{self._type} with no relative standard deviation")
            var = float(x["relativeStandardDeviation95In"])
            if not hasattr(self, 'var'): # Here because only normal and lognormal can have pedigree
                logging.info(f"\t\t{self._type} with no pedigree information")
            self.varpedigree = var
        elif self._type in ('triangular', 'uniform'):
            try:
                self.min = float(
                    x.get('minimumValue', x.get('minimumAmount')))
            except: raise KeyError(f"{self._type} with no minimum amount/value")
            try:
                self.max = float(
                    x.get('maximumValue', x.get('maximumAmount')))
            except: raise KeyError(f"{self._type} with no maximum amount/value")

    @classmethod
    def init_from_comment(cls, x):
        for c in ensure_list(x.get('generalComment', {}), ensure_text=True): # Here the comment is not created in self
            if re.search('\nNot Converted: [A-z]+ distribution with parameters ', c['#text']):
                self = cls()
                # cm = re.split('\nNot Converted: [A-z]+ distribution with parameters ', c['#text'])[0]
                # if cm and not cm.isspace():
                #     self.comment = ILCD1Helper.text_add_index({'@lang': c['@lang'], '#text': cm})
                c_ = re.search(
                    '\nNot Converted: [A-z]+ distribution with parameters (.*)', c['#text']).groups()[0]
                if '=' not in c_: # Too loose, get the 'not_converted' part functioning
                    return None
                for n in c_.split(','):
                    setattr(self, n.split('=')[0].strip().replace(' ', '_'), n.split('=')[1].strip())
                self._type = 'other' # for consistency with the calculate method
                return self
        else:
            return None

    def calculate(self, m, f, field):
        if hasattr(self, 'comment') and self.comment != []:
            field.comment = self.comment
        if hasattr(self, 'pedigree'):
            p_index = ('reliability', 'completeness', 'temporalCorrelation',
                       'geographicalCorrelation', 'furtherTechnologyCorrelation')
            for i, factor in enumerate(self.pedigree.split(',')):
                setattr(field.pedigreeMatrix, p_index[i], factor)
        if self._type == 'lognormal':
            var = math.log(math.sqrt(self.varpedigree))**2
            # Sometimes the m is negative :/
            field.lognormal.mu = math.log(m) if m > 0 else 0
            field.lognormal.meanValue = m
            field.lognormal.variance = getattr(self, 'var', var)
            field.lognormal.varianceWithPedigreeUncertainty = var
            self._var = var
        elif self._type == 'normal':
            var = (self.varpedigree * f / 2) ** 2
            field.normal.meanValue = m
            field.normal.variance = getattr(self, 'var', var)
            field.normal.varianceWithPedigreeUncertainty = var
            self._var = var
        elif self._type == 'triangular':
            field.triangular.minValue = self.min * f
            field.triangular.mostLikelyValue = m
            field.triangular.maxValue = self.max * f
        elif self._type == 'uniform':
            field.uniform.minValue = self.min * f
            field.uniform.maxValue = self.max * f
        else:  # Beta, Gamma and Binomial. No factor is used since the value is the same as the converted ECS2
            if hasattr(self, 'n'):
                for x in ('n', 'p'):
                    setattr(field.binomial, '@'+x, float(getattr(self, x)))
            elif hasattr(self, 'shape'):
                for x in ('shape', 'scale', 'minValue'):
                    setattr(field.gamma, '@'+x, float(getattr(self, x)))
            elif hasattr(self, 'mostLikelyValue'):
                for x in ('minValue', 'mostLikelyValue', 'maxValue'):
                    setattr(field.beta, '@'+x, float(getattr(self, x)))
            elif hasattr(self, 'standardDeviation95'):
                for x in ('minValue', 'standardDeviation95', 'maxValue'):
                    setattr(field.undefined, '@'+x, float(getattr(self, x)))
        return self

    def _get_distribution(self, amount):
        self._unc = {
            'lognormal': (ot.LogNormal, lambda: [math.log(abs(amount.m)), math.sqrt(self._var)]),
            'normal': (ot.Normal, lambda: [amount.m, math.sqrt(self._var)])
        }.get(self._type)
        return self._unc[0](*self._unc[1]())

    def _change_data(self, amount, other_unc, operation, field):
        logging.info(
            f"\t\tUncertainty: Distribution operation {operation} between two {self._type} distributions")
        unc = self._get_distribution(amount)
        if operation == 'add':
            new = (unc + other_unc)
        if self._type == 'normal':
            self._var = new.getStandardDeviation()[0] ** 2
            field.normal.meanValue = new.getMean()[0]
            field.normal.variance = self._var
            field.normal.varianceWithPedigreeUncertainty = self._var

class Amount(ABC):

    uncertainty_conversion = None

    def __init__(self, amount, unit_text, uncertainty_struct):
        self._a = up.Quantity(amount, unit_text.replace('(s)', '')) # Item(s) are recognized as item * seconds
        self._f = 1
        if uncertainty_struct:
            if uncertainty_struct.get('uncertaintyDistributionType') and uncertainty_struct['uncertaintyDistributionType'] != 'undefined':
                self._unc = type(self).uncertainty_conversion.normal_init(
                    uncertainty_struct)
            else:
                if type(self).uncertainty_conversion.init_from_comment(uncertainty_struct):
                    self._unc = type(self).uncertainty_conversion.init_from_comment(
                        uncertainty_struct)
        self.o = copy(self)

    @property
    def m(self): return self._a.m
    @property
    def u(self): return self._a.u
    @property
    def a(self): return self._a
    # Original value can be 0 (no magnitude division) and it can have different dimensionalities between original and new (no unit conversion)
    # @property
    # def f(self): return self._f
    # @property
    # def unc(self): return self._unc if hasattr(self, '_unc') else None
    @property
    def dimensionality(self): return self._a.dimensionality

    # def to(self, unit):
    #     self._a = self._a.to(unit)
    #     return self

    @abstractmethod
    def calculate_unc(self):
        pass


class ILCD1ToECS2Amount(Amount):

    def calculate_unc(self, field):
        if hasattr(self, '_unc') and self._unc: # self._unc can be None, can be done several times
            self._unc = self._unc.calculate(
                self._a.m, self._f, field.uncertainty)
            return self._unc
        return None

    def sum_(self, other, field):
        if isinstance(other, ILCD1ToECS2Amount):
            if hasattr(self, '_unc') and hasattr(other, '_unc'):
                if self._unc._type == other._unc._type == 'normal':
                    self._unc._change_data(self, other._unc._get_distribution(other), 'add', field.uncertainty)
                else:
                    del self._unc  # If there is a division and it is not two lognormal uncertainties, desconsider uncertainty
        self._a = self._a + (other.a if isinstance(other,
                             ILCD1ToECS2Amount) else other)
        self._f += other.m

    def multiply(self, other):
        self._a = self._a * other
        self._f *= other.m

    def divide(self, other):
        self._a = self._a / other
        self._f /= other.m


class ILCD1ToECS2VariableConversion:

    # Variable Parameters go to the flows actualy
    #   production volume variables are not converted back to their variables

    amountClass = None

    parameter_holder = None
    
    master_field = None

    _available_variables = {}
    
    _non_conform_variables = {}
    
    def __init__(self, x, not_converted):
        self.not_converted = not_converted

        self.name = x['@name']
        self.o_name = self.name
        if not re.search(r'^[A-Za-z]{1}', self.name):
            type(self)._non_conform_variables[self.name] = 'uc'+self.name
            self.name = 'uc'+self.name
        
        self.amount = type(self).amountClass(float(x['meanValue']),
                                             'dimensionless',
                                             x)
        self.formula = x['formula'] if x.get('formula') else None

        self.comment = []
        for c in ensure_list(x.get('comment', {}), ensure_text=True):
            if re.search(r'\[(.*)\]', c['#text']):  # [!] Search for the unit id
                self.unit = re.search(r'\[(.*)\]', c['#text']).groups()[0]
                c['#text'] = re.sub(r'(\[.*\])', '', c['#text']).strip()
                self.comment.append(ILCD1Helper.text_add_index(c))
            else:
                self.comment.append(ILCD1Helper.text_add_index(c))

        # [!] Maybe consider the comment going to the flow [add unit name and id]
        type(self)._available_variables[self.o_name] = {
            'used?': False, 'self': self}

    @classmethod
    def change_formula(cls, instance):
        if instance.formula:
            for n in cls._non_conform_variables: # __ha_to_m2__ is not valid as it has to start with a letter
                if n in instance.formula:
                    instance.formula = instance.formula.replace(n, cls._non_conform_variables[n])

    @classmethod
    def create_parameters(cls):  # It doesn't really have a unit name actualy
        vs = {k: v['self']
              for k, v in cls._available_variables.items() if not v['used?']}
        for k, var in vs.items():
            par = cls.parameter_holder.get_class('parameter')()
            par.name = ILCD1Helper.text_dict_from_text(0, k)
            var.amount.calculate_unc(par)
            par.parameterId = uuid_from_string(k)
            par.variableName = var.name
            if var.formula:
                cls.change_formula(var)
                par.mathematicalRelation = var.formula
                par.isCalculatedAmount = True
            par.amount = var.amount.m
            if hasattr(var, 'unit'):
                par.unitName = ILCD1Helper.text_dict_from_text(0, var.unit)
            if var.comment:
                par.comment = var.comment

            setattr(cls.parameter_holder, 'parameter', par)
            
            master = cls.master_field.get_class('parameter')()
            master.name = ILCD1Helper.text_dict_from_text(0, k)
            master.id = uuid_from_string(k)
            master.defaultVariableName = var.name
            setattr(cls.master_field, 'parameter', master)

    @classmethod
    def get_variable(cls, name):
        cls._available_variables[name]['used?'] = True
        self = cls._available_variables[name]['self']
        cls.change_formula(self)
        cls._available_variables[name]['self'] = self
        return cls._available_variables[name]['self']


class ILCD1ToECS2FlowConversion:  # Originally, the production volume is not conversible

    uuid_process = None

    uuid_specs = None
    compartment_mapping = None

    amountClass = None
    source_ref_conversion = None
    variable_conversion = None

    flow_holder = None
    
    master_field = None

    _reference_flows = []
    _flow_internal_refs = None
    _all_em_flows = set()
    _all_flow_ids = set() # Used to avoid duplicates on the field 'id'

    _use_md_prop = None
    property_master_data = None
        
    def __init__(self, x, not_converted):
        self.not_converted = not_converted

        # Dimensionless for the time, it will have an unit in the references
        self.id_ = x['referenceToFlowDataSet']['@refObjectId']
        self._name =  ensure_list(x['referenceToFlowDataSet']['shortDescription'], ensure_text=True)[0]['#text']
        logging.info(f'\tStarting conversion of flow {self._name} : {self.id_}')
        self.amount = type(self).amountClass(float(x.get('resultingAmount', x.get('meanAmount'))),
                                             'dimensionless', x)

        self.comment = []
        for n in ensure_list(x.get('generalComment', {}), ensure_text=True):
            self.comment.append(ILCD1Helper.text_add_index(n))

        if x.get('referenceToVariable'):
            self.variable = type(self).variable_conversion.get_variable(
                x['referenceToVariable'])
        self.group = x['exchangeDirection']
        self.isReference = True if x['@dataSetInternalID'] in type(
            self)._reference_flows else False

        self.properties = {}
        self.main = None # Unit property
        if x.get('allocations'):
            self.alloc_properties = {}
            for alloc in x['allocations'].get('allocation', []): # No @master allocation or other allocation type since it can be allocated for any of them
                self.alloc_properties['allocation for '+type(self)._flow_internal_refs[ # Maybe consider the ecospold name here
                    str(alloc['@internalReferenceToCoProduct'])]] = float(alloc['@allocatedFraction'])
    
    class Property:

        amountClass = None

        property_holder = None
        
        master_field = None

        _energy = []
    
        @classmethod
        def master_data(cls, id_, d, not_converted):
            self = cls()
            self.not_converted = not_converted
            self.name = d['name']
            self.id_ = id_
            logging.info(f'Starting conversion of master property {self.name} : {self.id_}')
            self.isConvertible = True
            self.amount = type(self).amountClass(float(d['amount'].replace(',','.')), d['unitName'], None)
            self.field = cls.property_holder.get_class('property')()
            self.field.unitName = ILCD1Helper.text_dict_from_text(0, d['unitName'])
            self.field.unitId = [x[0] for x in ilcd_to_ecs2_un.values() if x[1] == d['unitName']][0]
            self.field.isDefiningValue = True if d['isDefiningValue'] == "VERDADEIRO" else False
            self.amount.calculate_unc(self.field)
            if d['comment'] != '':
                self.field.comment = ILCD1Helper.text_dict_from_text(0, d['comment'])
            return self

        @classmethod
        def normal_init(cls, x, not_converted):
            self = cls()
            self.not_converted = not_converted
            self.name = x['referenceToFlowPropertyDataSet']['shortDescription']['#text']
            self.id_ = x["referenceToFlowPropertyDataSet"]["@refObjectId"]
            logging.info(f'Starting conversion of property {self.name} : {self.id_}')
            self.fp = fp = ilcd_to_ecs2_fp.get(self.id_, None)
            self.isConvertible = True if fp else False

            if fp:
                self.amount = type(self).amountClass(float(x['meanValue']),
                                                     fp[1], x)
                self.field = cls.property_holder.get_class('property')()
                self.field.unitName = ILCD1Helper.text_dict_from_text(0, fp[1])
                self.field.unitId = fp[0]

                if fp[3] == 'heating value, gross':
                    cls._energy.append('GROSS')
                elif fp[3] == 'heating value, net':
                    cls._energy.append('NET')

                self.amount.calculate_unc(self.field)
                for n in ensure_list(x.get('generalComment', {}), ensure_text=True):
                    self.field.comment = ILCD1Helper.text_add_index(n)
            else:
                logging.warning(
                    f"\t\tFlow property {self.name} not a valid EcoSpold2 flow property")

            return self

        @classmethod
        def allocation_init(cls, name, amount, flow_master=None):
            self = cls()
            self.isConvertible = True
            self.not_converted = None

            self.amount = type(self).amountClass(amount,
                                                 'dimensionless',
                                                 None)
            self.field = cls.property_holder.get_class('property')()
            self.field.unitName = ILCD1Helper.text_dict_from_text(
                1, 'dimensionless')
            self.field.unitId = '577e242a-461f-44a7-922c-d8e1c3d2bf45'

            self.field.propertyId = uuid_from_string(name['#text'])
            self.field.name = ILCD1Helper.text_add_index(name, index=1)

            self.field.amount = self.amount.m

            prop = flow_master.get_class('property')()
            prop.amount = self.amount.m
            prop.propertyId = uuid_from_string(name['#text'])
            prop.name = ILCD1Helper.text_add_index(name, index=1)
            prop.unitName = ILCD1Helper.text_dict_from_text(
                1, 'dimensionless')
            prop.unitId = '577e242a-461f-44a7-922c-d8e1c3d2bf45'
            setattr(flow_master, 'property', prop)
            
            prop = type(self).master_field.get_class('property')()
            prop.name = ILCD1Helper.text_add_index(name, index=1)
            prop.id = uuid_from_string(name['#text'])
            setattr(type(self).master_field, 'property', prop)

            return self

        @classmethod
        def mass_prop_init(cls, amount, name, id_):
            self = cls()
            self.isConvertible = True

            self.amount = type(self).amountClass(amount,
                                                 'kg',
                                                 None)  # [!] No uncertainty considered
            self.field = cls.property_holder.get_class('property')()
            self.field.unitName = ILCD1Helper.text_dict_from_text(0, 'kg')
            self.field.unitId = '487df68b-4994-4027-8fdc-a4dc298257b7'

            self.field.propertyId = id_
            self.field.name = ILCD1Helper.text_dict_from_text(1, name)

            self.amount.calculate_unc(self.field)

            return self

        @classmethod
        def convert_properties(cls, props, flow, master_data):
            if master_data:
                for k, prop in props.items():
                    prop.field.propertyId = prop.id_
                    prop.field.name = ILCD1Helper.text_dict_from_text(1, prop.name)
                    prop.field.amount = prop.amount.m
            else:
                if 'water content' in props:
                    if str(flow.amount.u) == 'm**3':
                        logging.warning(
                            '\t\tProperties Wet mass and dry mass not converted due to a need for density values in m3/kg')
                    else:
                        props['wet mass'] = cls.mass_prop_init(
                            1, 'wet mass', '67f102e2-9cb6-4d20-aa16-bf74d8a03326')
                        props['dry mass'] = cls.mass_prop_init(
                            1-props['water content'].amount.m, 'dry mass', '3a0af1d6-04c3-41c6-a3da-92c4f61e0eaa')
                        props['water in wet mass'] = cls.mass_prop_init(
                            props['water content'].amount.m, 'water in wet mass', '6d9e1462-80e3-4f10-b3f4-71febd6f1168')
    
                for k, prop in props.items():
                    if ' content' in k:
                        if not prop.field.get('propertyId'):
                            mass, volume = prop.fp[4]
                            if str(flow.amount.u) == 'kg' and mass:
                                prop.field.unitName = ILCD1Helper.text_dict_from_text(0, 'kg/kg')
                                prop.field.unitId = '83ecd334-1b5b-4784-8938-6a0d0a9d8954'
                                prop.field.propertyId = mass[0]
                                prop.field.name = ILCD1Helper.text_dict_from_text(
                                    1, mass[1])
                            elif str(flow.amount.u) == 'm**3' and volume:
                                prop.field.unitName = ILCD1Helper.text_dict_from_text(0, 'kg/m3')
                                prop.field.unitId = 'cacb6d36-694d-4e4f-9e79-6c9c73146839'
                                prop.field.propertyId = volume[0]
                                prop.field.name = ILCD1Helper.text_dict_from_text(
                                    1, volume[1])
                            else:
                                if 'dry mass' in props:
                                    if props['dry mass'].amount.m != 0:
                                        prop.amount.divide(props['dry mass'].amount.a)
                                    else:
                                        prop.amount._a = up.Quantity(0, 'kg')
                                else:  # unit correction only, considered dry mass as 1
                                    prop.amount.divide(up.Quantity(1, 'kg'))
                                prop.field.propertyId = prop.fp[2]
                                prop.field.name = ILCD1Helper.text_dict_from_text(
                                    1, prop.fp[3])
                    else:
                        if not prop.field.get('propertyId'):
                            prop.field.propertyId = prop.fp[2]
                            prop.field.name = ILCD1Helper.text_dict_from_text(
                                1, prop.fp[3])
    
                    prop.field.amount = prop.amount.m

            return [p for p in props.values()]

    def get_properties(self, file):
        with open(file) as f:  # It is exhausted in the first iteration so it has to be opened again
            map_ = {'/flowDataSet/flowProperties/flowProperty':
                    lambda t: self.properties.__setitem__(t['referenceToFlowPropertyDataSet']['shortDescription']['#text'],
                                                          self.Property.normal_init(t, self.not_converted))}
            for path, t in XMLStreamIterable(f, map_):
                if t['@dataSetInternalID'] != self.info['reference']:
                    map_[path](t)
                else:
                    self.main = ilcd_to_ecs2_un.get(
                        t['referenceToFlowPropertyDataSet']['@refObjectId'])
    
    def get_master_data_properties(self, id_):
        for propid, prop in type(self).property_master_data.get(id_, {}).items():
            self.properties[prop['name']] = self.Property.master_data(propid, prop, self.not_converted)

    def get_elementary_flow_info(self, n, file):
        self.field.elementaryExchangeId = n["TargetFlowUUID"]
        self.field.name = ILCD1Helper.text_dict_from_text(
            0, n["TargetFlowName"])

        self.master = type(self).master_field.get_class('elementaryExchange')()
        
        self.master.id = n["TargetFlowUUID"]
        self.mtype = 'elementaryExchange'
        c = type(self).compartment_mapping.get(n["TargetFlowContext"], None)
        if c:
            # TODO take out the subcompartmentId key from json
            self.field.compartment.subcompartmentId = c['subcompartmentId']
            self.field.compartment.compartment = ILCD1Helper.text_dict_from_text(
                0, n['TargetFlowContext'].split('/')[0])
            self.field.compartment.subcompartment = ILCD1Helper.text_dict_from_text(
                0, n['TargetFlowContext'].split('/')[1])
            
            comp = self.master.get_class('compartment')()
            comp.subcompartmentId = c['subcompartmentId']
            comp.compartment = ILCD1Helper.text_dict_from_text(
                0, n['TargetFlowContext'].split('/')[0])
            comp.subcompartment = ILCD1Helper.text_dict_from_text(
                0, n['TargetFlowContext'].split('/')[1])
            setattr(self.master, 'compartment', comp)
            
        else:
            raise ValueError(
                f"Compartment {n['TargetFlowContext']} is not a valid EcoSpold2 compartment")

        cf = float(n['ConversionFactor']) if n['ConversionFactor'] not in (
            '', 'n/a') else 1
        self.amount.multiply(up.Quantity(cf, n['TargetUnit']))
        self.amount.calculate_unc(self.field)
        self.field.unitName = ILCD1Helper.text_dict_from_text(
            0, n['TargetUnit'])
        for k, v in ilcd_to_ecs2_un.items():
            if up.Quantity(1, v[1].replace(' ', '_')).dimensionality == up.Quantity(1, n['TargetUnit']).dimensionality:
                self.field.unitId = v[0]
                break
        else:
            raise ValueError(f"Unit {n['TargetUnit']} not found")
            
        if self.info.get('CAS'):
            self.field.casNumber = self.info['CAS']
        if self.info.get('synonym'):
            self.field.synonym = self.info['synonym']
        if self.info.get('formula'):
            self.field.formula = self.info['formula']
            
        self.master.name = ILCD1Helper.text_dict_from_text(
            0, n["TargetFlowName"])
        self.master.unitName = ILCD1Helper.text_dict_from_text(
            0, n['TargetUnit'])
        self.master.unitId = v[0]

        if type(self)._use_md_prop:
            self.get_master_data_properties(n["TargetFlowUUID"])
        else:
            self.get_properties(file)
        type(self)._all_em_flows.add(self)

    def get_intermediate_flow_info(self, file):
        self.field.intermediateExchangeId = uuid_from_uuid(
            *(self.id_,), *type(self).uuid_specs)
        self.field.name = [ILCD1Helper.text_add_index(x, index=1) for x in self.info['name']] # Only one flow name
        
        self.get_properties(file)

        if not self.main:
            self.isConvertible = False
            logging.warning(f"Flow {self.info['name']} : {self.id_} not converted as unit is not a valid ILCD unit")
            return
        
        self.amount.multiply(up.Quantity(1, self.main[1].replace(' ', '_')))
        self.amount.calculate_unc(self.field)
        self.field.unitName = ILCD1Helper.text_dict_from_text(0, self.main[1])
        self.field.unitId = self.main[0]
        
        if self.info.get('CAS'):
            self.field.casNumber = self.info['CAS']
        if self.info.get('synonym'):
            self.field.synonym = self.info['synonym']
        
        self.master = type(self).master_field.get_class('intermediateExchange')()

        self.master.id = uuid_from_uuid(*(self.id_,), *type(self).uuid_specs)
        self.mtype = 'intermediateExchange'
        self.master.name = [ILCD1Helper.text_add_index(x, index=1) for x in self.info['name']] # Only one flow name
        self.master.unitName = ILCD1Helper.text_dict_from_text(0, self.main[1])
        self.master.unitId = self.main[0]
        

    def finish_flow_info(self, final = False):
        id_ = uuid_from_string(
            type(self).uuid_process + self.info['name'][0]['#text']) # Assumed the first name
        if id_ in type(self)._all_flow_ids:
            i = 0
            while id_ in type(self)._all_flow_ids:
                i += 1
                id_ = uuid_from_string(type(self).uuid_process + self.info['name'][0]['#text'] + str(i)) # TODO See in the ILCD conv too
            self.field.id = id_
        else:
            self.field.id = id_
        type(self)._all_flow_ids.add(id_)
            
        self.field.comment = self.comment
        self.field.amount = self.amount.m

        if self.isReference:
            self.field.outputGroup = 0
        else:
            if self.group == 'Input':
                self.field.inputGroup = {
                    'Elementary flow': 4,
                    'Product flow': 5,
                    'Waste flow': 5,
                    'Other flow': 5
                    }.get(self.info['type'])
            else:
                self.field.outputGroup = {
                    'Elementary flow': 4,
                    'Product flow': 2,
                    'Waste flow': 3,
                    'Other flow': 2 # This flow makes no sense, but has to be converted to the closest possible option
                    }.get(self.info['type'])

        if hasattr(self, 'variable'):
            self.field.variableName = self.variable.name
            self.master.defaultVariableName = self.variable.name
            if self.variable.formula:
                self.field.mathematicalRelation = self.variable.formula
                self.field.isCalculatedAmount = True

        if hasattr(self, 'properties'):
            self.properties = {k: v for k,
                               v in self.properties.items() if v.isConvertible}
            self.properties = self.Property.convert_properties(
                self.properties, self, type(self)._use_md_prop)
            if hasattr(self, 'alloc_properties'):
                self.properties.extend([self.Property.allocation_init(
                    {'@lang': 'en', '#text': k}, v, self.master) for k, v in self.alloc_properties.items()])
            for p in self.properties:
                self.field.property = p.field
        
        if not final:
            setattr(type(self).master_field, self.mtype, self.master)
    
    def set_field(self, ref):
        if self.isConvertible:
            if ref is not None:
                for x in ensure_list(ref.get('referenceToDataSource', {})):
                    type(self).source_ref_conversion(x, self.not_converted,
                                                     {'regular': self.field},
                                                     {'id': 'sourceId',
                                                         'first_author': 'sourceFirstAuthor',
                                                         'year': 'sourceYear',
                                                         'page': 'pageNumbers'}).get_source()  # [!] Make take the get_source and get_contact out
            if self.info['type'] == 'Elementary flow':
                setattr(type(self).flow_holder,
                        'elementaryExchange', self.field)
            else:
                setattr(type(self).flow_holder,
                        'intermediateExchange', self.field)


class ILCD1ToECS2ReferenceConversion:

    uuid_specs = None
    elem_flow_mapping = None

    class_conversion = None

    _ilcd_root_path = None

    def __init__(self, x, not_converted):
        self.not_converted = not_converted
        self.file = type(self).get_file(x, type(self).type_)
        self.isConvertible = True if self.file else False
        if x.get('@refObjectId'):
            self.id_ = x['@refObjectId']
        else: self.isConvertible = False
        self.shortDescription = x.get('shortDescription', {})
        self.get_not_converted(x)

    def get_not_converted(self, x):
        pass

    @classmethod
    def get_file(cls, x, type_):
        path = Path(cls._ilcd_root_path, type_)
        if path.is_dir():
            options = (x.get('@uri', '').split('/')[-1],
                       x.get('@refObjectId', '')+'_'+
                       x.get('@version', '')+'.xml',
                       x.get('@refObjectId', '')+'.xml')
            for option in options: # Prioritize this
                p = Path(path, option)
                if p.exists() and p.is_file():
                    return p
                #for file in path.glob('*xml'):
                #    if file.name == option:
                #        return file
            else:
                if x.get('@refObjectId'): # Versions could be mismatched from the process and flow
                    for file in os.listdir(path): # path.glob('*xml'):
                        if x['@refObjectId'] in file: # .name:
                            return Path(path, file)

                logging.warning(
                    f"\t\tfile of type '{type_}' and id '{x.get('@refObjectId', '[no ID]')}' not found")
                Print.output(f"\tfile of type '{type_}' and id '{x.get('@refObjectId', '[no ID]')}' not found")
                return None
        else:
            logging.warning(f"\t\tfolder of type '{type_}' not found")
            Print.output(f"\tfolder of type '{type_}' not found")
            return None

    def set_attr(self, cl, field):
        if self.isConvertible:
            setattr(cl, field, self.field)


class ILCD1ToECS2SourceReferenceConversion(ILCD1ToECS2ReferenceConversion):
    
    type_ = 'sources'
    
    master_field = None
    
    _all_sources = set()

    def __init__(self, x, not_converted, field, attrname, uri_source=False):
        super().__init__(x, not_converted)
        self.attrname = attrname
        short_des = x.get("shortDescription", {'#text': ''})['#text']
        if short_des.startswith("Image URL from "):
            self.subtype = 'imageUrl'
        elif short_des == "Dataset Icon":
            self.subtype = 'datasetIcon'
        elif uri_source:
            # For cases like the technology pictogramme where the source is really an imageUrl
            self.subtype = 'imageUrl'
        else:
            self.subtype = 'regular'
        self.field = field[self.subtype]

    def get_master_source(self, id_, fa, yr, title, type_='0'):
        if id_ not in type(self)._all_sources:
            src = type(self).master_field.get_class('source')()
            src.id = id_
            src.sourceType = type_
            src.firstAuthor = fa
            src.year = yr
            src.title = title
            setattr(type(self).master_field, 'source', src)
            type(self)._all_sources.add(id_)

    def get_source(self):  # Remember TTextAndImage are Unique :3
        if self.isConvertible:
            with open(self.file) as f:
                if self.subtype in ('imageUrl', 'datasetIcon'):
                    map_ = {'/sourceDataSet/sourceInformation/dataSetInformation/referenceToDigitalFile/@uri':
                            lambda x: ILCD1Helper.add_index({'#text': x}) if self.subtype == 'imageUrl' else x}
                    for k, t in XMLStreamIterable(f, map_):
                        setattr(self.field, self.subtype, map_[k](t))
                else:
                    map_ = {'/sourceDataSet/sourceInformation/dataSetInformation/sourceCitation': lambda x, t: x.__setitem__('citation', t),
                            '/sourceDataSet/sourceInformation/dataSetInformation/shortName': lambda x, t: x.__setitem__('name', t['#text'])
                            }  # [!] classification, timestamp, dataSetVersion and permanentDataSetURI for not_converted
                    info = {}
                    for path, t in XMLStreamIterable(f, map_):
                        map_[path](info, t)

                    id_ = uuid_from_uuid(self.id_, b'\__Lav_IL1EC2__/', "flow_conversion_2")
                    setattr(self.field, self.attrname['id'], id_)
                    if re.search(r'[ \(\[,](\d{4})[\)\]] p\. (.*)$', info.get('citation', info['name'])):
                        n = re.search(
                            "(.*)[ \(\[,](\d{4})[\)\]] p\. (.*)$", info.get('citation', info['name'])).groups()
                        fa = n[0].strip()[:-1]
                        yr =  n[1].strip()
                        setattr(
                            self.field, self.attrname['page'], n[2].strip())
                        setattr(
                            self.field, self.attrname['year'], n[1].strip())
                        setattr(
                            self.field, self.attrname['first_author'], fa)
                    elif re.search("[ \(\[,](\d{4})[\)\]](?:.*)$", info.get('citation', info['name'])):
                        n = re.search(
                            "(.*)[ \(\[,](\d{4})[\)\]](?:.*)$", info.get('citation', info['name']).strip()).groups()
                        fa = n[0].strip()[:-1]
                        yr = n[1].strip()
                        setattr(
                            self.field, self.attrname['year'], n[1].strip())
                        setattr(
                            self.field, self.attrname['first_author'], fa)
                    else:
                        logging.info(
                            f"\t\tYear could not be converted for source {info['name']} with id {self.id_}")
                        fa = info['name'].strip()
                        yr = "0000"
                        setattr(
                            self.field, self.attrname['first_author'], fa)
                        
                    self.get_master_source(id_, fa, yr, info.get('citation', info['name']).strip())


class ILCD1ToECS2ContactReferenceConversion(ILCD1ToECS2ReferenceConversion):

    type_ = 'contacts'

    master_field = None
    
    _all_contacts = set()

    def __init__(self, x, not_converted, field, attrname):
        super().__init__(x, not_converted)
        self.attrname = attrname
        self.field = field
        
        # This is done due to problems with lack of contact files (even with self.isConvertible being False)
        if hasattr(self, 'id_'):
            setattr(self.field, self.attrname['id'], self.id_)
            setattr(self.field, self.attrname['name'], self.shortDescription.get('#text', ''))
            if self.attrname.get('email'):
                setattr(self.field, self.attrname['email'], '')
    
    def get_master_contact(self, id_, name, email=None):
        if id_ not in type(self)._all_contacts:
            if self.attrname['name'] == 'companyCode':
                src = type(self).master_field.get_class('company')()
                src.code = name
                n = 'company'
            else:
                src = type(self).master_field.get_class('person')()
                n = 'person'
                src.email = email or '' # mandatory
                src.name = name
            src.id = id_
            setattr(type(self).master_field, n, src)
            type(self)._all_contacts.add(id_)

    def get_contact(self):
        if self.isConvertible:
            with open(self.file) as f:
                map_ = {'/contactDataSet/contactInformation/dataSetInformation/name': lambda x, t: x.__setitem__('name', t['#text']),
                        '/contactDataSet/contactInformation/dataSetInformation/shortName': lambda x, t: x.__setitem__('sname', t['#text']),
                        '/contactDataSet/contactInformation/dataSetInformation/email': lambda x, t: x.__setitem__('email', t)}
                info = {}
                for path, t in XMLStreamIterable(f, map_):
                    map_[path](info, t)

                id_ = uuid_from_uuid(self.id_, b'\__Lav_IL1EC2__/', "flow_conversion_2")
                setattr(self.field, self.attrname['id'], id_)
                # The reference name is enough
                #print('\n---->', info.get('sname', info.get('name')))
                #setattr(self.field, self.attrname['name'], info.get(
                #    'sname', info.get('name'))) # Generaly, it is used the shortname in the reference
                if self.attrname.get('email'):
                    setattr(self.field, self.attrname['email'], info.get('email', '')) # Email is not mandatory in ILCD
                    
                self.get_master_contact(id_, info['name'], info.get('email'))


class ILCD1ToECS2FlowReferenceConversion(ILCD1ToECS2ReferenceConversion):

    type_ = 'flows'

    def __init__(self, x, not_converted, flow):
        super().__init__(x, not_converted)
        self.flow = flow

    def get_flow(self):
        if self.isConvertible:
            with open(self.file) as f:

                # classifications = []

                map_ = {'/flowDataSet/modellingAndValidation/LCIMethod/typeOfDataSet':
                            lambda x, t: x.__setitem__('type', t),
                        '/flowDataSet/flowInformation/dataSetInformation/name/baseName':
                            lambda x, t: x.__setitem__('name', x.get('name', []) + ensure_list(t, ensure_text=True)), # Multilang
                        '/flowDataSet/flowInformation/dataSetInformation/CASNumber':
                            lambda x, t: x.__setitem__('CAS', t),
                        '/flowDataSet/flowInformation/dataSetInformation/sumFormula':
                            lambda x, t: x.__setitem__('formula', t),
                        # '/flowDataSet/flowInformation/dataSetInformation/synonyms':
                        #     lambda x, t: x.__setitem__(
                        #         'synonym', x.get('synonym', []) + [
                        #             {'@index': i, '@lang': t['@lang'] if isinstance(t, dict) else 'en', '#text': y} for i, y in enumerate(chain(
                        #                 *[n['#text'].split(';') for n in ensure_list(t, ensure_text=True)]))]),
                        '/flowDataSet/flowInformation/quantitativeReference/referenceToReferenceFlowProperty':
                            lambda x, t: x.__setitem__(
                                'reference', t),
                        # TODO
                        # '/flowDataSet/flowInformation/dataSetInformation/classificationInformation/classification':
                        #     lambda x, t: classifications.append(
                        #         type(self).class_conversion(t, self.not_converted).field),
                        # General comment of flow not converted as it is a duplication
                        }
                info = {}
                for path, t in XMLStreamIterable(f, map_):
                    map_[path](info, t)

                self.flow.isConvertible = True
                # Flow information dependent on the flow data set file
                # Get a list of not-converted flows when possible for GLAD
                if info['type'] == 'Elementary flow':
                    self.flow.field = type(self.flow).flow_holder.get_class(
                        'elementaryExchange')()
                    n = type(self).elem_flow_mapping.get(self.flow.id_, None)
                    if n is not None:
                        if n['MapType'] not in ("NO_MATCH_MAPPING", "NO MATCH"):
                            self.flow.info = info
                            self.flow.get_elementary_flow_info(n, self.file)
                        else:
                            self.flow.isConvertible = False
                            logging.warning(
                                "\t\tFlow not converted due to lack of elementary flow correspondence in the mapping file")
                            Print.output(f"\tFlow '{self.flow._name}' not converted due to lack of elementary flow correspondence in the mapping file")
                    else:
                        self.flow.isConvertible = False
                        logging.warning(
                            "\t\tFlow not converted as the flow is not present on the elementary flow mapping file")
                        Print.output(f"\tFlow '{self.flow._name}' not converted as the flow is not present on the elementary flow mapping file")
                else:
                    self.flow.field = type(self.flow).flow_holder.get_class(
                        'intermediateExchange')()
                    self.flow.info = info
                    self.flow.get_intermediate_flow_info(self.file)

                if self.flow.isConvertible:
                    self.flow.finish_flow_info()
                    # TODO
                    # if info['type'] != 'Elementary flow' and classifications:
                    #     setattr(self.flow.field, 'classification', type(
                    #         self).class_conversion.organize(classifications, 'CPC'))
                    # else:
                    #     pass # Implement not converted instance for elementary exchanges
        else:
            self.flow.isConvertible = False
        return self.flow


class ILCD1ToECS2ClassificationConversion:

    _defaults = {
        "ISIC rev.4 ecoinvent": "d6fe4ff7-31ec-4037-bc34-fbd2cf071c50",
        "EcoSpold01Categories": "47f2f263-6166-4db0-9886-bc31bd8c70d7",
        "CPC": "b6106531-feeb-4e5f-ac73-2c716e3738cd",
        "By-product classification": "4a8680f8-67ed-4617-bb83-e82ee882f92f"
    }

    class_mapping = None

    class_holder = None
    
    master_field = None
    
    def __init__(self, x, not_converted):
        return # This is deprecated as the mapping is bad
        
        # # Set instances
        # self.field = self.class_holder.get_class('classification')()
        # self.not_converted = not_converted
        # self.master = type(self).master_field.get_class('classificationSystem')()
        # self.clv = self.master.get_class('classificationValue')()

        # # Used variables
        # self.name = "ILCD" if not x.get("@name") else x["@name"]
        # if self.name in type(self)._defaults.keys():
        #     if self.name != 'EcoSpold01Categories':
        #         self.value = ensure_list(x['class'])[-1]["#text"]
        #     else:
        #         self.value = '/'.join([x['#text']
        #                               for x in ensure_list(x['class'])])
        # else: # It can be equal {}
        #     self.value = '/'.join([x['#text']
        #                           for x in ensure_list(x.get('class', {}))])

        # # Get basic fields
        # self.field.classificationSystem = {
        #     '@index': 0, '@lang': 'en', '#text': self.name}
        # self.master.id = uuid_from_string(self.name)
        # self.master.type = 3 # TODO
        # self.master.name = {'@index': 0, '@lang': 'en', '#text': self.name}
        # self.field.classificationValue = {
        #     '@index': 0, '@lang': 'en', '#text': self.value}
        # self.clv.name = {'@index': 0, '@lang': 'en', '#text': self.value}
    
        # # Get class fields
        # self.get_classification()
        # setattr(self.master, 'classificationValue', self.clv)
        # setattr(type(self).master_field, 'classificationSystem', self.master)
        
        # # Get not converted
        # self.get_not_converted(x)

    def get_not_converted(self, x):
        pass

    def get_classification(self):
        return # This is deprecated as the mapping is bad
    
        # n = type(self).class_mapping.get(self.name+'/'+self.value)
        # if n is None:
        #     id_ = uuid_from_string(self.name)
        # else:
        #     id_ = n['classificationValueId']
        # self.field.classificationId = id_
        # self.clv.id = id_

    @classmethod
    def organize(cls, classifications, priority):
        for i, c in enumerate(classifications):  # CPC and ISIC have priority
            if c.get('classificationSystem') == priority:
                return [classifications.pop(i)] + classifications
        else:
            return classifications


class ILCD1ToECS2ReviewConversion:

    # _set_TextAndImage = None

    contact_ref_conversion = None

    review_holder = None

    _version = [1, 0, 1, 0]

    def __init__(self, x, not_converted):
        self.not_converted = not_converted
        self.field = type(self).review_holder.get_class('review')()

        # TODO This is just a cameo
        self.field.reviewDate = '1900-01-01' # Default values
        
        if '@type' in x:
            self.field.details.text = ILCD1Helper.text_dict_from_text(1, f'Review type: {x["@type"]}')
        if 'scope' in x:
            txt = 'Review done for Scopes:\n'
            for s in ensure_list(x['scope']):
                txt += f"\t{s.get('@name', '-')}. Validation methods:\n"
                if 'method' in s:
                    for m in ensure_list(s['method']):
                        txt += f"\t\t{m.get('@name', '-')}\n"
            self.field.details.text = ILCD1Helper.text_dict_from_text(2, txt)
                    
        if 'dataQualityIndicators' in x:
            txt = 'Data Quality Indicators:\n'
            for dq in ensure_list(x['dataQualityIndicators'].get('dataQualityIndicator', {})):
                txt += f"\t{dq['@name']}: {dq['@value']}\n"
            self.field.details.text = ILCD1Helper.text_dict_from_text(3, txt)
        
        for review in ensure_list(x.get('reviewDetails', {}), ensure_text=True):
            review = self.review_comment(review)
            self.field.details.text = ILCD1Helper.text_add_index(ILCD1Helper.text_add_index(review))

        for review in ensure_list(x.get('otherReviewDetails', {}), ensure_text=True):
            self.field.otherDetails = ILCD1Helper.text_add_index(review)

        self.ref = x.get('referenceToNameOfReviewerAndInstitution', {}) # Som as more then 1, which are combined into 1
        self.rev_name = []
        for ref in ensure_list(self.ref):
            # This is really one and only one field in ECS2, but in ILCD it is 0 or more
            self.rev_name.append(ensure_list(ref['shortDescription'], ensure_text=True)[0]['#text'])
            type(self).contact_ref_conversion(ref,
                                          not_converted,
                                          self.field,
                                          {'id': 'reviewerId', 'name': 'reviewerName', 'email': 'reviewerEmail'}).get_contact()
        
        # TODO The review version has to be revisited as it is too irregular
        if not self.field.get('reviewedMajorRelease'):
            v = type(self)._version
            self.field.reviewedMajorRelease, self.field.reviewedMinorRelease = v[0], v[1]
            self.field.reviewedMajorRevision, self.field.reviewedMinorRevision = v[
                2], v[3]
            type(self)._version[2] += 1
            
        if self.field.get('reviewerName') == '/'.join(self.rev_name): # Depends on the contact info
            self.field.reviewerId = uuid_from_string('/'.join(self.rev_name))

        self.get_not_converted(x)

    def review_comment(self, x):
        if re.search(r'Review Version: [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\n', x['#text']):
            v = re.search(
                r'Review Version: ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\n', x['#text']).groups()[0].split('.')
            x['#text'] = re.sub(r'Review Version: ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\n', '', x['#text'])
            self.field.reviewedMajorRelease, self.field.reviewedMinorRelease = v[0], v[1]
            self.field.reviewedMajorRevision, self.field.reviewedMinorRevision = v[
                2], v[3]
        if re.search(r'Date of Review: [0-9 -]+\n', x['#text']):
            date = re.search(
                r'Date of Review: ([0-9 -]+)\n', x['#text']).groups()[0]
            self.field.reviewDate = date
            x['#text'] = re.sub(r'Date of Review: [0-9 -]+\n', '', x['#text'])
        return x

    def set_field(self, struct, field): # Checks if there is an id, name and email for reviewer (mandatory)
        if self.ref:
            setattr(struct, field, self.field)
        else:
            pass # TODO call get_not_converted

    def get_not_converted(self, x):
        # scope with methods and scores
        # quality indicators
        # report from referenceToCompleteReviewReport
        # @type of review
        pass

# Field mapping for conversion


class ILCD1ToECS2BasicFieldMapping(FieldMapping, ABC):

    # Conversion Defaults
    _uuid_conv_spec = (b'\__Lav_IL1EC2__/', 'flow_conversion_2')
    _default_language = 'en'
    _default_compartment_mapping = FieldMapping._dict_from_file(
        Path("Mappings/ilcd1_to_ecs2_compartments.json"))
    _default_geographies_mapping = FieldMapping._dict_from_file(
        Path("Mappings/ilcd1_to_ecs2_geographies.json"))
    _default_master_data_property = FieldMapping._dict_from_file(
        Path("Mappings/ecs2_master_data_properties.json"))

    # Converter/Factory Defaults
    _default_files = None
    _default_elem_mapping = None
    # _default_class_mapping = Path("Mappings/ilcd1_to_ecs2_classes.json")

    # Configuration Defaults
    _convert_additional_fields = True
    
    # Additional Options
    convert_user_data = None
    use_master_data_properties = None
    sum_same_elementary_amounts = None

    def set_mappings(self, ef_map):
        self._elem_mapping = self._dict_from_file(
            ef_map or type(self)._default_elem_mapping, 'SourceFlowUUID')
        # self._class_mapping = self._dict_from_file(
        #     type(self)._default_class_mapping, 'SourceFlowUUID')
        # Attributions
        self.ReferenceConversion.elem_flow_mapping = self._elem_mapping
        self.ClassificationConversion.class_mapping = self._class_mapping
        self.FlowConversion.compartment_mapping = type(
            self)._default_compartment_mapping
        self.FlowConversion.property_master_data = type(
            self)._default_master_data_property

    def __init__(self):

        self.Amount = ILCD1ToECS2Amount
        self.UncertaintyConversion = ILCD1ToECS2UncertaintyConversion
        self.SourceReferenceConversion = ILCD1ToECS2SourceReferenceConversion
        self.ContactReferenceConversion = ILCD1ToECS2ContactReferenceConversion
        self.FlowReferenceConversion = ILCD1ToECS2FlowReferenceConversion
        self.ReferenceConversion = ILCD1ToECS2ReferenceConversion
        self.FlowConversion = ILCD1ToECS2FlowConversion
        self.VariableConversion = ILCD1ToECS2VariableConversion
        self.ClassificationConversion = ILCD1ToECS2ClassificationConversion
        self.ReviewConversion = ILCD1ToECS2ReviewConversion
        self.NotConverted = ILCD1ToECS2DataNotConverted()

    def start_conversion(self):
        ILCD1Helper.default_language = type(self)._default_language
        self.ReferenceConversion.uuid_specs = type(self)._uuid_conv_spec
        self.FlowConversion.uuid_specs = type(self)._uuid_conv_spec
        self.FlowConversion._use_md_prop = type(self).use_master_data_properties

        self.Amount.uncertainty_conversion = self.UncertaintyConversion
        self.ReferenceConversion.class_conversion = self.ClassificationConversion
        self.FlowConversion.variable_conversion = self.VariableConversion
        self.ReviewConversion.contact_ref_conversion = self.ContactReferenceConversion
        self.FlowConversion.source_ref_conversion = self.SourceReferenceConversion

        self.VariableConversion.amountClass = self.Amount
        self.FlowConversion.amountClass = self.Amount
        self.FlowConversion.Property.amountClass = self.Amount

    def end_conversion(self):
        ILCD1ToECS2BasicFieldMapping.reset_conversion(self)
        self.get_statistics()

    def reset_conversion(self):
        ILCD1Helper.number = 1000
        self.VariableConversion._available_variables = {}
        self.VariableConversion._non_conform_variables = {}
        self.FlowConversion._reference_flows = []
        self.FlowConversion._flow_internal_refs = None
        self.FlowConversion._all_em_flows = set()
        self.FlowConversion._all_flow_ids = set()
        self.FlowConversion.Property._energy = []
        self.ReferenceConversion._ilcd_root_path = None
        self.SourceReferenceConversion._all_sources = set()
        self.ContactReferenceConversion._all_contacts = set()
        self.ReviewConversion._version = [1, 0, 1, 0]

    def set_file_info(self, path, save_path):
        # Attributions
        self.ReferenceConversion._ilcd_root_path = path

    def set_output_class_defaults(self, cl_struct):
        
        self._class_holder = cl_struct.activityDescription
        self._energy_holder = cl_struct.activityDescription.activity
        self._lci_ma_holder = cl_struct.modellingAndValidation.representativeness
        self._access_restriction_holder = cl_struct.administrativeInformation.dataGeneratorAndPublication
        self._master_system_model_holder = cl_struct.userMaster
        self._master_activity_name_holder = cl_struct.userMaster.get_class('activityName')()

        self._tai = cl_struct.textAndImage
        self.VariableConversion.parameter_holder = cl_struct.flowData
        self.FlowConversion.flow_holder = cl_struct.flowData
        self.FlowConversion.Property.property_holder = cl_struct.property
        self.ClassificationConversion.class_holder = cl_struct.activityDescription
        self.ReviewConversion.review_holder = cl_struct.modellingAndValidation
        
        self.SourceReferenceConversion.master_field = cl_struct.userMaster
        self.ContactReferenceConversion.master_field = cl_struct.userMaster
        self.FlowConversion.master_field = cl_struct.userMaster
        self.FlowConversion.Property.master_field = cl_struct.userMaster
        self.VariableConversion.master_field = cl_struct.userMaster
        self.ClassificationConversion.master_field = cl_struct.userMaster


class ILCD1ToECS2FieldMapping(ILCD1ToECS2BasicFieldMapping):

    # File pre-mapping attribute
    _flow_internal_refs = None

    def get_statistics(self):
        pass

    def set_file_info(self, *args):
        ref = type(self)._flow_internal_refs
        self.FlowConversion._flow_internal_refs = {
            ref[i][0]: ref[i][1] for i in range(len(ref))}
        # self.ReviewConversion._set_TextAndImage = self.set_TextAndImage
        super().set_file_info(*args)

    def default(self, cl_struct):
        # mapping_options that influence the structure can't be done set_output_class_defaults
        type(cl_struct).convert_user_data = type(self).convert_user_data
        
        from .. import __version__
        setattr(cl_struct.activityDescription.macroEconomicScenario,
                'macroEconomicScenarioId', 'd9f57f0a-a01f-42eb-a57b-8f18d6635801')
        setattr(cl_struct.activityDescription.macroEconomicScenario,
                'name', ILCD1Helper.text_dict_from_text(1, 'Business-as-Usual'))
        setattr(cl_struct.activityDescription.activity,
                'inheritanceDepth', 0)
        setattr(cl_struct.activityDescription.timePeriod,
                'isDataValidForEntirePeriod', 1) # Default as True when no other info is presented
        setattr(cl_struct.activityDescription.activity,
                'specialActivityType', 0)
        setattr(cl_struct.activityDescription.technology,
                'technologyLevel', 3) # [!] Too many informations are 'assumed' beforehand
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'defaultLanguage', 'en')  # TODO Can be better
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'fileGenerator', f"Lavoisier version {__version__}")
        t = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'lastEditTimestamp', t)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'fileTimestamp', t)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'creationTimestamp', t)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'internalSchemaVersion', '2.0.10')
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'majorRelease', 1)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'minorRelease', 0)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'majorRevision', 0)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'minorRevision', 0)

        setattr(cl_struct.administrativeInformation.fileAttributes,
                'contextId', "de659012-50c4-4e96-b54a-fc781bf987ab")
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'contextName', ILCD1Helper.text_dict_from_text(1, 'ecoinvent'))
        
        setattr(cl_struct.userMaster.activityIndexEntry,
                'specialActivityType', 0)

    # Setting variables that help conversions that depend on more than one field
    def start_conversion(self):
        # self._main_classifications = []
        self._LCI_MA = []
        self._original_model = None
        self._access_restricted_to = None
        super().start_conversion()

    def reset_conversion(self, end=False):
        # setattr(self._class_holder, 'classification',
        #         self.ClassificationConversion.organize(self._main_classifications,
        #                                                'ISIC rev.4 ecoinvent'))
        # self._main_classifications = []

        # [!] This is too random, maybe think about a better way
        if self._original_model is not None:
            setattr(self._lci_ma_holder, 'systemModelId',
                    system_model_1_.get(self._original_model))
            setattr(self._lci_ma_holder, 'systemModelName',
                    ILCD1Helper.text_dict_from_text(1, self._original_model))
            setattr(self._master_system_model_holder.activityIndexEntry, 'systemModelId',
                    system_model_1_.get(self._original_model))
        elif self._LCI_MA:
            c = Counter([x for x in self._LCI_MA]).most_common(1)[0][0]
            setattr(self._lci_ma_holder, 'systemModelId', c[1])
            setattr(self._lci_ma_holder, 'systemModelName',
                    ILCD1Helper.text_dict_from_text(1, c[0]))
            setattr(self._master_system_model_holder.activityIndexEntry, 'systemModelId',
                    c[1])
        else:
            setattr(self._lci_ma_holder, 'systemModelId',
                    "8b738ea0-f89e-4627-8679-433616064e82")
            setattr(self._lci_ma_holder, 'systemModelName',
                    ILCD1Helper.text_dict_from_text(1, 'Undefined'))
            setattr(self._master_system_model_holder.activityIndexEntry, 'systemModelId',
                           "8b738ea0-f89e-4627-8679-433616064e82")
        self._original_model = None
        self._LCI_MA = []

        if not self._energy_holder.get('energyValues'):
            energy = self.FlowConversion.Property._energy
            n = sum(1 if x == "NET" else 0 for x in energy)
            g = sum(1 if x == "GROSS" else 0 for x in energy)
            if n >= 3*g:
                setattr(self._energy_holder, "energyValues", '1')
            elif g >= 3*n:
                setattr(self._energy_holder, "energyValues", '2')
            else:
                setattr(self._energy_holder, "energyValues", '0')

        if self._access_restricted_to:
            setattr(self._access_restriction_holder, 'accessRestrictedTo',
                    self._access_restricted_to)
        self._access_restricted_to = None

        self.VariableConversion.create_parameters()
        
        setattr(self._master_system_model_holder, 'activityName', self._master_activity_name_holder) # TODO
        
        if type(self).sum_same_elementary_amounts:
            double_el_flow = defaultdict(list)
            for flow in self.FlowConversion._all_em_flows:
                double_el_flow[(flow.field.get('elementaryExchangeId'), flow.group)].append(flow)
            df = [x for k, x in double_el_flow.items() if len(x) > 1]
            
            for flow in df: # Allocation, Uncertainty and overall comments and properties of previous data are not converted
                
                for f in flow[1:]:
                    flow[0].amount.sum_(f.amount, flow[0].field)
                
                # if not type(self).use_master_data_properties:
                del flow[0].properties
                if hasattr(flow[0], 'variable'):
                    del flow[0].variable
                flow[0].finish_flow_info(final=True)
                
                n = self.FlowConversion.master_field.get('elementaryExchange')
                for f in flow:
                    n.pop(self.FlowConversion.master_field.get('elementaryExchange').index(f.master))
                del self.FlowConversion.master_field['elementaryExchange']
                for x in n:
                    self.FlowConversion.master_field.elementaryExchange = x
                
                setattr(self.FlowConversion.master_field, flow[0].mtype, flow[0].master)
                
                n = self.FlowConversion.flow_holder.get('elementaryExchange')
                for f in flow[1:]:
                    n.pop(self.FlowConversion.flow_holder.get('elementaryExchange').index(f.field))
                del self.FlowConversion.flow_holder['elementaryExchange']
                for x in n:
                    self.FlowConversion.flow_holder.elementaryExchange = x

        if not end:
            super().reset_conversion()

    def end_conversion(self):
        self.reset_conversion(end=True)
        super().end_conversion()

    # def set_TextAndImage(self, x, inst):
    #     tai = self._tai()
    #     setattr(tai, 'text', ILCD1Helper.text_add_index(x))
    #     return tai

    def general_comment(self, cl_struct, x):
        x['#text'] = ECS2Helper._get_uuid(cl_struct.activityDescription.activity,
                                          'activityNameId',
                                          r'Activity Linkable Id:',
                                          x['#text'],
                                          extra=lambda x: (setattr(cl_struct.userMaster.activityIndexEntry,
                                                                  'activityNameId',
                                                                  x),
                                                           setattr(self._master_activity_name_holder,
                                                                   'id', x))
                                          )
        x['#text'] = ECS2Helper._get_str(cl_struct.activityDescription.activity,
                                         'specialActivityType',
                                         special_activity_,
                                         r'Activity Subtype:',
                                         x['#text'],
                                         extra=lambda x: (setattr(cl_struct.userMaster.activityIndexEntry,
                                                                 'specialActivityType',
                                                                 x),
                                                          setattr(cl_struct.activityDescription.activity,
                                                                  'specialActivityType',
                                                                  x)))
        x['#text'] = ECS2Helper._get_str(cl_struct.activityDescription.activity,
                                         'inheritanceDepth',
                                         child_type_,
                                         r'Inheritance:',
                                         x['#text'])
        x['#text'] = ECS2Helper._get_uuid(cl_struct.activityDescription.activity,
                                          'parentActivityId',
                                          r'Parent Id:',
                                          x['#text'],
                                          extra=lambda x: (setattr(cl_struct,
                                                                   'main_activity_type',
                                                                   'childActivityDataset'),
                                                           setattr(cl_struct.activityDescription.activity,
                                                                   'inheritanceDepth',
                                                                   '-1')))
        x['#text'] = ECS2Helper._get_list_str(cl_struct.activityDescription.activity,
                                              'tag',
                                              r'Tag:',
                                              x['#text'])
        return ILCD1Helper.text_add_index(x)

    def time_comment(self, cl_struct, x):
        x['#text'] = ECS2Helper._get_str(cl_struct.activityDescription.timePeriod,
                                         'isDataValidForEntirePeriod',
                                         time_period_,
                                         r'Validity:',
                                         x['#text'])
        return ILCD1Helper.text_add_index(x)

    def tech_comment(self, cl_struct, x):
        if re.search(r'Activity Start: (.*)\nActivity End: ', x['#text']):
            setattr(cl_struct.activityDescription.activity,
                    'includedActivitiesStart',
                    ILCD1Helper.text_dict_from_text(1, re.search(r'Activity Start: (.*)\nActivity End: ', x['#text']).groups()[0]))
            x['#text'] = re.sub(r'Activity Start: (.*)\n', '', x['#text'])
        if re.search(r'Activity End: (.*)(?:\n|;|$)', x['#text']):
            setattr(cl_struct.activityDescription.activity,
                    'includedActivitiesEnd',
                    ILCD1Helper.text_dict_from_text(2, re.search(r'Activity End: (.*)(?:\n|;|$)', x['#text']).groups()[0]))
            x['#text'] = re.sub(
                r'Activity End: (.*)(?:\n|;|$)', '', x['#text'])
        x['#text'] = ECS2Helper._get_str(cl_struct.activityDescription.technology,
                                         'technologyLevel',
                                         tech_,
                                         r'Technology Level:',
                                         x['#text'])
        return ILCD1Helper.text_add_index(x)

    def modelling_constants(self, cl_struct, x):
        x['#text'] = ECS2Helper._get_str(cl_struct.activityDescription.activity,
                                         'energyValues',
                                         energy_,
                                         r'Energy:',
                                         x['#text'])
        return x

    def deviation_comment(self, x):
        if re.search(r'Original ecoinvent System Model: (.*)+?$', x['#text']):
            self._original_model = re.search(
                r'Original ecoinvent System Model: (.*)+?$', x['#text']).groups()[0]
            x['#text'] = re.sub(
                r'Original ecoinvent System Model: (.*)+?$', '', x['#text'])
        return x

    def ensure_dict(self, x):
        if isinstance(x, str):
            return {'@lang': 'en', '#text': x}
        else: return x

    def new_geography_master(self, x, struct):
        if type(self)._default_geographies_mapping.get(x) is None:
            geo = struct.get_class('geography')()
            geo.id = uuid_from_string(x)
            geo.name = ILCD1Helper.text_dict_from_text(1, x)
            geo.shortname = ILCD1Helper.text_dict_from_text(1, x)
            setattr(struct, 'geography', geo)
            setattr(struct.activityIndexEntry, 'geographyId', uuid_from_string(x)),
        else:
            setattr(struct.activityIndexEntry, 'geographyId', type(self)._default_geographies_mapping.get(x)),

    def mapping(self):
        _keys = {
            '/processDataSet/processInformation/dataSetInformation/UUID':
                lambda cl_struct, x: (setattr(cl_struct.activityDescription.activity, 'id', uuid_from_uuid(*(x,), *self._uuid_conv_spec)),
                                      setattr(self.FlowConversion, 'uuid_process', x),
                                      setattr(cl_struct.userMaster.activityIndexEntry, 'id', uuid_from_uuid(*(x,), *self._uuid_conv_spec))),
            # [!] activityNameId is created here since it is mandatory
            '/processDataSet/processInformation/dataSetInformation/name/baseName':
                lambda cl_struct, x: (logging.info(f"Conversion started for {x['#text']}"),
                                      setattr(cl_struct.activityDescription.activity, 'activityName', ILCD1Helper.text_add_index(x, index=1)),
                                      setattr(cl_struct.activityDescription.activity, 'activityNameId', uuid_from_string(x['#text'])),
                                      setattr(cl_struct.userMaster.activityIndexEntry, 'activityNameId', uuid_from_string(x['#text'])),
                                      setattr(self._master_activity_name_holder, 'id', uuid_from_string(x['#text'])),
                                      setattr(self._master_activity_name_holder, 'name', ILCD1Helper.text_add_index(x, index=1))),
            '/processDataSet/processInformation/dataSetInformation/name/treatmentStandardsRoutes':
                lambda cl_struct, x: (setattr(
                    cl_struct.activityDescription.activity, 'activityName', ILCD1Helper.text_add_index(x, index=1)),
                    setattr(self._master_activity_name_holder, 'name', ILCD1Helper.text_add_index(x, index=1))),
            '/processDataSet/processInformation/dataSetInformation/name/mixAndLocationTypes':
                lambda cl_struct, x: (setattr(
                    cl_struct.activityDescription.activity, 'activityName', ILCD1Helper.text_add_index(x, index=1)),
                    setattr(self._master_activity_name_holder, 'name', ILCD1Helper.text_add_index(x, index=1))),
            '/processDataSet/processInformation/dataSetInformation/name/functionalUnitFlowProperties':
                lambda cl_struct, x: (setattr(
                    cl_struct.activityDescription.activity, 'activityName', ILCD1Helper.text_add_index(x, index=1)),
                    setattr(self._master_activity_name_holder, 'name', ILCD1Helper.text_add_index(x, index=1))),
            '/processDataSet/processInformation/dataSetInformation/identifierOfSubDataSet':
                lambda cl_struct, x: (setattr(self.NotConverted, 'identifierOfSubDataSet', x),
                                      setattr(cl_struct.activityDescription.activity.generalComment, 'text',
                                              ILCD1Helper.text_add_index(ILCD1Helper.text_dict_from_text(1, 'Identifier name: '+x)))),
            '/processDataSet/processInformation/dataSetInformation/synonyms':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.activity, 'synonym', [ILCD1Helper.text_add_index({'@lang': 'en',
                                                                                                                            '#text': n}) for n in x['#text'].split('; ')]),
            '/processDataSet/processInformation/dataSetInformation/complementingProcesses':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'complementingProcesses', x),
            '/processDataSet/processInformation/dataSetInformation/classificationInformation/classification': # TODO
                lambda cl_struct, x: None, # self._main_classifications.append(
                    # self.ClassificationConversion(x, self.NotConverted).field),
            '/processDataSet/processInformation/dataSetInformation/generalComment':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.activity.generalComment, 'text',
                                             self.general_comment(cl_struct, ILCD1Helper.text_add_index(x))),
            '/processDataSet/processInformation/dataSetInformation/referenceToExternalDocumentation':
                lambda cl_struct, x: self.SourceReferenceConversion(x, self.NotConverted,
                                                                    {'imageUrl': cl_struct.activityDescription.activity.generalComment,
                                                                     'datasetIcon': cl_struct.activityDescription.activity},
                                                                    {}).get_source(),
            '/processDataSet/processInformation/quantitativeReference/referenceToReferenceFlow':
                lambda cl_struct, x: self.FlowConversion._reference_flows.append(
                    x),
            '/processDataSet/processInformation/quantitativeReference/functionalUnitOrOther':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'functionalUnitOrOther', x),
            '/processDataSet/processInformation/quantitativeReference/type':
                lambda cl_struct, x: setattr(self.NotConverted, 'type', x),
            '/processDataSet/processInformation/time/referenceYear':
                lambda cl_struct, x: (setattr(
                    cl_struct.activityDescription.timePeriod, 'startDate', x+'-01-01'),
                    setattr(cl_struct.userMaster.activityIndexEntry, 'startDate', x+'-01-01')),
            '/processDataSet/processInformation/time/dataSetValidUntil':
                lambda cl_struct, x: (setattr(
                    cl_struct.activityDescription.timePeriod, 'endDate', x+'-12-31'),
                    setattr(cl_struct.userMaster.activityIndexEntry, 'endDate', x+'-12-31')),
            '/processDataSet/processInformation/time/timeRepresentativenessDescription':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.timePeriod.comment, 'text',
                                             self.time_comment(cl_struct, ILCD1Helper.text_add_index(x))),
            '/processDataSet/processInformation/geography/locationOfOperationSupplyOrProduction/descriptionOfRestrictions':
                lambda cl_struct, x: setattr(
                    cl_struct.activityDescription.geography.comment, 'text',  ILCD1Helper.text_add_index(x)),
            # TODO Some geographies doesn't have a proper conversion (no Id in ECS2), so the master antry has to be added and the 'not_converted' called
            '/processDataSet/processInformation/geography/locationOfOperationSupplyOrProduction/@location':
                lambda cl_struct, x: (setattr(cl_struct.activityDescription.geography, 'shortname', ILCD1Helper.text_dict_from_text(1, x)),
                                      logging.warning(f'\tGeography {x} not found in ecoinvent. Creating new UUID') if type(self)._default_geographies_mapping.get(x) is None else None,
                                      Print.output(f'\t\tGeography {x} not found in ecoinvent. Creating new UUID') if type(self)._default_geographies_mapping.get(x) is None else None,
                                      setattr(cl_struct.activityDescription.geography, 'geographyId',
                                              type(self)._default_geographies_mapping.get(x) or uuid_from_string(x)),
                                      self.new_geography_master(x, cl_struct.userMaster)),
            '/processDataSet/processInformation/geography/locationOfOperationSupplyOrProduction/@latituteAndLongitude':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'latitudeAndLongitude', x),
            '/processDataSet/processInformation/geography/subLocationOfOperationSupplyOrProduction':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'subLocationOfOperationSupplyOrProduction', x),
            '/processDataSet/processInformation/technology/technologyDescriptionAndIncludedProcesses':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.technology.comment, 'text',
                                             self.tech_comment(cl_struct, ILCD1Helper.text_add_index(x))),
            '/processDataSet/processInformation/technology/referenceToIncludedProcesses':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToIncludedProcesses', x),
            '/processDataSet/processInformation/technology/technologyApplicability':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.technology.comment, 'text', ILCD1Helper.text_add_index(ILCD1Helper.text_add_index(x))),
            '/processDataSet/processInformation/technology/referenceToTechnologyPictogramme':
                lambda cl_struct, x: self.SourceReferenceConversion(x, self.NotConverted,
                                                                    {'imageUrl': cl_struct.activityDescription.technology.comment},
                                                                    {}, uri_source=True).get_source(),
            '/processDataSet/processInformation/technology/referenceToTechnologyFlowDiagrammOrPicture':
                lambda cl_struct, x: self.SourceReferenceConversion(x, self.NotConverted,
                                                                    {'imageUrl': cl_struct.activityDescription.technology.comment},
                                                                    {}, uri_source=True).get_source(),
            '/processDataSet/processInformation/mathematicalRelations/modelDescription':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.activity.generalComment, 'text', ILCD1Helper.text_add_index(ILCD1Helper.text_add_index(x))),
            '/processDataSet/processInformation/mathematicalRelations/variableParameter':
                lambda cl_struct, x: self.VariableConversion(
                    x, self.NotConverted),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/typeOfDataSet':
                lambda cl_struct, x: setattr(
                    cl_struct.activityDescription.activity, 'type', type_process_.get(x)),
            # [!] Better verify this information
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/LCIMethodPrinciple':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'LCIMethodPrinciple', x),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/deviationsFromLCIMethodPrinciple':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'extrapolations',
                                             self.deviation_comment(ILCD1Helper.text_add_index(x,
                                                                                               prefix="Deviations from LCI Method Principles: "))) if x['#text'] != 'none' else None,
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/LCIMethodApproaches':
                lambda cl_struct, x: self._LCI_MA.append((system_model_2_.get(x),
                                                          system_model_1_.get(system_model_2_.get(x)))),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/deviationsFromLCIMethodApproaches':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.activity.allocationComment, 'text',
                                             ILCD1Helper.text_add_index(ILCD1Helper.text_add_index(x))) if self.ensure_dict(x)['#text'] != 'none' else None,
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/modellingConstants':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'samplingProcedure',
                                             self.modelling_constants(cl_struct, ILCD1Helper.text_add_index(x, prefix="Modelling Constants: "))),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/deviationsFromModellingConstants':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'extrapolations',
                                             ILCD1Helper.text_add_index(x, prefix="Deviations from Modelling Constants: ")),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/referenceToLCAMethodDetails':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToLCAMethodDetails', x),
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/dataCutOffAndCompletenessPrinciples':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'samplingProcedure',
                                             ILCD1Helper.text_add_index(x, prefix="Data Cut-Off And Completeness Principles: ")),
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/deviationsFromCutOffAndCompletenessPrinciples':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'extrapolations',
                                             ILCD1Helper.text_add_index(x, prefix="Deviations from Cut-Off and Completeness Principles: ")) if x['#text'] != 'none' else None,
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/dataSelectionAndCombinationPrinciples':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'samplingProcedure',
                                             ILCD1Helper.text_add_index(x, prefix="Data Selection and Combination Principles: ")),
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/deviationsFromSelectionAndCombinationPrinciples':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'extrapolations',
                                             ILCD1Helper.text_add_index(x, prefix="Deviations from Data Selection and Combination Principles: ")) if x['#text'] != 'none' else None,
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/dataTreatmentAndExtrapolationsPrinciples':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'samplingProcedure',
                                             ILCD1Helper.text_add_index(x, prefix="Data Treatment and Extrapolations Principles: ")),
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/deviationsFromTreatmentAndExtrapolationPrinciples':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'extrapolations',
                                             ILCD1Helper.text_add_index(x, prefix="Deviations from Data Treatment and Extrapolations Principles: ")) if x['#text'] != 'none' else None,
            # TODO [!] The lack of a source sink is rather concerning
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/referenceToDataHandlingPrinciples':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToDataHandlingPrinciples', x),
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/referenceToDataSource':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToDataSource', x),
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/percentageSupplyOrProductionCovered':
                lambda cl_struct, x: setattr(
                    cl_struct.modellingAndValidation.representativeness, 'percent', x),
            # TODO [!] Can be better
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/annualSupplyOrProductionVolume':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'annualSupplyOrProductionVolume', x),
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/samplingProcedure':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'samplingProcedure',
                                             ILCD1Helper.text_add_index(x, index=0)),
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/dataCollectionPeriod':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'samplingProcedure',
                                             ILCD1Helper.text_add_index(x, prefix="Data Collection Period: ")),
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/uncertaintyAdjustments':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'samplingProcedure',
                                             ILCD1Helper.text_add_index(x, prefix="Uncertainty Adjustments: ")),
            '/processDataSet/modellingAndValidation/dataSourcesTreatmentAndRepresentativeness/useAdviceForDataSet':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'samplingProcedure',
                                             ILCD1Helper.text_add_index(x, prefix="Use Advice for Dataset: ")),
            # TODO [!] Can be better
            '/processDataSet/modellingAndValidation/completeness':
                lambda cl_struct, x: (logging.warning("\tCompleteness information could not be converted as EcoSpold 2 doesn't have matching field(s) for the information"),
                                      Print.output("\tCompleteness information could not be converted as EcoSpold 2 doesn't have matching field(s) for the information"),
                                                      setattr(self.NotConverted, 'completeness', x)),
            '/processDataSet/modellingAndValidation/validation/review':
                lambda cl_struct, x: self.ReviewConversion(x, self.NotConverted).set_field(cl_struct.modellingAndValidation, 'review'),
            # TODO [!] Can be better
            '/processDataSet/modellingAndValidation/complianceDeclarations/compliance':
                lambda cl_struct, x: (logging.warning("\tCompliance information could not be converted as EcoSpold 2 doesn't have matching field(s) for the information"),
                                      Print.output("\tCompliance information could not be converted as EcoSpold 2 doesn't have matching field(s) for the information"),
                                      setattr(self.NotConverted, 'compliance', x)),
            # TODO [!] Can be better
            '/processDataSet/administrativeInformation/commissionerAndGoal':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'commissionerAndGoal', x),
            '/processDataSet/administrativeInformation/dataGenerator/referenceToPersonOrEntityGeneratingTheDataSet':
                lambda cl_struct, x: self.ContactReferenceConversion(x, self.NotConverted,
                                                                     cl_struct.administrativeInformation.dataGeneratorAndPublication,
                                                                     {'id': 'personId',
                                                                      'name': 'personName',
                                                                      'email': 'personEmail'}).get_contact(),
            '/processDataSet/administrativeInformation/dataEntryBy/timeStamp':  # Done in the default
                lambda cl_struct, x: (setattr(cl_struct.administrativeInformation.fileAttributes, 'creationTimestamp', x),
                                      setattr(self.NotConverted, 'timeStamp', x)),
            '/processDataSet/administrativeInformation/dataEntryBy/referenceToDataSetFormat':  # TODO can be better allocated
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToDataSetFormat', x),
            '/processDataSet/administrativeInformation/dataEntryBy/referenceToConvertedOriginalDataSetFrom':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToConvertedOriginalDataSetFrom', x),
            '/processDataSet/administrativeInformation/dataEntryBy/referenceToPersonOrEntityEnteringTheData':
                lambda cl_struct, x: self.ContactReferenceConversion(x, self.NotConverted,
                                                                     cl_struct.administrativeInformation.dataEntryBy,
                                                                     {'id': 'personId',
                                                                      'name': 'personName',
                                                                      'email': 'personEmail'}).get_contact(),
            '/processDataSet/administrativeInformation/dataEntryBy/referenceToDataSetUseApproval':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToDataSetUseApproval', x),
            '/processDataSet/administrativeInformation/publicationAndOwnership/dateOfLastRevision':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'dateOfLastRevision', x),
            '/processDataSet/administrativeInformation/publicationAndOwnership/dataSetVersion':
                lambda cl_struct, x: (setattr(cl_struct.administrativeInformation.fileAttributes, 'majorRelease', int(x.split('.')[0])),
                                      setattr(
                                          cl_struct.administrativeInformation.fileAttributes, 'minorRelease', 0),
                                      setattr(cl_struct.administrativeInformation.fileAttributes, 'majorRevision', int(
                                          x.split('.')[1])),
                                      # Here the version can be 00.00, so there is no 'third' element in the split
                                      setattr(cl_struct.administrativeInformation.fileAttributes, 'minorRevision', int(x.split('.')[2] if len(x.split('.'))==3 else '000'))),
            '/processDataSet/administrativeInformation/publicationAndOwnership/referenceToPrecedingDataSetVersion':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToPrecedingDataSetVersion', x),
            # TODO [!] isn't there a better conversion
            '/processDataSet/administrativeInformation/publicationAndOwnership/permanentDataSetURI':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'permanentDataSetURI', x),
            '/processDataSet/administrativeInformation/publicationAndOwnership/workflowAndPublication':
                lambda cl_struct, x: setattr(cl_struct.administrativeInformation.dataGeneratorAndPublication,
                                             'dataPublishedIn', status_publication_.get(x)),
            '/processDataSet/administrativeInformation/publicationAndOwnership/referenceToUnchangedRepublication':
                lambda cl_struct, x: self.SourceReferenceConversion(x, self.NotConverted,
                                                                    {'regular': cl_struct.administrativeInformation.dataGeneratorAndPublication},
                                                                    {'id': 'publishedSourceId',
                                                                        'first_author': 'publishedSourceFirstAuthor',
                                                                        'year': 'publishedSourceYear',
                                                                        'page': 'pageNumbers'}).get_source(),
            '/processDataSet/administrativeInformation/publicationAndOwnership/referenceToRegistrationAuthority':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToRegistrationAuthority', x),
            '/processDataSet/administrativeInformation/publicationAndOwnership/registrationNumber':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'registrationNumber', x['#text']),
            '/processDataSet/administrativeInformation/publicationAndOwnership/referenceToOwnershipOfDataSet':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToOwnershipOfDataSet', x),
            '/processDataSet/administrativeInformation/publicationAndOwnership/copyright':
                lambda cl_struct, x: setattr(cl_struct.administrativeInformation.dataGeneratorAndPublication,
                                             'isCopyrightProtected', x),
            '/processDataSet/administrativeInformation/publicationAndOwnership/referenceToEntitiesWithExclusiveAccess':
                lambda cl_struct, x: (self.ContactReferenceConversion(x, self.NotConverted,  # Only using the last entry
                                                                      cl_struct.administrativeInformation.dataGeneratorAndPublication,
                                                                      {'id': 'companyId',
                                                                       'name': 'companyCode'}).get_contact(),
                                      setattr(self, '_access_restricted_to', 3)),
            '/processDataSet/administrativeInformation/publicationAndOwnership/licenseType':
                lambda cl_struct, x: setattr(
                    self, '_access_restricted_to', restrictions_.get(x)),
            '/processDataSet/administrativeInformation/publicationAndOwnership/accessRestrictions':  # TODO Licensees; Licensees
                lambda cl_struct, x: setattr(
                    # Considered '1' as a default
                    self._access_restriction_holder, 'accessRestrictedTo', access_.get(x['#text'].split(';')[0])) if access_.get(x['#text'].split(';')[0]) is not None else '1', 
            '/processDataSet/exchanges/exchange':
                lambda cl_struct, x: self.FlowReferenceConversion(x['referenceToFlowDataSet'],
                                                                  self.NotConverted,
                                                                  self.FlowConversion(
                                                                      x, self.NotConverted)
                                                                  ).get_flow().set_field(x.get('referencesToDataSource'))
        }

        return _keys

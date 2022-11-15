#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  1 00:32:43 2022

@author: jotape42p
"""

from abc import ABC, abstractmethod
from pathlib import Path
from copy import copy
from collections import Counter

from .utils import (
    uuid_from_uuid,
    uuid_from_string,
    ensure_list,
    FieldMapping
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

import logging
import time
import re
import math
import pint
up = pint.UnitRegistry()
up.define('@alias hour = h')
up.define('item = [item] = _ = Item = Items')
up.define('EUR2005 = [currency] = EUR_default')
up.define('fraction = [] = frac')
for u in units_def.values():
    up.define(u)

__version__ = "Debug"


class ILCD1ToECS2UncertaintyConversion:

    @classmethod
    def normal_init(cls, x):
        self = cls()
        self._type = x['uncertaintyDistributionType']['#text'].replace(
            'log-normal', 'lognormal')

        # Get Comment
        self.comment = []
        for c in ensure_list(x.get('generalComment', {}), ensure_text=True):
            if 'Uncertainty Comment:\n' in c['#text']:
                c_ = c['#text'].split('Uncertainty Comment:\n')[-1]
                if 'Pedigree: (' in c_:
                    g = re.search(
                        r"(Pedigree: \(([0-9]{1},[0-9]{1},[0-9]{1},[0-9]{1},[0-9]{1})\))", c_).groups()
                    c_ = c_.replace(g[0], '')
                    self.pedigree = g[1]
                if 'Basic Variance: ' in c_:
                    g = re.search(r"(Basic Variance: ([0-9\.]+))", c_).groups()
                    c_ = c_.replace(g[0], '')
                    self.variance = g[1]
                self.comment.append(ILCD1Helper.text_add_index(
                    {'@lang': c['@lang'], '#text': c_}))
            else:
                self.comment.append(ILCD1Helper.text_add_index(c))

        # Get basic data
        self._get_data(x)
        return self

    def _get_data(self, x):
        if self._type in ('normal', 'lognormal'):
            var = float(x["relativeStandardDeviation95In"]['#text'])
            if hasattr(self, 'variance'):
                self.var = float(self.variance)
            else:
                logging.info("\t\tLognormal with no pedigree information")
            self.varpedigree = var
        elif self._type in ('triangular', 'uniform', 'undefined'):
            self.min = float(
                x.get('minimumValue', x.get('minimumAmount'))['#text'])
            self.max = float(
                x.get('maximumValue', x.get('maximumAmount'))['#text'])
            if self._type == 'undefined':
                self.std = float(x["relativeStandardDeviation95In"]['#text'])

    @classmethod
    def init_from_comment(cls, x):
        for c in ensure_list(x.get('generalComment', {}), ensure_text=True):
            if re.search('\nNot Converted: [A-z]+ distribution with parameters ', c['#text']):
                self = cls()
                c_ = re.search(
                    '\nNot Converted: [A-z]+ distribution with parameters (.*)').groups()[0]
                for n in c_.split(','):
                    setattr(self, 'a_'+n.split('=')
                            [0].strip().replace(' ', '_'), n.split('=')[1].strip())
                return self
        else:
            return None

    def calculate(self, m, f, field):
        if hasattr(self, 'comment') and self.comment:
            field.comment = self.comment
        if hasattr(self, 'pedigree'):
            p_index = ('a_reliability', 'a_completeness', 'a_temporalCorrelation',
                       'a_geographicalCorrelation', 'a_furtherTechnologyCorrelation')
            for i, factor in enumerate(self.pedigree.split(',')):
                setattr(field.pedigreeMatrix, p_index[i], factor)
        if self._type == 'lognormal':
            var = math.log(math.sqrt(self.varpedigree))**2
            # Sometimes the m is negative :/
            field.lognormal.a_mu = math.log(m) if m > 0 else 0
            field.lognormal.a_meanValue = m
            field.lognormal.a_variance = getattr(self, 'var', var)
            field.lognormal.a_varianceWithPedigreeUncertainty = var
        elif self._type == 'normal':
            var = (self.varpedigree * f / 2) ** 2
            field.normal.a_meanValue = m
            field.normal.a_variance = getattr(self, 'var', var)
            field.normal.a_varianceWithPedigreeUncertainty = var
        elif self._type == 'triangular':
            field.triangular.a_minValue = self.min * f
            field.triangular.a_mostLikelyValue = m
            field.triangular.a_maxValue = self.max * f
        elif self._type == 'uniform':
            field.uniform.a_minValue = self.min * f
            field.uniform.a_maxValue = self.max * f
        elif self._type == 'undefined':  # STD here is like an error propagation
            std = self.std * f
            field.undefined.a_standardDeviation95 = std
            field.undefined.a_minValue = (self.min + self.max) * f / 2 - std
            field.undefined.a_maxValue = (self.min + self.max) * f / 2 + std
        else:  # Beta, Gamma and Binomial
            if hasattr(self, 'a_n'):
                (setattr(field.binomial, p, float(getattr(self, p)))
                 for p in ('a_n', 'a_p'))
            elif hasattr(self, 'a_shape'):
                (setattr(field.gamma, p, float(getattr(self, p)))
                 for p in ('a_shape', 'a_scale', 'a_min'))
            elif hasattr(self, 'a_most_frequent'):
                (setattr(field.beta, p, float(getattr(self, p)))
                 for p in ('a_min', 'a_most_frequent', 'a_max'))


class Amount(ABC):

    uncertainty_conversion = None

    def __init__(self, amount, unit_text, uncertainty_struct):
        self._a = up.Quantity(amount, unit_text)
        self._f = 1
        if uncertainty_struct:
            if uncertainty_struct.get('uncertaintyDistributionType'):
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
    @property
    def f(self): return self._f
    @property
    def unc(self): return self._unc if hasattr(self, '_unc') else None
    @property
    def dimensionality(self): return self._a.dimensionality

    def to(self, unit):
        self._a = self._a.to(unit)
        return self

    @abstractmethod
    def calculate_unc(self):
        pass


class ILCD1ToECS2Amount(Amount):

    def calculate_unc(self, field):
        if hasattr(self, '_unc'):
            self._unc = self._unc.calculate(
                self._a.m, self._f, field.uncertainty)
            return self._unc
        return None

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
        
        self.amount = type(self).amountClass(float(x['meanValue']['#text']),
                                             'dimensionless',
                                             x)
        self.formula = x['formula']['#text'] if x.get('formula') else None

        self.comment = []
        for c in ensure_list(x.get('comment', {}), ensure_text=True):
            if re.search(r'\[(.*)\]', c['#text']):  # [!] Search for the unit id
                self.unit = re.search(r'\[(.*)\]', c['#text']).groups()[0]
                c['#text'] = re.sub(r'\[(.*)\]', '', c['#text'])
                self.comment.append(ILCD1Helper.text_add_index(c))
            else:
                self.comment.append(ILCD1Helper.text_add_index(c))

        # [!] Maybe consider the comment going to the flow [add unit name and id]
        type(self)._available_variables[self.o_name] = {
            'used?': False, 'self': self}

    @classmethod
    def create_parameters(cls):  # It doesn't really have a unit name actualy
        vs = {k: v['self']
              for k, v in cls._available_variables.items() if not v['used?']}
        for k, var in vs.items():
            par = cls.parameter_holder.get_class('parameter')()
            par.name = ILCD1Helper.text_dict_from_text(0, k)
            var.amount.calculate_unc(par)
            par.a_parameterId = uuid_from_string(k)
            par.a_variableName = var.name
            if var.formula:
                for n in cls._non_conform_variables: # __ha_to_m2__ is not valid as it has to start with a letter
                    if n in var.formula:
                        var.formula = var.formula.replace(n, cls._non_conform_variables[n])
                par.a_mathematicalRelation = var.formula
                par.a_isCalculatedAmount = True
            par.a_amount = var.amount.m
            if hasattr(var, 'unit'):
                par.unitName = ILCD1Helper.text_dict_from_text(0, var.unit)
            if var.comment:
                par.comment = var.comment

            setattr(cls.parameter_holder, 'parameter', par)
            
            master = cls.master_field.get_class('parameter')()
            master.name = ILCD1Helper.text_dict_from_text(0, k)
            master.a_id = uuid_from_string(k)
            master.a_defaultVariableName = var.name
            setattr(cls.master_field, 'parameter', master)

    @classmethod
    def get_variable(cls, name):
        cls._available_variables[name]['used?'] = True
        self = cls._available_variables[name]['self']
        if self.formula:
            for n in cls._non_conform_variables: # __ha_to_m2__ is not valid as it has to start with a letter
                if n in self.formula:
                    self.formula = self.formula.replace(n, cls._non_conform_variables[n])
        cls._available_variables[name]['self'] = self
        return cls._available_variables[name]['self']


class ILCD1ToECS2FlowConversion:  # Originally, the production volume is not conversible

    uuid_specs = None
    compartment_mapping = None

    amountClass = None
    source_ref_conversion = None
    variable_conversion = None

    flow_holder = None

    _reference_flows = []
    _flow_internal_refs = None
    _all_flows = set()
    _all_flow_ids = set() # Used to avoid duplicates on the field 'id'

    def __init__(self, x, not_converted):
        self.not_converted = not_converted

        # Dimensionless for the time, it will have an unit in the references
        self.id_ = x['referenceToFlowDataSet']['@refObjectId']
        self.amount = type(self).amountClass(float(x.get('resultingAmount', x.get('meanAmount'))['#text']),
                                             'dimensionless', x)

        self.comment = []
        for n in ensure_list(x.get('generalComment', {}), ensure_text=True):
            self.comment.append(ILCD1Helper.text_add_index(n))

        if x.get('referenceToVariable'):
            self.variable = type(self).variable_conversion.get_variable(
                x['referenceToVariable']['#text'])
        self.group = x['exchangeDirection']['#text']
        self.isReference = True if x['@dataSetInternalID'] in type(
            self)._reference_flows else False

        self.properties = {}
        self.main_prop = None
        if x.get('allocations'):
            self.alloc_properties = {}
            for alloc in x['allocations'].get('allocation', []):
                self.alloc_properties['allocation for '+type(self)._flow_internal_refs(
                    alloc['@internalReferenceToCoProduct'])] = float(alloc['@allocatedFraction'])
    
    class Property:

        amountClass = None

        property_holder = None
        
        master_field = None

        _energy = []

        @classmethod
        def normal_init(cls, x, not_converted):
            self = cls()
            self.not_converted = not_converted
            self.fp = fp = ilcd_to_ecs2_fp.get(
                x["referenceToFlowPropertyDataSet"]["@refObjectId"], None)
            self.isConvertible = True if fp else False

            if fp:
                self.amount = type(self).amountClass(float(x['meanValue']['#text']),
                                                     fp[1], x)
                self.field = cls.property_holder.get_class('property')()
                self.field.unitName = ILCD1Helper.text_dict_from_text(0, fp[1])
                self.field.a_unitId = fp[0]

                if fp[1] == 'heating value, gross':
                    cls._energy.append('GROSS')
                elif fp[1] == 'heating value, net':
                    cls._energy.append('NET')

                self.amount.calculate_unc(self.field)
                for n in ensure_list(x.get('generalComment', {}), ensure_text=True):
                    self.field.comment = ILCD1Helper.text_add_index(n)
            else:
                logging.warning(
                    f"Flow property {x['referenceToFlowPropertyDataSet']['shortDescription']['#text']} not a valid EcoSpold2 flow property")

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
            self.field.a_unitId = '577e242a-461f-44a7-922c-d8e1c3d2bf45'

            self.field.a_propertyId = uuid_from_string(name)
            self.field.name = ILCD1Helper.text_dict_from_text(1, name)

            self.field.a_amount = self.amount.m

            prop = flow_master.get_class('property')()
            prop.a_amount = self.amount.m
            prop.a_propertyId = uuid_from_string(name)
            prop.name = name
            prop.unitName = 'dimensionless'
            prop.a_unitId = '577e242a-461f-44a7-922c-d8e1c3d2bf45'
            setattr(flow_master, 'property', prop)
            
            prop = type(self).master_field.get_class('property')()
            prop.name = name
            prop.a_id = uuid_from_string(name)
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
            self.field.a_unitId = '487df68b-4994-4027-8fdc-a4dc298257b7'

            self.field.a_propertyId = id_
            self.field.name = ILCD1Helper.text_dict_from_text(1, name)

            self.amount.calculate_unc(self.field)

            return self

        @classmethod
        def get_dry_and_wet_mass(cls, props, flow):
            if 'water content' in props:
                if str(flow.amount.u) == 'm**3':
                    logging.warning(
                        '\tProperties Wet mass and dry mass not converted due to a need for density values in m3/kg')
                else:
                    props['wet mass'] = cls.mass_prop_init(
                        1, 'wet mass', '67f102e2-9cb6-4d20-aa16-bf74d8a03326')
                    props['dry mass'] = cls.mass_prop_init(
                        1-props['water content'].amount.m, 'dry mass', '3a0af1d6-04c3-41c6-a3da-92c4f61e0eaa')
                    props['water in wet mass'] = cls.mass_prop_init(
                        props['water content'].amount.m, 'water in wet mass', '6d9e1462-80e3-4f10-b3f4-71febd6f1168')

            for k, prop in props.items():
                if ' content' in k:
                    if 'dry mass' in props:
                        if props['dry mass'].amount.m != 0:
                            prop.amount.divide(props['dry mass'].amount.a)
                        else:
                            prop.amount._a = up.Quantity(0, 'kg')
                    else:  # unit correction only
                        prop.amount.divide(up.Quantity(1, 'kg'))

                    if not prop.field.get('a_propertyId'):
                        mass, volume = prop.fp[4]
                        if str(flow.amount.u) == 'kg' and mass:
                            prop.field.a_propertyId = mass[0]
                            prop.field.name = ILCD1Helper.text_dict_from_text(
                                1, mass[1])
                        elif str(flow.amount.u) == 'm**3' and volume:
                            prop.field.a_propertyId = volume[0]
                            prop.field.name = ILCD1Helper.text_dict_from_text(
                                1, volume[1])
                        else:
                            prop.field.a_propertyId = prop.fp[2]
                            prop.field.name = ILCD1Helper.text_dict_from_text(
                                1, prop.fp[3])
                else:
                    if not prop.field.get('a_propertyId'):
                        prop.field.a_propertyId = prop.fp[2]
                        prop.field.name = ILCD1Helper.text_dict_from_text(
                            1, prop.fp[3])

                prop.field.a_amount = prop.amount.m

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

    def get_elementary_flow_info(self, n, file):
        self.field.a_elementaryExchangeId = n["TargetFlowUUID"]
        self.field.name = ILCD1Helper.text_dict_from_text(
            0, n["TargetFlowName"])

        self.master = type(self).master_field.get_class('elementaryExchange')()
        
        self.master.a_id = n["TargetFlowUUID"]
        self.mtype = 'elementaryExchange'
        c = type(self).compartment_mapping.get(n["TargetFlowContext"], None)
        if c:
            # TODO take out the subcompartmentId key from json
            self.field.compartment.a_subcompartmentId = c['subcompartmentId']
            self.field.compartment.compartment = ILCD1Helper.text_dict_from_text(
                0, n['TargetFlowContext'].split('/')[0])
            self.field.compartment.subcompartment = ILCD1Helper.text_dict_from_text(
                0, n['TargetFlowContext'].split('/')[1])
            
            comp = self.master.get_class('compartment')()
            comp.a_subcompartmentId = c['subcompartmentId']
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
                self.field.a_unitId = v[0]
                break
        else:
            raise ValueError(f"Unit {n['TargetUnit']} not found")
            
        self.master.name = ILCD1Helper.text_dict_from_text(
            0, n["TargetFlowName"])
        self.master.unitName = ILCD1Helper.text_dict_from_text(
            0, n['TargetUnit'])
        self.master.a_unitId = v[0]

        self.get_properties(file)

    def get_intermediate_flow_info(self, file):
        self.field.a_intermediateExchangeId = uuid_from_uuid(
            *(self.id_,), *type(self).uuid_specs)
        self.field.name = ILCD1Helper.text_dict_from_text(1, self.info['name'])

        self.get_properties(file)

        self.amount.multiply(up.Quantity(1, self.main[1].replace(' ', '_')))
        self.amount.calculate_unc(self.field)
        self.field.unitName = ILCD1Helper.text_dict_from_text(0, self.main[1])
        self.field.a_unitId = self.main[0]
        
        self.master = type(self).master_field.get_class('intermediateExchange')()

        self.master.a_id = uuid_from_uuid(*(self.id_,), *type(self).uuid_specs)
        self.mtype = 'intermediateExchange'
        self.master.name = ILCD1Helper.text_dict_from_text(1, self.info['name'])
        self.master.unitName = ILCD1Helper.text_dict_from_text(0, self.main[1])
        self.master.a_unitId = self.main[0]
        

    def finish_flow_info(self):
        id_ = uuid_from_string(
            type(self).uuid_process + self.info['name'])
        if id_ in type(self)._all_flow_ids:
            i = 0
            while id_ in type(self)._all_flow_ids:
                i += 1
                id_ = uuid_from_string(type(self).uuid_process + self.info['name'] + str(i)) # TODO See in the ILCD conv too
            self.field.a_id = id_
        else:
            self.field.a_id = id_
        type(self)._all_flow_ids.add(id_)
            
        self.field.comment = self.comment
        self.field.a_amount = self.amount.m

        if self.isReference:
            self.field.outputGroup = 0
        else:
            if self.group == 'Input':
                self.field.inputGroup = {
                    'Elementary flow': 4,
                    'Product flow': 5,
                    'Waste flow': 5,
                    }.get(self.info['type'])
            else:
                self.field.outputGroup = {
                    'Elementary flow': 4,
                    'Product flow': 2,
                    'Waste flow': 3
                    }.get(self.info['type'])

        if hasattr(self, 'variable'):
            self.field.a_variableName = self.variable.name
            self.master.a_defaultVariableName = self.variable.name
            if self.variable.formula:
                self.field.a_mathematicalRelation = self.variable.formula
                self.field.a_isCalculatedAmount = True

        if hasattr(self, 'properties'):
            self.properties = {k: v for k,
                               v in self.properties.items() if v.isConvertible}
            self.properties = self.Property.get_dry_and_wet_mass(
                self.properties, self)
            if hasattr(self, 'alloc_properties'):
                self.properties.extend([self.Property.allocation_init(
                    k, v, self.master) for k, v in self.alloc_properties.items()])
            for p in self.properties:
                self.field.property = p.field
                
        setattr(type(self).master_field, self.mtype, self.master)
    
    def set_field(self, ref):
        if self.isConvertible:
            if ref is not None:
                for x in ensure_list(ref.get('referenceToDataSource', {})):
                    type(self).source_ref_conversion(x, self.not_converted,
                                                     {'regular': self.field},
                                                     {'id': 'a_sourceId',
                                                         'first_author': 'a_sourceFirstAuthor',
                                                         'year': 'a_sourceYear',
                                                         'page': 'a_pageNumbers'}).get_source()  # [!] Make take the get_source and get_contact out
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
        self.id_ = x['@refObjectId']
        self.shortDescription = x['shortDescription']
        self.get_not_converted(x)

    def get_not_converted(self, x):
        pass

    @classmethod
    def get_file(cls, x, type_):
        path = Path(cls._ilcd_root_path, type_)
        if path.is_dir():
            options = (x.get('@uri', '').split('/')[-1],
                       x.get('@refObjectId', '')+'_' +
                       x.get('@version', '')+'.xml',
                       x.get('@refObjectId', '')+'.xml')
            for file in path.glob('*xml'):
                for option in options:
                    if file.name == option:
                        return file
            else:
                logging.warning(
                    f"\tfile of type '{type_}' and id '{x['@refObjectId']}' not found")
                return None
        else:
            logging.warning(f"\tfolder of type '{type_}' not found")
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
            self.subtype = 'a_datasetIcon'
        elif uri_source:
            # For cases like the technology pictogramme where the source is really an imageUrl
            self.subtype = 'imageUrl'
        else:
            self.subtype = 'regular'
        self.field = field[self.subtype]

    def get_master_source(self, id_, fa, yr, title, type_='0'):
        if id_ not in type(self)._all_sources:
            src = type(self).master_field.get_class('source')()
            src.a_id = id_
            src.a_sourceType = type_
            src.a_firstAuthor = fa
            src.a_year = yr
            src.a_title = title
            setattr(type(self).master_field, 'source', src)
            type(self)._all_sources.add(id_)

    def get_source(self):  # Remember TTextAndImage are Unique :3
        if self.isConvertible:
            with open(self.file) as f:
                if self.subtype in ('imageUrl', 'a_datasetIcon'):
                    map_ = {'/sourceDataSet/sourceInformation/dataSetInformation/referenceToDigitalFile/@uri':
                            lambda x: ILCD1Helper.text_add_index({'@lang': 'en', '#text': x}) if self.subtype == 'imageUrl' else x}
                    for k, t in XMLStreamIterable(f, map_):
                        setattr(self.field, self.subtype, map_[k](t))
                else:
                    map_ = {'/sourceDataSet/sourceInformation/dataSetInformation/sourceCitation': lambda x, t: x.__setitem__('citation', t['#text']),
                            '/sourceDataSet/sourceInformation/dataSetInformation/shortName': lambda x, t: x.__setitem__('name', t['#text'])
                            }  # [!] classification, timestamp, dataSetVersion and permanentDataSetURI for not_converted
                    info = {}
                    for path, t in XMLStreamIterable(f, map_):
                        map_[path](info, t)

                    id_ = uuid_from_uuid(self.id_, b'_Lavosier_ECS2_/', "to_ECS2")
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
                            f"Year could not be converted for source {info['name']} with id {self.id_}")
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
    
    def get_master_contact(self, id_, name, email=None):
        if id_ not in type(self)._all_contacts:
            if self.attrname['name'] == 'a_companyCode':
                src = type(self).master_field.get_class('company')()
                src.a_code = name
                n = 'company'
            else:
                src = type(self).master_field.get_class('person')()
                n = 'person'
                if email is not None:
                    src.a_email = email
                    src.a_name = name
            src.a_id = id_
            setattr(type(self).master_field, n, src)
            type(self)._all_contacts.add(id_)

    def get_contact(self):
        if self.isConvertible:
            with open(self.file) as f:
                map_ = {'/contactDataSet/contactInformation/dataSetInformation/name': lambda x, t: x.__setitem__('name', t['#text']),
                        '/contactDataSet/contactInformation/dataSetInformation/shortName': lambda x, t: x.__setitem__('sname', t['#text']),
                        '/contactDataSet/contactInformation/dataSetInformation/email': lambda x, t: x.__setitem__('email', t['#text'])}
                info = {}
                for path, t in XMLStreamIterable(f, map_):
                    map_[path](info, t)

                id_ = uuid_from_uuid(self.id_, b'_Lavosier_ECS2_/', "to_ECS2")
                setattr(self.field, self.attrname['id'], id_)
                setattr(self.field, self.attrname['name'], info.get(
                    'name', info.get('shortName')))
                if self.attrname.get('email'):
                    setattr(self.field, self.attrname['email'], info['email'])
                    
                self.get_master_contact(id_, info['name'], info.get('email'))


class ILCD1ToECS2FlowReferenceConversion(ILCD1ToECS2ReferenceConversion):

    type_ = 'flows'

    def __init__(self, x, not_converted, flow):
        super().__init__(x, not_converted)
        self.flow = flow

    def get_flow(self):
        if self.isConvertible:
            with open(self.file) as f:

                classifications = []

                map_ = {'/flowDataSet/modellingAndValidation/LCIMethod/typeOfDataSet':
                        lambda x, t: x.__setitem__('type', t['#text']),
                        '/flowDataSet/flowInformation/dataSetInformation/name/baseName':
                            lambda x, t: x.__setitem__('name', t['#text']),
                        '/flowDataSet/flowInformation/dataSetInformation/CASNumber':
                            lambda x, t: x.__setitem__('CAS', t['#text']),
                        '/flowDataSet/flowInformation/dataSetInformation/sumFormula':
                            lambda x, t: x.__setitem__('formula', t['#text']),
                        '/flowDataSet/flowInformation/dataSetInformation/synonyms':
                            lambda x, t: x.__setitem__(
                                'synonym', x.get('synonym', []) + [t]),
                        '/flowDataSet/flowInformation/quantitativeReference/referenceToReferenceFlowProperty':
                            lambda x, t: x.__setitem__(
                                'reference', t['#text']),
                        '/flowDataSet/flowInformation/dataSetInformation/classificationInformation/classification':
                            lambda x, t: classifications.append(
                                type(self).class_conversion(t, self.not_converted).field),
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
                                "Flow not converted due to lack of elementary flow correspondence in the mapping file")
                    else:
                        self.flow.isConvertible = False
                        logging.warning(
                            "Flow not converted as the flow is not present on the elementary flow mapping file")
                else:
                    self.flow.field = type(self.flow).flow_holder.get_class(
                        'intermediateExchange')()
                    self.flow.info = info
                    self.flow.get_intermediate_flow_info(self.file)

                if self.flow.isConvertible:
                    self.flow.finish_flow_info()
                    if classifications:
                        setattr(self.flow.field, 'classification', type(
                            self).class_conversion.organize(classifications, 'CPC'))
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
        # Set instances
        self.field = self.class_holder.get_class('classification')()
        self.not_converted = not_converted
        self.master = type(self).master_field.get_class('classificationSystem')()
        self.clv = self.master.get_class('classificationValue')()

        # Used variables
        self.name = "ILCD" if not x.get("@name") else x["@name"]
        if self.name in type(self)._defaults.keys():
            if self.name != 'EcoSpold01Categories':
                self.value = ensure_list(x['class'])[-1]["#text"]
            else:
                self.value = '/'.join([x['#text']
                                      for x in ensure_list(x['class'])])
        else:
            self.value = '/'.join([x['#text']
                                  for x in ensure_list(x['class'])])

        # Get basic fields
        self.field.classificationSystem = {
            '@index': 0, '@lang': 'en', '#text': self.name}
        self.master.a_id = uuid_from_string(self.name)
        self.master.a_type = 3 # TODO
        self.master.name = {'@index': 0, '@lang': 'en', '#text': self.name}
        self.field.classificationValue = {
            '@index': 0, '@lang': 'en', '#text': self.value}
        self.clv.name = {'@index': 0, '@lang': 'en', '#text': self.value}
    
        # Get class fields
        self.get_classification()
        setattr(self.master, 'classificationValue', self.clv)
        setattr(type(self).master_field, 'classificationSystem', self.master)
        
        # Get not converted
        self.get_not_converted(x)

    def get_not_converted(self, x):
        pass

    def get_classification(self):
        n = type(self).class_mapping.get(self.name+'/'+self.value)
        if n is None:
            id_ = uuid_from_string(self.value)
        else:
            id_ = n['classificationValueId']
        self.field.a_classificationId = id_
        self.clv.a_id = id_

    @classmethod
    def organize(cls, classifications, priority):
        for i, c in enumerate(classifications):  # CPC and ISIC have priority
            if c.get('classificationSystem') == priority:
                return [classifications.pop(i)] + classifications
        else:
            return classifications


class ILCD1ToECS2ReviewConversion:

    _set_TextAndImage = None

    contact_ref_conversion = None

    review_holder = None

    _version = [1, 0, 1, 0]

    def __init__(self, x, not_converted):
        self.not_converted = not_converted
        self.field = type(self).review_holder.get_class('review')()

        for review in ensure_list(x.get('reviewDetails', {}), ensure_text=True):
            self.review_comment(review)
            self.field.details = type(self)._set_TextAndImage(
                ILCD1Helper.text_add_index(review))

        for review in ensure_list(x.get('otherReviewDetails', {}), ensure_text=True):
            self.field.otherDetails = ILCD1Helper.text_add_index(review)

        type(self).contact_ref_conversion(x['referenceToNameOfReviewerAndInstitution'],
                                          not_converted,
                                          self.field,
                                          {'id': 'a_reviewerId', 'name': 'a_reviewerName', 'email': 'a_reviewerEmail'}).get_contact()

        # TODO This is just a cameo
        self.field.a_reviewDate = '1900-01-01'

        # TODO The review version has to be revisited as it is too irregular
        if not self.field.get('a_reviwedMajorRelease'):
            v = type(self)._version
            self.field.a_reviewedMajorRelease, self.field.a_reviewedMinorRelease = v[0], v[1]
            self.field.a_reviewedMajorRevision, self.field.a_reviewedMinorRevision = v[
                2], v[3]
            type(self)._version[2] += 1

        self.get_not_converted(x)

    def review_comment(self, x):
        if re.search(r'Review Version: [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\n', x['#text']):
            v = re.search(
                r'Review Version: ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\n', x['#text']).groups()[0].split('.')
            self.field.a_reviewedMajorRelease, self.field.a_reviewedMinorRelease = v[0], v[1]
            self.field.a_reviewedMajorRevision, self.field.a_reviewedMinorRevision = v[
                2], v[3]
        if re.search(r'Date of Review: [A-z ]+\n', x['#text']):
            date = re.search(
                r'Date of Review: ([A-z ]+)\n', x['#text']).groups()[0]
            self.field.a_reviewDate = date

    def get_not_converted(self, x):
        # scope with methods and scores
        # quality indicators
        # report from referenceToCompleteReviewReport
        # @type of review
        pass

# Field mapping for conversion


class ILCD1ToECS2BasicFieldMapping(FieldMapping, ABC):

    # Conversion Defaults
    _uuid_conv_spec = (b'_Lavosier_ECS2_/', 'to_ECS2')
    _default_language = 'en'
    _default_compartment_mapping = FieldMapping._dict_from_file(
        Path("Mappings/ilcd1_to_ecs2_compartments.json"))
    _default_geographies_mapping = FieldMapping._dict_from_file(
        Path("Mappings/ilcd1_to_ecs2_geographies.json"))

    # Converter/Factory Defaults
    _default_files = None
    _default_elem_mapping = None
    _default_class_mapping = Path("Mappings/ilcd1_to_ecs2_classes.json")

    # Configuration Defaults
    _convert_additional_fields = True

    def set_mappings(self, ef_map, cl_map):
        self._elem_mapping = self._dict_from_file(
            ef_map or type(self)._default_elem_mapping, 'SosurceFlowUUID')
        self._class_mapping = self._dict_from_file(
            cl_map or type(self)._default_class_mapping, 'SourceFlowUUID')
        # Attributions
        self.ReferenceConversion.elem_flow_mapping = self._elem_mapping
        self.ClassificationConversion.class_mapping = self._class_mapping
        self.FlowConversion.compartment_mapping = type(
            self)._default_compartment_mapping

    def __init__(self,
                 Amount,
                 UncertaintyConversion,
                 SourceReferenceConversion,
                 ContactReferenceConversion,
                 FlowReferenceConversion,
                 ReferenceConversion,
                 FlowConversion,
                 VariableConversion,
                 ClassificationConversion,
                 ReviewConversion,
                 NotConverted):

        self.Amount = Amount
        self.UncertaintyConversion = UncertaintyConversion
        self.SourceReferenceConversion = SourceReferenceConversion
        self.ContactReferenceConversion = ContactReferenceConversion
        self.FlowReferenceConversion = FlowReferenceConversion
        self.ReferenceConversion = ReferenceConversion
        self.FlowConversion = FlowConversion
        self.VariableConversion = VariableConversion
        self.ClassificationConversion = ClassificationConversion
        self.ReviewConversion = ReviewConversion
        self.NotConverted = NotConverted()

    def start_conversion(self):
        ILCD1Helper.default_language = type(self)._default_language
        self.ReferenceConversion.uuid_specs = type(self)._uuid_conv_spec
        self.FlowConversion.uuid_specs = type(self)._uuid_conv_spec

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
        self.FlowConversion._all_flows = set()
        self.FlowConversion._all_flow_ids = set()
        self.FlowConversion.Property._energy = []
        self.ReferenceConversion._ilcd_root_path = None
        self.SourceReferenceConversion._all_sources = set()
        self.ContactReferenceConversion._all_contacts = set()
        self.ReviewConversion.version = [1, 0, 1, 0]

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
        self.ReviewConversion._set_TextAndImage = self.set_TextAndImage
        super().set_file_info(*args)

    def default(self, cl_struct):
        setattr(cl_struct.activityDescription.macroEconomicScenario,
                'a_macroEconomicScenarioId', 'd9f57f0a-a01f-42eb-a57b-8f18d6635801')
        setattr(cl_struct.activityDescription.macroEconomicScenario,
                'name', ILCD1Helper.text_dict_from_text(1, 'Business-as-Usual'))
        setattr(cl_struct.activityDescription.activity,
                'a_inheritanceDepth', 0)
        setattr(cl_struct.activityDescription.timePeriod,
                'a_isDataValidForEntirePeriod', 0)
        setattr(cl_struct.activityDescription.activity,
                'a_specialActivityType', 0)
        setattr(cl_struct.activityDescription.technology,
                'a_technologyLevel', 3)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'a_defaultLanguage', 'en')  # TODO Can be better
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'a_fileGenerator', f"Lavoisier version {__version__}")
        t = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'a_lastEditTimestamp', t)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'a_fileTimestamp', t)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'a_creationTimestamp', t)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'a_internalSchemaVersion', '2.0.10')
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'a_majorRelease', 1)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'a_minorRelease', 0)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'a_majorRevision', 0)
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'a_minorRevision', 0)

        setattr(cl_struct.administrativeInformation.fileAttributes,
                'a_contextId', "de659012-50c4-4e96-b54a-fc781bf987ab")
        setattr(cl_struct.administrativeInformation.fileAttributes,
                'contextName', ILCD1Helper.text_dict_from_text(1, 'ecoinvent'))

    # Setting variables that help conversions that depend on more than one field
    def start_conversion(self):
        self._main_classifications = []
        self._LCI_MA = []
        self._original_model = None
        self._access_restricted_to = None
        super().start_conversion()

    def reset_conversion(self, end=False):
        setattr(self._class_holder, 'classification',
                self.ClassificationConversion.organize(self._main_classifications,
                                                       'ISIC rev.4 ecoinvent'))
        self._main_classifications = []

        # [!] This is too random, maybe think about a better way
        if self._original_model is not None:
            setattr(self._lci_ma_holder, 'a_systemModelId',
                    system_model_1_.get(self._original_model))
            setattr(self._lci_ma_holder, 'systemModelName',
                    ILCD1Helper.text_dict_from_text(1, self._original_model))
            setattr(self._master_system_model_holder.activityIndexEntry, 'a_systemModelId',
                    system_model_1_.get(self._original_model))
        elif self._LCI_MA:
            c = Counter([x for x in self._LCI_MA]).most_common(1)[0][0]
            setattr(self._lci_ma_holder, 'a_systemModelId', c[1])
            setattr(self._lci_ma_holder, 'systemModelName',
                    ILCD1Helper.text_dict_from_text(1, c[0]))
            setattr(self._master_system_model_holder.activityIndexEntry, 'a_systemModelId',
                    c[1])
        else:
            setattr(self._lci_ma_holder, 'a_systemModelId',
                    "8b738ea0-f89e-4627-8679-433616064e82")
            setattr(self._lci_ma_holder, 'systemModelName',
                    ILCD1Helper.text_dict_from_text(1, 'Undefined'))
            setattr(self._master_system_model_holder.activityIndexEntry, 'a_systemModelId',
                           "8b738ea0-f89e-4627-8679-433616064e82")
        self._original_model = None
        self._LCI_MA = []

        if not self._energy_holder.get('a_energyValues'):
            energy = self.FlowConversion.Property._energy
            n = sum(1 if x == "NET" else 0 for x in energy)
            g = sum(1 if x == "GROSS" else 0 for x in energy)
            if n >= 3*g:
                setattr(self._energy_holder, "a_energyValues", '1')
            elif g >= 3*n:
                setattr(self._energy_holder, "a_energyValues", '2')
            else:
                setattr(self._energy_holder, "a_energyValues", '0')

        if self._access_restricted_to:
            setattr(self._access_restriction_holder, 'a_accessRestrictedTo',
                    self._access_restricted_to)
        self._access_restricted_to = None

        self.VariableConversion.create_parameters()
        
        setattr(self._master_system_model_holder, 'activityName', self._master_activity_name_holder) # TODO

        if not end:
            super().reset_conversion()

    def end_conversion(self):
        self.reset_conversion(end=True)
        super().end_conversion()

    def set_TextAndImage(self, x):
        tai = self._tai()
        setattr(tai, 'text', ILCD1Helper.text_add_index(x))
        return tai

    def general_comment(self, cl_struct, x):
        x['#text'] = ECS2Helper._get_uuid(cl_struct.activityDescription.activity,
                                          'a_activityNameId',
                                          r'Activity Linkable Id:',
                                          x['#text'],
                                          extra=lambda x: (setattr(cl_struct.userMaster.activityIndexEntry,
                                                                  'a_activityNameId',
                                                                  x),
                                                           setattr(self._master_activity_name_holder,
                                                                   'a_id', x))
                                          )
        x['#text'] = ECS2Helper._get_str(cl_struct.activityDescription.activity,
                                         'a_specialActivityType',
                                         special_activity_,
                                         r'Activity Subtype:',
                                         x['#text'],
                                         extra=lambda x: setattr(cl_struct.userMaster.activityIndexEntry,
                                                                 'a_specialActivityType',
                                                                 x))
        x['#text'] = ECS2Helper._get_str(cl_struct.activityDescription.activity,
                                         'a_inheritanceDepth',
                                         child_type_,
                                         r'Inheritance:',
                                         x['#text'])
        x['#text'] = ECS2Helper._get_uuid(cl_struct.activityDescription.activity,
                                          'a_parentActivityId',
                                          r'Parent Id:',
                                          x['#text'],
                                          extra=lambda x: (setattr(cl_struct,
                                                                   'main_activity_type',
                                                                   'childActivityDataset'),
                                                           setattr(cl_struct.activityDescription.activity,
                                                                   'a_inheritanceDepth',
                                                                   '-1')))
        x['#text'] = ECS2Helper._get_list_str(cl_struct.activityDescription.activity,
                                              'tag',
                                              r'Tag:',
                                              x['#text'])
        return self.set_TextAndImage(x)

    def time_comment(self, cl_struct, x):
        x['#text'] = ECS2Helper._get_str(cl_struct.activityDescription.timePeriod,
                                         'a_isDataValidForEntirePeriod',
                                         time_period_,
                                         r'Validity:',
                                         x['#text'])
        return self.set_TextAndImage(x)

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
                                         'a_technologyLevel',
                                         tech_,
                                         r'Technology Level:',
                                         x['#text'])
        return self.set_TextAndImage(x)

    def modelling_constants(self, cl_struct, x):
        x['#text'] = ECS2Helper._get_str(cl_struct.activityDescription.activity,
                                         'a_energyValues',
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

    def mapping(self):
        _keys = {
            '/processDataSet/processInformation/dataSetInformation/UUID':
                lambda cl_struct, x: (setattr(cl_struct.activityDescription.activity, 'a_id', uuid_from_uuid(*(x['#text'],), *self._uuid_conv_spec)),
                                      setattr(self.FlowConversion, 'uuid_process', x['#text']),
                                      setattr(cl_struct.userMaster.activityIndexEntry, 'a_id', uuid_from_uuid(*(x['#text'],), *self._uuid_conv_spec))),
            # [!] activityNameId is created here since it is mandatory
            '/processDataSet/processInformation/dataSetInformation/name/baseName':
                lambda cl_struct, x: (setattr(cl_struct.activityDescription.activity, 'activityName', ILCD1Helper.text_add_index(x, index=1)),
                                      setattr(cl_struct.activityDescription.activity, 'a_activityNameId', uuid_from_string(x['#text'])),
                                      setattr(cl_struct.userMaster.activityIndexEntry, 'a_activityNameId', uuid_from_string(x['#text'])),
                                      setattr(self._master_activity_name_holder, 'a_id', uuid_from_string(x['#text'])),
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
                                      setattr(cl_struct.activityDescription.activity, 'generalComment',
                                              self.set_TextAndImage(ILCD1Helper.text_dict_from_text(1, 'Identifier name: '+x)))),
            '/processDataSet/processInformation/dataSetInformation/synonyms':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.activity, 'synonym', [ILCD1Helper.text_add_index({'@lang': 'en',
                                                                                                                            '#text': n}) for n in x['#text'].split('; ')]),
            '/processDataSet/processInformation/dataSetInformation/complementingProcesses':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'complementingProcesses', x),
            '/processDataSet/processInformation/dataSetInformation/classificationInformation/classification':
                lambda cl_struct, x: self._main_classifications.append(
                    self.ClassificationConversion(x, self.NotConverted).field),
            '/processDataSet/processInformation/dataSetInformation/generalComment':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.activity, 'generalComment',
                                             self.general_comment(cl_struct, ILCD1Helper.text_add_index(x))),
            '/processDataSet/processInformation/dataSetInformation/referenceToExternalDocumentation':
                lambda cl_struct, x: self.SourceReferenceConversion(x, self.NotConverted,
                                                                    {'imageUrl': cl_struct.activityDescription.activity.generalComment,
                                                                     'a_datasetIcon': cl_struct.activityDescription.activity},
                                                                    {}).get_source(),
            '/processDataSet/processInformation/quantitativeReference/referenceToReferenceFlow':
                lambda cl_struct, x: self.FlowConversion._reference_flows.append(
                    x),
            '/processDataSet/processInformation/quantitativeReference/functionalUnitOrOther':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'functionalUnitOrOther', x),
            '/processDataSet/processInformation/quantitativeReference/a_type':
                lambda cl_struct, x: setattr(self.NotConverted, 'a_type', x),
            '/processDataSet/processInformation/time/referenceYear':
                lambda cl_struct, x: (setattr(
                    cl_struct.activityDescription.timePeriod, 'a_startDate', x['#text']+'-01-01'),
                    setattr(cl_struct.userMaster.activityIndexEntry, 'a_startDate', x['#text']+'-01-01')),
            '/processDataSet/processInformation/time/dataSetValidUntil':
                lambda cl_struct, x: (setattr(
                    cl_struct.activityDescription.timePeriod, 'a_endDate', x['#text']+'-12-31'),
                    setattr(cl_struct.userMaster.activityIndexEntry, 'a_endDate', x['#text']+'-12-31')),
            '/processDataSet/processInformation/time/timeRepresentativenessDescription':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.timePeriod, 'comment',
                                             self.time_comment(cl_struct, ILCD1Helper.text_add_index(x))),
            '/processDataSet/processInformation/geography/locationOfOperationSupplyOrProduction/descriptionOfRestrictions':
                lambda cl_struct, x: setattr(
                    cl_struct.activityDescription.geography, 'comment',  self.set_TextAndImage(x)),
            '/processDataSet/processInformation/geography/locationOfOperationSupplyOrProduction/@location':
                lambda cl_struct, x: (setattr(cl_struct.activityDescription.geography, 'shortname', ILCD1Helper.text_dict_from_text(1, x)),
                                      setattr(cl_struct.activityDescription.geography, 'a_geographyId',
                                              type(self)._default_geographies_mapping.get(x)),
                                      setattr(cl_struct.userMaster.activityIndexEntry,
                                              'a_geographyId', type(self)._default_geographies_mapping.get(x))),
            '/processDataSet/processInformation/geography/locationOfOperationSupplyOrProduction/@latituteAndLongitude':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'a_latitudeAndLongitude', x),
            '/processDataSet/processInformation/geography/subLocationOfOperationSupplyOrProduction':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'subLocationOfOperationSupplyOrProduction', x),
            '/processDataSet/processInformation/technology/technologyDescriptionAndIncludedProcesses':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.technology, 'comment',
                                             self.tech_comment(cl_struct, ILCD1Helper.text_add_index(x))),
            '/processDataSet/processInformation/technology/referenceToIncludedProcesses':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToIncludedProcesses', x),
            '/processDataSet/processInformation/technology/technologyApplicability':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.technology,
                                             'comment', self.set_TextAndImage(ILCD1Helper.text_add_index(x))),
            '/processDataSet/processInformation/technology/referenceToTechnologyPictogramme':
                lambda cl_struct, x: self.SourceReferenceConversion(x, self.NotConverted,
                                                                    {'imageUrl': cl_struct.activityDescription.technology.comment},
                                                                    {}, uri_source=True).get_source(),
            '/processDataSet/processInformation/technology/referenceToTechnologyFlowDiagrammOrPicture':
                lambda cl_struct, x: self.SourceReferenceConversion(x, self.NotConverted,
                                                                    {'imageUrl': cl_struct.activityDescription.technology.comment},
                                                                    {}, uri_source=True).get_source(),
            '/processDataSet/processInformation/mathematicalRelations/modelDescription':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.activity,
                                             'generalComment', self.set_TextAndImage(ILCD1Helper.text_add_index(x))),
            '/processDataSet/processInformation/mathematicalRelations/variableParameter':
                lambda cl_struct, x: self.VariableConversion(
                    x, self.NotConverted),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/typeOfDataSet':
                lambda cl_struct, x: setattr(
                    cl_struct.activityDescription.activity, 'a_type', type_process_.get(x['#text'])),
            # [!] Better verify this information
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/LCIMethodPrinciple':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'LCIMethodPrinciple', x['#text']),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/deviationsFromLCIMethodPrinciple':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'extrapolations',
                                             self.deviation_comment(ILCD1Helper.text_add_index(x,
                                                                                               prefix="Deviations from LCI Method Principles: "))) if x['#text'] != 'none' else None,
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/LCIMethodApproaches':
                lambda cl_struct, x: self._LCI_MA.append((system_model_2_.get(x['#text']),
                                                          system_model_1_.get(system_model_2_.get(x['#text'])))),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/deviationsFromLCIMethodApproaches':
                lambda cl_struct, x: setattr(cl_struct.activityDescription.activity,
                                             'allocationComment',
                                             self.set_TextAndImage(ILCD1Helper.text_add_index(x))) if x['#text'] != 'none' else None,
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
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/referenceToDataHandlingPrinciples':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToDataHandlingPrinciples', x),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/referenceToDataSource':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToDataSource', x),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/percentageSupplyOrProductionCovered':
                lambda cl_struct, x: setattr(
                    cl_struct.modellingAndValidation.representativeness, 'a_percent', x),
            # TODO [!] Can be better
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/annualSupplyOrProductionVolume':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'annualSupplyOrProductionVolume', x),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/samplingProcedure':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'samplingProcedure',
                                             ILCD1Helper.text_add_index(x, index=0)),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/dataCollectionPeriod':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'samplingProcedure',
                                             ILCD1Helper.text_add_index(x, prefix="Data Collection Period: ")),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/uncertaintyAdjustments':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'samplingProcedure',
                                             ILCD1Helper.text_add_index(x, prefix="Uncertainty Adjustments: ")),
            '/processDataSet/modellingAndValidation/LCIMethodAndAllocation/useAdviceForDataSet':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.representativeness,
                                             'samplingProcedure',
                                             ILCD1Helper.text_add_index(x, prefix="Use Advice for Dataset: ")),
            # TODO [!] Can be better
            '/processDataSet/modellingAndValidation/completeness':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'completeness', x),
            '/processDataSet/modellingAndValidation/validation/review':
                lambda cl_struct, x: setattr(cl_struct.modellingAndValidation, 'review',
                                             self.ReviewConversion(x, self.NotConverted).field),
            # TODO [!] Can be better
            '/processDataSet/modellingAndValidation/complianceDeclarations/compliance':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'compliance', x),
            # TODO [!] Can be better
            '/processDataSet/administrativeInformation/commissionerAndGoal':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'commissionerAndGoal', x),
            '/processDataSet/administrativeInformation/dataGenerator/referenceToPersonOrEntityGeneratingTheDataSet':
                lambda cl_struct, x: self.ContactReferenceConversion(x, self.NotConverted,
                                                                     cl_struct.administrativeInformation.dataGeneratorAndPublication,
                                                                     {'id': 'a_personId',
                                                                      'name': 'a_personName',
                                                                      'email': 'a_personEmail'}).get_contact(),
            '/processDataSet/administrativeInformation/dataEntryBy/timeStamp':  # Done in the default
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'timeStamp', x['#text']),
            '/processDataSet/administrativeInformation/dataEntryBy/referenceToDataSetFormat':  # TODO can be better allocated
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToDataSetFormat', x),
            '/processDataSet/administrativeInformation/dataEntryBy/referenceToConvertedOriginalDataSetFrom':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToConvertedOriginalDataSetFrom', x),
            '/processDataSet/administrativeInformation/dataEntryBy/referenceToPersonOrEntityEnteringTheData':
                lambda cl_struct, x: self.ContactReferenceConversion(x, self.NotConverted,
                                                                     cl_struct.administrativeInformation.dataEntryBy,
                                                                     {'id': 'a_personId',
                                                                      'name': 'a_personName',
                                                                      'email': 'a_personEmail'}).get_contact(),
            '/processDataSet/administrativeInformation/dataEntryBy/referenceToDataSetUseApproval':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToDataSetUseApproval', x),
            '/processDataSet/administrativeInformation/publicationAndOwnership/dateOfLastRevision':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'dateOfLastRevision', x['#text']),
            '/processDataSet/administrativeInformation/publicationAndOwnership/dataSetVersion':
                lambda cl_struct, x: (setattr(cl_struct.administrativeInformation.fileAttributes, 'a_majorRelease', int(x['#text'].split('.')[0])),
                                      setattr(
                                          cl_struct.administrativeInformation.fileAttributes, 'a_minorRelease', 0),
                                      setattr(cl_struct.administrativeInformation.fileAttributes, 'a_majorRevision', int(
                                          x['#text'].split('.')[1])),
                                      setattr(cl_struct.administrativeInformation.fileAttributes, 'a_minorRevision', int(x['#text'].split('.')[2]))),
            '/processDataSet/administrativeInformation/publicationAndOwnership/referenceToPrecedingDataSetVersion':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'referenceToPrecedingDataSetVersion', x),
            # TODO [!] isn't there a better conversion
            '/processDataSet/administrativeInformation/publicationAndOwnership/permanentDataSetURI':
                lambda cl_struct, x: setattr(
                    self.NotConverted, 'permanentDataSetURI', x['#text']),
            '/processDataSet/administrativeInformation/publicationAndOwnership/workflowAndPublication':
                lambda cl_struct, x: setattr(cl_struct.administrativeInformation.dataGeneratorAndPublication,
                                             'a_dataPublishedIn', status_publication_.get(x['#text'])),
            '/processDataSet/administrativeInformation/publicationAndOwnership/referenceToUnchangedRepublication':
                lambda cl_struct, x: self.SourceReferenceConversion(x, self.NotConverted,
                                                                    {'regular': cl_struct.administrativeInformation.dataGeneratorAndPublication},
                                                                    {'id': 'a_publishedSourceId',
                                                                        'first_author': 'a_publishedSourceFirstAuthor',
                                                                        'year': 'a_publishedSourceYear',
                                                                        'page': 'a_pageNumbers'}).get_source(),
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
                                             'a_isCopyrightProtected', x['#text']),
            '/processDataSet/administrativeInformation/publicationAndOwnership/referenceToEntitiesWithExclusiveAccess':
                lambda cl_struct, x: (self.ContactReferenceConversion(x, self.NotConverted,  # Only using the last entry
                                                                      cl_struct.administrativeInformation.dataGeneratorAndPublication,
                                                                      {'id': 'a_companyId',
                                                                       'name': 'a_companyCode'}).get_contact(),
                                      setattr(self, '_access_restricted_to', 3)),
            '/processDataSet/administrativeInformation/publicationAndOwnership/licenseType':
                lambda cl_struct, x: setattr(
                    self, '_access_restricted_to', restrictions_.get(x['#text'])),
            '/processDataSet/administrativeInformation/publicationAndOwnership/accessRestrictions':  # TODO Licensees; Licensees
                lambda cl_struct, x: setattr(
                    self._access_restriction_holder, 'a_accessRestrictedTo', access_.get(x['#text'].split(';')[0])),
            '/processDataSet/exchanges/exchange':
                lambda cl_struct, x: self.FlowReferenceConversion(x['referenceToFlowDataSet'],
                                                                  self.NotConverted,
                                                                  self.FlowConversion(
                                                                      x, self.NotConverted)
                                                                  ).get_flow().set_field(x.get('referencesToDataSource'))
        }

        return _keys

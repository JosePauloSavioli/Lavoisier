#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 11:42:36 2022

@author: jotape42p
"""

import time
import math
import re
import logging
import pint
import xmltodict

import openturns as ot

from abc import ABC, abstractmethod
from copy import copy
from pathlib import Path
from functools import reduce  # , lru_cache
# from copy import deepcopy

from .utils import (
    uuid_from_uuid,
    uuid_from_string,
    ensure_list,
    copy_file,
    FieldMapping
)
from .units import (
    pint_to_ilcd_def,
    pint_to_ilcd_fp,
    units_def
)
from .data import (
    pedigree,
    child_type,
    type_process,
    special_activity,
    energy,
    tech,
    time_period, 
    system_model,
    system_model_2,
    status_publication,
    restrictions,
    access
)
from ..formats import ILCD1Helper, ECS2Helper

up = pint.UnitRegistry()
up.define('@alias hour = h')
up.define('item = [item] = _ = Item = Items')
up.define('EUR2005 = [currency] = EUR_default')
up.define('fraction = [] = frac')
for u in units_def.values():
    up.define(u)

# Helper classes for structural class converters


class ECS2ToILCD1UncertaintyConversion:  # Not intrusive. Doesn't modify the uncertainty data entered

    statistics = 0

    def __init__(self, unc):
        # Used variables
        self._type = list(unc)[0]
        self._d = unc[self._type]

        # Get comment
        self.comment = []
        if unc.get('pedigreeMatrix'):
            self.comment.append(ILCD1Helper.text_dict_from_text(
                898, "Pedigree: ("+','.join(unc['pedigreeMatrix'].values())+")"))
            if self._d.get('@variance'):
                self.comment.append(ILCD1Helper.text_dict_from_text(
                    898, "Basic Variance: "+self._d['@variance']))
                p = 0
                for k, v in unc['pedigreeMatrix'].items():
                    p += pedigree[k[1:].capitalize().replace('corr',
                                                             ' corr').replace('technology', ' technological')][int(v)-1]
                if abs((float(self._d['@variance'])+p)-float(self._d['@varianceWithPedigreeUncertainty'])) > 0.000001:
                    logging.warning(
                        f"\t\tUncertainty: Pedigree uncertainty does not match the variance. {self._d['@variance']} + {p} != {self._d['@varianceWithPedigreeUncertainty']}")
        for i, n in enumerate(ensure_list(unc.get('comment', {}), ensure_text=True)):
            self.comment.append(ILCD1Helper.text_add_index(n, index=801+i))
        if self._type in ('beta', 'gamma', 'binomial'):
            self.comment.append(ILCD1Helper.text_dict_from_text(
                899, self._get_not_converted_text()))
        if self.comment:
            self.comment.insert(0, ILCD1Helper.text_dict_from_text(
                800, 'Uncertainty Comment:'))

        # Get data
        self._get_data()

    def _get_data(self):
        if self._type in ('lognormal', 'normal'):
            self._var = float(self._d['@varianceWithPedigreeUncertainty'])
            if self._type == 'lognormal':
                if float(self._d['@meanValue']) < 0:
                    logging.warning(
                        f"\t\tUncertainty: Lognormal uncertainty with negative geometric mean {self._d['@meanValue']}")
        elif self._type in ('triangular', 'uniform', 'undefined'):
            self._min = float(self._d['@minValue'])
            self._max = float(self._d['@maxValue'])
            if self._type == 'triangular':
                if self._min > float(self._d['@mostLikelyValue']) or self._max < float(self._d['@mostLikelyValue']):
                    logging.warning(
                        f"\t\tUncertainty: Triangular distribution with mode out of bounds: {self._min} > {self._d['@mostLikelyValue']} > {self._max}")
        if self._type == 'undefined':
            self._std = float(self._d['@standardDeviation95'])

    def _get_distribution(self, amount):
        self._unc = {
            'lognormal': (ot.LogNormal, lambda: [math.log(abs(amount.m)), math.sqrt(self._var)])
        }.get(self._type)
        return self._unc[0](*self._unc[1]())

    def _change_data(self, amount, other_unc, operation):
        logging.info(
            f"\t\tUncertainty: Distribution operation {operation} between lognormal amounts")
        unc = self._get_distribution(amount)
        new = (unc * other_unc) if operation == 'mult' else (unc / other_unc)
        if self._type == 'lognormal':
            self._var = new.getParametersCollection()[0][1] ** 2

    def _calculate(self, m, f):  # Pre-calculation
        if self._type == 'lognormal':
            self.std95 = math.exp(math.sqrt(self._var))**2
            self.min = m / self.std95
            self.max = m * self.std95
        elif self._type == 'normal':
            # Unbiased variance == sample variance
            self.std95 = 2*math.sqrt(self._var)*f
            self.min = m - self.std95
            self.max = m + self.std95
        elif self._type in ('triangular', 'uniform'):
            self.min = self._min * f
            self.max = self._max * f
        elif self._type == 'undefined':  # STD here is like an error propagation
            # This is certain, the maximum and minimum are calculated from this
            self.std95 = self._std * f
            self.min = (self._min + self._max) * f / 2 - self.std95
            self.max = (self._min + self._max) * f / 2 + self.std95
        return self

    def get_uncertainty(self, field, comment, not_converted=None, type_="Amount"):
        for t in self.comment:
            setattr(field, comment, t)
        if self._type in ('beta', 'gamma', 'binomial'):
            if hasattr(self, 'not_converted'):
                not_converted.uncertainty = self.not_converted
        else:
            if type_ == "Amount":
                field.minimumAmount = self.min
                field.maximumAmount = self.max
            elif type_ == "Value":
                field.minimumValue = self.min
                field.maximumValue = self.max
            field.uncertaintyDistributionType = self._type.replace(
                "lognormal", "log-normal")
            if self._type in ('lognormal', 'normal', 'undefined'):
                field.relativeStandardDeviation95In = self.std95

            # Update statistic
            type(self).statistics += 1

    def _get_not_converted_text(self):
        return {
            'beta': lambda: f"\nNot Converted: Beta distribution with parameters min={self._d['@minValue']}, most frequent={self._d['@mostLikelyValue']}, max={self._d['@maxValue']}",
            'gamma': lambda: f"\nNot Converted: Gamma distribution with parameters shape={self._d['@shape']}, scale={self._d['@scale']}, min={self._d['@minValue']}",
            'binomial': lambda: f"\nNot Converted: Binomial distribution with parameters n={self._d['@n']}, p={self._d['@p']}"
        }.get(self._type)()


class Amount(ABC):

    uncertainty_conversion = None

    def __init__(self, amount, unit_text, uncertainty_struct):
        self._a = up.Quantity(amount, self.unit_name_correction(unit_text))
        self._f = 1
        if uncertainty_struct is not None:
            self._unc = type(self).uncertainty_conversion(uncertainty_struct)
        self.o = copy(self)

    @abstractmethod
    def unit_name_correction(name):
        pass

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

    def calculate_unc(self):
        pass


class ECS2ToILCD1VariableConversion:

    _all_variable_names = []

    statistics = 0

    class Formula:

        amountClass = None

        def __init__(self, math, var):
            self.math = math
            self.__o_math = math
            self.var = var

        def correct_unit_conversion(self, field):
            def _subroutine(x):
                b, i, n, m, f = 0, False, '', '', []
                for l in iter(x):
                    n += l
                    if l == '(' and i:
                        b += 1
                        m += l
                    elif l == ')' and i:
                        b -= 1
                        m += l
                        if b == 0:
                            f.append(m[1:-1])
                            m = ''
                            i = False
                    elif i: m += l
                    if n[-14:] == 'UnitConversion': i = True
                return f
            
            # Unit convertion correction
            if re.search('UnitConversion', self.math):
                for elem in _subroutine(self.math):# re.findall(r"UnitConversion\(([\w -.',]+?)\)", self.math):
                    
                    elem_ = [elem.replace("'", '').split(', ')[0]] +\
                        [type(self).amountClass.unit_name_correction(
                            e) for e in elem.replace("'", '').split(', ')[1:]]
                    try:
                        value = float(elem_[0].replace(',', '.').replace('_', ''))
                    except ValueError:
                        value = elem_[0]
                    amount = type(self).amountClass.from_single_init(
                            1, elem_[1]).to(elem_[2])
                    if self.var._cv:
                        x = self.var.unit_conversion_var(amount).create(
                            field,
                            amount,
                            [ILCD1Helper.text_dict_from_text(10, f"\nConversion from {amount.get_original_unit_str()} to {amount.get_final_unit_str()} for UnitConversion formulas")])
                        if x is not None:
                            field.variableParameter = x
                    self.math = self.math.replace('UnitConversion'+f'({elem})',
                                      "("+(str(value) if isinstance(value,float) else f"({value})")+'*'+amount.get_conversion_str()+")")
                
                logging.info(
                    f"\t\tFormula corrected from {self.__o_math} to {self.math}")
            return self

        def correct_ref(self, excs):
            # Reference to other flow ID for production volume ID correction
            if re.search(r'Ref\(', self.math):
                for elem in re.findall(r"Ref\('(.*?)'\)", self.math):
                    e = excs[elem.split("'")[0]]
                    elem_ = elem.split("'")
                    if len(elem_) > 1:
                        if elem_[2] == 'ProductionVolume':
                            value = e[1]
                    else:
                        value = e[0]
                    self.math = re.sub(
                        r"Ref\('"+elem+r"'\)", str(value), self.math)
                logging.info(
                    f"\t\tFormula corrected from {self.__o_math} to {self.math}")
            return self

        def correct_other(self):
            # Percentage correction
            if re.search('%', self.math):
                self.math = re.sub('%', '/ 100', self.math)
                logging.info(
                    f"\t\tFormula corrected from {self.__o_math} to {self.math}")
            # Float with ',' as decimal separator correction
            if re.search('[0-9]+,[0-9]+', self.math):
                self.math = re.sub(',', '.', self.math)
                logging.info(
                    f"\t\tFormula corrected from {self.__o_math} to {self.math}")
            return self

    def __init__(self, var_name, math, com=None, convert_unit=True):
        # Used variables
        self._name = var_name
        self._math = math
        if self._math:
            self._math = self._math.strip() # Some residual can come
        if com is not None:
            self._com = com
        self._cv = convert_unit

    def create(self, field, amount, comment):
        if self._name not in type(self)._all_variable_names:
            type(self)._all_variable_names.append(self._name)
            v = field.get_class('variableParameter')()
            v.a_name = self._name
            if self._math:
                v.formula = self.Formula(self._math, self).correct_unit_conversion(
                    field).correct_ref(type(amount)._flow_result_for_formula).correct_other().math
            v.meanValue = amount.m
            if amount.unc is not None:
                type(amount).uncertainty_conversion.statistics -= 1
                amount.calculate_unc().get_uncertainty(v, 'comment', type_="Value")
            if comment is not None:
                for c in comment:
                    v.comment = c
            return v
        else:
            return None

    @staticmethod
    def get_str(amount, x):
        return x+"__from_"+amount.get_conversion_str()[2:]

    @staticmethod
    def get_math(amount, x):
        return "("+x+")*"+amount.get_conversion_str()

    def converted_var(self, amount, convert_unit=True):
        _math = self.get_math(amount, self._math) if self._math else None
        _name = self.get_str(amount, self._name)
        _name = _name if len(_name) <= 50 else _name.split('__from')[0]+'__uc'
        return ECS2ToILCD1VariableConversion(_name, _math, convert_unit)

    @staticmethod
    def unit_conversion_var(amount):
        _math = None
        _name = amount.get_conversion_str()
        return ECS2ToILCD1VariableConversion(_name, _math)


class AmountWithVariable(Amount, ABC):

    variable_conversion = None

    def __init__(self, amount, unit_text, uncertainty_struct, variable):
        super().__init__(amount, unit_text, uncertainty_struct)
        if variable[0] or variable[1]:
            self._var = type(self).variable_conversion(*variable)
        self.o = copy(self)


# Maintain name as it can be used in other conversions
class ECS2ToILCD1Amount(AmountWithVariable):

    variable_holder = None
    
    _equation_counter = 1
    _flow_result_for_formula = {}
    _all_amounts = []

    def __init__(self, amount, unit_text, uncertainty_struct, variable, type_, no_conversion_to_ilcd_unit=False, tab='\t'):
        # Set the amount here is necessary due to uncertainty being optional
        super().__init__(amount, unit_text, uncertainty_struct, variable)
        if variable[0] or variable[1]:
            self._var._name = self._var._name if self._var._name is not None else "Eq_" + \
                type_[:2]+"_"+str(type(self)._equation_counter)
            type(self)._equation_counter += 1

        self.type_ = type_
        if not no_conversion_to_ilcd_unit:
            if uncertainty_struct is not None:
                self.o._unc._calculate(self.o.m, 1)

            self._a = self.to_ilcd_unit(self._a)
            if self.o.u != self._a.u:
                logging.info(
                    f"{tab}Unit conversion from {self.o.u} to {self._a.u} with a multiplication factor of {self.f}")

        type(self)._all_amounts.append(self)

    @classmethod
    def from_single_init(cls, amount, unit_text):
        return cls(amount, unit_text, None, (None, None), '', no_conversion_to_ilcd_unit=True, tab='')

    def multiply(self, other):  # LOG return a new instance [better for debug]
        if isinstance(other, ECS2ToILCD1Amount):
            if hasattr(self, '_unc') and hasattr(other, '_unc'):
                if self._unc._type == other._unc._type == 'lognormal':
                    self._unc._change_data(
                        self, other._unc._get_distribution(other), 'mult')
                else:
                    del self._unc  # If there is a multiplication and it is not two lognormal uncertainties, desconsider uncertainty
        self._a = self._a * (other.a if isinstance(other,
                             ECS2ToILCD1Amount) else other)
        self._f *= other.m

    def divide(self, other):  # LOG return a new instance [better for debug]
        if isinstance(other, ECS2ToILCD1Amount):
            if hasattr(self, '_unc') and hasattr(other, '_unc'):
                if self._unc._type == other._unc._type == 'lognormal':
                    self._unc._change_data(
                        self, other._unc._get_distribution(other), 'div')
                else:
                    del self._unc  # If there is a division and it is not two lognormal uncertainties, desconsider uncertainty
        self._a = self._a / (other.a if isinstance(other,
                             ECS2ToILCD1Amount) else other)
        self._f /= other.m

    def calculate_unc(self):
        if hasattr(self, '_unc'):
            self._unc = self._unc._calculate(self._a.m, self._f)
            return self._unc
        return None

    def construct_variable(self):
        # Done after due to formulas
        field = type(self).variable_holder
        if self._f != 1 and self.type_ == "flow":
            cv_u = True

            # Original to be used in other formulas as variable [check if the variable name is not for the equation-only case]
            if hasattr(self, '_var') and not re.search(r'Eq_[a-z]{2}_[0-9]+', self._var._name):
                c = [ILCD1Helper.text_dict_from_text(-1, '['+self.get_original_unit_str()+']')]
                x = self._var.create(field, self.o, c)
                if x is not None: 
                    field.variableParameter = x
                cv_u = False

            # Converted
            if hasattr(self, '_var'):
                var_c = self._var = self._var.converted_var(self, convert_unit=cv_u)
                type(self).variable_conversion.statistics += 1
            else:
                var_c = self._var = type(self).variable_conversion(
                    'Eq_uv_'+str(type(self)._equation_counter), str(self.o.m)+'*'+self.get_conversion_str(), convert_unit=cv_u)
            type(self)._equation_counter += 1
            c = [ILCD1Helper.text_dict_from_text(-1, '['+self.get_final_unit_str()+']')]
            x = var_c.create(field, self, c)
            if x is not None: 
                field.variableParameter = x

            # Conversion
            amount = ECS2ToILCD1Amount.from_single_init(
                self.f, 'dimensionless')
            var_c = self._var.unit_conversion_var(self)
            c = [ILCD1Helper.text_dict_from_text(-1, f"\nConversion from {self.get_original_unit_str()} to {self.get_final_unit_str()}")]
            x = var_c.create(field, amount, c)
            if x is not None: 
                field.variableParameter = x

            logging.info(
                f"\tConversion variable {self._var._name if self._var._name is not None else self._var._math}")
        # normal flow, property, parameter, production_volume amounts are all self.o
        elif hasattr(self, '_var'):
            c = [ILCD1Helper.text_dict_from_text(-1, '['+self.get_original_unit_str()+']')] + getattr(self._var, '_com', [])
            x = self._var.create(field, self.o, c)
            if x is not None:
                field.variableParameter = x
            type(self).variable_conversion.statistics += 1

    @classmethod
    def add_flow_data(cls, data):
        cls._flow_result_for_formula.update(data)

    # can't place the cache here since two amounts can result in the same answer
    def to_ilcd_unit(self, qtt):
        uuid_ = uuid_from_string(str(qtt.dimensionality))
        if uuid_ in pint_to_ilcd_def.keys():
            unit = pint_to_ilcd_def[uuid_][-1]
            if str(qtt.u) != unit:  # Just for time gain
                self._f *= up.Quantity(1, qtt.u).to(unit).m
                return qtt.to(unit)
            else:
                return qtt
        else:  # LOG
            self._f *= up.Quantity(1, qtt.u).to_base_units().m
            return qtt.to_base_units()

    @staticmethod
    def unit_name_correction(name):

        if not isinstance(name, str):
            return name

        # Basic replacements
        rep = [('(2011)', '2011'),
               ('% (obsolete)', 'pct'),
               (' ', '_'),
               ('-', '_'),
               ('.', '*'),
               ('^', '**'),
               ('/hp*h', '/(hp*h)'),
               ('(s)', 's')]

        name = reduce(lambda y, x: y.replace(*x), rep, name)

        # Exponent assignment: Capture several letters followed by a number. The number can't be followed by a number
        if re.search(r'([a-zA-Z]{1,})[2-4]{1}(?![\d])', name):
            exp = all(s not in name for s in (
                'NH3', 'N2O', 'NO3', 'P2O5', 'PO4'))
            if exp:
                name = reduce(lambda y, x: re.sub(r"([a-zA-Z]{1,})"+x+r"{1}(?![\d])", r"\1**"+x, y),
                              [r'2', r'3', r'4'], name)

        if name not in up:  # Hardcoded units TODO [!] Deprecated
            try:
                up.define(units_def[name])
            except:
                raise ValueError(
                    f'Unit {name} is not defined in the scope of the program')

        return name

    def __str_unit(self, x):
        return f"{x:~}".replace(" ", "").replace("/", "_per_").replace("**", "").replace("*", "_times_").replace(".", "_")

    def get_original_unit_str(self):
        return self.__str_unit(self.o.u)

    def get_final_unit_str(self):
        return self.__str_unit(self._a.u)

    def get_conversion_str(self):
        return "__"+self.get_original_unit_str()+"_to_"+self.get_final_unit_str()+"__"


class ECS2ToILCD1QuantitativeObject(ABC):

    ref_conversion = None

    def __init__(self, id_, type_):
        self.id_ = id_
        self.type_ = type_

    def get_source(self, id_, source_ref):
            return self.ref_conversion("source",
                                        (True, id_),
                                        source_ref).make_dataset({
                                            "reference": source_ref,
                                            "classification": 'Publications and communications'
                                        }).field

# Structural class converters


class ECS2ToILCD1ParameterConversion(ECS2ToILCD1QuantitativeObject):

    amountClass = None    

    statistics = 0

    def __init__(self, x, not_converted):
        # No source, converted as variable, no unit constraint, uses var_comment to place a variable comment
        
        logging.info(
            f'Started conversion of Parameter: {x["name"]["#text"] if isinstance(x["name"], dict) else x["name"][0]["#text"]} : {x["@parameterId"]}')
        # Initializate QuantitativeObject
        super().__init__(x["@parameterId"], 'parameter')

        # Set instances
        self.not_converted = not_converted.Parameter()

        # Get comment
        c = []
        for n in ensure_list(x.get('comment', {})):
            c.append(ILCD1Helper.text_add_index(n))
        # self.amount.construct_variable(comment=c)
        
        # Used variables
        self.units = ([a["#text"] for a in ensure_list(
            x.get('unitName', {}))], x.get('@unitId'))
        self.amount = type(self).amountClass(float(x['@amount']),
                                        self.units[0][0] if self.units[0] else 'dimensionless',
                                        x.get('uncertainty'),
                                        (x.get('@variableName'),
                                         x.get('@mathematicalRelation'), c),
                                        'parameter',
                                        no_conversion_to_ilcd_unit=True,
                                        tab='\t\t')
        self.amount.calculate_unc()

        # Get statistics
        type(self).statistics += 1

        # Get not converted
        self.get_not_converted(x)

    def get_not_converted(self, x): # name? (beacause the used one is the variable name)
        if x.get('@isCalculatedAmount'):
            self.not_converted.a_isCalculatedAmount = x['@isCalculatedAmount']
        if x.get('@parameterContextId'):
            self.not_converted.a_parameterContextId = x['@parameterContextId']
        if x.get('@unitContextId'):
            self.not_converted.a_unitContextId = x['@unitContextId']


class ECS2ToILCD1FlowConversion(ECS2ToILCD1QuantitativeObject):

    amountClass = None    

    convert_properties = None
    class_conversion = None
    
    quantity_holder = None
    flow_holder = None

    _flow_internal_id_counter = 1
    _all_flows = []
    _all_flow_prop_values = {}
    _main_property = None
    _allocation_properties = {}

    class Property(ECS2ToILCD1QuantitativeObject):

        amountClass = None

        flow_property_field = None
        
        _energy = None
        
        _prop_internal_id_counter = 1

        statistics = 0

        def __init__(self, x, ref_field, flow_not_converted):
            # Two booleans, unit is optional, constrained to available ilcd properties
            
            logging.info(
                f'\tStarted conversion of Property: {x["name"]["#text"] if isinstance(x["name"], dict) else x["name"][0]["#text"]} : {x["@propertyId"]}')
            # Initializate QuantitativeObject
            super().__init__(x['@propertyId'], 'flow')

            # Set instances
            self.field = self.flow_property_field()
            self.not_converted = flow_not_converted.Property()

            # Used variables
            self.is_considered = True
            self.has_ilcd_equivalent = True

            self.uuid = pint_to_ilcd_fp.get(x['@propertyId'], None)
            self.units = ([a["#text"] for a in ensure_list(x.get('unitName', {}))], x.get(
                '@unitId'))  # Units are optional in properties
            self.amount = type(self).amountClass(float(x['@amount']),
                                            self.units[0][0] if self.units[0] else 'dimensionless',
                                            x.get('uncertainty'),
                                            (x.get('@variableName'),
                                             x.get('@mathematicalRelation')),
                                            'property',
                                            tab='\t\t')

            # Other getters
            if x.get('@sourceId'):
                source = self.get_source(x['@sourceId'],
                                ILCD1Helper.source_short_ref(x.get('@sourceFirstAuthor'),
                                                             x.get('@sourceYear'),
                                                             None))
                try:
                    ref_field.referencesToDataSource.referenceToDataSource = source
                except KeyError:
                    ref_field.referenceToExternalDocumentation = source

            if self.uuid is None: # Get comment on 'not_converted'
                logging.warning(
                    f"\t\tproperty '{x['name']['#text'] if isinstance(x['name'], dict) else x['name'][0]['#text']}' not a valid ILCD property")
                self.not_converted.a_amount = x['@amount']
                if (x.get('@unitId') and x.get('unitName')):
                    self.not_converted.a_unitId = x['@unitId']
                else:
                    self.is_considered = False
                self.has_ilcd_equivalent = False
            elif not (x.get('@unitId') and x.get('unitName')):
                logging.warning(
                    f"\t\tproperty '{x['name']['#text'] if isinstance(x['name'], dict) else x['name'][0]['#text']}' doesn't have an unit")
                self.not_converted.a_amount = x['@amount']
                self.is_considered = False
                self.has_ilcd_equivalent = False
            else:  # Get property

                # Get comment
                for n in ensure_list(x.get('comment', {}), ensure_text=True):
                    self.field.generalComment = ILCD1Helper.text_add_index(n)

                # Get basic fields
                self.field.a_dataSetInternalID = type(
                    self)._prop_internal_id_counter
                type(self)._prop_internal_id_counter += 1

                # Get reference to flow property
                self.field.referenceToFlowPropertyDataSet = self.ref_conversion(
                    'flow property',
                    (False,
                     self.uuid[0]),
                    self.uuid[-1],
                    version=self.uuid[-2]
                ).make_dataset({
                    'unit_id': self.uuid[1]
                }).field

            # Get not converted
            self.get_not_converted(x)

        def get_not_converted(self, x):
            if x.get('@propertyContextId'):
                self.not_converted.a_propertyContextId = x['@propertyContextId']
            if x.get('@isDefiningValue'):
                self.not_converted.a_isDefiningValue = x['@isDefiningValue']
            if x.get('@isCalculatedAmount'):
                self.not_converted.a_isCalculatedAmount = x['@isCalculatedAmount']
            if x.get('@unitContextId'):
                self.not_converted.a_unitContextId = x['@unitContextId']
            if x.get('@sourceIdOverwrittenByChild'):
                self.not_converted.a_sourceIdOverwrittenByChild = x['@sourceIdOverwrittenByChild']
            if x.get('@sourceContextId'):
                self.not_converted.a_sourceContextId = x['@sourceContextId']

        @staticmethod
        def get_ilcd_equivalent(props, flow):
            # Generic properties (related to the flow not to the flow in a process)

            mnames = []
            if props:
                
                def correction_for_flow_unit_conversion(p, case):
                    mnames.append(p)
                    if flow.amount.f != 1:
                        f = up.Quantity(flow.amount.f, 'dimensionless')
                        t = f"\t\t[{case}] Property {p}: {props[p].amount.a} corrected for flow unit conversion of [division by {flow.amount.f}] to "
                        props[p].amount.divide(f)
                        if props[p].amount.m != 0:
                            logging.info(t+f"{props[p].amount.a}")
                
                def correction_for_dry_mass(p, case):
                    mnames.append(p)
                    if props.get('dry mass'):
                        f = props['dry mass'].amount
                        if f.m != 1:
                            t = f"\t\t[{case}] Property {p}: {props[p].amount.a} corrected for dry mass of [multiplication by {props['dry mass'].amount.a}] to "
                            props[p].amount.multiply(f)
                            if props[p].amount.m != 0:
                                logging.info(t+f"{props[p].amount.a}")
                        else: # just for unit correction
                            props[p].amount.multiply(f)
                    else:
                        props[p].is_considered = False
                        logging.warning(f"\t\tProperty '{p}' not considered as a dry mass value is not available")
                    
                def correction_for_flow_amount(p, case):
                    mnames.append(p)
                    f = flow.amount.a
                    f = f * (1 if f.m >= 0 else -1) # Can be a negative flow
                    if f.m != 1:
                        t = f"\t\t[{case}] Property {p}: {props[p].amount.a} corrected for flow unit conversion of [division by {flow.amount.a}] to "
                        props[p].amount.multiply(f)
                        if props[p].amount.m != 0:
                            logging.info(t+f"{props[p].amount.a}")
                    else: # just for unit correction
                        props[p].amount.multiply(f)
                    
                # Correction for flow unit [flow from ha to m2 (*10000). Dry mass from kg/ha to kg/m2 (/10000)]
                for p in ('dry mass', 'wet mass', 'water in wet mass', 'price', 'true value relation', 'lifetime'):
                    if p in props.keys():
                        correction_for_flow_unit_conversion(p, '1')

                # Correction for dry mass [dry mass is already corrected. Properties are per dry mass. Property from % to kg]
                for p in ('water content', 'carbon content, fossil', 'carbon content, non-fossil'):
                    if p in props.keys():
                        correction_for_dry_mass(p, '2')
                    elif props.get('dry mass') and p == 'water content' and props.get('wet mass'):
                        mnames.append(p)
                        logging.info(f"\t\tWater content information estimated for {flow.fid}")
                        p_dict = {"name": {"#text": p},
                                  "@propertyId": "a9358458-9724-4f03-b622-106eda248916",
                                  "@amount": props['wet mass'].amount.m - props['dry mass'].amount.m,
                                  "unitName": {"@lang": "en", "#text": 'kg'},
                                  "@unitId": "487df68b-4994-4027-8fdc-a4dc298257b7"}
                        props[p] = flow.Property(p_dict, flow.field, flow.not_converted)

                # General correction
                for p in props.keys():
                    if p not in mnames:

                        u = str(props[p].amount.o.u).replace(" ", "").split("/")
                        # Contents are considered relative to the amount and are considered as a general property of a flow
                        if 'content' in p:
                            # Correction of content for flow unit [flow from ha to m2 (*10000). Property from kg/ha to kg/m2 (/10000)]
                            if str(props[p].amount.u) in ('kilogram', 'megajoule'): # megajoule for energy content
                                correction_for_flow_unit_conversion(p, '3')
                            # Correction of content for dry mass (Property from % to kg)
                            elif str(props[p].amount.u) == 'dimensionless':
                                correction_for_dry_mass(p, '4')
                            else:
                                logging.warning(f"\t\tProperty '{p}' of type 'content' not converted")
                                props[p].is_considered = False
                        # Concentrations are considered general property of a flow (the ones with a comma)
                        elif 'concentration, ' in p and len(u) > 1:
                            # Correction of concentration for flow amount [flow from ha to m2 (*10000). Property from kg/ha to kg/m2 to kg (*flow)]
                            if up.Quantity(u[-1]).check(flow.amount.dimensionality):
                                correction_for_flow_amount(p, '5')
                        # Heating values are considered general property of a flow (the ones with a comma)
                        elif 'heating value, ' in p and str(props[p].amount.o.u) == 'megajoule':
                            correction_for_flow_unit_conversion(p, '6')
                        # Lifetime values are considered general property of a flow [flow from dozen to item (*12). Lifetime cap from MJ/dozen to MJ/item (/12)]
                        elif 'lifetime capacity' in p:
                            correction_for_flow_unit_conversion(p, '7')

                    if p not in mnames:
                        logging.warning(f"\t\tProperty '{p}' not converted")
                        props[p].is_considered = False

            if 'water content' in props and 'water in wet mass' in props:
                del props['water in wet mass'] # Duplication

            return props

        @classmethod
        def get_unit_property(cls, dimensionality):
            # Set instances
            field = cls.flow_property_field()

            def get_energy_prop(cls, uuid_):
                # For energy, the default is the Net Energy if energyValue is not informed
                if uuid_ == 'f09fb2f1-8af1-3630-8463-c7ebc26474be':
                    return {
                        None: uuid_,
                        'undefined': uuid_,
                        'net calorific value': uuid_,
                        'gross calorific value': 'f09fb2f1-8af1-3630-8463-c7ebc26474bf'
                    }.get(cls._energy)
                else:
                    return uuid_

            # Used variables
            unit_id = get_energy_prop(cls, uuid_from_string(
                str(dimensionality)))

            # Set fields
            field.a_dataSetInternalID = '0'
            try:
                field.referenceToFlowPropertyDataSet = cls.ref_conversion(
                    'flow property',
                    (False, pint_to_ilcd_fp.get(
                        unit_id)[0]),
                    pint_to_ilcd_fp.get(
                        unit_id)[-1],
                    version=pint_to_ilcd_fp.get(
                        unit_id)[-2]
                ).make_dataset({
                    'unit_id': pint_to_ilcd_fp.get(unit_id)[1]
                }).field
            except:
                raise ValueError(f"Unit with dimensions '{dimensionality}' not found in the unit table")
            field.meanValue = 1.0
            field.generalComment = ILCD1Helper.text_dict_from_text(
                1, 'Main flow unit')

            return field.get_dict()

        def get_dict(self):  # Necessary to call after the properties are properly calculated
            # Get statistic
            type(self).statistics += 1
            self.field.meanValue = self.amount.m
            if self.amount.unc:
                self.amount.calculate_unc().get_uncertainty(
                    self.field, 'generalComment', self.not_converted, type_="Value")

            return self.field.get_dict()

    def __init__(self, x, initialize=True):
        # Initializate QuantitativeObject
        super().__init__(x['@id'], 'flow')

        # Set instances
        self.field = type(self).flow_holder.get_class('exchange')()

        # Reset variables
        self.Property._prop_internal_id_counter = 1

        # Used variables
        if initialize:
            self.basic_initialization(x)
        self.allocation_property = x.get(
            "@specificAllocationProperty", type(self)._main_property)
        if self.allocation_property != type(self)._main_property:
            logging.info(
                f"\tSpecific allocation property {self.allocation_property}")

        # Get comment
        for n in ensure_list(x.get('comment', {}), ensure_text=True):
            self.field.generalComment = ILCD1Helper.text_add_index(n)
        if x.get('tag'):
            self.field.generalComment = ILCD1Helper.text_dict_from_text(
                -1, 'Tag '+'; '.join([t for t in x.get("tag", [])]))

        # Get uncertainty
        if self.amount.unc:
            self.amount.calculate_unc().get_uncertainty(
                self.field, 'generalComment', self.not_converted)

        # Other getters
        self.get_direction(x)
        if type(self).convert_properties:
            self.get_properties(x)
        else:
            self.remaining_properties = []

        # Set basic fields
        self.field.exchangeDirection = self.direction

        # Other getters
        if x.get('@sourceId'):
            self.field.referencesToDataSource.referenceToDataSource =\
                self.get_source(x['@sourceId'],
                                ILCD1Helper.source_short_ref(x.get('@sourceFirstAuthor'),
                                                             x.get('@sourceYear'),
                                                             x.get('@pageNumbers')))

        # Append self
        ECS2ToILCD1FlowConversion._all_flows.append(self)

    def basic_initialization(self, x):
        self.id_ = x['@id']
        self.units = ([n["#text"]
                      for n in ensure_list(x['unitName'])], x['@unitId'])
        if len(self.units[0]) > 1:
            logging.info(f"\tMore than one unit: {self.units}")
        # Here I state that the first unit is the valid one
        self.amount = type(self).amountClass(float(x["@amount"]),
                                        self.units[0][0],
                                        x.get('uncertainty'),
                                        (x.get('@variableName'),
                                         x.get('@mathematicalRelation')),
                                        'flow')

    def get_direction(self, x):
        self.direction, self.direction_type = ('Input', x["inputGroup"]["#text"]) if x.get(
            'inputGroup') else ('Output', x['outputGroup']["#text"])
        if hasattr(self, '_by_prod_class'):
            self.ftype = "Waste flow" if self._by_prod_class == "Waste" else "Product flow"
            logging.info(
                f"\tFlow type '{self.ftype}' gathered from by-product classification")
        else:
            if self.direction == "Output":
                self.ftype = {
                    "0": "Product flow",
                    "2": "Product flow",
                    "3": "Waste flow",
                    "4": "Elementary flow",
                    "5": "Product flow"
                }.get(self.direction_type)
            else:
                self.ftype = "Elementary flow" if self.direction_type == '4' else "Product flow"

        # Due to inheritance, type(self) is not the ideal here since a call from Elementary would reset the counter
        cls = ECS2ToILCD1FlowConversion
        self.field.a_dataSetInternalID = cls._flow_internal_id_counter
        if self.direction == "Output" and self.direction_type == "0":
            setattr(cls.quantity_holder, 'referenceToReferenceFlow', cls._flow_internal_id_counter)
        cls._flow_internal_id_counter += 1

    def get_allocation(self):
        cls = ECS2ToILCD1FlowConversion
        if self.id_ in cls._allocation_properties.keys():
            n = sum([x for x in cls._allocation_properties.values()])
            s = self.field.allocations.get_class('allocation')
            s.internalReferenceToCoProduct = 0
            s.allocatedFraction = cls._allocation_properties[self.id_] / n
            self.field.allocations = s

    # Various exceptions for the elementary flows not converted
    def get_properties(self, x, elem_not_converted_ref_field=None):
        self.properties = {}
        for prop in ensure_list(x.get("property", {})):
            p = self.Property(prop,
                              self.field if elem_not_converted_ref_field is None else elem_not_converted_ref_field,
                              self.not_converted)
            if hasattr(self, 'allocation_property') and prop['@propertyId'] == self.allocation_property:
                logging.info(
                    f"\tAllocated flow by property {prop['name']['#text']}")
                ECS2ToILCD1FlowConversion._allocation_properties.update(
                    {self.id_: p.amount.o.m * self.amount.o.m})
            if p.is_considered:
                self.properties[prop['name']["#text"]] = p
        self.properties = self.Property.get_ilcd_equivalent(
            self.properties, self)
        self.remaining_properties = []
        for prop in self.properties.values():
            if prop.is_considered and prop.has_ilcd_equivalent:
                self.remaining_properties.append(prop)

    def get_not_converted(self, x):
        self.not_converted.a_id = self.id_
        self.not_converted.a_fId = self.fid
        for t in ensure_list(x.get('tag', {})):
            self.not_converted.tag = t['#text'] if isinstance(t, dict) else t
        if x.get('@unitContextId'):
            self.not_converted.a_unitContextId = x['@unitContextId']
        if x.get('@isCalculatedAmount'):
            self.not_converted.a_isCalculatedAmount = x['@isCalculatedAmount']
        if x.get('@sourceIdOverwrittenByChild'):
            self.not_converted.a_sourceIdOverwrittenByChild = x['@sourceIdOverwrittenByChild']
        if x.get('@specificAllocationPropertyIdOverwrittenByChild'):
            self.not_converted.a_specificAllocationPropertyIdOverwrittenByChild = x[
                '@specificAllocationPropertyIdOverwrittenByChild']
        if x.get('@specificAllocationPropertyContextId'):
            self.not_converted.a_specificAllocationPropertyContextId
        for t in x.get('transferCoefficient', []):
            self.not_converted.transferCoefficient = t


class ECS2ToILCD1IntermediateFlowConversion(ECS2ToILCD1FlowConversion):

    statistics = 0

    class ProductionVolume(ECS2ToILCD1QuantitativeObject):

        amountClass = None        

        prod_v_holder = None
        
        _prod_v_number = -1000
        
        statistics = 0

        def __init__(self, x, flow):
            # Initializate QuantitativeObject
            super().__init__(x['@id'], 'production volume')

            # Set instance
            self.not_converted = flow.not_converted.ProductionVolume()

            # Used variables
            self.amount = type(self).amountClass(float(x['@productionVolumeAmount']),
                                            flow.amount.o.u,
                                            x.get(
                                                'productionVolumeUncertainty'),
                                            (x.get('@productionVolumeVariableName'),
                                             x.get('@productionVolumeMathematicalRelation')),
                                            'production_volume',
                                            no_conversion_to_ilcd_unit=True,  # They don't need unit conversions for var or std
                                            tab='\t\tProdVolume: ')

            # Get uncertainty
            unc_text = ''
            if self.amount.unc:
                self.uncertainty = self.amount.calculate_unc()
                if hasattr(self.uncertainty, 'std'):
                    unc_text = f" with standard deviation of {self.uncertainty.std}"

            # Other getters
            if x.get('@productionVolumeSourceId'):
                flow.field.referencesToDataSource.referenceToDataSource =\
                    self.get_source(x['@productionVolumeSourceId'],
                                    ILCD1Helper.source_short_ref(x.get('@productionVolumeSourceFirstAuthor'),
                                                                 x.get('@productionVolumeSourceYear'),
                                                                 None))

            # Get comment
            for n in ensure_list(x.get('productionVolumeComment', {})):
                flow.field.generalComment = ILCD1Helper.text_add_index(
                    n, prefix='Production Volume Comment: ')
            text = f"Production volume for {x['name']['#text']} is {self.amount.m} {self.amount.u}" + unc_text
            setattr(type(self).prod_v_holder, 'annualSupplyOrProductionVolume',
                    ILCD1Helper.text_dict_from_text(type(self)._prod_v_number, text))
            type(self)._prod_v_number += 1

            # Get statistic
            type(self).statistics += 1

            # Get not converted
            self.get_not_converted(x)

        def get_not_converted(self, x):
            if x.get('@productionVolumeSourceIdOverwrittenByChild'):
                self.not_converted.a_productionVolumeSourceIdOverwrittenByChild = x[
                    '@productionVolumeSourceIdOverwrittenByChild']
            if x.get('@productionVolumeSourceContextId'):
                self.not_converted.a_productionVolumeSourceContextId = x[
                    '@productionVolumeSourceContextId']

    def __init__(self, x, not_converted):
        
        logging.info(
            f'Started conversion of Intermediate Flow: {x["name"]["#text"] if isinstance(x["name"], dict) else x["name"][0]["#text"]} : {x["@id"]}')
        # Set instances
        self.not_converted = not_converted.Flow()
        # Used variables
        self.fid = x["@intermediateExchangeId"]

        # Get classification fields
        self.get_classification(x)

        # Get processDataSet fields
        super().__init__(x)

        # Assess productionVolume fields and feed variable conversion with the amounts for the formula correction
        if x.get("@productionVolumeAmount"):
            logging.info('\tProduction volume found')
            self.production_volume = self.ProductionVolume(x, self)
            self.amount.add_flow_data(
                {self.id_: (self.amount.o.m, self.production_volume.amount.o.m)})
        else:
            self.amount.add_flow_data({self.id_: (self.amount.o.m, None)})

        # Get comment
        if x.get('activityLinkId'):
            self.field.generalComment = ILCD1Helper.text_dict_from_text(
                -20, f'Ecoinvent activity linkable id: {x["activityLinkId"]}')

        # Make of the ILCD flowDataSet
        self.get_flow_dict(x)

        # Get statistic
        type(self).statistics += 1

        # Get not converted
        self.get_not_converted(x)
        not_converted = self.not_converted

    def get_flow_dict(self, x):
        name = [n["#text"] for n in ensure_list(x['name'])]
        synonyms = '; '.join([n["#text"]
                             for n in ensure_list(x.get('synonym', {})) if n])
        fp = [self.Property.get_unit_property(self.amount.dimensionality)]
        for p in self.remaining_properties:
            fp.append(p.get_dict())

        self.__args = ['flow', (True, self.fid), name[0]]
        ref = self.ref_conversion(*self.__args)
        
        def send_data_to_make_dataset(version):
            info = {
                'type': 'intermediate',
                'name': name[0],
                'synonyms': synonyms,
                **({'classification': self.classification} if getattr(self, 'classification', None) else {}),
                **({'casNumber': x.get('@casNumber')} if x.get('casNumber') else {}),
                'generalComment': f"Ecospold 2 exchange, IntermediateExchangeID = {self.fid}",
                'typeOfDataSet': self.ftype,
                'version': version,
                'flowProperty': fp
            }
            self.field.referenceToFlowDataSet = self.ref_conversion(
                *self.__args, version=version).make_dataset(info).field

        def get_version(ref, add):
            ref.complete_info(add)
            return ref.field
        
        # If there are different properties, the flow is made again
        if self.fid in type(self)._all_flow_prop_values:
            for add, version_values in type(self)._all_flow_prop_values[self.fid].items():
                if fp == version_values:
                    self.field.referenceToFlowDataSet = get_version(ref, add)
                    break
            else:
                logging.info('\tIntermediate flow converted again due to different properties')
                new_version = max(type(self)._all_flow_prop_values[self.fid].keys()) + 1
                type(self)._all_flow_prop_values[self.fid][new_version] = fp
                send_data_to_make_dataset('01.00.'+f'{new_version:0>3}')
        else:
            type(self)._all_flow_prop_values[self.fid] = {1:fp}
            send_data_to_make_dataset('01.00.001')

    def get_not_converted(self, x):
        super().get_not_converted(x)
        if x.get('@activityLinkIdOverwrittenByChild'):
            self.not_converted.a_activityLinkIdOverwrittenByChild = x[
                '@activityLinkIdOverwrittenByChild']
        if x.get('@intermediateExchangeContextId'):
            self.not_converted.a_intermediateExchangeContextId = x['@intermediateExchangeContextId']
        if x.get('@activityLinkContextId'):
            self.not_converted.a_activityLinkContextId = x['@activityLinkContextId']

    def get_classification(self, x):
        if x.get('classification'):
            self.classification = []
            for c in ensure_list(x['classification']):
                if c['classificationSystem']['#text'] == "By-product classification" and c["classificationValue"] is not None:
                    self._by_prod_class = c["classificationValue"]["#text"]
                self.classification.append(self.class_conversion(
                    c, self.not_converted).field)
            self.classification = self.class_conversion.organize(self.classification, 'CPC')
            self.classification = list(map(lambda x: x.get_dict(), self.classification))


class ECS2ToILCD1ElementaryFlowConversion(ECS2ToILCD1FlowConversion):

    save_dir = None
    default_files = None
    elem_flow_mapping = None
    external_ref_holder = None

    statistics = 0

    def __init__(self, x, not_converted):
        logging.info(
            f'Started conversion of Elementary Flow: {x["name"]["#text"] if isinstance(x["name"], dict) else x["name"][0]["#text"]} : {x["@id"]}')
        # Set instances
        self.not_converted = not_converted.Flow()

        # Used variables
        self.fid = x["@elementaryExchangeId"]

        # Get elementary flow fields
        self.get_elementary_info(x)

        # Check if elementary flow is convertible
        if self._has_conversion:  # Data for processDataSet and copy of the elementary flow ILCD file
            super().__init__(x, initialize=False)
            type(self).statistics += 1
            self.get_flow_dict(x)
        # Conversion of variables, sources and properties (for allocation and their variables and sources)
        else:
            super().basic_initialization(x)
            self.get_properties(x, elem_not_converted_ref_field=type(self).external_ref_holder)
            if x.get('@sourceId'):
                type(self).external_ref_holder.referenceToExternalDocumentation =\
                    self.get_source(x['@sourceId'],
                                    ILCD1Helper.source_short_ref(x.get('@sourceFirstAuthor'),
                                                                 x.get('@sourceYear'),
                                                                 x.get('@pageNumbers')))

        # Get not converted
        self.get_not_converted(x)
        not_converted = self.not_converted

        # Feed variable conversion with the amounts for the formula correction
        self.amount.add_flow_data({self.id_: (self.amount.o.m, None)})

    def get_elementary_info(self, x):
        self._has_conversion = False
        n = type(self).elem_flow_mapping.get(self.fid, None)
        if n is not None:
            if n['MapType'] not in ("NO_MATCH_MAPPING", "NO MATCH"):
                self._has_conversion = True
                self.ilcd_id = n['TargetFlowUUID']
                self.name = n['TargetFlowName']

                self.conversionFactor = float(
                    n['ConversionFactor']) if n['ConversionFactor'] not in ("", "n/a") else 1.0
                self.amount = type(self).amountClass(float(x['@amount']) * self.conversionFactor,
                                                n['TargetUnit'],
                                                x.get('uncertainty'),
                                                (x.get('@variableName'),
                                                 x.get('@mathematicalRelation')),
                                                'flow')
            else:
                logging.warning(
                    "Flow not converted due to lack of elementary flow correspondence in the mapping file")
        else:
            logging.warning(
                "Flow not converted as the flow is not present on the elementary flow mapping file")

    def get_not_converted(self, x):
        super().get_not_converted(x)
        if x.get('@elementaryExchangeContextId'):
            self.not_converted.a_elementaryExchangeContextId = x['@elementaryExchangeContextId']

    def get_flow_dict(self, x):
        fp = [self.Property.get_unit_property(self.amount.dimensionality)]
        for p in self.remaining_properties:
            fp.append(p.get_dict())
        for f in fp:
            f['referenceToFlowPropertyDataSet'][0]['common:shortDescription'] = f['referenceToFlowPropertyDataSet'][0].pop(
                'c:shortDescription')

        self.__args = ['flow', (False, self.ilcd_id), self.name]
        ref = self.ref_conversion(*self.__args)

        def send_data_to_make_dataset(version, ref):
            info = {
                'type': 'elementary',
                'file': str(Path(Path(__file__).parent.parent.resolve(), self.default_files, self.ilcd_id+".xml")),
                'flowProperty': fp,
                'add_version': version
            }
            self.field.referenceToFlowDataSet = ref.make_dataset(info).field

        def get_version(ref, add):
            ref.complete_info(add,
                              file=str(Path(Path(__file__).parent.parent.resolve(), self.default_files, self.ilcd_id+".xml")))
            return ref.field

        # If there are different properties, the flow is made again
        if self.fid in type(self)._all_flow_prop_values:
            for add, version_values in type(self)._all_flow_prop_values[self.fid].items():
                if fp == version_values:
                    self.field.referenceToFlowDataSet = get_version(ref, add)
                    break
            else:
                logging.info('\tElementary flow converted again due to different properties')
                new_version = max(version_values.keys()) + 1
                type(self)._all_flow_prop_values[self.fid][new_version] = fp
                send_data_to_make_dataset(new_version, ref)
        else:
            if len(fp) == 1:
                type(self)._all_flow_prop_values[self.fid] = {0:fp}
                self.field.referenceToFlowDataSet = get_version(ref, 0)
                copy_file(self.save_dir, self.default_files, 'flows', self.ilcd_id)
            else:
                type(self)._all_flow_prop_values[self.fid] = {1:fp}
                logging.info('\tElementary Flow converted for additional properties')
                send_data_to_make_dataset(1, ref)

    def set_field(self, cl):
        if hasattr(self, 'field'):
            setattr(cl, 'exchange', self.field)


class ECS2ToILCD1ReferenceConversion:

    _options = {
        'contact': 'contacts',
        'source': 'sources',
        'flow': 'flows',
        'flow property': 'flowproperties',
        'unit group': 'unitgroups'
    }

    all_data = {
        'flow property': [],
        'unit group': [],
        'source': [],
        'contact': []
    }

    save_dir = None
    default_files = None
    uuid_conv_spec = None
    ref_field = None

    source_statistics = 0  # Due to the defaults
    contact_statistics = 0

    class AdditionalDataset(ABC):  # [!] Maybe make them DotDicts

        def __init__(self, ref, info, output_name_with_version=False):
            self.name = ref.type_
            self.uuid = ref.uuid
            self.version = ref.version
            self.output_name_with_version = output_name_with_version
            self._folder_path = Path(ref.save_dir, ref._options.get(self.name))
            self.info = info

        def check(self, field, info_name, return_func=lambda x: x):
            return {field: return_func(self.info[info_name])} if info_name in self.info else {}

        @abstractmethod
        def make_structure(self):
            self.structure = {self.name + "DataSet": {
                "@version": "1.1",
                "@xmlns": "http://lca.jrc.it/ILCD/" + self.name.capitalize(),
                "@xmlns:c": "http://lca.jrc.it/ILCD/Common",
                self.name + "Information": {
                    "dataSetInformation": {
                            "c:UUID": self.uuid
                    }
                },
                "administrativeInformation": {
                    "dataEntryBy": {
                        "c:timeStamp": str(time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())),
                        "c:referenceToDataSetFormat": ECS2ToILCD1ReferenceConversion(
                            'source',
                            (False, 'a97a0155-0234-4b87-b4ce-a45da52f2a40'),
                            'ILCD Format',
                            '03.00.000').field.get_dict()},
                    "publicationAndOwnership": {
                        "c:dataSetVersion": self.version}
                },
            }
            }
            return self

        def make_dataset(self):
            self._folder_path.mkdir(exist_ok=True)
            filename = self.uuid + ('_'+self.version if self.output_name_with_version else '') 
            with open(str(Path(self._folder_path, filename+".xml")), 'w') as f:
                f.write(xmltodict.unparse(self.structure,
                        pretty=True, newl='\n', indent="  "))

    class SourceDataSet(AdditionalDataset):

        def make_structure(self):
            super().make_structure()
            res = {
                "c:shortName": self.info['reference'],
                **self.check("classificationInformation", 'classification', lambda x: {'c:classification':
                                                                                       {"@name": "ILCD",
                                                                                        "@classes": "ILCDClassification.xml",
                                                                                        "c:class": {"@level": 0,
                                                                                                    "#text": x}
                                                                                        }
                                                                                       }),
                **self.check("sourceCitation", 'complete_reference'),
                **self.check("sourceDescriptionOrComment", 'link', lambda x: {"@xml:lang": 'en',
                                                                              "#text": x}),
                **self.check("referenceToDigitalFile", 'link', lambda x: {"@uri": x})
            }
            self.structure["sourceDataSet"]["sourceInformation"]["dataSetInformation"].update(
                res)
            return self

    class ContactDataSet(AdditionalDataset):

        def make_structure(self):
            super().make_structure()
            res = {
                "c:name": self.info["name"],
                **self.check("classificationInformation", 'classification', lambda x: {'c:classification':
                                                                                       {"@name": "ILCD",
                                                                                        "@classes": "ILCDClassification.xml",
                                                                                        "c:class": {"@level": 0,
                                                                                                    "#text": x}
                                                                                        }
                                                                                       }),
                # Active Author should be place in dump before here
                **self.check("email", 'email'),
                **self.check("contactDescriptionOrComment", 'active', lambda x: f"Active author?: {x}")
            }
            self.structure["contactDataSet"]["contactInformation"]["dataSetInformation"].update(
                res)
            return self

    class IntermediateFlowDataSet(AdditionalDataset):

        def make_structure(self):
            super().make_structure()
            dsi = {
                'name': {'baseName':  {"@xml:lang": 'en',
                                       "#text": self.info['name']}},
                **({'c:synonyms': self.info['synonyms']} if self.info['synonyms'] != [] else {}),
                **({'classificationInformation': {"c:classification": self.info['classification']}} if self.info.get('classification') else {}),
                **({'CASNumber': self.info['casNumber']} if self.info.get('casNumber') else {}),
                'c:generalComment': self.info['generalComment']
            }
            mav = {
                "LCIMethod": {'typeOfDataSet': self.info['typeOfDataSet']}
            }

            self.structure["flowDataSet"]["flowInformation"]["dataSetInformation"].update(
                dsi)
            self.structure["flowDataSet"]["flowInformation"]["quantitativeReference"] = {
                "referenceToReferenceFlowProperty": "0"}
            self.structure["flowDataSet"]["modellingAndValidation"] = mav
            self.structure["flowDataSet"]["flowProperties"] = {
                'flowProperty': self.info['flowProperty']}
            
            for n in ("flowInformation", "modellingAndValidation", "administrativeInformation", "flowProperties"):
                self.structure['flowDataSet'][n] = self.structure['flowDataSet'].pop(n)

            return self

    class ElementaryFlowDataSet(AdditionalDataset):

        def make_structure(self):
            with open(self.info['file'], 'r') as f:
                self.structure = xmltodict.parse(f.read())

            self.structure["flowDataSet"]["flowInformation"]["quantitativeReference"] = {
                "referenceToReferenceFlowProperty": "0"}

            self.version = self.produce_new_version(self.structure, self.info['add_version'])
            self.structure["flowDataSet"]["administrativeInformation"]["publicationAndOwnership"]["common:dataSetVersion"] = self.version

            _ = self.structure["flowDataSet"]["administrativeInformation"]["dataEntryBy"].pop(
                "common:timeStamp", None)
            self.structure["flowDataSet"]["administrativeInformation"]["dataEntryBy"] =\
                {"common:timeStamp": str(time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(
                )))} | self.structure["flowDataSet"]["administrativeInformation"]["dataEntryBy"]
            self.structure["flowDataSet"]["flowProperties"] = {
                'flowProperty': self.info['flowProperty']}
            
            for n in ("flowInformation", "modellingAndValidation", "administrativeInformation", "flowProperties"):
                self.structure['flowDataSet'][n] = self.structure['flowDataSet'].pop(n)

            return self
        
        @staticmethod
        def produce_new_version(struct, add):
            version = struct["flowDataSet"]["administrativeInformation"][
                "publicationAndOwnership"]["common:dataSetVersion"].split('.')
            version = [version[0], version[1], f"{int(version[2])+add:0>3}"]
            return '.'.join(version)
        
        @classmethod
        def get_version(cls, file, add):
            with open(file, 'r') as f:
                struct = xmltodict.parse(f.read())
            return cls.produce_new_version(struct, add)

    def __init__(self, type_, uuid_, shortDesc, version="01.00.000", subRef=None):
        # Set instances
        self.field = self.ref_field()

        # Error checking
        if uuid_[0] and type_ in ('flow property', 'unit group'):
            raise TypeError(
                f"\tAttempt to create a {type_} dataset with uuid={uuid_[1]} outside the default ones available for ILCD")

        # Used variables
        self.type_ = type_
        self.version = version
        self.uuid = uuid_from_uuid(
            *(uuid_[1],)+self.uuid_conv_spec) if uuid_[0] else uuid_[1]
        self.uri = '../' + self._options.get(self.type_) + '/' + self.uuid

        # Get basic fields
        self.field.a_type = type_ + ' data set'
        self.field.a_refObjectId = self.uuid
        if type_ != 'flow':
            self.field.a_version = self.version
            self.field.a_uri = self.uri 
        self.field.c_shortDescription = ILCD1Helper.text_dict_from_text(
            1, shortDesc)
        if subRef is not None:
            self.field.c_subReference = subRef

    def complete_info(self, add, file=None):
        if file:
            # Only for flows due to the making of version and uri only at the end
            self.version = self.ElementaryFlowDataSet.get_version(file, add)
            self.field.a_version = self.version # Version is done based on the existent one
            self.field.a_uri = self.uri + ('_'+self.version if add != 0 else '')
        else:
            self.version = '01.00.'+f'{add:0>3}'
            self.field.a_version = self.version # Version is done based on the existent one
            self.field.a_uri = self.uri + '_' + self.version

    def make_dataset(self, dataset_info):
        # Contacts and Sources
        if self.type_ in ('contact', 'source'):
            if self.type_ == 'contact':
                type(self).contact_statistics += 1
            else:
                type(self).source_statistics += 1
            if self.uuid not in self.all_data[self.type_]:
                type(self).all_data[self.type_].append(self.uuid)
                {"contact": self.ContactDataSet,
                 "source": self.SourceDataSet
                 }.get(self.type_)(self, dataset_info).make_structure().make_dataset()

        # Flows: flows checks are done at the class
        elif self.type_ == 'flow':
            if dataset_info['type'] == 'intermediate':
                self.IntermediateFlowDataSet(
                    self, dataset_info, output_name_with_version=True).make_structure().make_dataset()
                self.field.a_version = self.version # Version is done based on the existent one
                self.field.a_uri = self.uri + '_' + self.version
            else:
                elf = self.ElementaryFlowDataSet(
                    self, dataset_info, output_name_with_version=True).make_structure()
                self.field.a_version = elf.version # Version is done based on the existent one
                self.field.a_uri = self.uri + '_' + elf.version
                elf.make_dataset()

        # Flow Properties and Unit Groups
        else:
            if self.uuid not in self.all_data["flow property"]:
                for t, id_ in zip(('flow property', 'unit group'), (self.uuid, dataset_info['unit_id'])):
                    type(self).all_data[t].append(id_)
                    copy_file(self.save_dir, self.default_files.get(
                        t), self._options.get(t), id_)

        return self


class ECS2ToILCD1ClassificationConversion:

    class_mapping = None
    class_field = None

    statistics = 0

    def __init__(self, x, not_converted):
        # Set instances
        self.field = self.class_field()
        self.not_converted = not_converted

        # Used variables
        self.system = x["classificationSystem"]["#text"]
        self.value = x["classificationValue"]["#text"]
        self.id_ = x["@classificationId"]

        # Get basic fields
        self.field.a_name = self.system
        self.field.a_classes = '../classification_' + self.system + '.xml'

        # Get class fields
        self.get_classification()

        # Get not converted
        self.get_not_converted(x)

    def get_classification(self):
        lvl = False
        n = type(self).class_mapping.get(self.id_)
        if n is None:
            n = type(self).class_mapping.get("NULL_UUID")
            if n is not None:
                if self.value.replace(": ", ":") == n['classificationValueName'].replace(": ", ":"):
                    lvl = [('.'.join(str(n['ILCD_ClassId']).split('.')[:i]), l) for i, l in enumerate(
                        [n['Class_0'], n['Class_1'], n['Class_2'], n['Class_3'], n['Class_4']]) if l != '']
        else:
            lvl = [('.'.join(str(n['ILCD_ClassId']).split('.')[:i]), l) for i, l in enumerate(
                [n['Class_0'], n['Class_1'], n['Class_2'], n['Class_3'], n['Class_4']]) if l != '']

        if lvl:
            type(self).statistics += 1
            for i, (id_, level) in enumerate(lvl):
                n = self.field.get_class('c_class')()
                n.a_level = str(i)
                n.a_classId = id_
                n.t_ = level
                self.field.c_class = n
        else:
            logging.info("Other classification {self.id_}: {self.value}")
            n = self.field.get_class('c_class')()
            n.a_level = '0'
            n.a_classId = '0'
            n.t_ = self.value
            self.field.c_class = n

    @classmethod
    def organize(cls, classifications, priority):
        for i, c in enumerate(classifications):  # CPC and ISIC have priority
            if c.get('a_name') == priority:
                return [classifications.pop(i)] + classifications
        else:
            return classifications

    def get_not_converted(self, x):
        if x.get("@classificationContextId"):
            self.not_converted.classification = {
                'id': self.id_,
                'context': x["@classificationContextId"]
            }


class ECS2ToILCD1ReviewConversion:

    TTextAndImage = None
    ref_conversion = None

    review_holder = None
    
    statistics = 0

    def __init__(self, x, not_converted):
        # Set instances
        self.field = type(self).review_holder.get_class('review')()
        self.not_converted = not_converted

        # Used variables
        self.review_date = x['@reviewDate']
        self.version = self.get_version(x)

        # Get comments
        self.field.c_reviewDetails = ILCD1Helper.text_dict_from_text(
            -2, f"Date of Review: {self.review_date}")
        self.field.c_reviewDetails = ILCD1Helper.text_dict_from_text(
            -1, f"Review Version: {self.version}")
        if x.get('details'):
            self.field.c_reviewDetails = self.TTextAndImage(
                x['details'], "details").ILCDProcess().text
        if x.get('otherDetails'):
            self.field.c_otherReviewDetails = ILCD1Helper.text_add_index(
                x['otherDetails'], index=1)

        # Get contact reference
        self.field.c_referenceToNameOfReviewerAndInstitution = self.ref_conversion(
            "contact",
            (True, x['@reviewerId']),
            x['@reviewerName']).make_dataset({
                "name": x['@reviewerName'],
                "email": x.get('@reviewerEmail', None),
                "classification": 'Persons'
            }).field

        # Get statistics
        type(self).statistics += 1

        # Get not converted
        self.get_not_converted(x)

    def get_not_converted(self, x):
        self.not_converted.review = {
            '@reviewerId': x["@reviewerId"],
            '@reviewDate': self.review_date,
            '@version': self.version}

    @staticmethod
    def get_version(x):
        return ".".join([x['@reviewedMajorRelease'],
                         x['@reviewedMajorRevision'],
                         x['@reviewedMinorRelease'],
                         x['@reviewedMinorRevision']])

# Field mapping for conversion

class ECS2ToILCD1BasicFieldMapping(FieldMapping, ABC):

    # Conversion Defaults
    _uuid_conv_spec = (b'_Lavosier_ECS2_/', 'to_ILCD1')
    _default_language = 'en'
    
    # Converter/Factory Defaults
    _default_files = None
    _default_elem_mapping = None
    _default_class_mapping = Path("Mappings/ecs2_to_ilcd1_classes.json")

    # Configuration Defaults
    _convert_additional_fields = True
    
    # Options
    convert_properties = None
    
    def set_mappings(self, ef_map, cl_map):
        self._elem_mapping = self._dict_from_file(
            ef_map or type(self)._default_elem_mapping, 'SourceFlowUUID')
        self._class_mapping = self._dict_from_file(
            cl_map or type(self)._default_class_mapping, 'SourceFlowUUID')
        # Attributions
        self.ElementaryFlowConversion.elem_flow_mapping = self._elem_mapping
        self.ClassificationConversion.class_mapping = self._class_mapping

    def __init__(self,
                 Amount_,
                 UncertaintyConversion,
                 VariableConversion,
                 FlowConversion,
                 IntermediateFlowConversion,
                 QuantitativeObject,
                 ElementaryFlowConversion,
                 ParameterConversion,
                 ReferenceConversion,
                 ReviewConversion,
                 ClassificationConversion,
                 NotConverted):

        self.Amount = Amount_
        self.UncertaintyConversion = UncertaintyConversion
        self.VariableConversion = VariableConversion
        self.QuantitativeObject = QuantitativeObject
        self.FlowConversion = FlowConversion
        self.IntermediateFlowConversion = IntermediateFlowConversion
        self.ElementaryFlowConversion = ElementaryFlowConversion
        self.ParameterConversion = ParameterConversion
        self.ReferenceConversion = ReferenceConversion
        self.ReviewConversion = ReviewConversion
        self.ClassificationConversion = ClassificationConversion
        self.NotConverted = NotConverted()

    def start_conversion(self):
        ILCD1Helper.default_language = type(self)._default_language
        self.ReferenceConversion.uuid_conv_spec = type(self)._uuid_conv_spec
        self.ReferenceConversion.default_files = {
            k: v for k, v in type(self)._default_files.items() if k != 'elementary flow'}
        self.FlowConversion.convert_properties = type(self).convert_properties
        self.ElementaryFlowConversion.default_files = type(self)._default_files['elementary flow']
        
        self.Amount.uncertainty_conversion = self.UncertaintyConversion
        self.Amount.variable_conversion = self.VariableConversion
        self.QuantitativeObject.ref_conversion = self.ReferenceConversion
        self.FlowConversion.class_conversion = self.ClassificationConversion
        self.ReviewConversion.ref_conversion = self.ReferenceConversion
        
        self.VariableConversion.Formula.amountClass = self.Amount
        self.ParameterConversion.amountClass = self.Amount
        self.FlowConversion.amountClass = self.Amount
        self.FlowConversion.Property.amountClass = self.Amount
        self.IntermediateFlowConversion.ProductionVolume.amountClass = self.Amount
        
    def end_conversion(self):
        ECS2ToILCD1BasicFieldMapping.reset_conversion(self)
        
        self.ReferenceConversion.all_data = {
            'flow property': [],
            'unit group': [],
            'source': [],
            'contact': []
        }
        
        self.get_statistics()

        type(self).unc_stat = 0
        self.UncertaintyConversion.statistics = 0
        type(self).var_stat = 0
        self.VariableConversion.statistics = 0
        type(self).src_stat = 0
        self.ReferenceConversion.source_statistics = 0
        type(self).cnt_stat = 0
        self.ReferenceConversion.contact_statistics = 0
        type(self).inf_stat = 0
        self.IntermediateFlowConversion.statistics = 0
        type(self).elf_stat = 0
        self.ElementaryFlowConversion.statistics = 0
        type(self).prp_stat = 0
        self.FlowConversion.Property.statistics = 0
        type(self).par_stat = 0
        self.ParameterConversion.statistics = 0
        type(self).pvl_stat = 0
        self.IntermediateFlowConversion.ProductionVolume.statistics = 0
        type(self).rev_stat = 0
        self.ReviewConversion.statistics = 0
        type(self).cls_stat = 0
        self.ClassificationConversion.statistics = 0

    def reset_conversion(self):
        ILCD1Helper.number = 1000

        self.Amount._equation_counter = 1
        self.Amount._all_amounts = []
        self.Amount._flow_result_for_formula = {}
        self.VariableConversion._all_variable_names = []
        self.FlowConversion._flow_internal_id_counter = 1
        self.FlowConversion._all_flow_prop_values = {}
        self.FlowConversion._main_property = None
        self.FlowConversion._allocation_properties = {}
        self.FlowConversion._all_flows = []
        self.FlowConversion.Property._energy = None
        self.IntermediateFlowConversion.ProductionVolume._prod_v_number = -1000

    def set_file_info(self, path, save_path):
        # Attributions
        self.ReferenceConversion.save_dir = Path(save_path, 'ILCD-algorithm')
        self.ElementaryFlowConversion.save_dir = Path(save_path, 'ILCD-algorithm')

    def set_output_class_defaults(self, cl_struct):
        self.ECS2TTextAndImage.ref_field = cl_struct.dataSetInformation
        self.FlowConversion.Property.flow_property_field = cl_struct.flow_property
        self.ReferenceConversion.ref_field = cl_struct.reference
        self.ClassificationConversion.class_field = cl_struct.classification
        
        self.Amount.variable_holder = cl_struct.mathematicalRelations
        self.FlowConversion.quantity_holder = cl_struct.quantitativeReference
        self.FlowConversion.flow_holder = cl_struct.exchanges
        self.IntermediateFlowConversion.ProductionVolume.prod_v_holder = cl_struct.modellingAndValidation.dataSourcesTreatmentAndRepresentativeness
        self.ElementaryFlowConversion.external_ref_holder = cl_struct.dataSetInformation
        self.ReviewConversion.review_holder = cl_struct.modellingAndValidation.validation
        
        self._class_holder = cl_struct.dataSetInformation.classificationInformation
        self._LCI_default_fields = (cl_struct.modellingAndValidation.LCIMethodAndAllocation, 
                                    cl_struct.modellingAndValidation.dataSourcesTreatmentAndRepresentativeness)


class ECS2ToILCD1FieldMapping(ECS2ToILCD1BasicFieldMapping):

    unc_stat = 0
    var_stat = 0
    src_stat = 0
    cnt_stat = 0
    inf_stat = 0
    elf_stat = 0
    prp_stat = 0
    par_stat = 0
    pvl_stat = 0
    rev_stat = 0
    cls_stat = 0

    def get_statistics(self):
        logging.info(
            f"Intermediate Flow: {self.IntermediateFlowConversion.statistics}/{type(self).inf_stat}")
        logging.info(
            f"Elementary Flow: {self.ElementaryFlowConversion.statistics}/{type(self).elf_stat}")
        logging.info(
            f"Property: {self.FlowConversion.Property.statistics}/{type(self).prp_stat}")
        logging.info(
            f"Uncertainty: {self.UncertaintyConversion.statistics}/{type(self).unc_stat}")
        logging.info(
            f"Variable: {self.VariableConversion.statistics}/{type(self).var_stat}")
        logging.info(
            f"ProductionVolume: {self.IntermediateFlowConversion.ProductionVolume.statistics}/{type(self).pvl_stat}")
        logging.info(
            f"Parameter: {self.ParameterConversion.statistics}/{type(self).par_stat}")
        logging.info(
            f"Source: {self.ReferenceConversion.source_statistics}/{type(self).src_stat}")
        logging.info(
            f"Contact: {self.ReferenceConversion.contact_statistics}/{type(self).cnt_stat}")
        logging.info(
            f"Review: {self.ReviewConversion.statistics}/{type(self).rev_stat}")
        logging.info(
            f"Classification: {self.ClassificationConversion.statistics}/{type(self).cls_stat}")

    def set_file_info(self, *args):
        super().set_file_info(*args)

    def default(self, cl_struct):
        setattr(cl_struct.quantitativeReference,
                'a_type', "Reference flow(s)")
        setattr(cl_struct.administrativeInformation.publicationAndOwnership,
                'c_licenseType', "License fee")
        setattr(cl_struct.administrativeInformation.publicationAndOwnership,
                'c_accessRestrictions', ILCD1Helper.text_dict_from_text(1, "Licensees"))
        setattr(cl_struct.administrativeInformation.dataEntryBy, 'c_timeStamp',
                time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()))
        setattr(cl_struct.administrativeInformation.dataEntryBy, 'c_referenceToDataSetFormat', [
            self.ReferenceConversion(
                'source',
                (False, 'a97a0155-0234-4b87-b4ce-a45da52f2a40'),
                'ILCD Format',
                version="03.00.003").field,
            self.ReferenceConversion(
                'source',
                (False, 'cada7914-53c3-47ec-ac27-659b21240a99'),
                'Ecospold Format',
                version="01.00.003").field
        ])
        type(self).src_stat += 1
        setattr(cl_struct.administrativeInformation.dataEntryBy, 'c_referenceToConvertedOriginalDataSetFrom',
                self.ReferenceConversion(
                    'source',
                    (False, uuid_from_string(
                        "ecoinvent Database")),
                    'ecoinvent Database',
                    version="01.00.000").make_dataset({
                        "reference": "ecoinvent Database",
                        "classification": 'Databases'
                    }).field)

    def start_conversion(self):
        self.ECS2TTextAndImage.ref_conversion = self.ReferenceConversion
        self.ECS2TTextAndImage.src_stat_holder = type(self)
        self.ReviewConversion.TTextAndImage = self.ECS2TTextAndImage
        
        self._main_classifications = []
        super().start_conversion()

    def reset_conversion(self, end=False):
        setattr(self._class_holder, 'c_classification',
                self.ClassificationConversion.organize(self._main_classifications,
                                                       'ISIC rev.4 ecoinvent'))
        
        for n in ('deviationsFromLCIMethodPrinciple', 'deviationsFromLCIMethodApproaches'):
            if not self._LCI_default_fields[0].get(n):
                setattr(self._LCI_default_fields[0], n, ILCD1Helper.text_dict_from_text(0, 'none'))
        for n in ('deviationsFromCutOffAndCompletenessPrinciples', 'deviationsFromSelectionAndCombinationPrinciples', 'deviationsFromTreatmentAndExtrapolationPrinciples'):
            if not self._LCI_default_fields[1].get(n):
                setattr(self._LCI_default_fields[1], n, ILCD1Helper.text_dict_from_text(0, 'none'))

        # This has to be before the flow amount conversion due to the variable name
        for amount in self.Amount._all_amounts:
            amount.construct_variable()
        for flow in self.FlowConversion._all_flows:
            flow.get_allocation()
            if hasattr(flow.amount, '_var'):
                flow.field.referenceToVariable = flow.amount._var._name
                flow.field.meanAmount = 1
                flow.field.resultingAmount = flow.amount.m
            else:
                flow.field.meanAmount = flow.amount.m
                flow.field.resultingAmount = flow.amount.m

        if not end:
            super().reset_conversion()
        
    def end_conversion(self):
        self.reset_conversion(end=True)
        super().end_conversion()

    class ECS2TTextAndImage:

        ref_conversion = None
        ref_field = None
        src_stat_holder = None

        def __init__(self, x, field):
            self._x = {k: ([v] if isinstance(v, dict) else v)
                       for k, v in x.items()}
            self._field = field
            self.text, self.refs = [], []

        def ILCDProcess(self):
            var = []
            if 'variable' in self._x:
                var = [(k["@name"], k["#text"]) for k in self._x['variable']]
            for k, v in self._x.items():
                if k == "text":
                    for t in v:
                        for (ot_, rt) in var:
                            t["#text"] = t["#text"].replace("{{"+ot_+"}}", rt)
                        self.text.append(t)
                if k == "imageUrl":
                    for t in v:
                        type(self).src_stat_holder.src_stat += 1
                        info = {
                            "reference": "Image URL",
                            "link": t['#text'],
                            "classification": 'Images'
                        }
                        setattr(self.ref_field, 'referenceToExternalDocumentation', self.ref_conversion("source",
                                                                                                        (False, ECS2Helper.get_text_uuid(
                                                                                                            t["#text"])),
                                                                                                        "Image URL from "+self._field).make_dataset(info).field)

            return self
        
        def verify_and_set_text(self, cl, field):
            if self.text:
                setattr(cl, field, self.text)

    __prefix_repeating_tag = True

    def add_stat(self, name):
        setattr(type(self), name, getattr(type(self), name) + 1)

    # [!] Maybe make the ECS2 types and use them to convert to ILCD the fields like flow comments and such (all direct or indirect)
    def mapping(self):
        _keys = {
            "/ecoSpold/activityDataset/activityDescription/activity/@id": # OK 1
            lambda cl_struct, x: setattr(
                cl_struct.dataSetInformation, 'c_UUID', uuid_from_uuid(*(x,), *self._uuid_conv_spec)), 
            "/ecoSpold/activityDataset/activityDescription/activity/@activityNameId": # OK 1
            lambda cl_struct, x: (setattr(self.NotConverted, 'activityNameId', x),
                                  setattr(cl_struct.dataSetInformation, 'c_generalComment',
                                          ILCD1Helper.text_dict_from_text(-10, f'Activity Linkable Id: {x}'))), 
            "/ecoSpold/activityDataset/activityDescription/activity/@activityNameContextId":
            lambda cl_struct, x: setattr(
                self.NotConverted, "activityNameContextId", x),
            "/ecoSpold/activityDataset/activityDescription/activity/@parentActivityId":
            lambda cl_struct, x: (setattr(self.NotConverted, "parentActivityId", x),
                                  setattr(cl_struct.dataSetInformation, 'c_generalComment',
                                          ILCD1Helper.text_dict_from_text(-7, f'Parent Id: {x}'))),
            "/ecoSpold/activityDataset/activityDescription/activity/@parentActivityContextId":
            lambda cl_struct, x: setattr(
                self.NotConverted, "parentActivityContextId", x),
            "/ecoSpold/activityDataset/activityDescription/activity/@inheritanceDepth": # OK 1
            lambda cl_struct, x: (setattr(self.NotConverted, "inheritanceDepth", x),
                                  setattr(cl_struct.dataSetInformation, 'c_generalComment',
                                          ILCD1Helper.text_dict_from_text(-8, f'Inheritance: {child_type.get(x)}')) if child_type.get(x) else None),
            "/ecoSpold/activityDataset/activityDescription/activity/@type": # OK 1
            lambda cl_struct, x: setattr(
                cl_struct.modellingAndValidation.LCIMethodAndAllocation, 'typeOfDataSet', type_process.get(x)),
            "/ecoSpold/activityDataset/activityDescription/activity/@specialActivityType": # OK 1
            lambda cl_struct, x: (setattr(self.NotConverted, 'specialActivityType', x),
                                  setattr(cl_struct.dataSetInformation, 'c_generalComment',
                                          ILCD1Helper.text_dict_from_text(-9, f'Activity Subtype: {special_activity.get(x)}'))),
            "/ecoSpold/activityDataset/activityDescription/activity/@energyValues": 
            lambda cl_struct, x: (setattr(cl_struct.modellingAndValidation.LCIMethodAndAllocation, 'modellingConstants',
                                          ILCD1Helper.text_dict_from_text(1, f'Energy: {energy.get(x)}')),
                                  setattr(self.FlowConversion.Property, 'energy', energy.get(x))),
            "/ecoSpold/activityDataset/activityDescription/activity/@masterAllocationPropertyId":
            lambda cl_struct, x: (setattr(self.FlowConversion, 'main_property', x),
                                  setattr(self.NotConverted, 'masterAllocationPropertyId', x)),
            "/ecoSpold/activityDataset/activityDescription/activity/@masterAllocationPropertyIdOverwrittenByChild":
            lambda cl_struct, x: setattr(
                self.NotConverted, 'masterAllocationPropertyIdOverwrittenByChild', x),
            "/ecoSpold/activityDataset/activityDescription/activity/@masterAllocationPropertyContextId":
            lambda cl_struct, x: setattr(
                self.NotConverted, 'masterAllocationPropertyContextId', x),
            "/ecoSpold/activityDataset/activityDescription/activity/@datasetIcon":
                lambda cl_struct, x: (self.add_stat('src_stat'),
                                      setattr(cl_struct.dataSetInformation, 'referenceToExternalDocumentation',
                                              self.ReferenceConversion(
                                                  "source",
                                                  (False, ECS2Helper.get_text_uuid(
                                                      x)),
                                                  "Dataset Icon").make_dataset({
                                                      "reference": "Dataset Icon",
                                                      "link": x,
                                                      "classification": 'Images'
                                                  }).field)),
            "/ecoSpold/activityDataset/activityDescription/activity/activityName": # OK 1
            lambda cl_struct, x: setattr(
                cl_struct.dataSetInformation.name, 'baseName', ILCD1Helper.text_add_index(x)),
            "/ecoSpold/activityDataset/activityDescription/activity/synonym": # OK 1/complex with 2
            lambda cl_struct, x: setattr(cl_struct.dataSetInformation,
                                         'c_synonyms', ILCD1Helper.text_add_index(x, index=1)), # Has to be always the same
            "/ecoSpold/activityDataset/activityDescription/activity/includedActivitiesStart": # OK 1
                lambda cl_struct, x: setattr(cl_struct.technology, 'technologyDescriptionAndIncludedProcesses',
                                             ILCD1Helper.text_add_index(x, prefix="Activity Start: ")),
            "/ecoSpold/activityDataset/activityDescription/activity/includedActivitiesEnd": # OK 1
                lambda cl_struct, x: setattr(cl_struct.technology, 'technologyDescriptionAndIncludedProcesses',
                                             ILCD1Helper.text_add_index(x, prefix="Activity End: ")),
            "/ecoSpold/activityDataset/activityDescription/activity/allocationComment": # OK 1
            lambda cl_struct, x: self.ECS2TTextAndImage(x, 'allocation').ILCDProcess().verify_and_set_text(
                cl_struct.modellingAndValidation.LCIMethodAndAllocation, 'deviationsFromLCIMethodApproaches'),
            "/ecoSpold/activityDataset/activityDescription/activity/generalComment": # OK 1
            lambda cl_struct, x: self.ECS2TTextAndImage(x, 'generalComment').ILCDProcess().verify_and_set_text(
                cl_struct.dataSetInformation, 'c_generalComment'),
            "/ecoSpold/activityDataset/activityDescription/activity/tag":
            lambda cl_struct, x: (setattr(self.NotConverted, "tag", x),
                                  setattr(cl_struct.dataSetInformation, 'c_generalComment',
                                          ILCD1Helper.text_dict_from_text(-6, f'\nTag: {x["#text"]}' if type(self).__prefix_repeating_tag else x['#text'])) if x.get("#text") else None,
                                  setattr(type(self), '__prefix_repeating_tag', False)),
            "/ecoSpold/activityDataset/activityDescription/classification": # OK 1
            lambda cl_struct, x: (self.add_stat('cls_stat'),
                                  self._main_classifications.append(self.ClassificationConversion(x, self.NotConverted).field)
                                  ),
            "/ecoSpold/activityDataset/activityDescription/geography/@geographyId": 
            lambda cl_struct, x: setattr(self.NotConverted, 'geographyId', x),
            "/ecoSpold/activityDataset/activityDescription/geography/@geographyContextId":
            lambda cl_struct, x: setattr(
                self.NotConverted, 'geographyContextId', x),
            "/ecoSpold/activityDataset/activityDescription/geography/shortname": # OK 1
            lambda cl_struct, x: setattr(cl_struct.geography.locationOfOperationSupplyOrProduction,
                                         'a_location', x["#text"]),  # ECS2 can have more than one shortname in geography
            "/ecoSpold/activityDataset/activityDescription/geography/comment": # OK 1
            lambda cl_struct, x: self.ECS2TTextAndImage(x, 'geography').ILCDProcess().verify_and_set_text(
                cl_struct.geography.locationOfOperationSupplyOrProduction, 'descriptionOfRestrictions'),
            "/ecoSpold/activityDataset/activityDescription/technology/@technologyLevel": # OK 1
            lambda cl_struct, x: (setattr(self.NotConverted, 'technologyLevel', x),
                                  setattr(cl_struct.technology, 'technologyDescriptionAndIncludedProcesses',
                                          ILCD1Helper.text_dict_from_text(-1, f"Technology Level: {tech.get(x)}"))),
            "/ecoSpold/activityDataset/activityDescription/technology/comment": # OK 1
            lambda cl_struct, x: self.ECS2TTextAndImage(x, 'technology').ILCDProcess().verify_and_set_text(
                cl_struct.technology, 'technologyDescriptionAndIncludedProcesses'),
            "/ecoSpold/activityDataset/activityDescription/timePeriod/@startDate": # OK 1
            lambda cl_struct, x: setattr(cl_struct.time, 'c_referenceYear', str(
                time.strptime(x, '%Y-%m-%d').tm_year)),
            "/ecoSpold/activityDataset/activityDescription/timePeriod/@endDate": # OK 1
            lambda cl_struct, x: setattr(
                cl_struct.time, 'c_dataSetValidUntil', ILCD1Helper.time_get_end(x)),
            "/ecoSpold/activityDataset/activityDescription/timePeriod/@isDataValidForEntirePeriod": # OK 1
            lambda cl_struct, x: (setattr(self.NotConverted, "isDataValidForEntirePeriod", x),
                                  setattr(cl_struct.time, 'c_timeRepresentativenessDescription',
                                          ILCD1Helper.text_dict_from_text(-1, f"Validity: {time_period.get(x)}"))),
            "/ecoSpold/activityDataset/activityDescription/timePeriod/comment": # OK 1
            lambda cl_struct, x: self.ECS2TTextAndImage(x, 'technology').ILCDProcess().verify_and_set_text(
                cl_struct.time, 'c_timeRepresentativenessDescription'),
            "/ecoSpold/activityDataset/activityDescription/macroEconomicScenario/@macroEconomicScenarioId":\
            lambda cl_struct, x: setattr(
                self.NotConverted, 'macroEconomicScenarioId', x),
            "/ecoSpold/activityDataset/activityDescription/macroEconomicScenario/@macroEconomicScenarioContextId":\
            lambda cl_struct, x: setattr(
                self.NotConverted, 'macroEconomicScenarioContextId', x),
            "/ecoSpold/activityDataset/activityDescription/macroEconomicScenario/name": # OK 1
            lambda cl_struct, x: (setattr(self.NotConverted, 'macroEconomicScenario_name', x['#text']),
                                  setattr(cl_struct.dataSetInformation, 'c_generalComment',
                                          ILCD1Helper.text_add_index(x, prefix='Macroeconomic Scenario: ', index=-5))),
            "/ecoSpold/activityDataset/activityDescription/macroEconomicScenario/comment":\
            lambda cl_struct, x: (setattr(self.NotConverted, 'macroEconomicScenario_comment', x),
                                  setattr(cl_struct.dataSetInformation, 'c_generalComment',
                                          ILCD1Helper.text_add_index(x, prefix='Macroeconomic Scenario Comment: ', index=-4))),
            "/ecoSpold/activityDataset/flowData/intermediateExchange":\
            lambda cl_struct, x: (self.add_stat('inf_stat'), setattr(cl_struct.exchanges, 'exchange', self.IntermediateFlowConversion(x,
                                                                                                                                      self.NotConverted).field),
                                  self.add_stat('var_stat') if x.get(
                                      '@variableName') or x.get('@mathematicalRelation') else None,
                                  self.add_stat('pvl_stat') if x.get(
                                      '@productionVolumeAmount') else None,
                                  self.add_stat('var_stat') if x.get('@productionVolumeVariableName') or x.get('@productionVolumeMathematicalRelation') else None),
            "/ecoSpold/activityDataset/flowData/intermediateExchange/@sourceId":\
            lambda cl_struct, x: self.add_stat('src_stat'),
            "/ecoSpold/activityDataset/flowData/intermediateExchange/@productionVolumeSourceId":\
            lambda cl_struct, x: self.add_stat('src_stat'),
            "/ecoSpold/activityDataset/flowData/intermediateExchange/property/@sourceId":\
            lambda cl_struct, x: self.add_stat('src_stat'),
            "/ecoSpold/activityDataset/flowData/intermediateExchange/uncertainty":\
            lambda cl_struct, x: self.add_stat('unc_stat'),
            "/ecoSpold/activityDataset/flowData/intermediateExchange/productionVolumeUncertainty":\
            lambda cl_struct, x: self.add_stat('unc_stat'),
            "/ecoSpold/activityDataset/flowData/intermediateExchange/property/uncertainty":\
            lambda cl_struct, x: self.add_stat('unc_stat'),
            "/ecoSpold/activityDataset/flowData/intermediateExchange/classification":\
            lambda cl_struct, x: self.add_stat('cls_stat'),
            "/ecoSpold/activityDataset/flowData/intermediateExchange/property":\
            lambda cl_struct, x: (self.add_stat('prp_stat'), self.add_stat('var_stat') if x.get(
                '@variableName') or x.get('@mathematicalRelation') else None),
            "/ecoSpold/activityDataset/flowData/elementaryExchange":\
            lambda cl_struct, x: (self.add_stat('elf_stat'), self.ElementaryFlowConversion(x, self.NotConverted).set_field(cl_struct.exchanges),
                                  self.add_stat('var_stat') if x.get('@variableName') or x.get('@mathematicalRelation') else None),
            "/ecoSpold/activityDataset/flowData/elementaryExchange/@sourceId":\
            lambda cl_struct, x: self.add_stat('src_stat'),
            "/ecoSpold/activityDataset/flowData/elementaryExchange/property/@sourceId":\
            lambda cl_struct, x: self.add_stat('src_stat'),
            "/ecoSpold/activityDataset/flowData/elementaryExchange/uncertainty":\
            lambda cl_struct, x: self.add_stat('unc_stat'),
            "/ecoSpold/activityDataset/flowData/elementaryExchange/property/uncertainty":\
            lambda cl_struct, x: self.add_stat('unc_stat'),
            "/ecoSpold/activityDataset/flowData/elementaryExchange/property":\
            lambda cl_struct, x: (self.add_stat('prp_stat'), self.add_stat('var_stat') if x.get(
                '@variableName') or x.get('@mathematicalRelation') else None),
            "/ecoSpold/activityDataset/flowData/parameter": lambda cl_struct, x:
                (self.add_stat('par_stat'), self.ParameterConversion(x, self.NotConverted), 
                 self.add_stat('var_stat') if x.get('@variableName') or x.get('@mathematicalRelation') else None),
            "/ecoSpold/activityDataset/flowData/parameter/uncertainty":\
            lambda cl_struct, x: self.add_stat('unc_stat'),
            "/ecoSpold/activityDataset/modellingAndValidation/representativeness/@percent":\
            lambda cl_struct, x: setattr(
                cl_struct.modellingAndValidation.dataSourcesTreatmentAndRepresentativeness, "percentageSupplyOrProductionCovered", x),
            "/ecoSpold/activityDataset/modellingAndValidation/representativeness/@systemModelId":\
            lambda cl_struct, x: setattr(
                self.NotConverted, "systemModelId", x),
            "/ecoSpold/activityDataset/modellingAndValidation/representativeness/@systemModelContextId":\
            lambda cl_struct, x: setattr(
                self.NotConverted, "systemModelContextId", x),
            "/ecoSpold/activityDataset/modellingAndValidation/representativeness/systemModelName":\
            lambda cl_struct, x: (setattr(cl_struct.modellingAndValidation.LCIMethodAndAllocation, "LCIMethodPrinciple", system_model.get(x["#text"])),
                                  setattr(cl_struct.modellingAndValidation.LCIMethodAndAllocation, "deviationsFromLCIMethodPrinciple",
                                          ILCD1Helper.text_add_index(x, prefix='Original ecoinvent System Model: ', index=1)),
                                  setattr(cl_struct.modellingAndValidation.LCIMethodAndAllocation, "LCIMethodApproaches", system_model_2.get(x["#text"]))),  # Remove Data
            "/ecoSpold/activityDataset/modellingAndValidation/representativeness/samplingProcedure":\
            lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.dataSourcesTreatmentAndRepresentativeness,
                                         "samplingProcedure", ILCD1Helper.text_add_index(x, index=1)),
            "/ecoSpold/activityDataset/modellingAndValidation/representativeness/extrapolations":\
            lambda cl_struct, x: setattr(cl_struct.modellingAndValidation.dataSourcesTreatmentAndRepresentativeness,
                                         "dataTreatmentAndExtrapolationsPrinciples", ILCD1Helper.text_add_index(x, index=1)),
            "/ecoSpold/activityDataset/modellingAndValidation/review":\
                lambda cl_struct, x: (self.add_stat('rev_stat'), self.add_stat('cnt_stat'), setattr(cl_struct.modellingAndValidation.validation, 'review',
                                                                                                    self.ReviewConversion(x,
                                                                                                                          self.NotConverted).field),
                                      setattr(cl_struct.administrativeInformation.publicationAndOwnership, 'c_dateOfLastRevision', x['@reviewDate'])),
            "/ecoSpold/activityDataset/administrativeInformation/dataEntryBy":\
            lambda cl_struct, x: (self.add_stat('cnt_stat'), setattr(cl_struct.administrativeInformation.dataEntryBy, "c_referenceToPersonOrEntityEnteringTheData",
                                                                     self.ReferenceConversion(
                                                                         "contact",
                                                                         (True,
                                                                          x['@personId']),
                                                                         x['@personName']).make_dataset({
                                                                             "name": x['@personName'],
                                                                             "email": x.get('@personEmail', None),
                                                                             "active": x.get("@isActiveAuthor", None),
                                                                             "classification": 'Persons'
                                                                         }).field),
                                  setattr(self.NotConverted, "dataEntryBy_personContextId",
                                          x["@personId"]+"/"+x["@personContextId"]) if x.get("@personContextId") else None),
            "/ecoSpold/activityDataset/administrativeInformation/dataGeneratorAndPublication":\
            lambda cl_struct, x: (self.add_stat('cnt_stat'), setattr(cl_struct.administrativeInformation.dataGenerator, "c_referenceToPersonOrEntityGeneratingTheDataSet",
                                                                     self.ReferenceConversion(
                                                                         "contact",
                                                                         (True,
                                                                          x['@personId']),
                                                                         x['@personName']).make_dataset({
                                                                             "name": x['@personName'],
                                                                             "email": x.get('@personEmail', None),
                                                                             "classification": 'Persons'
                                                                         }).field),
                                  setattr(self.NotConverted, "dataGeneratorAndPublication_personContextId",
                                          x["@personId"]+"/"+x["@personContextId"]) if x.get("@personContextId") else None,
                                  self.add_stat('src_stat') if x.get(
                                      "@publishedSourceId") else None,
                                  setattr(cl_struct.administrativeInformation.publicationAndOwnership, "c_referenceToUnchangedRepublication",
                                          self.ReferenceConversion(
                                              "source",
                                              (True,
                                               x['@publishedSourceId']),
                                              ILCD1Helper.source_short_ref(x.get('@publishedSourceFirstAuthor'),
                                                                           x.get(
                                                  '@publishedSourceYear'),
                                                  x.get('pageNumbers'))).make_dataset({
                                                      "reference": ILCD1Helper.source_short_ref(x.get('@publishedSourceFirstAuthor'),
                                                                                                x.get(
                                                          '@publishedSourceYear'),
                                                          x.get('pageNumbers')),
                                                      "complete_reference": ILCD1Helper.source_short_ref(x.get('@publishedSourceFirstAuthor'),
                                                                                                         x.get(
                                                          '@publishedSourceYear'),
                                                          x.get('pageNumbers')),
                                                      "classification": 'Publications and communications'
                                                  }).field) if x.get("@publishedSourceId") else None,
                                  setattr(self.NotConverted, "publishedSourceIdOverwrittenByChild",
                                          x["@personId"]+"/"+x["@publishedSourceIdOverwrittenByChild"]) if x.get("@publishedSourceIdOverwrittenByChild") and x.get("@personId") else None,
                                  setattr(self.NotConverted, "publishedSourceContextId",
                                          x["@personId"]+"/"+x["@publishedSourceContextId"]) if x.get("@publishedSourceContextId") else None,
                                  self.add_stat('cnt_stat') if x.get(
                                      "@companyId") else None,
                                  setattr(cl_struct.administrativeInformation.publicationAndOwnership, "c_referenceToEntitiesWithExclusiveAccess",
                                          self.ReferenceConversion(
                                              "contact",
                                              (True,
                                               x['@companyId']),
                                              x.get(
                                                  "@companyCode", "Company")
                                          ).make_dataset({
                                              "name": x.get("@companyCode", "Company"),
                                              "classification": 'Organisations'
                                          }).field) if x.get("@companyId") else None,
                                  setattr(cl_struct.administrativeInformation.publicationAndOwnership, "c_accessRestrictions",
                                          ILCD1Helper.text_dict_from_text(2, x["@companyCode"])) if x.get("@companyCode") else None,
                                  setattr(self.NotConverted, "companyIdOverwrittenByChild",
                                          x["@companyId"]+"/"+x["@companyIdOverwrittenByChild"]) if x.get("@companyIdOverwrittenByChild") and x.get("@companyId") else None,
                                  setattr(self.NotConverted, "companyContextId",
                                          x["@companyId"]+"/"+x["@companyContextId"]) if x.get("@companyContextId") else None),
            "/ecoSpold/activityDataset/administrativeInformation/dataGeneratorAndPublication/@dataPublishedIn":\
            lambda cl_struct, x: setattr(cl_struct.administrativeInformation.publicationAndOwnership,
                                         "c_workflowAndPublicationStatus", status_publication.get(x)),
            "/ecoSpold/activityDataset/administrativeInformation/dataGeneratorAndPublication/@isCopyrightProtected":\
            lambda cl_struct, x: setattr(
                cl_struct.administrativeInformation.publicationAndOwnership, "c_copyright", x),
            "/ecoSpold/activityDataset/administrativeInformation/dataGeneratorAndPublication/@accessRestrictedTo":\
            lambda cl_struct, x: (setattr(cl_struct.administrativeInformation.publicationAndOwnership, "c_licenseType", restrictions.get(x)),
                                  setattr(cl_struct.administrativeInformation.publicationAndOwnership, 'c_accessRestrictions', ILCD1Helper.text_dict_from_text(1, access.get(x)))),
            "/ecoSpold/activityDataset/administrativeInformation/fileAttributes":\
            lambda cl_struct, x: (setattr(cl_struct.administrativeInformation.publicationAndOwnership, "c_dataSetVersion",
                                          "0"+x.get("@majorRelease", '0')+".0"+x.get("@minorRevision", '0')+".000"),
                                  setattr(self.NotConverted, "version", x.get("@majorRelease",'-')+"|" + \
                                          x.get("@minorRelease",'-')+"|"+x.get("@majorRevision",'-')+"|"+x.get("@minorRevision",'-')),
                                  setattr(self.NotConverted, "fileInfo",
                                          f"{[n for n in x.get('contextName',[])]}"+"|" +\
                                          x.get("@internalSchemaVersion", "-")+"|" +\
                                          x.get("@defaultLanguage", "en")+"|" +\
                                          x.get("@creationTimestamp", "-")+"|" +\
                                          x.get('@lastEditTimestamp', "-")+"|" +\
                                          x.get("@fileGenerator", "-")+"|" +\
                                          x.get('@fileTimestamp', "-")+"|" +\
                                          x.get('@contextId', "-"))),  # fileGenerator/fileTimestamp/context is actualy mandatory
            "/ecoSpold/activityDataset/administrativeInformation/fileAttributes/requiredContext":\
            lambda cl_struct, x: setattr(self.NotConverted, "requiredContext",
                                         f"{[n for n in x['requiredContextName']]}"+"|" +\
                                         x["@majorRelease"]+"|" +\
                                         x["@minorRelease"]+"|" +\
                                         x.get("@majorRevision", "-")+"|" +\
                                         x.get('@minorRevision', "-")+"|" +\
                                         x["@requiredContextId"]+"|" +\
                                         x.get('@requiredContextFileLocation'))
        }

        _keys |= {k.replace(
            "activityDataset", "childActivityDataset"): v for k, v in _keys.items()}
        return _keys

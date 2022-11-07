#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  7 05:29:17 2022

@author: jotape42p
"""

import re
import datetime
from collections import defaultdict
from abc import ABC
from .main import DotDict, Validator
from .utils import text_to_list

### ENUMERATIONS 

Languages = (
    'aa','ab','ae','af','ak','am','an','ar','as','av','ay','az','ba','be','bg',
    'bh','bi','bm','bn','bo','br','bs','ca','ce','ch','co','cr','cs','cu','cv',
    'cy','da','de','dv','dz','ee','el','en','eo','es','et','eu','fa','ff','fi',
    'fj','fo','fr','fy','ga','gd','gl','gn','gu','gv','ha','he','hi','ho','hr',
    'ht','hu','hy','hz','ia','id','ie','ig','ii','ik','io','is','it','iu','ja',
    'jv','ka','kg','ki','kj','kk','kl','km','kn','ko','kr','ks','ku','kv','kw',
    'ky','la','lb','lg','li','ln','lo','lt','lu','lv','mg','mh','mi','mk','ml',
    'mn','mo','mr','ms','mt','my','na','nb','nd','ne','ng','nl','nn','no','nr',
    'nv','ny','oc','oj','om','or','os','pa','pi','pl','ps','pt','qu','rm','rn',
    'ro','ru','rw','sa','sc','sd','se','sg','si','sk','sl','sm','sn','so','sq',
    'sr','ss','st','su','sv','sw','ta','te','tg','th','ti','tk','tl','tn','to',
    'tr','ts','tt','tw','ty','ug','uk','ur','uz','ve','vi','vo','wa','wo','xh',
    'yi','yo','za','zh','zu'
    )

GlobalReferenceTypeValues = (
    "source data set",
    "process data set",
    "flow data set",
    "flow property data set",
    "unit group data set",
    "contact data set",
    "LCIA method data set",
    "other external file"
    )

TypeOfQuantitativeReferenceValues = (
    "Reference flow(s)",
    "Functional unit",
    "Other parameter",
    "Production period"
    )

UncertaintyDistributionTypeValues = (
    "undefined",
    "log-normal",
    "normal",
    "triangular",
    "uniform"
    )

TypeOfProcessValues = (
    "Unit process, single operation",
    "Unit process, black box",
    "LCI result",
    "Partly terminated system",
    "Avoided product system"
    )

LCIMethodPrincipleValues = (
    "Attributional",
    "Consequential",
    "Consequential with attributional components",
    "Not applicable",
    "Other"
    )

LCIMethodApproachesValues = (
    "Allocation - market value",
    "Allocation - gross calorific value",
    "Allocation - net calorific value",
    "Allocation - exergetic content",
    "Allocation - element content",
    "Allocation - mass",
    "Allocation - volume",
    "Allocation - ability to bear",
    "Allocation - marginal causality",
    "Allocation - physical causality",
    "Allocation - 100% to main function",
    "Allocation - other explicit assignment",
    "Allocation - equal distribution",
    "Substitution - BAT",
    "Substitution - average, market price correction",
    "Substitution - average, technical properties correction",
    "Allocation - recycled content",
    "Substitution - recycling potential",
    "Substitution - average, no correction",
    "Substitution - specific",
    "Consequential effects - other",
    "Not applicable",
    "Other"
    )

CompletenessValues = (
    "All relevant flows quantified",
    "Relevant flows missing",
    "Topic not relevant",
    "No statement"
    )

CompletenessTypeValues = (
    "Climate change",
    "Ozone depletion",
    "Summer smog",
    "Eutrophication",
    "Acidification",
    "Human toxicity",
    "Freshwater ecotoxicity",
    "Seawater eco-toxicity",
    "Terrestric eco-toxicity",
    "Radioactivity",
    "Land use",
    "Non-renewable material resource depletion",
    "Renewable material resource consumption",
    "Non-renewable primary energy depletion",
    "Renewable primary energy consumption",
    "Particulate matter/respiratory inorganics",
    "Species depletion",
    "Noise"
    )

ScopeOfReviewValues = ( # Common Validation
    "Raw data",
    "Unit process(es), single operation",
    "Unit process(es), black box",
    "LCI results or Partly terminated system",
    "LCIA results",
    "Documentation",
    "Life cycle inventory methods",
    "LCIA results calculation",
    "Goal and scope definition"
    )

MethodOfReviewValues = ( # Common Validation
    "Validation of data sources",
    "Sample tests on calculations",
    "Energy balance",
    "Element balance",
    "Cross-check with other source",
    "Cross-check with other data set",
    "Expert judgement",
    "Mass balance",
    "Compliance with legal limits",
    "Compliance with ISO 14040 to 14044",
    "Documentation",
    "Evidence collection by means of plant visits and/or interviews"
    )

DataQualityIndicatorValues = (
    "Technological representativeness",
    "Time representativeness",
    "Geographical representativeness",
    "Completeness",
    "Precision",
    "Methodological appropriateness and consistency",
    "Overall quality"
    )

QualityValues = (
    "Very good",
    "Good",
    "Fair",
    "Poor",
    "Very poor",
    "Not evaluated / unknown",
    "Not applicable"
    )

TypeOfReviewValues = (
    "Dependent internal review",
    "Independent internal review",
    "Independent external review",
    "Accredited third party review",
    "Independent review panel",
    "Not reviewed"
    )

ComplianceValues = (
    "Fully compliant",
    "Not compliant",
    "Not defined"
    )

WorkflowAndPublicationStatusValues = (
    "Working draft",
    "Final draft for internal review",
    "Final draft for external review",
    "Data set finalised; unpublished",
    "Under revision",
    "Withdrawn",
    "Data set finalised; subsystems published",
    "Data set finalised; entirely published"
    )

LicenseTypeValues = (
    "Free of charge for all users and uses",
    "Free of charge for some user types or use types",
    "Free of charge for members only",
    "License fee",
    "Other"
    )

ExchangeFunctionTypeValues = (
    "General reminder flow",
    "Allocation reminder flow",
    "System expansion reminder flow"
    )

ExchangeDirectionValues = (
    "Input",
    "Output"
    )

DataSourceTypeValues = (
    "Primary",
    "> 90% primary",
    "Mixed primary / secondary",
    "Secondary"
    )

DataDerivationTypeStatusValues = (
    "Measured",
    "Calculated",
    "Estimated",
    "Unknown derivation"
    )

### VALIDATORS

class INT(Validator, ABC):
    def _validate(self, x):
        try:
            x = int(x)
        except:
            raise TypeError(f'{self.__class__.__name__}: Expected an integer, received {x} of type {type(x)}')
        if x < 0:
            raise ValueError(f'{self.__class__.__name__}: Entry {x} is not valid. Must be positive')
        return x

class Real(Validator):
    def _validate(self, x):
        try:
            x = float(x)
        except:
            raise TypeError(f'{self.__class__.__name__}: Expected a float, received {x} of type {type(x)}')
        return x

class Perc(Real): # [!] Discuss again as it has totalDigits = 5 and fractionDigits = 3
    pass

class Int1(INT):
    def _validate(self, x):
        x = super()._validate(x)
        if len(str(x)) != 1:
            raise ValueError(f'Int1: Entry {x} is not valid. Must have only one digit')
        return x

class Int6(INT):
    def _validate(self, x):
        x = super()._validate(x)
        if len(str(x)) > 6:
            raise ValueError(f'Int6: Entry {x} is not valid. Must have less than six digits')
        return x
    def add(self, o):
        if hasattr(self, '_x'):
            self._x = (self._x if isinstance(self._x, list) else [self._x]) + [self._validate(o)]
        else:
            self._x = self._validate(o)
        return self

class Year(INT):
    def _validate(self, x):
        x = super()._validate(x)
        if len(str(x)) != 4:
            raise ValueError(f'Year: Entry {x} is not valid. Must have four digits')
        return x

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

class Version(Pattern):
    def __init__(self):
        self._pattern = r'\d{2}\.\d{2}(\.\d{3})?'
        
class GIS(Pattern):
    def __init__(self):
        self._pattern = r'\s*([\-+]?(([0-8]?\d)(\.\d*)?)|(90(\.0{0,2})?))\s*;\s*(([\-+]?(((1[0-7]\d)(\.\d*)?)|([0-9]\d(\.\d*)?)|(\d(\.\d*)?)|(180(\.[0]*)?))))\s*'
        
class DateTime(Validator):
    def _validate(self, x):
        if not isinstance(x, str):
            raise TypeError(f'{self.__class__.__name__}: Expected a string, received {x} of type {type(x)}')
        try:
            x = datetime.datetime.fromisoformat(x.replace('Z', '+00:00'))
        except:
            raise ValueError(f'{self.__class__.__name__}: Entry {x} is not valid. Must be an ISO 8601 datetime')
        return x
    def end(self):
        return self._x.isoformat()

class ReviewDateTime(DateTime):
    def add(self, o):
        if not hasattr(self, '_x'):
            self._x = self._validate(o)
        else:
            o = self._validate(o)
            if o.replace(tzinfo=None) > self._x.replace(tzinfo=None):
                self._x = o
        return self

class BOOL(Validator): # Anything can be a bool, so it is verified through a handful of cases
    VALID = ('true','false','True','False',1,0,'1','0',True,False)
    def _validate(self, x):
        if x not in self.VALID:
            raise ValueError(f'BOOL: {x} is not valid. Must be one of {", ".join([str(x) for x in self.VALID])}')
        return bool(x) if not isinstance(x, str) else x in ('1', 'true', 'True')

class STR(Validator):
    def _validate(self, x):
        if not isinstance(x, str):
            raise TypeError(f'{self.__class__.__name__}: Expected a string, received {x} of type {type(x)}')
        return x

class FT(STR):
    ignore_limit = False
    def add(self, o, sep='\n'):
        if not hasattr(self, '_x'):
            self._x = self._validate(o)
        else:
            self._x += sep+self._validate(o)
        return self
    
class String(FT):
    limit = 500
    def _end_validate(self):
        if not (1 <= len(self._x) <= self.limit) and not self.ignore_limit:
            raise ValueError(f'String: Entry {self._x} with length {len(self._x)} is not valid. Must have length between 1 and 500')

class NullableString(FT):
    limit = 500
    def _end_validate(self):
        if len(self._x) >= self.limit and not self.ignore_limit:
            raise ValueError(f'NullableString: Entry {self._x} with length {len(self._x)} is not valid. Must have length lower than 500')

class ST(FT):
    limit = 1000
    def _end_validate(self):
        if len(self._x) >= self.limit and not self.ignore_limit:
            raise ValueError(f'ST: Entry {self._x} with length {len(self._x)} is not valid. Must have length lower than 1000')
    
class MatV(FT):
    limit = 50
    def _end_validate(self):
        if len(self._x) >= self.limit and not self.ignore_limit:
            raise ValueError(f'MatV: Entry {self._x} with length {len(self._x)} is not valid. Must have length lower than 50')
           
def ILCD1_ignore_limits(value):
    FT.ignore_limit = value
           
class MultiLang(Validator, ABC):
    
    _text = None
    
    def _validate(self, x):
        if not isinstance(x, dict):
            raise TypeError(f'{self.__class__.__name__}: Expected a dict, recieved {x} of type {type(x)}')
        for n in ('@index', '@lang', '#text'):
            if n not in x:
                raise KeyError(f'{self.__class__.__name__}: Key {n} not found in {x}')
        try:
            x['@index'] = int(x['@index'])
        except:
            raise ValueError(f'{self.__class__.__name__}: Expected an integer, received {x["@index"]} of type {type(x["@index"])}')
        if x['@lang'] not in Languages:
            raise ValueError(f'{self.__class__.__name__}: {x["@lang"]} is not a valid language')
        x['#text'] = self._text().add(x['#text'])
        return x
    
    def _retrieve(self, x):
        n = []
        if not isinstance(x, list):
            x = [x]
        for l in x:
            n.append(self._validate(l))
        return n
    
    def add(self, o):
        def _add():
            for n in self._retrieve(o):
                for m in self._x:
                    if n['@index'] == m['@index'] and n['@lang'] == m['@lang']:
                        if not m['#text']._x or m['#text']._x.isspace() or not n['#text']._x or n['#text']._x.isspace(): sep=''
                        else: sep='; '
                        self._x[self._x.index(m)]['#text'].add(n['#text']._x, sep=sep) # Can't call 'end' here yet
                        break
                else:
                    self._x.append(n)
        self._x = self._x if hasattr(self, '_x') else []
        _add()
        return self
    
    def _end_validate(self, x): # _end_validate doesn't modify self._x, otherwise the end process cannot be done again
        n = []
        for s in x:
            t = s.pop('#text')
            if not type(t) is FT and len(t._x) > t.limit:
                n.extend([s | {"#text": self._text().add(n).end()} for n in text_to_list(t._x, t.limit)])
            else:
                n.append(s | {"#text": t.end()})
        return n
    
    def end(self):
        x = sorted(self._x, key=lambda x:x['@index'])
        d = defaultdict(str)
        for s in x:
            d[s['@lang']] += '\n'+s['#text']._x if d.get(s['@lang']) else s['#text']._x # Can't call 'end' here yet
        x = [{"@xml:lang": k, "#text": self._text().add(v)} for k, v in d.items()]
        x = self._end_validate(x)
        return x

class StringMultiLang(MultiLang):
    _text = String

class FTMultiLang(MultiLang):
    _text = FT

class STMultiLang(MultiLang):
    _text = ST

def return_enum(enum, list_=False): # licenseType can overwrite its value with double 'add' calls
    class Enumeration(Validator):
        def __init__(self):
            self._enum = enum
        def _validate(self, x):
            if isinstance(x, (list, tuple)) and not list_:
                raise TypeError(f'Enumeration: Expected a str, received {x} of type {type(x)}')
            s = x if isinstance(x, (list, tuple)) else [x]
            for x in s:
                if x not in self._enum:
                    raise ValueError(f'Enumeration: {x} is not valid. Must be one of: {", ".join(self._enum)}')
            return x if not list_ else s
        def add(self, o):
            if list_:
                self._x = [] if not hasattr(self, '_x') else self._x
                self._x += [n for n in self._validate(o) if n not in self._x]
            else:
                self._x = self._validate(o)
            return self
    return Enumeration

### GENERAL STRUCTURES

class ILCD1Reference(DotDict):

    VALID = {
        'a_type': {'type': return_enum(GlobalReferenceTypeValues), 'mandatory': True, 'order': 0, 'unique': True},
        'a_refObjectId': {'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'a_version': {'type': Version, 'mandatory': False, 'order': 0, 'unique': True},
        'a_uri': {'type': STR, 'mandatory': False, 'order': 0, 'unique': True}, # anyURI
        'c_subReference': {'type': String, 'mandatory': False, 'order': 1},
        'c_shortDescription': {'type': STMultiLang, 'mandatory': False, 'order': 2}
    }

class ILCD1Classification(DotDict):

    class __Class(DotDict):
        
        VALID = {
            'a_level': {'type': Int1, 'mandatory': True, 'order': 0, 'unique': True},
            'a_classId': {'type': STR, 'mandatory': True, 'order': 0, 'unique': True},
            't_': {'type': String, 'mandatory': True, 'order': 0}  # It has a text
        }

    VALID = {
        'a_name': {'type': STR, 'mandatory': True, 'order': 0, 'unique': True},
        'a_classes': {'type': STR, 'mandatory': True, 'order': 0, 'unique': True}, # anyURI
        'c_class': {'type': __Class, 'mandatory': True, 'order': 1}
    }

class ILCD1FlowProperty(DotDict): # [!] FlowDataSets can have a location, how to transcrible it from ECS2?

    VALID = {
        'a_dataSetInternalID': {'type': Int6, 'mandatory': True, 'order': 0, 'unique': True},
        'referenceToFlowPropertyDataSet': {'type': ILCD1Reference, 'mandatory': True, 'order': 1, 'unique': True},
        'meanValue': {'type': Real, 'mandatory': True, 'order': 2, 'unique': True},
        'minimumValue': {'type': Real, 'mandatory': False, 'order': 3, 'unique': True},
        'maximumValue': {'type': Real, 'mandatory': False, 'order': 4, 'unique': True},
        'uncertaintyDistributionType': {'type': return_enum(UncertaintyDistributionTypeValues), 'mandatory': False, 'order': 5, 'unique': True},
        'relativeStandardDeviation95In': {'type': Perc, 'mandatory': False, 'order': 6, 'unique': True},
        'dataDerivationTypeStatus': {'type': return_enum(DataDerivationTypeStatusValues), 'mandatory': False, 'order': 7, 'unique': True},
        'generalComment': {'type': StringMultiLang, 'mandatory': False, 'order': 16}
    }

### MAIN STRUCTURE

class ILCD1Structure:
    
    # [!] LCIAResults are not considered here
    # [!] The processDataSet @version will have to be specified in future
    
    class DataSetInformation(DotDict):

        class __Name(DotDict):
            
            VALID = {
                'baseName': {'type': StringMultiLang, 'mandatory': True, 'order': 1},
                'treatmentStandardsRoutes': {'type': StringMultiLang, 'mandatory': False, 'order': 2},
                'mixAndLocationTypes': {'type': StringMultiLang, 'mandatory': False, 'order': 3},
                'functionalUnitFlowProperties': {'type': StringMultiLang, 'mandatory': False, 'order': 4}
            }

        class __ComplementingProcesses(DotDict):
            
            VALID = {
                'referenceToComplementingProcess': {'type': ILCD1Reference, 'mandatory': True, 'order': 1}
            }

        class __ClassificationInformation(DotDict):
            
            VALID = {
                'c_classification': {'type': ILCD1Classification, 'mandatory': False, 'order': 1}
            }

        VALID = {
            'c_UUID': {'type': UUID, 'mandatory': True, 'order': 1, 'unique': True},
            'name': {'type': __Name, 'mandatory': False, 'order': 2, 'unique': True},
            'identifierOfSubDataSet': {'type': String, 'mandatory': False, 'order': 3, 'unique': True},
            'c_synonyms': {'type': FTMultiLang, 'mandatory': False, 'order': 4},
            'complementingProcesses': {'type': __ComplementingProcesses, 'mandatory': False, 'order': 5, 'unique': True},
            'classificationInformation': {'type': __ClassificationInformation, 'mandatory': False, 'order': 6, 'unique': True},
            'c_generalComment': {'type': FTMultiLang, 'mandatory': False, 'order': 7},
            'referenceToExternalDocumentation': {'type': ILCD1Reference, 'mandatory': False, 'order': 8}
        }
        
    class QuantitativeReference(DotDict): # Optional

        VALID = {
            'a_type': {'type': return_enum(TypeOfQuantitativeReferenceValues), 'mandatory': True, 'order': 0, 'unique': True},
            'referenceToReferenceFlow': {'type': Int6, 'mandatory': False, 'order': 1},
            'functionalUnitOrOther': {'type': StringMultiLang, 'mandatory': False, 'order': 2}
        }
        
    class Time(DotDict):

        VALID = {
            'c_referenceYear': {'type': Year, 'mandatory': False, 'order': 1, 'unique': True},
            'c_dataSetValidUntil': {'type': Year, 'mandatory': False, 'order': 2, 'unique': True},
            'c_timeRepresentativenessDescription': {'type': FTMultiLang, 'mandatory': False, 'order': 3}
        }

    class Geography(DotDict):

        class __LocationOfOperationSupplyOrProduction(DotDict):

            VALID = {
                'a_location': {'type': NullableString, 'mandatory': True, 'order': 0, 'unique': True},
                'a_latitudeAndLongitude': {'type': GIS, 'mandatory': False, 'order': 0, 'unique': True},
                'descriptionOfRestrictions': {'type': FTMultiLang, 'mandatory': False, 'order': 1}
            }

        class __SubLocationOfOperationSupplyOrProduction(DotDict):

            VALID = {
                'a_subLocation': {'type': String, 'mandatory': False, 'order': 0, 'unique': True},
                'a_latitudeAndLongitude': {'type': GIS, 'mandatory': False, 'order': 0, 'unique': True},
                'descriptionOfRestrictions': {'type': FTMultiLang, 'mandatory': False, 'order': 1}
            }

        VALID = {
            'locationOfOperationSupplyOrProduction': {'type': __LocationOfOperationSupplyOrProduction, 'mandatory': False, 'order': 1, 'unique': True},
            'subLocationOfOperationSupplyOrProduction': {'type': __SubLocationOfOperationSupplyOrProduction, 'mandatory': False, 'order': 2}
        }

    class Technology(DotDict):

        VALID = {
            'technologyDescriptionAndIncludedProcesses': {'type': FTMultiLang, 'mandatory': False, 'order': 1},
            'referenceToIncludedProcesses': {'type': ILCD1Reference, 'mandatory': False, 'order': 2},
            'technologicalApplicability': {'type': FTMultiLang, 'mandatory': False, 'order': 3},
            'referenceToTechnologyPictogramme': {'type': ILCD1Reference, 'mandatory': False, 'order': 4, 'unique': True},
            'referenceToTechnologyFlowDiagrammOrPicture': {'type': ILCD1Reference, 'mandatory': False, 'order': 5}
        }

    class MathematicalRelations(DotDict):

        class __VariableParameter(DotDict):

            VALID = {
                'a_name': {'type': MatV, 'mandatory': True, 'order': 0, 'unique': True},
                'formula': {'type': STR, 'mandatory': False, 'order': 1, 'unique': True},
                'meanValue': {'type': Real, 'mandatory': False, 'order': 2, 'unique': True},
                'minimumValue': {'type': Real, 'mandatory': False, 'order': 3, 'unique': True},
                'maximumValue': {'type': Real, 'mandatory': False, 'order': 4, 'unique': True},
                'uncertaintyDistributionType': {'type': return_enum(UncertaintyDistributionTypeValues), 'mandatory': False, 'order': 5, 'unique': True},
                'relativeStandardDeviation95In': {'type': Perc, 'mandatory': False, 'order': 6, 'unique': True},
                'comment': {'type': StringMultiLang, 'mandatory': False, 'order': 7}
            }

        VALID = {
            'modelDescription': {'type': FTMultiLang, 'mandatory': False, 'order': 1},
            'variableParameter': {'type': __VariableParameter, 'mandatory': False, 'order': 2}
        }

    class ModellingAndValidation(DotDict):

        class __LCIMethodAndAllocation(DotDict):

            VALID = {
                'typeOfDataSet': {'type': return_enum(TypeOfProcessValues), 'mandatory': False, 'order': 1, 'unique': True},
                'LCIMethodPrinciple': {'type': return_enum(LCIMethodPrincipleValues), 'mandatory': False, 'order': 2, 'unique': True},
                'deviationsFromLCIMethodPrinciple': {'type': FTMultiLang, 'mandatory': False, 'order': 3},
                'LCIMethodApproaches': {'type': return_enum(LCIMethodApproachesValues, list_=True), 'mandatory': False, 'order': 4},
                'deviationsFromLCIMethodApproaches': {'type': FTMultiLang, 'mandatory': False, 'order': 5},
                'modellingConstants': {'type': FTMultiLang, 'mandatory': False, 'order': 6},
                'deviationsFromModellingConstants': {'type': FTMultiLang, 'mandatory': False, 'order': 7},
                'referenceToLCAMethodDetails': {'type': ILCD1Reference, 'mandatory': False, 'order': 8}
            }

        class __DataSourcesTreatmentAndRepresentativeness(DotDict):

            VALID = {
                'dataCutOffAndCompletenessPrinciples': {'type': FTMultiLang, 'mandatory': False, 'order': 1},
                'deviationsFromCutOffAndCompletenessPrinciples': {'type': FTMultiLang, 'mandatory': False, 'order': 2},
                'dataSelectionAndCombinationPrinciples': {'type': FTMultiLang, 'mandatory': False, 'order': 3},
                'deviationsFromSelectionAndCombinationPrinciples': {'type': FTMultiLang, 'mandatory': False, 'order': 4},
                'dataTreatmentAndExtrapolationsPrinciples': {'type': FTMultiLang, 'mandatory': False, 'order': 5},
                'deviationsFromTreatmentAndExtrapolationPrinciples': {'type': FTMultiLang, 'mandatory': False, 'order': 6},
                'referenceToDataHandlingPrinciples': {'type': ILCD1Reference, 'mandatory': False, 'order': 7},
                'referenceToDataSource': {'type': ILCD1Reference, 'mandatory': False, 'order': 8},
                'percentageSupplyOrProductionCovered': {'type': Perc, 'mandatory': False, 'order': 9, 'unique': True},
                'annualSupplyOrProductionVolume': {'type': StringMultiLang, 'mandatory': False, 'order': 10},
                'samplingProcedure': {'type': FTMultiLang, 'mandatory': False, 'order': 11},
                'dataCollectionPeriod': {'type': StringMultiLang, 'mandatory': False, 'order': 12},
                'uncertaintyAdjustments': {'type': FTMultiLang, 'mandatory': False, 'order': 13},
                'useAdviceForDataSet': {'type': FTMultiLang, 'mandatory': False, 'order': 14}
            }

        class __Completeness(DotDict):

            class __CompletenessElementaryFlows(DotDict):

                VALID = {
                    'a_type': {'type': return_enum(CompletenessTypeValues), 'mandatory': True, 'order': 0, 'unique': True},
                    'a_value': {'type': return_enum(CompletenessValues), 'mandatory': True, 'order': 0, 'unique': True}
                }

            VALID = {
                'completenessProductModel': {'type': return_enum(CompletenessValues, list_=True), 'mandatory': False, 'order': 1},
                'referenceToSupportedImpactAssessmentMethods': {'type': ILCD1Reference, 'mandatory': False, 'order': 2},
                'completenessElementaryFlows': {'type': __CompletenessElementaryFlows, 'mandatory': False, 'order': 3},
                'completenessOtherProblemField': {'type': FTMultiLang, 'mandatory': False, 'order': 4}
            }

        class __Validation(DotDict):

            class __Review(DotDict):

                class __Scope(DotDict):

                    class __Method(DotDict):

                        VALID = {
                            'a_name': {'type': return_enum(MethodOfReviewValues), 'mandatory': True, 'order': 0, 'unique': True}
                        }

                    VALID = {
                        'a_name': {'type': return_enum(ScopeOfReviewValues), 'mandatory': True, 'order': 0, 'unique': True},
                        'c_method': {'type': __Method, 'mandatory': False, 'order': 1}
                    }

                class __DataQualityIndicators(DotDict):

                    class __DataQualityIndicator(DotDict):

                        VALID = {
                            'a_name': {'type': return_enum(DataQualityIndicatorValues), 'mandatory': True, 'order': 0, 'unique': True},
                            'a_value': {'type': return_enum(QualityValues), 'mandatory': True, 'order': 0, 'unique': True}
                        }

                    VALID = {
                        'c_dataQualityIndicator': {'type': __DataQualityIndicator, 'mandatory': True, 'order': 1}
                    }

                VALID = {
                    'a_type': {'type': return_enum(TypeOfReviewValues), 'mandatory': False, 'order': 0, 'unique': True},
                    'c_scope': {'type': __Scope, 'mandatory': False, 'order': 1},
                    'c_dataQualityIndicators': {'type': __DataQualityIndicators, 'mandatory': False, 'order': 2, 'unique': True},
                    'c_reviewDetails': {'type': FTMultiLang, 'mandatory': False, 'order': 3},
                    'c_referenceToNameOfReviewerAndInstitution': {'type': ILCD1Reference, 'mandatory': False, 'order': 4},
                    'c_otherReviewDetails': {'type': FTMultiLang, 'mandatory': False, 'order': 5},
                    'c_referenceToCompleteReviewReport': {'type': ILCD1Reference, 'mandatory': False, 'order': 6, 'unique': True}
                }

            VALID = {
                'review': {'type': __Review, 'mandatory': False, 'order': 1}
            }

        class __ComplianceDeclarations(DotDict):

            class __Compliance(DotDict):

                VALID = {
                    'c_referenceToComplianceSystem': {'type': ILCD1Reference, 'mandatory': True, 'order': 1, 'unique': True},
                    'c_approvalOfOverallCompliance': {'type': return_enum(ComplianceValues), 'mandatory': False, 'order': 2, 'unique': True},
                    'c_nomenclatureCompliance': {'type': return_enum(ComplianceValues), 'mandatory': False, 'order': 3, 'unique': True},
                    'c_methodologicalCompliance': {'type': return_enum(ComplianceValues), 'mandatory': False, 'order': 4, 'unique': True},
                    'c_reviewCompliance': {'type': return_enum(ComplianceValues), 'mandatory': False, 'order': 5, 'unique': True},
                    'c_documentationCompliance': {'type': return_enum(ComplianceValues), 'mandatory': False, 'order': 6, 'unique': True},
                    'c_qualityCompliance': {'type': return_enum(ComplianceValues), 'mandatory': False, 'order': 7, 'unique': True}
                }

            VALID = {
                'compliance': {'type': __Compliance, 'mandatory': True, 'order': 1}
            }

        VALID = {
            'LCIMethodAndAllocation': {'type': __LCIMethodAndAllocation, 'mandatory': False, 'order': 1, 'unique': True},
            'dataSourcesTreatmentAndRepresentativeness': {'type': __DataSourcesTreatmentAndRepresentativeness, 'mandatory': False, 'order': 2, 'unique': True},
            'completeness': {'type': __Completeness, 'mandatory': False, 'order': 3, 'unique': True},
            'validation': {'type': __Validation, 'mandatory': False, 'order': 4, 'unique': True},
            'complianceDeclarations': {'type': __ComplianceDeclarations, 'mandatory': False, 'order': 5, 'unique': True}
        }

    class AdministrativeInformation(DotDict):

        class __CommissionerAndGoal(DotDict):

            VALID = {
                'c_referenceToCommissioner': {'type': ILCD1Reference, 'mandatory': False, 'order': 1},
                'c_project': {'type': StringMultiLang, 'mandatory': False, 'order': 2},
                'c_intendedApplications': {'type': FTMultiLang, 'mandatory': False, 'order': 3}
            }

        class __DataGenerator(DotDict):

            VALID = {
                'c_referenceToPersonOrEntityGeneratingTheDataSet': {'type': ILCD1Reference, 'mandatory': False, 'order': 1}
            }

        class __DataEntryBy(DotDict):

            VALID = {
                'c_timeStamp': {'type': DateTime, 'mandatory': False, 'order': 1, 'unique': True},
                'c_referenceToDataSetFormat': {'type': ILCD1Reference, 'mandatory': False, 'order': 2},
                'c_referenceToConvertedOriginalDataSetFrom': {'type': ILCD1Reference, 'mandatory': False, 'order': 3, 'unique': True},
                'c_referenceToPersonOrEntityEnteringTheData': {'type': ILCD1Reference, 'mandatory': False, 'order': 4, 'unique': True},
                'c_referenceToDataSetUseApproval': {'type': ILCD1Reference, 'mandatory': False, 'order': 5}
            }

        class __PublicationAndOwnership(DotDict):

            VALID = {
                'c_dateOfLastRevision': {'type': ReviewDateTime, 'mandatory': False, 'order': 1}, # 'unique': True but can be overwritten in ECS2
                'c_dataSetVersion': {'type': Version, 'mandatory': True, 'order': 2, 'unique': True},
                'c_referenceToPrecedingDataSetVersion': {'type': ILCD1Reference, 'mandatory': False, 'order': 3},
                'c_permanentDataSetURI': {'type': STR, 'mandatory': False, 'order': 4, 'unique': True},
                'c_workflowAndPublicationStatus': {'type': return_enum(WorkflowAndPublicationStatusValues), 'mandatory': False, 'order': 5, 'unique': True},
                'c_referenceToUnchangedRepublication': {'type': ILCD1Reference, 'mandatory': False, 'order': 6, 'unique': True},
                'c_referenceToRegistrationAuthority': {'type': ILCD1Reference, 'mandatory': False, 'order': 7, 'unique': True},
                'c_registrationNumber': {'type': String, 'mandatory': False, 'order': 8, 'unique': True},
                'c_referenceToOwnershipOfDataSet': {'type': ILCD1Reference, 'mandatory': False, 'order': 9, 'unique': True},
                'c_copyright': {'type': BOOL, 'mandatory': False, 'order': 10, 'unique': True},
                'c_referenceToEntitiesWithExclusiveAccess': {'type': ILCD1Reference, 'mandatory': False, 'order': 11},
                'c_licenseType': {'type': return_enum(LicenseTypeValues), 'mandatory': False, 'order': 12}, # 'unique': True but can override the default in ECS2
                'c_accessRestrictions': {'type': FTMultiLang, 'mandatory': False, 'order': 13}
            }

        VALID = {
            'c_commissionerAndGoal': {'type': __CommissionerAndGoal, 'mandatory': False, 'order': 1, 'unique': True},
            'dataGenerator': {'type': __DataGenerator, 'mandatory': False, 'order': 2, 'unique': True},
            'dataEntryBy': {'type': __DataEntryBy, 'mandatory': False, 'order': 3, 'unique': True},
            'publicationAndOwnership': {'type': __PublicationAndOwnership, 'mandatory': False, 'order': 4, 'unique': True}
        }
        
    class Exchanges(DotDict):

        class __Exchange(DotDict):

            class __Allocations(DotDict):

                class __Allocation(DotDict):

                    VALID = {
                        'a_internalReferenceToCoProduct': {'type': Int6, 'mandatory': True, 'order': 0, 'unique': True},
                        'a_allocatedFraction': {'type': Perc, 'mandatory': True, 'order': 0, 'unique': True}
                    }

                VALID = {
                    'allocation': {'type': __Allocation, 'mandatory': True, 'order': 1}
                }

            class __ReferencesToDataSource(DotDict):

                VALID = {
                    'referenceToDataSource': {'type': ILCD1Reference, 'mandatory': False, 'order': 1}
                }

            VALID = {
                'a_dataSetInternalID': {'type': Int6, 'mandatory': True, 'order': 0, 'unique': True},
                'referenceToFlowDataSet': {'type': ILCD1Reference, 'mandatory': True, 'order': 1, 'unique': True},
                'location': {'type': String, 'mandatory': False, 'order': 2, 'unique': True},
                'functionType': {'type': return_enum(ExchangeFunctionTypeValues), 'mandatory': False, 'order': 3, 'unique': True},
                'exchangeDirection': {'type': return_enum(ExchangeDirectionValues), 'mandatory': False, 'order': 4, 'unique': True},
                'referenceToVariable': {'type': STR, 'mandatory': False, 'order': 5, 'unique': True},
                'meanAmount': {'type': Real, 'mandatory': True, 'order': 6, 'unique': True},
                'resultingAmount': {'type': Real, 'mandatory': False, 'order': 7, 'unique': True},
                'minimumAmount': {'type': Real, 'mandatory': False, 'order': 8, 'unique': True},
                'maximumAmount': {'type': Real, 'mandatory': False, 'order': 9, 'unique': True},
                'uncertaintyDistributionType': {'type': return_enum(UncertaintyDistributionTypeValues), 'mandatory': False, 'order': 10, 'unique': True},
                'relativeStandardDeviation95In': {'type': Perc, 'mandatory': False, 'order': 11, 'unique': True},
                'allocations': {'type': __Allocations, 'mandatory': False, 'order': 12, 'unique': True},
                'dataSourceType': {'type': return_enum(DataSourceTypeValues), 'mandatory': False, 'order': 13, 'unique': True},
                'dataDerivationTypeStatus': {'type': return_enum(DataDerivationTypeStatusValues), 'mandatory': False, 'order': 14, 'unique': True},
                'referencesToDataSource': {'type': __ReferencesToDataSource, 'mandatory': False, 'order': 15, 'unique': True},
                'generalComment': {'type': StringMultiLang, 'mandatory': False, 'order': 16}
            }

        VALID = {
            'exchange': {'type': __Exchange, 'mandatory': False, 'order': 1}
        }

    def __init__(self):
        self.dataSetInformation = self.DataSetInformation()
        self.quantitativeReference = self.QuantitativeReference()
        self.time = self.Time()
        self.technology = self.Technology()
        self.geography = self.Geography()
        self.modellingAndValidation = self.ModellingAndValidation()
        self.administrativeInformation = self.AdministrativeInformation()
        self.mathematicalRelations = self.MathematicalRelations()
        self.exchanges = self.Exchanges()
        
        self.flow_property = ILCD1FlowProperty
        self.classification = ILCD1Classification
        self.reference = ILCD1Reference
        
    def get_dict(self):
        return {
            'processDataSet': {
                '@xmlns': 'http://lca.jrc.it/ILCD/Process',
                '@xmlns:c': 'http://lca.jrc.it/ILCD/Common',
                '@version': '1.1', 
                '@locations': '../ILCDLocations.xml',
                '@metaDataOnly': "false",
                'processInformation': {
                    'dataSetInformation': self.dataSetInformation.get_dict(),
                    'quantitativeReference': self.quantitativeReference.get_dict(),
                    'time': self.time.get_dict(),
                    'geography': self.geography.get_dict(),
                    'technology': self.technology.get_dict(),
                    'mathematicalRelations': self.mathematicalRelations.get_dict()
                    },
                'modellingAndValidation': self.modellingAndValidation.get_dict(),
                'administrativeInformation': self.administrativeInformation.get_dict(),
                'exchanges': self.exchanges.get_dict()
                }
            }

# TODO Retirar

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

class ECS2ToILCD1DataNotConverted(DotDict):

    class Flow(DotDict):

        class Property(DotDict):

            VALID = {
                'a_id': {'type': STR, 'mandatory': True},
                'a_amount': {'type': Real, 'mandatory': False},
                'a_unitId': {'type': STR, 'mandatory': False},
                'a_variableName': {'type': STR, 'mandatory': False},
                'a_mathematicalRelation': {'type': STR, 'mandatory': False},
                'a_propertyContextId': {'type': STR, 'mandatory': False},
                'a_isDefiningValue': {'type': BOOL, 'mandatory': False},
                'a_isCalculatedAmount': {'type': BOOL, 'mandatory': False},
                'a_unitContextId': {'type': STR, 'mandatory': False},
                'a_sourceIdOverwrittenByChild': {'type': STR, 'mandatory': False},
                'a_sourceContextId': {'type': STR, 'mandatory': False}
            }

        class ProductionVolume(DotDict):

            VALID = {
                'a_productionVolumeSourceIdOverwrittenByChild': {'type': STR, 'mandatory': False},
                'a_productionVolumeSourceContextId': {'type': STR, 'mandatory': False}
            }

        VALID = {
            'a_id': {'type': STR, 'mandatory': True},
            'classification': {'type': LIST, 'mandatory': False},
            'a_fId': {'type': STR, 'mandatory': False},
            'tag': {'type': LIST, 'mandatory': False},
            'a_unitContextId': {'type': STR, 'mandatory': False},
            'a_isCalculatedAmount': {'type': BOOL, 'mandatory': False},
            'a_sourceIdOverwrittenByChild': {'type': BOOL, 'mandatory': False},
            'a_specificAllocationPropertyIdOverwrittenByChild': {'type': STR, 'mandatory': False},
            'a_specificAllocationPropertyContextId': {'type': STR, 'mandatory': False},
            'transferCoefficient': {'type': LIST, 'mandatory': False},
            'properties': {'type': Property, 'mandatory': True},
            'uncertainty': {'type': LIST, 'mandatory': False},
            'productionVolume': {'type': ProductionVolume, 'mandatory': True},
            'a_activityLinkIdOverwrittenByChild': {'type': BOOL, 'mandatory': False},
            'a_intermediateExchangeContextId': {'type': STR, 'mandatory': False},
            'a_elementaryExchangeContextId': {'type': STR, 'mandatory': False},
            'a_activityLinkContextId': {'type': STR, 'mandatory': False}
        }

    class Parameter(DotDict):

        VALID = {
            'a_amount': {'type': Real, 'mandatory': False},
            'a_parameterContextId': {'type': STR, 'mandatory': False},
            'a_isCalculatedAmount': {'type': BOOL, 'mandatory': False},
            'a_unitContextId': {'type': STR, 'mandatory': False}
        }

    VALID = {
        'activityNameId': {'type': STR, 'mandatory': True},
        'activityNameContextId': {'type': STR, 'mandatory': False},
        'parentActivityId': {'type': STR, 'mandatory': False},
        'parentActivityContextId': {'type': STR, 'mandatory': False},
        'inheritanceDepth': {'type': STR, 'mandatory': False},
        'specialActivityType': {'type': STR, 'mandatory': True},
        'masterAllocationPropertyId': {'type': STR, 'mandatory': True},
        'masterAllocationPropertyIdOverwrittenByChild': {'type': STR, 'mandatory': False},
        'masterAllocationPropertyContextId': {'type': STR, 'mandatory': False},
        'tag': {'type': LIST, 'mandatory': False},
        'geographyId': {'type': STR, 'mandatory': True},
        'geographyContextId': {'type': STR, 'mandatory': False},
        'technologyLevel': {'type': STR, 'mandatory': False},
        'isDataValidForEntirePeriod': {'type': BOOL, 'mandatory': True},
        'macroEconomicScenarioId': {'type': STR, 'mandatory': True},
        'macroEconomicScenarioContextId': {'type': STR, 'mandatory': False},
        'macroEconomicScenario_name': {'type': STR, 'mandatory': True},
        'macroEconomicScenario_comment': {'type': LIST, 'mandatory': False},
        'classificationContext': {'type': LIST, 'mandatory': False},
        'systemModelId': {'type': STR, 'mandatory': True},
        'systemModelContextId': {'type': STR, 'mandatory': False},
        'review': {'type': LIST, 'mandatory': False},
        'dataEntryBy_personContextId': {'type': STR, 'mandatory': False},
        'dataGeneratorAndPublication_personContextId': {'type': LIST, 'mandatory': False},
        'publishedSourceIdOverwrittenByChild': {'type': LIST, 'mandatory': False},
        'publishedSourceContextId': {'type': LIST, 'mandatory': False},
        'companyIdOverwrittenByChild': {'type': LIST, 'mandatory': False},
        'companyContextId': {'type': LIST, 'mandatory': False},
        'version': {'type': STR, 'mandatory': True},
        'fileInfo': {'type': STR, 'mandatory': True},
        'requiredContext': {'type': LIST, 'mandatory': True},
        'flows': {'type': Flow, 'mandatory': True},
        'parameter': {'type': Parameter, 'mandatory': True}
    }

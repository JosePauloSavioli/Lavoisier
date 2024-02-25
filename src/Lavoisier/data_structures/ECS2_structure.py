#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 31 19:20:32 2022

@author: jotape42p
"""

from .main import DotDict
from .abstractions import StructureTemplate
from .validators.general_validators import (
    Validator,
    Real,
    Int,
    UUID,
    Str
    )
from .validators.ECS2_validators import (
    Percent,
    Bool,
    InheritanceDepthINT,
    SourceTypeINT,
    TypeINT,
    SpecialActivityTypeINT,
    EnergyValuesINT,
    TechnologyLevelINT,
    DataPublishedInINT,
    AccessRestrictedToINT,
    PedigreeINT,
    InputGroupIntermediateINT,
    OutputGroupIntermediateINT,
    InputGroupElementaryINT,
    OutputGroupElementaryINT,
    CASNumber,
    Date,
    CompleteDate,
    ISOTwoLetterCode,
    ISOThreeLetterCode,
    Lang,
    CompanyCode,
    BaseString30,
    BaseString40,
    BaseString80,
    BaseString255,
    BaseString32000,
    UniqueBaseString30,
    UniqueBaseString40,
    ReviewString,
    UniqueBaseString80,
    VariableName,
    NamedString32000,
    String20,
    String40,
    String80,
    String120,
    String255,
    String32000,
    UniqueString40,
    IndexedStringSTR,
    IndexedString32000,
    String80_NLR,
    ClassificationValueString120,
    ExchangeNameString80,
    Name
    )

### Basic classes

class Lognormal(DotDict):
    
    VALID = {
        'meanValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'mu': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'variance': {'xml_type': 'attribute', 'type': Real, 'mandatory': False, 'order': 0, 'unique': True}, # Not sure if it is mandatory
        'varianceWithPedigreeUncertainty': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
        }
    
class Normal(DotDict):
    
    VALID = {
        'meanValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0},
        'variance': {'xml_type': 'attribute', 'type': Real, 'mandatory': False, 'order': 0},
        'varianceWithPedigreeUncertainty': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0}
        }

class Triangular(DotDict):
    
    VALID = {
        'minValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'mostLikelyValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'maxValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
        }

class Uniform(DotDict):
    
    VALID = {
        'minValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'maxValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
        }

class Beta(DotDict):
    
    VALID = {
        'minValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'mostLikelyValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'maxValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
        }

class Gamma(DotDict):
    
    VALID = {
        'shape': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'scale': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'minValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
        }

class Binomial(DotDict):
    
    VALID = {
        'n': {'xml_type': 'attribute', 'type': Int, 'mandatory': True, 'order': 0, 'unique': True},
        'p': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
        }
    
class Undefined(DotDict):
    
    VALID = {
        'minValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'maxValue': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'standardDeviation95': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
        }

class PedigreeMatrix(DotDict):
    
    VALID = {
        'reliability': {'xml_type': 'attribute', 'type': PedigreeINT, 'mandatory': True, 'order': 0, 'unique': True},
        'completeness': {'xml_type': 'attribute', 'type': PedigreeINT, 'mandatory': True, 'order': 0, 'unique': True},
        'temporalCorrelation': {'xml_type': 'attribute', 'type': PedigreeINT, 'mandatory': True, 'order': 0, 'unique': True},
        'geographicalCorrelation': {'xml_type': 'attribute', 'type': PedigreeINT, 'mandatory': True, 'order': 0, 'unique': True},
        'furtherTechnologyCorrelation': {'xml_type': 'attribute', 'type': PedigreeINT, 'mandatory': True, 'order': 0, 'unique': True},
        }

class ECS2Uncertainty(DotDict):
    
    VALID = {
        'lognormal': {'type': Lognormal, 'mandatory': False, 'order': 1, 'unique': True},
        'normal': {'type': Normal, 'mandatory': False, 'order': 2, 'unique': True},
        'triangular': {'type': Triangular, 'mandatory': False, 'order': 3, 'unique': True},
        'uniform': {'type': Uniform, 'mandatory': False, 'order': 4, 'unique': True},
        'beta': {'type': Beta, 'mandatory': False, 'order': 5, 'unique': True},
        'gamma': {'type': Gamma, 'mandatory': False, 'order': 6, 'unique': True},
        'binomial': {'type': Binomial, 'mandatory': False, 'order': 7, 'unique': True},
        'undefined': {'type': Undefined, 'mandatory': False, 'order': 8, 'unique': True},
        'pedigreeMatrix': {'type': PedigreeMatrix, 'mandatory': False, 'order': 9, 'unique': True},
        'comment': {'type': String32000, 'mandatory': False, 'order': 10, 'unique': False}
        }

##########################

class ECS2Source(DotDict):
    
    VALID = {
        'sourceId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE
        'sourceIdOverwrittenByChild': {'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': True},
        'sourceContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'sourceYear': {'xml_type': 'attribute', 'type': UniqueBaseString30, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE
        'sourceFirstAuthor': {'xml_type': 'attribute', 'type': UniqueBaseString40, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE
        }

##########################

class ECS2QuantitativeReference(DotDict):
    
    VALID_NO_SOURCE = {
        'amount': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0},
        'mathematicalRelation': {'xml_type': 'attribute', 'type': BaseString32000, 'mandatory': False, 'order': 0, 'unique': True},
        'isCalculatedAmount': {'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': True},
        'comment': {'type': String32000, 'mandatory': False, 'order': 4, 'unique': False},
        'uncertainty': {'type': ECS2Uncertainty, 'mandatory': False, 'order': 3, 'unique': True}
        }
    
    VALID = ECS2Source.VALID | {
        'amount': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0},
        'mathematicalRelation': {'xml_type': 'attribute', 'type': BaseString32000, 'mandatory': False, 'order': 0, 'unique': True},
        'isCalculatedAmount': {'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': True},
        'comment': {'type': String32000, 'mandatory': False, 'order': 3, 'unique': False},
        'uncertainty': {'type': ECS2Uncertainty, 'mandatory': False, 'order': 4, 'unique': True}
        }
    
    VALID_PROP = ECS2Source.VALID | {
        'amount': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0},
        'mathematicalRelation': {'xml_type': 'attribute', 'type': BaseString32000, 'mandatory': False, 'order': 0, 'unique': True},
        'isCalculatedAmount': {'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': True},
        'comment': {'type': String32000, 'mandatory': False, 'order': 4, 'unique': False},
        'uncertainty': {'type': ECS2Uncertainty, 'mandatory': False, 'order': 3, 'unique': True}
        }
    
##########################

class ECS2QuantitativeReferenceWithUnit(DotDict):
    
    VALID = ECS2QuantitativeReference.VALID | {
        'variableName': {'xml_type': 'attribute', 'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
        'unitId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE
        'unitContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': ExchangeNameString80, 'mandatory': True, 'order': 1, 'unique': False},
        'unitName': {'type': UniqueString40, 'mandatory': True, 'order': 2, 'unique': False},
        }
    
    VALID_NO_SOURCE = ECS2QuantitativeReference.VALID_NO_SOURCE | { # Parameter doesn't have mandatory unit id or name
        'variableName': {'xml_type': 'attribute', 'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
        'unitId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE
        'unitContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': ExchangeNameString80, 'mandatory': True, 'order': 1, 'unique': False},
        'unitName': {'type': UniqueString40, 'mandatory': False, 'order': 2, 'unique': False},
        }
    
    VALID_PROP = ECS2QuantitativeReference.VALID_PROP | { # Parameter doesn't have mandatoty unit id or name
        'variableName': {'xml_type': 'attribute', 'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
        'unitId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE
        'unitContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': ExchangeNameString80, 'mandatory': True, 'order': 1, 'unique': False},
        'unitName': {'type': UniqueString40, 'mandatory': False, 'order': 2, 'unique': False},
        }
   
##########################

class ECS2TextAndImage(DotDict):
    
    VALID = {
        'text': {'type': IndexedString32000, 'mandatory': False, 'order': 1, 'unique': False}, # Can't enumerate indexes because this is separated
        'imageUrl': {'type': IndexedStringSTR, 'mandatory': False, 'order': 2, 'unique': False},
        'variable': {'type': NamedString32000, 'mandatory': False, 'order': 3, 'unique': False}
        }

##########################

class ECS2Classification(DotDict):
    
    VALID = {
        'classificationId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'classificationContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'classificationSystem': {'type': String255, 'mandatory': True, 'order': 1, 'unique': False},
        'classificationValue': {'type': ClassificationValueString120, 'mandatory': True, 'order': 2, 'unique': False}
        }

##########################

class ECS2Property(DotDict):
    
    VALID = ECS2QuantitativeReferenceWithUnit.VALID_PROP | {
        'propertyId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'propertyContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'isDefiningValue': {'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': True}
        }


### Master data files

# xmlns="http://www.EcoInvent.org/UsedUserMasterData"

class ActivityNameMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': False}, # Double
        'name': {'type': String120, 'mandatory': True, 'order': 1, 'unique': False}
        }

##########################

class CSClassificationValue(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'name': {'type': ClassificationValueString120, 'mandatory': True, 'order': 1, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
        }

class ClassificationSystemMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'type': {'xml_type': 'attribute', 'type': TypeINT, 'mandatory': True, 'order': 0, 'unique': True}, # 1 = activity classification, 2 = product classification, 3 = activity and product classification
        'name': {'type': String255, 'mandatory': True, 'order': 1, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False},
        'classificationValue': {'type': CSClassificationValue, 'mandatory': True, 'order': 3, 'unique': False}
        }

##########################

class CompanyMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'code': {'xml_type': 'attribute', 'type': CompanyCode, 'mandatory': True, 'order': 0, 'unique': True},
        'website': {'xml_type': 'attribute', 'type': BaseString255, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': String255, 'mandatory': False, 'order': 1, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
        }

##########################

class CSubcompartmentMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'name': {'type': String40, 'mandatory': True, 'order': 1, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
        }

class CompartmentMaster(DotDict):
        
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'name': {'type': String40, 'mandatory': True, 'order': 1, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False},
        'subcompartment': {'type': CSubcompartmentMaster, 'mandatory': True, 'order': 3, 'unique': False}
        }

##########################

class EMCompartment(DotDict):
    
    VALID = {
        'subcompartmentId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'subcompartmentContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'compartment': {'type': String40, 'mandatory': True, 'order': 1, 'unique': False},
        'subcompartment': {'type': String40, 'mandatory': True, 'order': 2, 'unique': False}
        }

class ElementaryMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'unitId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'unitContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'formula': {'xml_type': 'attribute', 'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
        'casNumber': {'xml_type': 'attribute', 'type': CASNumber, 'mandatory': False, 'order': 0, 'unique': True},
        'defaultVariableName': {'xml_type': 'attribute', 'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': String120, 'mandatory': True, 'order': 1, 'unique': False},
        'unitName': {'type': String40, 'mandatory': True, 'order': 2, 'unique': False},
        'compartment': {'type': EMCompartment, 'mandatory': True, 'order': 3, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 4, 'unique': False},
        'synonym': {'type': String80_NLR, 'mandatory': False, 'order': 5, 'unique': False},
        'property': {'type': ECS2Property, 'mandatory': False, 'order': 6, 'unique': False},
        'productInformation': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 7, 'unique': True}
        }

##########################

class GeographyMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'longitude': {'xml_type': 'attribute', 'type': Real, 'mandatory': False, 'order': 0, 'unique': True},
        'latitude': {'xml_type': 'attribute', 'type': Real, 'mandatory': False, 'order': 0, 'unique': True},
        'ISOTwoLetterCode': {'xml_type': 'attribute', 'type': ISOTwoLetterCode, 'mandatory': False, 'order': 0, 'unique': True},
        'ISOThreeLetterCode': {'xml_type': 'attribute', 'type': ISOThreeLetterCode, 'mandatory': False, 'order': 0, 'unique': True},
        'uNCode': {'xml_type': 'attribute', 'type': Int, 'mandatory': False, 'order': 0, 'unique': True}, # INT1
        'uNRegionCode': {'xml_type': 'attribute', 'type': Int, 'mandatory': False, 'order': 0, 'unique': True},
        'uNSubregionCode': {'xml_type': 'attribute', 'type': Int, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': String255, 'mandatory': True, 'order': 1, 'unique': False},
        'shortname': {'type': String40, 'mandatory': True, 'order': 2, 'unique': False},
        'comment': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 3, 'unique': True},
        # 'kml': {'type':}
        }

##########################

class IntermediateMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'unitId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'unitContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'casNumber': {'xml_type': 'attribute', 'type': CASNumber, 'mandatory': False, 'order': 0, 'unique': True},
        'defaultVariableName': {'xml_type': 'attribute', 'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': String120, 'mandatory': True, 'order': 1, 'unique': False},
        'unitName': {'type': String40, 'mandatory': True, 'order': 2, 'unique': False},
        'classification': {'type': ECS2Classification, 'mandatory': False, 'order': 3, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 4, 'unique': False},
        'synonym': {'type': String80_NLR, 'mandatory': False, 'order': 5, 'unique': False},
        'property': {'type': ECS2Property, 'mandatory': False, 'order': 6, 'unique': False},
        'productInformation': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 7, 'unique': True}
        }
    
##########################

class LanguageMaster(DotDict):
    
    VALID = {
        'code': {'xml_type': 'attribute', 'type': Lang, 'mandatory': True, 'order': 0, 'unique': True},
        'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
        }

##########################

class MacroEconomicScenarioMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'name': {'type': String80, 'mandatory': True, 'order': 1, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
        }

##########################

class ParameterMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'defaultVariableName': {'xml_type': 'attribute', 'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
        'unitId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'unitContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': String80, 'mandatory': True, 'order': 1, 'unique': False},
        'unitName': {'type': String40, 'mandatory': False, 'order': 2, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 3, 'unique': False}
        }

##########################

class PersonMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'name': {'xml_type': 'attribute', 'type': BaseString40, 'mandatory': True, 'order': 0, 'unique': True},
        'address': {'xml_type': 'attribute', 'type': BaseString255, 'mandatory': False, 'order': 0, 'unique': True},
        'telephone': {'xml_type': 'attribute', 'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
        'telefax': {'xml_type': 'attribute', 'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
        'email': {'xml_type': 'attribute', 'type': BaseString80, 'mandatory': True, 'order': 0, 'unique': True},
        'companyId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'companyContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'companyName': {'type': String255, 'mandatory': False, 'order': 1, 'unique': False}
        }

##########################

class PropertyMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'defaultVariableName': {'xml_type': 'attribute', 'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
        'unitId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'unitContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': String80, 'mandatory': True, 'order': 1, 'unique': False},
        'unitName': {'type': String40, 'mandatory': False, 'order': 2, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 3, 'unique': False}
        }
    
##########################

class SourceMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'sourceType': {'xml_type': 'attribute', 'type': SourceTypeINT, 'mandatory': True, 'order': 0, 'unique': True},
        'year': {'xml_type': 'attribute', 'type': BaseString30, 'mandatory': False, 'order': 0, 'unique': True},
        'volumeNo': {'xml_type': 'attribute', 'type': Int, 'mandatory': False, 'order': 0, 'unique': True},
        'firstAuthor': {'xml_type': 'attribute', 'type': BaseString40, 'mandatory': True, 'order': 0, 'unique': True},
        'additionalAuthors': {'xml_type': 'attribute', 'type': BaseString255, 'mandatory': False, 'order': 0, 'unique': True},
        'title': {'xml_type': 'attribute', 'type': BaseString255, 'mandatory': True, 'order': 0, 'unique': True},
        'shortName': {'xml_type': 'attribute', 'type': BaseString80, 'mandatory': False, 'order': 0, 'unique': True},
        'pageNumbers': {'xml_type': 'attribute', 'type': BaseString30, 'mandatory': False, 'order': 0, 'unique': True},
        'nameOfEditors': {'xml_type': 'attribute', 'type': BaseString255, 'mandatory': False, 'order': 0, 'unique': True},
        'titleOfAnthology': {'xml_type': 'attribute', 'type': BaseString255, 'mandatory': False, 'order': 0, 'unique': True},
        'placeOfPublications': {'xml_type': 'attribute', 'type': BaseString32000, 'mandatory': False, 'order': 0, 'unique': True},
        'publisher': {'xml_type': 'attribute', 'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
        'journal': {'xml_type': 'attribute', 'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
        'issueNo': {'xml_type': 'attribute', 'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
        'comment': {'type': String32000, 'mandatory': False, 'order': 1, 'unique': False}
        }

##########################

class SystemModelMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'name': {'type': String120, 'mandatory': True, 'order': 1, 'unique': False},
        'shortname': {'type': String20, 'mandatory': True, 'order': 2, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 3, 'unique': False}
        }
    
##########################

class TagMaster(DotDict):
    
    VALID = {
        'name': {'xml_type': 'attribute', 'type': BaseString40, 'mandatory': True, 'order': 0, 'unique': True},
        'comment': {'type': String32000, 'mandatory': False, 'order': 1, 'unique': False}
        }

##########################

class UnitMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'name': {'type': String40, 'mandatory': True, 'order': 1, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
        }

##########################

class ActivityIndexEntryMaster(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True}, # OK
        'activityNameId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': False}, # OK
        'geographyId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True}, # OK
        'startDate': {'xml_type': 'attribute', 'type': Date, 'mandatory': True, 'order': 0, 'unique': True},
        'endDate': {'xml_type': 'attribute', 'type': Date, 'mandatory': True, 'order': 0, 'unique': True},
        'specialActivityType': {'xml_type': 'attribute', 'type': SpecialActivityTypeINT, 'mandatory': True, 'order': 0}, # DOUBLE
        'systemModelId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True}
        }

##########################

class ECS2UsedUserMasterData(DotDict):
    
    VALID = {
        'activityName': {'type': ActivityNameMaster, 'mandatory': False, 'order': 0, 'unique': False},
        'language': {'type': LanguageMaster, 'mandatory': False, 'order': 1, 'unique': False},
        'geography': {'type': GeographyMaster, 'mandatory': False, 'order': 2, 'unique': False},
        'systemModel': {'type': SystemModelMaster, 'mandatory': False, 'order': 3, 'unique': False},
        'tag': {'type': TagMaster, 'mandatory': False, 'order': 4, 'unique': False},
        'macroEconomicScenario': {'type': MacroEconomicScenarioMaster, 'mandatory': False, 'order': 5, 'unique': False},
        'compartment': {'type': CompartmentMaster, 'mandatory': False, 'order': 6, 'unique': False},
        'classificationSystem': {'type': ClassificationSystemMaster, 'mandatory': False, 'order': 7, 'unique': False},
        'company': {'type': CompanyMaster, 'mandatory': False, 'order': 8, 'unique': False},
        'person': {'type': PersonMaster, 'mandatory': False, 'order': 9, 'unique': False},
        'source': {'type': SourceMaster, 'mandatory': False, 'order': 10, 'unique': False},
        'units': {'type': UnitMaster, 'mandatory': False, 'order': 11, 'unique': False},
        'parameter': {'type': ParameterMaster, 'mandatory': False, 'order': 12, 'unique': False},
        'property': {'type': PropertyMaster, 'mandatory': False, 'order': 13, 'unique': False},
        # 'context': {'type': __ContextMaster, 'mandatory': False, 'order': 4, 'unique': False},
        'elementaryExchange': {'type': ElementaryMaster, 'mandatory': False, 'order': 14, 'unique': False},
        'intermediateExchange': {'type': IntermediateMaster, 'mandatory': False, 'order': 15, 'unique': False},
        'activityIndexEntry': {'type': ActivityIndexEntryMaster, 'mandatory': False, 'order': 16, 'unique': True},
        }

##########################

class CETransferCoefficient(DotDict):
    
    VALID = ECS2QuantitativeReference.VALID | {
        'exchangeId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True}
        }

### Regular classes

class ECS2CustomExchange(DotDict):
    
    VALID = ECS2QuantitativeReferenceWithUnit.VALID | {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0},
        'casNumber': {'xml_type': 'attribute', 'type': CASNumber, 'mandatory': False, 'order': 0, 'unique': True},
        'pageNumbers': {'xml_type': 'attribute', 'type': BaseString30, 'mandatory': False, 'order': 0, 'unique': True},
        'specificAllocationPropertyId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'specificAllocationPropertyIdOverwrittenByChild': {'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': True},
        'specificAllocationPropertyContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'synonym': {'type': String80_NLR, 'mandatory': False, 'order': 5, 'unique': False},
        'property': {'type': ECS2Property, 'mandatory': False, 'order': 6, 'unique': False},
        'transferCoefficient': {'type': CETransferCoefficient, 'mandatory': False, 'order': 7, 'unique': False},
        'tag': {'type': BaseString40, 'mandatory': False, 'order': 8, 'unique': False}
        }

##########################

class Activity(DotDict):
    
    VALID = {
        'id': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'activityNameId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': False}, # Actualy unique, but double entry
        'activityNameContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'parentActivityId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'parentActivityContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'inheritanceDepth': {'xml_type': 'attribute', 'type': InheritanceDepthINT, 'mandatory': True, 'order': 0, 'unique': False}, # [DEFAULT] Actualy not mandatory but can be filled with default
        'type': {'xml_type': 'attribute', 'type': TypeINT, 'mandatory': True, 'order': 0, 'unique': True},
        'specialActivityType': {'xml_type': 'attribute', 'type': SpecialActivityTypeINT, 'mandatory': True, 'order': 0, 'unique': False}, # Actualy unique, but double entry
        'energyValues': {'xml_type': 'attribute', 'type': EnergyValuesINT, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE [DEFAULT]
        'masterAllocationPropertyId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'masterAllocationPropertyIdOverwrittenByChild': {'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': True},
        'masterAllocationPropertyContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'datasetIcon': {'xml_type': 'attribute', 'type': Str, 'mandatory': False, 'order': 0, 'unique': True},
        'activityName': {'type': Name, 'mandatory': True, 'order': 1, 'unique': False},
        'synonym': {'type': String80_NLR, 'mandatory': False, 'order': 2, 'unique': False},
        'includedActivitiesStart': {'type': String32000, 'mandatory': False, 'order': 3, 'unique': False}, # If LCI, has to be "From cradle, including..."
        'includedActivitiesEnd': {'type': String32000, 'mandatory': False, 'order': 4, 'unique': False},
        'allocationComment': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 5, 'unique': True},
        'generalComment': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 6, 'unique': True},
        'tag': {'type': BaseString40, 'mandatory': False, 'order': 7, 'unique': False}
        }
    
class Geography(DotDict):
    
    VALID = {
        'geographyId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'geographyContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'shortname': {'type': String40, 'mandatory': True, 'order': 1, 'unique': False},
        'comment': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 2, 'unique': True}
        }
        
class Technology(DotDict):
    
    VALID = {
        'technologyLevel': {'xml_type': 'attribute', 'type': TechnologyLevelINT, 'mandatory': True, 'order': 0, 'unique': False}, # DEFAULT
        'comment': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 1, 'unique': True}
        }

class TimePeriod(DotDict):
    
    VALID = {
        'startDate': {'xml_type': 'attribute', 'type': Date, 'mandatory': True, 'order': 0, 'unique': True},
        'endDate': {'xml_type': 'attribute', 'type': Date, 'mandatory': True, 'order': 0, 'unique': True},
        'isDataValidForEntirePeriod': {'xml_type': 'attribute', 'type': Bool, 'mandatory': True, 'order': 0, 'unique': False}, # Actualy unique, but double entry
        'comment': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 1, 'unique': True}
        }

class MacroEconomicScenario(DotDict):
    
    VALID = {
        'macroEconomicScenarioId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'macroEconomicScenarioContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'name': {'type': String80, 'mandatory': True, 'order': 1, 'unique': False},
        'comment': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
        }
           
class ActivityDescription(DotDict):
    
    VALID = {
        'activity': {'type': Activity, 'mandatory': True, 'order': 1, 'unique': True},
        'classification': {'type': ECS2Classification, 'mandatory': False, 'order': 2, 'unique': False},
        'geography': {'type': Geography, 'mandatory': True, 'order': 3, 'unique': True},
        'technology': {'type': Technology, 'mandatory': True, 'order': 4, 'unique': True},
        'timePeriod': {'type': TimePeriod, 'mandatory': True, 'order': 5, 'unique': True},
        'macroEconomicScenario': {'type': MacroEconomicScenario, 'mandatory': True, 'order': 6, 'unique': True},
        }

##########################

class Representativeness(DotDict):
    
    VALID = {
        'percent': {'xml_type': 'attribute', 'type': Percent, 'mandatory': False, 'order': 0, 'unique': True},
        'systemModelId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'systemModelContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'systemModelName': {'type': String120, 'mandatory': True, 'order': 1, 'unique': False},
        'samplingProcedure': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False},
        'extrapolations': {'type': String32000, 'mandatory': False, 'order': 3, 'unique': False}
        }

class Review(DotDict):
    
    VALID = {
        'reviewerId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
        'reviewerContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True}, 
        'reviewerName': {'xml_type': 'attribute', 'type': ReviewString, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE / can be multiple, and it is divided by /
        'reviewerEmail': {'xml_type': 'attribute', 'type': UniqueBaseString80, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
        'reviewDate': {'xml_type': 'attribute', 'type': Date, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
        'reviewedMajorRelease': {'xml_type': 'attribute', 'type': Int, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
        'reviewedMinorRelease': {'xml_type': 'attribute', 'type': Int, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
        'reviewedMajorRevision': {'xml_type': 'attribute', 'type': Int, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
        'reviewedMinorRevision': {'xml_type': 'attribute', 'type': Int, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
        'details': {'type': ECS2TextAndImage, 'mandatory': False, 'order': 1, 'unique': True},
        'otherDetails': {'type': String32000, 'mandatory': False, 'order': 2, 'unique': False}
        }

class ModellingAndValidation(DotDict):
    
    VALID = {
        'representativeness': {'type': Representativeness, 'mandatory': False, 'order': 1, 'unique': True},
        'review': {'type': Review, 'mandatory': False, 'order': 2, 'unique': False}
        }

##########################
    
class DataEntryBy(DotDict):
    
    VALID = {
        'personId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
        'personContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'isActiveAuthor': {'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE
        'personName': {'xml_type': 'attribute', 'type': UniqueBaseString40, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
        'personEmail': {'xml_type': 'attribute', 'type': UniqueBaseString80, 'mandatory': True, 'order': 0, 'unique': False} # DOUBLE
        }
    
class DataGeneratorAndPublication(DotDict):
    
    VALID = {
        'personId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
        'personContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'personName': {'xml_type': 'attribute', 'type': UniqueBaseString40, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
        'personEmail': {'xml_type': 'attribute', 'type': UniqueBaseString80, 'mandatory': True, 'order': 0, 'unique': False}, # DOUBLE
        'dataPublishedIn': {'xml_type': 'attribute', 'type': DataPublishedInINT, 'mandatory': False, 'order': 0, 'unique': True},
        'publishedSourceId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE TEST
        'publishedSourceIdOverwrittenByChild': {'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': True},
        'publishedSourceContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'publishedSourceYear': {'xml_type': 'attribute', 'type': BaseString30, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE TEST
        'publishedSourceFirstAuthor': {'xml_type': 'attribute', 'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE TEST
        'isCopyrightProtected': {'xml_type': 'attribute', 'type': Bool, 'mandatory': True, 'order': 0, 'unique': True},
        'pageNumbers': {'xml_type': 'attribute', 'type': BaseString30, 'mandatory': False, 'order': 0, 'unique': True},
        'accessRestrictedTo': {'xml_type': 'attribute', 'type': AccessRestrictedToINT, 'mandatory': False, 'order': 0, 'unique': False}, # Double
        'companyId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': False}, # Can have duplicates
        'companyIdOverwrittenByChild': {'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': True},
        'companyContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'companyCode': {'xml_type': 'attribute', 'type': CompanyCode, 'mandatory': False, 'order': 0, 'unique': False} # Can have duplicates
        }

class RequiredContextReference(DotDict):
    
    VALID = {
        'majorRelease': {'xml_type': 'attribute', 'type': Int, 'mandatory': True, 'order': 0, 'unique': False}, # Double
        'minorRelease': {'xml_type': 'attribute', 'type': Int, 'mandatory': True, 'order': 0, 'unique': False}, # Double
        'majorRevision': {'xml_type': 'attribute', 'type': Int, 'mandatory': False, 'order': 0, 'unique': False}, # Double
        'minorRevision': {'xml_type': 'attribute', 'type': Int, 'mandatory': False, 'order': 0, 'unique': False}, # Double
        'requiredContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'requiredContextFileLocation': {'xml_type': 'attribute', 'type': Str, 'mandatory': False, 'order': 0, 'unique': True},
        'requiredContextName': {'type': String80, 'mandatory': True, 'order': 1, 'unique': False}
        }
    
class FileAttributes(DotDict):
    
    VALID = {
        'majorRelease': {'xml_type': 'attribute', 'type': Int, 'mandatory': True, 'order': 0, 'unique': False}, # Double
        'minorRelease': {'xml_type': 'attribute', 'type': Int, 'mandatory': True, 'order': 0, 'unique': False}, # Double
        'majorRevision': {'xml_type': 'attribute', 'type': Int, 'mandatory': True, 'order': 0, 'unique': False}, # Double
        'minorRevision': {'xml_type': 'attribute', 'type': Int, 'mandatory': True, 'order': 0, 'unique': False}, # Double
        'internalSchemaVersion': {'xml_type': 'attribute', 'type': BaseString80, 'mandatory': False, 'order': 0, 'unique': True},
        'defaultLanguage': {'xml_type': 'attribute', 'type': Lang, 'mandatory': False, 'order': 0, 'unique': True},
        'creationTimestamp': {'xml_type': 'attribute', 'type': CompleteDate, 'mandatory': False, 'order': 0, 'unique': False}, # DOUBLE
        'lastEditTimestamp': {'xml_type': 'attribute', 'type': CompleteDate, 'mandatory': False, 'order': 0, 'unique': True},
        'fileGenerator': {'xml_type': 'attribute', 'type': BaseString255, 'mandatory': True, 'order': 0, 'unique': True},
        'fileTimestamp': {'xml_type': 'attribute', 'type': CompleteDate, 'mandatory': True, 'order': 0, 'unique': True},
        'contextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'contextName': {'type': String80, 'mandatory': False, 'order': 1, 'unique': False},
        'requiredContext': {'type': RequiredContextReference, 'mandatory': False, 'order': 2, 'unique': False}
        }
    
class AdministrativeInformation(DotDict):
    
    VALID = {
        'dataEntryBy': {'type': DataEntryBy, 'mandatory': True, 'order': 1, 'unique': True},
        'dataGeneratorAndPublication': {'type': DataGeneratorAndPublication, 'mandatory': True, 'order': 2, 'unique': True},
        'fileAttributes': {'type': FileAttributes, 'mandatory': True, 'order': 3, 'unique': True}
        }

##########################
    
class IntermediateExchange(ECS2CustomExchange, DotDict):
    
    VALID = ECS2CustomExchange.VALID | {
        'intermediateExchangeId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'intermediateExchangeContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'activityLinkId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'activityLinkIdOverwrittenByChild': {'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': True},
        'activityLinkContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'productionVolumeAmount': {'xml_type': 'attribute', 'type': Real, 'mandatory': False, 'order': 0, 'unique': True},
        'productionVolumeVariableName': {'xml_type': 'attribute', 'type': VariableName, 'mandatory': False, 'order': 0, 'unique': True},
        'productionVolumeMathematicalRelation': {'xml_type': 'attribute', 'type': BaseString32000, 'mandatory': False, 'order': 0, 'unique': True},
        'productionVolumeSourceId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'productionVolumeSourceIdOverwrittenByChild': {'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': True},
        'productionVolumeSourceContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'productionVolumeSourceYear': {'xml_type': 'attribute', 'type': BaseString30, 'mandatory': False, 'order': 0, 'unique': True},
        'productionVolumeSourceFirstAuthor': {'xml_type': 'attribute', 'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
        'productionVolumeComment': {'type': String32000, 'mandatory': False, 'order': 9, 'unique': False},
        'productionVolumeUncertainty': {'type': ECS2Uncertainty, 'mandatory': False, 'order': 10, 'unique': True},
        'classification': {'type': ECS2Classification, 'mandatory': False, 'order': 11, 'unique': False},
        'inputGroup': {'type': InputGroupIntermediateINT, 'mandatory': False, 'order': 12, 'unique': True},
        'outputGroup': {'type': OutputGroupIntermediateINT, 'mandatory': False, 'order': 13},
        }

class Compartment(DotDict):
    
    VALID = {
        'subcompartmentId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'subcompartmentContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'compartment': {'type': String40, 'mandatory': True, 'order': 1, 'unique': False},
        'subcompartment': {'type': String40, 'mandatory': True, 'order': 2, 'unique': False}
        }
    
class ElementaryExchange(DotDict):
    
    VALID = ECS2CustomExchange.VALID | {
        'elementaryExchangeId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'elementaryExchangeContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'formula': {'xml_type': 'attribute', 'type': BaseString40, 'mandatory': False, 'order': 0, 'unique': True},
        'compartment': {'type': Compartment, 'mandatory': True, 'order': 9, 'unique': True},
        'inputGroup': {'type': InputGroupElementaryINT, 'mandatory': False, 'order': 10},
        'outputGroup': {'type': OutputGroupElementaryINT, 'mandatory': False, 'order': 11}
        }
                
class Parameter(DotDict):
    
    VALID = ECS2QuantitativeReferenceWithUnit.VALID_NO_SOURCE | {
        'parameterId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'parameterContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True}
        }
    
class ImpactIndicator(DotDict):
    
    VALID = {
        'impactIndicatorId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'impactIndicatorContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'impactMethodId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'impactMethodContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'impactCategoryId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': True, 'order': 0, 'unique': True},
        'impactCategoryContextId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'amount': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True},
        'impactMethodName': {'type': String120, 'mandatory': True, 'order': 1, 'unique': False},
        'impactCategoryName': {'type': String120, 'mandatory': True, 'order': 2, 'unique': False},
        'name': {'type': String120, 'mandatory': True, 'order': 3, 'unique': False},
        'unitName': {'type': String40, 'mandatory': True, 'order': 4, 'unique': False}
        }
    
class FlowData(DotDict):
    
    VALID = {
        'intermediateExchange': {'type': IntermediateExchange, 'mandatory': True, 'order': 1, 'unique': False},
        'elementaryExchange': {'type': ElementaryExchange, 'mandatory': False, 'order': 2, 'unique': False},
        'parameter': {'type': Parameter, 'mandatory': False, 'order': 3, 'unique': False},
        'impactIndicator': {'type': ImpactIndicator, 'mandatory': False, 'order': 4, 'unique': False}
        }

##########################

class ECS2Structure(StructureTemplate):
    
    convert_user_data = True
    
    def __init__(self):
        self.activityDescription = ActivityDescription()
        self.flowData = FlowData()
        self.modellingAndValidation = ModellingAndValidation()
        self.administrativeInformation = AdministrativeInformation()
        
        self.textAndImage = ECS2TextAndImage
        self.property = ECS2CustomExchange()
        self.userMaster = ECS2UsedUserMasterData()
        
        # User master (testing)
        self.activityNameMaster = ActivityNameMaster
        self.classificationSystemMaster = ClassificationSystemMaster
        self.companyMaster = CompanyMaster
        self.compartmentMaster = CompartmentMaster
        self.elementaryMaster = ElementaryMaster
        self.geographyMaster = GeographyMaster
        self.intermediateMaster = IntermediateMaster
        self.languageMaster = LanguageMaster
        self.macroEconomicScenarioMaster = MacroEconomicScenarioMaster
        self.parameterMaster = ParameterMaster
        self.personMaster = PersonMaster
        self.propertyMaster = PropertyMaster
        self.unitMaster = UnitMaster
        self.sourceMaster = SourceMaster
        self.systemModelMaster = SystemModelMaster
        self.tagMaster = TagMaster
        self.activityIndexEntryMaster = ActivityIndexEntryMaster
        
        # Useful for testing
        self.uncertainty = ECS2Uncertainty
        self.source = ECS2Source
        self.quantitativeReference = ECS2QuantitativeReference
        self.quantitativeReferenceWithUnit = ECS2QuantitativeReferenceWithUnit
        self.classification = ECS2Classification
        self.customExchange = ECS2CustomExchange
        self.property_intern = ECS2Property
        
        self.main_activity_type = 'activityDataset'
        
    def get_filename(self, hash_):
        ads = self.activityDescription
        name = f"{ads.activity.get('activityName')['#text']}, "+\
            f"{ads.geography.get('shortname')[0]['#text']}, "+\
            f"{ads.timePeriod.get('startDate')[:4]} - {ads.timePeriod.get('endDate')[:4]}"+\
            f"{hash_}"
        return name.replace('/', ' per ')
        
    def get_dict(self):
        return {
            'ecoSpold': {
                '@xmlns': 'http://www.EcoInvent.org/EcoSpold02',
                'activityDataset': { # self.main_activity_type [child datasets are not accept by ecoeditor]
                    'activityDescription': self.activityDescription.get_dict(),
                    'flowData': self.flowData.get_dict(),
                    'modellingAndValidation': self.modellingAndValidation.get_dict(),
                    'administrativeInformation': self.administrativeInformation.get_dict()
                    },
                **({'usedUserMasterData': {
                    '@xmlns': 'http://www.EcoInvent.org/UsedUserMasterData',
                    **self.userMaster.get_dict()
                    }} if type(self).convert_user_data else {})
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
        'identifierOfSubDataSet': {'type': Str, 'mandatory': False},
        'complementingProcesses': {'type': LIST, 'mandatory': False},
        'functionalUnitOrOther': {'type': LIST, 'mandatory': False},
        'type': {'type': Str, 'mandatory': False},
        'latitudeAndLongitude': {'type': Str, 'mandatory': False},
        'subLocationOfOperationSupplyOrProduction': {'type': LIST, 'mandatory': False},
        'referenceToIncludedProcesses': {'type': LIST, 'mandatory': False},
        'LCIMethodPrinciple': {'type': Str, 'mandatory': False},
        'referenceToLCAMethodDetails': {'type': LIST, 'mandatory': False},
        'referenceToDataHandlingPrinciples': {'type': LIST, 'mandatory': False},
        'referenceToDataSource': {'type': LIST, 'mandatory': False},
        'annualSupplyOrProductionVolume': {'type': LIST, 'mandatory': False},
        'completeness': {'type': LIST, 'mandatory': False},
        'compliance': {'type': LIST, 'mandatory': False},
        'commissionerAndGoal': {'type': LIST, 'mandatory': False},
        'timeStamp': {'type': Str, 'mandatory': False},
        'referenceToDataSetFormat': {'type': LIST, 'mandatory': False},
        'referenceToConvertedOriginalDataSetFrom': {'type': LIST, 'mandatory': False},
        'referenceToDataSetUseApproval': {'type': LIST, 'mandatory': False},
        'dateOfLastRevision': {'type': Str, 'mandatory': False},
        'referenceToPrecedingDataSetVersion': {'type': LIST, 'mandatory': False},
        'permanentDataSetURI': {'type': Str, 'mandatory': False},
        'referenceToRegistrationAuthority': {'type': LIST, 'mandatory': False},
        'registrationNumber': {'type': Str, 'mandatory': False},
        'referenceToOwnershipOfDataSet': {'type': LIST, 'mandatory': False},
        'accessRestrictions': {'type': Str, 'mandatory': False},
    }

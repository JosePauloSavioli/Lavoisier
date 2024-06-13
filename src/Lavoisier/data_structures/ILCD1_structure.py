#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  7 05:29:17 2022

@author: jotape42p
"""

from .main import DotDict
from .abstractions import StructureTemplate
from .validators.enumerations import (
    GlobalReferenceTypeValues,
    UncertaintyDistributionTypeValues,
    DataDerivationTypeStatusValues,
    TypeOfQuantitativeReferenceValues,
    TypeOfProcessValues,
    LCIMethodPrincipleValues,
    LCIMethodApproachesValues,
    CompletenessTypeValues,
    CompletenessValues,
    MethodOfReviewValues,
    ScopeOfReviewValues,
    DataQualityIndicatorValues,
    QualityValues,
    TypeOfReviewValues,
    ComplianceValues,
    WorkflowAndPublicationStatusValues,
    LicenseTypeValues,
    ExchangeFunctionTypeValues,
    ExchangeDirectionValues,
    DataSourceTypeValues
    )
from .validators.general_validators import (
    Validator,
    list_add,
    return_enum,
    Real,
    Bool,
    Int,
    UUID,
    Str
    )
from .validators.ILCD1_validators import (
    Int1,
    Int6, Int6List,
    Year,
    Version,
    GIS,
    DateTime,
    ReviewDateTime,
    String,
    NullableString,
    MatV,
    STMultiLang,
    StringMultiLang,
    FTMultiLang
    )

### GENERAL StrUCTURES

class ILCD1Reference(DotDict):

    VALID = {
        'type': {'xml_type': 'attribute', 'type': return_enum(GlobalReferenceTypeValues), 'mandatory': True, 'order': 0, 'unique': True},
        'refObjectId': {'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'version': {'xml_type': 'attribute', 'type': Version, 'mandatory': False, 'order': 0, 'unique': True},
        'uri': {'xml_type': 'attribute', 'type': Str, 'mandatory': False, 'order': 0, 'unique': True}, # anyURI
        'subReference': {'xml_type': 'nms:common', 'type': String, 'mandatory': False, 'order': 1},
        'shortDescription': {'xml_type': 'nms:common', 'type': STMultiLang, 'mandatory': False, 'order': 2}
    }

class ILCD1Classification(DotDict):

    class __Class(DotDict):
        
        VALID = {
            'level': {'xml_type': 'attribute', 'type': Int1, 'mandatory': True, 'order': 0, 'unique': True},
            'classId': {'xml_type': 'attribute', 'type': Str, 'mandatory': True, 'order': 0, 'unique': True},
            'text': {'xml_type': 'text', 'type': String, 'mandatory': True, 'order': 0}  # It has a text
        }

    VALID = {
        'name': {'xml_type': 'attribute', 'type': Str, 'mandatory': False, 'order': 0, 'unique': True}, # Actualy mandatory, but not for OpenLCA
        'classes': {'xml_type': 'attribute', 'type': Str, 'mandatory': False, 'order': 0, 'unique': True}, # anyURI, Actualy mandatory, but not for OpenLCA
        'class': {'xml_type': 'nms:common', 'type': __Class, 'mandatory': True, 'order': 1}
    }

class ILCD1FlowProperty(DotDict): # [!] FlowDataSets can have a location, how to transcrible it from ECS2?

    VALID = {
        'dataSetInternalID': {'xml_type': 'attribute', 'type': Int6, 'mandatory': True, 'order': 0, 'unique': True},
        'referenceToFlowPropertyDataSet': {'type': ILCD1Reference, 'mandatory': True, 'order': 1, 'unique': True},
        'meanValue': {'type': Real, 'mandatory': True, 'order': 2, 'unique': True},
        'minimumValue': {'type': Real, 'mandatory': False, 'order': 3, 'unique': True},
        'maximumValue': {'type': Real, 'mandatory': False, 'order': 4, 'unique': True},
        'uncertaintyDistributionType': {'type': return_enum(UncertaintyDistributionTypeValues), 'mandatory': False, 'order': 5, 'unique': True},
        'relativeStandardDeviation95In': {'type': Real, 'mandatory': False, 'order': 6, 'unique': True}, # [!] Perc
        'dataDerivationTypeStatus': {'type': return_enum(DataDerivationTypeStatusValues), 'mandatory': False, 'order': 7, 'unique': True},
        'generalComment': {'type': StringMultiLang, 'mandatory': False, 'order': 16}
    }

### MAIN StrUCTURE

##########################

class Name(DotDict):
    
    VALID = {
        'baseName': {'type': StringMultiLang, 'mandatory': True, 'order': 1},
        'treatmentStandardsRoutes': {'type': StringMultiLang, 'mandatory': False, 'order': 2},
        'mixAndLocationTypes': {'type': StringMultiLang, 'mandatory': False, 'order': 3},
        'functionalUnitFlowProperties': {'type': StringMultiLang, 'mandatory': False, 'order': 4}
    }

class ComplementingProcesses(DotDict):
    
    VALID = {
        'referenceToComplementingProcess': {'type': ILCD1Reference, 'mandatory': True, 'order': 1}
    }
    
class ClassificationInformation(DotDict):
    
    VALID = {
        'classification': {'xml_type': 'nms:common', 'type': ILCD1Classification, 'mandatory': False, 'order': 1}
    }
        
class DataSetInformation(DotDict):
    
    VALID = {
        'UUID': {'xml_type': 'nms:common', 'type': UUID, 'mandatory': True, 'order': 1, 'unique': True},
        'name': {'type': Name, 'mandatory': False, 'order': 2, 'unique': True},
        'identifierOfSubDataSet': {'type': String, 'mandatory': False, 'order': 3, 'unique': True},
        'synonyms': {'xml_type': 'nms:common', 'type': FTMultiLang, 'mandatory': False, 'order': 4},
        'complementingProcesses': {'type': ComplementingProcesses, 'mandatory': False, 'order': 5, 'unique': True},
        'classificationInformation': {'type': ClassificationInformation, 'mandatory': False, 'order': 6, 'unique': True},
        'generalComment': {'xml_type': 'nms:common', 'type': FTMultiLang, 'mandatory': False, 'order': 7},
        'referenceToExternalDocumentation': {'type': ILCD1Reference, 'mandatory': False, 'order': 8}
    }

##########################

class QuantitativeReference(DotDict): # Optional

    VALID = {
        'type': {'xml_type': 'attribute', 'type': return_enum(TypeOfQuantitativeReferenceValues), 'mandatory': True, 'order': 0, 'unique': True},
        'referenceToReferenceFlow': {'type': Int6List, 'mandatory': False, 'order': 1},
        'functionalUnitOrOther': {'type': StringMultiLang, 'mandatory': False, 'order': 2}
    }
    
##########################

class Time(DotDict):

    VALID = {
        'referenceYear': {'xml_type': 'nms:common', 'type': Year, 'mandatory': False, 'order': 1, 'unique': True},
        'dataSetValidUntil': {'xml_type': 'nms:common', 'type': Year, 'mandatory': False, 'order': 2, 'unique': True},
        'timeRepresentativenessDescription': {'xml_type': 'nms:common', 'type': FTMultiLang, 'mandatory': False, 'order': 3}
    }
   
class OLCATime(DotDict):

    VALID = Time.VALID | {
        'startDate': {'xml_nms': 'olca', 'xml_type': 'attribute', 'type': Int, 'mandatory': False, 'order': 0, 'unique': True},
        'endDate': {'xml_nms': 'olca', 'xml_type': 'attribute', 'type': Int, 'mandatory': False, 'order': 0, 'unique': True}
    }
    
##########################
    
class LocationOfOperationSupplyOrProduction(DotDict):

    VALID = {
        'location': {'xml_type': 'attribute', 'type': NullableString, 'mandatory': True, 'order': 0, 'unique': True},
        'latitudeAndLongitude': {'xml_type': 'attribute', 'type': GIS, 'mandatory': False, 'order': 0, 'unique': True},
        'descriptionOfRestrictions': {'type': FTMultiLang, 'mandatory': False, 'order': 1}
    }

class SubLocationOfOperationSupplyOrProduction(DotDict):

    VALID = {
        'subLocation': {'xml_type': 'attribute', 'type': String, 'mandatory': False, 'order': 0, 'unique': True},
        'latitudeAndLongitude': {'xml_type': 'attribute', 'type': GIS, 'mandatory': False, 'order': 0, 'unique': True},
        'descriptionOfRestrictions': {'type': FTMultiLang, 'mandatory': False, 'order': 1}
    }

class Geography(DotDict):

    VALID = {
        'locationOfOperationSupplyOrProduction': {'type': LocationOfOperationSupplyOrProduction, 'mandatory': False, 'order': 1, 'unique': True},
        'subLocationOfOperationSupplyOrProduction': {'type': SubLocationOfOperationSupplyOrProduction, 'mandatory': False, 'order': 2}
    }
    
##########################

class Technology(DotDict):

    VALID = {
        'technologyDescriptionAndIncludedProcesses': {'type': FTMultiLang, 'mandatory': False, 'order': 1},
        'referenceToIncludedProcesses': {'type': ILCD1Reference, 'mandatory': False, 'order': 2},
        'technologicalApplicability': {'type': FTMultiLang, 'mandatory': False, 'order': 3},
        'referenceToTechnologyPictogramme': {'type': ILCD1Reference, 'mandatory': False, 'order': 4, 'unique': True},
        'referenceToTechnologyFlowDiagrammOrPicture': {'type': ILCD1Reference, 'mandatory': False, 'order': 5}
    }
    
##########################
        
class VariableParameter(DotDict):

    VALID = {
        'name': {'xml_type': 'attribute', 'type': MatV, 'mandatory': True, 'order': 0, 'unique': True},
        'formula': {'type': Str, 'mandatory': False, 'order': 1, 'unique': True},
        'meanValue': {'type': Real, 'mandatory': False, 'order': 2, 'unique': True},
        'minimumValue': {'type': Real, 'mandatory': False, 'order': 3, 'unique': True},
        'maximumValue': {'type': Real, 'mandatory': False, 'order': 4, 'unique': True},
        'uncertaintyDistributionType': {'type': return_enum(UncertaintyDistributionTypeValues), 'mandatory': False, 'order': 5, 'unique': True},
        'relativeStandardDeviation95In': {'type': Real, 'mandatory': False, 'order': 6, 'unique': True},
        'comment': {'type': StringMultiLang, 'mandatory': False, 'order': 7}
    }

class OLCAVariableParameter(DotDict):
    
    VALID = VariableParameter.VALID | {
        'scope': {'xml_nms': 'olca', 'xml_type': 'attribute', 'type': String, 'mandatory': False, 'order': 0, 'unique': True}
        }

class MathematicalRelations(DotDict):

    VALID = {
        'modelDescription': {'type': FTMultiLang, 'mandatory': False, 'order': 1},
        'variableParameter': {'type': VariableParameter, 'mandatory': False, 'order': 2}
    }
    
class OLCAMathematicalRelations(DotDict):

    VALID = MathematicalRelations.VALID | {
        'variableParameter': {'type': OLCAVariableParameter, 'mandatory': False, 'order': 2}
    }
    
##########################

class LCIMethodAndAllocation(DotDict):

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

class DataSourcesTreatmentAndRepresentativeness(DotDict):

    VALID = {
        'dataCutOffAndCompletenessPrinciples': {'type': FTMultiLang, 'mandatory': False, 'order': 1},
        'deviationsFromCutOffAndCompletenessPrinciples': {'type': FTMultiLang, 'mandatory': False, 'order': 2},
        'dataSelectionAndCombinationPrinciples': {'type': FTMultiLang, 'mandatory': False, 'order': 3},
        'deviationsFromSelectionAndCombinationPrinciples': {'type': FTMultiLang, 'mandatory': False, 'order': 4},
        'dataTreatmentAndExtrapolationsPrinciples': {'type': FTMultiLang, 'mandatory': False, 'order': 5},
        'deviationsFromTreatmentAndExtrapolationPrinciples': {'type': FTMultiLang, 'mandatory': False, 'order': 6},
        'referenceToDataHandlingPrinciples': {'type': ILCD1Reference, 'mandatory': False, 'order': 7},
        'referenceToDataSource': {'type': ILCD1Reference, 'mandatory': False, 'order': 8},
        'percentageSupplyOrProductionCovered': {'type': Real, 'mandatory': False, 'order': 9, 'unique': True},
        'annualSupplyOrProductionVolume': {'type': StringMultiLang, 'mandatory': False, 'order': 10},
        'samplingProcedure': {'type': FTMultiLang, 'mandatory': False, 'order': 11},
        'dataCollectionPeriod': {'type': StringMultiLang, 'mandatory': False, 'order': 12},
        'uncertaintyAdjustments': {'type': FTMultiLang, 'mandatory': False, 'order': 13},
        'useAdviceForDataSet': {'type': FTMultiLang, 'mandatory': False, 'order': 14}
    }

class CompletenessElementaryFlows(DotDict):

    VALID = {
        'type': {'xml_type': 'attribute', 'type': return_enum(CompletenessTypeValues), 'mandatory': True, 'order': 0, 'unique': True},
        'value': {'xml_type': 'attribute', 'type': return_enum(CompletenessValues), 'mandatory': True, 'order': 0, 'unique': True}
    }
    
class Completeness(DotDict):

    VALID = {
        'completenessProductModel': {'type': return_enum(CompletenessValues, list_=True), 'mandatory': False, 'order': 1},
        'referenceToSupportedImpactAssessmentMethods': {'type': ILCD1Reference, 'mandatory': False, 'order': 2},
        'completenessElementaryFlows': {'type': CompletenessElementaryFlows, 'mandatory': False, 'order': 3},
        'completenessOtherProblemField': {'type': FTMultiLang, 'mandatory': False, 'order': 4}
    }

class Method(DotDict):

    VALID = {
        'name': {'xml_type': 'attribute', 'type': return_enum(MethodOfReviewValues), 'mandatory': True, 'order': 0, 'unique': True}
    }

class Scope(DotDict):

    VALID = {
        'name': {'xml_type': 'attribute', 'type': return_enum(ScopeOfReviewValues), 'mandatory': True, 'order': 0, 'unique': True},
        'method': {'xml_type': 'nms:common', 'type': Method, 'mandatory': False, 'order': 1}
    }

class DataQualityIndicator(DotDict):

    VALID = {
        'name': {'xml_type': 'attribute', 'type': return_enum(DataQualityIndicatorValues), 'mandatory': True, 'order': 0, 'unique': True},
        'value': {'xml_type': 'attribute', 'type': return_enum(QualityValues), 'mandatory': True, 'order': 0, 'unique': True}
    }
    
class DataQualityIndicators(DotDict):

    VALID = {
        'dataQualityIndicator': {'xml_type': 'nms:common', 'type': DataQualityIndicator, 'mandatory': True, 'order': 1}
    }

class Review(DotDict):

    VALID = {
        'type': {'xml_type': 'attribute', 'type': return_enum(TypeOfReviewValues), 'mandatory': False, 'order': 0, 'unique': True},
        'scope': {'xml_type': 'nms:common', 'type': Scope, 'mandatory': False, 'order': 1},
        'dataQualityIndicators': {'xml_type': 'nms:common', 'type': DataQualityIndicators, 'mandatory': False, 'order': 2, 'unique': True},
        'reviewDetails': {'xml_type': 'nms:common', 'type': FTMultiLang, 'mandatory': False, 'order': 3},
        'referenceToNameOfReviewerAndInstitution': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 4},
        'otherReviewDetails': {'xml_type': 'nms:common', 'type': FTMultiLang, 'mandatory': False, 'order': 5},
        'referenceToCompleteReviewReport': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 6, 'unique': True}
    }

class Validation(DotDict):

    VALID = {
        'review': {'type': Review, 'mandatory': False, 'order': 1}
    }

class Compliance(DotDict):

    VALID = {
        'referenceToComplianceSystem': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': True, 'order': 1, 'unique': True},
        'approvalOfOverallCompliance': {'xml_type': 'nms:common', 'type': return_enum(ComplianceValues), 'mandatory': False, 'order': 2, 'unique': True},
        'nomenclatureCompliance': {'xml_type': 'nms:common', 'type': return_enum(ComplianceValues), 'mandatory': False, 'order': 3, 'unique': True},
        'methodologicalCompliance': {'xml_type': 'nms:common', 'type': return_enum(ComplianceValues), 'mandatory': False, 'order': 4, 'unique': True},
        'reviewCompliance': {'xml_type': 'nms:common', 'type': return_enum(ComplianceValues), 'mandatory': False, 'order': 5, 'unique': True},
        'documentationCompliance': {'xml_type': 'nms:common', 'type': return_enum(ComplianceValues), 'mandatory': False, 'order': 6, 'unique': True},
        'qualityCompliance': {'xml_type': 'nms:common', 'type': return_enum(ComplianceValues), 'mandatory': False, 'order': 7, 'unique': True}
    }

class ComplianceDeclarations(DotDict):

    VALID = {
        'compliance': {'type': Compliance, 'mandatory': True, 'order': 1}
    }

class ModellingAndValidation(DotDict):

    VALID = {
        'LCIMethodAndAllocation': {'type': LCIMethodAndAllocation, 'mandatory': False, 'order': 1, 'unique': True},
        'dataSourcesTreatmentAndRepresentativeness': {'type': DataSourcesTreatmentAndRepresentativeness, 'mandatory': False, 'order': 2, 'unique': True},
        'completeness': {'type': Completeness, 'mandatory': False, 'order': 3, 'unique': True},
        'validation': {'type': Validation, 'mandatory': False, 'order': 4, 'unique': True},
        'complianceDeclarations': {'type': ComplianceDeclarations, 'mandatory': False, 'order': 5, 'unique': True}
    }
    
##########################

class CommissionerAndGoal(DotDict):

    VALID = {
        'referenceToCommissioner': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 1},
        'project': {'xml_type': 'nms:common', 'type': StringMultiLang, 'mandatory': False, 'order': 2},
        'intendedApplications': {'xml_type': 'nms:common', 'type': FTMultiLang, 'mandatory': False, 'order': 3}
    }

class DataGenerator(DotDict):

    VALID = {
        'referenceToPersonOrEntityGeneratingTheDataSet': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 1}
    }

class DataEntryBy(DotDict):

    VALID = {
        'timeStamp': {'xml_type': 'nms:common', 'type': DateTime, 'mandatory': False, 'order': 1, 'unique': True},
        'referenceToDataSetFormat': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 2},
        'referenceToConvertedOriginalDataSetFrom': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 3, 'unique': True},
        'referenceToPersonOrEntityEnteringTheData': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 4, 'unique': True},
        'referenceToDataSetUseApproval': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 5}
    }

class PublicationAndOwnership(DotDict):

    VALID = {
        'dateOfLastRevision': {'xml_type': 'nms:common', 'type': ReviewDateTime, 'mandatory': False, 'order': 1}, # 'unique': True but can be overwritten in ECS2
        'dataSetVersion': {'xml_type': 'nms:common', 'type': Version, 'mandatory': True, 'order': 2, 'unique': True},
        'referenceToPrecedingDataSetVersion': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 3},
        'permanentDataSetURI': {'xml_type': 'nms:common', 'type': Str, 'mandatory': False, 'order': 4, 'unique': True},
        'workflowAndPublicationStatus': {'xml_type': 'nms:common', 'type': return_enum(WorkflowAndPublicationStatusValues), 'mandatory': False, 'order': 5, 'unique': True},
        'referenceToUnchangedRepublication': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 6, 'unique': True},
        'referenceToRegistrationAuthority': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 7, 'unique': True},
        'registrationNumber': {'xml_type': 'nms:common', 'type': String, 'mandatory': False, 'order': 8, 'unique': True},
        'referenceToOwnershipOfDataSet': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 9, 'unique': True},
        'copyright': {'xml_type': 'nms:common', 'type': Bool, 'mandatory': False, 'order': 10, 'unique': True},
        'referenceToEntitiesWithExclusiveAccess': {'xml_type': 'nms:common', 'type': ILCD1Reference, 'mandatory': False, 'order': 11},
        'licenseType': {'xml_type': 'nms:common', 'type': return_enum(LicenseTypeValues), 'mandatory': False, 'order': 12}, # 'unique': True but can override the default in ECS2
        'accessRestrictions': {'xml_type': 'nms:common', 'type': FTMultiLang, 'mandatory': False, 'order': 13}
    }

class AdministrativeInformation(DotDict):

    VALID = {
        'commissionerAndGoal': {'xml_type': 'nms:common', 'type': CommissionerAndGoal, 'mandatory': False, 'order': 1, 'unique': True},
        'dataGenerator': {'type': DataGenerator, 'mandatory': False, 'order': 2, 'unique': True},
        'dataEntryBy': {'type': DataEntryBy, 'mandatory': False, 'order': 3, 'unique': True},
        'publicationAndOwnership': {'type': PublicationAndOwnership, 'mandatory': False, 'order': 4, 'unique': True}
    }
    
##########################

class Allocation(DotDict):

    VALID = {
        'internalReferenceToCoProduct': {'xml_type': 'attribute', 'type': Int6, 'mandatory': True, 'order': 0, 'unique': True},
        'allocatedFraction': {'xml_type': 'attribute', 'type': Real, 'mandatory': True, 'order': 0, 'unique': True}
    }

class Allocations(DotDict):

    VALID = {
        'allocation': {'type': Allocation, 'mandatory': True, 'order': 1}
    }

class ReferencesToDataSource(DotDict):

    VALID = {
        'referenceToDataSource': {'type': ILCD1Reference, 'mandatory': False, 'order': 1}
    }

class Exchange(DotDict):

    VALID = {
        'dataSetInternalID': {'xml_type': 'attribute', 'type': Int6, 'mandatory': True, 'order': 0, 'unique': True},
        'referenceToFlowDataSet': {'type': ILCD1Reference, 'mandatory': True, 'order': 1, 'unique': True},
        'location': {'type': String, 'mandatory': False, 'order': 2, 'unique': True},
        'functionType': {'type': return_enum(ExchangeFunctionTypeValues), 'mandatory': False, 'order': 3, 'unique': True},
        'exchangeDirection': {'type': return_enum(ExchangeDirectionValues), 'mandatory': False, 'order': 4, 'unique': True},
        'referenceToVariable': {'type': Str, 'mandatory': False, 'order': 5, 'unique': True},
        'meanAmount': {'type': Real, 'mandatory': True, 'order': 6}, # DOUBLE
        'resultingAmount': {'type': Real, 'mandatory': False, 'order': 7}, # DOUBLE
        'minimumAmount': {'type': Real, 'mandatory': False, 'order': 8}, # DOUBLE
        'maximumAmount': {'type': Real, 'mandatory': False, 'order': 9}, # DOUBLE
        'uncertaintyDistributionType': {'type': return_enum(UncertaintyDistributionTypeValues), 'mandatory': False, 'order': 10}, # DOUBLE
        'relativeStandardDeviation95In': {'type': Real, 'mandatory': False, 'order': 11}, # DOUBLE
        'allocations': {'type': Allocations, 'mandatory': False, 'order': 12, 'unique': True},
        'dataSourceType': {'type': return_enum(DataSourceTypeValues), 'mandatory': False, 'order': 13, 'unique': True},
        'dataDerivationTypeStatus': {'type': return_enum(DataDerivationTypeStatusValues), 'mandatory': False, 'order': 14, 'unique': True},
        'referencesToDataSource': {'type': ReferencesToDataSource, 'mandatory': False, 'order': 15, 'unique': True},
        'generalComment': {'type': StringMultiLang, 'mandatory': False, 'order': 16}
    }

class OLCAExchange(DotDict):
    
    VALID = Exchange.VALID | {
        'formula': {'xml_nms': 'olca', 'xml_type': 'attribute', 'type': String, 'mandatory': False, 'order': 0, 'unique': True},
        'unitId': {'xml_nms': 'olca', 'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'propertyId': {'xml_nms': 'olca', 'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True},
        'amount': {'xml_nms': 'olca', 'xml_type': 'attribute', 'type': Real, 'mandatory': False, 'order': 0, 'unique': True},
        'pedigreeUncertainty': {'xml_nms': 'olca', 'xml_type': 'attribute', 'type': String, 'mandatory': False, 'order': 0, 'unique': True},
        'baseUncertainty': {'xml_nms': 'olca', 'xml_type': 'attribute', 'type': String, 'mandatory': False, 'order': 0, 'unique': True},
        'mostLikelyValue': {'xml_nms': 'olca', 'xml_type': 'attribute', 'type': Real, 'mandatory': False, 'order': 0, 'unique': True},
        'avoidedProduct': {'xml_nms': 'olca', 'xml_type': 'attribute', 'type': Bool, 'mandatory': False, 'order': 0, 'unique': True},
        'defaultProvider': {'xml_nms': 'olca', 'xml_type': 'attribute', 'type': UUID, 'mandatory': False, 'order': 0, 'unique': True}
        }

class Exchanges(DotDict):

    VALID = {
        'exchange': {'type': Exchange, 'mandatory': False, 'order': 1}
    }
    
class OLCAExchanges(DotDict):

    VALID = {
        'exchange': {'type': OLCAExchange, 'mandatory': False, 'order': 1}
    }
    
##########################

class ILCD1Structure(StructureTemplate):
    
    # [!] LCIAResults are not considered here
    # [!] The processDataSet @version will have to be specified in future
    
    def __init__(self):
        self.dataSetInformation = DataSetInformation()
        self.quantitativeReference = QuantitativeReference()
        self.time = Time()
        self.technology = Technology()
        self.geography = Geography()
        self.modellingAndValidation = ModellingAndValidation()
        self.administrativeInformation = AdministrativeInformation()
        self.mathematicalRelations = MathematicalRelations()
        self.exchanges = Exchanges()
        
        self.flow_property = ILCD1FlowProperty
        self.classification = ILCD1Classification
        self.reference = ILCD1Reference
        
    def get_filename(self, hash_):
        base_name = self.dataSetInformation['name'].get('baseName')
        geo = self.geography['locationOfOperationSupplyOrProduction']
        name = f"{base_name[0]['#text'] if isinstance(base_name, list) else base_name['#text']}, "+\
            f"{geo.get('location')}, "+\
            f"{self.time.get('referenceYear')} - {self.time.get('dataSetValidUntil')}"+\
            f"{hash_}"
        return name.replace('/', ' per ')
        
    def get_dict(self):
        return {
            'processDataSet': {
                '@xmlns': 'http://lca.jrc.it/ILCD/Process',
                '@xmlns:common': 'http://lca.jrc.it/ILCD/Common',
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

class OLCAILCD1Structure(ILCD1Structure):
    # https://www.javatips.net/api/olca-modules-master/olca-ilcd/src/main/java/org/openlca/ilcd/util/ProcessInfoExtension.java
    # ilcd/util/filesThatEndWithExtension
    
    DataSetInformation = DataSetInformation
    QuantitativeReference = QuantitativeReference
    Time = OLCATime
    Technology = Technology
    Geography = Geography
    ModellingAndValidation = ModellingAndValidation
    AdministrativeInformation = AdministrativeInformation
    
    def __init__(self):
        super().__init__()
        self.exchanges = OLCAExchanges()
        self.mathematicalRelations = OLCAMathematicalRelations()
        self.time = OLCATime()
    
    def get_dict(self):
        p = super().get_dict()
        p['processDataSet']['@xmlns:olca'] = 'http://openlca.org/ilcd-extensions'
        return p

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
                'id': {'type': Str, 'mandatory': True},
                'amount': {'type': Real, 'mandatory': False},
                'unitId': {'type': Str, 'mandatory': False},
                'variableName': {'type': Str, 'mandatory': False},
                'mathematicalRelation': {'type': Str, 'mandatory': False},
                'propertyContextId': {'type': Str, 'mandatory': False},
                'isDefiningValue': {'type': Bool, 'mandatory': False},
                'isCalculatedAmount': {'type': Bool, 'mandatory': False},
                'unitContextId': {'type': Str, 'mandatory': False},
                'sourceIdOverwrittenByChild': {'type': Str, 'mandatory': False},
                'sourceContextId': {'type': Str, 'mandatory': False}
            }

        class ProductionVolume(DotDict):

            VALID = {
                'productionVolumeSourceIdOverwrittenByChild': {'type': Str, 'mandatory': False},
                'productionVolumeSourceContextId': {'type': Str, 'mandatory': False}
            }

        VALID = {
            'id': {'type': Str, 'mandatory': True},
            'classification': {'type': LIST, 'mandatory': False},
            'fId': {'type': Str, 'mandatory': False},
            'tag': {'type': LIST, 'mandatory': False},
            'unitContextId': {'type': Str, 'mandatory': False},
            'isCalculatedAmount': {'type': Bool, 'mandatory': False},
            'sourceIdOverwrittenByChild': {'type': Bool, 'mandatory': False},
            'specificAllocationPropertyIdOverwrittenByChild': {'type': Str, 'mandatory': False},
            'specificAllocationPropertyContextId': {'type': Str, 'mandatory': False},
            'transferCoefficient': {'type': LIST, 'mandatory': False},
            'properties': {'type': Property, 'mandatory': True},
            'uncertainty': {'type': LIST, 'mandatory': False},
            'productionVolume': {'type': ProductionVolume, 'mandatory': True},
            'activityLinkIdOverwrittenByChild': {'type': Bool, 'mandatory': False},
            'intermediateExchangeContextId': {'type': Str, 'mandatory': False},
            'elementaryExchangeContextId': {'type': Str, 'mandatory': False},
            'activityLinkContextId': {'type': Str, 'mandatory': False}
        }

    class Parameter(DotDict):

        VALID = {
            'amount': {'type': Real, 'mandatory': False},
            'parameterContextId': {'type': Str, 'mandatory': False},
            'isCalculatedAmount': {'type': Bool, 'mandatory': False},
            'unitContextId': {'type': Str, 'mandatory': False}
        }

    VALID = {
        'activityNameId': {'type': Str, 'mandatory': True},
        'activityNameContextId': {'type': Str, 'mandatory': False},
        'parentActivityId': {'type': Str, 'mandatory': False},
        'parentActivityContextId': {'type': Str, 'mandatory': False},
        'inheritanceDepth': {'type': Str, 'mandatory': False},
        'specialActivityType': {'type': Str, 'mandatory': True},
        'masterAllocationPropertyId': {'type': Str, 'mandatory': True},
        'masterAllocationPropertyIdOverwrittenByChild': {'type': Str, 'mandatory': False},
        'masterAllocationPropertyContextId': {'type': Str, 'mandatory': False},
        'tag': {'type': LIST, 'mandatory': False},
        'geographyId': {'type': Str, 'mandatory': True},
        'geographyContextId': {'type': Str, 'mandatory': False},
        'technologyLevel': {'type': Str, 'mandatory': False},
        'isDataValidForEntirePeriod': {'type': Bool, 'mandatory': True},
        'macroEconomicScenarioId': {'type': Str, 'mandatory': True},
        'macroEconomicScenarioContextId': {'type': Str, 'mandatory': False},
        'macroEconomicScenario_name': {'type': Str, 'mandatory': True},
        'macroEconomicScenario_comment': {'type': LIST, 'mandatory': False},
        'classificationContext': {'type': LIST, 'mandatory': False},
        'systemModelId': {'type': Str, 'mandatory': True},
        'systemModelContextId': {'type': Str, 'mandatory': False},
        'review': {'type': LIST, 'mandatory': False},
        'dataEntryBy_personContextId': {'type': Str, 'mandatory': False},
        'dataGeneratorAndPublication_personContextId': {'type': LIST, 'mandatory': False},
        'publishedSourceIdOverwrittenByChild': {'type': LIST, 'mandatory': False},
        'publishedSourceContextId': {'type': LIST, 'mandatory': False},
        'companyIdOverwrittenByChild': {'type': LIST, 'mandatory': False},
        'companyContextId': {'type': LIST, 'mandatory': False},
        'version': {'type': Str, 'mandatory': True},
        'fileInfo': {'type': Str, 'mandatory': True},
        'requiredContext': {'type': LIST, 'mandatory': True},
        'flows': {'type': Flow, 'mandatory': True},
        'parameter': {'type': Parameter, 'mandatory': True}
    }

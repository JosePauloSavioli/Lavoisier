#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 13 10:03:19 2022

@author: jotape42p
"""

import pytest

from src.Lavoisier.data_structures.ILCD1_structure import ILCD1Structure
    
# Ways of attribution for subclasses of 'Verification'
# [1] Direct attribution: Unique method
#
# dsi.UUID = '4dfe5a1f-cd1a-4fb3-87bf-55bfc40e0818'
#
# Ways of attribution for subclasses of 'DotDict'
# [1] Direct attribution
#
# fpr.referenceToFlowPropertyDataSet = ref
#
# [2] Indirect attribution.
#   'f' is the field if field has 'unique' == True. This mode locks the attribution via __setitem__.
#       Else it is not bound to the DotDict field, having to be returned back to field
#
# f = fpr.get_class('referenceToFlowPropertyDataSet')() # Non-unique
# f = ref
# fpr.referenceToFlowPropertyDataSet = f # This line has to be done in order for the value of 'f' to be considered
#
# f = fpr.referenceToFlowPropertyDataSet # Unique
# f.subReference = 'lol3' # Changes directly the field

uuid = ('4dfe5a1f-cd1a-4fb3-87bf-55bfc40e0818', 'cd373f89-264e-4fe3-85c4-d0c38970ada6')
version = ('00.00.000', '01.00.000')
real = (10.0, 20.0)
string = ('string', 'string 2', 'string 3')
strres = ('string; string 2', 'string 2; string 3', 'string; string 2; string 3')
mtlang = (([{'@index': 1, '@lang': 'en', '#text': 'lol1'},
           {'@index': 1, '@lang': 'en', '#text': 'lol2'}],
           [{'@xml:lang': 'en', '#text': 'lol1; lol2'}]),
          ({'@index': 1, '@lang': 'en', '#text': 'lol3'},
           [{'@xml:lang': 'en', '#text': 'lol3'}]),
          ([{'@index': 1, '@lang': 'pt', '#text': 'lol4'},
           {'@index': 2, '@lang': 'pt', '#text': 'lol5'}],
           [{'@xml:lang': 'pt', '#text': 'lol4\nlol5'}]))
mtlangres = ([{'@xml:lang': 'en', '#text': 'lol1; lol2; lol3'},
             {'@xml:lang': 'pt', '#text': 'lol4\nlol5'}],
             [{'@xml:lang': 'en', '#text': 'lol3; lol1; lol2'},
              {'@xml:lang': 'pt', '#text': 'lol4\nlol5'}],
             [{'@xml:lang': 'pt', '#text': 'lol4; lol4; lol4\nlol5; lol5; lol5'}],
             [{'@xml:lang': 'en', '#text': 'lol3; lol3; lol3'}])

s = ILCD1Structure()

@pytest.mark.structure
@pytest.mark.parametrize('class_', ['reference',
                                    'classification',
                                    'flow_property',
                                    'dataSetInformation',
                                    'quantitativeReference',
                                    'time',
                                    'technology',
                                    'geography',
                                    'modellingAndValidation',
                                    'administrativeInformation',
                                    'mathematicalRelations',
                                    'exchanges'])
def test_call_to_nonexistent_field(class_):
    a = getattr(s, class_)
    if isinstance(a, type): a = a()
    with pytest.raises(KeyError):
        _ = a.not_field
    with pytest.raises(AttributeError):
        a.not_field = ''

@pytest.mark.structure
@pytest.mark.parametrize('class_', ['reference',
                                    'classification',
                                    'flow_property',
                                    'dataSetInformation',
                                    'quantitativeReference'])
def test_mandatory_fields(class_):
    a = getattr(s, class_)
    if isinstance(a, type): a = a()
    with pytest.raises(AttributeError):
        a.get_dict()

ref = s.reference()
@pytest.mark.structure
def test_reference():
    ref.type = 'source data set'
    ref.refObjectId = uuid[0]
    ref.version = version[0]
    ref.uri = string[0]
    ref.subReference = string[0]
    ref.subReference = string[1]
    ref.shortDescription = mtlang[0][0]
    ref.shortDescription = mtlang[1][0]
    ref.shortDescription = mtlang[2][0]

    with pytest.raises(ValueError):
        ref.type = 'contact data set'
        ref.refObjectId = uuid[1]
        ref.version = version[1]
        ref.uri = string[2]

    assert ref.get_dict() == {'@type': 'source data set',
                              '@refObjectId': uuid[0],
                              '@version': version[0],
                              '@uri': string[0],
                              'c:subReference': strres[0],
                              'c:shortDescription': mtlangres[0]}

clf = s.classification()
@pytest.mark.structure
def test_classification():
    clf.name = string[0]
    clf.classes = string[0]

    cl_1 = clf.get_class('class')()
    cl_1.level = 0
    cl_1.classId = string[0]
    cl_1.text = string[0]
    cl_1.text = string[1]
    setattr(clf, 'class', cl_1)

    cl_2 = clf.get_class('class')()
    cl_2.level = 1
    cl_2.classId = string[0]
    cl_2.text = string[0]
    cl_2.text = string[1]
    setattr(clf, 'class', cl_2)

    with pytest.raises(KeyError):
        cl_1 = getattr(clf, 'class')

    with pytest.raises(ValueError):
        clf.name = string[1]
        clf.classes = string[1]
        cl_1.level = 2
        cl_1.classId = string[1]
        cl_2.level = 2
        cl_2.classId = string[1]

    assert clf.get_dict() == {'@name': string[0],
                              '@classes': string[0],
                              'c:class': [{'@level': 0, '@classId': string[0], '#text': strres[0]},
                                          {'@level': 1, '@classId': string[0], '#text': strres[0]}]}

fpr = s.flow_property()
@pytest.mark.structure
def test_flow_property():
    fpr.dataSetInternalID = 0
    fpr.referenceToFlowPropertyDataSet = ref
    
    get_unique2 = fpr.referenceToFlowPropertyDataSet
    get_unique2.subReference = string[2]
    
    fpr.meanValue = real[0]
    fpr.minimumValue = real[0]
    fpr.maximumValue = real[0]
    fpr.uncertaintyDistributionType = 'log-normal'
    fpr.relativeStandardDeviation95In = real[0]
    fpr.dataDerivationTypeStatus = "Measured"
    fpr.generalComment = mtlang[2][0]
    fpr.generalComment = mtlang[1][0]
    fpr.generalComment = mtlang[0][0]

    with pytest.raises(ValueError):
        fpr.dataSetInternalID = 1
        fpr.referenceToFlowPropertyDataSet = get_unique2
        fpr.meanValue = real[1]
        fpr.minimumValue = real[1]
        fpr.maximumValue = real[1]
        fpr.uncertaintyDistributionType = 'normal'
        fpr.relativeStandardDeviation95In = real[1]
        fpr.dataDerivationTypeStatus = "Other"

    assert fpr.get_dict() == {'@dataSetInternalID': 0,
                              'referenceToFlowPropertyDataSet': [{'@type': 'source data set',
                                                                  '@refObjectId': uuid[0],
                                                                  '@version': '00.00.000',
                                                                  '@uri': string[0],
                                                                  'c:subReference': strres[2],
                                                                  'c:shortDescription': mtlangres[0]}],
                              'meanValue': real[0],
                              'minimumValue': real[0],
                              'maximumValue': real[0],
                              'uncertaintyDistributionType': 'log-normal',
                              'relativeStandardDeviation95In': real[0],
                              'dataDerivationTypeStatus': "Measured",
                              'generalComment': mtlangres[1]}

dsi = s.dataSetInformation
@pytest.mark.structure
def test_dataset_information():
    dsi.UUID = uuid[0]

    name = dsi.name
    name.baseName = mtlang[2][0]
    name.baseName = mtlang[1][0]
    name.baseName = mtlang[0][0]
    name.treatmentStandardsRoutes = mtlang[0][0]
    name.mixAndLocationTypes = mtlang[1][0]
    name.functionalUnitFlowProperties = mtlang[2][0]

    dsi.identifierOfSubDataSet = string[0]
    dsi.synonyms = mtlang[2][0]
    dsi.synonyms = mtlang[2][0]
    dsi.synonyms = mtlang[2][0]

    cproc = dsi.complementingProcesses
    rcpro1 = cproc.get_class('referenceToComplementingProcess')()
    rcpro2 = cproc.get_class('referenceToComplementingProcess')()

    rcpro1.type = 'source data set'
    rcpro1.refObjectId = uuid[0]
    rcpro1.version = version[0]
    rcpro1.uri = string[0]
    rcpro1.subReference = string[0]
    rcpro1.subReference = string[1]
    rcpro1.shortDescription = mtlang[0][0]
    rcpro1.shortDescription = mtlang[1][0]
    rcpro1.shortDescription = mtlang[2][0]
    cproc.referenceToComplementingProcess = rcpro1

    rcpro2.type = 'source data set'
    rcpro2.refObjectId = uuid[1]
    rcpro2.version = version[0]
    rcpro2.uri = string[1]
    rcpro2.subReference = string[1]
    rcpro2.subReference = string[2]
    rcpro2.shortDescription = mtlang[2][0]
    rcpro2.shortDescription = mtlang[1][0]
    rcpro2.shortDescription = mtlang[0][0]
    cproc.referenceToComplementingProcess = rcpro2

    dsi.classificationInformation.classification = clf
    dsi.generalComment = mtlang[1][0]
    dsi.generalComment = mtlang[1][0]
    dsi.generalComment = mtlang[1][0]
    dsi.referenceToExternalDocumentation = ref
    dsi.referenceToExternalDocumentation = ref
    dsi.referenceToExternalDocumentation = ref

    with pytest.raises(KeyError):
        cproc = dsi.get_class('complementingProcesses')
        name = dsi.get_class('UUID')
        rcpro1 = cproc.referenceToComplementingProcess

    with pytest.raises(ValueError):
        dsi.UUID = uuid[0]
        dsi.name = name
        dsi.identifierOfSubDataSet = string[1]
        dsi.classificationInformation = ''
        dsi.complementingProcesses = cproc

    assert dsi.get_dict() == {'c:UUID': uuid[0],
                              'name': [{'baseName': [{'@xml:lang': 'en',
                                                      '#text': 'lol3; lol1; lol2'},
                                                     {'@xml:lang': 'pt',
                                                      '#text': 'lol4\nlol5'}],
                                        'treatmentStandardsRoutes': [{'@xml:lang': 'en',
                                                                      '#text': 'lol1; lol2'}],
                                        'mixAndLocationTypes': [{'@xml:lang': 'en',
                                                                 '#text': 'lol3'}],
                                        'functionalUnitFlowProperties': [{'@xml:lang': 'pt',
                                                                          '#text': 'lol4\nlol5'}]}],
                              'identifierOfSubDataSet': string[0],
                              'c:synonyms': mtlangres[2],
                              'complementingProcesses': [{
                                  'referenceToComplementingProcess': [{'@type': 'source data set',
                                                                       '@refObjectId': uuid[0],
                                                                       '@version': version[0],
                                                                       '@uri': string[0],
                                                                       'c:subReference': strres[0],
                                                                       'c:shortDescription': mtlangres[0]},
                                                                      {'@type': 'source data set',
                                                                       '@refObjectId': uuid[1],
                                                                       '@version': version[0],
                                                                       '@uri': string[1],
                                                                       'c:subReference': strres[1],
                                                                       'c:shortDescription': mtlangres[1]}]}],
                              'classificationInformation': [{'c:classification': [clf.get_dict()]}],
                              'c:generalComment': mtlangres[3],
                              'referenceToExternalDocumentation': [ref.get_dict(),
                                                                   ref.get_dict(),
                                                                   ref.get_dict()]}
    
qrf = s.quantitativeReference
@pytest.mark.structure
def test_quantitative_information():
    qrf.type = "Reference flow(s)"
    qrf.referenceToReferenceFlow = 123
    qrf.referenceToReferenceFlow = 124
    qrf.referenceToReferenceFlow = 125
    qrf.functionalUnitOrOther = mtlang[0][0]
    qrf.functionalUnitOrOther = mtlang[1][0]
    qrf.functionalUnitOrOther = mtlang[2][0]

    with pytest.raises(ValueError):
        qrf.type = "Functional unit"

    assert qrf.get_dict() == {'@type': 'Reference flow(s)',
                              'referenceToReferenceFlow': [123, 124, 125],
                              'functionalUnitOrOther': mtlangres[0]}

tim = s.time
@pytest.mark.structure
def test_time():
    tim.referenceYear = 2000
    tim.dataSetValidUntil = 2000
    tim.timeRepresentativenessDescription = mtlang[0][0]
    tim.timeRepresentativenessDescription = mtlang[1][0]
    tim.timeRepresentativenessDescription = mtlang[2][0]

    with pytest.raises(ValueError):
        tim.referenceYear = 2001
        tim.dataSetValidUntil = 2001

    assert tim.get_dict() == {'c:referenceYear': 2000,
                              'c:dataSetValidUntil': 2000,
                              'c:timeRepresentativenessDescription': mtlangres[0]}

tec = s.technology
@pytest.mark.structure
def test_technology():
    tec.technologyDescriptionAndIncludedProcesses = mtlang[0][0]
    tec.referenceToIncludedProcesses = ref
    tec.referenceToIncludedProcesses = ref
    tec.technologicalApplicability = mtlang[1][0]
    tec.referenceToTechnologyPictogramme = ref
    tec.referenceToTechnologyFlowDiagrammOrPicture = ref
    tec.referenceToTechnologyFlowDiagrammOrPicture = ref

    with pytest.raises(ValueError):
        tec.referenceToTechnologyPictogramme = ref

    assert tec.get_dict() == {'technologyDescriptionAndIncludedProcesses': mtlang[0][1],
                              'referenceToIncludedProcesses': [ref.get_dict(),
                                                               ref.get_dict()],
                              'technologicalApplicability': mtlang[1][1],
                              'referenceToTechnologyPictogramme': [ref.get_dict()],
                              'referenceToTechnologyFlowDiagrammOrPicture': [ref.get_dict(),
                                                                             ref.get_dict()]}

geo = s.geography
@pytest.mark.structure
def test_geography():
    loc = geo.locationOfOperationSupplyOrProduction
    loc.location = string[0]
    loc.latitudeAndLongitude = "+89.2;-130.3"
    loc.descriptionOfRestrictions = mtlang[0][0]

    slo1 = geo.get_class('subLocationOfOperationSupplyOrProduction')()
    slo1.subLocation = string[1]
    slo1.latitudeAndLongitude = "+89;-130"
    slo1.descriptionOfRestrictions = mtlang[1][0]
    geo.subLocationOfOperationSupplyOrProduction = slo1

    slo2 = geo.get_class('subLocationOfOperationSupplyOrProduction')()
    slo2.subLocation = string[2]
    slo2.latitudeAndLongitude = "89;130"
    slo2.descriptionOfRestrictions = mtlang[2][0]
    geo.subLocationOfOperationSupplyOrProduction = slo2
    
    with pytest.raises(KeyError):
        slo1 = geo.subLocationOfOperationSupplyOrProduction

    with pytest.raises(ValueError):
        loc.location = string[2]
        loc.latitudeAndLongitude = "0;0"
        slo1.subLocation = string[0]
        slo1.latitudeAndLongitude = "0;0"
        slo2.subLocation = string[1]
        slo2.latitudeAndLongitude = "0;0"

    assert geo.get_dict() == {
        'locationOfOperationSupplyOrProduction': [{'@location': string[0],
                                                   '@latitudeAndLongitude': "+89.2;-130.3",
                                                   'descriptionOfRestrictions': mtlang[0][1]}],
        'subLocationOfOperationSupplyOrProduction': [{'@subLocation': string[1],
                                                      '@latitudeAndLongitude': "+89;-130",
                                                      'descriptionOfRestrictions': mtlang[1][1]},
                                                     {'@subLocation': string[2],
                                                      '@latitudeAndLongitude': "89;130",
                                                      'descriptionOfRestrictions': mtlang[2][1]}]}

mav = s.modellingAndValidation
@pytest.mark.structure
def test_LCI_method_and_allocation():
    mav.LCIMethodAndAllocation.typeOfDataSet = "LCI result"
    mav.LCIMethodAndAllocation.LCIMethodPrinciple = "Attributional"
    mav.LCIMethodAndAllocation.deviationsFromLCIMethodPrinciple = mtlang[0][0]
    mav.LCIMethodAndAllocation.LCIMethodApproaches = "Allocation - market value"
    mav.LCIMethodAndAllocation.LCIMethodApproaches = "Allocation - gross calorific value"
    mav.LCIMethodAndAllocation.deviationsFromLCIMethodApproaches = mtlang[1][0]
    mav.LCIMethodAndAllocation.modellingConstants = mtlang[2][0]
    mav.LCIMethodAndAllocation.deviationsFromModellingConstants = mtlang[0][0]
    mav.LCIMethodAndAllocation.referenceToLCAMethodDetails = ref
    mav.LCIMethodAndAllocation.referenceToLCAMethodDetails = ref

    with pytest.raises(ValueError):
        mav.LCIMethodAndAllocation = ''
        mav.LCIMethodAndAllocation.typeOfDataSet = "Partly terminated system"
        mav.LCIMethodAndAllocation.LCIMethodPrinciple = "Consequential"
        mav.LCIMethodAndAllocation.LCIMethodApproaches = "Allocation - gross calorific value"

    assert mav.LCIMethodAndAllocation.get_dict() == {'typeOfDataSet': "LCI result",
                                                     'LCIMethodPrinciple': "Attributional",
                                                     'deviationsFromLCIMethodPrinciple': mtlang[0][1],
                                                     'LCIMethodApproaches': ["Allocation - market value",
                                                                             "Allocation - gross calorific value"],
                                                     'deviationsFromLCIMethodApproaches': mtlang[1][1],
                                                     'modellingConstants': mtlang[2][1],
                                                     'deviationsFromModellingConstants': mtlang[0][1],
                                                     'referenceToLCAMethodDetails': [ref.get_dict(),
                                                                                     ref.get_dict()]
                                                     }

@pytest.mark.structure
def test_datsources_treatment_and_representativeness():
    mav.dataSourcesTreatmentAndRepresentativeness.dataCutOffAndCompletenessPrinciples = mtlang[1][0]
    mav.dataSourcesTreatmentAndRepresentativeness.deviationsFromCutOffAndCompletenessPrinciples = mtlang[2][0]
    mav.dataSourcesTreatmentAndRepresentativeness.dataSelectionAndCombinationPrinciples = mtlang[0][0]
    mav.dataSourcesTreatmentAndRepresentativeness.deviationsFromSelectionAndCombinationPrinciples = mtlang[1][0]
    mav.dataSourcesTreatmentAndRepresentativeness.dataTreatmentAndExtrapolationsPrinciples = mtlang[2][0]
    mav.dataSourcesTreatmentAndRepresentativeness.deviationsFromTreatmentAndExtrapolationPrinciples = mtlang[0][0]
    mav.dataSourcesTreatmentAndRepresentativeness.referenceToDataHandlingPrinciples = ref
    mav.dataSourcesTreatmentAndRepresentativeness.referenceToDataHandlingPrinciples = ref
    mav.dataSourcesTreatmentAndRepresentativeness.referenceToDataSource = ref
    mav.dataSourcesTreatmentAndRepresentativeness.referenceToDataSource = ref
    mav.dataSourcesTreatmentAndRepresentativeness.percentageSupplyOrProductionCovered = real[0]
    mav.dataSourcesTreatmentAndRepresentativeness.annualSupplyOrProductionVolume = mtlang[1][0]
    mav.dataSourcesTreatmentAndRepresentativeness.samplingProcedure = mtlang[2][0]
    mav.dataSourcesTreatmentAndRepresentativeness.dataCollectionPeriod = mtlang[0][0]
    mav.dataSourcesTreatmentAndRepresentativeness.uncertaintyAdjustments = mtlang[1][0]
    mav.dataSourcesTreatmentAndRepresentativeness.useAdviceForDataSet = mtlang[2][0]

    with pytest.raises(ValueError):
        mav.dataSourcesTreatmentAndRepresentativeness = ''
        mav.dataSourcesTreatmentAndRepresentativeness.percentageSupplyOrProductionCovered = real[1]

    assert mav.dataSourcesTreatmentAndRepresentativeness.get_dict() == {'dataCutOffAndCompletenessPrinciples': mtlang[1][1],
                                                                        'deviationsFromCutOffAndCompletenessPrinciples': mtlang[2][1],
                                                                        'dataSelectionAndCombinationPrinciples': mtlang[0][1],
                                                                        'deviationsFromSelectionAndCombinationPrinciples': mtlang[1][1],
                                                                        'dataTreatmentAndExtrapolationsPrinciples': mtlang[2][1],
                                                                        'deviationsFromTreatmentAndExtrapolationPrinciples': mtlang[0][1],
                                                                        'referenceToDataHandlingPrinciples': [ref.get_dict(),
                                                                                                              ref.get_dict()],
                                                                        'referenceToDataSource': [ref.get_dict(),
                                                                                                  ref.get_dict()],
                                                                        'percentageSupplyOrProductionCovered': real[0],
                                                                        'annualSupplyOrProductionVolume': mtlang[1][1],
                                                                        'samplingProcedure': mtlang[2][1],
                                                                        'dataCollectionPeriod': mtlang[0][1],
                                                                        'uncertaintyAdjustments': mtlang[1][1],
                                                                        'useAdviceForDataSet': mtlang[2][1]
                                                                        }

@pytest.mark.structure
def test_completeness():
    mav.completeness.completenessProductModel = "Relevant flows missing"
    mav.completeness.completenessProductModel = "Topic not relevant"
    mav.completeness.referenceToSupportedImpactAssessmentMethods = ref
    mav.completeness.referenceToSupportedImpactAssessmentMethods = ref
    
    compl_1 = mav.completeness.get_class('completenessElementaryFlows')()
    compl_2 = mav.completeness.get_class('completenessElementaryFlows')()
    compl_1.type = "Summer smog"
    compl_1.value = "Relevant flows missing"
    compl_2.type = "Eutrophication"
    compl_2.value = "Topic not relevant"
    mav.completeness.completenessElementaryFlows = compl_1
    mav.completeness.completenessElementaryFlows = compl_2
    
    mav.completeness.completenessOtherProblemField = mtlang[0][0]

    with pytest.raises(KeyError):
        compl_1 = mav.completeness.completenessElementaryFlows
        
    with pytest.raises(ValueError):
        compl_1.type = "Eutrophication"
        compl_1.value = "Topic not relevant"
        compl_2.type = "Summer smog"
        compl_2.value = "Relevant flows missing"
        mav.completeness = ''

    assert mav.completeness.get_dict() == {'completenessProductModel': ["Relevant flows missing", "Topic not relevant"],  # List = True
                                           'referenceToSupportedImpactAssessmentMethods': [ref.get_dict(),
                                                                                           ref.get_dict()],
                                           'completenessElementaryFlows': [{'@type': "Summer smog",
                                                                            '@value': "Relevant flows missing"},
                                                                           {'@type': "Eutrophication",
                                                                            '@value': "Topic not relevant"}],
                                           'completenessOtherProblemField': mtlang[0][1]
                                           }

@pytest.mark.structure
def test_validation():
    # Review is a non-unique class field, do it liberates only an instance of its class when accessed (in the get_dict)
    n = mav.validation.get_class('review')()
    
    n.type = "Independent external review"
    
    sc1 = n.get_class('scope')()
    sc2 = n.get_class('scope')()
    sc1.name = "Raw data"
    mt11 = sc1.get_class('method')()
    mt12 = sc1.get_class('method')()
    mt11.name = "Validation of data sources"
    mt12.name = "Sample tests on calculations"
    sc1.method = mt11
    sc1.method = mt12
    sc2.name = "Unit process(es), single operation"
    mt21 = sc2.get_class('method')()
    mt22 = sc2.get_class('method')()
    mt21.name = "Energy balance"
    mt22.name = "Element balance"
    sc2.method = mt21
    sc2.method = mt22
    n.scope = sc1
    n.scope = sc2
    
    dqi1 = n.dataQualityIndicators.get_class('dataQualityIndicator')()
    dqi2 = n.dataQualityIndicators.get_class('dataQualityIndicator')()
    dqi1.name = "Technological representativeness"
    dqi1.value = "Good"
    dqi2.name = "Time representativeness"
    dqi2.value = "Fair"
    n.dataQualityIndicators.dataQualityIndicator = dqi1
    n.dataQualityIndicators.dataQualityIndicator = dqi2
    
    n.reviewDetails = mtlang[0][0]
    n.referenceToNameOfReviewerAndInstitution = ref
    n.referenceToNameOfReviewerAndInstitution = ref
    n.otherReviewDetails = mtlang[1][0]
    n.referenceToCompleteReviewReport = ref
    
    mav.validation.review = n
    
    with pytest.raises(KeyError):
        n = mav.validation.review
        sc1 = n.scope
        mt11 = sc1.method
        dqi1 = n.dataQualityIndicators.dataQualityIndicator
    
    with pytest.raises(ValueError):
        n.type = "Accredited third party review"
        sc1.name = "Unit process(es), single operation"
        sc2.name = "Raw data"
        mt11.name = "Element balance"
        mt12.name = "Energy balance"
        mt21.name = "Sample tests on calculations"
        mt22.name = "Validation of data sources"
        dqi1.name = "Time representativeness"
        dqi2.name = "Technological representativeness"
        dqi1.value = "Fair"
        dqi2.value = "Good"
        n.dataQualityIndicators = ''
        n.referenceToCompleteReviewReport = ref
        mav.validation = ''
        mav.validation.review = ''

    for review in mav.validation.get('review'):
        assert review.get_dict() == {'@type': "Independent external review",
                                     'c:scope': [{'@name': "Raw data",
                                                 "c:method": [{'@name': "Validation of data sources"},
                                                              {'@name': "Sample tests on calculations"}]},
                                                 {'@name': "Unit process(es), single operation",
                                                 "c:method": [{'@name': "Energy balance"},
                                                              {'@name': "Element balance"}]}],
                                     'c:dataQualityIndicators': [{'c:dataQualityIndicator': [{'@name': "Technological representativeness",
                                                                                              '@value': "Good"},
                                                                                             {'@name': "Time representativeness",
                                                                                             '@value': "Fair"}]}],
                                     'c:reviewDetails': mtlang[0][1],
                                     'c:referenceToNameOfReviewerAndInstitution': [ref.get_dict(),
                                                                                   ref.get_dict()],
                                     'c:otherReviewDetails': mtlang[1][1],
                                     'c:referenceToCompleteReviewReport': [ref.get_dict()],
                                     }

@pytest.mark.structure
def test_compliance_declarations():
    # One can't call mav.complianceDeclarations.compliance.[field] directly or it would not create it right
    
    comp_1 = mav.complianceDeclarations.get_class('compliance')()
    comp_1.referenceToComplianceSystem = ref
    comp_1.approvalOfOverallCompliance = "Not compliant"
    comp_1.nomenclatureCompliance = "Not compliant"
    comp_1.methodologicalCompliance = "Not compliant"
    comp_1.reviewCompliance = "Not compliant"
    comp_1.documentationCompliance = "Not compliant"
    comp_1.qualityCompliance = "Not compliant"
    mav.complianceDeclarations.compliance = comp_1

    with pytest.raises(KeyError):
        comp_1 = mav.complianceDeclarations.compliance
        
    with pytest.raises(ValueError):
        mav.complianceDeclarations = ''
        comp_1.compliance = ''
        comp_1.compliance.referenceToComplianceSystem = ref
        comp_1.compliance.approvalOfOverallCompliance = "Not defined"
        comp_1.compliance.nomenclatureCompliance = "Not defined"
        comp_1.methodologicalCompliance = "Not defined"
        comp_1.reviewCompliance = "Not defined"
        comp_1.documentationCompliance = "Not defined"
        comp_1.qualityCompliance = "Not defined"

    for compliance in mav.complianceDeclarations.get('compliance'):
        assert compliance.get_dict() == {'c:referenceToComplianceSystem': [ref.get_dict()],
                                         'c:approvalOfOverallCompliance': "Not compliant",
                                         'c:nomenclatureCompliance': "Not compliant",
                                         'c:methodologicalCompliance': "Not compliant",
                                         'c:reviewCompliance': "Not compliant",
                                         'c:documentationCompliance': "Not compliant",
                                         'c:qualityCompliance': "Not compliant"
                                         }

adm = s.administrativeInformation
@pytest.mark.structure
def test_commissioner_and_goal():
    adm.commissionerAndGoal.referenceToCommissioner = ref
    adm.commissionerAndGoal.referenceToCommissioner = ref
    adm.commissionerAndGoal.project = mtlang[0][0]
    adm.commissionerAndGoal.intendedApplications = mtlang[1][0]

    with pytest.raises(ValueError):
        adm.commissionerAndGoal = ''

    assert adm.commissionerAndGoal.get_dict() == {'c:referenceToCommissioner': [ref.get_dict(),
                                                                                  ref.get_dict()],
                                                    'c:project': mtlang[0][1],
                                                    'c:intendedApplications': mtlang[1][1]
                                                    }

@pytest.mark.structure
def test_datgenerator():
    adm.dataGenerator.referenceToPersonOrEntityGeneratingTheDataSet = ref
    adm.dataGenerator.referenceToPersonOrEntityGeneratingTheDataSet = ref

    assert adm.dataGenerator.get_dict() == {
        'c:referenceToPersonOrEntityGeneratingTheDataSet': [ref.get_dict(), ref.get_dict()]}
    
    
    with pytest.raises(ValueError):
        adm.dataGenerator = ''

@pytest.mark.structure
def test_datentry_by():
    adm.dataEntryBy.timeStamp = '2000-09-12T23:45:12'
    adm.dataEntryBy.referenceToDataSetFormat = ref
    adm.dataEntryBy.referenceToDataSetFormat = ref
    adm.dataEntryBy.referenceToConvertedOriginalDataSetFrom = ref
    adm.dataEntryBy.referenceToPersonOrEntityEnteringTheData = ref
    adm.dataEntryBy.referenceToDataSetUseApproval = ref
    adm.dataEntryBy.referenceToDataSetUseApproval = ref

    with pytest.raises(ValueError):
        adm.dataEntryBy = ''
        adm.dataEntryBy.timeStamp = '2000-09-13'
        adm.dataEntryBy.referenceToConvertedOriginalDataSetFrom = ref
        adm.dataEntryBy.referenceToPersonOrEntityEnteringTheData = ref

    assert adm.dataEntryBy.get_dict() == {'c:timeStamp': '2000-09-12T23:45:12',
                                          'c:referenceToDataSetFormat': [ref.get_dict(),
                                                                         ref.get_dict()],
                                          'c:referenceToConvertedOriginalDataSetFrom': [ref.get_dict()],
                                          'c:referenceToPersonOrEntityEnteringTheData': [ref.get_dict()],
                                          'c:referenceToDataSetUseApproval': [ref.get_dict(),
                                                                              ref.get_dict()]
                                          }

@pytest.mark.structure
def test_publication_and_ownership():
    adm.publicationAndOwnership.dateOfLastRevision = '2000-09-12T23:45:12'
    adm.publicationAndOwnership.dateOfLastRevision = '2020-09-12T23:45:12'
    adm.publicationAndOwnership.dataSetVersion = '01.00.000'
    adm.publicationAndOwnership.referenceToPrecedingDataSetVersion = ref
    adm.publicationAndOwnership.referenceToPrecedingDataSetVersion = ref
    adm.publicationAndOwnership.permanentDataSetURI = string[0]
    adm.publicationAndOwnership.workflowAndPublicationStatus = "Working draft"
    adm.publicationAndOwnership.referenceToUnchangedRepublication = ref
    adm.publicationAndOwnership.referenceToRegistrationAuthority = ref
    adm.publicationAndOwnership.registrationNumber = string[0]
    adm.publicationAndOwnership.referenceToOwnershipOfDataSet = ref
    adm.publicationAndOwnership.copyright = 'true'
    adm.publicationAndOwnership.referenceToEntitiesWithExclusiveAccess = ref
    adm.publicationAndOwnership.referenceToEntitiesWithExclusiveAccess = ref
    adm.publicationAndOwnership.licenseType = "Free of charge for all users and uses"
    adm.publicationAndOwnership.licenseType = "Free of charge for some user types or use types"
    adm.publicationAndOwnership.accessRestrictions = mtlang[2][0]

    with pytest.raises(ValueError):
        adm.publicationAndOwnership = ''
        adm.publicationAndOwnership.dataSetVersion = '02.00.000'
        adm.publicationAndOwnership.permanentDataSetURI = string[1]
        adm.publicationAndOwnership.workflowAndPublicationStatus = "Final draft for internal review"
        adm.publicationAndOwnership.referenceToUnchangedRepublication = ref
        adm.publicationAndOwnership.referenceToRegistrationAuthority = ref
        adm.publicationAndOwnership.registrationNumber = string[1]
        adm.publicationAndOwnership.referenceToOwnershipOfDataSet = ref
        adm.publicationAndOwnership.copyright = 'true'

    assert adm.publicationAndOwnership.get_dict() == {'c:dateOfLastRevision': '2020-09-12T23:45:12',
                                                      'c:dataSetVersion': '01.00.000',
                                                      'c:referenceToPrecedingDataSetVersion': [ref.get_dict(),
                                                                                               ref.get_dict()],
                                                      'c:permanentDataSetURI': string[0],
                                                      'c:workflowAndPublicationStatus': "Working draft",
                                                      'c:referenceToUnchangedRepublication': [ref.get_dict()],
                                                      'c:referenceToRegistrationAuthority': [ref.get_dict()],
                                                      'c:registrationNumber': string[0],
                                                      'c:referenceToOwnershipOfDataSet': [ref.get_dict()],
                                                      'c:copyright': True,
                                                      'c:referenceToEntitiesWithExclusiveAccess': [ref.get_dict(),
                                                                                                   ref.get_dict()],
                                                      'c:licenseType': "Free of charge for some user types or use types",
                                                      'c:accessRestrictions': mtlang[2][1]
                                                      }

mth = s.mathematicalRelations
@pytest.mark.structure
def test_mathematical_relations():
    mth.modelDescription = mtlang[0][0]
    
    var_1 = mth.get_class('variableParameter')()
    var_1.name = 'Equação1'
    var_1.meanValue = real[0]
    var_1.minimumValue = real[0]
    var_1.maximumValue = real[0]
    var_1.uncertaintyDistributionType = 'normal'
    var_1.relativeStandardDeviation95In = real[0]
    var_1.comment = mtlang[1][0]
    mth.variableParameter = var_1

    var_2 = mth.get_class('variableParameter')()
    var_2.name = 'Equação2'
    var_2.meanValue = real[1]
    var_2.minimumValue = real[1]
    var_2.maximumValue = real[1]
    var_2.uncertaintyDistributionType = 'triangular'
    var_2.relativeStandardDeviation95In = real[1]
    var_2.comment = mtlang[2][0]
    mth.variableParameter = var_2

    with pytest.raises(KeyError):
        var_1 = mth.variableParameter
        
    with pytest.raises(ValueError):
        var_1.name = 'Equação2'
        var_1.meanValue = real[1]
        var_1.minimumValue = real[1]
        var_1.maximumValue = real[1]
        var_1.uncertaintyDistributionType = 'triangular'
        var_1.relativeStandardDeviation95In = real[1]
        var_2.name = 'Equação1'
        var_2.meanValue = real[0]
        var_2.minimumValue = real[0]
        var_2.maximumValue = real[0]
        var_2.uncertaintyDistributionType = 'normal'
        var_2.relativeStandardDeviation95In = real[0]

    assert mth.get_dict() == {'modelDescription': mtlang[0][1],
                              'variableParameter': [{'@name': 'Equação1',
                                                     'meanValue': real[0],
                                                     'minimumValue': real[0],
                                                     'maximumValue': real[0],
                                                     'uncertaintyDistributionType': 'normal',
                                                     'relativeStandardDeviation95In': real[0],
                                                     'comment': mtlang[1][1]},
                                                    {'@name': 'Equação2',
                                                     'meanValue': real[1],
                                                     'minimumValue': real[1],
                                                     'maximumValue': real[1],
                                                     'uncertaintyDistributionType': 'triangular',
                                                     'relativeStandardDeviation95In': real[1],
                                                     'comment': mtlang[2][1]}]}

exc = s.exchanges
@pytest.mark.structure
def test_exchanges():
    e = exc.get_class('exchange')()
    
    e.dataSetInternalID = 0
    e.referenceToFlowDataSet = ref
    e.location = 'FR'
    e.functionType = "General reminder flow"
    e.exchangeDirection = "Input"
    e.referenceToVariable = string[1]
    e.meanAmount = real[0]
    e.resultingAmount = real[0]
    e.minimumAmount = real[0]
    e.maximumAmount = real[0]
    e.uncertaintyDistributionType = 'log-normal'
    e.relativeStandardDeviation95In = real[0]
    
    als = e.allocations
    al_1 = als.get_class('allocation')()
    al_2 = als.get_class('allocation')()
    al_1.internalReferenceToCoProduct = 0
    al_1.allocatedFraction = 0.324682763
    al_2.internalReferenceToCoProduct = 1
    al_2.allocatedFraction = 0.125124674
    als.allocation = al_1
    als.allocation = al_2
    
    e.dataSourceType = "Primary"
    e.dataDerivationTypeStatus = "Measured"
    rds = e.referencesToDataSource
    rds.referenceToDataSource = ref
    rds.referenceToDataSource = ref
    e.generalComment = mtlang[2][0]
    
    exc.exchange = e

    with pytest.raises(KeyError):
        e = exc.exchange
        al_1 = als.allocation
        
    with pytest.raises(ValueError):
        e.dataSetInternalID = 1
        e.allocations = ''
        e.referencesToDataSource = ''
        e.referenceToFlowDataSet = ref
        e = ''
        e.location = 'BR'
        e.functionType = "Allocation reminder flow"
        e.exchangeDirection = "Output"
        e.referenceToVariable = string[2]
        e.meanAmount = real[1]
        e.minimumAmount = real[1]
        e.maximumAmount = real[1]
        e.uncertaintyDistributionType = 'normal'
        e.relativeStandardDeviation95In = real[1]
        al_1.internalReferenceToCoProduct = 2
        al_2.internalReferenceToCoProduct = 2
        al_1.allocatedFraction = 0.1
        al_2.allocatedFraction = 0.1
        e.dataSourceType = "> 90% primary"
        e.dataDerivationTypeStatus = "Calculated"

    for exchange in exc.get('exchange'):
        assert exchange.get_dict() == {'@dataSetInternalID': 0,
                                       'referenceToFlowDataSet': [ref.get_dict()],
                                       'location': 'FR',
                                       'functionType': "General reminder flow",
                                       'exchangeDirection': "Input",
                                       'referenceToVariable': string[1],
                                       'meanAmount': real[0],
                                       'resultingAmount': real[0],
                                       'minimumAmount': real[0],
                                       'maximumAmount': real[0],
                                       'uncertaintyDistributionType': 'log-normal',
                                       'relativeStandardDeviation95In': real[0],
                                       'allocations': [{'allocation': [{'@internalReferenceToCoProduct': 0,
                                                                        '@allocatedFraction': 0.324682763},
                                                                       {'@internalReferenceToCoProduct': 1,
                                                                        '@allocatedFraction': 0.125124674}]}],
                                       'dataSourceType': "Primary",
                                       'dataDerivationTypeStatus': "Measured",
                                       'referencesToDataSource': [{'referenceToDataSource': [ref.get_dict(),
                                                                                             ref.get_dict()]}],
                                       'generalComment': mtlang[2][1]
                                       }

@pytest.mark.structure
def test_ILCD1_structure():
    assert s.get_dict() == {'processDataSet': 
                            {'@xmlns': 'http://lca.jrc.it/ILCD/Process',
                             '@xmlns:c': 'http://lca.jrc.it/ILCD/Common',
                             '@version': '1.1', 
                             '@locations': '../ILCDLocations.xml',
                             '@metaDataOnly': 'false',
                             'processInformation': {
                                 'dataSetInformation': dsi.get_dict(),
                                 'quantitativeReference': qrf.get_dict(),
                                 'time': tim.get_dict(),
                                 'geography': geo.get_dict(),
                                 'technology': tec.get_dict(),
                                 'mathematicalRelations': mth.get_dict()
                                 },
                             'modellingAndValidation': mav.get_dict(),
                             'administrativeInformation': adm.get_dict(),
                             'exchanges': exc.get_dict()
                             }
                            }

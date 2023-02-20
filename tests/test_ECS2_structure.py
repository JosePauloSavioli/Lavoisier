#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 13 10:03:19 2022

@author: jotape42p
"""

import pytest

from src.Lavoisier.data_structures.ECS2_structure import ECS2Structure

from copy import deepcopy

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

## All unique attributions creates a list, so it is not only {}, but [{}] (see uncertainty dict result)

uuid = ('4dfe5a1f-cd1a-4fb3-87bf-55bfc40e0818', 'cd373f89-264e-4fe3-85c4-d0c38970ada6')
version = ('00.00.000', '01.00.000')
real = (10.0, 20.0, 30.0, 40.0, 50.0)
int_ = (0, 1, 2, 3, 4, 5)
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

s = ECS2Structure()

@pytest.mark.structure
@pytest.mark.parametrize('class_', ['activityDescription',
                                    'flowData',
                                    'modellingAndValidation',
                                    'administrativeInformation',
                                    'textAndImage',
                                    'property',
                                    'userMaster',
                                    'uncertainty',
                                    'source',
                                    'quantitativeReference',
                                    'quantitativeReferenceWithUnit',
                                    'classification'])
def test_call_to_nonexistent_field(class_):
    a = getattr(s, class_)
    if isinstance(a, type): a = a()
    with pytest.raises(KeyError):
        _ = a.not_field
    with pytest.raises(AttributeError):
        a.not_field = ''

@pytest.mark.structure
@pytest.mark.parametrize('class_', ['activityDescription',
                                    'flowData',
                                    'administrativeInformation',
                                    'property',
                                    'quantitativeReference',
                                    'quantitativeReferenceWithUnit'])
def test_mandatory_fields(class_):
    a = getattr(s, class_)
    if isinstance(a, type): a = a()
    with pytest.raises(AttributeError):
        a.get_dict()

unc = s.uncertainty()
@pytest.mark.structure
def test_uncertainty():
    
    log = unc.lognormal
    log.meanValue = real[0]
    log.mu = real[1]
    log.variance = real[2]
    log.varianceWithPedigreeUncertainty = real[3]
    
    with pytest.raises(ValueError): # For unique fields
        log.meanValue = real[4]
        log.mu = real[4]
        log.variance = real[4]
        log.varianceWithPedigreeUncertainty = real[4]
        
    nor = unc.normal
    nor.meanValue = real[0]
    nor.variance = real[1]
    nor.varianceWithPedigreeUncertainty = real[2]
    
    with pytest.raises(ValueError): # For unique fields
        nor.meanValue = real[3]
        nor.variance = real[3]
        nor.varianceWithPedigreeUncertainty = real[3]
    
    tri = unc.triangular
    tri.minValue = real[0]
    tri.mostLikelyValue = real[1]
    tri.maxValue = real[2]
    
    with pytest.raises(ValueError): # For unique fields
        tri.minValue = real[3]
        tri.mostLikelyValue = real[3]
        tri.maxValue = real[3]
    
    uni = unc.uniform
    uni.minValue = real[0]
    uni.maxValue = real[1]
    
    with pytest.raises(ValueError): # For unique fields
        uni.minValue = real[2]
        uni.maxValue = real[2]
    
    bet = unc.beta
    bet.minValue = real[0]
    bet.mostLikelyValue = real[1]
    bet.maxValue = real[2]
    
    with pytest.raises(ValueError): # For unique fields
        bet.minValue = real[3]
        bet.mostLikelyValue = real[3]
        bet.maxValue = real[3]
        
    gam = unc.gamma
    gam.shape = real[0]
    gam.scale = real[1]
    gam.minValue = real[2]
    
    with pytest.raises(ValueError): # For unique fields
        gam.shape = real[3]
        gam.scale = real[3]
        gam.minValue = real[3]
    
    _bin = unc.binomial
    _bin.n = int_[1]
    _bin.p = real[0]
    
    with pytest.raises(ValueError): # For unique fields
        _bin.n = int_[2]
        _bin.p = real[1]
    
    und = unc.undefined
    und.minValue = real[0]
    und.standardDeviation95 = real[1]
    und.maxValue = real[2]
    
    with pytest.raises(ValueError): # For unique fields
        und.minValue = real[3]
        und.standardDeviation95 = real[3]
        und.maxValue = real[3]
    
    ped = unc.pedigreeMatrix
    ped.reliability = int_[1]
    ped.completeness = int_[2]
    ped.temporalCorrelation = int_[3]
    ped.geographicalCorrelation = int_[4]
    ped.furtherTechnologyCorrelation = int_[5]
    
    with pytest.raises(ValueError): # For unique fields
        ped.reliability = int_[0]
        ped.completeness = int_[0]
        ped.temporalCorrelation = int_[0]
        ped.geographicalCorrelation = int_[0]
        ped.furtherTechnologyCorrelation = int_[0]
    
    unc.comment = mtlang[0][0]
    unc.comment = mtlang[1][0]
    unc.comment = mtlang[2][0]

    assert unc.get_dict() == {
        'lognormal': [{
            '@meanValue': 10.0,
            '@mu': 20.0,
            '@variance': 30.0,
            '@varianceWithPedigreeUncertainty': 40.0
            }],
        'normal': [{
            '@meanValue': 10.0,
            '@variance': 20.0,
            '@varianceWithPedigreeUncertainty': 30.0
            }],
        'triangular': [{
            '@minValue': 10.0,
            '@mostLikelyValue': 20.0,
            '@maxValue': 30.0
            }],
        'uniform': [{
            '@minValue': 10.0,
            '@maxValue': 20.0
            }],
        'beta': [{
            '@minValue': 10.0,
            '@mostLikelyValue': 20.0,
            '@maxValue': 30.0
            }],
        'gamma': [{
            '@shape': 10.0,
            '@scale': 20.0,
            '@minValue': 30.0
            }],
        'binomial': [{
            '@n': 1,
            '@p': 10.0,
            }],
        'undefined': [{
            '@minValue': 10.0,
            '@standardDeviation95': 20.0,
            '@maxValue': 30.0
            }],
        'pedigreeMatrix': [{
            '@reliability': 1,
            '@completeness': 2,
            '@temporalCorrelation': 3,
            '@geographicalCorrelation': 4,
            '@furtherTechnologyCorrelation': 5
            }],
        'comment': mtlangres[0]}

src = s.source()
@pytest.mark.structure
def test_source():
    
    src.sourceId = uuid[0]
    src.sourceId = uuid[1]
    src.sourceIdOverwrittenByChild = True
    src.sourceContextId = uuid[1]
    src.sourceYear = string[0]
    src.sourceYear = string[1]
    src.sourceFirstAuthor = string[0]
    src.sourceFirstAuthor = string[1]

    with pytest.raises(ValueError):
        src.sourceIdOverwrittenByChild = False
        src.sourceContextId = uuid[0]
        
    assert src.get_dict() == {
        '@sourceId': uuid[1],
        '@sourceIdOverwrittenByChild': 'true',
        '@sourceContextId': uuid[1],
        '@sourceYear': string[1],
        '@sourceFirstAuthor': string[1]
        }

qtt = s.quantitativeReference()
@pytest.mark.structure
def test_quantitative_reference():
    
    qtt.amount = real[0]
    qtt.mathematicalRelation = string[0]
    qtt.isCalculatedAmount = True
    qtt.comment = mtlang[2][0]
    qtt.comment = mtlang[1][0]
    qtt.comment = mtlang[0][0]
    qtt.uncertainty = unc
    for k, v in src.items():
        setattr(qtt, k, v.end())

    with pytest.raises(ValueError):
        qtt.amount = real[1]
        qtt.mathematicalRelation = string[1]
        qtt.isCalculatedAmount = False
        qtt.uncertainty = unc
        
    assert qtt.get_dict() == {
        '@amount': real[0],
        '@mathematicalRelation': string[0],
        '@isCalculatedAmount': 'true',
        'comment': mtlangres[1],
        'uncertainty': [unc.get_dict()],
        } | src.get_dict()

qtu = s.quantitativeReferenceWithUnit()
@pytest.mark.structure
def test_quantitative_reference_with_unit():
    
    qtu.variableName = string[0]
    qtu.unitId = uuid[0]
    qtu.unitContextId = uuid[1]
    qtu.name = mtlang[2][0]
    qtu.name = mtlang[1][0]
    qtu.unitName = mtlang[2][0]
    qtu.unitName = mtlang[2][0]
    qtu.unitName = mtlang[2][0]
    for k, v in qtt.items():
        if k != 'comment':
            setattr(qtu, k, v.end() if not isinstance(v, list) else v)
    qtu.comment = mtlang[2][0]
    qtu.comment = mtlang[1][0]
    qtu.comment = mtlang[0][0]
    
    with pytest.raises(ValueError):
        qtu.variableName = string[1]
        qtu.unitId = uuid[1]
        qtu.unitContextId = uuid[0]
        
    assert qtu.get_dict() == {
        '@variableName': string[0],
        '@unitId': uuid[0],
        '@unitContextId': uuid[1],
        'name': {'@xml:lang': 'pt', '#text': 'lol4'}, # Here it is not a list because the 'end' function returns only the first occurrence, also 'pt' goes last always
        'unitName': [mtlangres[0][1]]
        } | qtt.get_dict()
        
tai = s.textAndImage()
@pytest.mark.structure
def test_text_and_image():
    
    tai.text = mtlang[2][0]
    tai.text = mtlang[2][0]
    tai.text = mtlang[2][0]
    tai.imageUrl = {'@index': 1, '#text': 'lol'}
    tai.imageUrl = [{'@index': 1, '#text': 'lol1'}, {'@index': 2, '#text': 'lol2'}]
    tai.variable = {'@name': 'myname', '#text': 'lol'}
    tai.variable = [{'@name': 'myname1', '#text': 'lol1'}, {'@name': 'myname2', '#text': 'lol2'}]
    
    assert tai.get_dict() == {
        'text': [{'#text': 'lol4; lol4; lol4', '@index': 1, '@xml:lang': 'pt'},
                 {'#text': 'lol5; lol5; lol5', '@index': 2, '@xml:lang': 'pt'}], # IndexedString
        'imageUrl': [{'@index': 1, '#text': 'lol1'},
                     {'@index': 2, '#text': 'lol2'}], # it is just one string that can be placed
        'variable': [{'@name': 'myname', '#text': 'lol'},
                     {'@name': 'myname1', '#text': 'lol1'},
                     {'@name': 'myname2', '#text': 'lol2'}]
        }
        
cla = s.classification()
@pytest.mark.structure
def test_classification():
    
    cla.classificationId = uuid[0]
    cla.classificationContextId = uuid[1]
    cla.classificationSystem = mtlang[2][0]
    cla.classificationSystem = mtlang[1][0]
    cla.classificationSystem = mtlang[0][0]
    cla.classificationValue = mtlang[1][0]
    cla.classificationValue = mtlang[2][0]

    with pytest.raises(ValueError):
        cla.classificationId = uuid[1]
        cla.classificationContextId = uuid[0]
        
    assert cla.get_dict() == {
        '@classificationId': uuid[0],
        '@classificationContextId': uuid[1],
        'classificationSystem': mtlangres[1],
        'classificationValue': {'@xml:lang': 'pt', '#text': 'lol5'}, # Here it is not a list because the 'end' function returns only the first occurrence, also 'pt' goes last always
        }

anm = s.activityNameMaster()
@pytest.mark.structure
def test_activity_name_master():
    
    anm.id = uuid[0]
    anm.id = uuid[1]
    anm.name = mtlang[2][0]
    anm.name = mtlang[1][0]
    anm.name = mtlang[0][0]
    
    assert anm.get_dict() == {
        '@id': uuid[1],
        'name': mtlangres[1]
        }

csm = s.classificationSystemMaster()
@pytest.mark.structure
def test_classification_system_master():
    
    csm.id = uuid[0]
    csm.type = int_[1]
    csm.name = mtlang[2][0]
    csm.name = mtlang[1][0]
    csm.name = mtlang[0][0]
    csm.comment = mtlang[0][0]
    csm.comment = mtlang[1][0]
    csm.comment = mtlang[2][0]
    
    csc = csm.get_class('classificationValue')()
    csc.id = uuid[0]
    csc.name = mtlang[2][0]
    csc.name = mtlang[1][0]
    csc.name = mtlang[0][0]
    csc.comment = mtlang[0][0]
    csc.comment = mtlang[1][0]
    csc.comment = mtlang[2][0]
    csm.classificationValue = csc

    with pytest.raises(ValueError):
        csm.id = uuid[1]
        csm.type = int_[2]
        csc.id = uuid[1]

    assert csm.get_dict() == {
        '@id': uuid[0],
        '@type': int_[1],
        'name': mtlangres[1],
        'comment': mtlangres[0],
        'classificationValue': [{
            '@id': uuid[0],
            'name': {'@xml:lang': 'pt', '#text': 'lol5'}, # No list here, only one of the list positions is used
            'comment': mtlangres[0]
            }]
        }

cpm = s.companyMaster()
@pytest.mark.structure
def test_company_master():
    
    cpm.id = uuid[0]
    cpm.code = string[0]
    cpm.website = string[1]
    cpm.name = mtlang[2][0]
    cpm.name = mtlang[1][0]
    cpm.name = mtlang[0][0]
    cpm.comment = mtlang[0][0]
    cpm.comment = mtlang[1][0]
    cpm.comment = mtlang[2][0]

    with pytest.raises(ValueError):
        cpm.id = uuid[1]
        cpm.code = string[1]
        cpm.website = string[0]

    assert cpm.get_dict() == {
        '@id': uuid[0],
        '@code': string[0],
        '@website': string[1],
        'name': mtlangres[1],
        'comment': mtlangres[0]
        }

ctm = s.compartmentMaster()
@pytest.mark.structure
def test_compartment_master():
    
    ctm.id = uuid[0]
    ctm.name = mtlang[2][0]
    ctm.name = mtlang[1][0]
    ctm.name = mtlang[0][0]
    ctm.comment = mtlang[0][0]
    ctm.comment = mtlang[1][0]
    ctm.comment = mtlang[2][0]
    
    csu = ctm.get_class('subcompartment')()
    csu.id = uuid[0]
    csu.name = mtlang[2][0]
    csu.name = mtlang[1][0]
    csu.name = mtlang[0][0]
    csu.comment = mtlang[0][0]
    csu.comment = mtlang[1][0]
    csu.comment = mtlang[2][0]
    ctm.subcompartment = csu

    with pytest.raises(ValueError):
        ctm.id = uuid[1]
        csu.id = uuid[1]

    assert ctm.get_dict() == {
        '@id': uuid[0],
        'name': mtlangres[1],
        'comment': mtlangres[0],
        'subcompartment': [{
            '@id': uuid[0],
            'name': mtlangres[1],
            'comment': mtlangres[0]
            }]
        }
    
pri = s.property_intern()
@pytest.mark.structure
def test_property():
    
    pri.propertyId = uuid[0]
    pri.propertyContextId = uuid[1]
    pri.isDefiningValue = 'true'
    for k, v in qtu.items():
        if k not in ('comment', 'name', 'unitName'):
            setattr(pri, k, v.end() if not isinstance(v, list) else v)
    pri.name = mtlang[2][0]
    pri.name = mtlang[1][0]
    pri.unitName = mtlang[2][0]
    pri.unitName = mtlang[2][0]
    pri.unitName = mtlang[2][0]
    pri.comment = mtlang[2][0]
    pri.comment = mtlang[1][0]
    pri.comment = mtlang[0][0]

    with pytest.raises(ValueError):
        pri.propertyId = uuid[1]
        pri.propertyContextId = uuid[0]
        pri.isDefiningValue = 'false'

    assert pri.get_dict() == {
        '@propertyId': uuid[0],
        '@propertyContextId': uuid[1],
        '@isDefiningValue': 'true'
        } | qtu.get_dict()

elm = s.elementaryMaster()
@pytest.mark.structure
def test_elementary_master():
    
    elm.id = uuid[0]
    elm.unitId = uuid[1]
    elm.unitContextId = uuid[1]
    elm.formula = string[0]
    elm.casNumber = '7732-18-5'
    elm.defaultVariableName = string[0]
    elm.name = mtlang[2][0]
    elm.name = mtlang[1][0]
    elm.name = mtlang[0][0]
    elm.unitName = mtlang[2][0]
    elm.unitName = mtlang[2][0]
    elm.unitName = mtlang[2][0]
    emc = elm.get_class('compartment')()
    emc.subcompartmentId = uuid[0]
    emc.subcompartmentContextId = uuid[1]
    emc.compartment = mtlang[2][0]
    emc.compartment = mtlang[1][0]
    emc.compartment = mtlang[0][0]
    emc.subcompartment = mtlang[0][0]
    emc.subcompartment = mtlang[1][0]
    emc.subcompartment = mtlang[2][0]
    elm.compartment = emc
    elm.comment = mtlang[2][0]
    elm.comment = mtlang[1][0]
    elm.comment = mtlang[0][0]
    elm.synonym = mtlang[0][0]
    elm.synonym = mtlang[1][0]
    elm.property = pri
    elm.productInformation = tai

    with pytest.raises(ValueError):
        elm.id = uuid[1]
        elm.unitId = uuid[0]
        elm.unitContextId = uuid[0]
        elm.formula = string[1]
        elm.casNumber = '7732-18-6'
        elm.defaultVariableName = string[1]
        emc.subcompartmentId = uuid[1]
        emc.subcompartmentContextId = uuid[0]

    assert elm.get_dict() == {
        '@id': uuid[0],
        '@unitId': uuid[1],
        '@unitContextId': uuid[1],
        '@formula': string[0],
        '@casNumber': '7732-18-5',
        '@defaultVariableName': string[0],
        'name': mtlangres[1],
        'unitName': mtlangres[2],
        'compartment': [{
            '@subcompartmentId': uuid[0],
            '@subcompartmentContextId': uuid[1],
            'compartment': mtlangres[1],
            'subcompartment': mtlangres[0]
            }],
        'comment': mtlangres[1],
        'synonym': [{'@xml:lang': 'en', '#text': 'lol1'}, {'@xml:lang': 'en', '#text': 'lol2'}, {'@xml:lang': 'en', '#text': 'lol3'}],
        'property': [pri.get_dict()],
        'productInformation': [tai.get_dict()]
        }

gem = s.geographyMaster()
@pytest.mark.structure
def test_geography_master():
    
    gem.id = uuid[0]
    gem.longitude = real[0]
    gem.latitude = real[1]
    gem.ISOTwoLetterCode = 'AB'
    gem.ISOThreeLetterCode = 'ABC'
    gem.uNCode = 1
    gem.uNRegionCode = 2
    gem.uNSubregionCode = 3
    gem.name = mtlang[2][0]
    gem.name = mtlang[1][0]
    gem.name = mtlang[0][0]
    gem.shortname = mtlang[2][0]
    gem.shortname = mtlang[1][0]
    gem.shortname = mtlang[0][0]
    gem.comment = tai
    
    with pytest.raises(ValueError):
        gem.id = uuid[1]
        gem.longitude = real[1]
        gem.latitude = real[0]
        gem.ISOTwoLetterCode = 'BC'
        gem.ISOThreeLetterCode = 'BCD'
        gem.uNCode = 2
        gem.uNRegionCode = 3
        gem.uNSubregionCode = 4
    
    assert gem.get_dict() == {
        '@id': uuid[0],
        '@longitude': real[0],
        '@latitude': real[1],
        '@ISOTwoLetterCode': 'AB',
        '@ISOThreeLetterCode': 'ABC',
        '@uNCode': 1,
        '@uNRegionCode': 2,
        '@uNSubregionCode': 3,
        'name': mtlangres[1],
        'shortname': mtlangres[1],
        'comment': [tai.get_dict()]
        }
    
inm = s.intermediateMaster()
@pytest.mark.structure
def test_intermediate_master():
    
    inm.id = uuid[0]
    inm.unitId = uuid[1]
    inm.unitContextId = uuid[1]
    inm.casNumber = '7732-18-5'
    inm.defaultVariableName = string[0]
    inm.name = mtlang[2][0]
    inm.name = mtlang[1][0]
    inm.name = mtlang[0][0]
    inm.unitName = mtlang[2][0]
    inm.unitName = mtlang[2][0]
    inm.unitName = mtlang[2][0]
    inm.classification = cla
    inm.comment = mtlang[2][0]
    inm.comment = mtlang[1][0]
    inm.comment = mtlang[0][0]
    inm.synonym = mtlang[0][0]
    inm.synonym = mtlang[1][0]
    inm.property = pri
    inm.productInformation = tai

    with pytest.raises(ValueError):
        inm.id = uuid[1]
        inm.unitId = uuid[0]
        inm.unitContextId = uuid[0]
        inm.formula = string[1]
        inm.casNumber = '7732-18-6'
        inm.defaultVariableName = string[1]

    assert inm.get_dict() == {
        '@id': uuid[0],
        '@unitId': uuid[1],
        '@unitContextId': uuid[1],
        '@casNumber': '7732-18-5',
        '@defaultVariableName': string[0],
        'name': mtlangres[1],
        'unitName': mtlangres[2],
        'classification': [cla.get_dict()],
        'comment': mtlangres[1],
        'synonym': [{'@xml:lang': 'en', '#text': 'lol1'}, {'@xml:lang': 'en', '#text': 'lol2'}, {'@xml:lang': 'en', '#text': 'lol3'}],
        'property': [pri.get_dict()],
        'productInformation': [tai.get_dict()]
        }

lgm = s.languageMaster()
@pytest.mark.structure
def test_language_master():
    
    lgm.code = 'en'
    lgm.comment = mtlang[2][0]
    lgm.comment = mtlang[1][0]
    lgm.comment = mtlang[0][0]

    with pytest.raises(ValueError):
        lgm.code = 'pt'

    assert lgm.get_dict() == {
        '@code': 'en',
        'comment': mtlangres[1]
        }
    
msm = s.macroEconomicScenarioMaster()
@pytest.mark.structure
def test_macro_economic_scenario_master():
    
    msm.id = uuid[0]
    msm.name = mtlang[2][0]
    msm.name = mtlang[1][0]
    msm.name = mtlang[0][0]
    msm.comment = mtlang[2][0]
    msm.comment = mtlang[1][0]
    msm.comment = mtlang[0][0]

    with pytest.raises(ValueError):
        msm.id = uuid[1]

    assert msm.get_dict() == {
        '@id': uuid[0],
        'name': mtlangres[1],
        'comment': mtlangres[1]
        }
    
prm = s.parameterMaster()
@pytest.mark.structure
def test_parameter_master():
    
    prm.id = uuid[0]
    prm.defaultVariableName = string[0]
    prm.unitId = uuid[1]
    prm.unitContextId = uuid[1]
    prm.name = mtlang[2][0]
    prm.name = mtlang[1][0]
    prm.name = mtlang[0][0]
    prm.unitName = mtlang[2][0]
    prm.unitName = mtlang[2][0]
    prm.unitName = mtlang[2][0]
    prm.comment = mtlang[2][0]
    prm.comment = mtlang[1][0]
    prm.comment = mtlang[0][0]

    with pytest.raises(ValueError):
        prm.id = uuid[1]
        prm.defaultVariableName = string[1]
        prm.unitId = uuid[0]
        prm.unitContextId = uuid[0]

    assert prm.get_dict() == {
        '@id': uuid[0],
        '@defaultVariableName': string[0],
        '@unitId': uuid[1],
        '@unitContextId': uuid[1],
        'name': mtlangres[1],
        'unitName': mtlangres[2],
        'comment': mtlangres[1],
        }

psm = s.personMaster()
@pytest.mark.structure
def test_person_master():
    
    psm.id = uuid[0]
    psm.name = string[0]
    psm.address = string[0]
    psm.telephone = string[0]
    psm.telefax = string[0]
    psm.email = string[0]
    psm.companyId = uuid[0]
    psm.companyContextId = uuid[0]
    psm.companyName = mtlang[0][0]
    psm.companyName = mtlang[1][0]
    psm.companyName = mtlang[2][0]

    with pytest.raises(ValueError):
        psm.id = uuid[1]
        psm.name = string[1]
        psm.address = string[1]
        psm.telephone = string[1]
        psm.telefax = string[1]
        psm.email = string[1]
        psm.companyId = uuid[1]
        psm.companyContextId = uuid[1]

    assert psm.get_dict() == {
        '@id': uuid[0],
        '@name': string[0],
        '@address': string[0],
        '@telephone': string[0],
        '@telefax': string[0],
        '@email': string[0],
        '@companyId': uuid[0],
        '@companyContextId': uuid[0],
        'companyName': mtlangres[0]
        }

ppm = s.propertyMaster()
@pytest.mark.structure
def test_property_master():
    
    ppm.id = uuid[0]
    ppm.defaultVariableName = string[0]
    ppm.unitId = uuid[1]
    ppm.unitContextId = uuid[1]
    ppm.name = mtlang[2][0]
    ppm.name = mtlang[1][0]
    ppm.name = mtlang[0][0]
    ppm.unitName = mtlang[2][0]
    ppm.unitName = mtlang[2][0]
    ppm.unitName = mtlang[2][0]
    ppm.comment = mtlang[2][0]
    ppm.comment = mtlang[1][0]
    ppm.comment = mtlang[0][0]

    with pytest.raises(ValueError):
        ppm.id = uuid[1]
        ppm.defaultVariableName = string[1]
        ppm.unitId = uuid[0]
        ppm.unitContextId = uuid[0]

    assert ppm.get_dict() == {
        '@id': uuid[0],
        '@defaultVariableName': string[0],
        '@unitId': uuid[1],
        '@unitContextId': uuid[1],
        'name': mtlangres[1],
        'unitName': mtlangres[2],
        'comment': mtlangres[1],
        }

srm = s.sourceMaster()
@pytest.mark.structure
def test_source_master():
    
    srm.id = uuid[0]
    srm.sourceType = int_[0]
    srm.year = string[0]
    srm.volumeNo = int_[0]
    srm.firstAuthor = string[0]
    srm.additionalAuthors = string[0]
    srm.title = string[0]
    srm.shortName = string[0]
    srm.pageNumbers = string[0]
    srm.nameOfEditors = string[0]
    srm.titleOfAnthology = string[0]
    srm.placeOfPublications = string[0]
    srm.publisher = string[0]
    srm.journal = string[0]
    srm.issueNo = string[0]
    srm.comment = mtlang[0][0]
    srm.comment = mtlang[1][0]
    srm.comment = mtlang[2][0]

    with pytest.raises(ValueError):
        srm.id = uuid[1]
        srm.sourceType = int_[1]
        srm.year = string[1]
        srm.volumeNo = int_[1]
        srm.firstAuthor = string[1]
        srm.additionalAuthors = string[1]
        srm.title = string[1]
        srm.shortName = string[1]
        srm.pageNumbers = string[1]
        srm.nameOfEditors = string[1]
        srm.titleOfAnthology = string[1]
        srm.placeOfPublications = string[1]
        srm.publisher = string[1]
        srm.journal = string[1]
        srm.issueNo = string[1]
        
    assert srm.get_dict() == {
        '@id': uuid[0],
        '@sourceType': int_[0],
        '@year': string[0],
        '@volumeNo': int_[0],
        '@firstAuthor': string[0],
        '@additionalAuthors': string[0],
        '@title': string[0],
        '@shortName': string[0],
        '@pageNumbers': string[0],
        '@nameOfEditors': string[0],
        '@titleOfAnthology': string[0],
        '@placeOfPublications': string[0],
        '@publisher': string[0],
        '@journal': string[0],
        '@issueNo': string[0],
        'comment': mtlangres[0]
        }

smm = s.systemModelMaster()
@pytest.mark.structure
def test_system_model_master():
    
    smm.id = uuid[0]
    smm.name = mtlang[2][0]
    smm.name = mtlang[1][0]
    smm.name = mtlang[0][0]
    smm.shortname = mtlang[2][0]
    smm.shortname = mtlang[1][0]
    smm.shortname = mtlang[0][0]
    smm.comment = mtlang[0][0]
    smm.comment = mtlang[1][0]
    smm.comment = mtlang[2][0]

    with pytest.raises(ValueError):
        smm.id = uuid[1]
        smm.type = int_[2]

    assert smm.get_dict() == {
        '@id': uuid[0],
        'name': mtlangres[1],
        'shortname': mtlangres[1],
        'comment': mtlangres[0]
        }

tgm = s.tagMaster()
@pytest.mark.structure
def test_tag_master():
    
    tgm.name = string[0]
    tgm.comment = mtlang[0][0]
    tgm.comment = mtlang[1][0]
    tgm.comment = mtlang[2][0]

    with pytest.raises(ValueError):
        tgm.name = string[1]

    assert tgm.get_dict() == {
        '@name': string[0],
        'comment': mtlangres[0]
        }
    
unm = s.unitMaster()
@pytest.mark.structure
def test_unit_master():
    
    unm.id = uuid[0]
    unm.name = mtlang[0][0]
    unm.name = mtlang[1][0]
    unm.name = mtlang[2][0]
    unm.comment = mtlang[0][0]
    unm.comment = mtlang[1][0]
    unm.comment = mtlang[2][0]

    with pytest.raises(ValueError):
        unm.id = uuid[1]

    assert unm.get_dict() == {
        '@id': uuid[0],
        'name': mtlangres[0],
        'comment': mtlangres[0]
        }

aim = s.activityIndexEntryMaster()
@pytest.mark.structure
def test_activity_index_entry_master():
    
    aim.id = uuid[0]
    aim.activityNameId = uuid[0]
    aim.activityNameId = uuid[1]
    aim.geographyId = uuid[0]
    aim.startDate = '1981-04-05'
    aim.endDate = '1981-04-05'
    aim.specialActivityType = int_[0]
    aim.systemModelId = uuid[0]

    with pytest.raises(ValueError):
        aim.id = uuid[0]
        aim.geographyId = uuid[0]
        aim.startDate = '1981-04-06'
        aim.endDate = '1981-04-06'
        aim.specialActivityType = int_[1]
        aim.systemModelId = uuid[1]

    assert aim.get_dict() == {
        '@id': uuid[0],
        '@activityNameId': uuid[1],
        '@geographyId': uuid[0],
        '@startDate': '1981-04-05',
        '@endDate': '1981-04-05',
        '@specialActivityType': int_[0],
        '@systemModelId': uuid[0]
        }
    
usm = s.userMaster
@pytest.mark.structure
def test_used_user_master():
    
    usm.activityName = anm
    usm.language = lgm
    usm.geography = gem
    usm.systemModel = smm
    usm.tag = tgm
    usm.macroEconomicScenario = msm
    usm.compartment = ctm
    usm.classificationSystem = csm
    usm.company = cpm
    usm.person = psm
    usm.source = srm
    usm.units = unm
    usm.parameter = prm
    usm.property = ppm
    usm.elementaryExchange = elm
    usm.intermediateExchange = inm
    usm.activityIndexEntry = aim

    assert usm.get_dict() == {
        'activityName': [anm.get_dict()],
        'language': [lgm.get_dict()],
        'geography': [gem.get_dict()],
        'systemModel': [smm.get_dict()],
        'tag': [tgm.get_dict()],
        'macroEconomicScenario': [msm.get_dict()],
        'compartment': [ctm.get_dict()],
        'classificationSystem': [csm.get_dict()],
        'company': [cpm.get_dict()],
        'person': [psm.get_dict()],
        'source': [srm.get_dict()],
        'units': [unm.get_dict()],
        'parameter': [prm.get_dict()],
        'property': [ppm.get_dict()],
        'elementaryExchange': [elm.get_dict()],
        'intermediateExchange': [inm.get_dict()],
        'activityIndexEntry': [aim.get_dict()]
        }

ece = s.customExchange()
@pytest.mark.structure
def test_custom_exchange():
    
    ece.id = uuid[0]
    ece.casNumber = '7732-18-6'
    ece.pageNumbers = string[0]
    ece.specificAllocationPropertyId = uuid[0]
    ece.specificAllocationPropertyIdOverwrittenByChild = 'true'
    ece.specificAllocationPropertyContextId = uuid[0]
    ece.synonym = mtlang[0][0]
    ece.synonym = mtlang[1][0]
    ece.property = pri
    cet = ece.get_class('transferCoefficient')()
    cet.exchangeId = uuid[0]
    for k, v in qtt.items():
        if k != 'comment':
            setattr(cet, k, v.end() if not isinstance(v, list) else v)
    cet.comment = mtlang[2][0]
    cet.comment = mtlang[1][0]
    cet.comment = mtlang[0][0]
    ece.transferCoefficient = cet
    ece.tag = string[0]
    ece.tag = string[1]
    for k, v in qtu.items():
        if k not in ('comment', 'name', 'unitName'):
            setattr(ece, k, v.end() if not isinstance(v, list) else v)
    ece.name = mtlang[2][0]
    ece.name = mtlang[1][0]
    ece.unitName = mtlang[2][0]
    ece.unitName = mtlang[2][0]
    ece.unitName = mtlang[2][0]
    ece.comment = mtlang[2][0]
    ece.comment = mtlang[1][0]
    ece.comment = mtlang[0][0]

    with pytest.raises(ValueError):
        ece.id = uuid[1]
        ece.casNumber = '7732-18-5'
        ece.pageNumbers = string[1]
        ece.specificAllocationPropertyId = uuid[1]
        ece.specificAllocationPropertyIdOverwrittenByChild = 'false'
        ece.specificAllocationPropertyContextId = uuid[1]
        cet.exchangeId = uuid[1]

    assert ece.get_dict() == {
        '@id': uuid[0],
        '@casNumber': '7732-18-6',
        '@pageNumbers': string[0],
        '@specificAllocationPropertyId': uuid[0],
        '@specificAllocationPropertyIdOverwrittenByChild': 'true',
        '@specificAllocationPropertyContextId': uuid[0],
        'synonym': [{'@xml:lang': 'en', '#text': 'lol1'}, {'@xml:lang': 'en', '#text': 'lol2'}, {'@xml:lang': 'en', '#text': 'lol3'}],
        'property': [pri.get_dict()],
        'transferCoefficient': [{
            '@exchangeId': uuid[0]
            } | qtt.get_dict()],
        'tag': strres[0]
        } | qtu.get_dict()

act = s.activityDescription.activity
@pytest.mark.structure
def test_activity():
    
    act.id = uuid[0]
    act.activityNameId = uuid[0] # Double
    act.activityNameId = uuid[1]
    act.activityNameContextId = uuid[1]
    act.parentActivityId = uuid[0]
    act.parentActivityContextId = uuid[0]
    act.inheritanceDepth = int_[0]
    act.inheritanceDepth = int_[1]
    act.type = int_[2]
    act.specialActivityType = int_[3]
    act.specialActivityType = int_[4]
    act.energyValues = int_[0]
    act.energyValues = int_[1]
    act.masterAllocationPropertyId = uuid[0]
    act.masterAllocationPropertyIdOverwrittenByChild = 'true'
    act.masterAllocationPropertyContextId = uuid[1]
    act.datasetIcon = string[0]
    act.activityName = mtlang[2][0]
    act.activityName = mtlang[1][0]
    act.activityName = mtlang[0][0]
    act.synonym = mtlang[0][0]
    act.synonym = mtlang[1][0]
    act.includedActivitiesStart = mtlang[2][0]
    act.includedActivitiesStart = mtlang[1][0]
    act.includedActivitiesStart = mtlang[0][0]
    act.includedActivitiesEnd = mtlang[2][0]
    act.includedActivitiesEnd = mtlang[1][0]
    act.includedActivitiesEnd = mtlang[0][0]
    act.allocationComment = tai
    act.generalComment = tai
    act.tag = string[0]
    act.tag = string[1]

    with pytest.raises(ValueError):
        act.id = uuid[1]
        act.activityNameContextId = uuid[0]
        act.parentActivityId = uuid[1]
        act.parentActivityContextId = uuid[1]
        act.type = int_[0]
        act.masterAllocationPropertyId = uuid[1]
        act.masterAllocationPropertyIdOverwrittenByChild = 'false'
        act.masterAllocationPropertyContextId = uuid[0]
        act.datasetIcon = string[1]
        act.allocationComment = tai
        act.generalComment = tai

    assert act.get_dict() == {
        '@id': uuid[0],
        '@activityNameId': uuid[1],
        '@activityNameContextId': uuid[1],
        '@parentActivityId': uuid[0],
        '@parentActivityContextId': uuid[0],
        '@inheritanceDepth': int_[1],
        '@type': int_[2],
        '@specialActivityType': int_[4],
        '@energyValues': int_[1],
        '@masterAllocationPropertyId': uuid[0],
        '@masterAllocationPropertyIdOverwrittenByChild': 'true',
        '@masterAllocationPropertyContextId': uuid[1],
        '@datasetIcon': string[0],
        'activityName': {'@xml:lang': 'pt', '#text': 'lol4'},
        'synonym': [{'@xml:lang': 'en', '#text': 'lol1'}, {'@xml:lang': 'en', '#text': 'lol2'}, {'@xml:lang': 'en', '#text': 'lol3'}],
        'includedActivitiesStart': mtlangres[1],
        'includedActivitiesEnd': mtlangres[1],
        'allocationComment': [tai.get_dict()],
        'generalComment': [tai.get_dict()],
        'tag': strres[0]
        }

geo = s.activityDescription.geography
@pytest.mark.structure
def test_geography():
    
    geo.geographyId = uuid[0]
    geo.geographyContextId = uuid[1]
    geo.shortname = mtlang[2][0]
    geo.shortname = mtlang[1][0]
    geo.shortname = mtlang[0][0]
    geo.comment = tai
    
    with pytest.raises(ValueError):
        geo.geographyId = uuid[1]
        geo.geographyContextId = uuid[0]
        geo.comment = tai
    
    assert geo.get_dict() == {
        '@geographyId': uuid[0],
        '@geographyContextId': uuid[1],
        'shortname': mtlangres[1],
        'comment': [tai.get_dict()]
        }

tec = s.activityDescription.technology
@pytest.mark.structure
def test_technology():
    
    tec.technologyLevel = int_[1]
    tec.technologyLevel = int_[2]
    tec.comment = tai
    
    with pytest.raises(ValueError):
        tec.comment = tai
    
    assert tec.get_dict() == {
        '@technologyLevel': int_[2],
        'comment': [tai.get_dict()]
        }

tmp = s.activityDescription.timePeriod
@pytest.mark.structure
def test_time_period():
    
    tmp.startDate = '1981-04-05'
    tmp.endDate = '1981-04-05'
    tmp.isDataValidForEntirePeriod = 'true'
    tmp.isDataValidForEntirePeriod = 'false'
    tmp.comment = tai
    
    with pytest.raises(ValueError):
        tmp.startDate = '1981-04-06'
        tmp.endDate = '1981-04-06'
        tmp.comment = tai
    
    assert tmp.get_dict() == {
        '@startDate': '1981-04-05',
        '@endDate': '1981-04-05',
        '@isDataValidForEntirePeriod': 'false',
        'comment': [tai.get_dict()]
        }

mss = s.activityDescription.macroEconomicScenario
@pytest.mark.structure
def test_macro_economic_scenario():
    
    mss.macroEconomicScenarioId = uuid[0]
    mss.macroEconomicScenarioContextId = uuid[1]
    mss.name = mtlang[2][0]
    mss.name = mtlang[1][0]
    mss.name = mtlang[0][0]
    mss.comment = mtlang[2][0]
    mss.comment = mtlang[1][0]
    mss.comment = mtlang[0][0]

    with pytest.raises(ValueError):
        mss.macroEconomicScenarioId = uuid[1]
        mss.macroEconomicScenarioContextId = uuid[0]

    assert mss.get_dict() == {
        '@macroEconomicScenarioId': uuid[0],
        '@macroEconomicScenarioContextId': uuid[1],
        'name': mtlangres[1],
        'comment': mtlangres[1]
        }

acd = s.activityDescription
@pytest.mark.structure
def test_activity_description():
    
    acd.classification = cla

    assert acd.get_dict() == {
        'activity': [act.get_dict()],
        'classification': [cla.get_dict()],
        'geography': [geo.get_dict()],
        'technology': [tec.get_dict()],
        'timePeriod': [tmp.get_dict()],
        'macroEconomicScenario': [mss.get_dict()],
        }

rep = s.modellingAndValidation.representativeness
@pytest.mark.structure
def test_representativeness():
    
    rep.percent = real[0]
    rep.systemModelId = uuid[0]
    rep.systemModelContextId = uuid[1]
    rep.systemModelName = mtlang[2][0]
    rep.systemModelName = mtlang[1][0]
    rep.systemModelName = mtlang[0][0]
    rep.samplingProcedure = mtlang[2][0]
    rep.samplingProcedure = mtlang[1][0]
    rep.samplingProcedure = mtlang[0][0]
    rep.extrapolations = mtlang[2][0]
    rep.extrapolations = mtlang[1][0]
    rep.extrapolations = mtlang[0][0]

    with pytest.raises(ValueError):
        rep.percent = real[1]
        rep.systemModelId = uuid[1]
        rep.systemModelContextId = uuid[0]

    assert rep.get_dict() == {
        '@percent': str(real[0]),
        '@systemModelId': uuid[0],
        '@systemModelContextId': uuid[1],
        'systemModelName': mtlangres[1],
        'samplingProcedure': mtlangres[1],
        'extrapolations': mtlangres[1]
        }

rev = s.modellingAndValidation.get_class('review')()
@pytest.mark.structure
def test_review():
    
    rev.reviewerId = uuid[0]
    rev.reviewerId = uuid[1]
    rev.reviewerContextId = uuid[1]
    rev.reviewerName = string[0]
    rev.reviewerEmail = string[1]
    rev.reviewerName = string[1]
    rev.reviewerEmail = string[0]
    rev.reviewDate = '1981-04-05'
    rev.reviewedMajorRelease = int_[0]
    rev.reviewedMinorRelease = int_[1]
    rev.reviewedMajorRevision = int_[2]
    rev.reviewedMinorRevision = int_[3]
    rev.details = tai
    rev.otherDetails = mtlang[0][0]
    rev.otherDetails = mtlang[1][0]
    rev.otherDetails = mtlang[2][0]

    with pytest.raises(ValueError):
        rev.reviewerContextId = uuid[0]
        rev.reviewDate = '1981-04-06'

    assert rev.get_dict() == {
        '@reviewerId': uuid[1],
        '@reviewerContextId': uuid[1],
        '@reviewerName': string[1],
        '@reviewerEmail': string[0],
        '@reviewDate': '1981-04-05',
        '@reviewedMajorRelease': int_[0],
        '@reviewedMinorRelease': int_[1],
        '@reviewedMajorRevision': int_[2],
        '@reviewedMinorRevision': int_[3],
        'details': [tai.get_dict()],
        'otherDetails': mtlangres[0]
        }

mav = s.modellingAndValidation
@pytest.mark.structure
def test_modelling_and_validation():
    
    mav.review = rev
    
    assert mav.get_dict() == {
        'representativeness': [rep.get_dict()],
        'review': [rev.get_dict()]
        }

deb = s.administrativeInformation.dataEntryBy
@pytest.mark.structure
def test_data_entry_by():
    
    deb.personId = uuid[0]
    deb.personId = uuid[1]
    deb.personContextId = uuid[1]
    deb.isActiveAuthor = 'true'
    deb.personName = string[0]
    deb.personEmail = string[1]
    deb.isActiveAuthor = 'false'
    deb.personName = string[1]
    deb.personEmail = string[0]

    with pytest.raises(ValueError):
        deb.personContextId = uuid[0]
        
    assert deb.get_dict() == {
        '@personId': uuid[1],
        '@personContextId': uuid[1],
        '@isActiveAuthor': 'false',
        '@personName': string[1],
        '@personEmail': string[0]
        }

dgp = s.administrativeInformation.dataGeneratorAndPublication
@pytest.mark.structure
def test_data_generator_and_publication():
    
    dgp.personId = uuid[0]
    dgp.personId = uuid[1]
    dgp.personContextId = uuid[1]
    dgp.personName = string[0]
    dgp.personEmail = string[1]
    dgp.personName = string[1]
    dgp.personEmail = string[0]
    dgp.dataPublishedIn = int_[0]
    dgp.publishedSourceId = uuid[0]
    dgp.publishedSourceIdOverwrittenByChild = 'true'
    dgp.publishedSourceContextId = uuid[0]
    dgp.publishedSourceYear = string[0]
    dgp.publishedSourceFirstAuthor = string[0]
    dgp.isCopyrightProtected = 'false'
    dgp.pageNumbers = string[0]
    dgp.accessRestrictedTo = int_[0]
    dgp.accessRestrictedTo = int_[1]
    dgp.companyId = uuid[0]
    dgp.companyId = uuid[1]
    dgp.companyIdOverwrittenByChild = 1
    dgp.companyContextId = uuid[1]
    dgp.companyCode = 'code'
    dgp.companyCode = 'code1'
    
    with pytest.raises(ValueError):
        dgp.personContextId = uuid[0]
        dgp.dataPublishedIn = int_[1]
        dgp.publishedSourceId = uuid[1]
        dgp.publishedSourceIdOverwrittenByChild = 'false'
        dgp.publishedSourceContextId = uuid[1]
        dgp.publishedSourceId = uuid[1]
        dgp.publishedSourceYear = string[1]
        dgp.publishedSourceFirstAuthor = string[1]
        dgp.isCopyrightProtected = 'true'
        dgp.pageNumbers = string[1]
        dgp.companyIdOverwrittenByChild = 0
        dgp.companyContextId = uuid[0]

    assert dgp.get_dict() == {
        '@personId': uuid[1],
        '@personContextId': uuid[1],
        '@personName': string[1],
        '@personEmail': string[0],
        '@dataPublishedIn': int_[0],
        '@publishedSourceId': uuid[0],
        '@publishedSourceIdOverwrittenByChild': 'true',
        '@publishedSourceContextId': uuid[0],
        '@publishedSourceYear': string[0],
        '@publishedSourceFirstAuthor': string[0],
        '@isCopyrightProtected': 'false',
        '@pageNumbers': string[0],
        '@accessRestrictedTo': int_[1],
        '@companyId': uuid[1],
        '@companyIdOverwrittenByChild': 'true',
        '@companyContextId': uuid[1],
        '@companyCode': 'code1'
        }

fat = s.administrativeInformation.fileAttributes
@pytest.mark.structure
def test_file_attributes():
    
    fat.majorRelease = int_[0]
    fat.majorRelease = int_[1]
    fat.minorRelease = int_[1]
    fat.minorRelease = int_[2]
    fat.majorRevision = int_[2]
    fat.majorRevision = int_[3]
    fat.minorRevision = int_[3]
    fat.minorRevision = int_[4]
    fat.internalSchemaVersion = string[0]
    fat.defaultLanguage = 'en'
    fat.creationTimestamp = '1981-04-07'
    fat.lastEditTimestamp = '1981-04-07'
    fat.fileGenerator = string[1]
    fat.fileTimestamp = '1981-04-07'
    fat.contextId = uuid[0]
    fat.contextName = mtlang[0][0]
    fat.contextName = mtlang[1][0]
    fat.contextName = mtlang[2][0]
    rct = fat.get_class('requiredContext')()
    rct.majorRelease = int_[0]
    rct.majorRelease = int_[1]
    rct.minorRelease = int_[1]
    rct.minorRelease = int_[2]
    rct.majorRevision = int_[2]
    rct.majorRevision = int_[3]
    rct.minorRevision = int_[3]
    rct.minorRevision = int_[4]
    rct.requiredContextId = uuid[0]
    rct.requiredContextFileLocation = string[0]
    rct.requiredContextName = mtlang[0][0]
    rct.requiredContextName = mtlang[1][0]
    rct.requiredContextName = mtlang[2][0]
    fat.requiredContext = rct

    with pytest.raises(ValueError):
        fat.internalSchemaVersion = string[1]
        fat.defaultLanguage = 'pt'
        fat.creationTimestamp = '1981-04-08'
        fat.lastEditTimestamp = '1981-04-08'
        fat.fileGenerator = string[0]
        fat.fileTimestamp = '1981-04-08'
        fat.contextId = uuid[1]
        rct.requiredContextId = uuid[1]
        rct.requiredContextFileLocation = string[1]

    assert fat.get_dict() == {
        '@majorRelease': int_[1],
        '@minorRelease': int_[2],
        '@majorRevision': int_[3],
        '@minorRevision': int_[4],
        '@internalSchemaVersion': string[0],
        '@defaultLanguage': 'en',
        '@creationTimestamp': '1981-04-07T00:00:00',
        '@lastEditTimestamp': '1981-04-07T00:00:00',
        '@fileGenerator': string[1],
        '@fileTimestamp': '1981-04-07T00:00:00',
        '@contextId': uuid[0],
        'contextName': mtlangres[0],
        'requiredContext': [{
            '@majorRelease': int_[1],
            '@minorRelease': int_[2],
            '@majorRevision': int_[3],
            '@minorRevision': int_[4],
            '@requiredContextId': uuid[0],
            '@requiredContextFileLocation': string[0],
            'requiredContextName': mtlangres[0]
            }]
        }

adm = s.administrativeInformation
@pytest.mark.structure
def test_administrative_information():
    
    assert adm.get_dict() == {
        'dataEntryBy': [deb.get_dict()],
        'dataGeneratorAndPublication': [dgp.get_dict()],
        'fileAttributes': [fat.get_dict()]
        }
    
ine = s.flowData.get_class('intermediateExchange')()
@pytest.mark.structure
def test_intermediate_exchange():
    
    ine.intermediateExchangeId = uuid[0]
    ine.intermediateExchangeContextId = uuid[1]
    ine.activityLinkId = uuid[0]
    ine.activityLinkIdOverwrittenByChild = 'true'
    ine.activityLinkContextId = uuid[1]
    ine.productionVolumeAmount = real[0]
    ine.productionVolumeVariableName = string[0]
    ine.productionVolumeMathematicalRelation = string[1]
    ine.productionVolumeSourceId = uuid[0]
    ine.productionVolumeSourceIdOverwrittenByChild = 'false'
    ine.productionVolumeSourceContextId = uuid[1]
    ine.productionVolumeSourceYear = string[0]
    ine.productionVolumeSourceFirstAuthor = string[1]
    ine.productionVolumeComment = mtlang[0][0]
    ine.productionVolumeComment = mtlang[1][0]
    ine.productionVolumeComment = mtlang[2][0]
    ine.productionVolumeUncertainty = unc
    ine.classification = cla
    ine.inputGroup = 3
    ine.outputGroup = 2
    
    for k, v in ece.items():
        if k not in ('comment', 'name', 'unitName', 'synonym'):
            setattr(ine, k, v.end() if not isinstance(v, list) else v)
    ine.synonym = mtlang[0][0]
    ine.synonym = mtlang[1][0]
    ine.name = mtlang[2][0]
    ine.name = mtlang[1][0]
    ine.unitName = mtlang[2][0]
    ine.unitName = mtlang[2][0]
    ine.unitName = mtlang[2][0]
    ine.comment = mtlang[2][0]
    ine.comment = mtlang[1][0]
    ine.comment = mtlang[0][0]

    with pytest.raises(ValueError):
        ine.intermediateExchangeId = uuid[1]
        ine.intermediateExchangeContextId = uuid[0]
        ine.activityLinkId = uuid[1]
        ine.activityLinkIdOverwrittenByChild = 'false'
        ine.activityLinkContextId = uuid[0]
        ine.productionVolumeAmount = real[1]
        ine.productionVolumeVariableName = string[1]
        ine.productionVolumeMathematicalRelation = string[0]
        ine.productionVolumeSourceId = uuid[1]
        ine.productionVolumeSourceIdOverwrittenByChild = 'true'
        ine.productionVolumeSourceContextId = uuid[0]
        ine.productionVolumeSourceYear = string[1]
        ine.productionVolumeSourceFirstAuthor = string[0]
        ine.productionVolumeUncertainty = unc
        ine.inputGroup = 2
        ine.outputGroup = 2

    assert ine.get_dict() == {
        '@intermediateExchangeId': uuid[0],
        '@intermediateExchangeContextId': uuid[1],
        '@activityLinkId': uuid[0],
        '@activityLinkIdOverwrittenByChild': 'true',
        '@activityLinkContextId': uuid[1],
        '@productionVolumeAmount': real[0],
        '@productionVolumeVariableName': string[0],
        '@productionVolumeMathematicalRelation': string[1],
        '@productionVolumeSourceId': uuid[0],
        '@productionVolumeSourceIdOverwrittenByChild': 'false',
        '@productionVolumeSourceContextId': uuid[1],
        '@productionVolumeSourceYear': string[0],
        '@productionVolumeSourceFirstAuthor': string[1],
        'productionVolumeComment': mtlangres[0],
        'productionVolumeUncertainty': [unc.get_dict()],
        'classification': [cla.get_dict()],
        'inputGroup': 3,
        'outputGroup': 2
        } | ece.get_dict()
    
ele = s.flowData.get_class('elementaryExchange')()
@pytest.mark.structure
def test_elementary_exchange():
    
    ele.elementaryExchangeId = uuid[0]
    ele.elementaryExchangeContextId = uuid[1]
    ele.formula = string[0]
    cpt = ele.compartment
    cpt.subcompartmentId = uuid[0]
    cpt.subcompartmentContextId = uuid[1]
    cpt.compartment = mtlang[2][0]
    cpt.compartment = mtlang[1][0]
    cpt.compartment = mtlang[0][0]
    cpt.subcompartment = mtlang[2][0]
    cpt.subcompartment = mtlang[1][0]
    cpt.subcompartment = mtlang[0][0]
    ele.inputGroup = 4
    ele.outputGroup = 4
    
    for k, v in ece.items():
        if k not in ('comment', 'name', 'unitName', 'synonym'):
            setattr(ele, k, v.end() if not isinstance(v, list) else v)
    ele.synonym = mtlang[0][0]
    ele.synonym = mtlang[1][0]
    ele.name = mtlang[2][0]
    ele.name = mtlang[1][0]
    ele.unitName = mtlang[2][0]
    ele.unitName = mtlang[2][0]
    ele.unitName = mtlang[2][0]
    ele.comment = mtlang[2][0]
    ele.comment = mtlang[1][0]
    ele.comment = mtlang[0][0]

    with pytest.raises(ValueError):
        ele.elementaryExchangeId = uuid[1]
        ele.elementaryExchangeContextId = uuid[0]
        ele.formula = string[1]
        ele.inputGroup = 4
        ele.outputGroup = 4
        cpt.subcompartmentId = uuid[1]
        cpt.subcompartmentContextId = uuid[0]

    assert ele.get_dict() == {
        '@elementaryExchangeId': uuid[0],
        '@elementaryExchangeContextId': uuid[1],
        '@formula': string[0],
        'compartment': [{
            '@subcompartmentId': uuid[0],
            '@subcompartmentContextId': uuid[1],
            'compartment': mtlangres[1],
            'subcompartment': mtlangres[1]
            }],
        'inputGroup': 4,
        'outputGroup': 4
        } | ece.get_dict()

par = s.flowData.get_class('parameter')()
@pytest.mark.structure
def test_parameter():
    
    par.parameterId = uuid[0]
    par.parameterContextId = uuid[1]
    
    for k, v in qtu.items(): # Parameters don't have a source
        if k not in ('comment', 'name', 'unitName', 'sourceId', 'sourceIdOverwrittenByChild', 'sourceContextId', 'sourceYear', 'sourceFirstAuthor'):
            setattr(par, k, v.end() if not isinstance(v, list) else v)
    par.name = mtlang[2][0]
    par.name = mtlang[1][0]
    par.unitName = mtlang[2][0]
    par.unitName = mtlang[2][0]
    par.unitName = mtlang[2][0]
    par.comment = mtlang[2][0]
    par.comment = mtlang[1][0]
    par.comment = mtlang[0][0]
    
    nqtu = deepcopy(qtu.get_dict())
    nqtu.pop('@sourceId')
    nqtu.pop('@sourceIdOverwrittenByChild')
    nqtu.pop('@sourceContextId')
    nqtu.pop('@sourceYear')
    nqtu.pop('@sourceFirstAuthor')
    
    with pytest.raises(ValueError):
        par.parameterId = uuid[1]
        par.parameterContextId = uuid[0]
    
    assert par.get_dict() == {
        '@parameterId': uuid[0],
        '@parameterContextId': uuid[1]
        } | nqtu
        
imp = s.flowData.get_class('impactIndicator')()
@pytest.mark.structure
def test_impact_indicator():
    
    imp.impactIndicatorId = uuid[0]
    imp.impactIndicatorContextId = uuid[1]
    imp.impactMethodId = uuid[0]
    imp.impactMethodContextId = uuid[1]
    imp.impactCategoryId = uuid[0]
    imp.impactCategoryContextId = uuid[1]
    imp.amount = real[0]
    
    imp.impactMethodName = mtlang[2][0]
    imp.impactMethodName = mtlang[1][0]
    imp.impactMethodName = mtlang[0][0]
    imp.impactCategoryName = mtlang[0][0]
    imp.impactCategoryName = mtlang[1][0]
    imp.impactCategoryName = mtlang[2][0]
    imp.name = mtlang[2][0]
    imp.name = mtlang[1][0]
    imp.name = mtlang[0][0]
    imp.unitName = mtlang[2][0]
    imp.unitName = mtlang[2][0]
    imp.unitName = mtlang[2][0]
    
    with pytest.raises(ValueError):
        imp.impactIndicatorId = uuid[1]
        imp.impactIndicatorContextId = uuid[0]
        imp.impactMethodId = uuid[1]
        imp.impactMethodContextId = uuid[0]
        imp.impactCategoryId = uuid[1]
        imp.impactCategoryContextId = uuid[0]
        imp.amount = real[1]
    
    assert imp.get_dict() == {
        '@impactIndicatorId': uuid[0],
        '@impactIndicatorContextId': uuid[1],
        '@impactMethodId': uuid[0],
        '@impactMethodContextId': uuid[1],
        '@impactCategoryId': uuid[0],
        '@impactCategoryContextId': uuid[1],
        '@amount': real[0],
        'impactMethodName': mtlangres[1],
        'impactCategoryName': mtlangres[0],
        'name': mtlangres[1],
        'unitName': mtlangres[2]
        }
    
flo = s.flowData
@pytest.mark.structure
def test_flow():
    
    flo.intermediateExchange = ine
    flo.elementaryExchange = ele
    flo.parameter = par
    flo.impactIndicator = imp
    
    assert flo.get_dict() == {
        'intermediateExchange': [ine.get_dict()],
        'elementaryExchange': [ele.get_dict()],
        'parameter': [par.get_dict()],
        'impactIndicator': [imp.get_dict()]
        }

@pytest.mark.structure
def test_ecs2():
    
    assert s.get_dict() == {
            'ecoSpold': {
                '@xmlns': 'http://www.EcoInvent.org/EcoSpold02',
                'activityDataset': {
                    'activityDescription': acd.get_dict(),
                    'flowData': flo.get_dict(),
                    'modellingAndValidation': mav.get_dict(),
                    'administrativeInformation': adm.get_dict()
                    },
                'usedUserMasterData': {
                    '@xmlns': 'http://www.EcoInvent.org/UsedUserMasterData'
                    } | usm.get_dict()
                }
            }

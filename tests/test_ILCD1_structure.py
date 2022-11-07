#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 13 10:03:19 2022

@author: jotape42p
"""

import pytest

from src.Lavoisier.data_structures.ILCD1_structure import (
    Real,
    INT,
    Int1,
    Int6,
    Year,
    Pattern,
    UUID,
    Version,
    GIS,
    DateTime,
    ReviewDateTime,
    BOOL,
    STR,
    FT,
    String,
    NullableString,
    ST,
    MatV,
    MultiLang,
    FTMultiLang,
    StringMultiLang,
    STMultiLang,
    return_enum,
    Languages,
    ILCD1Structure
)
from datetime import datetime


class INT_(INT):
    pass


class Pattern_(Pattern):
    def __init__(self):
        self._pattern = 'a+'


class MultiLang_(MultiLang):
    _text = FT


Enum_normal = return_enum(Languages)
Enum_list = return_enum(Languages, list_=True)

numeric_verification = ('', None, [1], {1: 2})
string_verification = (1, 1.0, None, [''], {'a': ''})
mtlang_verification = ('', 'plain_text', None, 1, 1.0)
enum_verification = ('', 'not_in_enum', 1, 1.0, None, {'a': ''})

# Important: For Validators that doesn't overload the method 'add',
#   the action of several additions in a row will simply return the last value and,
#   thus, are not tested here at multiple_input verifications

@pytest.mark.validator
@pytest.mark.single_input
@pytest.mark.parametrize('class_, type_, input_, validation_result',
                         [
                             *((Real, float, a, b) for a, b in ((2.0,)*2,
                                                               ('2.0', 2.0),
                                                               ('2', 2.0),
                                                               (2, 2.0),
                                                               (-2.0,)*2,
                                                               ('-2.0', -2.0),
                                                               ('-2', -2.0),
                                                               (-2, -2.0))),
                             *((INT_, int, a, b) for a, b in ((2.0, 2),
                                                             ('2', 2),
                                                             (2,)*2)),
                             *((Pattern_, str, a, b) for a, b in (('a',)*2,
                                                                 ('aa',)*2,
                                                                 ('aaa',)*2)),
                             (UUID, str, '4dfe5a1f-cd1a-4fb3-87bf-55bfc40e0818',
                              '4dfe5a1f-cd1a-4fb3-87bf-55bfc40e0818'),
                             (Version, str, '00.00.000',
                              '00.00.000'),
                             *((GIS, str, a, b) for a, b in (("+42.42;-180",)*2,
                                                            ("0;0",)*2,
                                                            ("13.22 ; -3",)*2)),
                             *((c, str, a, b) for a, b in (('1981-04-05',
                                                           datetime.fromisoformat('1981-04-05').isoformat()),
                                                          ('2000-01-01',
                                                           datetime.fromisoformat('2000-01-01').isoformat()),
                                                          ('2019-08-19T13:47:30',
                                                           datetime.fromisoformat('2019-08-19T13:47:30').isoformat()),
                                                          ('2019-08-19T13:47:31Z',
                                                           datetime.fromisoformat('2019-08-19T13:47:31Z'.replace('Z', '+00:00')).isoformat()))
                              for c in (DateTime, ReviewDateTime)),
                             *((BOOL, bool, a, b) for a, b in (('true', True),
                                                              ('false', False),
                                                              ('True', True),
                                                              ('False', False),
                                                              (1, True),
                                                              (0, False),
                                                              ('1', True),
                                                              ('0', False),
                                                              (True,)*2,
                                                              (False,)*2)),
                             *((STR, str, a, b) for a, b in (('a',)*2,
                                                            ('b',)*2,
                                                            ('',)*2)),
                             *((MultiLang_, list, a, b) for a, b in (([],)*2,
                                                                    ({'@index': 1, '@lang': 'en', '#text': ''},
                                                                     [{'@xml:lang': 'en', '#text': ''}]))),
                             *((Enum_normal, str, a, b) for a, b in (('en',)*2,
                                                                    ('pt',)*2,
                                                                    ('fr',)*2)),
                             *((Enum_list, list, a, b) for a, b in (('aa', ['aa']),
                                                                   (['en', 'fr'],)*2,
                                                                   (['pt'],)*2)),
                         ])
def test_single_input_validation(class_, type_, input_, validation_result):
    r = class_()
    a = r.add(input_).end()
    assert isinstance(a, type_)
    assert a == validation_result


@pytest.mark.validator
@pytest.mark.multiple_input
@pytest.mark.parametrize('class_, inputs_',
                         [
                             (Int6, ((a, b) for a, b in ((10, 10),
                                                         (20, [10, 20]),
                                                         (30, [10, 20, 30])))),
                             (FT, ((a, b) for a, b in (('a', 'a'),
                                                       ('b', 'a\nb'),
                                                       ('c', 'a\nb\nc')))),
                             (MultiLang_, ((a, b) for a, b in (([],)*2,
                                                               ([],)*2))),  # Second verification to see if end doesn't modify self._x
                             (MultiLang_, ((a, b) for a, b in (({'@index': 1, '@lang': 'en', '#text': ''},
                                                                [{'@xml:lang': 'en', '#text': ''}]),
                                                               ({'@index': '1', '@lang': 'en', '#text': 'lol'},
                                                                [{'@xml:lang': 'en', '#text': 'lol'}]),
                                                               ([{'@index': 1, '@lang': 'en', '#text': 'lol1'},
                                                                 {'@index': 1, '@lang': 'en', '#text': ''}],
                                                                [{'@xml:lang': 'en', '#text': 'lol; lol1'}])
                                                               ))),  # Start with dict, get dict, get list
                             (MultiLang_, ((a, b) for a, b in (([{'@index': 1, '@lang': 'en', '#text': 'lol1'},
                                                                 {'@index': 1, '@lang': 'en',
                                                                     '#text': 'lol2'},
                                                                 {'@index': 2, '@lang': 'en',
                                                                     '#text': 'lol3'},
                                                                 {'@index': 2, '@lang': 'en', '#text': 'lol4'}],
                                                                [{'@xml:lang': 'en', '#text': 'lol1; lol2\nlol3; lol4'}]),
                                                               ({'@index': 1, '@lang': 'fr', '#text': 'fl'},
                                                                [{'@xml:lang': 'en', '#text': 'lol1; lol2\nlol3; lol4'},
                                                                 {'@xml:lang': 'fr', '#text': 'fl'}]),
                                                               ([{'@index': 1, '@lang': 'en', '#text': 'lol5'},
                                                                 {'@index': 1, '@lang': 'pt',
                                                                     '#text': 'lol1'},
                                                                 {'@index': 2, '@lang': 'en',
                                                                     '#text': 'lol6'},
                                                                 {'@index': 2, '@lang': 'pt', '#text': 'lol2'}],
                                                                [{'@xml:lang': 'en', '#text': 'lol1; lol2; lol5\nlol3; lol4; lol6'},
                                                                 {'@xml:lang': 'fr',
                                                                     '#text': 'fl'},
                                                                 {'@xml:lang': 'pt', '#text': 'lol1\nlol2'}])
                                                               ))),  # Start with list, get dict, get list
                             (MultiLang_, ((a, b) for a, b in (([{'@index': 1, '@lang': 'en', '#text': 'lol1'},
                                                                 {'@index': 1, '@lang': 'pt', '#text': 'lol2'}],
                                                                [{'@xml:lang': 'en', '#text': 'lol1'},
                                                                 {'@xml:lang': 'pt', '#text': 'lol2'}]),
                                                               ([{'@index': 1, '@lang': 'pt', '#text': 'lol1'},
                                                                 {'@index': 1, '@lang': 'en', '#text': 'lol2'}],
                                                                [{'@xml:lang': 'en', '#text': 'lol1; lol2'},
                                                                 {'@xml:lang': 'pt', '#text': 'lol2; lol1'}]),
                                                               ({'@index': 2, '@lang': 'en', '#text': 'lol3'},
                                                                [{'@xml:lang': 'en', '#text': 'lol1; lol2\nlol3'},
                                                                 {'@xml:lang': 'pt', '#text': 'lol2; lol1'}])
                                                               ))),  # Start with list, get list, get dict
                             (FTMultiLang, ((a, b) for a, b in (([{'@index': 1, '@lang': 'en', '#text': 'lol1 '*50},
                                                                 {'@index': 1, '@lang': 'en', '#text': 'lol2 '*50}],
                                                                [{'@xml:lang': 'en', '#text': 'lol1 '*50+'; '+'lol2 '*50}]),
                                                                ([{'@index': 1, '@lang': 'en', '#text': 'lol3 '*50},
                                                                 {'@index': 1, '@lang': 'en', '#text': 'lol4 '*50}],
                                                                [{'@xml:lang': 'en', '#text': 'lol1 '*50+'; '+'lol2 '*50+'; '+'lol3 '*50+'; '+'lol4 '*50}]),
                                                                ({'@index': 1, '@lang': 'en', '#text': 'loln '*500},
                                                                [{'@xml:lang': 'en', '#text': 'lol1 '*50+'; '+'lol2 '*50+'; '+'lol3 '*50+'; '+'lol4 '*50+'; '+'loln '*500}])
                                                                ))),
                             (StringMultiLang, ((a, b) for a, b in (([{'@index': 1, '@lang': 'en', '#text': 'lol1 '*50},
                                                                      {'@index': 1, '@lang': 'en', '#text': 'lol2 '*50}],
                                                                     [{'@xml:lang': 'en', '#text': 'lol1 '*50+';'},
                                                                      {'@xml:lang': 'en', '#text': 'lol2 '*49+'lol2'}]),
                                                                    ([{'@index': 1, '@lang': 'en', '#text': 'lol3 '*50},
                                                                      {'@index': 1, '@lang': 'en', '#text': 'lol4 '*50}],
                                                                     [{'@xml:lang': 'en', '#text': 'lol1 '*50+';'},
                                                                        {'@xml:lang': 'en',
                                                                         '#text': 'lol2 '*50+';'},
                                                                        {'@xml:lang': 'en',
                                                                         '#text': 'lol3 '*50+';'},
                                                                        {'@xml:lang': 'en', '#text': 'lol4 '*49+'lol4'}]),
                                                                    ({'@index': 1, '@lang': 'en', '#text': 'loln '*500},
                                                                     [{'@xml:lang': 'en', '#text': 'lol1 '*50+';'},
                                                                        {'@xml:lang': 'en',
                                                                         '#text': 'lol2 '*50+';'},
                                                                        {'@xml:lang': 'en',
                                                                         '#text': 'lol3 '*50+';'},
                                                                        {'@xml:lang': 'en',
                                                                         '#text': 'lol4 '*50+';'},
                                                                        *({'@xml:lang': 'en', '#text': 'loln '*89+'loln'},)*5,
                                                                        {'@xml:lang': 'en', '#text': 'loln '*48+'loln'}])
                                                                    ))),
                             (STMultiLang, ((a, b) for a, b in (([{'@index': 1, '@lang': 'en', '#text': 'lol1 '*50},
                                                                 {'@index': 1, '@lang': 'en', '#text': 'lol2 '*50}],
                                                                [{'@xml:lang': 'en', '#text': 'lol1 '*50+'; '+'lol2 '*50}]),
                                                                ([{'@index': 1, '@lang': 'en', '#text': 'lol3 '*50},
                                                                 {'@index': 1, '@lang': 'en', '#text': 'lol4 '*50}],
                                                                [{'@xml:lang': 'en', '#text': 'lol1 '*50+'; '+'lol2 '*50+'; '+'lol3 '*50+';'},
                                                                 {'@xml:lang': 'en', '#text': 'lol4 '*49+'lol4'}]),
                                                                ({'@index': 1, '@lang': 'en', '#text': 'loln '*500},
                                                                [{'@xml:lang': 'en', '#text': 'lol1 '*50+'; '+'lol2 '*50+'; '+'lol3 '*50+';'},
                                                                 {'@xml:lang': 'en',
                                                                     '#text': 'lol4 '*50+';'},
                                                                 *({'@xml:lang': 'en',
                                                                     '#text': 'loln '*189+'loln'},)*2,
                                                                 {'@xml:lang': 'en', '#text': 'loln '*118+'loln'}])
                                                                ))),
                             (Enum_list, ((a, b) for a, b in (('aa', ['aa']),
                                                              (['en', 'fr'], [
                                                               'aa', 'en', 'fr']),
                                                              (['pt'], ['aa', 'en', 'fr', 'pt'])))),
                         ])
def test_multiple_input_validation(class_, inputs_):
    r = class_()
    for input_, validation_result in inputs_:
        r = r.add(input_)
        assert r.end() == validation_result


@pytest.mark.validator
@pytest.mark.single_input
@pytest.mark.parametrize('class_, error, input_',
                         [
                             (INT_, ValueError, -2),
                             (Int1, ValueError, 10),
                             (Int6, ValueError, 1000000),
                             (Year, ValueError, 10000),
                             (Year, ValueError, 100),
                             (Pattern_, ValueError, ''),
                             (Enum_normal, TypeError, [1]),
                             (Enum_list, ValueError, [1]),
                             *((DateTime, ValueError, a) for a in ('2000',
                                                                  '99999',
                                                                  '2009-13-01',
                                                                  '1002-02-59',
                                                                  '1002-02-01T25:40:20',
                                                                  '1002-02-01T22:70:20',
                                                                  '1002-02-01T22:40:70')),
                             *((BOOL, ValueError, a)
                              for a in numeric_verification),
                             *((String, ValueError, a) for a in ('', 'b'*501)),
                             (NullableString, ValueError, 'b'*501),
                             (ST, ValueError, 'b'*1001),
                             (MatV, ValueError, 'b'*51),
                             *((MultiLang_, ValueError, a) for a in ({'@index': 'lol', '@lang': 'en', '#text': 'lol'},
                                                                    {'@index': 1, '@lang': 'lol', '#text': 'lol'})),
                             *((c, TypeError, a)
                              for a in numeric_verification for c in (Real, INT_)),
                             *((c, TypeError, a) for a in string_verification for c in (
                                 Pattern, DateTime, STR)),
                             *((c, ValueError, a) for a in enum_verification for c in (
                                 Enum_normal, Enum_list)), # Error because it is not one of the enumeration values
                             *((MultiLang_, TypeError, a)
                              for a in mtlang_verification),
                             (Enum_normal, TypeError, ['pt', 'en']),
                             *((MultiLang_, KeyError, a) for a in ({},
                                                                  {'#text': 'lol'},
                                                                  {'@lang': 'en'},
                                                                  {'@index': 1},
                                                                  {'@lang': 'en',
                                                                      '#text': 'lol'},
                                                                  {'@index': 1,
                                                                      '@lang': 'en'},
                                                                  {'@index': 1, '#text': 'lol'})),
                         ])
def test_single_input_validator_error(class_, error, input_):
    r = class_()
    with pytest.raises(error):
        r.add(input_).end()


@pytest.mark.validator
@pytest.mark.multiple_input
@pytest.mark.parametrize('class_, inputs_',
                         [
                             (String, ('b'*250, 'b'*350)),
                             (NullableString, ('b'*250, 'b'*350)),
                             (ST, ('b'*500, 'b'*600)),
                             (MatV, ('b'*25, 'b'*35)),
                         ])
def test_multiple_input_validator_value_error(class_, inputs_):
    r = class_()
    for i, input_ in enumerate(inputs_):
        if i != len(inputs_)-1:
            r = r.add(input_)
        else:
            with pytest.raises(ValueError):
                r.add(input_).end()
    
# Ways of attribution for subclasses of 'Verification'
# [1] Direct attribution: Unique method
#
# dsi.c_UUID = '4dfe5a1f-cd1a-4fb3-87bf-55bfc40e0818'
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
# f = fpr.referenceToFlowPropertyDataSet # Non-unique
# f = ref
# fpr.referenceToFlowPropertyDataSet = f # This line has to be done in order for the value of 'f' to be considered
#
# f = fpr.referenceToFlowPropertyDataSet # Unique
# f.c_subReference = 'lol3' # Changes directly the field

uuid = ('4dfe5a1f-cd1a-4fb3-87bf-55bfc40e0818', 'cd373f89-264e-4fe3-85c4-d0c38970ada6')
version = ('00.00.000', '01.00.000')
real = (10.0, 20.0)
string = ('string', 'string 2', 'string 3')
strres = ('string\nstring 2', 'string 2\nstring 3', 'string\nstring 2\nstring 3')
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
             [{'@xml:lang': 'pt', '#text': 'lol4\nlol5'},
              {'@xml:lang': 'en', '#text': 'lol3; lol1; lol2'}],
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
        _ = a.not_a_field
    with pytest.raises(AttributeError):
        a.not_a_field = ''

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
    ref.a_type = 'source data set'
    ref.a_refObjectId = uuid[0]
    ref.a_version = version[0]
    ref.a_uri = string[0]
    ref.c_subReference = string[0]
    ref.c_subReference = string[1]
    ref.c_shortDescription = mtlang[0][0]
    ref.c_shortDescription = mtlang[1][0]
    ref.c_shortDescription = mtlang[2][0]

    with pytest.raises(ValueError):
        ref.a_type = 'contact data set'
        ref.a_refObjectId = uuid[1]
        ref.a_version = version[1]
        ref.a_uri = string[2]

    assert ref.get_dict() == {'@type': 'source data set',
                              '@refObjectId': uuid[0],
                              '@version': version[0],
                              '@uri': string[0],
                              'c:subReference': strres[0],
                              'c:shortDescription': mtlangres[0]}

clf = s.classification()
@pytest.mark.structure
def test_classification():
    clf.a_name = string[0]
    clf.a_classes = string[0]

    cl_1 = clf.get_class('c_class')()
    cl_1.a_level = 0
    cl_1.a_classId = string[0]
    cl_1.t_ = string[0]
    cl_1.t_ = string[1]
    clf.c_class = cl_1

    cl_2 = clf.get_class('c_class')()
    cl_2.a_level = 1
    cl_2.a_classId = string[0]
    cl_2.t_ = string[0]
    cl_2.t_ = string[1]
    clf.c_class = cl_2

    with pytest.raises(KeyError):
        cl_1 = clf.c_class

    with pytest.raises(ValueError):
        clf.a_name = string[1]
        clf.a_classes = string[1]
        cl_1.a_level = 2
        cl_1.a_classId = string[1]
        cl_2.a_level = 2
        cl_2.a_classId = string[1]

    assert clf.get_dict() == {'@name': string[0],
                              '@classes': string[0],
                              'c:class': [{'@level': 0, '@classId': string[0], '#text': strres[0]},
                                          {'@level': 1, '@classId': string[0], '#text': strres[0]}]}

fpr = s.flow_property()
@pytest.mark.structure
def test_flow_property():
    fpr.a_dataSetInternalID = 0
    fpr.referenceToFlowPropertyDataSet = ref
    
    get_unique2 = fpr.referenceToFlowPropertyDataSet
    get_unique2.c_subReference = string[2]
    
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
        fpr.a_dataSetInternalID = 1
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
def test_data_set_information():
    dsi.c_UUID = uuid[0]

    name = dsi.name
    name.baseName = mtlang[2][0]
    name.baseName = mtlang[1][0]
    name.baseName = mtlang[0][0]
    name.treatmentStandardsRoutes = mtlang[0][0]
    name.mixAndLocationTypes = mtlang[1][0]
    name.functionalUnitFlowProperties = mtlang[2][0]

    dsi.identifierOfSubDataSet = string[0]
    dsi.c_synonyms = mtlang[2][0]
    dsi.c_synonyms = mtlang[2][0]
    dsi.c_synonyms = mtlang[2][0]

    cproc = dsi.complementingProcesses
    rcproc_1 = cproc.get_class('referenceToComplementingProcess')()
    rcproc_2 = cproc.get_class('referenceToComplementingProcess')()

    rcproc_1.a_type = 'source data set'
    rcproc_1.a_refObjectId = uuid[0]
    rcproc_1.a_version = version[0]
    rcproc_1.a_uri = string[0]
    rcproc_1.c_subReference = string[0]
    rcproc_1.c_subReference = string[1]
    rcproc_1.c_shortDescription = mtlang[0][0]
    rcproc_1.c_shortDescription = mtlang[1][0]
    rcproc_1.c_shortDescription = mtlang[2][0]
    cproc.referenceToComplementingProcess = rcproc_1

    rcproc_2.a_type = 'source data set'
    rcproc_2.a_refObjectId = uuid[1]
    rcproc_2.a_version = version[0]
    rcproc_2.a_uri = string[1]
    rcproc_2.c_subReference = string[1]
    rcproc_2.c_subReference = string[2]
    rcproc_2.c_shortDescription = mtlang[2][0]
    rcproc_2.c_shortDescription = mtlang[1][0]
    rcproc_2.c_shortDescription = mtlang[0][0]
    cproc.referenceToComplementingProcess = rcproc_2

    dsi.classificationInformation.c_classification = clf
    dsi.c_generalComment = mtlang[1][0]
    dsi.c_generalComment = mtlang[1][0]
    dsi.c_generalComment = mtlang[1][0]
    dsi.referenceToExternalDocumentation = ref
    dsi.referenceToExternalDocumentation = ref
    dsi.referenceToExternalDocumentation = ref

    with pytest.raises(KeyError):
        cproc = dsi.get_class('complementingProcesses')
        name = dsi.get_class('c_UUID')
        rcproc_1 = cproc.referenceToComplementingProcess

    with pytest.raises(ValueError):
        dsi.c_UUID = uuid[0]
        dsi.name = name
        dsi.identifierOfSubDataSet = string[1]
        dsi.classificationInformation = ''
        dsi.complementingProcesses = cproc

    assert dsi.get_dict() == {'c:UUID': uuid[0],
                              'name': [{'baseName': [{'@xml:lang': 'pt',
                                                      '#text': 'lol4\nlol5'},
                                                     {'@xml:lang': 'en',
                                                      '#text': 'lol3; lol1; lol2'}],
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
    qrf.a_type = "Reference flow(s)"
    qrf.referenceToReferenceFlow = 123
    qrf.referenceToReferenceFlow = 124
    qrf.referenceToReferenceFlow = 125
    qrf.functionalUnitOrOther = mtlang[0][0]
    qrf.functionalUnitOrOther = mtlang[1][0]
    qrf.functionalUnitOrOther = mtlang[2][0]

    with pytest.raises(ValueError):
        qrf.a_type = "Functional unit"

    assert qrf.get_dict() == {'@type': 'Reference flow(s)',
                              'referenceToReferenceFlow': [123, 124, 125],
                              'functionalUnitOrOther': mtlangres[0]}

tim = s.time
@pytest.mark.structure
def test_time():
    tim.c_referenceYear = 2000
    tim.c_dataSetValidUntil = 2000
    tim.c_timeRepresentativenessDescription = mtlang[0][0]
    tim.c_timeRepresentativenessDescription = mtlang[1][0]
    tim.c_timeRepresentativenessDescription = mtlang[2][0]

    with pytest.raises(ValueError):
        tim.c_referenceYear = 2001
        tim.c_dataSetValidUntil = 2001

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
    loc.a_location = string[0]
    loc.a_latitudeAndLongitude = "+89.2;-130.3"
    loc.descriptionOfRestrictions = mtlang[0][0]

    sloc_1 = geo.get_class('subLocationOfOperationSupplyOrProduction')()
    sloc_1.a_subLocation = string[1]
    sloc_1.a_latitudeAndLongitude = "+89;-130"
    sloc_1.descriptionOfRestrictions = mtlang[1][0]
    geo.subLocationOfOperationSupplyOrProduction = sloc_1

    sloc_2 = geo.get_class('subLocationOfOperationSupplyOrProduction')()
    sloc_2.a_subLocation = string[2]
    sloc_2.a_latitudeAndLongitude = "89;130"
    sloc_2.descriptionOfRestrictions = mtlang[2][0]
    geo.subLocationOfOperationSupplyOrProduction = sloc_2
    
    with pytest.raises(KeyError):
        sloc_1 = geo.subLocationOfOperationSupplyOrProduction

    with pytest.raises(ValueError):
        loc.a_location = string[2]
        loc.a_latitudeAndLongitude = "0;0"
        sloc_1.a_subLocation = string[0]
        sloc_1.a_latitudeAndLongitude = "0;0"
        sloc_2.a_subLocation = string[1]
        sloc_2.a_latitudeAndLongitude = "0;0"

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
def test_data_sources_treatment_and_representativeness():
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
    compl_1.a_type = "Summer smog"
    compl_1.a_value = "Relevant flows missing"
    compl_2.a_type = "Eutrophication"
    compl_2.a_value = "Topic not relevant"
    mav.completeness.completenessElementaryFlows = compl_1
    mav.completeness.completenessElementaryFlows = compl_2
    
    mav.completeness.completenessOtherProblemField = mtlang[0][0]

    with pytest.raises(KeyError):
        compl_1 = mav.completeness.completenessElementaryFlows
        
    with pytest.raises(ValueError):
        compl_1.a_type = "Eutrophication"
        compl_1.a_value = "Topic not relevant"
        compl_2.a_type = "Summer smog"
        compl_2.a_value = "Relevant flows missing"
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
    
    n.a_type = "Independent external review"
    
    sc1 = n.get_class('c_scope')()
    sc2 = n.get_class('c_scope')()
    sc1.a_name = "Raw data"
    mt11 = sc1.get_class('c_method')()
    mt12 = sc1.get_class('c_method')()
    mt11.a_name = "Validation of data sources"
    mt12.a_name = "Sample tests on calculations"
    sc1.c_method = mt11
    sc1.c_method = mt12
    sc2.a_name = "Unit process(es), single operation"
    mt21 = sc2.get_class('c_method')()
    mt22 = sc2.get_class('c_method')()
    mt21.a_name = "Energy balance"
    mt22.a_name = "Element balance"
    sc2.c_method = mt21
    sc2.c_method = mt22
    n.c_scope = sc1
    n.c_scope = sc2
    
    dqi1 = n.c_dataQualityIndicators.get_class('c_dataQualityIndicator')()
    dqi2 = n.c_dataQualityIndicators.get_class('c_dataQualityIndicator')()
    dqi1.a_name = "Technological representativeness"
    dqi1.a_value = "Good"
    dqi2.a_name = "Time representativeness"
    dqi2.a_value = "Fair"
    n.c_dataQualityIndicators.c_dataQualityIndicator = dqi1
    n.c_dataQualityIndicators.c_dataQualityIndicator = dqi2
    
    n.c_reviewDetails = mtlang[0][0]
    n.c_referenceToNameOfReviewerAndInstitution = ref
    n.c_referenceToNameOfReviewerAndInstitution = ref
    n.c_otherReviewDetails = mtlang[1][0]
    n.c_referenceToCompleteReviewReport = ref
    
    mav.validation.review = n
    
    with pytest.raises(KeyError):
        n = mav.validation.review
        sc1 = n.c_scope
        mt11 = sc1.c_method
        dqi1 = n.c_dataQualityIndicators.c_dataQualityIndicator
    
    with pytest.raises(ValueError):
        n.a_type = "Accredited third party review"
        sc1.a_name = "Unit process(es), single operation"
        sc2.a_name = "Raw data"
        mt11.name = "Element balance"
        mt12.name = "Energy balance"
        mt21.name = "Sample tests on calculations"
        mt22.name = "Validation of data sources"
        dqi1.a_name = "Time representativeness"
        dqi2.a_name = "Technological representativeness"
        dqi1.a_value = "Fair"
        dqi2.a_value = "Good"
        n.c_dataQualityIndicators = ''
        n.c_referenceToCompleteReviewReport = ref
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
    comp_1.c_referenceToComplianceSystem = ref
    comp_1.c_approvalOfOverallCompliance = "Not compliant"
    comp_1.c_nomenclatureCompliance = "Not compliant"
    comp_1.c_methodologicalCompliance = "Not compliant"
    comp_1.c_reviewCompliance = "Not compliant"
    comp_1.c_documentationCompliance = "Not compliant"
    comp_1.c_qualityCompliance = "Not compliant"
    mav.complianceDeclarations.compliance = comp_1

    with pytest.raises(KeyError):
        comp_1 = mav.complianceDeclarations.compliance
        
    with pytest.raises(ValueError):
        mav.complianceDeclarations = ''
        comp_1.compliance = ''
        comp_1.compliance.c_referenceToComplianceSystem = ref
        comp_1.compliance.c_approvalOfOverallCompliance = "Not defined"
        comp_1.compliance.c_nomenclatureCompliance = "Not defined"
        comp_1.c_methodologicalCompliance = "Not defined"
        comp_1.c_reviewCompliance = "Not defined"
        comp_1.c_documentationCompliance = "Not defined"
        comp_1.c_qualityCompliance = "Not defined"

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
    adm.c_commissionerAndGoal.c_referenceToCommissioner = ref
    adm.c_commissionerAndGoal.c_referenceToCommissioner = ref
    adm.c_commissionerAndGoal.c_project = mtlang[0][0]
    adm.c_commissionerAndGoal.c_intendedApplications = mtlang[1][0]

    with pytest.raises(ValueError):
        adm.c_commissionerAndGoal = ''

    assert adm.c_commissionerAndGoal.get_dict() == {'c:referenceToCommissioner': [ref.get_dict(),
                                                                                  ref.get_dict()],
                                                    'c:project': mtlang[0][1],
                                                    'c:intendedApplications': mtlang[1][1]
                                                    }

@pytest.mark.structure
def test_data_generator():
    adm.dataGenerator.c_referenceToPersonOrEntityGeneratingTheDataSet = ref
    adm.dataGenerator.c_referenceToPersonOrEntityGeneratingTheDataSet = ref

    assert adm.dataGenerator.get_dict() == {
        'c:referenceToPersonOrEntityGeneratingTheDataSet': [ref.get_dict(), ref.get_dict()]}
    
    
    with pytest.raises(ValueError):
        adm.dataGenerator = ''

@pytest.mark.structure
def test_data_entry_by():
    adm.dataEntryBy.c_timeStamp = '2000-09-12T23:45:12'
    adm.dataEntryBy.c_referenceToDataSetFormat = ref
    adm.dataEntryBy.c_referenceToDataSetFormat = ref
    adm.dataEntryBy.c_referenceToConvertedOriginalDataSetFrom = ref
    adm.dataEntryBy.c_referenceToPersonOrEntityEnteringTheData = ref
    adm.dataEntryBy.c_referenceToDataSetUseApproval = ref
    adm.dataEntryBy.c_referenceToDataSetUseApproval = ref

    with pytest.raises(ValueError):
        adm.dataEntryBy = ''
        adm.dataEntryBy.c_timeStamp = '2000-09-13'
        adm.dataEntryBy.c_referenceToConvertedOriginalDataSetFrom = ref
        adm.dataEntryBy.c_referenceToPersonOrEntityEnteringTheData = ref

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
    adm.publicationAndOwnership.c_dateOfLastRevision = '2000-09-12T23:45:12'
    adm.publicationAndOwnership.c_dateOfLastRevision = '2020-09-12T23:45:12'
    adm.publicationAndOwnership.c_dataSetVersion = '01.00.000'
    adm.publicationAndOwnership.c_referenceToPrecedingDataSetVersion = ref
    adm.publicationAndOwnership.c_referenceToPrecedingDataSetVersion = ref
    adm.publicationAndOwnership.c_permanentDataSetURI = string[0]
    adm.publicationAndOwnership.c_workflowAndPublicationStatus = "Working draft"
    adm.publicationAndOwnership.c_referenceToUnchangedRepublication = ref
    adm.publicationAndOwnership.c_referenceToRegistrationAuthority = ref
    adm.publicationAndOwnership.c_registrationNumber = string[0]
    adm.publicationAndOwnership.c_referenceToOwnershipOfDataSet = ref
    adm.publicationAndOwnership.c_copyright = 'true'
    adm.publicationAndOwnership.c_referenceToEntitiesWithExclusiveAccess = ref
    adm.publicationAndOwnership.c_referenceToEntitiesWithExclusiveAccess = ref
    adm.publicationAndOwnership.c_licenseType = "Free of charge for all users and uses"
    adm.publicationAndOwnership.c_licenseType = "Free of charge for some user types or use types"
    adm.publicationAndOwnership.c_accessRestrictions = mtlang[2][0]

    with pytest.raises(ValueError):
        adm.publicationAndOwnership = ''
        adm.publicationAndOwnership.c_dataSetVersion = '02.00.000'
        adm.publicationAndOwnership.c_permanentDataSetURI = string[1]
        adm.publicationAndOwnership.c_workflowAndPublicationStatus = "Final draft for internal review"
        adm.publicationAndOwnership.c_referenceToUnchangedRepublication = ref
        adm.publicationAndOwnership.c_referenceToRegistrationAuthority = ref
        adm.publicationAndOwnership.c_registrationNumber = string[1]
        adm.publicationAndOwnership.c_referenceToOwnershipOfDataSet = ref
        adm.publicationAndOwnership.c_copyright = 'true'

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
    var_1.a_name = 'Equação1'
    var_1.meanValue = real[0]
    var_1.minimumValue = real[0]
    var_1.maximumValue = real[0]
    var_1.uncertaintyDistributionType = 'normal'
    var_1.relativeStandardDeviation95In = real[0]
    var_1.comment = mtlang[1][0]
    mth.variableParameter = var_1

    var_2 = mth.get_class('variableParameter')()
    var_2.a_name = 'Equação2'
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
        var_1.a_name = 'Equação2'
        var_1.meanValue = real[1]
        var_1.minimumValue = real[1]
        var_1.maximumValue = real[1]
        var_1.uncertaintyDistributionType = 'triangular'
        var_1.relativeStandardDeviation95In = real[1]
        var_2.a_name = 'Equação1'
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
    
    e.a_dataSetInternalID = 0
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
    al_1.a_internalReferenceToCoProduct = 0
    al_1.a_allocatedFraction = 0.324682763
    al_2.a_internalReferenceToCoProduct = 1
    al_2.a_allocatedFraction = 0.125124674
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
        e.a_dataSetInternalID = 1
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
        al_1.a_internalReferenceToCoProduct = 2
        al_2.a_internalReferenceToCoProduct = 2
        al_1.a_allocatedFraction = 0.1
        al_2.a_allocatedFraction = 0.1
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

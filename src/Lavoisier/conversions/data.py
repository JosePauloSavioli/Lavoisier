#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 10:02:00 2021

@author: jotape42p
"""

child_type = {'0': None,
              '-1':'child from: ', # Some datasets had -1 as they were child datasets
              '1':'geography child from: ', 
              '2':'technological child from: ', 
              '3':'macroeconomic child from: '}

child_type_ = {v: k for k, v in child_type.items()}

type_process = {'1':'Unit process, black box',
                '2':'LCI result'}

type_process_ = {'Unit process, single operation': '1',
                    'Unit process, black box': '1',
                    'LCI result': '2',
                    'Partly terminated system': '1',
                    'Avoided product system': '1'}

special_activity = {'0':'ordinary transforming activity',
                    '1':'market activity',
                    '2':'IO activity',
                    '3':'residual activity',
                    '4':'production mix',
                    '5':'import activity',
                    '6':'supply mix',
                    '7':'export activity',
                    '8':'re-Export activity',
                    '9':'correction activity',
                    '10':'market group'}

special_activity_ = {v: k for k, v in special_activity.items()}

energy = {'0':'undefined',
          '1':'net calorific value',
          '2':'gross calorific value'}

energy_ = {v: k for k, v in energy.items()}

tech = {'0':'Undefined',
        '1':'New',
        '2':'Modern',
        '3':'Current',
        '4':'Old',
        '5':'Outdated'}

tech_ = {v: k for k, v in tech.items()}

time_period = {'true':'Data is valid for the entire period.',
               'false': 'Data is not valid for the entire period.'}

time_period_ = {v: k for k, v in time_period.items()}

inputGroup_type = {'1':'Materials/Fuels',
                   '2':'Electricity/Heat',
                   '3':'Services',
                   '4':'From Environment',
                   '5':'From Technosphere (unspecified)'}

outputGroup_type = {'0':'Reference Product',
                    '2':'By-product;',
                    '3':'Material for Treatment',
                    '4':'To Environment',
                    '5':'Stock Additions'}

system_model = {'Undefined':'Not applicable',
                'Allocation, manually linked':'Attributional',
                'Allocation by dry mass':'Attributional',
                'Allocation at the point of substitution':'Attributional',
                'Allocation, legacy':'Attributional',
                'Allocation by carbon':'Attributional',
                'Allocation by revenue':'Attributional',
                'Allocation, cut-off by classification':'Attributional',
                'Substitution, consequential, long-term':'Consequential',
                'Substitution, constrained by-products':'Consequential'}

system_model_2 = {'Undefined':'Not applicable',
                'Allocation, manually linked':'Allocation - other explicit assignment',
                'Allocation by dry mass':'Allocation - mass',
                'Allocation at the point of substitution':'Substitution - average, market price correction',
                'Allocation, legacy':'Allocation - other explicit assignment',
                'Allocation by carbon':'Allocation - element content',
                'Allocation by revenue':'Allocation - market value',
                'Allocation, cut-off by classification':'Allocation - 100% to main function',
                'Substitution, consequential, long-term':'Substitution - specific',
                'Substitution, constrained by-products':'Substitution - specific'}

system_model_1_ = {
    "Allocation, manually linked": "ba1ff5c1-9a0b-41ce-a5f8-fc2ff3163405",
    "Allocation by dry mass": "a253b4b8-5257-4c53-be06-d5b4d78ea407",
    "Allocation at the point of substitution": "06590a66-662a-4885-8494-ad0cf410f956",
    "Allocation, legacy": "4352935f-32fb-41a5-ad98-bec679e527ca",
    "Allocation, cut-off by classification": "290c1f85-4cc4-4fa1-b0c8-2cb7f4276dce",
    "Substitution, consequential, long-term": "dd7f13f5-0658-489c-a19c-f2ff8a00bdd9",
    "Undefined": "8b738ea0-f89e-4627-8679-433616064e82",
    "Allocation by carbon": "3e629972-8eb8-4fc9-a303-addbde01cf74",
    "Substitution, constrained by-products": "91800971-8f93-41e6-a3fd-f7a65283aa20",
    "Allocation by revenue": "709a9344-2acf-4fc9-9cd3-ef9b4d41ec46"
    }

system_model_2_ = {
    "Allocation - market value": 'Allocation by revenue',
    "Allocation - gross calorific value": "Undefined",
    "Allocation - net calorific value": "Undefined",
    "Allocation - exergetic content": "Undefined",
    "Allocation - element content": "Undefined",
    "Allocation - mass": "Allocation by dry mass",
    "Allocation - volume": "Undefined",
    "Allocation - ability to bear": "Allocation by revenue",
    "Allocation - marginal causality": "Undefined",
    "Allocation - physical causality": "Undefined",
    "Allocation - 100% to main function": 'Allocation, cut-off by classification',
    "Allocation - other explicit assignment": "Allocation, manually linked",
    "Allocation - equal distribution": "Allocation, manually linked",
    "Substitution - BAT": "Undefined",
    "Substitution - average, market price correction": 'Allocation at the point of substitution',
    "Substitution - average, technical properties correction": 'Substitution, constrained by-products',
    "Allocation - recycled content": "Undefined",
    "Substitution - recycling potential": "Undefined",
    "Substitution - average, no correction": 'Substitution, constrained by-products',
    "Substitution - specific": 'Substitution, constrained by-products',
    "Consequential effects - other": 'Substitution, consequential, long-term',
    "Not applicable": 'Undefined',
    "Other": 'Undefined'
    }

status_publication = {'0':"Data set finalised; unpublished",
                      '1':"Data set finalised; subsystems published",
                      '2':"Data set finalised; entirely published"}

status_publication_ = {
    "Working draft": '0',
    "Final draft for internal review": '0',
    "Final draft for external review": '0',
    "Data set finalised; unpublished": '0',
    "Under revision": '0',
    "Withdrawn": '0',
    "Data set finalised; subsystems published": '1',
    "Data set finalised; entirely published": '2'
    }

restrictions = {'0':'Free of charge for all users and uses',
                '1':'License fee',
                '2':'Other',
                '3':'Other'}

restrictions_ = { # An additional step is carried in the main code to verify for the case '3': 'Restricted' with company code
    "Free of charge for all users and uses": "0",
    "Free of charge for some user types or use types": "1",
    "Free of charge for members only": "1",
    "License fee": "1",
    "Other": "1" # Other is difficult to convert to one specific case
    }

access = {'0': 'Public',
          '1': 'Licensees',
          '2': 'Results only',
          '3': 'Restricted to '}

access_ = {v: k for k, v in access.items()}

compartment_conversion = { # keep in mind this is reference to the GLAD table and have to be updated upon new tables
    'emission/air/indoor':'Emissions/Emissions to air/Emissions to air, indoor',
    'emission/air/lower stratosphere and upper troposphere':'Emissions/Emissions to air/Emissions to lower stratosphere and upper troposphere',
    'emission/air/non urban or from high stack':'Emissions/Emissions to air/Emissions to non-urban air or from high stacks',
    'emission/air/unspecified':'Emissions/Emissions to air/Emissions to air, unspecified',
    'emission/air/unspecified long term':'Emissions/Emissions to air/Emissions to air, unspecified (long-term)',
    'emission/air/urban/close to ground':'Emissions/Emissions to air/Emissions to urban air close to ground',
    'emission/soil/agricultural':'Emissions/Emissions to soil/Emissions to agricultural soil',
    'emission/soil/non agricultural':'Emissions/Emissions to soil/Emissions to non-agricultural soil',
    'emission/soil/unspecified':'Emissions/Emissions to soil/Emissions to soil, unspecified',
    'emission/water/fresh water':'Emissions/Emissions to water/Emissions to fresh water',
    'emission/water/sea water':'Emissions/Emissions to water/Emissions to sea water',
    'emission/water/unspecified':'Emissions/Emissions to water/Emissions to water, unspecified',
    'emission/water/unspecified long term':'Emissions/Emissions to water/Emissions to water, unspecified (long-term)',
    'land use/occupation':'Land use/Land occupation',
    'land use/transformation':'Land use/Land transformation',
    'resource/air/renewable/element':'Resources/Resources from air/Renewable element resources from air',
    'resource/air/renewable/energy':'Resources/Resources from air/Renewable energy resources from air',
    'resource/air/renewable/material':'Resources/Resources from air/Renewable material resources from air',
    'resource/biosphere/renewable/energy':'Resources/Resources from biosphere/Renewable energy resources from biosphere',
    'resource/biosphere/renewable/material':'Resources/Resources from biosphere/Renewable material resources from biosphere',
    'resource/ground/non renewable/element':'Resources/Resources from ground/Non-renewable element resources from ground',
    'resource/ground/non renewable/energy':'Resources/Resources from ground/Non-renewable energy resources from ground',
    'resource/ground/non renewable/material':'Resources/Resources from ground/Non-renewable material resources from ground',
    'resource/ground/renewable/element':'Resources/Resources from ground/Renewable element resources from ground',
    'resource/water/non renewable/element':'Resources/Resources from water/Non-renewable element resources from water',
    'resource/water/non renewable/material':'Resources/Resources from water/Non-renewable material resources from water',
    'resource/water/renewable/energy':'Resources/Resources from water/Renewable energy resources from water',
    'resource/water/renewable/material':'Resources/Resources from water/Renewable material resources from water'
    }

pedigree = {
    "Reliability":[0,0.0006,0.002,0.008,0.04],
    "Completeness":[0,0.0001,0.0006,0.002,0.008],
    "Temporal correlation":[0,0.0002,0.002,0.008,0.04],
    "Geographical correlation":[0,2.50E-05,0.0001,0.0006,0.002],
    "Further technological correlation":[0,0.0006,0.008,0.04,0.12]
    }

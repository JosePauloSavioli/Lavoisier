#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 29 15:37:16 2023

@author: jotape42p
"""

### ECS2 


### ILCD1

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

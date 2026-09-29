#!/usr/bin/env python3
# -*- coding: utf-8 -*-

CANONICAL_KEY = b'\\__Lav_EC2CAN__/'

PROCESS_TYPE = {
    1: 'Unit process',
    2: 'LCI result',
}

SPECIAL_ACTIVITY = {
    0: 'ordinary transforming activity (default)',
    1: 'market activity',
    2: 'IO activity',
    3: 'Residual activity',
    4: 'production mix',
    5: 'import activity',
    6: 'supply mix',
    7: 'export activity',
    8: 're-export activity',
    9: 'correction activity',
    10: 'market group',
}

INHERITANCE = {
    0: 'not a child',
    1: 'geography child',
    2: 'temporal child',
    3: 'macro-economic scenario child',
}

TECHNOLOGY = {
    0: 'Undefined',
    1: 'New',
    2: 'Modern',
    3: 'Current',
    4: 'Old',
    5: 'Outdated',
}

ENERGY = {
    0: 'undefined',
    1: 'net calorific value',
    2: 'gross calorific value',
}

INPUT_GROUP = {
    1: 'Materials/Fuels',
    2: 'Electricity/Heat',
    3: 'Services',
    4: 'From Environment',
    5: 'From Technosphere (unspecified)',
}

OUTPUT_GROUP = {
    0: 'Reference Product',
    2: 'By-product',
    3: 'Material for Treatment',
    4: 'To Environment',
    5: 'Stock Additions',
}


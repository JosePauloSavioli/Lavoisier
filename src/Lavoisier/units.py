#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 17:26:27 2021

This dictionaries were based on the xml files from the C library UDUNITS,
which was produced by the Unidata Program Center of the
University Corporation for Atmospheric Research (UCAR)
more information in <http://www.unidata.ucar.edu>
and github <https://github.com/Unidata/UDUNITS-2>

@author: jotape42p
"""

import math

rank_ent = lambda x: x*1.8
rank_out = lambda x: x/1.8
fahr_ent = lambda x: (x-32)*5/9+273.15
fahr_out = lambda x: (x-273.15)*9/5+32
cels_ent = lambda x: x+273.15
cels_out = lambda x: x-273.15

bspl_ent = lambda x: 0.1*20*math.log10(x/20e-6)
bspl_out = lambda x: 10**(x/(0.1*20))*20-6

bwat_ent = lambda x: 10*10*math.log10(x)
bwat_out = lambda x: 10**(x/(10*10))

bmwat_ent = lambda x: 10*10*math.log10(x/1000)
bmwat_out = lambda x: 1000*10**(x/(10*10))

bvol_ent = lambda x: 10*10*math.log10(0.775*x)
bvol_out = lambda x: 1/0.775*10**(x/(10*10))

buvol_ent = lambda x: 10*10*math.log10(1e-6*x)
buvol_out = lambda x: 1/1e-6*10**(x/(10*10))

rhe_ent = lambda x: 10/x
rhe_out = lambda x: 10/x

kay_ent = lambda x: 100/x
kay_out = lambda x: 100/x

pi = math.pi
avg = 6.02214179e23

unit_pref = {
            'yotta':1e24,
            'zetta':1e21,
            'exa':1e18,
            'peta':1e15,
            'tera':1e12,
            'giga':1e9,
            'mega':1e6,
            'kilo':1e3,
            'hecto':100,
            'deka':10,
            'deci':.1,
            'centi':.01,
            'milli':1e-3,
            'micro':1e-6,
            'nano':1e-9,
            'pico':1e-12,
            'femto':1e-15,
            'atto':1e-18,
            'zepto':1e-21,
            'yocto':1e-24,
            'Y':1e24,
            'Z':1e21,
            'E':1e18,
            'P':1e15,
            'T':1e12,
            'G':1e9,
            'M':1e6,
            'k':1e3,
            'h':100,
            'da':10,
            'd':.1,
            'c':.01,
            'm':1e-3,
            'µ':1e-6,
            'μ':1e-6,
            'u':1e-6,
            'n':1e-9,
            'p':1e-12,
            'f':1e-15,
            'a':1e-18,
            'z':1e-21,
            'y':1e-24
            }

unit_s = {
        'm': ('distance', 1),
        'au': ('distance', 1.49597870700e11),
        'ua': ('distance', 1.495979e11),
        'Å': ('distance', 1e-10),
        'Å': ('distance', 1e-10),
        'meter': ('distance', 1),
        'metre': ('distance', 1),
        'astronomical_unit': ('distance', 1.49597870700e11),
        'astronomical_unit_BIPM_2006': ('distance', 1.495979e11),
        'nautical_mile': ('distance', 1852),
        'angstrom': ('distance', 1e-10),
        'ångström': ('distance', 1e-10),
        'fermi': ('distance', 1e-15),
        'light_year': ('distance', 9.46073e15),
        'micron': ('distance', 1e-6),
        'mil': ('distance', 2.54e-5),
        'parsec': ('distance', 3.085678e16),
        'printers_point': ('distance', 3.514598e-4),
        'chain': ('distance', 2.011684e1),
        'printers_pica': ('distance', 12*3.514598e-4),
        'pica': ('distance', 12*3.514598e-4),
        'nmile': ('distance', 1852),
        'US_survey_foot': ('distance', 1200/3937),
        'US_survey_feet': ('distance', 1200/3937),
        'US_survey_yard': ('distance', 3*(1200/3937)),
        'US_survey_mile': ('distance', 5280*1200/3937),
        'US_statute_mile': ('distance', 5280*1200/3937),
        'rod': ('distance', 16.5*1200/3937),
        'pole': ('distance', 16.5*1200/3937),
        'perch': ('distance', 16.5*1200/3937),
        'furlong': ('distance', 660*1200/3937),
        'fathom': ('distance', 6*1200/3937),
        'international_inch': ('distance', 2.54/100),
        'inch': ('distance', 2.54/100),
        'in': ('distance', 2.54/100),
        'international_foot': ('distance', 12*2.54/100),
        'international_feet': ('distance', 12*2.54/100),
        'foot': ('distance', 12*2.54/100),
        'feet': ('distance', 12*2.54/100),
        'ft': ('distance', 12*2.54/100),
        'international_yard': ('distance', 3*12*2.54/100),
        'yard': ('distance', 3*12*2.54/100),
        'yd': ('distance', 3*12*2.54/100),
        'international_mile': ('distance', 5280*12*2.54/100),
        'mile': ('distance', 5280*12*2.54/100),
        'mi': ('distance', 5280*12*2.54/100),
        'big_point': ('distance', (2.54/100)/72),
        'barleycorn': ('distance', (2.54/100)/3),
        'arpentlin': ('distance', 191.835*12*2.54/100),
        'kilogram': ('weight', 1),
        'kg': ('weight', 1),
        'metric_ton': ('weight', 1000),
        'tonne': ('weight', 1000),
        't': ('weight', 1000),
        'unified_atomic_mass_unit': ('weight', 1.6605402e-27),
        'u': ('weight', 1.6605402e-27),
        'atomic_mass_unit': ('weight', 1.6605402e-27),
        'atomicmassunit': ('weight', 1.6605402e-27),
        'amu': ('weight', 1.6605402e-27),
        'assay_ton': ('weight', 2.916667e-2),
        'avoirdupois_ounce': ('weight', 2.834952e-2),
        'avoirdupois_pound': ('weight', 4.5359237e-1),
        'pound': ('weight', 4.5359237e-1),
        'lb': ('weight', 4.5359237e-1),
        'carat': ('weight', 2e-4),
        'grain': ('weight', 6.479891e-5),
        'gr': ('weight', 6.479891e-5),
        'long_hundredweight': ('weight', 5.080235e1),
        'pennyweight': ('weight', 1.555174e-3),
        'short_hundredweight': ('weight', 4.535924e1),
        'slug': ('weight', 14.59390),
        'troy_ounce': ('weight', 3.110348e-2),
        'apothecary_ounce': ('weight', 3.110348e-2),
        'troy_pound': ('weight', 3.732417e-1),
        'apothecary_pound': ('weight', 3.732417e-1),
        'scruple': ('weight', 20*6.479891e-5),
        'apdram': ('weight', 60*6.479891e-5),
        'dram': ('weight', 2.834952e-2/16),
        'dr': ('weight', 2.834952e-2/16),
        'apounce': ('weight', 480*6.479891e-5),
        'appound': ('weight', 5760*6.479891e-5),
        'bag': ('weight', 94*4.5359237e-1),
        'short_ton': ('weight', 2000*4.5359237e-1),
        'ton': ('weight', 2000*4.5359237e-1),
        'long_ton': ('weight', 2240*4.5359237e-1),
        'gram': ('weight', 1e-3),
        'g': ('weight', 1e-3),
        'second': ('time', 1),
        's': ('time', 1),
        'sec': ('time', 1),
        'minute': ('time', 60),
        'min': ('time', 60),
        'hour': ('time', 60*60),
        'h': ('time', 60*60),
        'hr': ('time', 60*60),
        'day': ('time', 24*60*60),
        'd': ('time', 24*60*60),
        'shake': ('time', 1e-8),
        'sidereal_day': ('time', 8.616409e4),
        'sidereal_hour': ('time', 3.590170e3),
        'sidereal_minute': ('time', 5.983617e1),
        'sidereal_second': ('time', 0.9972696),
        'sidereal_year': ('time', 3.155815e7),
        'tropical_year': ('time', 3.15569259747e7),
        'year': ('time', 3.15569259747e7),
        'yr': ('time', 3.15569259747e7),
        'lunar_month': ('time', 24*60*60*29.530589),
        'common_year': ('time', 365*24*60*60),
        'leap_year': ('time', 366*24*60*60),
        'Julian_year': ('time', 365.25*24*60*60),
        'Gregorian_year': ('time', 365.2425*24*60*60),
        'sidereal_month': ('time', 27.321661*24*60*60),
        'tropical_month': ('time', 27.321582*24*60*60),
        'fortnight': ('time', 14*24*60*60),
        'week': ('time', 7*24*60*60),
        'jiffy': ('time', 0.01),
        'eon': ('time', 1e-9*3.15569259747e7),
        'month': ('time', 3.15569259747e7/12),
        'work_year': ('time', 2056*60*60),
        'work_month': ('time', 2056*60*60/12),
        'ampere': ('current', 1),
        'A': ('current', 1),
        'amp': ('current', 1),
        'abampere': ('current', 10),
        'gilbert': ('current', 7.957747e-1),
        'statampere': ('current', 3.335640e-10),
        'biot': ('current', 10),
        'kelvin': ('temperature', 1),
        'K': ('temperature', 1),
        'degree_kelvin': ('temperature', 1),
        'degrees_kelvin': ('temperature', 1),
        'degree_K': ('temperature', 1),
        'degrees_K': ('temperature', 1),
        'degreeK': ('temperature', 1),
        'degreesK': ('temperature', 1),
        'deg_K': ('temperature', 1),
        'degs_K': ('temperature', 1),
        'degK': ('temperature', 1),
        'degsK': ('temperature', 1),
        'degree_Celsius': ('temperature', 1, cels_ent, cels_out),
        'degrees_Celsius': ('temperature', 1, cels_ent, cels_out),
        '℃': ('temperature', 1, cels_ent, cels_out),
        '°C': ('temperature', 1, cels_ent, cels_out),
        'ºC': ('temperature', 1, cels_ent, cels_out),
        'celsius': ('temperature', 1, cels_ent, cels_out),
        'degree_C': ('temperature', 1, cels_ent, cels_out),
        'degrees_C': ('temperature', 1, cels_ent, cels_out),
        'degreeC': ('temperature', 1, cels_ent, cels_out),
        'degreesC': ('temperature', 1, cels_ent, cels_out),
        'deg_C': ('temperature', 1, cels_ent, cels_out),
        'degs_C': ('temperature', 1, cels_ent, cels_out),
        'degC': ('temperature', 1, cels_ent, cels_out),
        'degsC': ('temperature', 1, cels_ent, cels_out),
        '°R': ('temperature', 1, rank_ent, rank_out),
        'ºR': ('temperature', 1, rank_ent, rank_out),
        'degree_rankine': ('temperature', 1, rank_ent, rank_out),
        'degrees_rankine': ('temperature', 1, rank_ent, rank_out),
        'degree_R': ('temperature', 1, rank_ent, rank_out),
        'degrees_R': ('temperature', 1, rank_ent, rank_out),
        'degreeR': ('temperature', 1, rank_ent, rank_out),
        'degreesR': ('temperature', 1, rank_ent, rank_out),
        'deg_R': ('temperature', 1, rank_ent, rank_out),
        'degs_R': ('temperature', 1, rank_ent, rank_out),
        'degR': ('temperature', 1, rank_ent, rank_out),
        'degsR': ('temperature', 1, rank_ent, rank_out),
        '℉': ('temperature', 1, fahr_ent, fahr_out),
        '°F': ('temperature', 1, fahr_ent, fahr_out),
        'ºF': ('temperature', 1, fahr_ent, fahr_out),
        'degree_fahrenheit': ('temperature', 1, fahr_ent, fahr_out),
        'degrees_fahrenheit': ('temperature', 1, fahr_ent, fahr_out),
        'degree_F': ('temperature', 1, fahr_ent, fahr_out),
        'degrees_F': ('temperature', 1, fahr_ent, fahr_out),
        'degreeF': ('temperature', 1, fahr_ent, fahr_out),
        'degreesF': ('temperature', 1, fahr_ent, fahr_out),
        'deg_F': ('temperature', 1, fahr_ent, fahr_out),
        'degs_F': ('temperature', 1, fahr_ent, fahr_out),
        'degF': ('temperature', 1, fahr_ent, fahr_out),
        'degsF': ('temperature', 1, fahr_ent, fahr_out),
        'mole': ('amount of substance', 1),
        'mol': ('amount of substance', 1),
        'einstein':  ('amount of substance', 1),
        'molecule': ('amount of substance', 1/avg),
        'molec': ('amount of substance', 1/avg),
        'nucleon': ('amount of substance', 1/avg),
        'nuc': ('amount of substance', 1/avg),
        'candela': ('luminous intensity', 1),
        'cd': ('luminous intensity', 1),
        'candle': ('luminous intensity', 1),
        'radian': ('angle', 1),
        'rad': ('angle', 1),
        'arc_degree': ('angle', pi/180),
        'angular_degree': ('angle', pi/180),
        'degree': ('angle', pi/180),
        'arcdeg': ('angle', pi/180),
        '°': ('angle', pi/180),
        'º': ('angle', pi/180),
        'arc_minute': ('angle', (pi/180)/60),
        "'": ('angle', (pi/180)/60),
        "′": ('angle', (pi/180)/60),
        'angular_minute': ('angle', (pi/180)/60),
        'arcminute': ('angle', (pi/180)/60),
        'arcmin': ('angle', (pi/180)/60),
        'arc_second': ('angle', ((pi/180)/60)/60),
        '"': ('angle', ((pi/180)/60)/60),
        '″': ('angle', ((pi/180)/60)/60),
        'angular_second': ('angle', ((pi/180)/60)/60),
        'arcsecond': ('angle', ((pi/180)/60)/60),
        'arcsec': ('angle', ((pi/180)/60)/60),
        'grade': ('angle', 0.9),
        'circle': ('angle', 2*pi),
        'cycle': ('angle', 2*pi),
        'turn': ('angle', 2*pi),
        'revolution': ('angle', 2*pi),
        'rotation': ('angle', 2*pi),
        'degree_north': ('angle', pi/180),
        'degrees_north': ('angle', pi/180),
        'degree_N': ('angle', pi/180),
        'degrees_N': ('angle', pi/180),
        'degreeN': ('angle', pi/180),
        'degreesN': ('angle', pi/180),
        'degree_east': ('angle', pi/180),
        'degrees_east': ('angle', pi/180),
        'degree_E': ('angle', pi/180),
        'degrees_E': ('angle', pi/180),
        'degreeE': ('angle', pi/180),
        'degreesE': ('angle', pi/180),
        'degree_true': ('angle', pi/180),
        'degrees_true': ('angle', pi/180),
        'degree_T': ('angle', pi/180),
        'degrees_T': ('angle', pi/180),
        'degreeT': ('angle', pi/180),
        'degreesT': ('angle', pi/180),
        'degree_west': ('angle', -pi/180),
        'degrees_west': ('angle', -pi/180),
        'degree_W': ('angle', -pi/180),
        'degrees_W': ('angle', -pi/180),
        'degreeW': ('angle', -pi/180),
        'degreesW': ('angle', -pi/180),
        'steradian': ('sphere angle', 1),
        'sr': ('sphere angle', 1),
        'hertz': ('frequency', 1),
        'Hz': ('frequency', 1),
        'becquerel': ('frequency', 1),
        'Bq': ('frequency', 1),
        'baud': ('frequency', 1),
        'Bd': ('frequency', 1),
        'bps': ('frequency', 1),
        'newton': ('force', 1),
        'N': ('force', 1),
        'force': ('force', 9.806650),
        'dyne': ('force', 1e-5),
        'pond': ('force', 9.806650e-3),
        'force_kilogram': ('force', 9.806650),
        'kilogram_force': ('force', 9.806650),
        'kilograms_force': ('force', 9.806650),
        'kgf': ('force', 9.806650),
        'force_ounce': ('force', 2.780139e-1),
        'ounce_force': ('force', 2.780139e-1),
        'ounces_force': ('force', 2.780139e-1),
        'ozf': ('force', 2.780139e-1),
        'force_pound': ('force', 4.4482216152605),
        'pound_force': ('force', 4.4482216152605),
        'pounds_force': ('force', 4.4482216152605),
        'lbf': ('force', 4.4482216152605),
        'poundal': ('force', 1.382550e-1),
        'gram_force': ('force', 0.00980665),
        'grams_force': ('force', 0.00980665),
        'force_gram': ('force', 0.00980665),
        'gf': ('force', 0.00980665),
        'force_ton': ('force', 2000*4.4482216152605),
        'ton_force': ('force', 2000*4.4482216152605),
        'tons_force': ('force', 2000*4.4482216152605),
        'kip': ('force', 1000*4.4482216152605),
        'pascal': ('pressure', 1),
        'Pa': ('pressure', 1),
        'bar': ('pressure', 100000),
        'standard_atmosphere': ('pressure', 1.01325e5),
        'atmosphere': ('pressure', 1.01325e5),
        'atm': ('pressure', 1.01325e5),
        'technical_atmosphere': ('pressure', 98066.5),
        'at': ('pressure', 98066.5),
        'cm_H20': ('pressure', 98.0665),
        'cmH20': ('pressure', 98.0665),
        'inch_H2O_39F': ('pressure', 249.08890833333),
        'inches_H2O_39F': ('pressure', 249.08890833333),
        'inch_H2O_60F': ('pressure', 248.84),
        'inches_H2O_60F': ('pressure', 248.84),
        'foot_water': ('pressure', 2988.984),
        'feet_water': ('pressure', 2988.984),
        'foot_H2O': ('pressure', 2988.984),
        'feet_H2O': ('pressure', 2988.984),
        'footH2O': ('pressure', 2988.984),
        'feetH2O': ('pressure', 2988.984),
        'ftH2O': ('pressure', 2988.984),
        'fth2o': ('pressure', 2988.984),
        'cm_Hg': ('pressure', 1333.2234),
        'cmHg': ('pressure', 1333.2234),
        'millimeter_Hg_0C': ('pressure', 133.32234),
        'millimeters_Hg_0C': ('pressure', 133.32234),
        'millimeter_Hg': ('pressure', 133.32234),
        'millimeters_Hg': ('pressure', 133.32234),
        'mm_Hg': ('pressure', 133.32234),
        'mm_hg': ('pressure', 133.32234),
        'mmHg': ('pressure', 133.32234),
        'mmhg': ('pressure', 133.32234),
        'Torr': ('pressure', 133.32234),
        'inch_Hg_32F': ('pressure', 3386.3882),
        'inches_Hg_32F': ('pressure', 3386.3882),
        'inch_Hg_60F': ('pressure', 3376.8522),
        'inches_Hg_60F': ('pressure', 3376.8522),
        'inch_Hg': ('pressure', 3386.3882),
        'inches_Hg': ('pressure', 3386.3882),
        'in_Hg': ('pressure', 3386.3882),
        'inHg': ('pressure', 3386.3882),
        'psi': ('pressure', 6894.7572931783),
        'ksi': ('pressure', 6894757.2931783),
        'barie': ('pressure', 0.1),
        'barye': ('pressure', 0.1),
        'B_SPL': ('pressure', 1, bspl_ent, bspl_out),
        'joule': ('energy or work', 1),
        'J': ('energy or work', 1),
        'electronvolt': ('energy or work', 1.60217733e-19),
        'eV': ('energy or work', 1.60217733e-19),
        'electron_volt': ('energy or work', 1.60217733e-19),
        'erg': ('energy or work', 1e-7),
        'IT_Btu': ('energy or work', 1.05505585262e3),
        'IT_Btus': ('energy or work', 1.05505585262e3),
        'Btu': ('energy or work', 1.05505585262e3),
        'Btus': ('energy or work', 1.05505585262e3),
        'EC_therm': ('energy or work', 1.05506e8),
        'thermochemical_calorie': ('energy or work', 4.184000),
        'IT_calorie': ('energy or work', 4.1868),
        'calorie': ('energy or work', 4.1868),
        'cal': ('energy or work', 4.1868),
        'ton_TNT': ('energy or work', 4.184e9),
        'tons_TNT': ('energy or work', 4.184e9),
        'US_therm': ('energy or work', 1.054804e8),
        'therm': ('energy or work', 1.054804e8),
        'thm': ('energy or work', 1.054804e8),
        'bev': ('energy or work', 1e9*1.60217733e-19),
        'watthour': ('energy or work', 3600),
        'Wh': ('energy or work', 3600),
        'wh': ('energy or work', 3600),
        'm²': ('area', 1),
        'm^2': ('area', 1),
        'square_meter': ('area', 1),
        'square_meters': ('area', 1),
        'm2': ('area', 1),
        'circular_mil': ('area', 5.067075e-10),
        'darcy': ('area', 9.869233e-13),
        'acre': ('area', 4046.856422),
        'are': ('area', 100),
        'a': ('area', 100),
        'hectare': ('area', 10000),
        'barn': ('area', 10e-28),
        'b': ('area', 10e-28),
        'm³': ('volume', 1),
        'm^3': ('volume', 1),
        'cubic_meter': ('volume', 1),
        'cubic_meters': ('volume', 1),
        'm3': ('volume', 1),
        'acre_foot': ('volume', 1.233489e3),
        'acre_feet': ('volume', 1.233489e3),
        'board_foot': ('volume', 2.359737e-3),
        'board_feet': ('volume', 2.359737e-3),
        'bushel': ('volume', 3.523907e-2),
        'bu': ('volume', 3.523907e-2),
        'peck': ('volume', 3.523907e-2/4),
        'pk': ('volume', 3.523907e-2/4),
        'Canadian_liquid_gallon': ('volume', 4.546090e-3),
        'US_dry_gallon': ('volume', 4.404884e-3),
        'cc': ('volume', 1e-6),
        'stere': ('volume', 1),
        'register_ton': ('volume', 2.831685),
        'US_dry_quart': ('volume', 4.404884e-3/4),
        'dry_quart': ('volume', 4.404884e-3/4),
        'US_dry_pint': ('volume', 4.404884e-3/8),
        'dry_pint': ('volume', 4.404884e-3/8),
        'US_liquid_gallon': ('volume', 3.785412e-3),
        'liquid_gallon': ('volume', 3.785412e-3),
        'gallon': ('volume', 3.785412e-3),
        'barrel': ('volume', 42*3.785412e-3),
        'bbl': ('volume', 42*3.785412e-3),
        'firkin': ('volume', 42*3.785412e-3/4),
        'US_liquid_quart': ('volume', 3.785412e-3/4),
        'liquid_quart': ('volume', 3.785412e-3/4),
        'quart': ('volume', 3.785412e-3/4),
        'US_liquid_pint': ('volume', 3.785412e-3/8),
        'liquid_pint': ('volume', 3.785412e-3/8),
        'pint': ('volume', 3.785412e-3/8),
        'pt': ('volume', 3.785412e-3/8),
        'US_liquid_cup': ('volume', 3.785412e-3/16),
        'liquid_cup': ('volume', 3.785412e-3/16),
        'cup': ('volume', 3.785412e-3/16),
        'US_liquid_gill': ('volume', 3.785412e-3/32),
        'liquid_gill': ('volume', 3.785412e-3/32),
        'gill': ('volume', 3.785412e-3/32),
        'US_fluid_ounce': ('volume', 3.785412e-3/128),
        'fluid_ounce': ('volume', 3.785412e-3/128),
        'US_liquid_ounce': ('volume', 3.785412e-3/128),
        'liquid_ounce': ('volume', 3.785412e-3/128),
        'oz': ('volume', 3.785412e-3/128),
        'floz': ('volume', 3.785412e-3/128),
        'tablespoon': ('volume', (3.785412e-3/128)/2),
        'Tbl': ('volume', (3.785412e-3/128)/2),
        'Tbsp': ('volume', (3.785412e-3/128)/2),
        'tbsp': ('volume', (3.785412e-3/128)/2),
        'Tblsp': ('volume', (3.785412e-3/128)/2),
        'tblsp': ('volume', (3.785412e-3/128)/2),
        'fluid_dram': ('volume', (3.785412e-3/128)/8),
        'fldr': ('volume', (3.785412e-3/128)/8),
        'teaspoon': ('volume', (3.785412e-3/128)/6),
        'tsp': ('volume', (3.785412e-3/128)/6),
        'UK_liquid_gallon': ('volume', 4.546090e-3),
        'UK_liquid_quart': ('volume', 4.546090e-3/4),
        'UK_liquid_pint': ('volume', 4.546090e-3/8),
        'UK_liquid_cup': ('volume', 4.546090e-3/16),
        'UK_liquid_gill': ('volume', 4.546090e-3/32),
        'UK_fluid_ounce': ('volume', 4.546090e-3/160),
        'UK_liquid_ounce': ('volume', 4.546090e-3/160),
        'liter': ('volume', 0.001),
        'litre': ('volume', 0.001),
        'l': ('volume', 0.001),
        'BZ': ('radar', 1),
        'Bz': ('radar', 1),
        'unit': ('constant', 1),
        'count': ('constant', 1),
        'bit': ('constant', 1),
        'octet': ('constant', 8),
        'byte': ('constant', 8),
        'percent': ('constant', 0.01),
        '%': ('constant', 0.01),
        'ppv': ('constant', 1),
        'ppm': ('constant', 1e-6),
        'ppmv': ('constant', 1e-6),
        'ppb': ('constant', 1e-9),
        'ppbv': ('constant', 1e-9),
        'ppt': ('constant', 1e-12),
        'pptv': ('constant', 1e-12),
        'ppq': ('constant', 1e-15),
        'ppqv': ('constant', 1e-15),
        'B': ('constant', bwat_ent, bwat_out),
        'watt': ('power', 1),
        'W': ('power', 1),
        'V.A': ('power', 1),
        'VA': ('power', 1),
        'volt_ampere': ('power', 1),
        'boiler_horsepower': ('power', 9.80950e3),
        'shaft_horsepower': ('power', 7.456999e2),
        'horsepower': ('power', 7.456999e2),
        'hp': ('power', 7.456999e2),
        'metric_horsepower': ('power', 7.35499e2),
        'electric_horsepower': ('power', 7.460000e2),
        'water_horsepower': ('power', 7.46043e2),
        'UK_horsepower': ('power', 7.4570e2),
        'refrigeration_ton': ('power', 3516.85284),
        'ton_of_refrigeration': ('power', 3516.85284),
        'tons_of_refrigeration': ('power', 3516.85284),
        'BW': ('power', bwat_ent, bwat_out),
        'Bm': ('power', bmwat_ent, bmwat_out),
        'C': ('electric charge', 1),
        'coulomb': ('electric charge', 1),
        'e': ('electric charge', 1.602176487e-19),
        'chemical_faraday': ('electric charge', 9.64957e4),
        'physical_faraday': ('electric charge', 9.65219e4),
        'C12_faraday': ('electric charge', 9.648531e4),
        'faraday': ('electric charge', 9.648531e4),
        'statcoulomb': ('electric charge', 3.335640e-10),
        'volt': ('electric potential difference', 1),
        'V': ('electric potential difference', 1),
        'abvolt': ('electric potential difference', 1e-8),
        'statvolt': ('electric potential difference', 2.997925e2),
        'BV': ('electric potential difference', bwat_ent, bwat_out),
        'Bv': ('electric potential difference', bvol_ent, bvol_out),
        'BµV': ('electric potential difference', buvol_ent, buvol_out),
        'farad': ('capacitance', 1),
        'F': ('capacitance', 1),
        'abfarad': ('capacitance', 1e9),
        'statfarad': ('capacitance', 1.112650e-12),
        'meters_per_second': ('velocity', 1),
        'meter_per_second': ('velocity', 1),
        'm/s': ('velocity', 1),
        'meter/s': ('velocity', 1),
        'meters/s': ('velocity', 1),
        'meter/sec': ('velocity', 1),
        'meters/sec': ('velocity', 1),
        'international_knot': ('velocity', 0.514444),
        'knot_international': ('velocity', 0.514444),
        'knot': ('velocity', 0.514444),
        'kt': ('velocity', 0.514444),
        'kts': ('velocity', 0.514444),
        'mile_per_second': ('velocity', 1609.34),
        'mi/s': ('velocity', 1609.34),
        'mps': ('velocity', 1609.34),
        'mph': ('velocity', 0.44704),
        'mile_per_hour': ('velocity', 0.44704),
        'miles_per_second': ('velocity', 1609.34),
        'miles_per_hour': ('velocity', 0.44704),
        'inch_per_second': ('velocity', 0.0254),
        'inches_per_second': ('velocity', 0.0254),
        'in/s': ('velocity', 0.0254),
        'foot_per_second': ('velocity', 0.3048),
        'feet_per_second': ('velocity', 0.3048),
        'ft/s': ('velocity', 0.3048),
        'kilometers_per_hour': ('velocity', 0,277778),
        'kilometer_per_hour': ('velocity', 0,277778),
        'km/h': ('velocity', 0,277778),
        'kilometers_per_day': ('velocity', 0.0115741),
        'kilometer_per_day': ('velocity', 0.0115741),
        'km/day': ('velocity', 0.0115741),
        'km/s': ('velocity', 0.001),
        'kilometers_per_second': ('velocity', 0.001),
        'kilometer_per_second': ('velocity', 0.001),
        'yard_per_second': ('velocity', 0.9144),
        'yards_per_second': ('velocity', 0.9144),
        'yd/s': ('velocity', 0.9144),
        'meters_per_square_second': ('velocity', 1),
        'meter_per_square_second': ('velocity', 1),
        'm/s^2': ('acceleration', 1),
        'm/s²': ('acceleration', 1),
        'm/s2': ('acceleration', 1),
        'meter/s^2': ('acceleration', 1),
        'meters/s^2': ('acceleration', 1),
        'meter/sec^2': ('acceleration', 1),
        'meters/sec^2': ('acceleration', 1),
        'km/s^2': ('acceleration', 0.001),
        'km/s²': ('acceleration', 0.001),
        'km/s2': ('acceleration', 0.001),
        'kilometers_per_square_second': ('acceleration', 0.001),
        'kilometer_per_square_second': ('acceleration', 0.001),
        'km/sec^2': ('acceleration', 0.001),
        'mile_per_square_second': ('acceleration', 1609.344),
        'miles_per_square_second': ('acceleration', 1609.344),
        'mi/s^2': ('acceleration', 1609.344),
        'mi/s2': ('acceleration', 1609.344),
        'mi/s²': ('acceleration', 1609.344),
        'yard_per_square_second': ('acceleration', 0.9144),
        'yard_per_square_second': ('acceleration', 0.9144),
        'yd/s^2': ('acceleration', 0.9144),
        'yd/s2': ('acceleration', 0.9144),
        'yd/s²': ('acceleration', 0.9144),
        'inch_per_square_second': ('acceleration', 0.0254),
        'inches_per_square_second': ('acceleration', 0.0254),
        'in/s^2': ('acceleration', 0.0254),
        'in/s2': ('acceleration', 0.0254),
        'in/s²': ('acceleration', 0.0254),
        'feet_per_square_second': ('acceleration', 0.3048),
        'foot_per_square_second': ('acceleration', 0.3048),
        'ft/s^2': ('acceleration', 0.3048),
        'ft/s2': ('acceleration', 0.3048),
        'ft/s²': ('acceleration', 0.3048),
        'standard_free_fall': ('acceleration', 9.806650),
        'gravity': ('acceleration', 9.806650),
        'geopotential': ('acceleration', 9.806650),
        'dynamic': ('acceleration', 9.806650),
        'gp': ('acceleration', 9.806650),
        'gal': ('acceleration', 0.01),
        'ohm': ('resistance', 1),
        'Ω': ('resistance', 1),
        'Ω': ('resistance', 1),
        'abohm': ('resistance', 1e-9),
        'statohm': ('resistance', 8.987554e11),
        'radian_per_second': ('angular velocity', 1),
        'radians_per_second': ('angular velocity', 1),
        'rad/s': ('angular velocity', 1),
        'rad/sec': ('angular velocity', 1),
        'rotation_per_second': ('angular velocity', 1/(2*pi)),
        'rotations_per_second': ('angular velocity', 1/(2*pi)),
        'rps': ('angular velocity', 1/(2*pi)),
        'cps': ('angular velocity', 1/(2*pi)),
        'rotation_per_minute': ('angular velocity', 0.10472),
        'rotations_per_minute': ('angular velocity', 0.10472),
        'rpm': ('angular velocity', 0.10472),
        'kg/m': ('lineic mass', 1),
        'kilogram_per_meter': ('lineic mass', 1),
        'kilograms_per_meter': ('lineic mass', 1),
        'denier': ('lineic mass', 1.111111e-7),
        'tex': ('lineic mass', 1e-6),
        'kg/(Pa.s.m^2)': ('mass per time', 1),
        'kg/Pasm2': ('mass per time', 1),
        'kg/Pasm²': ('mass per time', 1),
        'kg/Pasm^2': ('mass per time', 1),
        'kilogram_per_pascal_second_square_meter': ('mass per time', 1),
        'kilograms_per_pascal_second_square_meter': ('mass per time', 1),
        'perm_0C': ('mass per time', 5.72135e-11),
        'perms_0C': ('mass per time', 5.72135e-11),
        'perm_23C': ('mass per time', 5.74525e-11),
        'perms_23C': ('mass per time', 5.74525e-11),
        'm^3/s': ('volume per time', 1),
        'm³/s': ('volume per time', 1),
        'm3/s': ('volume per time', 1),
        'cubic_meters_per_second': ('volume per time', 1),
        'sverdrup': ('volume per time', 1e6),
        'Pa.s': ('viscosity', 1),
        'Pas': ('viscosity', 1),
        'Pascal_per_second': ('viscosity', 1),
        'Pascals_per_second': ('viscosity', 1),
        'pascal_per_second': ('viscosity', 1),
        'pascals_per_second': ('viscosity', 1),
        'poise': ('viscosity', 1e-1),
        'stokes': ('viscosity', 1e-4),
        'St': ('viscosity', 1e-4),
        'rhe': ('viscosity', 1, rhe_ent, rhe_out),
        'K.m^2/W': ('heat', 1),
        'K.m²/W': ('heat', 1),
        'K.m2/W': ('heat', 1),
        'Km^2/W': ('heat', 1),
        'Km²/W': ('heat', 1),
        'Km2/W': ('heat', 1),
        'Kelvin_square_meter_per_watt': ('heat', 1),
        'kelvin_square_meter_per_watt': ('heat', 1),
        'clo': ('heat', 1.55e-1),
        '1/m': ('inverse of distance', 1),
        'one_over_meter': ('inverse of distance', 1),
        '1_over_meter': ('inverse of distance', 1),
        'kayser': ('inverse of distance', 1, kay_ent, kay_out),
        'm^2 s^-1 K kg^-1': ('vorticity', 1),
        'm^2/s.K/kg': ('vorticity', 1),
        'm^2K/kgs': ('vorticity', 1),
        'm²/s.K/kg': ('vorticity', 1),
        'm²K/kgs': ('vorticity', 1),
        'm2/s.K/kg': ('vorticity', 1),
        'm2K/kgs': ('vorticity', 1),
        'm².K/kg.s': ('vorticity', 1),
        'm^2.K/kg.s': ('vorticity', 1),
        'm2.K/kg.s': ('vorticity', 1),
        'potential_vorticity_unit': ('vorticity', 1e-6),
        'PVU': ('vorticity', 1e-6),
        'siemens': ('electric conductance', 1),
        'S': ('electric conductance', 1),
        'abmho': ('electric conductance', 1e9),
        'statmho': ('electric conductance', 1.112650e-12),
        'weber': ('magnetic flux', 1),
        'Wb': ('magnetic flux', 1),
        'unit_pole': ('magnetic flux', 1.256637e-7),
        'maxwell': ('magnetic flux', 1e-8),
        'tesla': ('flux density', 1),
        'T': ('flux density', 1),
        'gamma': ('flux density', 1e-9),
        'gauss': ('flux density', 1e-4),
        'henry': ('inductance', 1),
        'H': ('inductance', 1),
        'abhenry': ('inductance', 1e-9),
        'stathenry': ('inductance', 8.987554e11),
        'lumen': ('luminous flux', 1),
        'lm': ('luminous flux', 1),
        'lux': ('illuminance', 1),
        'lx': ('illuminance', 1),
        'footcandle': ('illuminance', 1.076391e-1),
        'phot': ('illuminance', 1e4),
        'ph': ('illuminance', 1e4),
        'katal': ('catalytic activity', 1),
        'kat': ('catalytic activity', 1),
        'J/kg': ('energy per mass', 1),
        'Joules_per_kilogram': ('energy per mass', 1),
        'Joule_per_kilogram': ('energy per mass', 1),
        'joules_per_kilogram': ('energy per mass', 1),
        'joule_per_kilogram': ('energy per mass', 1),
        'gray': ('energy per mass', 1),
        'Gy': ('energy per mass', 1),
        'sievert': ('energy per mass', 1),
        'Sv': ('energy per mass', 1),
        'rem': ('energy per mass', 0.01),
        'TNT': ('energy per mass', 4184),
        'curie': ('frequency', 3.7e10),
        'Ci': ('frequency', 3.7e10),
        'roentgen': ('ionizing radiation', 2.58e-4),
        'R': ('ionizing radiation', 2.58e-4),
        'C/kg': ('ionizing radiation', 1),
        'coulomb_per_kilogram': ('ionizing radiation', 1),
        'coulombs_per_kilogram': ('ionizing radiation', 1),
        'A/m': ('magnetic field', 1),
        'ampere_per_meter': ('magnetic field', 1),
        'amperes_per_meter': ('magnetic field', 1),
        'oersted': ('magnetic field', 7.957747e1),
        'Oe': ('magnetic field', 7.957747e1),
        'cd/m^2': ('illumination', 1),
        'cd/m2': ('illumination', 1),
        'cd/m²': ('illumination', 1),
        'candela_per_square_meter': ('illumination', 1),
        'candelas_per_square_meter': ('illumination', 1),
        'footlambert': ('illumination', 3.426259),
        'lambert': ('illumination', 1e4/pi),
        'stilb': ('illumination', 1e4),
        'sb': ('illumination', 1e4),
        'nit': ('illumination', 1),
        'nt': ('illumination', 1),
        'blondel': ('illumination', 1/pi),
        'apostilb': ('illumination', 1/pi),
        'kg/s²': ('tensão superficial', 1),
        'kg/s^2': ('tensão superficial', 1),
        'kg/s2': ('tensão superficial', 1),
        'N/m': ('tensão superficial', 1),
        'J/m²': ('tensão superficial', 1),
        'J/m2': ('tensão superficial', 1),
        'J/m^2': ('tensão superficial', 1),
        'langley': ('tensão superficial', 4.184000e4),
        }
    
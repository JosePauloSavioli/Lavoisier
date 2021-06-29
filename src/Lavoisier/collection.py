#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 24 07:46:20 2021

Collection of functions for the conversion library

@author: jotape42p
"""

import os, csv, re
from lxml import etree as ET
from math import exp
from uuid import uuid4
from time import strptime
from functools import wraps

import Lavoisier.additional_files as additional_files
from Lavoisier.units import unit_s, unit_pref, unit_uid, unit_ecoinvent, special_property_list, factor_elem_flow


###############################################################################
#############################***DECORATORS***##################################
###############################################################################

def memory(func, count = [0]):
    '''Wrapper with memory of ids created for duplicates check
    
    This function should be revised in future builds tackling market datasets
    '''
    
    @wraps(func)
    def c(ort, tt, ee, *args):
        
        # Verifies if it is not an Elementary Flow call without doubled names possible
        if isinstance(ort, int):
            func(ort, tt, ee, *args)
            
        # Intermediate flow captured
        else:
            
            # Verifies if it is a new activity, clearing the memory
            if args[0] not in trigger:
                trigger.add(args[0])
                count[0] = 0
                memory.clear()
            
            # Verifies if the intermediateExchangeId is doubled, if it is, add a counter to the name
            v = tt.find('{http://www.EcoInvent.org/EcoSpold02}intermediateExchange').get('id')
            if v not in memory:
                memory.add(v)
                func(ort, tt, ee, *args)
            else:
                count[0] += 1
                func(ort, tt, ee, args[0],
                     tt.find('{http://www.EcoInvent.org/EcoSpold02}intermediateExchange').get('id'),
                     tt.find('//{http://www.EcoInvent.org/EcoSpold02}name').text + '_' + str(count[0]))
            
    memory = set()
    trigger = set()
    
    return c


###############################################################################

def memoryPar(func):
    '''Wrapper with memory of ids created for duplicates check on variableParameters
    
    This function should be revised in future builds tackling market datasets
    '''
    
    @wraps(func)
    def c(ilcd_tree, name, *args):
        
        if ilcd_tree not in trigger:
            trigger.add(ilcd_tree)
            memory.clear()
        if name not in memory:
            memory.add(name)
            result = func(ilcd_tree, name, *args)
            return result
        else:
            if len(args) == 5:
                return None, None
            else:
                return None
            
    memory = set()
    trigger = set()
    
    return c


###############################################################################
##########################***SIMPLE FUNCTIONS***###############################
###############################################################################

def zipdir(path, ziph):
    '''Makes a directory into zip file'''
    
    len_path = len(path)
    for root, _, files in os.walk(path):
        for file in files:
            filepath = os.path.join(root, file)
            ziph.write(filepath, filepath[len_path:])
            

###############################################################################

def get_namespace(ns_type):
    '''Get namespace declarations for the xml file'''
    
    if ns_type == 'ILCD_process':
        return {None: "http://lca.jrc.it/ILCD/Process",
                'c': "http://lca.jrc.it/ILCD/Common"}
    elif ns_type == 'ILCD_flow':
        return {None: "http://lca.jrc.it/ILCD/Flow",
                'c': "http://lca.jrc.it/ILCD/Common"}


###############################################################################

def str_(l):
    '''String construct with namespaces for verification'''
    
    return "/{http://www.EcoInvent.org/EcoSpold02}".join(['/']+l)


###############################################################################

def create_folder(name):
    '''Create a folder'''
    
    try:
        os.mkdir(name)
    except OSError:
        pass
    

###############################################################################

def sub(tree,name,par,attrib,var = 'processDataSet'):
    '''Make subelement'''
    
    if var not in ('processDataSet', 'flowDataSet'):
        s = ET.SubElement(par, name, attrib)
    else:
        if par in ('processDataSet', 'flowDataSet'):
            s = ET.SubElement(tree.getroot(), name, attrib)
        else:
            s = ET.SubElement(tree.find('/'+par), name, attrib)
    return s


###############################################################################
    
def root_(flow):
    '''Creates a root element'''
    
    root = ET.Element('root')
    root.append(flow)
    return ET.ElementTree(root)


###############################################################################

def texts(tree,name):
    '''Verify text in element'''
    
    try:
        return tree.find(name).text
    except:
        return ''


###############################################################################

def check_flow_type(flow):
    '''Checks the type of flow'''
    
    if flow.find('.//{http://www.EcoInvent.org/EcoSpold02}classification') is not None:
        for class_ in flow.findall('.//{http://www.EcoInvent.org/EcoSpold02}classification'):
            value = class_.find('{http://www.EcoInvent.org/EcoSpold02}classificationSystem').text
            if class_.find('{http://www.EcoInvent.org/EcoSpold02}classificationValue') is not None and value == "By-product classification":
                type_ = class_.find('{http://www.EcoInvent.org/EcoSpold02}classificationValue').text
                if type_ == "Waste":
                    return 'Waste flow'
                elif type_ in ("Recyclable", "allocatable product"):
                    return 'Product flow'
                
    # If there is no classification of the sort, use output and input values
    if flow.find('.//{http://www.EcoInvent.org/EcoSpold02}outputGroup') is not None:
        if flow.find('.//{http://www.EcoInvent.org/EcoSpold02}outputGroup').text == '0':
            return 'Product flow'
        elif flow.find('//{http://www.EcoInvent.org/EcoSpold02}outputGroup').text in ('2','3'):
            return 'Waste flow'
    else:
        return 'Other flow'
    
    
###############################################################################

def do_uncertainty(tree, par, mean_v, bool_ = 0, path = '//{http://www.EcoInvent.org/EcoSpold02}uncertainty', mult = 1, isGeneralComment = None):
    '''Uncertainty calculation for any variable'''
    
    # Subtree of property correction
    if tree.find('./').get('propertyId'):
        tree = tree.find('./')
    
    if tree.find(path) is not None:
        
        # Checks if variable gets a value or an amount as field name
        def create_minmax_elem(bool_):
            if bool_:
                min_a = ET.SubElement(par, 'minimumAmount')
                max_a = ET.SubElement(par, 'maximumAmount')
            else:
                min_a = ET.SubElement(par, 'minimumValue')
                max_a = ET.SubElement(par, 'maximumValue')
            return min_a, max_a
        
        # Sets uncertainty distribution name
        unc_type_text = tree.find(path)[0].tag.split('}')[1]
            
        # Does uncertainty calculations depending on the type of uncertainty attributed to the flow
        if unc_type_text == 'lognormal':
            s = exp((float(tree.find(path)[0].attrib['varianceWithPedigreeUncertainty'])*(mult)**(1/2))**(1/2))
            min_a, max_a = create_minmax_elem(bool_)
            min_a.text = str(float(mean_v)/s)
            max_a.text = str(float(mean_v)*s)
            unc_type = ET.SubElement(par, 'uncertaintyDistributionType')
            unc_type.text = 'log-normal'
            std95 = ET.SubElement(par, 'relativeStandardDeviation95In')
            std95.text = str(s)[:5]
        elif unc_type_text == 'normal':
            s = (float(tree.find(path)[0].attrib['varianceWithPedigreeUncertainty'])*(mult)**(1/2))**(1/2)
            min_a, max_a = create_minmax_elem(bool_)
            min_a.text = str(float(mean_v)-s)
            max_a.text = str(float(mean_v)+s)
            unc_type = ET.SubElement(par, 'uncertaintyDistributionType')
            unc_type.text = unc_type_text
            std95 = ET.SubElement(par, 'relativeStandardDeviation95In')
            std95.text = str(s)[:5]
        elif unc_type_text in ('normal', 'triangular'):
            min_a, max_a = create_minmax_elem(bool_)
            min_a.text = tree.find(path)[0].attrib['minValue']
            max_a.text = tree.find(path)[0].attrib['maxValue']
            unc_type = ET.SubElement(par, 'uncertaintyDistributionType')
            unc_type.text = unc_type_text
        else:
            if isGeneralComment is not None:
                if isGeneralComment == '':
                    comment = ET.SubElement(par, 'generalComment',{"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                    comment.text = 'Uncertainty not supported (Beta, Gamma or Binomial) or Undefined.'
                else:
                    isGeneralComment.text += "; " + 'Uncertainty not supported (Beta, Gamma or Binomial) or Undefined.'
            else:
                if par.find("comment") is not None:
                    comment = par.find("comment")
                    comment.text += '; Uncertainty not supported (Beta, Gamma or Binomial) or Undefined'
                else:
                    comment = ET.SubElement(par, 'comment',{"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                    comment.text = 'Uncertainty not supported (Beta, Gamma or Binomial) or Undefined.'
        
        # Checks if there is any comment on the uncertainty
        if texts(tree, path+'/{http://www.EcoInvent.org/EcoSpold02}comment'):
            if par.find("comment") is not None:
                comment = par.find("comment")
                comment.text = comment.text + '; ' + tree.find(path+'/{http://www.EcoInvent.org/EcoSpold02}comment').text
            else:
                if isGeneralComment is not None:
                    if isGeneralComment == '':
                        comment = ET.SubElement(par, 'generalComment',{"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                        comment.text = tree.find(path+'/{http://www.EcoInvent.org/EcoSpold02}comment').text
                    else:
                        isGeneralComment.text += "; " + tree.find(path+'/{http://www.EcoInvent.org/EcoSpold02}comment').text
                else:
                    comment = ET.SubElement(par, 'comment',{"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                    comment.text = tree.find(path+'/{http://www.EcoInvent.org/EcoSpold02}comment').text


###############################################################################

def do_reference(reference, type_r, refObjectId, short_d, version = '01.00.000'):
    '''Make a reference subelement'''
    
    # Set basic reference subelements
    reference.set('type', type_r)
    reference.set('refObjectId', refObjectId)
    if refObjectId == 'a97a0155-0234-4b87-b4ce-a45da52f2a40':
        version = '01.01.000'
    reference.set('version', version)
    
    # Set path for the given referenced file
    folder = {'contact data set':'../contacts/',
              'source data set':'../sources/',
              'flow data set':'../flows/',
              'flow property data set':'../flowproperties/',
              'unit group data set':'../unitgroups/'}.get(type_r)
    
    reference.set('uri', folder + refObjectId + '.xml')
    
    # Creates a short description subelement on the reference
    if short_d is not None:
        short_description = ET.SubElement(reference, '{http://lca.jrc.it/ILCD/Common}shortDescription')
        short_description.set('{http://www.w3.org/XML/1998/namespace}lang','en')
        short_description.text = short_d
                

###############################################################################
    
def do_classification(text, classification):
    '''ISIC Classification''' 
    
    classification.set('name', 'ISIC rev.4 ecoinvent')
    classification.set('classes', '../classification.xml')
    
    div_text = text.split(':')
    
    t = 2
    if len(div_text[0]) != 5:
        if len(div_text[0]) != 3:
            z = 2
        else:
            z = 1
    else:
        z = 3
    lvl = ['']*4
    
    # Find the correspondence of classification in ISIC.txt file
    path_ = os.path.abspath(os.path.dirname(__file__))
    pathMP = os.path.join(path_, "Mapping_files/ISIC.txt")
    with open(pathMP,'r') as f:
        for line in f:
            if div_text[0][:-z] == line.split(':::')[0]:
                lvl[t] = div_text[0][:-z] + ':' + line.split(':::')[1]
                t = t-1
                z = z-1
            elif div_text[0] == line.split(':::')[0]:
                lvl[3] = line.split(':::')[2].rstrip('\n')
                lvl[0] = div_text[0] + ':' + line.split(':::')[1]
                break
    
    lvl = [l for l in lvl if l != '']
    if div_text[0] == '19a':
        lvl = ['19a:Liquid and gaseous fuels from biomass', "01:Crop and animal production, hunting and related service activities", 'A.Agriculture, forestry and fishing']
    
    # Set class' text
    for i, level in enumerate(lvl[::-1]):
        clas = ET.SubElement(classification, '{http://lca.jrc.it/ILCD/Common}class')
        clas.set('level',str(i))
        clas.text = level
        

###############################################################################

def convert_unit_raw(v, u1, u2, full_result = False):
    '''This function converts a unit based on UDUNITS unit convertion library [cfunits for python]'''
    
    def check(u, key):
        '''This function checks if unit has any prefix'''
        if unit_s[key].get(u):
            return False
        else:
            return True
        
    def check_(u, key):
        '''This function checks if unit has any prefix and correct the value'''
        
        # If unit is a valid unit, return it
        if unit_s[key].get(u):
            return unit_s[key][u]
        # Elif unit has a prefix
        else:
            for prefix in unit_pref.keys():
                for unit in unit_s[key].keys():
                    if u == prefix+unit:
                        u = u[len(prefix):]
                        n_unit = list(unit_s[key][u])
                        
                        # Exponent in the case of higher order units
                        if "2" in u or "²" in u or 'square' in u:
                            a = 2
                        elif "3" in u or "³" in u or 'cubic' in u:
                            a = 3
                        else:
                            a = 1
                        
                        n_unit[1] *= unit_pref[prefix]**a
                        return tuple(n_unit)
            else:
                return None
        
    def check_1(u, key):
        '''This function checks if any string correction can yield an unit value'''
        
        # If unit is seperated by a space, try verifications
        if re.search(' ', u):
            
            mult_ = 1
            
            # If the first word of the unit is a valid unit (EX: calorie thermochemical)
            if isinstance(check_(u.split(' ')[0], key), tuple):
                
                # If the first word has a prefix, add a multiplier
                if check(u.split(' ')[0], key):
                    for prefix in unit_pref.keys():
                        for unit in unit_s[key].keys():
                            if u.split(' ')[0] == prefix+unit:
                                u = u[len(prefix):]
                                
                                # Exponent in the case of higher order units
                                if "2" in u or "²" in u or 'square' in u:
                                    a = 2
                                elif "3" in u or "³" in u or 'cubic' in u:
                                    a = 3
                                else:
                                    a = 1
                                
                                mult_ = unit_pref[prefix]**a
                
                # Check if changing order of the first and last words results in a valid unit
                if isinstance(check_(u.split(' ')[-1]+'_'+u.split(' ')[0], key), tuple):
                    f = list(check_(u.split(' ')[-1]+'_'+u.split(' ')[0], key))
                    f[1] *= mult_
                    return tuple(f)
                
                # Check if there is an indication of ISO IT unit
                elif "IT" in u:
                    if isinstance(check_(u.split(' ')[0], key), tuple):
                        f = list(check_(u.split(' ')[0], key))
                        f[1] *= mult_
                        return tuple(f)
                    
            # If there is only a problem with space, a non-valid character on UDUNITS
            if isinstance(check_('_'.join(u.split(' ')), key), tuple):
                return check_('_'.join(u.split(' ')), key)
            
            # Check if changing order of the first and last words results in a valid unit
            if isinstance(check_(u.split(' ')[-1]+'_'+u.split(' ')[0], key), tuple):
                f = list(check_(u.split(' ')[-1]+'_'+u.split(' ')[0], key))
                f[1] *= mult_
                return tuple(f)
            
        # If it is a plural form
        if re.search('s$', u.lower()):
            if isinstance(check_(u[:-1], key), tuple):
                return check_(u[:-1], key)
            
        # Else
        else:
            return None
    
    
    # Main unit conversion
    u1 = u1.strip()
    u2 = u2.strip()
    
    v = float(v)
    
    for key, units in unit_s.items():
        
        a, b = None, None
        
        a = check_(u1, key)
        b = check_(u2, key)
        
        # If direct check fails, check for units changing the string
        if a is None:
            a = check_1(u1, key)
        if b is None:
            b = check_1(u2, key)
    
        if a is not None and b is not None:
            break
    else:
        print(f"Warning: Unit {u1} or {u2} could not be converted")
        return f"UnitConversion({v},{u1},{u2})"
    
    if a[0] != b[0]:
        print("Warning: units with different measures {a[0]} and {b[0]}")
        return f"UnitConversion({v},{u1},{u2})"
    
    # Calculation of the new value after the conversion
    else:
        
        result = v * a[1]
        
        if len(a) == 4:
            result = a[2](result)
            
        result *= 1/b[1]
        
        if len(b) == 4:
            result = b[3](result)
        
        if full_result:
            return a, b
        else:
            return str(result)


###############################################################################
#########################***COMPLEX FUNCTIONS***###############################
###############################################################################

def allocation(e_tree):
    '''
    Loops through intermediate exchanges on Ecospold2 file and return a list of 
    allocation fractions for ILCD output flows
    '''
    
    # Verifies if Ecospold2 has an masterAllocationProperty
    if e_tree.find(str_(['activity[@masterAllocationPropertyId]'])) is not None:
        
        # Counters and booleans to work with Reference Flow
        a, count, ver = 0, 1, True
        
        # Allocation list declaration
        al, flow_id = [], [] 
        
        # For flow inside Ecospold2, verifies if it is an output flow
        for flow in e_tree.iterfind(str_(['intermediateExchange'])):
            if flow.find('{http://www.EcoInvent.org/EcoSpold02}outputGroup') is not None:
                
                # Check if flow is the Reference Flow
                if ver:
                    if flow.find('{http://www.EcoInvent.org/EcoSpold02}outputGroup').text == '0':
                        count -=1
                        a = count
                        ver = False
                        
                # Check for specific allocation properties
                if flow.get('specificAllocationPropertyId'):
                    id_allocation = flow.get('specificAllocationPropertyId')
                else:
                    id_allocation = e_tree.find(str_(['activity'])).get('masterAllocationPropertyId')
                    
                # Loop through the flow properties to get specific allocation fractions
                for prop in flow.iterfind('{http://www.EcoInvent.org/EcoSpold02}property'):
                    if prop.get('propertyId') == id_allocation:
                        al.append(float(prop.get('amount'))*float(flow.get('amount')))
                        flow_id.append((flow.get('id'), count-a))
            
            count +=1
            a = 0
        
        # Allocation list preparation for main mapping application
        al = list(map(lambda x: x/sum(al),al))
        alloc = tuple(zip(flow_id, al))
        
        return alloc
    

###############################################################################

def flow_set_and_internal_ID(i_tree, outputRef, countNonReference, referencePassed, alInfoActivation, flow, ref_exc):
    '''Creates flow element and sets an internal ID as attribute'''
    
    # Output case
    if outputRef is not None:
        dir_ = 'Output'
        if outputRef.text == '0':
            if referencePassed:
                
                # Product flow with outputGroup 0 are prioritized over Waste flows
                if check_flow_type(flow) == "Product flow":
                    ref_exc.set('dataSetInternalID',str(countNonReference))
                    countNonReference += 1
                    ref_exc.remove(ref_exc.find('allocations'))
                    exchange = sub(i_tree,'exchange','exchanges',{'dataSetInternalID':'0'})
                    ref_exc = exchange
                    alInfoActivation = True
                else:
                    exchange = sub(i_tree,'exchange','exchanges',{'dataSetInternalID':str(countNonReference)})
                    countNonReference += 1
            else:
                exchange = sub(i_tree,'exchange','exchanges',{'dataSetInternalID':'0'})
                ref_exc = exchange
                alInfoActivation = True
                referencePassed = True
        else:
            exchange = sub(i_tree,'exchange','exchanges',{'dataSetInternalID':str(countNonReference)})
            countNonReference += 1
    
    # Input case
    else:
        dir_ = 'Input'
        exchange = sub(i_tree,'exchange','exchanges',{'dataSetInternalID':str(countNonReference)})
        countNonReference += 1
        
    e_direction = ET.SubElement(exchange,'exchangeDirection')
    e_direction.text = dir_
        
    return exchange, countNonReference, referencePassed, alInfoActivation, ref_exc


###############################################################################

def flow_allocation_info(al, exc):
    '''Creates allocation subelements inside the flow'''
    
    for el in al:
        element_al1 = ET.SubElement(exc, 'allocations')
        element_al = ET.SubElement(element_al1, 'allocation')
        element_al.set('internalReferenceToCoProduct', str(el[0][1]))
        element_al.set('allocatedFraction', str(el[1]*100))


###############################################################################

def f_property(tree, el, *args, **kwargs):
    '''Creates datasets for a flow property and its units'''
    
    from Lavoisier.conversion_caller import save_dir

    # Creates folders if necessary
    create_folder(save_dir+'/flowproperties')
    create_folder(save_dir+'/unitgroups')
    
    
    if "intermediateExchange" in tree.find('./').tag:
        unit_id = tree.find('./').get('unitId')
    elif "elementaryExchange" in tree.find('./').tag:
        unit_id = tree.find('./').get('unitId')
    else:
        unit_id = kwargs['unit_id']
        
    flow_prop, info, factor = unit_conv(unit_id)
    
    # Sets the ID of the flowPropertyDataSet
    el.set('dataSetInternalID', args[2][0])
    
    # Check if the property is a special property that is not on ILCD default properties
    if kwargs.get('special_property'):
        
        # Set a reference to property
        ref = ET.SubElement(el, 'referenceToFlowPropertyDataSet')
        mv = ET.SubElement(el, 'meanValue')
        do_reference(ref, 'flow property data set', kwargs.get('uuid'), kwargs.get('name'))
        
        # Copies the flowPropertyDataSet and unitDataSet from the repository to the zip folder
        mv.text = str(float(kwargs.get('amount')) * factor)
        
            
    # Else it's a default property
    else:
        
        # Set reference variables for each flow property
        if len(args[0].findall('flowProperties/flowProperty')) == 1:
            ref = sub(args[0], 'referenceToFlowPropertyDataSet', 'flowProperties/flowProperty', None)
            mv = sub(args[0], 'meanValue', 'flowProperties/flowProperty', None)
        else:
            ref = ET.SubElement(el, 'referenceToFlowPropertyDataSet')
            mv = ET.SubElement(el, 'meanValue')
        
        # If the unit is converted
        if len(args) == 3:
            args = list(args)
            args.append(tree.find('./').get('unitId'))
        
        flow_prop, info, factor = unit_conv(args[3])
        
        # Set reference subelement
        do_reference(ref, 'flow property data set', flow_prop[2], flow_prop[0])
        
        # Set correct mean value to flowProperties
        mv.text = args[2][-1]
        
    # Create flowPropertyDataSet and unitGroupDataSet
    if kwargs.get('special_property'):
        nn = tree.find('{http://www.EcoInvent.org/EcoSpold02}name').text
        nn = nn[0].upper() + nn[1:]
        additional_files.create_f_prop(args[1], tree.get('propertyId'), nn, flow_prop[3], info[-1])
        additional_files.create_unit_group(args[1], flow_prop[3], "Units of " + info[-1], info[-1], flow_prop[1])
    else:
        additional_files.create_f_prop(args[1], flow_prop[2], flow_prop[0], flow_prop[3], info[-1])
        additional_files.create_unit_group(args[1], flow_prop[3], "Units of " + info[-1], info[-1], flow_prop[1])


###############################################################################

def unit_conv(name, single = False):
    '''Converts flow property units and do single unit conversion for ILCD standards'''
    
    # Single unit conversion
    if single:
        return convert_unit_raw(*name)
                
    # Flow property unit conversion
    else:
        
        info = unit_ecoinvent[name]
        flow_prop = unit_uid[info[1]]
        mult_ = convert_unit_raw(1, info[0], flow_prop[1])
        
        return flow_prop, info, float(mult_)
            

###############################################################################

def set_equation(is_math, o_t):
    '''Corrects the equations of variables to make them usable'''

    # Unit convertion correction
    if re.search('UnitConversion', is_math):
        for elem in re.findall("UnitConversion\(([\w -.',]+?)\)", is_math):
            elem_ = elem.replace("'", '').split(', ')
            elem_[0] = elem_[0].replace(',','.')
            is_math = re.sub('UnitConversion\('+elem+'\)',unit_conv(elem_, True),is_math)
    # Reference to other flow ID or production volume ID correction
    if re.search('Ref\(', is_math):
        for elem in re.findall("Ref\('(.*?)'\)", is_math):
            for e in o_t.findall(str_(['intermediateExchange'])):
                if e.get('id') == elem.split("'")[0]:
                    elem_ = elem.split("'")
                    if len(elem_)>1:
                        if elem_[2] == 'ProductionVolume':
                            value = e.get('productionVolumeAmount')
                    else:
                        value = e.get('amount')
                    is_math = re.sub("Ref\('"+elem+"'\)", value, is_math)
    # Percentage correction
    if re.search('%', is_math):
        is_math = re.sub('%','/100',is_math)
    # Float with ',' as decimal separator correction
    if re.search('[0-9]+,[0-9]+', is_math):
        is_math = re.sub(',', '.', is_math)
        
    return is_math
       

###############################################################################

@memoryPar
def parameter_for_v_calculation(o_tree, name, o_t, formula, amount, comment, uncertainty):
    '''Creates a variableParameter for Ecospold2 variable equation'''
    
    math_r = o_tree.find('//mathematicalRelations')
    var = ET.SubElement(math_r,'variableParameter')
    
    var.set('name', name)
    
    form_v = ET.SubElement(var,'formula')
    f = set_equation(formula, o_t)
    form_v.text = f
    
    mean_v = ET.SubElement(var,'meanValue')
    mean_v.text = str(amount)
    
    if uncertainty[0] is not None:
        do_uncertainty(root_(uncertainty[1]), var, amount, path = uncertainty[2])
        
    if comment != '' and comment is not None:
        if len(comment) > 500:
            gc = o_tree.find("//dataSetInformation/{http://lca.jrc.it/ILCD/Common}generalComment")
            if gc is not None:
                gc.text += '\n' + 'Comment for [variable] ' + name + ': ' + comment
                if var.find("comment") is None:
                    com = ET.SubElement(var, 'comment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                    com.text = "Variable comment placed in dataset's general comment for passing the number of characters"
            else:
                gc = ET.SubElement(o_tree.find('//dataSetInformation'), '{http://lca.jrc.it/ILCD/Common}generalComment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                gc.text = 'Comment for [variable] ' + name + ': ' + comment
                if var.find("comment") is None:
                    com = ET.SubElement(var, 'comment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                    com.text = "Variable comment placed in dataset's general comment for passing the number of characters"
        else:
            if var.find("comment") is None:
                com = ET.SubElement(var, 'comment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                com.text = comment
            else:
                com = var.find("comment")
                com.text += '; ' + comment
        
    return name, f


###############################################################################

@memoryPar
def parameter_for_variables(o_tree, name, amount, comment, uncertainty):
    '''Creates a variableParameter for Ecospold2 variable values'''
    
    math_r = o_tree.find('//mathematicalRelations')
    var = ET.SubElement(math_r,'variableParameter')
    
    var.set('name', name)
    
    mean_v = ET.SubElement(var,'meanValue')
    mean_v.text = str(amount)
    
    if uncertainty[0] is not None:
        do_uncertainty(root_(uncertainty[1]), var, amount, path = uncertainty[2])
        
    if comment != '' and comment is not None:
        if len(comment) > 500:
            gc = o_tree.find("//dataSetInformation/{http://lca.jrc.it/ILCD/Common}generalComment")
            if gc is not None:
                gc.text += '\n' + 'Comment for [variable] ' + name + ': ' + comment
                if var.find("comment") is None:
                    com = ET.SubElement(var, 'comment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                    com.text = "Variable comment placed in dataset's general comment for passing the number of characters"
            else:
                gc = ET.SubElement(o_tree.find('//dataSetInformation'), '{http://lca.jrc.it/ILCD/Common}generalComment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                gc.text = 'Comment for [variable] ' + name + ': ' + comment
                if var.find("comment") is None:
                    com = ET.SubElement(var, 'comment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                    com.text = "Variable comment placed in dataset's general comment for passing the number of characters"
        else:
            if var.find("comment") is None:
                com = ET.SubElement(var, 'comment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                com.text = comment
            else:
                com = var.find("comment")
                com.text += '; ' + comment
        
        
    return name


###############################################################################

@memoryPar
def parameter_for_unit_conversions(o_tree, name, original, converted, factor):
    '''Creates a variableParameter for unit conversion values'''
    
    math_r = o_tree.find('//mathematicalRelations')
    var = ET.SubElement(math_r,'variableParameter')
    
    var.set('name', f'_{original}_to_{converted}_')
    
    mean_v = ET.SubElement(var,'meanValue')
    mean_v.text = str(factor)
    
    return f'_{original}_to_{converted}_'
    

###############################################################################

@memoryPar
def equation_for_unit_conversion(o_tree, name, o_t, original, converted, factor, amount, formula, uncertainty, id_for_name):
    '''Creates a variableParameter for unit conversion values'''
    
    math_r = o_tree.find('//mathematicalRelations')
    var = ET.SubElement(math_r,'variableParameter')
    
    if len(f'{original}_to_{converted}_') > 14:
        nn = f'{original[:5]}_to_{converted[:5]}_'+id_for_name
        var.set('name', nn)
    else:
        nn = f'{original}_to_{converted}_'+id_for_name
        var.set('name', nn)
    
    form_v = ET.SubElement(var,'formula')
    form_v.text = set_equation('('+formula+f')*_{original}_to_{converted}_', o_t)
    
    mean_v = ET.SubElement(var,'meanValue')
    mean_v.text = str(amount*factor)
    
    if uncertainty[0] is not None:
        do_uncertainty(root_(uncertainty[1]), var, amount, path = uncertainty[2])
        
    com = ET.SubElement(var, 'comment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
    com.text = "Additional equation for unit conversion"
    
    
    return nn
    

###############################################################################
        
def set_parameters_and_variables(o_t, f_tree, o_tree, flow, exc, orig_id, is_flow=1):
    '''
    Multifunction to convert variableParameters, mathematical equations and
        properties for flows and parameters of Ecospold2
    Attribution of the resulting value for a different unit is done here
    Uncertainty of equations, parameters, volume of production and properties are done here
        
    Inputs:
        flow: single flow element from Ecospold2 (parameter element for parameter entries)
        exc:  single exchange root element for ILCD (None for parameter entries)
        is_flow: 1 for flow and 0 for parameters
    '''
    
    # Functions to check if there is comment
    def check_comment(field):
        nonlocal flow
        if flow.find(field) is not None:
            return texts(flow, field)
        else:
            return ''
    
    def check_comment_prop(prop, field):
        if prop.find(field) is not None:
            return texts(prop, field)
        else:
            return ''
        
    # Functions to check if there is uncertainty
    def check_unc(field):
        nonlocal flow
        if flow.find(field) is not None:
            return (flow.find(field), flow, field)
        else:
            return (None, None, None)
    
    def check_unc_prop(prop, field):
        if prop.find(field) is not None:
            return (prop.find(field), prop, field)
        else:
            return (None, None, None) 
    
    def order_dataSources_subelements(elem):
        return {'dataCutOffAndCompletenessPrinciples':0,
                 'deviationsFromCutOffAndCompletenessPrinciples':1,
                 'dataSelectionAndCombinationPrinciples':2,
                 'deviationsFromSelectionAndCombinationPrinciples':3,
                 'dataTreatmentAndExtrapolationsPrinciples':4,
                 'deviationsFromTreatmentAndExtrapolationPrinciples':5,
                 'referenceToDataHandlingPrinciples':6,
                 'referenceToDataSource':7,
                 'percentageSupplyOrProductionCovered':8,
                 'annualSupplyOrProductionVolume':9,
                 'samplingProcedure':10,
                 'dataCollectionPeriod':11,
                 'uncertaintyAdjustments':12,
                 'useAdviceForDataSet':13}.get(elem.tag)
    
    # Initial variables 
    id_ = set(['0']) # Zero value has to be in the original id_ set
    is_var_with_equation = False
    id_f = None # Specific error when isCalculatedAmount = true but there are no equation
    
    # Amount of ecoinvent flow
    amount = float(flow.get('amount'))
    
    # Get activityLink if exists
    if flow.get('activityLinkId'):
        if exc.find('generalComment') is not None:
            exc.find('generalComment').text += '; ' + "Original provider ID: " + flow.get('activityLinkId')
        else:
            gcom = ET.SubElement(exc, 'generalComment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
            gcom.text = "Original provider ID: " + flow.get('activityLinkId')    
    
    
    # 1. Create parameter for the main conversion of unit on the flow/parameter and get unit conversion values
    if flow.find('{http://www.EcoInvent.org/EcoSpold02}unitName') is not None:
        
        if is_flow:
            if exc.find('generalComment') is not None:
                if exc.find('generalComment').text is not None:
                    exc.find('generalComment').text = f"[{flow.find('{http://www.EcoInvent.org/EcoSpold02}unitName').text}] " + exc.find('generalComment').text
                else:
                    exc.find('generalComment').text = f"[{flow.find('{http://www.EcoInvent.org/EcoSpold02}unitName').text}] "
            else:
                gcom = ET.SubElement(exc, 'generalComment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                gcom.text = f"[{flow.find('{http://www.EcoInvent.org/EcoSpold02}unitName').text}] "
                    
        
        # Check for values with only unitNames and no Id
        if flow.get('unitId'):
            flow_prop, info_eco, factor = unit_conv(flow.get('unitId'))
        else:
            u_ = flow.find('{http://www.EcoInvent.org/EcoSpold02}unitName').text
            for k,v in unit_ecoinvent.items():
                if u_ == v[0]:
                    flow_prop, info_eco, factor = unit_conv(k)
                    break
    else:
        flow_prop, info_eco, factor = None, None, 1

    
    # 1.5: Modify mean values and resulting values if there is a unit conversion
    if is_flow and factor != 1:
        exc.find('meanAmount').text = str(float(exc.find('meanAmount').text) * factor)
        exc.find('resultingAmount').text = str(float(exc.find('resultingAmount').text) * factor)
        
        
    # 2. Create parameters in ILCD for the parameters already in Ecospold2 inside flows or parameter fields
    if flow.get('variableName') or flow.get('isCalculatedAmount') == "true":
            
        
        if is_flow:
            exc.find('meanAmount').text = '1.0'
            ref_to_var = ET.SubElement(exc,'referenceToVariable')
        
        # Checks if variable is calculated
        if flow.get('isCalculatedAmount') == "true":
            
            if flow.get('variableName'):
                name = flow.get('variableName')
                is_var_with_equation = True
            else:
                if flow.get('intermediateExchangeId'):
                    name = 'Eq_'+flow.get('id').replace('-','_')
                elif flow.get('elementaryExchangeId'):
                    name = 'Eq_'+flow.get('elementaryExchangeId').replace('-','_')
                else:
                    name = 'Eq_[par]_'+flow.get('parameterId').replace('-','_')
                
            # There are datasets which only indicates that is calculated
            if flow.get('mathematicalRelation', '') != '':
                id_f, formula = parameter_for_v_calculation(o_tree, 
                                                            name, o_t,
                                                            flow.get('mathematicalRelation').rstrip(), 
                                                            amount,
                                                            check_comment('{http://www.EcoInvent.org/EcoSpold02}comment'),
                                                            check_unc('{http://www.EcoInvent.org/EcoSpold02}uncertainty')
                                                            )
                id_.add(id_f)
            else:
                is_var_with_equation = False
            
        if flow.get('variableName') and not is_var_with_equation:
            formula = flow.get('variableName')
            id_f = parameter_for_variables(o_tree, 
                                            flow.get('variableName'),
                                            amount,
                                            check_comment('{http://www.EcoInvent.org/EcoSpold02}comment'),
                                            check_unc('{http://www.EcoInvent.org/EcoSpold02}uncertainty')
                                            )
            id_.add(id_f)
        
            
        # Checks if there was a unit conversion over the equation and/or variableParameter
        if is_flow and id_f:
            if factor != 1:
                
                if f'_{info_eco[0]}_to_{flow_prop[1]}_' not in orig_id:
                    id_.add(parameter_for_unit_conversions(o_tree,
                                                           f'_{info_eco[0]}_to_{flow_prop[1]}_',
                                                           info_eco[0], 
                                                           flow_prop[1], factor))
                
                if flow.get('intermediateExchangeId'):
                    name = flow.get('id').replace('-','_')
                elif flow.get('elementaryExchangeId'):
                    name = flow.get('elementaryExchangeId').replace('-','_')
                
                if f'{info_eco[0]}_to_{flow_prop[1]}_'+name not in orig_id:
                    id_f = equation_for_unit_conversion(o_tree,
                                                         f'{info_eco[0]}_to_{flow_prop[1]}_'+name,
                                                         o_t,
                                                         info_eco[0], 
                                                         flow_prop[1],
                                                         factor,
                                                         amount,
                                                         formula,
                                                         check_unc('{http://www.EcoInvent.org/EcoSpold02}uncertainty'),
                                                         name)
                    id_.add(id_f)
                
                
                
                ref_to_var.text = id_f
                
            else:
                ref_to_var.text = id_f
                
        elif is_flow:
            ref_to_var.getparent().remove(ref_to_var)
            

    # 3. Check for production volume values and their equations if any
    if flow.get('productionVolumeAmount'):
        
        p_amount = flow.get('productionVolumeAmount')
        
        p_text = "Annual prod. "+ flow.find("{http://www.EcoInvent.org/EcoSpold02}name").text +\
                        ':' + p_amount +\
                        flow.find('{http://www.EcoInvent.org/EcoSpold02}unitName').text
                        
        # Set elements representing prodution volume on ILCD
        if flow.find('.//{http://www.EcoInvent.org/EcoSpold02}outputGroup') is not None:
            if flow.find('.//{http://www.EcoInvent.org/EcoSpold02}outputGroup').text == "0" and check_flow_type(flow) != "Waste flow":
                if o_tree.find('//dataSourcesTreatmentAndRepresentativeness/annualSupplyOrProductionVolume') is not None:
                    if p_text not in o_tree.find('//dataSourcesTreatmentAndRepresentativeness/annualSupplyOrProductionVolume').text:
                        annual_s = o_tree.find('//dataSourcesTreatmentAndRepresentativeness/annualSupplyOrProductionVolume')
                        annual_s.text += "; " + p_text
                else:
                    annual_s = ET.SubElement(o_tree.find('//dataSourcesTreatmentAndRepresentativeness'), 'annualSupplyOrProductionVolume', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                    annual_s.text = p_text
            else:
                if o_tree.find("//dataSetInformation/{http://lca.jrc.it/ILCD/Common}generalComment") is not None:
                    gc = o_tree.find("//dataSetInformation/{http://lca.jrc.it/ILCD/Common}generalComment")
                    if gc.text is not None:
                        if p_text not in gc.text:
                            gc.text += "; " + p_text
                    else:
                        gc.text = p_text
                else:
                    gc = ET.SubElement(o_tree.find("//dataSetInformation"), "{http://lca.jrc.it/ILCD/Common}generalComment", {"{http://www.w3.org/XML/1998/namespace}lang": 'en'})
                    gc.text = p_text
        else:
            if o_tree.find("//dataSetInformation/{http://lca.jrc.it/ILCD/Common}generalComment") is not None:
                gc = o_tree.find("//dataSetInformation/{http://lca.jrc.it/ILCD/Common}generalComment")
                if gc.text is not None:
                    if p_text not in gc.text:
                        gc.text += "; " + p_text
                else:
                    gc.text = p_text
            else:
                gc = ET.SubElement(o_tree.find("//dataSetInformation"), "{http://lca.jrc.it/ILCD/Common}generalComment", {"{http://www.w3.org/XML/1998/namespace}lang": 'en'})
                gc.text = p_text
                
        dd = o_tree.find('//dataSourcesTreatmentAndRepresentativeness')
        
        dd[:] = sorted(dd, key=order_dataSources_subelements)

        # Set variables on mathematicalRelations relative to productionVolume value or calculations
        if flow.get('productionVolumeVariableName') or flow.get('productionVolumeMathematicalRelation'):
            is_var_with_equation = False # Default
            
            # Checks if variable is calculated
            if flow.get('productionVolumeMathematicalRelation'):
                
                if flow.get('productionVolumeVariableName'):
                    name = flow.get('productionVolumeVariableName')
                    is_var_with_equation = True
                else:
                    if flow.get('intermediateExchangeId'):
                        ex_id = flow.get('id').replace('-','_')
                    elif flow.get('elementaryExchangeId'):
                        ex_id = flow.get('elementaryExchangeId').replace('-','_')
                    uname = flow.find('{http://www.EcoInvent.org/EcoSpold02}unitName').text
                    if len(uname) < 8:
                        name = 'pvl['+ uname +']_'+ex_id
                    else:
                        name = 'pvl['+ uname[:8] +']_'+ex_id
                
                id_f, formula = parameter_for_v_calculation(o_tree, 
                                                    name, o_t,
                                                    flow.get('productionVolumeMathematicalRelation').rstrip(), 
                                                    p_amount,
                                                    check_comment('{http://www.EcoInvent.org/EcoSpold02}productionVolumeComment'),
                                                    check_unc('{http://www.EcoInvent.org/EcoSpold02}productionVolumeUncertainty')
                                                    )
                id_.add(id_f)
                
            if flow.get('productionVolumeVariableName') and not is_var_with_equation:
                formula = flow.get('productionVolumeVariableName')
                id_f = parameter_for_variables(o_tree, 
                                                flow.get('productionVolumeVariableName'),
                                                p_amount,
                                                check_comment('{http://www.EcoInvent.org/EcoSpold02}productionVolumeComment'),
                                                check_unc('{http://www.EcoInvent.org/EcoSpold02}productionVolumeUncertainty')
                                                )
                id_.add(id_f)
            
            
    # 4. Check for flow properties, it's values and equations if any. 
    #    If it's an special flow property, creates a flowPropertyDataSet for it
    for prop in flow.iterfind('{http://www.EcoInvent.org/EcoSpold02}property'):
        
        amount_for_parameters = prop.get('amount')
       
        # Set variables on mathematicalRelations relative to flow parameters' value or calculations (don't use p_amount)
        if prop.get('variableName') or prop.get('isCalculatedAmount') == "true":
            is_var_with_equation = False    
            
            # Checks if variable is calculated
            if prop.get('isCalculatedAmount') == "true":
                
                if prop.get('variableName'):
                    name = prop.get('variableName')
                    is_var_with_equation = True
                else:
                    ex_id = prop.get('propertyId').replace(' ', '_')
                    if prop.find('{http://www.EcoInvent.org/EcoSpold02}unitName') is not None:
                        uname = prop.find('{http://www.EcoInvent.org/EcoSpold02}unitName').text
                        if len(uname) < 7:
                            name = 'prop['+ uname +']_'+ex_id
                        else:
                            name = 'prop['+ uname[:7] +']_'+ex_id
                    else:
                        name = 'prop[]_'+ex_id
                
                if prop.get('mathematicalRelation'):
                    id_f, formula = parameter_for_v_calculation(o_tree,
                                                        name, o_t,
                                                        prop.get('mathematicalRelation').rstrip(), 
                                                        amount_for_parameters,
                                                        check_comment_prop(prop, '{http://www.EcoInvent.org/EcoSpold02}comment'),
                                                        check_unc_prop(prop, '{http://www.EcoInvent.org/EcoSpold02}uncertainty')
                                                        )
                    id_.add(id_f)
                else:
                    is_var_with_equation = False
                
            if prop.get('variableName') and not is_var_with_equation:
                id_f = parameter_for_variables(o_tree, 
                                                prop.get('variableName'),
                                                amount_for_parameters,
                                                check_comment_prop(prop, '{http://www.EcoInvent.org/EcoSpold02}comment'),
                                                check_unc_prop(prop, '{http://www.EcoInvent.org/EcoSpold02}uncertainty')
                                                )
                id_.add(id_f)
        
        # For every new property in all the flows, creates a new flowPropertyDataSet for it and its specific unitDataSets
        if prop.find('{http://www.EcoInvent.org/EcoSpold02}name').text in special_property_list:
            
            # Some properties don't have unit names nor Ids, so are not converted as property
            if prop.find('{http://www.EcoInvent.org/EcoSpold02}unitName') is not None:
                el = ET.SubElement(f_tree.find('//flowProperties'), 'flowProperty')
                f_property(prop, el, f_tree, o_tree, [str(len(f_tree.findall('//flowProperty'))-1), ''], special_property = 1, uuid = prop.get('propertyId'), amount = str(float(amount_for_parameters)/factor), name = prop.find('{http://www.EcoInvent.org/EcoSpold02}name').text, unit_id = prop.get('unitId'))
    
    return id_


###############################################################################
########################***TRIGGERED FUNCTIONS***##############################
###############################################################################

def review(tree, el, *args):
    '''Review elements conversion and contactDataSet creation for reviewers'''
    
    # Check in review fields for the last review date
    if tree.findall(str_(['modellingAndValidation', 'review'])):
        last_revision = sorted([a.get('reviewDate') for a in tree.findall(str_(['modellingAndValidation', 'review']))])[-1]
    
    # Loop through all reviews and add information on ILCD tree
    for rev in tree.findall(str_(['modellingAndValidation', 'review'])):
        
        # Create review subelement
        _ = sub(args[0], 'review', args[1], None)
        
        # Check if review is the last review done
        if rev.get('reviewDate') == last_revision:
            args[0].find(args[1]).insert(0,_)
        
        # Create review subelements
        revDetails = ET.SubElement(_, '{http://lca.jrc.it/ILCD/Common}reviewDetails', {"{http://www.w3.org/XML/1998/namespace}lang": 'en'})
        revDetails.text = "Date of last review: " + rev.get('reviewDate') +\
                            "; Major version: " + rev.get('reviewedMajorRelease') +\
                            "." + rev.get('reviewedMajorRevision') +\
                            '; Minor version: ' + rev.get('reviewedMinorRelease') +\
                            "." + rev.get('reviewedMinorRevision')
        ref_rev = ET.SubElement(_, '{http://lca.jrc.it/ILCD/Common}referenceToNameOfReviewerAndInstitution')
        
        other_details = ET.SubElement(_, '{http://lca.jrc.it/ILCD/Common}otherReviewDetails', {"{http://www.w3.org/XML/1998/namespace}lang": 'en'})
        other_details.text = texts(rev,'{http://www.EcoInvent.org/EcoSpold02}otherDetails')
        
        # Create reference for reviewer contactDataSet
        do_reference(ref_rev, 'contact data set', rev.get('reviewerId'), rev.get('reviewerName'))
        
        # Create contactDataSet for reviewer
        additional_files.create_contact(ET.ElementTree(ET.Element("contactDataSet", version = '1.1', nsmap = {None: "http://lca.jrc.it/ILCD/Contact",
                                                                                       'c': "http://lca.jrc.it/ILCD/Common"})),
                        rev.get('reviewerId'), args[0], rev.get('reviewerName'), rev.get('reviewerEmail'))
        

###############################################################################
    
def bool_(tree, el, *args):
    '''Specific reference to url of images on comments'''
    
    # Check for imageURL's
    if '\nImageURL: ' in el.text:
        
        # Check if it is on the generalComment
        if 'generalComment' in el.tag:
            
            # Create reference for the external image url
            ref = sub(args[0], 'referenceToExternalDocumentation','processInformation/dataSetInformation',None)
            if re.search('[A-z0-9]{8}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{12}', el.text):
                ref_uuid = re.search('[A-z0-9]{8}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{12}', el.text).group()
            else:
                ref_uuid = str(uuid4())
            do_reference(ref, 'source data set', ref_uuid, 'dataSetIcon')
            
            # Create sourceDataSet for the image url
            additional_files.create_source(ET.ElementTree(ET.Element("sourceDataSet", version = '1.1', nsmap = {None: "http://lca.jrc.it/ILCD/Source",
                                                                                     'c': "http://lca.jrc.it/ILCD/Common"})),
                            ref_uuid, args[0], 'dataSetIcon (ImageURL)', re.search(r'ImageURL: ([A-z0-9.:/\-]*)', el.text).group(1))
        
        # Check if it is on the technologicalApplicability
        elif 'technologicalApplicability' in el.tag:
            
            # Create reference for the external image url
            ref = sub(args[0], 'referenceToTechnologyPictogramme','processInformation/technology',None)
            if re.search('[A-z0-9]{8}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{12}', el.text):
                ref_uuid = re.search('[A-z0-9]{8}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{12}', el.text).group()
            else:
                ref_uuid = str(uuid4())
            do_reference(ref, 'source data set', ref_uuid, 'Technology comment URL')
            
            # Create sourceDataSet for the image url
            additional_files.create_source(ET.ElementTree(ET.Element("sourceDataSet", version = '1.1', nsmap = {None: "http://lca.jrc.it/ILCD/Source",
                                                                                     'c': "http://lca.jrc.it/ILCD/Common"})),
                            ref_uuid, args[0], 'Technology comment (ImageURL)', re.search(r'ImageURL: ([A-z0-9.:/\-]*)', el.text).group(1))

    
###############################################################################
  
def time_year(tree, el, *args):
    '''Timestamp conversion for valid period'''
    
    # Start valid date
    if args[0] == 'start':
        el.text = str(strptime(tree.find(str_(['timePeriod'])).get('startDate'), '%Y-%m-%d').tm_year)
    
    # End valid date
    elif args[0] == 'end':
        a = strptime(tree.find(str_(['timePeriod'])).get('endDate'), '%Y-%m-%d')
        if a.tm_mon > 6:
            el.text = str(a.tm_year + 1)
        else:
            el.text = str(a.tm_year)
         
            
###############################################################################

def class_(tree, el, *args):
    '''Convert classification information using ISIC classification function'''
    
    for cl in tree.findall(str_(['activityDescription','classification'])):
        if 'ISIC rev.4 ecoinvent' in cl[0].text:        
            do_classification(cl[1].text, el)


###############################################################################
            
def pedigree(tree, el, *args):
    '''Set the values of pedigree matrix as a comment (uncertainty done in do_uncertainty function)'''
    
    ped = tree.find(str_(['uncertainty','pedigreeMatrix'])).values()
    ell = el.getparent()
    if ell[-2].tag == 'generalComment':
        gc1 = ell[-2]
        gc1.text = 'Pedigree: ('+','.join(ped)+'). ' + gc1.text if gc1.text is not None else ''
    
    ell.remove(ell[-1])
    
    # el.text = 'Pedigree Matrix [reliab, complet, tempCorr, geogCorr, furtherTechCorr]: ('+','.join(ped)+')'
    

###############################################################################

def type_product(tree, el, *args):
    '''Set the type of the intermediate flow [product or waste]'''
    
    # Type of flow taken from the By-product classification
    if tree.find('//{http://www.EcoInvent.org/EcoSpold02}classification') is not None:
        for class_ in tree.findall('//{http://www.EcoInvent.org/EcoSpold02}classification'):
            value = class_.find('{http://www.EcoInvent.org/EcoSpold02}classificationSystem').text
            if class_.find('{http://www.EcoInvent.org/EcoSpold02}classificationValue') is not None and value == "By-product classification":
                type_ = class_.find('{http://www.EcoInvent.org/EcoSpold02}classificationValue').text
                if type_ == "Waste":
                    el.text = 'Waste flow'
                elif type_ in ("Recyclable", "allocatable product"):
                    el.text = 'Product flow'
    
    if el.text is None:
        
        # If there is no classification of the sort, use output and input values
        if tree.find('//{http://www.EcoInvent.org/EcoSpold02}outputGroup') is not None:
            if tree.find('//{http://www.EcoInvent.org/EcoSpold02}outputGroup').text == '0':
                el.text = 'Product flow'
            elif tree.find('//{http://www.EcoInvent.org/EcoSpold02}outputGroup').text in ('2','3'):
                el.text = 'Waste flow'
        else:
            el.text = 'Product flow'
            

###############################################################################

@memory
def flow_ref(ortree, tree, el, *args):
    '''Creates the reference to a flowDataSet'''
    
    el = args[0].findall('exchanges/exchange')[-1]
    
    #ref = sub(el2,'referenceToFlowDataSet','exchange',None)
    ref = ET.SubElement(el,'referenceToFlowDataSet')
    if args[1] is not None:
        do_reference(ref, 'flow data set', args[1], args[2])
    else:
        do_reference(ref, 'flow data set', tree.find('{http://www.EcoInvent.org/EcoSpold02}intermediateExchange').get('id'),
                     tree.find('//{http://www.EcoInvent.org/EcoSpold02}name').text)
        

###############################################################################
        
def elementary_flow_info(tree, el, *args):
    '''Does elementary exchange conversion and does its ID check using a mapping file with Ecospold2 ids -> ILCD ids'''
    
    # Creates basic information in the elementary flow
    _ = sub(args[0], 'name','flowInformation/dataSetInformation',None)
    baseName = sub(args[0], 'baseName','flowInformation/dataSetInformation/name',None)
    el.text = None
    
    # Opens mapping with elementary flows ids from Ecospold2 to ILCD
    path_ = os.path.abspath(os.path.dirname(__file__))
    pathMP = os.path.join(path_, "Mapping_files/Id_elementary_exchanges.csv")
    with open(pathMP) as elem_csv_unit:
        elem_r = csv.reader(elem_csv_unit, delimiter = ',')
        
        # Finds ID correspondence on file
        for row in elem_r:
            u_id = tree.find('/').get('elementaryExchangeId')
            if row[0] == u_id:
                
                el.text = row[1]
                baseName.text = row[2]
                
                if row[3] != '':
                    CASNumber = sub(args[0],'CASNumber', 'flowInformation/dataSetInformation', None)
                    CASNumber.text = row[3]
                    
                if row[4] != '':
                    synonyms = sub(args[0],'{http://lca.jrc.it/ILCD/Common}synonyms', 'flowInformation/dataSetInformation', None)
                    synonyms.text = row[4]
                break
            
        # If there is no correspondence, set Ecospold2 elementary exchange ID as ILCD ID
        if el.text == None:
            el.text = tree.find('/').get('elementaryExchangeId')
            
            # Set additional info if ID is not found
            baseName.text = texts(tree,str_(['name']))
            if tree.find('//{http://www.EcoInvent.org/EcoSpold02}synonym') is not None:
                synonyms = sub(args[0],'{http://lca.jrc.it/ILCD/Common}synonyms', 'flowInformation/dataSetInformation', None)
                synonyms.text = texts(tree,str_(['synonym']))
            if tree.find('//{http://www.EcoInvent.org/EcoSpold02}casNumber') is not None:
                CASNumber = sub(args[0],'CASNumber', 'flowInformation/dataSetInformation', None)
                CASNumber.text = texts(tree,str_(['casNumber']))
        
        # Create flowDataSet of elementary flow
        flow_ref(0,0,0,args[1],el.text, baseName.text)
        

###############################################################################

def elem_f_property(tree, el, *args):
    '''Gets specific convertion information to create flowPropertyDataSet of elementary flows'''
            
    # If elementary flow have a specific multiplication factor when converted from ecospold2 to ILCD due to nomenclature
    #   it creates two properties (one for the Ecospold original property and other for the correspondent ILCD one)
    if tree.find('/').get('elementaryExchangeId') in factor_elem_flow.keys():
        factor = factor_elem_flow[tree.find('/').get('elementaryExchangeId')]
        f_property(tree, el, args[0], args[1], ['0', str(factor[0])], factor[1])
        new_f = sub(args[0], 'flowProperty', 'flowProperties', None)
        f_property(tree, new_f, args[0], args[1], ['1', '1.0'])
        
    # Else send call to create flowPropertyDataSet with basic information
    else:
        f_property(tree, el, args[0], args[1], ['0', '1.0'])
            

###############################################################################
            
def compartment(tree, el, *args):
    '''Compartment conversion using mapping file'''
    
    el.set('name', "ElemFlowEcoinvent")
    el.set('categories', "../flowCategories.xml")
    
    # Create subelements of compartment
    cat = ['']*3
    for i in range(3):
        cat[i] = sub(args[0], '{http://lca.jrc.it/ILCD/Common}category', 'flowInformation/dataSetInformation/classificationInformation/{http://lca.jrc.it/ILCD/Common}elementaryFlowCategorization', {'level':str(i)})
    
    # Find correspondence of compartment
    path_ = os.path.abspath(os.path.dirname(__file__))
    pathMP = os.path.join(path_, "Mapping_files/compartment_w.csv")
    with open(pathMP, 'r') as comp_csv:
        comp_reader = csv.reader(comp_csv, delimiter = ';')
        for row in comp_reader:
            if row[0] == tree.find('//{http://www.EcoInvent.org/EcoSpold02}compartment').get('subcompartmentId'):
                cat[0].text = 'Elementary flows'
                cat[1].text = row[2]
                cat[2].text = row[1]
                break


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
from shutil import copy
from uuid import uuid4
from time import strptime

from additional_files import create_contact, create_source

from conversion_caller import save_dir


###############################################################################
##########################***SIMPLE FUNCTIONS***###############################
###############################################################################

def zipdir(path, ziph):
    '''Makes a directory into zip file'''
    
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))
            

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

def do_uncertainty(tree, par, mean_v, bool_ = 0, path = '//{http://www.EcoInvent.org/EcoSpold02}uncertainty', mult = 1):
    '''Uncertainty calculation for any variable'''
    
    if tree.find(path) is not None:
        
        # Checks if variable gets a value or an amount as field name
        if bool_:
            min_a = ET.SubElement(par, 'minimumAmount')
            max_a = ET.SubElement(par, 'maximumAmount')
        else:
            min_a = ET.SubElement(par, 'minimumValue')
            max_a = ET.SubElement(par, 'maximumValue')
        
        # Sets uncertainty distribution name
        unc_type = ET.SubElement(par, 'uncertaintyDistributionType')
        unc_type.text = tree.find(path)[0].tag.split('}')[1]
            
        # Does uncertainty calculations depending on the type of uncertainty attributed to the flow
        if unc_type.text == 'lognormal':
            unc_type.text = 'log-normal'
            std95 = ET.SubElement(par, 'relativeStandardDeviation95In')
            std95.text = str(exp((float(tree.find(path)[0].attrib['varianceWithPedigreeUncertainty'])*(mult)**(1/2))**(1/2)))
            min_a.text = str(float(mean_v)/float(std95.text))
            max_a.text = str(float(mean_v)*float(std95.text))
        elif unc_type.text == 'normal':
            std95 = ET.SubElement(par, 'relativeStandardDeviation95In')
            std95.text = str((float(tree.find(path)[0].attrib['varianceWithPedigreeUncertainty'])*(mult)**(1/2))**(1/2))
            min_a.text = str(float(mean_v)-float(std95.text))
            max_a.text = str(float(mean_v)+float(std95.text))
        elif unc_type.text in ('normal', 'triangular'):
            min_a.text = tree.find(path)[0].attrib['minValue']
            max_a.text = tree.find(path)[0].attrib['maxValue']
        else:
            comment = ET.SubElement(par, 'comment',{"{http://www.w3.org/XML/1998/namespace}lang":'en'})
            comment.text = 'Uncertainty not supported (Beta, Gamma or Binomial) or Undefined.'
        
        # Checks if there is any comment on the uncertainty
        if texts(tree, path+'/{http://www.EcoInvent.org/EcoSpold02}comment'):
            if 'comment' in locals():
                comment.text = comment.text + '\n' + tree.find(path+'/{http://www.EcoInvent.org/EcoSpold02}comment').text
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
    
    # Create class subelements under classification
    clas0 = ET.SubElement(classification, '{http://lca.jrc.it/ILCD/Common}class')
    clas0.set('level','0')
    clas1 = ET.SubElement(classification, '{http://lca.jrc.it/ILCD/Common}class')
    clas1.set('level','1')
    clas2 = ET.SubElement(classification, '{http://lca.jrc.it/ILCD/Common}class')
    clas2.set('level','2')
    clas3 = ET.SubElement(classification, '{http://lca.jrc.it/ILCD/Common}class')
    clas3.set('level','3')
    
    t = 2
    lvl = ['']*4
    
    # Find the correspondence of classification in ISIC.txt file
    with open("./Mapping files/ISIC.txt",'r') as f:
        div_text = text.split(':')
        for line in f:
            if div_text[0][:-t] == line.split(':::')[0]:
                lvl[t] = div_text[0][:-t] + ':' + line.split(':::')[1]
                t = t-1
            elif div_text[0] == line.split(':::')[0]:
                lvl[3] = line.split(':::')[2].rstrip('\n')
                lvl[0] = div_text[0] + ':' + line.split(':::')[1]
                break
            
    # Set class' text
    clas0.text,clas1.text,clas2.text,clas3.text = lvl[3],lvl[2],lvl[1],lvl[0]
    
    
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
                        flow_id.append((flow.get('intermediateExchangeId'), count-a))
            
            count +=1
            a = 0
        
        # Allocation list preparation for main mapping application
        al = list(map(lambda x: x/sum(al),al))
        alloc = tuple(zip(flow_id, al))
        
        return alloc
    

###############################################################################

def flow_set_and_internal_ID(i_tree, outputRef, countNonReference, referencePassed):
    '''Creates flow element and sets an internal ID as attribute'''
    
    # Output case
    if outputRef is not None:
        dir_ = 'Output'
        if outputRef.text == '0':
            if referencePassed:
                exchange = sub(i_tree,'exchange','exchanges',{'dataSetInternalID':str(countNonReference)})
                countNonReference += 1
            else:
                exchange = sub(i_tree,'exchange','exchanges',{'dataSetInternalID':'0'})
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
        
    return exchange, countNonReference, referencePassed


###############################################################################

def flow_allocation_info(al, exc):
    '''Creates allocation subelements inside the flow'''
    
    for el in al:  
        element_al = ET.SubElement(exc, 'allocation')
        element_al.set('internalReferenceToCoProduct', str(el[0][1]))
        element_al.set('allocatedFraction', str(el[1]*100))


###############################################################################

def f_property(tree, el, *args, **kwargs):
    '''Creates datasets for a flow property and its units'''
    
    # Creates folders if necessary
    create_folder(save_dir+'/flowproperties')
    create_folder(save_dir+'/unitgroups')
    
    # Sets the ID of the flowPropertyDataSet
    el.set('dataSetInternalID', args[1][0])
    
    # Check if the property is a special property that is not on ILCD default properties
    if kwargs.get('special_property'):
        
        # Set a reference to property
        ref = ET.SubElement(el, 'referenceToFlowPropertyDataSet')
        mv = ET.SubElement(el, 'meanValue')
        do_reference(ref, 'flow property data set', kwargs.get('uuid'), kwargs.get('name'))
        
        # Copies the flowPropertyDataSet and unitDataSet from the repository to the zip folder
        mv.text = kwargs.get('amount')
        copy('./ILCD flowProperties and units/flow_properties/'+kwargs.get('uuid')+'.xml', save_dir+'/flowproperties')
        if kwargs.get('unit_id'):
            copy('./ILCD flowProperties and units/unit_groups/'+kwargs.get('unit_id')+'.xml', save_dir+'/unitgroups')
            
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
        if len(args) == 2:
            args = list(args)
            args.append(tree.find('//{http://www.EcoInvent.org/EcoSpold02}unitName').text)
        r = unit_conv(args[2])
        
        # Set reference subelement
        do_reference(ref, 'flow property data set', r[0], r[1])
        
        # Set correct mean value to flowProperties
        mv.text = args[1][-1]
        
        # Copies the flowPropertyDataSet and unitDataSet from the repository to the zip folder
        copy('./ILCD flowProperties and units/flow_properties/'+r[0]+'.xml', save_dir+'/flowproperties')
        copy('./ILCD flowProperties and units/unit_groups/'+r[3]+'.xml', save_dir+'/unitgroups')


###############################################################################

def unit_conv(name, single = False):
    '''Converts flow property units and do single unit conversion for ILCD standards'''
    
    # Single unit conversion
    if single:
        with open('./Mapping files/conv_unit.csv', 'r') as conv_unit:
            conv_r = csv.reader(conv_unit, delimiter = ',')
            for row in conv_r:
                if name[1] == row[1] and name[2] == row[2]:
                    return str(float(name[0])*float(row[0]))
            else:
                return None
    # Flow property unit conversion
    else:
        with open('./Mapping files/property_to_unit.csv', 'r') as conv_unit:
            conv_r = csv.reader(conv_unit, delimiter = ',')
            for row in conv_r:
                if name in [row[0]]+row[4:]:
                    uuid = row[1]
                    name = row[2]
                    conv = float(row[3]) if row[3] != '' else 1
                    unit_id = row[4]
                    return uuid, name, conv, unit_id


###############################################################################

def var(mult, o_t, comm, o_tree, flow, exc, text, amount, is_math = 0, is_ref = 1, path = '//{http://www.EcoInvent.org/EcoSpold02}uncertainty'):
    '''
    Multifunction for all calculation of any variable (parameters). Has the following:
        
        1. 
    
    Inputs:
        mult:   convertion factor (multiplyier) of the unit for uncertainty purposes
        o_t:    deepcopy of original Ecospold2 tree
        comm:   commentary element of variable if any
        o_tree: original ILCD tree (it is a copy of the main ILCD tree)
        flow:   reference to exchange element of Ecospold2
        exc:    reference to flow (exchange) element of ILCD
        text:   initial text for parameter name if any
        amount: quantitative amount of the flow
        
        is_math:    if the variable is a calculation (equation)
        is_ref:     if the variable is the reference variable for the flow amount
        path:       element path of uncertainty, serves as an trigger for uncertainty calculations
        
    Output:
        id_     reference id_ for the list of ids of the main conversion file
    '''
    
    # Creation of the subelement variableParameter under mathematicalRelations
    math_r = o_tree.find('//mathematicalRelations')
    var = ET.SubElement(math_r,'variableParameter')
    
    # Set text (name) of variableParameter
    if re.search('for_$',text):
        if flow.get('elementaryExchangeId'):
            id_ = text + flow.get('elementaryExchangeId').replace('-','_')
        elif flow.get('intermediateExchangeId'):
            id_ = text + flow.get('intermediateExchangeId').replace('-','_')
        elif flow.get('parameterId'):
            id_ = text + flow.get('parameterId').replace('-','_')
    else:
        id_ = text
    var.set('name', id_)
    
    # Mean amount of the variableParameter
    mean_v = ET.SubElement(var,'meanValue')
    mean_v.text = amount
    
    # Mathematical relation equation text and corrections 
    #   (if takes a reference, its a unit conversion, a % or float with ',' as decimal separator)
    if is_math:
        is_math = is_math.rstrip()
        # Unit convertion correction
        if re.search('UnitConversion', is_math):
            for elem in re.findall("UnitConversion\(([\w -.',]+?)\)", is_math):
                elem_ = elem.replace("'", '').split(', ')
                elem_[0] = elem_[0].replace(',','.')
                is_math = sub('UnitConversion\('+elem+'\)',unit_conv(elem_, True),is_math)
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
                        is_math = sub("Ref\('"+elem+"'\)", value, is_math)
        # Percentage correction
        if re.search('%', is_math):
            is_math = sub('%','/100',is_math)
        # Float with ',' as decimal separator correction
        if re.search('[0-9]+,[0-9]+', is_math):
            is_math = sub(',', '.', is_math)
            
        # Set equation text inside 'formula' subelement
        form_v = ET.SubElement(var,'formula')
        form_v.text = is_math
        
    # If the variable represents the quantitative value of the flow 
    if is_ref:
        ref_var = ET.SubElement(exc,'referenceToVariable')
        ref_var.text = id_
    
    # If its necessary to set the uncertainty of the variable
    if path:
        do_uncertainty(root_(flow), var, amount, 0, path, mult)
        
    # Set comment on the variableParameter
    if comm != '':
        if flow.find(comm) is not None:
            comment = ET.SubElement(var, 'comment')
            comment.text = texts(flow, comm)
    
    return id_


###############################################################################
        
def set_parameters_and_variables(o_t, f_tree, o_tree, flow, exc, par_bool=1):
    '''
    Multifunction for flow subelements and attributes, mainly for calculations
    and amount setting. Has the following ordered functionalities:
        
        1. Convertion of units if necessary
        2. Check for variables and equations attributed to the flow
        3. Check the variables and equations attributed to the flow's production volume
        4. Check the variables and equations attributed to the flow's parameters 
    '''
    
    # Zero value has to be in the original id_ set
    id_ = set(['0'])
    
    # Get conversion factors for units
    if flow.find('{http://www.EcoInvent.org/EcoSpold02}unitName') is not None:
        r = unit_conv(flow.find('{http://www.EcoInvent.org/EcoSpold02}unitName').text)
    else:
        r = None
    
    # Get amount of flow (with unit correction using conversion factors)
    if r:
        if par_bool:
            exc.find('meanAmount').text = str(float(exc.find('meanAmount').text) * r[2])
            exc.find('resultingAmount').text = str(float(exc.find('resultingAmount').text) * r[2])
        amount = str(float(flow.get('amount')) * r[2])
    else:
        amount = flow.get('amount')
    
    # Check for variables attributed to the exchange and if they're calculated
    if flow.get('variableName') is not None:
        
        # Unit convertion check
        if not r:
            r = [0,0,1]
            
        # Checks for equations 
        if flow.get('isCalculatedAmount'):
            if par_bool:
                exc.find('meanAmount').text = '1.0'
                id_.add(var(r[2], o_t, '', o_tree, flow, exc, flow.get('variableName'), amount, flow.get('mathematicalRelation')))
            else:
                id_.add(var(1, o_t, '{http://www.EcoInvent.org/EcoSpold02}comment', o_tree, flow, exc, flow.get('variableName'), amount, flow.get('mathematicalRelation'), 0))
        else:
            if par_bool:
                exc.find('meanAmount').text = '1.0'
                id_.add(var(r[2], o_t, '', o_tree, flow, exc, flow.get('variableName'), amount))
            else:
                id_.add(var(1, o_t, '{http://www.EcoInvent.org/EcoSpold02}comment', o_tree, flow, exc, flow.get('variableName'), amount, 0, 0))
    
    # Check for equations used to calculate something in the flow
    elif flow.get('isCalculatedAmount') == 'true':
        
        # Unit convertion check
        if not r:
            r = [0,0,1]
        
        # Checks if the variable is a parameter (parameters get its specific set of ifs at the end of this function)
        if par_bool:
            exc.find('meanAmount').text = '1.0'
            id_.add(var(r[2], o_t, '', o_tree, flow, exc, 'Math_Rel_for_', amount, flow.get('mathematicalRelation')))
        else:
            id_.add(var(1, o_t, '{http://www.EcoInvent.org/EcoSpold02}comment', o_tree, flow, exc, 'Math_Rel_[parameter]_for_', amount, flow.get('mathematicalRelation'), 0))
    
    # Check for production volume values and their equations if any
    if flow.get('productionVolumeAmount') is not None:
        
        # Unit convertion check
        if r:
            pV_amount = str(float(flow.get('productionVolumeAmount')) * r[2])
        else:
            pV_amount = flow.get('productionVolumeAmount')
        
        # Set elements representing prodution volume on ILCD
        annual_s = ET.SubElement(o_tree.find('//dataSourcesTreatmentAndRepresentativeness'),'annualSupplyOrProductionVolume')
        annual_s.text = 'Annual Production of ' + flow.find("{http://www.EcoInvent.org/EcoSpold02}name").text +\
                        ' is ' + flow.get('productionVolumeAmount') + ' ' + flow.find('{http://www.EcoInvent.org/EcoSpold02}unitName').text

        # Set variables on mathematicalRelations relative to productionVolume value or calculations
        if flow.get('productionVolumeVariableName') is not None:
            if flow.get('productionVolumeMathematicalRelation') is not None:
                id_.add(var(1, o_t, '{http://www.EcoInvent.org/EcoSpold02}productionVolumeComment', o_tree, flow, exc, flow.get('productionVolumeVariableName'), pV_amount,flow.get('productionVolumeMathematicalRelation'),0,'//{http://www.EcoInvent.org/EcoSpold02}productionVolumeUncertainty'))
            else:
                id_.add(var(1, o_t, '{http://www.EcoInvent.org/EcoSpold02}productionVolumeComment', o_tree, flow, exc, flow.get('productionVolumeVariableName'), pV_amount,0,0,'//{http://www.EcoInvent.org/EcoSpold02}productionVolumeUncertainty'))
    
        elif flow.get('productionVolumeMathematicalRelation') is not None:
            id_.add(var(1, o_t, '{http://www.EcoInvent.org/EcoSpold02}productionVolumeComment', o_tree, flow, exc, 'Math_Rel_[product volume]_for_', pV_amount,flow.get('productionVolumeMathematicalRelation'),0,'//{http://www.EcoInvent.org/EcoSpold02}productionVolumeUncertainty'))

    # Check for flow properties, it's values and equations if any. If it's an special flow property, creates a flowPropertyDataSet for it
    for prop in flow.iterfind('{http://www.EcoInvent.org/EcoSpold02}property'):
        
        # Unit convertion check
        if prop.find('{http://www.EcoInvent.org/EcoSpold02}unitName') is not None:
            p = unit_conv(prop.find('{http://www.EcoInvent.org/EcoSpold02}unitName').text)
        else:
            p = None
        if p:
            prop_amount = str(float(prop.get('amount')) * p[2])
        else:
            prop_amount = prop.get('amount')
            
        # Set variables on mathematicalRelations relative to flow parameters' value or calculations
        if prop.get('variableName'):
            if prop.get('isCalculatedAmount') == 'true':
                id_.add(var(1, o_t, '{http://www.EcoInvent.org/EcoSpold02}comment', o_tree, prop, exc, prop.get('variableName'), prop_amount, prop.get('mathematicalRelation'),0,0))
            else:
                id_.add(var(1, o_t, '{http://www.EcoInvent.org/EcoSpold02}comment', o_tree, prop, exc, prop.get('variableName'), prop_amount,0,0,0))
        # For every new property in all the flows, creates a new flowPropertyDataSet for it and its specific unitDataSets
        else:
            if prop.find('{http://www.EcoInvent.org/EcoSpold02}name').text in ('water content', 'carbon content, non-fossil', 'carbon content, fossil', 'water in wet mass', 'wet mass', 'dry mass'):
                el = ET.SubElement(f_tree.find('//flowProperties'), 'flowProperty')
                f_property(f_tree, el, f_tree, [str(len(f_tree.findall('//flowProperty'))-1), ''], special_property = 1, uuid = prop.get('propertyId'), amount = prop.get('amount'), name = prop.find('{http://www.EcoInvent.org/EcoSpold02}name').text)
          
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
        _ = sub(args[0], 'review', args[1], {})
        
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
        create_contact(ET.ElementTree(ET.Element("contactDataSet", version = '1.1', nsmap = {None: "http://lca.jrc.it/ILCD/Contact",
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
            ref = sub(args[0], 'referenceToExternalDocument','processInformation/dataSetInformation',None)
            if re.search('[A-z0-9]{8}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{12}', el.text):
                ref_uuid = re.search('[A-z0-9]{8}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{12}', el.text).group()
            else:
                ref_uuid = str(uuid4())
            do_reference(ref, 'source data set', ref_uuid, 'dataSetIcon')
            
            # Create sourceDataSet for the image url
            create_source(ET.ElementTree(ET.Element("sourceDataSet", version = '1.1', nsmap = {None: "http://lca.jrc.it/ILCD/Source",
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
            create_source(ET.ElementTree(ET.Element("sourceDataSet", version = '1.1', nsmap = {None: "http://lca.jrc.it/ILCD/Source",
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
    if el.getparent()[-2].tag == 'generalComment':
        gc1 = el.getparent()[-2]
        gc1.text = 'Pedigree: ('+','.join(ped)+'). ' + gc1.text if gc1.text is not None else ''
    
    el.text = 'Pedigree Matrix [reliab, complet, tempCorr, geogCorr, furtherTechCorr]: ('+','.join(ped)+')'
    

###############################################################################

def type_product(tree, el, *args):
    '''Set the type of the intermediate flow [product or waste]'''
    
    if tree.find('//{http://www.EcoInvent.org/EcoSpold02}outputGroup') is not None:
        if tree.find('//{http://www.EcoInvent.org/EcoSpold02}outputGroup').text == '0':
            el.text = 'Product flow'
        elif tree.find('//{http://www.EcoInvent.org/EcoSpold02}outputGroup').text in ('2','3'):
            el.text = 'Waste flow'
    else:
        el.text = 'Product flow'
        

###############################################################################
        
def flow_ref(tree, el, *args):
    '''Creates the reference to a flowDataSet'''
    
    el = args[0].find('exchanges')[-1]
    ref = ET.SubElement(el,'referenceToFlowDataSet')
    if args[1] is not None:
        do_reference(ref, 'flow data set', args[1], args[2])
    else:
        do_reference(ref, 'flow data set', tree.find('{http://www.EcoInvent.org/EcoSpold02}intermediateExchange').get('intermediateExchangeId'),
                     tree.find('//{http://www.EcoInvent.org/EcoSpold02}name').text)
        

###############################################################################
        
def elementary_flow_info(tree, el, *args):
    '''Does elementary exchange conversion and does its ID check using a mapping file with Ecospold2 ids -> ILCD ids'''
    
    # Creates basic information in the elementary flow
    _ = sub(args[0], 'name','flowInformation/dataSetInformation',None)
    baseName = sub(args[0], 'baseName','flowInformation/dataSetInformation/name',None)
    el.text = None
    
    # Opens mapping with elementary flows ids from Ecospold2 to ILCD
    with open('./Mapping files/Id_elementary_exchanges.csv') as elem_csv_unit:
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
                    synonyms = sub(args[0],'synonyms', 'flowInformation/dataSetInformation', None)
                    synonyms.text = row[4]
                break
            
        # If there is no correspondence, set Ecospold2 elementary exchange ID as ILCD ID
        if el.text == None:
            el.text = tree.find('/').get('elementaryExchangeId')
            
            # Set additional info if ID is not found
            baseName.text = texts(tree,str_(['name']))
            if tree.find('//{http://www.EcoInvent.org/EcoSpold02}synonym') is not None:
                synonyms = sub(args[0],'synonyms', 'flowInformation/dataSetInformation', None)
                synonyms.text = texts(tree,str_(['synonym']))
            if tree.find('//{http://www.EcoInvent.org/EcoSpold02}casNumber') is not None:
                CASNumber = sub(args[0],'CASNumber', 'flowInformation/dataSetInformation', None)
                CASNumber.text = texts(tree,str_(['casNumber']))
        
        # Create flowDataSet of elementary flow
        flow_ref(0,0,args[1],el.text, baseName.text)
        

###############################################################################

def elem_f_property(tree, el, *args):
    '''Gets specific convertion information to create flowPropertyDataSet of elementary flows'''
    
    # Checks if elementary flow has an specific convertion of values
    with open('./Mapping files/factor_c.csv', 'r') as conv_fac:
        conv_r = csv.reader(conv_fac, delimiter = ',')
        
        # Checks if id is on the list of specific convertion factors and send call to create flowPropertyDataSet
        for row in conv_r:
            if row[0] == tree.find('/').get('elementaryExchangeId'):
                
                f_property(tree, el, args[0], ['0', row[1]], row[2])
                new_f = sub(args[0], 'flowProperty', 'flowProperties', None)
                f_property(tree, new_f, args[0], ['1', '1.0'])
                break
        
        # Else send call to create flowPropertyDataSet with basic information
        else:
            f_property(tree, el, args[0], ['0', '1.0'])
            

###############################################################################
            
def compartment(tree, el, *args):
    '''Compartment conversion using mapping file'''
    
    # Create subelements of compartment
    cat = ['']*3
    for i in range(3):
        cat[i] = sub(args[0], '{http://lca.jrc.it/ILCD/Common}category', 'flowInformation/dataSetInformation/classificationInformation/{http://lca.jrc.it/ILCD/Common}elementaryFlowCategorization', {'level':str(i)})
    
    # Find correspondence of compartment
    with open('./Mapping files/compartment_w.csv', 'r') as comp_csv:
        comp_reader = csv.reader(comp_csv, delimiter = ';')
        for row in comp_reader:
            if row[0] == tree.find('//{http://www.EcoInvent.org/EcoSpold02}compartment').get('subcompartmentId'):
                cat[0].text = 'Elementary flows'
                cat[1].text = row[2]
                cat[2].text = row[1]
                break


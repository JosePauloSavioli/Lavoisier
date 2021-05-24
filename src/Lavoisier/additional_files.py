#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 24 12:04:27 2021

This code creates sourceDataSets and contactDataSets for the ILCD zip file 

@author: jotape42p
"""

from lxml import etree as ET

from collection import do_reference, sub, create_folder

from conversion_caller import save_dir

# Initial global variables
c = "{http://lca.jrc.it/ILCD/Common}"
w = "{http://www.w3.org/XML/1998/namespace}lang"


###############################################################################

def memory(func):
    '''Wrapper with memory of ids created for duplicates check'''
    
    def c(*args):
        if args[2] not in t:
            t.add(args[2])
            memory.clear()
        if args[1] not in memory:
            memory.add(args[1])
            func(*args)
            
    t = set()
    memory = set()
    
    return c


###############################################################################

@memory
def create_contact(tree, *args):
    '''Creates a contactDataSet xml file'''
    
    # Create contactDataSet main subelements
    contactInformation = sub(tree, 'contactInformation', tree.getroot(), {}, 'contactDataSet')
    administrativeInformationCT = sub(tree, 'administrativeInformation', tree.getroot(), {}, 'contactDataSet')
    
    # Create contactInformation main subelements
    dataSetInformationCT = sub(tree, 'dataSetInformation', contactInformation, {}, 'contactDataSet')
    
    UUIDCT = sub(tree, c+'UUID', dataSetInformationCT, {}, 'contactDataSet')
    UUIDCT.text = args[0]
    
    NameCT = sub(tree, c+'name', dataSetInformationCT, {w:'en'}, 'contactDataSet')
    NameCT.text = args[2]
    
    if isinstance(args[-1], dict):
        if args[-1].get('active') != None:
            comment = sub(tree, 'contactDescriptionOrComment', dataSetInformationCT, {}, 'contactDataSet')
            comment.text = args[-1]['active']
        args = args[:-1]
        
    if len(args) == 4:
        emailCT = sub(tree, 'email', dataSetInformationCT, {}, 'contactDataSet')
        emailCT.text = args[3]
    

    # Create administrativeInformation/dataEntryBy main subelements
    dataEntryByCT = sub(tree, 'dataEntryBy', administrativeInformationCT, {}, 'contactDataSet')
    
    referenceToDataSetFormatCT = sub(tree, c+'referenceToDataSetFormat', dataEntryByCT, {}, 'contactDataSet')
    do_reference(referenceToDataSetFormatCT, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', 'ILCD Format')
    
    # Create administrativeInformation/publicationAndOwnership main subelements
    publicationAndOwnershipCT = sub(tree, 'publicationAndOwnership', administrativeInformationCT, {}, 'contactDataSet')
    
    dataSetVersionCT = sub(tree, c+'dataSetVersion', publicationAndOwnershipCT, {}, 'contactDataSet')
    dataSetVersionCT.text = "00.00.000"
    
    permanentDataSetURICT = sub(tree, c+'permanentDataSetURI', publicationAndOwnershipCT, {}, 'contactDataSet')
    permanentDataSetURICT.text = 'http://sicv.acv.ibict.br'
    
    # Create directory
    create_folder(save_dir+"/contacts")
    
    # Save contactDataSet file
    c_file = save_dir+"/contacts/" + args[0] + ".xml"
    with open(c_file, 'wb') as c_:
        c_.write(ET.tostring(tree, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))


###############################################################################

@memory
def create_source(tree, *args):
    '''Creates a sourceDataSet xml file'''

    # Create sourceDataSet main subelements
    sourceInformation = sub(tree, 'sourceInformation', tree.getroot(), {}, 'sourceDataSet')
    administrativeInformationSR = sub(tree, 'administrativeInformation', tree.getroot(), {}, 'sourceDataSet')
    
    # Create sourceInformation main subelements
    dataSetInformationSR = sub(tree, 'dataSetInformation', sourceInformation, {}, 'sourceDataSet')
    
    UUIDSR = sub(tree, c+'UUID', dataSetInformationSR, {}, 'sourceDataSet')
    UUIDSR.text = args[0]
    
    shortName = sub(tree, c+'shortName', dataSetInformationSR, {w:'en'}, 'sourceDataSet')
    shortName.text = args[2]
    
    # Create administrativeInformation/dataEntryBy main subelements (specific check if it's not the ILCD source file)
    if args[0] != "a97a0155-0234-4b87-b4ce-a45da52f2a40":
        dataEntryBySR = sub(tree, 'dataEntryBy', administrativeInformationSR, {}, 'sourceDataSet')
        referenceToDataSetFormatSR = sub(tree, c+'referenceToDataSetFormat', dataEntryBySR, {}, 'sourceDataSet')
        do_reference(referenceToDataSetFormatSR, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', 'ILCD Format')

    # Create administrativeInformation/publicationAndOwnership main subelements
    publicationAndOwnershipSR = sub(tree, 'publicationAndOwnership', administrativeInformationSR, {}, 'sourceDataSet')
    
    dataSetVersionSR = sub(tree, c+'dataSetVersion', publicationAndOwnershipSR, {}, 'sourceDataSet')
    dataSetVersionSR.text = "01.00.000"
    
    permanentDataSetURISR = sub(tree, c+'permanentDataSetURI', publicationAndOwnershipSR, {}, 'contactDataSet')
    if len(args) == 4:
        permanentDataSetURISR.text = args[3]
        
    # Create directory
    create_folder(save_dir+"/sources")
     
    # Save sourceDataSet file
    s_file = save_dir+"/sources/" + args[0] + ".xml"
    with open(s_file, 'wb') as s_:
        s_.write(ET.tostring(tree, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))


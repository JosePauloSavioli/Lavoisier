#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 24 12:04:27 2021

This code creates sourceDataSets and contactDataSets for the ILCD zip file 

@author: jotape42p
"""

from lxml import etree as ET

import Lavoisier.collection as collection

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
    contactInformation = collection.sub(tree, 'contactInformation', tree.getroot(), {}, 'contactDataSet')
    administrativeInformationCT = collection.sub(tree, 'administrativeInformation', tree.getroot(), {}, 'contactDataSet')
    
    # Create contactInformation main subelements
    dataSetInformationCT = collection.sub(tree, 'dataSetInformation', contactInformation, {}, 'contactDataSet')
    
    UUIDCT = collection.sub(tree, c+'UUID', dataSetInformationCT, {}, 'contactDataSet')
    UUIDCT.text = args[0]
    
    NameCT = collection.sub(tree, c+'name', dataSetInformationCT, {w:'en'}, 'contactDataSet')
    NameCT.text = args[2]
    
    if isinstance(args[-1], dict):
        if args[-1].get('active') != None:
            comment = collection.sub(tree, 'contactDescriptionOrComment', dataSetInformationCT, {}, 'contactDataSet')
            comment.text = args[-1]['active']
        args = args[:-1]
        
    if len(args) == 4:
        emailCT = collection.sub(tree, 'email', dataSetInformationCT, {}, 'contactDataSet')
        emailCT.text = args[3]
    

    # Create administrativeInformation/dataEntryBy main subelements
    dataEntryByCT = collection.sub(tree, 'dataEntryBy', administrativeInformationCT, {}, 'contactDataSet')
    
    referenceToDataSetFormatCT = collection.sub(tree, c+'referenceToDataSetFormat', dataEntryByCT, {}, 'contactDataSet')
    collection.do_reference(referenceToDataSetFormatCT, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', 'ILCD Format')
    
    # Create administrativeInformation/publicationAndOwnership main subelements
    publicationAndOwnershipCT = collection.sub(tree, 'publicationAndOwnership', administrativeInformationCT, {}, 'contactDataSet')
    
    dataSetVersionCT = collection.sub(tree, c+'dataSetVersion', publicationAndOwnershipCT, {}, 'contactDataSet')
    dataSetVersionCT.text = "00.00.000"
    
    permanentDataSetURICT = collection.sub(tree, c+'permanentDataSetURI', publicationAndOwnershipCT, {}, 'contactDataSet')
    permanentDataSetURICT.text = 'http://sicv.acv.ibict.br'
    
    from Lavoisier.conversion_caller import save_dir
    
    # Create directory
    collection.create_folder(save_dir+"/contacts")
    
    # Save contactDataSet file
    c_file = save_dir+"/contacts/" + args[0] + ".xml"
    with open(c_file, 'wb') as c_:
        c_.write(ET.tostring(tree, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))


###############################################################################

@memory
def create_source(tree, *args):
    '''Creates a sourceDataSet xml file'''

    # Create sourceDataSet main subelements
    sourceInformation = collection.sub(tree, 'sourceInformation', tree.getroot(), {}, 'sourceDataSet')
    administrativeInformationSR = collection.sub(tree, 'administrativeInformation', tree.getroot(), {}, 'sourceDataSet')
    
    # Create sourceInformation main subelements
    dataSetInformationSR = collection.sub(tree, 'dataSetInformation', sourceInformation, {}, 'sourceDataSet')
    
    UUIDSR = collection.sub(tree, c+'UUID', dataSetInformationSR, {}, 'sourceDataSet')
    UUIDSR.text = args[0]
    
    shortName = collection.sub(tree, c+'shortName', dataSetInformationSR, {w:'en'}, 'sourceDataSet')
    shortName.text = args[2]
    
    # Create administrativeInformation/dataEntryBy main subelements (specific check if it's not the ILCD source file)
    if args[0] != "a97a0155-0234-4b87-b4ce-a45da52f2a40":
        dataEntryBySR = collection.sub(tree, 'dataEntryBy', administrativeInformationSR, {}, 'sourceDataSet')
        referenceToDataSetFormatSR = collection.sub(tree, c+'referenceToDataSetFormat', dataEntryBySR, {}, 'sourceDataSet')
        collection.do_reference(referenceToDataSetFormatSR, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', 'ILCD Format')

    # Create administrativeInformation/publicationAndOwnership main subelements
    publicationAndOwnershipSR = collection.sub(tree, 'publicationAndOwnership', administrativeInformationSR, {}, 'sourceDataSet')
    
    dataSetVersionSR = collection.sub(tree, c+'dataSetVersion', publicationAndOwnershipSR, {}, 'sourceDataSet')
    dataSetVersionSR.text = "01.00.000"
    
    permanentDataSetURISR = collection.sub(tree, c+'permanentDataSetURI', publicationAndOwnershipSR, {}, 'contactDataSet')
    if len(args) == 4:
        permanentDataSetURISR.text = args[3]
        
    from Lavoisier.conversion_caller import save_dir
    
    # Create directory
    collection.create_folder(save_dir+"/sources")
     
    # Save sourceDataSet file
    s_file = save_dir+"/sources/" + args[0] + ".xml"
    with open(s_file, 'wb') as s_:
        s_.write(ET.tostring(tree, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))


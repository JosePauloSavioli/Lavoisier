#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 24 12:04:27 2021

This code creates sourceDataSets and contactDataSets for the ILCD zip file 

@author: jotape42p
"""

from lxml import etree as ET

import Lavoisier.collection as collection
import Lavoisier.units as ut

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

def memory_2(func):
    '''Wrapper with memory of ids created for duplicates check'''
    
    def c(*args):
        if args[0] not in t:
            t.add(args[0])
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
    
    if len(args) >= 4:
        if not isinstance(args[3], dict):
            emailCT = collection.sub(tree, 'email', dataSetInformationCT, {}, 'contactDataSet')
            emailCT.text = args[3]
        
    if isinstance(args[-1], dict):
        if args[-1].get('active') != None:
            comment = collection.sub(tree, 'contactDescriptionOrComment', dataSetInformationCT, {}, 'contactDataSet')
            comment.text = args[-1]['active']
        args = args[:-1]

    # Create administrativeInformation/dataEntryBy main subelements
    dataEntryByCT = collection.sub(tree, 'dataEntryBy', administrativeInformationCT, {}, 'contactDataSet')
    
    referenceToDataSetFormatCT = collection.sub(tree, c+'referenceToDataSetFormat', dataEntryByCT, {}, 'contactDataSet')
    collection.do_reference(referenceToDataSetFormatCT, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', 'ILCD Format')
    
    # Create administrativeInformation/publicationAndOwnership main subelements
    publicationAndOwnershipCT = collection.sub(tree, 'publicationAndOwnership', administrativeInformationCT, {}, 'contactDataSet')
    
    dataSetVersionCT = collection.sub(tree, c+'dataSetVersion', publicationAndOwnershipCT, {}, 'contactDataSet')
    dataSetVersionCT.text = "01.00.000"
    
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
    
    permanentDataSetURISR = collection.sub(tree, c+'permanentDataSetURI', publicationAndOwnershipSR, {}, 'sourceDataSet')
    if len(args) == 4:
        permanentDataSetURISR.text = args[3]
        
    from Lavoisier.conversion_caller import save_dir
    
    # Create directory
    collection.create_folder(save_dir+"/sources")
     
    # Save sourceDataSet file
    s_file = save_dir+"/sources/" + args[0] + ".xml"
    with open(s_file, 'wb') as s_:
        s_.write(ET.tostring(tree, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))


###############################################################################

@memory_2
def create_f_prop(ilcd_tree, id_, name, unit_id, unit_name):
    '''Creates a flowPropertyDataSet xml file'''
    
    # Create flowPropertyDataSet root element and tree
    tree = ET.ElementTree(ET.Element("flowPropertyDataSet", version = '1.1', nsmap = {None: "http://lca.jrc.it/ILCD/FlowProperty",
                                                                                       'c': "http://lca.jrc.it/ILCD/Common"}))
    
    # Create flowPropertyDataSet main subelements
    fpInformation = collection.sub(tree, 'flowPropertiesInformation', tree.getroot(), {}, 'flowPropertyDataSet')
    
    # Create flowPropertyInformation main subelements
    dataSetInformationCT = collection.sub(tree, 'dataSetInformation', fpInformation, {}, 'flowPropertyDataSet')
    
    UUIDCT = collection.sub(tree, c+'UUID', dataSetInformationCT, {}, 'flowPropertyDataSet')
    UUIDCT.text = id_
    
    NameCT = collection.sub(tree, c+'name', dataSetInformationCT, {w:'en'}, 'flowPropertyDataSet')
    NameCT.text = name
    
    quantitativeReference = collection.sub(tree, 'quantitativeReference', fpInformation, {}, 'flowPropertyDataSet')
        
    referenceToReferenceUnitGroup = collection.sub(tree, 'referenceToReferenceUnitGroup', quantitativeReference, {}, 'flowPropertyDataSet')
    collection.do_reference(referenceToReferenceUnitGroup, 'unit group data set', unit_id, "Units of "+unit_name)

    # Create administrativeInformation main subelements
    administrativeInformationCT = collection.sub(tree, 'administrativeInformation', tree.getroot(), {}, 'flowPropertyDataSet')
    
    dataEntryByCT = collection.sub(tree, 'dataEntryBy', administrativeInformationCT, {}, 'flowPropertyDataSet')
    
    referenceToDataSetFormatCT = collection.sub(tree, c+'referenceToDataSetFormat', dataEntryByCT, {}, 'flowPropertyDataSet')
    collection.do_reference(referenceToDataSetFormatCT, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', 'ILCD Format')
    
    publicationAndOwnershipCT = collection.sub(tree, 'publicationAndOwnership', administrativeInformationCT, {}, 'flowPropertyDataSet')
    
    dataSetVersionCT = collection.sub(tree, c+'dataSetVersion', publicationAndOwnershipCT, {}, 'flowPropertyDataSet')
    dataSetVersionCT.text = "01.00.000"
    
    permanentDataSetURICT = collection.sub(tree, c+'permanentDataSetURI', publicationAndOwnershipCT, {}, 'flowPropertyDataSet')
    permanentDataSetURICT.text = 'http://openlca.org/ilcd/resource/flowproperties/'+id_
    
    from Lavoisier.conversion_caller import save_dir
    
    # Create directory
    collection.create_folder(save_dir+"/flowproperties")
    
    # Save flowPropertyDataSet file
    c_file = save_dir+"/flowproperties/" + id_ + ".xml"
    with open(c_file, 'wb') as c_:
        c_.write(ET.tostring(tree, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))


###############################################################################

@memory_2
def create_unit_group(ilcd_tree, id_, name, unit_group, main_unit):
    '''Creates a unitGroupDataSet xml file'''
    
    # Create unitGroupDataSet root element and tree
    tree = ET.ElementTree(ET.Element("unitGroupDataSet", version = '1.1', nsmap = {None: "http://lca.jrc.it/ILCD/UnitGroup",
                                                                                       'c': "http://lca.jrc.it/ILCD/Common"}))
    
    # Create unitGroupDataSet main subelements
    ugInformation = collection.sub(tree, 'unitGroupInformation', tree.getroot(), {}, 'unitGroupDataSet')
    
    # Create unitGroupInformation main subelements
    dataSetInformationCT = collection.sub(tree, 'dataSetInformation', ugInformation, {}, 'unitGroupDataSet')
    
    UUIDCT = collection.sub(tree, c+'UUID', dataSetInformationCT, {}, 'unitGroupDataSet')
    UUIDCT.text = id_
    
    NameCT = collection.sub(tree, c+'name', dataSetInformationCT, {w:'en'}, 'unitGroupDataSet')
    NameCT.text = name
    
    quantitativeReference = collection.sub(tree, 'quantitativeReference', ugInformation, {}, 'unitGroupDataSet')
        
    referenceToReferenceUnit = collection.sub(tree, 'referenceToReferenceUnit', quantitativeReference, {}, 'unitGroupDataSet')
    referenceToReferenceUnit.text = "0"
    
    # Create administrativeInformation main subelements
    administrativeInformationCT = collection.sub(tree, 'administrativeInformation', tree.getroot(), {}, 'unitGroupDataSet')

    dataEntryByCT = collection.sub(tree, 'dataEntryBy', administrativeInformationCT, {}, 'unitGroupDataSet')
    
    referenceToDataSetFormatCT = collection.sub(tree, c+'referenceToDataSetFormat', dataEntryByCT, {}, 'unitGroupDataSet')
    collection.do_reference(referenceToDataSetFormatCT, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', 'ILCD Format')
    
    publicationAndOwnershipCT = collection.sub(tree, 'publicationAndOwnership', administrativeInformationCT, {}, 'unitGroupDataSet')
    
    dataSetVersionCT = collection.sub(tree, c+'dataSetVersion', publicationAndOwnershipCT, {}, 'unitGroupDataSet')
    dataSetVersionCT.text = "01.00.000"
    
    permanentDataSetURICT = collection.sub(tree, c+'permanentDataSetURI', publicationAndOwnershipCT, {}, 'unitGroupDataSet')
    permanentDataSetURICT.text = 'http://openlca.org/ilcd/resource/unitgroups/'+id_
    
    # Create the units using all units from units.py that are in the same category
    units = collection.sub(tree, 'units', tree.getroot(), {}, 'unitGroupDataSet')
    
    for i, (key, values) in enumerate(ut.unit_s2[unit_group].items()):
        unit = collection.sub(tree, 'unit', units, {}, 'unitGroupDataSet')
        if key == main_unit:
            unit.set("dataSetInternalID", '0')
        else:
            unit.set("dataSetInternalID", str(i+1))
        nameu = collection.sub(tree, 'name', unit, {}, 'unitGroupDataSet')
        nameu.text = key
        
        result = values[1]
        if len(values) == 4:
            result = values[2](1)
        
        meanvalueu = collection.sub(tree, 'meanValue', unit, {}, 'unitGroupDataSet')
        meanvalueu.text = str(result)
        
    from Lavoisier.conversion_caller import save_dir
    
    # Create directory
    collection.create_folder(save_dir+"/unitgroups")
    
    # Save unitGroupDataSet file
    c_file = save_dir+"/unitgroups/" + id_ + ".xml"
    with open(c_file, 'wb') as c_:
        c_.write(ET.tostring(tree, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))

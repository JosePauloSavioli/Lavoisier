#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 24 07:12:26 2021

Open the spold files, save the ILCD files and calling of allocation mapping

@author: jotape42p
"""

import os, glob
from lxml import etree as ET
from zipfile import ZipFile
from shutil import rmtree
from copy import deepcopy

# Collection functions
from collection import get_namespace, str_, create_folder, allocation, zipdir
# Converter
from conversion import convert_spold
# Mapping dict
from mapping import map_p

# Global variable
save_dir = ''


###############################################################################

def file_convertion_caller(e_tree, ilcd_tree, dir_path_to_save, return_xml = False):
    '''Calls the conversion function on conversion.py file, can return an xml file'''
    
    # Set path variable for other functions
    global save_dir
    save_dir = dir_path_to_save+"/ILCD-algorithm"
    
    # Initialization of ILCD .zip file
    ILCD_zip = ZipFile(dir_path_to_save + 
                       e_tree.find(str_(['activity', 'activityName'])).text +
                       ', ' + 
                       e_tree.find(str_(['geography', 'shortname'])).text + 
                       '.zip', 'w')
    
    # Creates dummy folder for the ILCD zip file
    if os.path.isdir(save_dir):
        rmtree(save_dir)
        create_folder(save_dir)
    else:
        create_folder(save_dir)
        
    # Allocation data. It has to be before the mapping since allocation is a
    #   major property on Ecospold2 files
    al = allocation(e_tree)
    
    # Call main conversion function
    convert_spold(map_p, e_tree, ilcd_tree, ilcd_tree, deepcopy(e_tree), al)
    
    # Create process folder to accomodate the resultant process file
    create_folder(save_dir+'/processes')
    
    # Save ILCD processDataSet
    with open(save_dir+'/processes/'+e_tree.find(str_(['activity'])).get('id')+'.xml', 'wb') as f:
        f.write(ET.tostring(ilcd_tree, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))
    
    # Zip the directory and close the zip file
    zipdir(save_dir, ILCD_zip)
    ILCD_zip.close()
    
    # Remove dummy directory
    rmtree(save_dir)
    
    if return_xml:
        return ilcd_tree
    
    
###############################################################################

def convert_file_to_ILCD(path_to_file, dir_path_to_save, return_xml = False):
    '''
    This function calls the mapping to convert a spold file (Ecospold2) to an ILCD zip file
    
    Inputs:
        path_to_file        absolute path to .spold file to be converted
        path_to_save_dir    absolute path to save file directory (relative paths will be saved on the library's directory)
        return_xml          return the xml file as a result of the function
        
    Outputs:
        [xml_file]  optional xml file returned when return_xml is True
    '''
    
    # Input handling
    if not isinstance(path_to_file, str) or not isinstance(dir_path_to_save, str):
        raise Exception("path_to_file or path_to_save_dir has to be a string")
    if not isinstance(return_xml, bool):
        raise Exception("return_xml is not a boolean")
    if not os.path.isfile(path_to_file):
        raise Exception(f"{path_to_file} is not a valid file path")
    if path_to_file.split('.')[-1] != ".spold":
        raise Exception("file is not an .spold file")
    if not os.path.isdir(dir_path_to_save):
        raise Exception(f"{dir_path_to_save} is not a valid directory path")
    
    # Ecospold tree xml file initialization 
    parser = ET.XMLParser(remove_blank_text = True)
    e_tree = ET.parse(path_to_file, parser)
    
    # New ILCD tree xml file initialization
    processDataSet = ET.Element('processDataSet', version = '1.1', nsmap = get_namespace('ILCD_process'))
    ilcd_tree = ET.ElementTree(processDataSet)
    
    # Call for single dataset conversion
    if return_xml:
        ilcd_tree = file_convertion_caller(e_tree, ilcd_tree, dir_path_to_save, return_xml)
        return ilcd_tree
    else:
        file_convertion_caller(e_tree, ilcd_tree, dir_path_to_save, return_xml)
    

def convert_dir_to_ILCD(path_to_dir, dir_path_to_save):
    '''
    This function calls the mapping to convert a spold file (Ecospold2) to an ILCD zip file
    
    Inputs:
        path_to_dir         absolute path to the directory of .spold files to be converted (all files has to be .spold files)
        path_to_save_dir    absolute path to save file directory (relative paths will be saved on the library's directory)
        return_xml          return the xml file as a result of the function
        
    Outputs:
        [xml_file]  optional xml file returned when return_xml is True
    '''
    
    # Input handling
    if not isinstance(path_to_dir, str) or not isinstance(dir_path_to_save, str):
        raise Exception("path_to_file or path_to_save_dir has to be a string")
    if not os.path.isfile(path_to_dir):
        raise Exception(f"{path_to_dir} is not a valid file path")
    if not os.path.isdir(dir_path_to_save):
        raise Exception(f"{dir_path_to_save} is not a valid directory path")
        
    # Loop through all spold files on the directory
    for file in glob.glob(os.path.join(path_to_dir,'/*.spold')):
        
        # Ecospold tree xml file initialization 
        parser = ET.XMLParser(remove_blank_text = True)
        e_tree = ET.parse(file, parser)
    
        # New ILCD tree xml file initialization
        processDataSet = ET.Element('processDataSet', version = '1.1', nsmap = get_namespace('ILCD_process'))
        ilcd_tree = ET.ElementTree(processDataSet)
        
        # Call for single dataset conversion
        file_convertion_caller(e_tree,ilcd_tree)
        
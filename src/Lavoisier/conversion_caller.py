#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 24 07:12:26 2021

Open the spold files, save the ILCD files and calling of allocation mapping

@author: jotape42p
"""

import os, glob, re, logging, time, sys
from lxml import etree as ET
from zipfile import ZipFile
from shutil import rmtree, copy
from copy import deepcopy

# Global variable
save_dir = ''

# Collection functions
from Lavoisier.collection import get_namespace, str_, create_folder, allocation, zipdir
# Converter
from Lavoisier.conversion import convert_spold
# Mapping dict
from Lavoisier.mapping import map_p

if sys.version_info >= (3, 8):
    import importlib.metadata as imp
else:
    import importlib_metadata as imp

__version__ = imp.version("Lavoisier")

###############################################################################

def file_convertion_caller(e_tree, ilcd_tree, dir_path_to_save, hash_ = '', return_xml = False):
    '''Calls the conversion function on conversion.py file, can return an xml file'''
    
    # Set path variable for other functions
    global save_dir
    save_dir = dir_path_to_save+"/ILCD-algorithm"
    
    # Initialization of ILCD .zip file
    text = e_tree.find(str_(['activity', 'activityName'])).text +\
                       ', ' +\
                       e_tree.find(str_(['geography', 'shortname'])).text +\
                       hash_ + '.zip'
    
    print("Converting: " + text)
    
    if re.search('/', text):
        text = re.sub('/', 'per', text)
    ILCD_zip = ZipFile(dir_path_to_save + '/' +  text, 'w')
    
    # Creates dummy folder for the ILCD zip file
    if os.path.isdir(save_dir):
        rmtree(save_dir)
        create_folder(save_dir)
    else:
        create_folder(save_dir)
        
    logging.basicConfig(filename=save_dir+"/lavoisier.log",
                        format="%(message)s",
                        force = True,
                        level=logging.DEBUG)
    
    logging.info(f"\n###\nLavoisier version: {__version__}\nConversion started at: {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())}\nLavoisier, converter from Ecospold2 to ILCD, powered by Gyro (UTFPR) and IBICT\nLicensed under GNU General Public License v3 (GPLv3)\n###\n")
    
    
    # Allocation data. It has to be before the mapping since allocation is a
    #   major property on Ecospold2 files
    al = allocation(e_tree)
    
    logging.info(f"Activity  {text}: {e_tree.find(str_(['activity'])).get('id')}")
    
    logging.debug(f"allocation: {al}")
    
    # Call main conversion function
    convert_spold(map_p, e_tree, ilcd_tree, ilcd_tree, deepcopy(e_tree), al)
    
    logging.info("Main conversion successful")
    
    # Create process folder to accomodate the resultant process file
    create_folder(save_dir+'/processes')
    
    # Save ILCD processDataSet
    with open(save_dir+'/processes/'+e_tree.find(str_(['activity'])).get('id')+'.xml', 'wb') as f:
        f.write(ET.tostring(ilcd_tree, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))
    
    # Place additional xml files
    path_ = os.path.abspath(os.path.dirname(__file__))
    pathMP = os.path.join(path_, "Mapping_files/classification.xml")
    copy(pathMP, save_dir)
    pathMP = os.path.join(path_, "Mapping_files/locations.xml")
    copy(pathMP, save_dir)
    pathMP = os.path.join(path_, "Mapping_files/flowCategories.xml")
    copy(pathMP, save_dir)
    
    # Close logging handlers and logging (Permission Denied Error)
    #logging.handlers.clear()
    logging.shutdown()
    
    # Zip the directory and close the zip file
    zipdir(save_dir, ILCD_zip)
    ILCD_zip.close()
    
    # Remove dummy directory
    rmtree(save_dir)
    
    if return_xml:
        return ilcd_tree
    
    
###############################################################################

def convert_file_to_ILCD(path_to_file, dir_path_to_save, hash_ = '', return_xml = False):
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
    if path_to_file.split('.')[-1].lower() != "spold":
        raise Exception("file is not an .spold file")
    if not os.path.isdir(dir_path_to_save):
        raise Exception(f"{dir_path_to_save} is not a valid directory path")
    
    # Ecospold tree xml file initialization 
    parser = ET.XMLParser(remove_blank_text = True)
    e_tree = ET.parse(path_to_file, parser)
    
    # New ILCD tree xml file initialization
    processDataSet = ET.Element('processDataSet', version = '1.1', nsmap = get_namespace('ILCD_process'))
    ilcd_tree = ET.ElementTree(processDataSet)
    processDataSet.set('locations', '../locations.xml')
    
    # Call for single dataset conversion
    if return_xml:
        ilcd_tree = file_convertion_caller(e_tree, ilcd_tree, dir_path_to_save, hash_, return_xml)
        return ilcd_tree
    else:
        file_convertion_caller(e_tree, ilcd_tree, dir_path_to_save, hash_, return_xml)
    

def convert_dir_to_ILCD(path_to_dir, dir_path_to_save, hash_ = ''):
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
    if not os.path.isdir(path_to_dir):
        raise Exception(f"{path_to_dir} is not a valid file path")
    if not os.path.isdir(dir_path_to_save):
        raise Exception(f"{dir_path_to_save} is not a valid directory path")
        
    # Loop through all spold files on the directory
    for file in glob.glob(os.path.join(path_to_dir,'*.spold')):
        
        # Ecospold tree xml file initialization 
        parser = ET.XMLParser(remove_blank_text = True)
        e_tree = ET.parse(file, parser)
    
        # New ILCD tree xml file initialization
        processDataSet = ET.Element('processDataSet', version = '1.1', nsmap = get_namespace('ILCD_process'))
        ilcd_tree = ET.ElementTree(processDataSet)
        processDataSet.set('locations', '../locations.xml')
        
        # Call for single dataset conversion
        file_convertion_caller(e_tree,ilcd_tree,dir_path_to_save,hash_)
        

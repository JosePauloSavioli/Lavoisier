#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 11:30:02 2022

@author: jotape42p
"""

import time
import shutil
import logging
import xmltodict
import zipfile
from pathlib import Path
from .utils import zipdir, Dataset

class ILCD1Helper:
    
    @staticmethod
    def is_valid(path):
        f = zipfile.ZipFile(path, 'r')
        b = any((x.startswith("processes/") or x.find("/processes/") != -1) and x.endswith(".xml") for x in f.namelist())
        if not b:
            raise Exception("ILCD 'process' folder not found or empty inside compressed file. File not considered as a valid ILCD file")

    number = 1000
    @classmethod
    def add(cls):
        cls.number += 1
        return cls.number
    
    default_language = None

    @staticmethod
    def add_prefix(x, prefix):
        return prefix + x['#text']

    @classmethod
    def add_index(cls, x, index = None, prefix = ''):
        if index is None: index = cls.add()
        return {'@index': index, '#text': cls.add_prefix(x, prefix)}

    @classmethod
    def text_add_index(cls, x, prefix="", index=None):
        if index is None:
            index = cls.number
            cls.number += 1
        if isinstance(x, str): # specific not well-formed texts
            x = {'@lang': 'en', '#text': x}
        return {'@index': index, '@lang': x.get('@lang', cls.default_language), '#text': prefix+x['#text']}

    @staticmethod
    def text_dict_from_text(index, text):
        return {'@index': index,
                '@lang': 'en',
                '#text': text}

    @staticmethod
    def time_get_end(x):
        if time.strptime(x, '%Y-%m-%d').tm_mon < 6:
            return str(time.strptime(x, '%Y-%m-%d').tm_year)
        else:
            return str(time.strptime(x, '%Y-%m-%d').tm_year + 1)
        
    @staticmethod
    def source_short_ref(first_author, source_year, page=None):
        if first_author is not None:
            if source_year is not None:
                if page is not None:
                    return first_author+', ('+source_year+') p. '+page
                return first_author+', ('+source_year+')'
            else:
                return first_author
        else:
            return "Source"

class ILCD(Dataset):

    _additional_files = {
        ('Lavoisier_Default_Files/Lavoisier_Classifications', ''):
            ("classification_ISIC rev.4 ecoinvent.xml",
             "classification_EcoSpold01Categories.xml",
             "classification_By-product classification.xml",
             "classification_CPC.xml",
             "ILCDLocations.xml",
             "ILCDFlowCategorization.xml",
             "ILCDClassification.xml"),
        ('Lavoisier_Default_Files/ILCD_Sources/', 'sources'):
            ("0d388ade-52ab-4ca6-8a9b-f06df45d880c.xml",
             "9ba3ac1e-6797-4cc0-afd5-1b8f7bf28c6a.xml",
             "a97a0155-0234-4b87-b4ce-a45da52f2a40.xml",
             "cada7914-53c3-47ec-ac27-659b21240a99.xml",
             "88d4f8d9-60f9-43d1-9ea3-329c10d7d727.xml"), # For unit groups
        ('Lavoisier_Default_Files/ILCD_Contacts/', 'contacts'):
            ("d0d5f8bb-9311-49d1-9e30-2f20a6977f4f.xml", # For the default sources
             "631b917e-eb39-4d0f-aae6-98c805513b2f.xml",
             "97f476bd-415a-4463-955a-019202b70ae4.xml"),
        ('Lavoisier_Default_Files/ILCD_External_Docs/', 'external_docs'):
            ("ILCD_Compliance_Rules_Draft_88d4f8d9-60f9-43d1-9ea3-329c10d7d727.pdf", # For the default sources
             "ILCD-Data-Network_Compliance-Entry-level_Version1.1_Jan2012.pdf")
    }

    hash_ = ''
    only_elem_flows = False

    def __init__(self,
                 save_path,
                 structure):
        self.__args = (save_path, structure)
        self.save_path = save_path.resolve()
        self.save_dir = Path(self.save_path, "ILCD-algorithm")
        self.struct = structure()

    def handle_error(self):
        if self.save_dir.is_dir():
            shutil.rmtree(self.save_dir)
                
        self.end_log()

    def start_conversion(self, filename):
        if self.save_dir.is_dir():
            shutil.rmtree(self.save_dir)

        for dir_ in ("", "processes", "external_docs", "sources", "contacts"):
            p = Path(self.save_dir, dir_)
            p.mkdir(exist_ok=True)
            
        for (orig_dir, to_save_dir), files in self._additional_files.items():
            for file in files:
                shutil.copy(Path(Path(__file__).parent.parent.resolve(), orig_dir, file),
                            Path(self.save_dir, to_save_dir))

        self.start_log()

    def start_log(self):
        from .. import __version__
        logging.basicConfig(filename=str(Path(self.save_dir, "lavoisier.log")),
                            format="%(levelname)s - %(message)s",
                            force=True,
                            level=logging.DEBUG)
        logging.info(f"\n###\nLavoisier version: {__version__}\nConversion started at: {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())}"+\
                     "\nLavoisier, converter of LCI formats, powered by Gyro (UTFPR) and IBICT\nLicensed under GNU General Public License v3 (GPLv3)\n###\n")

    def end_log(self):
        logging.info("\nConversion ended")
        logging.shutdown()

    def _write_process(self):
        process_dict = self.struct.get_dict()
        dsi = self.struct.dataSetInformation
        self.process_path = Path(
            self.save_dir, 'processes', dsi.get('c_UUID', dsi.get('UUID'))+'.xml')
        with open(self.process_path, 'w') as c:
            c.write(xmltodict.unparse(process_dict,
                    pretty=True, newl='\n', indent="  "))

    def get_process_name(self):
        bn = self.struct.dataSetInformation['name'].get('baseName')
        geo = self.struct.geography['locationOfOperationSupplyOrProduction']
        time = self.struct.time
        name = f"{bn[0]['#text'] if isinstance(bn, list) else bn['#text']}, "+\
            f"{geo.get('location')}, "+\
            f"{time.get('referenceYear')} - {time.get('dataSetValidUntil')}"+\
            f"{self.hash_}"
        return name.replace('/', ' per ')

    def end_conversion(self, multi=False, extracted_file=None):
        name = name_ = 'ILCD'+self.hash_ if multi else self.get_process_name()
        self.reset_conversion()
        
        if Path(self.save_path, name_+'.zip').is_file():
            i = 1
            while Path(self.save_path, name_+'.zip').is_file():
                name_ = name + ' (' + str(i) + ')'
                i += 1
        
        if extracted_file:
            if type(self).only_elem_flows:
                for dir_ in ("", "external_docs", "sources", "contacts", "flowproperties", "unitgroups"):
                    Path(self.save_dir, dir_).mkdir(exist_ok=True)
                    
                    if Path(extracted_file, 'processes').is_dir():
                        gen = Path(extracted_file, dir_).glob('*.xml')
                    else:
                        for d in Path(extracted_file).iterdir():
                            if Path(extracted_file, d).is_dir() and Path(extracted_file, d, 'processes').is_dir():
                                gen = Path(extracted_file, d, dir_).glob('*.xml')
                                break
                        else:
                            raise Exception("No valid ILCD directory in {extracted_file}")
                    for file in gen:
                        shutil.copy(file,
                                    Path(self.save_dir, dir_))
                        
            shutil.rmtree(extracted_file)
        
        self.zipfile_path = Path(
            self.save_path, name_+'.zip')
        ilcd_zipfile = zipfile.ZipFile(self.zipfile_path, 'w')
        zipdir(self.save_dir, ilcd_zipfile)
        ilcd_zipfile.close()
        
        shutil.rmtree(self.save_dir)

        self.end_log()

    def reset_conversion(self):
        self._write_process()
        bn = self.struct.dataSetInformation['name'].get('baseName')
        logging.info(
            f"\n\nConversion ended for {bn[0]['#text'] if isinstance(bn, list) else bn['#text']}\n")
        self.__init__(*self.__args)

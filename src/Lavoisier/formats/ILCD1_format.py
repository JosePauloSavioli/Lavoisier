#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 11:30:02 2022

@author: jotape42p
"""

import shutil
import xmltodict
import zipfile
from pathlib import Path
from .utils import zipdir
from .abstractions import InputTemplate, OutputTemplate
import tempfile

class ILCD1Input(InputTemplate):
    
    _valid_extensions = (".zip",".ZIP",".xml")
    
    # Includes path correction to the process folder
    def _extract(self, file):
        self.file = zipfile.ZipFile(file)
        for x in self.file.namelist():
            if (x.startswith("processes/") or x.find("/processes/") != -1) and x.endswith(".xml"):
                name = '.'.join(str(self.path).split('.')[:-1]).split('/')[-1]
                self._tempdir = tempfile.TemporaryDirectory() # Has to be closed after
                self._extracted_path = Path(self._tempdir.name, name)
                _path = Path(self._extracted_path, x.split("processes/")[0])
                self._input_file = _path
                self._extracted_path.mkdir(exist_ok=True)
                self.file.extractall(str(self._extracted_path))
                break
        return _path
    
    def _single_file_input(self): # This covers the case where there are multiple processes
        path = self._extract(self.path)
        yield from self._yield_files(list(self._get_files_of_extension(Path(path, 'processes'),
                                                                       self._valid_extensions[2:])))
        self._tempdir.cleanup()
    
    def _multiple_file_input(self):
        for i, zip_file in enumerate(self._get_files_of_extension(self.path,
                                                                  self._valid_extensions[:2])):
            path = self._extract(zip_file)
            yield from self._yield_files(list(self._get_files_of_extension(Path(path, 'processes'),
                                                                           self._valid_extensions[2:])))
            self._tempdir.cleanup()
        
    def handle_error(self):
        self._tempdir.cleanup()

    
class ILCD1Output(OutputTemplate):
    
    _additional_files = {
        ('Lavoisier_Default_Files/Lavoisier_Classifications', ''):
            (#"classification_ISIC rev.4 ecoinvent.xml",
             #"classification_EcoSpold01Categories.xml",
             #"classification_By-product classification.xml",
             #"classification_CPC.xml",
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
    
    def start_conversion(self):
        self._tempdir = tempfile.TemporaryDirectory() # Has to be closed after
        self._output_file = self._tempdir.name

        for dir_ in ("", "processes", "external_docs", "sources", "contacts", "flowproperties", "unitgroups"):
            p = Path(self._tempdir.name, dir_)
            p.mkdir(exist_ok=True)
            
        for (orig_dir, to_save_dir), files in self._additional_files.items():
            for file in files:
                shutil.copy(Path(Path(__file__).parent.parent.resolve(), orig_dir, file),
                            Path(self._tempdir.name, to_save_dir))

        self.log_path = Path(self._tempdir.name, "lavoisier.log")
        self.log.start_log(self.log_path)
    
    def write_process(self):
        process_dict = self.struct.get_dict()
        dsi = self.struct.dataSetInformation
        self.process_path = Path(
            self._tempdir.name, 'processes', dsi.get('c_UUID', dsi.get('UUID'))+'.xml')
        with open(self.process_path, 'w') as c:
            c.write(xmltodict.unparse(process_dict,
                    pretty=True, newl='\n', indent="  "))
    
    def end_conversion(self):
        name = 'ILCD'+self._hash if self.multi_files else self.struct.get_filename(self._hash)
        self.end_single_output_file()
        name = self.check_name_for_existence(name, '.zip')
        
        self.log.end_log(self.log_path)
        ilcd_zipfile = zipfile.ZipFile(Path(self.path, name+'.zip'), 'w')
        zipdir(self._tempdir.name, ilcd_zipfile)
        ilcd_zipfile.close()
        self._tempdir.cleanup()
            
    def handle_error(self):
        super().handle_error()
        if hasattr(self, '_tempdir'):
            self._tempdir.cleanup()

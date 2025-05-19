#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 11:37:05 2022

@author: jotape42p
"""

import xmltodict

from pathlib import Path
from .abstractions import InputTemplate, OutputTemplate

class ECS2Input(InputTemplate):
    
    _valid_extensions = (".spold", ".SPOLD")
    
    def _single_file_input(self):
        yield (self.path, True)
    
    def _multiple_file_input(self):
        yield from self._yield_files(list(self._get_files_of_extension(self.path,
                                                                       self._valid_extensions)))

class ECS2Output(OutputTemplate):
    
    def start_conversion(self):
        self.log_path = Path(self.path, f"{self.filename.replace('/', '_per_')}.log")
        self.log.start_log(self.log_path)

    def write_process(self):
        process_dict = self.struct.get_dict()
        self.name = self.struct.get_filename(self._hash)
        self.name = self.check_name_for_existence(self.name, '.spold')
        
        with open(Path(self.path, self.name+'.spold'), 'w') as c:
            c.write(xmltodict.unparse(process_dict,
                    pretty=True, newl='\n', indent="  "))

    def end_conversion(self):
        self.end_single_output_file()
        self.log.end_log(self.log_path)
        return str(Path(self.path, self.name+'.spold'))
        

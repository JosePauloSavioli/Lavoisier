#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 11:37:05 2022

@author: jotape42p
"""

import re
import uuid
import random
import time
import logging
import shutil
import xmltodict
rdn = random.Random()

from pathlib import Path
from .utils import Dataset

class ECS2Helper:
    
    @staticmethod
    def _get_str(cl, cl_f, keys, pattern, text, extra=lambda x:None):
        if re.search(pattern+r' (.*)+?(?:\n|$)', text):
            g = re.search(pattern+r' (.*)+?(?:\n|$)', text).groups()[0]
            setattr(cl, cl_f, keys.get(g))
            extra(keys.get(g))
            return re.sub(pattern+r' (.*)+?(?:\n|$)', '', text)
        return text
            
    @staticmethod
    def _get_list_str(cl, cl_f, pattern, text):
        if re.search(pattern+r' (.*)+?\n', text):
            rt = text
            for t in re.search(pattern+r' (.*)+?\n', text).groups()[0].split('; '):
                setattr(cl, cl_f, t)
                rt = re.sub(pattern+r' (.*)+?\n', '', rt)
            return rt
        return text
    
    @staticmethod
    def _get_uuid(cl, cl_f, pattern, text, extra=lambda x:None):
        if re.search(pattern+r' [a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\n', text):
            id_ = re.search(pattern+r' ([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\n', text).groups()[0]
            setattr(cl, cl_f, id_)
            extra(id_)
            return re.sub(pattern+r' [a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\n', '', text)
        return text
    
    @staticmethod
    def get_text_uuid(field):
        if re.search('[A-z0-9]{8}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{12}', field):
            return re.search('[A-z0-9]{8}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{12}', field).group(0)
        else:
            rdn.seed(int(''.join([str(ord(c)) for c in field])))
            return str(uuid.UUID(int=rdn.getrandbits(128), version=4))

class ECS2(Dataset):

    hash_ = ''

    def __init__(self,
                 save_path,
                 structure):
        self.__args = (save_path, structure)
        self.save_path = save_path.resolve()
        self.struct = structure()

    def handle_error(self, extracted_file):
        self.end_log()
        if extracted_file.is_dir():
            shutil.rmtree(extracted_file)

    def start_conversion(self, filename):
        self.filename = filename
        self.start_log()

    def start_log(self):
        from .. import __version__
        logging.basicConfig(filename=str(Path(self.save_path, f"lavoisier_{self.filename}.log")),
                            format="%(levelname)s - %(message)s",
                            force=True,
                            level=logging.DEBUG)
        logging.info(f"\n###\nLavoisier version: {__version__}\nConversion started at: {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())}"+\
                     "\nLavoisier, converter from Ecospold2 to ILCD, powered by Gyro (UTFPR) and IBICT\nLicensed under GNU General Public License v3 (GPLv3)\n###\n")

    def end_log(self):
        logging.info("\nConversion ended")
        logging.shutdown()

    def _write_process(self):
        process_dict = self.struct.get_dict()
        path = Path(self.save_path, self.get_process_name()+'.spold')
        with open(path, 'w') as c:
            c.write(xmltodict.unparse(process_dict,
                    pretty=True, newl='\n', indent="  "))

    def get_process_name(self):
        name = f"{self.struct.activityDescription.activity.get('activityName')[0]['#text']}, "+\
            f"{self.struct.activityDescription.geography.get('shortname')[0]['#text']}, "+\
            f"{self.struct.activityDescription.timePeriod.get('a_startDate')[:4]} - {self.struct.activityDescription.timePeriod.get('a_endDate')[:4]}"+\
            f"{self.hash_}"
        return name.replace('/', ' per ')

    def end_conversion(self, multi=None, extracted_file=None):
        self.reset_conversion()
        if extracted_file.is_dir():
            shutil.rmtree(extracted_file)
        self.end_log()

    def reset_conversion(self):
        self._write_process()
        logging.info(
            f"\n\nConversion ended for {self.struct.activityDescription.activity.get('activityName')[0]['#text']}\n")
        self.__init__(*self.__args)

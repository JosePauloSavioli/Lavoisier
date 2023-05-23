#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 02:25:47 2023

@author: jotape42p
"""

import re
import uuid
import time
import random
import zipfile
rdn = random.Random()

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
    def time_get_end(x): # Changed 30/03/2023 after feedback: use only the year
        return str(time.strptime(x, '%Y-%m-%d').tm_year)
        # if time.strptime(x, '%Y-%m-%d').tm_mon < 6:
        #     return str(time.strptime(x, '%Y-%m-%d').tm_year)
        # else:
        #     return str(time.strptime(x, '%Y-%m-%d').tm_year + 1)
        
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
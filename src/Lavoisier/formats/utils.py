#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 12:08:41 2022

@author: jotape42p
"""

import os

def zipdir(path, ziph):

    len_path = len(str(path))
    for root, _, files in os.walk(path):
        for file in files:
            filepath = os.path.join(root, file)
            ziph.write(filepath, filepath[len_path:])

from .abstractions import LogTemplate
import logging
import time, re

class DefaultLog(LogTemplate):
    # Make structure collect the file name

    def start_log(self, log_path):
        from .. import __version__
        logging.basicConfig(filename=str(log_path),
                            format="%(levelname)s - %(message)s",
                            force=True,
                            level=logging.DEBUG)
        logging.info(f"\n###\nLavoisier version: {__version__}\nConversion started at: {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())}"+\
                     "\nLavoisier, converter of LCI formats, powered by Gyro (UTFPR) and IBICT\nLicensed under GNU General Public License v3 (GPLv3)\n###\n")

    def reset_log(self, finished_filename):
        logging.info(f"\n\nConversion ended for {finished_filename}\n")

    def end_log(self, log_path):
        logging.info("\nConversion ended")
        logging.handlers = []
        
        if log_path is not None:
            with open(str(log_path), 'r') as f:
                converted = re.findall('INFO -[\W]+Starting conversion of flow ([\S ]+?) : ([0-9a-f-]{36})\nWARNING -[\W]+Flow not converted (due to lack of elementary flow correspondence in the|as the flow is not present on the elementary flow) mapping file', f.read())
            if len(converted) > 0:
                with open(str(log_path)[:-4]+'_not_converted_elementary_flows.log', 'w') as f:
                    for ef in converted:
                        print(ef[1]+' : '+ef[0], file=f)
        
        # logging.shutdown()

from .abstractions import BasicIterable
import xml.etree.cElementTree as etree

class XMLStreamIterable(BasicIterable):

    def __init__(self,
                 file,
                 keys: dict):
        self._tree = etree.iterparse(file, events=["start", "end"])
        self._keys = list(keys.keys())
        self._path = ""
        self.gen = self.gen_return()

    def __iter__(self):
        return self

    def elem2dict(self, e):

        result = {
            **{("@"+x.rpartition("}")[-1] if '}' in x else "@"+x): y for x, y in e.attrib.items()},
            **({'#text': e.text} if e.text and not e.text.isspace() else {}),
        }

        if len(e) == 0 and '@lang' in result and '#text' not in result:  # Maybe change
            result["#text"] = ''

        for t in e:
            n = t.tag.rpartition("}")[-1] if '}' in t.tag else t.tag
            if n in result:
                ln = result[n]
                result[n] = (ln if isinstance(ln, list)
                             else [ln]) + [self.elem2dict(t)]
            else:
                result[n] = self.elem2dict(t)

        if list(result) == ['#text']: # If its only a text, make it return only the text
            result = result['#text']

        return result

    def gen_return(self):
        try:
            while 1:
                event, n = next(self._tree)
                if event == "start":
                    self._path += "/" + n.tag.rpartition("}")[-1]
                elif event == "end":
                    if self._path in self._keys:
                        b = (bool(n.attrib), (n.text is not None or not str(
                            n.text).isspace()), len(n) != 0)
                        if any(b):
                            # n.clear() # This makes the pointer go to the next element after the entire 'n'
                            yield (self._path, self.elem2dict(n))
                    # else: # This else makes the pointer pass the attributes to the next element
                    for tag in n.attrib:
                        t = self._path + "/@" + tag
                        if t in self._keys:
                            yield (t, n.attrib[tag])
                            # self._keys.remove(t)
                    # if self._path in self._keys:
                        # n.clear()
                    self._path = self._path.rpartition("/")[0]
                    # n.clear()
                
        except StopIteration:
            pass

    def __next__(self):
        try:
            return next(self.gen)
        except StopIteration:
            raise StopIteration

import ijson

class JSONStreamIterablt(BasicIterable):

    def __init__(self, file, keys: dict): # 'keys' here is the mapping dictionary
        self._file = file
        self._keys = list(keys.keys())
        self.gen = self.gen_return()

    def __iter__(self):
        return self
    
    def gen_return(self):
        try:
            for key in self._keys:
                res = list(ijson.items(self._file, key))
                yield (key, (res[0] if len(res) == 1 else res))
                self._file.seek(0) # Returns the pointer to 0 for a new query
        except StopIteration:
            pass

    def __next__(self):
        return next(self.gen)

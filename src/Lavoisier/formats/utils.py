#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 12:08:41 2022

@author: jotape42p
"""

import os
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class AbstractDataclass(ABC):
    def __new__(cls, *args, **kwargs):
        if cls == AbstractDataclass or cls.__bases__[0] == AbstractDataclass:
            raise TypeError("Cannot instantiate abstract class.")
        return super().__new__(cls)

class Dataset(ABC):
    def __init__(self):
        pass
    @abstractmethod
    def handle_error(self):
        pass
    @abstractmethod
    def start_log(self):
        pass
    @abstractmethod
    def end_log(self):
        pass
    @abstractmethod
    def start_conversion(self):
        pass
    @abstractmethod
    def end_conversion(self):
        pass
    @abstractmethod
    def reset_conversion(self):
        pass

def zipdir(path, ziph):

    len_path = len(str(path))
    for root, _, files in os.walk(path):
        for file in files:
            filepath = os.path.join(root, file)
            ziph.write(filepath, filepath[len_path:])

from collections.abc import Iterator
import xml.etree.cElementTree as etree

class XMLStreamIterable(Iterator):

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

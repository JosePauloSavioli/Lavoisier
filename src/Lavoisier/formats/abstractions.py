#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 02:28:15 2023

@author: jotape42p
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections.abc import Iterator

@dataclass
class AbstractDataclass(ABC):
    def __new__(cls, *args, **kwargs):
        if cls == AbstractDataclass or cls.__bases__[0] == AbstractDataclass:
            raise TypeError("Cannot instantiate abstract class.")
        return super().__new__(cls)

class BasicIterable(Iterator, ABC):
    
    def __init__(self, file, keys):
        pass
    
    def __iter__(self):
        return self
    
    def __next__(self):
        pass
    
class LogTemplate(ABC):
    
    @abstractmethod
    def start_log(self, log_path):
        pass
    
    @abstractmethod
    def reset_log(self, finished_filename):
        pass
    
    @abstractmethod
    def end_log(self):
        pass

    
class PathVerifier(ABC):
    # Opens and contains the file

    def __init__(self, path):
        self.path = self._verify_path(path)
    
    def _verify_path(self, path):
        path = Path(path)
        if not path.exists():
            raise OSError(
                f'{path} is not a valid {"directory" if path.is_dir() else "file"} path')
        if path.is_file():
            for ve in type(self)._valid_extensions:
                if path.match('*'+ve):
                    break
            else:
                raise OSError(
                    f'{path} is not a valid extension for the input format. Valid extensions are {[ve for ve in type(self)._valid_extensions]}')
        return path


class InputTemplate(PathVerifier, ABC):
    # Create and make available a stream of files that shall be used in conversion
    
    _valid_extensions = tuple()
    
    def __init__(self, path):
        super().__init__(path)
        self._input_file = deepcopy(self.path) # Used in start conversion to pass to mapping
        if self.path.is_file():
            self.get_files = self._single_file_input
        elif self.path.is_dir():
            self.get_files = self._multiple_file_input
        else:
            raise ValueError(f"Invalid path {self.path}")
    
    @staticmethod
    def _yield_files(files):
        for i, f in enumerate(files):
            if i != len(files)-1:
                yield f, False
            else:
                yield f, True
    
    def _get_files_of_extension(self, path, ext):
        n = []
        for ve in ext:
            n.extend(path.glob('*'+ve))
        return n
    
    def get_files(self):
        pass

    def handle_error(self):
        pass

    
from copy import deepcopy
from pathlib import Path
from .utils import DefaultLog
        
class OutputTemplate(PathVerifier, ABC):
    
    # Create and maintain the file or directory structure in which data will be passed to
    # Holder of the structure of the files
    # Check for multi and ext_file necessities
    # Resets everytime a new file is demanded
    
    filename = ''
    _hash = ''
    
    only_elem_flows = False # Conversion only for elementary flows
    
    def __init__(self, path, of, structure):
        super().__init__(path)
        self._output_file = deepcopy(of) # Used in start conversion to pass to mapping
        self.path = self.path.resolve()
        self.struct = structure() # structure is a class
        self.log = DefaultLog()
        self.multi_files = False
        
    def end_single_output_file(self):
        self.write_process()
        self.log.reset_log(self.filename)
        self.__init__(self.path, self._output_file, self.struct.__class__)
        
    def check_name_for_existence(self, name, extension):
        name_ = deepcopy(name)
        if Path(self.path, name_+extension).is_file():
            i = 1
            while Path(self.path, name_+extension).is_file():
                name_ = name + ' (' + str(i) + ')'
                i += 1
        return name_
        
    @abstractmethod
    def write_process(self):
        pass
        
    @abstractmethod
    def start_conversion(self):
        pass

    def reset_conversion(self):
        self.end_single_output_file()
        self.multi_files = True # Has to be done latter as it resets on the end_single method
    
    @abstractmethod
    def end_conversion(self):
        pass
    
    def handle_error(self):
        self.log.end_log(None)

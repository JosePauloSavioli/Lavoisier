
from pathlib import Path
from abc import ABC, abstractmethod
from collections.abc import Iterator

import warnings
import zipfile

from .formats import (
    ECS2InputConfig,
    ILCD1OutputConfig,
    ECS2OutputConfig,
    ILCD1InputConfig,
    ILCD1Helper
)
from .conversions import MappingFactory

class Converter(ABC):

    def __init__(self,
                 path,
                 save_path,
                 hash_,
                 ef_map,
                 input_config,
                 output_config
                 ):

        self._names = (input_config.name, output_config.name)
        self._elem_nomenclature = (input_config.default_mapping if ef_map[0] is None else ef_map[0],
                                   output_config.default_mapping if ef_map[1] is None else ef_map[1])

        self._valid_extensions = input_config.valid_extensions
        self._ns = input_config.namespaces

        self.__output_data = output_config.output_data  # NOT CHANGE
        self.__output_data.hash_ = hash_
        self.__output_structure = output_config.output_structure  # NOT CHANGE

        self._iterator = input_config.iterator  # CHANGE
        self.__general_mapping = input_config.general_dataset_info
        self._elem_flow_mapping = None
        self._class_mapping = None

        self.path = path  # CHANGE
        self.save_path = save_path  # CHANGE

        self.convert_additional_fields = False # CHANGE
        
        self._options = []
        for conf in (input_config, output_config):
            for name, value in conf.add_options.items():
                self._options.append((conf.name + '_' + name, name, value[1:]))
                setattr(self, name, value[0])
        
        self.mapping_factory = MappingFactory(*self._names,
                                              *self._elem_nomenclature)
        
    def __str__(self):
        return f"\nConverter from {self._names[0]} : {self._elem_nomenclature[0]} to {self._names[1]} : {self._elem_nomenclature[1]}\n\nOptions:\n\tConvert additional fields: {self.convert_additional_fields}\n\t"+'\n\t'.join([f'[{x[0].split("_")[0]}] {"_".join(x[0].split("_")[1:]).replace("_"," ").capitalize()} : {getattr(self, x[1])}' for x in self._options])

    def __setattr__(self, key, value):
        if hasattr(self, '_options'):
            if (key in [x[1] for x in self._options] or key == 'convert_additional_fields') and value not in (True, False):
                raise TypeError(f"Option '{key}' only accepts booleans (True or False). Received '{value}' of type {type(value)}")
        super().__setattr__(key, value)

    def __check_new_mapping(self, path):
        p = Path(path)
        if p.suffix not in ('.csv', '.json'):
            raise OSError(
                f'{p} is not a valid mapping path. Must be a .csv or .json')
        return p

    @property
    def elem_flow_mapping(self):
        return self._elem_flow_mapping

    @elem_flow_mapping.setter
    def elem_flow_mapping(self, mapping_path):
        self._elem_flow_mapping = self.__check_new_mapping(mapping_path)

    @property
    def class_mapping(self):
        return self._class_mapping

    @class_mapping.setter
    def class_mapping(self, mapping_path):
        self._class_mapping = self.__check_new_mapping(mapping_path)

    @property
    def iterator(self):
        return self._iterator

    @iterator.setter
    def iterator(self, iter_):
        if isinstance(iter_, Iterator):
            self._iterator = iter_
        else:
            raise TypeError('Iterator must inherit from the Iterator class')

    def _set_format(self):
        pass

    def _set_field_mapping(self): # Set fields relative to the overall conversion
        type(self._field_mapping)._convert_additional_fields = self.convert_additional_fields
        self._field_mapping.set_mappings(self._elem_flow_mapping, self._class_mapping)

    @abstractmethod
    def convert(self):
        pass

    def _apply_configurations(self, conf_type):
        for _, name, (type_, func) in self._options:
            if type_ == conf_type:
                if type_ == 'single_type':
                    func(getattr(self, name))
                elif type_ == 'conversion_type':
                    func(type(self._field_mapping), getattr(self, name))

    def _get_pre_instance_file_information(self, file):
        self.file_info = {}
        self._o_version = getattr(self, '_version', None)
        with open(file, 'r') as f:
            for i, (path, t) in enumerate(self.iterator(f, self.__general_mapping)):
                gmp = self.__general_mapping[path]
                if gmp[0] not in self.file_info:
                    self.file_info[gmp[0]] = gmp[1](t) if 'list' not in gmp[0] else [gmp[1](t)]
                else:
                    self.file_info[gmp[0]].append(gmp[1](t))
        self._version = self.file_info.pop('version', None)

    def _set_post_instance_file_information(self):
        for field in self.file_info:
            if field[0] == 'mapping':
                setattr(type(self._field_mapping), field[1], self.file_info[field])
            elif field[0] == 'format':
                setattr(self._data, field[1], self.file_info[field])
        self._field_mapping.set_file_info(self.path, self.save_path)

    def start_conversion(self, file, filename, multi=False):
        self._apply_configurations('single_type')
        self._get_pre_instance_file_information(file)
        if not hasattr(self, '_data'):
            self._data = self.__output_data(self.save_path, self.__output_structure)
            self._set_format()
        if not self._o_version == self._version:
            self._field_mapping = self.mapping_factory.get_mapping(self._version)
            self._set_field_mapping()
        self._field_mapping.set_output_class_defaults(self._data.struct)
        self._set_post_instance_file_information()
        self._apply_configurations('conversion_type')
        self.mapping = self._field_mapping.mapping()
        if not multi:
            self._data.start_conversion(filename)
        self._field_mapping.start_conversion()
        
    def reset_conversion(self):
        self._field_mapping.reset_conversion()
        self._data.reset_conversion()

    def end_conversion(self, multi=False, e_file=None):
        self._field_mapping.end_conversion()
        self._data.end_conversion(multi=multi, extracted_file=e_file)

    def iterate(self, file):
        with open(file, 'r') as f:
            print(f"\tConverting {str(file).rpartition('/')[-1]}")
            for i, (path, t) in enumerate(self.iterator(f, self.mapping)):
                if i == 0:
                    self._field_mapping.default(self._data.struct)
                self.mapping[path](self._data.struct, t)
    
class SingleDatasetConverter(Converter):

    def convert(self):
        try:
            
            file = self.path.resolve()
            self.start_conversion(file, file.name)
            self.iterate(file)
            self.end_conversion()
        
        except Exception as e:
            self._data.handle_error()
            del self._data, self._field_mapping
            raise e

class SingleHierarchicalCompressedDatasetConverter(Converter):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.file = zipfile.ZipFile(self.path)
        for x in self.file.namelist():
            if (x.startswith("processes/") or x.find("/processes/") != -1) and x.endswith(".xml"):
                name = '.'.join(str(self.path).split('.')[:-1]).split('/')[-1]
                self._extracted_path = Path(self.save_path, name)
                self.path = Path(self._extracted_path, x.split("processes/")[0])
                break
        
    def convert(self):
        try:
            self._extracted_path.mkdir(exist_ok=True)
            self.file.extractall(str(self._extracted_path))
            processes = []
            for ve in self._valid_extensions[1:]:
                processes.extend(list(Path(self.path, 'processes').glob('*'+ve)))
            
            for i, file in enumerate(processes):
                self.start_conversion(file, file.name)
                self.iterate(file)
                self.end_conversion(e_file=self._extracted_path)
                
        except Exception as e:
            self.file.close()
            self._data.handle_error(self._extracted_path)
            del self._data, self._field_mapping
            raise e

class MultipleSingleDatasetConverter(Converter):

    def convert(self):
        try:
            files = []
            for ve in self._valid_extensions:
                files.extend(list(self.path.glob('*'+ve)))
                
            for i, file in enumerate(files):
                self.start_conversion(file, file.name)
                self.iterate(file)
                self.end_conversion()
                
        except Exception as e:
            self._data.handle_error()
            del self._data, self._field_mapping
            raise e

class MultipleHierarchicalCompressedDatasetConverter(Converter):
    
    def _get_processes(self, file):
        self.file = zipfile.ZipFile(file)
        for x in self.file.namelist():
            if (x.startswith("processes/") or x.find("/processes/") != -1) and x.endswith(".xml"):
                name = '.'.join(str(file).split('.')[:-1]).split('/')[-1]
                self._extracted_path = Path(self.save_path, name)
                self.path = Path(self._extracted_path, x.split("processes/")[0])
                break
        
    def convert(self):
        try:
            files = []
            for ve in self._valid_extensions[:1]:
                files.extend(list(self.path.glob('*'+ve)))
            for i, zip_file in enumerate(files):
                self._get_processes(zip_file)
                self._extracted_path.mkdir(exist_ok=True)
                self.file.extractall(str(self._extracted_path))
                processes = []
                for ve in self._valid_extensions[1:]:
                    processes.extend(list(Path(self.path, 'processes').glob('*'+ve)))
                
                for j, xml_file in enumerate(processes):
                    self.start_conversion(xml_file, xml_file.name)
                    self.iterate(xml_file)
                    if j < len(processes)-1:
                        self.reset_conversion()
                    else:
                        self.end_conversion(e_file=self._extracted_path)
                        
        except Exception as e:
            self.file.close()
            self._data.handle_error(self._extracted_path)
            del self._data, self._field_mapping
            raise e
            
class MultipleDatasetConverter(Converter):

    def convert(self):
        try:
            files = []
            for ve in self._valid_extensions:
                files.extend(list(self.path.glob('*'+ve)))
                
            for i, file in enumerate(files):
                if i == 0:
                    self.start_conversion(file, 'ILCD')
                else:
                    self.start_conversion(file, 'ILCD', multi=True)
                self.iterate(file)
                if i < len(files)-1:
                    self.reset_conversion()
                else:
                    self.end_conversion(multi=True)
        
        except Exception as e:
            self._data.handle_error()
            del self._data, self._field_mapping
            raise e

class ConverterFactory:

    @staticmethod
    def get_converter(input_, output, mode, path, save_path, hash_):
        InputConfig = {
            "EcoSpold2": ECS2InputConfig,
            "ILCD1": ILCD1InputConfig
            }.get(input_[0])
        OutputConfig = {
            "ILCD1": ILCD1OutputConfig,
            "EcoSpold2": ECS2OutputConfig
            }.get(output[0])
        ef = (input_[1], output[1])
        args = (path, save_path, hash_,      # Paths
                ef,                          # EF Mapping Config
                InputConfig,                 # Input Config
                OutputConfig)                # Output Config
        if mode == "to file":
            if path.is_file():
                if path.suffix not in InputConfig.valid_extensions:
                    raise OSError(
                        f'{path} is not a valid {input_} file path, must end with one of: {", ".join(InputConfig.valid_extensions)}')
                if input_[0] == 'ILCD1' and output[0] == 'EcoSpold2':
                    ILCD1Helper.is_valid(path)
                    return SingleHierarchicalCompressedDatasetConverter(*args)
                return SingleDatasetConverter(*args)
            elif path.is_dir():
                if input_[0] == 'ILCD1' and output[0] == 'EcoSpold2':
                    return MultipleHierarchicalCompressedDatasetConverter(*args)
                return MultipleSingleDatasetConverter(*args)
            else:
                raise OSError(f'{path} is not a valid path for conversion')    
        elif mode == "to database":
            if not path.is_dir():
                raise OSError(f'{path} is not a valid directory path')
            if input_[0] == 'EcoSpold2' and output[0] == 'ILCD1':
                warnings.warn('Conversion of EcoSpold2 to ILCD1 in database mode: different sets of property values for the same flow are converted to different versions of the same flow (and named as such). This is an ILCD1 feature not easily recognized by softwares, so this type of conversion is not recommended. It is recommended to use the mode "to file" or change the Converter attribute "convert_properties" to False', UserWarning)
            if input_[0] == 'ILCD1' and output[0] == 'EcoSpold2':
                return MultipleHierarchicalCompressedDatasetConverter(*args)
            return MultipleDatasetConverter(*args)


def get_converter(input_: tuple, output: tuple, path: str, save_path: str, mode: str, hash_ = ''):

    VALID = {
        "type": {"EcoSpold2", "ILCD1"},
        "ef_type": {"EcoSpold2": {"ecoinvent3.7"},
                    "ILCD1": {"EF3.0"}},
        "mode": {"to file", "to database"}
    }

    for x, n in ((input_[0], VALID['type']), 
                 (output[0], VALID['type']), 
                 (input_[1], VALID['ef_type'][input_[0]]), 
                 (output[1], VALID['ef_type'][output[0]]), 
                 (mode, VALID['mode'])):
        if not isinstance(x, str):
            raise TypeError(
                f"\tInvalid input type '{type(x)}'. Must be a string")
        if x not in n:
            vv = [f"'{l}'" for l in n]
            raise AttributeError(
                f"\tInvalid conversion input '{x}'. Must be one of {', '.join(vv)}")

    if input_[0] == output[0]:
        raise ValueError(f"Invalid conversion between equal types {input_[0]} and {output[0]}")

    path = Path(path)
    if not path.exists():
        raise OSError(
            f'{path} is not a valid {"directory" if path.is_dir() else "file"} path')
    save_path = Path(save_path)
    if not save_path.is_dir():
        raise OSError(f'{save_path} is not a valid directory path')

    return ConverterFactory.get_converter(input_, output, mode, path, save_path, hash_)

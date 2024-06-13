
from pathlib import Path, PosixPath
from collections.abc import Iterator

from dataclasses import asdict
import warnings
import inspect

from .formats import (
    ECS2InputConfig,
    ILCD1OutputConfig,
    OLCAILCD1OutputConfig,
    ECS2OutputConfig,
    ILCD1InputConfig,
    OLCAILCD1InputConfig,
    DefaultMappingConfig,
    InputTemplate,
    OutputTemplate
)
from .conversions import (
    MappingFactory,
    Print
    )
from .data_structures import (
    StructureFactory,
    StructureTemplate
    )
class Converter:

    def __init__(self,
                 path,
                 save_path,
                 input_config,
                 output_config,
                 mapping_config
                 ):

        self.__input_config = input_config
        self.__output_config = output_config

        # General necessary info
        self._names = (input_config.name, output_config.name)
        self._mfactory = MappingFactory(self._names, (
            getattr(input_config, 'ef_mapping', None),
            getattr(output_config, 'ef_mapping', None)))
        self._sfactory = StructureFactory(self._names[1])
        self.__hash = output_config.hash_
        
        # Set inputs that can be changed
        self._input_manager = input_config.input_manager(path)
        self._iterator = input_config.iterator
        self._elem_flow_mapping = None # Default is assigned at the mapping creation
        self._mapping_config = mapping_config
        self._output_version = output_config.version
        self._output_struct = output_config.output_structure
        self._output_manager = output_config.output_manager
        self._initial_info = input_config.initial_info

        # Public paths
        self.path = path  # CHANGE
        self.save_path = save_path  # CHANGE

        # Public options for conversion
        self.convert_additional_fields = False # CHANGE
        self.quiet = True
        self._start_configurations(input_config, output_config)
    
    ### Information for the user
        
    def __str__(self):
        return f"\nConverter from {self.__input_config.name} : {getattr(self.__input_config, 'ef_mapping', None)} "+\
                f"to {self.__output_config.name} : {getattr(self.__output_config, 'ef_mapping', None)}\n\n"+\
                "Mutable Variables:\n\t"+'\n\t'.join([f"{x.replace('_',' ').capitalize()}: {getattr(self, x).__class__.__name__ if not inspect.isclass(getattr(self, x)) else getattr(self, x).__name__}" for x in ('_input_manager', '_iterator', '_output_struct', '_output_manager', '_initial_info')])+\
                '\n\t' + '\n\t'.join([f"{x.replace('_',' ').capitalize()}: {getattr(self, x) if x == '_elem_flow_mapping' else asdict(getattr(self, x)())}" for x in ('_elem_flow_mapping', '_mapping_config')])+\
                f"\n\nOptions:\n\tQuiet mode: {self.quiet}\n\tConvert additional fields: {self.convert_additional_fields}\n\t"+\
                '\n\t'.join([f'[{x[0].split("_")[0]}] {"_".join(x[0].split("_")[1:]).replace("_"," ").capitalize()} : {getattr(self, x[1])}' for x in self._options]) + '\n'

    ### Changeable variables (elementary flow mapping file, iterator, input file manager, mapping)

    def __check_new_mapping(self, path):
        p = Path(path)
        if p.suffix not in ('.csv', '.json'):
            raise OSError(
                f'{p} is not a valid mapping path. Must be a .csv or .json')
        return p

    @property
    def elem_flow_mapping(self): return self._elem_flow_mapping

    @elem_flow_mapping.setter
    def elem_flow_mapping(self, mapping_path):
        self._elem_flow_mapping = self.__check_new_mapping(mapping_path)

    @property
    def output_version(self): return self._output_version

    @output_version.setter
    def output_version(self, version):
        self._output_version = version

    @property
    def iterator(self): return self._iterator

    @iterator.setter
    def iterator(self, iter_):
        if isinstance(iter_, Iterator):
            self._iterator = iter_
        else:
            raise TypeError('Iterator must inherit from the Iterator class')
    
    @property
    def input_manager(self): return self._input_manager

    @input_manager.setter
    def input_manager(self, input_manager):
        if isinstance(input_manager, InputTemplate):
            self._input_manager = input_manager
        else:
            raise TypeError('Input Manager must inherit from the InputTemplate class')

    @property
    def mapping(self): return self._mapping_config.mapping_class
    
    @mapping.setter
    def mapping(self, mapping_dict):
        self._mapping_config = DefaultMappingConfig(**mapping_dict)

    @property
    def output_manager(self): return self._output_manager

    @output_manager.setter
    def output_manager(self, output_manager):
        if isinstance(output_manager, OutputTemplate):
            self._output_manager = output_manager
        else:
            raise TypeError('Input Manager must inherit from the InputTemplate class')

    @property
    def output_structure(self): return self._output_struct

    @output_structure.setter
    def output_structure(self, output_structure):
        if isinstance(output_structure, StructureTemplate):
            self._output_struct = output_structure
        else:
            raise TypeError('Input Manager must inherit from the InputTemplate class')

    @property
    def initial_info(self): return self._initial_info
    
    @initial_info.setter
    def initial_info(self, initial_info):
        self._initial_info = initial_info
        
    ### Configuration start
    
    # Add-options (configurations) [start, add and apply]
    def _start_configurations(self, input_config, output_config):
        self._options = []
        for conf in (input_config, output_config):
            for name, value in conf.add_options.items():
                self._options.append((conf.name + '_' + name, name, value[1:]))
                setattr(self, name, value[0])
    
    def __setattr__(self, key, value):
        if hasattr(self, '_options'):
            if (key in [x[1] for x in self._options] or key in ('quiet', 'convert_additional_fields')) and value not in (True, False):
                raise TypeError(f"Option '{key}' only accepts booleans (True or False). Received '{value}' of type {type(value)}")
        super().__setattr__(key, value)

    def _apply_configurations(self, conf_type):
        for _, name, (type_, func) in self._options:
            if type_ == conf_type:
                if type_ == 'general_option':
                    func(getattr(self, name))
                elif type_ == 'mapping_option':
                    func(type(self._field_mapping), getattr(self, name))

    ### Information setting to mapping and data format

    def _set_format(self):
        if self._names[0] == self._names[1]:
            type(self._data).only_elem_flows = True
        type(self._data)._hash = self.__hash

    def _set_field_mapping(self, file): # Set fields relative to the overall conversion
        type(self._field_mapping)._convert_additional_fields = self.convert_additional_fields
        type(self._field_mapping)._file_reference = file
        self._field_mapping.set_mappings(self._elem_flow_mapping)
    
    ### Gathering of information from file to populate variables in mapping and data
    
    def _get_pre_instance_file_information(self, file):
        self.file_info = {}
        self._o_version = getattr(self, '_version', None)
        with open(file, 'r') as f:
            for i, (path, t) in enumerate(self.iterator(f, self._initial_info)):
                gmp = self._initial_info[path]
                if gmp[0] not in self.file_info:
                    self.file_info[gmp[0]] = gmp[1](t) if 'list' not in gmp[0] else [gmp[1](t)]
                elif 'list' in gmp[0]: # This verification takes into account fields that can have many languages but only 'one' data
                    self.file_info[gmp[0]].append(gmp[1](t))
        self._version = self.file_info.pop('version', None)
        self._filename = self.file_info.pop('filename', None)
        
    def _set_post_instance_file_information(self):
        for field in self.file_info:
            if field[0] == 'mapping':
                setattr(type(self._field_mapping), field[1], self.file_info[field])
            # elif field[0] == 'format':
            #     setattr(self._data, field[1], self.file_info[field])
        self._field_mapping.set_file_info(self._input_manager._input_file, self._data._output_file)

    ### Conversion hooks

    def start_conversion(self, file):
        Print.quiet = self.quiet
        self._apply_configurations('general_option')
        self._get_pre_instance_file_information(file)
        if not hasattr(self, '_data'):
            self._data = self._output_manager(self.save_path, self.save_path, self._sfactory.get_structure(self._output_struct, self._output_version))
            self._set_format()
        if (self._o_version != self._version) or (self._o_version is None and self._version is None):
            # self._data.struct = self._sfactory.get_structure(self._output_struct, self._version)()
            self._field_mapping = self._mfactory.get_mapping(self._mapping_config, self._version)
            self._set_field_mapping(file)
        self._field_mapping.set_output_class_defaults(self._data.struct)
        if not self._data.multi_files:
            self._data.filename = self._filename # The 'set_post' requires this to be initialized for the log filename
            self._data.start_conversion()
        self._set_post_instance_file_information()
        self._apply_configurations('mapping_option')
        self.__mapping = self._field_mapping.mapping()
        self._field_mapping.start_conversion()
        
    def reset_conversion(self):
        self._field_mapping.reset_conversion()
        self._data.reset_conversion()

    def end_conversion(self):
        self._field_mapping.end_conversion()
        self._data.end_conversion()

    def iterate(self, file):
        with open(file, 'r') as f:
            print(f"\tConverting {str(file).rpartition('/')[-1]}")
            for i, (path, t) in enumerate(self.iterator(f, self.__mapping)):
                if i == 0:
                    self._field_mapping.default(self._data.struct) # Struct has to be a class
                self.__mapping[path](self._data.struct, t)
    
    def convert(self, type_):
        
        if type_ == 'to_database' and self._names[0] == 'EcoSpold2' and self._names[1] in ('ILCD1', 'OLCAILCD1'):
            warnings.warn('Conversion of EcoSpold2 to ILCD1 in database mode: different sets of property values for the same flow are converted to different versions of the same flow (and named as such). This is an ILCD1 feature not easily recognized by softwares, so this type of conversion is not recommended. It is recommended to use the mode "to file" or change the Converter attribute "convert_properties" to False', UserWarning)
    
        try:
            for file, is_last in self._input_manager.get_files():
                self.start_conversion(file)
                self.iterate(file)
                if is_last or type_ == "to_file":
                    self.end_conversion()
                else:
                    self.reset_conversion()
        except Exception as e:
            if 'file' in locals():
                if not isinstance(file, PosixPath):
                    file.close()
            for name in ('_input_manager', '_data'):
                if hasattr(self, name):
                    inst = getattr(self, name)
                    inst.handle_error()
                    del inst
            if hasattr(self, '_field_mapping'):
                self._field_mapping.delete()
                del self._field_mapping
            raise e
            
    
# class SingleDatasetConverter(Converter):

#     def convert(self):
#         try:
            
#             file = self.path.resolve()
#             self.start_conversion(file, file.name)
#             self.iterate(file)
#             self.end_conversion()
        
#         except Exception as e:
#             self._data.handle_error()
#             del self._data, self._field_mapping
#             raise e

# class SingleHierarchicalCompressedDatasetConverter(Converter):
        
#     def convert(self):
#         try:
#             for i, file in enumerate(self._input_manager.get_files()):
#                 self.start_conversion(file, file.name)
#                 self.iterate(file)
#                 self.end_conversion()
                
#         except Exception as e:
#             self.file.close()
#             self._data.handle_error(self._extracted_path)
#             del self._data, self._field_mapping
#             raise e

# class MultipleSingleDatasetConverter(Converter):

#     def convert(self):
#         try:
                
#             for i, file in enumerate(self._input_manager.get_files()):
#                 self.start_conversion(file, file.name)
#                 self.iterate(file)
#                 self.end_conversion()
                
#         except Exception as e:
#             self._data.handle_error()
#             del self._data, self._field_mapping
#             raise e

# class MultipleHierarchicalCompressedDatasetConverter(Converter):
    
#     def _get_processes(self, file):
#         self.file = zipfile.ZipFile(file)
#         for x in self.file.namelist():
#             if (x.startswith("processes/") or x.find("/processes/") != -1) and x.endswith(".xml"):
#                 name = '.'.join(str(file).split('.')[:-1]).split('/')[-1]
#                 self._extracted_path = Path(self.save_path, name)
#                 self.path = Path(self._extracted_path, x.split("processes/")[0])
#                 break
        
#     def convert(self):
#         try:
#             files = []
#             for ve in self._valid_extensions[:1]:
#                 files.extend(list(self.path.glob('*'+ve)))
#             for i, zip_file in enumerate(files):
#                 self._get_processes(zip_file)
#                 self._extracted_path.mkdir(exist_ok=True)
#                 self.file.extractall(str(self._extracted_path))
#                 processes = []
#                 for ve in self._valid_extensions[1:]:
#                     processes.extend(list(Path(self.path, 'processes').glob('*'+ve)))
                
#                 for j, xml_file in enumerate(processes):
#                     self.start_conversion(xml_file, xml_file.name)
#                     self.iterate(xml_file)
#                     if j < len(processes)-1:
#                         self.reset_conversion()
#                     else:
#                         self.end_conversion(e_file=self._extracted_path)
                        
#         except Exception as e:
#             self.file.close()
#             self._data.handle_error(self._extracted_path)
#             del self._data, self._field_mapping
#             raise e
            
# class MultipleDatasetConverter(Converter):

#     def convert(self):
#         try:
#             files = []
#             for ve in self._valid_extensions:
#                 files.extend(list(self.path.glob('*'+ve)))
                
#             for i, file in enumerate(files):
#                 if i == 0:
#                     self.start_conversion(file, 'ILCD')
#                 else:
#                     self.start_conversion(file, 'ILCD', multi=True)
#                 self.iterate(file)
#                 if i < len(files)-1:
#                     self.reset_conversion()
#                 else:
#                     self.end_conversion(multi=True)
        
#         except Exception as e:
#             self._data.handle_error()
#             del self._data, self._field_mapping
#             raise e

class ConverterFactory:

    @staticmethod
    def get_converter(input_, output, path, save_path, hash_):
        
        InputConfig = {
            "EcoSpold2": ECS2InputConfig,
            "ILCD1": ILCD1InputConfig,
            "OLCAILCD1": OLCAILCD1InputConfig
            }.get(input_[0])
        InputConfig.ef_mapping = input_[1]
        
        OutputConfig = {
            "ILCD1": ILCD1OutputConfig,
            "EcoSpold2": ECS2OutputConfig,
            "OLCAILCD1": OLCAILCD1OutputConfig
            }.get(output[0])
        OutputConfig.hash_ = hash_
        OutputConfig.ef_mapping = output[1]
        
        args = (path, save_path,             # Paths
                InputConfig,                 # Input Config
                OutputConfig,                # Output Config
                DefaultMappingConfig)
        
        return Converter(*args)
        
        # if mode == "to file":
        #     if path.is_file():
        #         if path.suffix not in InputConfig.valid_extensions:
        #             raise OSError(
        #                 f'{path} is not a valid {input_} file path, must end with one of: {", ".join(InputConfig.valid_extensions)}')
        #         if input_[0] in ('ILCD1', 'OLCAILCD1'):
        #             ILCD1Helper.is_valid(path)
        #             return SingleHierarchicalCompressedDatasetConverter(*args)
        #         return SingleDatasetConverter(*args)
        #     elif path.is_dir():
        #         if input_[0] in ('ILCD1', 'OLCAILCD1'):
        #             return MultipleHierarchicalCompressedDatasetConverter(*args)
        #         return MultipleSingleDatasetConverter(*args)
        #     else:
        #         raise OSError(f'{path} is not a valid path for conversion')
        # elif mode == "to database":
        #     if not path.is_dir():
        #         raise OSError(f'{path} is not a valid directory path')
        #     if input_[0] == 'EcoSpold2' and output[0] in ('ILCD1', 'OLCAILCD1'):
        #         warnings.warn('Conversion of EcoSpold2 to ILCD1 in database mode: different sets of property values for the same flow are converted to different versions of the same flow (and named as such). This is an ILCD1 feature not easily recognized by softwares, so this type of conversion is not recommended. It is recommended to use the mode "to file" or change the Converter attribute "convert_properties" to False', UserWarning)
        #     if input_[0] in ('ILCD1', 'OLCAILCD1'):
        #         return MultipleHierarchicalCompressedDatasetConverter(*args)
        #     return MultipleDatasetConverter(*args)


def get_converter(input_: tuple, output: tuple, path: str, save_path: str, hash_ = ''):

    VALID = {
        "type": {"EcoSpold2", "ILCD1", "OLCAILCD1"},
        "ef_type": {"EcoSpold2": {"ecoinvent3.7"},
                    "ILCD1": {"EF3.0"},
                    "OLCAILCD1": {"EF3.0"}}
    }

    for x, n in ((input_[0], VALID['type']), 
                 (output[0], VALID['type']), 
                 (input_[1], VALID['ef_type'][input_[0]]), 
                 (output[1], VALID['ef_type'][output[0]])):
        if not isinstance(x, str):
            raise TypeError(
                f"\tInvalid input type '{type(x)}'. Must be a string")
        if x not in n and input_[0] != output[0]:
            vv = [f"'{l}'" for l in n]
            raise AttributeError(
                f"\tInvalid conversion input '{x}'. Must be one of {', '.join(vv)}")

    # Conversion between the same file are possible now for converting only elementary flows
    # if input_[0] == output[0]:
    #     raise ValueError(f"Invalid conversion between equal types {input_[0]} and {output[0]}")

    path = Path(path)
    if not path.exists():
        raise OSError(
            f'{path} is not a valid {"directory" if path.is_dir() else "file"} path')
    save_path = Path(save_path)
    if not save_path.is_dir():
        raise OSError(f'{save_path} is not a valid directory path')

    return ConverterFactory.get_converter(input_, output, path, save_path, hash_)

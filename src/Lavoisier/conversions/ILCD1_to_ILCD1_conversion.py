#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  3 22:46:15 2022

@author: jotape42p
"""
from abc import ABC
from .utils import (
    FieldMapping
)
from .units import ilcd_unit_to_fp, olcailcd_unit_to_fp
from .utils import ensure_list
from pathlib import Path
import shutil
import logging
import xmltodict
from copy import deepcopy
import warnings

# TODO make it so that the output flow is respected (copy and paste every file in the folders

'''
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
'''

class ILCD1ToILCD1ElementaryFlowConversion:
    
    default_files = None
    elem_flow_mapping = None
    ilcd_extracted_dir = None # TODO now instead of receiving the file.parent.parent, it only receives the file in the _file_reference variable
    save_dir = None
    
    exc_holder = None
    math_holder = None
    math_rel = None
    
    # [!] Fluxo no OpenLCA sempre está de acordo com a unidade padrão no unitgroups
    # [!] Fluxo do OpenLCA é sempre convertido para a unidade/propriedade padrão do ILCD
    # Há o caso de que a unidade foi modificada e não é a esperada, mas pode estar no flowProperties
    def __init__(self, x):
        n = type(self).elem_flow_mapping.get(x['referenceToFlowDataSet']['@refObjectId'], None)
        self.get_uri(x) # Old uri   
        self.nx = deepcopy(x)
        if n is not None:
            if n['MapType'] not in ("NO_MATCH_MAPPING", "NO MATCH"):
                
                self.save_original(n['TargetFlowUUID']+'.xml')
                
                self.nx['referenceToFlowDataSet']['@refObjectId'] = n['TargetFlowUUID']
                self.nx['referenceToFlowDataSet']['@uri'] = '../flows/'+n['TargetFlowUUID']+'.xml'
                self.nx['referenceToFlowDataSet'].pop('@version', None)
                self.nx['referenceToFlowDataSet']['shortDescription'] = self.nx['referenceToFlowDataSet']['shortDescription'] | {'#text': n['TargetFlowName']} # TODO common

                conversionFactor = float(n['ConversionFactor']) if n['ConversionFactor'] not in ("", "n/a") else 1.0
                
                # [!] The olca parameters aren't changed
                ounit = self.get_unit(self.nx.get('@unitId'))
                iunit = n['SourceUnit']
                nunit = n['TargetUnit']

                print(ounit, iunit, nunit)

                # 1ª Conversão de unidades [OLCA to MainILCD (kJ to MJ for CO2)]
                if 'olca' in list(ounit):
                    amount = float(self.nx['@amount']) * ounit['olca'][0][1]
                    unit = ounit['olca'][0][0]
                else:
                    amount = float(self.nx['resultingAmount'])
                    unit = ounit['main'][0][0]

                if iunit != nunit:
                    info = ilcd_unit_to_fp[nunit]
                    print(info)
                    self.save_original(info[0]+'.xml', dir_='flowproperties', type_='flow property')
                    self.save_original(info[1]+'.xml', dir_='unitgroups', type_='unit group')
                
                # 2ª Conversão de unidades [MainILCD to Source (MJ to kg for CO2)]
                # 3ª Conversão de unidades [Source to Target (kg to kBq for example)]
                if nunit == unit:
                    self.nx['resultingAmount'] = amount
                    if self.nx.get('referenceToVariable'):
                        self.nx['referenceToVariable'] = self.get_var(self.nx['referenceToVariable'], unit, nunit, conversionFactor, amount, conversion=False)
                elif iunit == unit:
                    self.nx['resultingAmount'] = amount * conversionFactor
                    if self.nx.get('@amount'):
                        self.nx['@amount'] = amount * conversionFactor
                        info = olcailcd_unit_to_fp[nunit]
                        self.nx['@unitId'] = info[1]
                        self.nx['@propertyId'] = info[0]
                    if self.nx.get('uncertaintyDistributionType'):
                        self.nx = self.get_unc(self.nx, self.nx['resultingAmount'], conversionFactor)
                    if self.nx.get('referenceToVariable'):
                        self.nx['referenceToVariable'] = self.get_var(self.nx['referenceToVariable'], unit, nunit, conversionFactor, amount)
                elif iunit in (u[0] for u in ounit['sec']):
                    factor = conversionFactor * [u[1] for u in ounit['sec'] if u[0]==iunit][0]
                    self.nx['resultingAmount'] = amount * factor
                    if self.nx.get('@amount'): # Align so both are equal
                        self.nx['@amount'] = amount * factor
                        info = olcailcd_unit_to_fp[nunit]
                        self.nx['@unitId'] = info[1]
                        self.nx['@propertyId'] = info[0]
                    if self.nx.get('uncertaintyDistributionType'):
                        self.nx = self.get_unc(self.nx, self.nx['resultingAmount'], factor)
                    if self.nx.get('referenceToVariable'):
                        self.nx['referenceToVariable'] = self.get_var(self.nx['referenceToVariable'], unit, nunit, factor, amount)
                else:
                    self.get_uri(x)
                    self.save_file()
                    logging.warning(
                        "Flow not converted due to lack of unit correspondence")
                    
            else:
                self.save_file()
                logging.warning(
                    "Flow not converted due to lack of elementary flow correspondence in the mapping file")
        else:
            self.save_file()
            logging.info(
                "Flow not converted as the flow is not present on the elementary flow mapping file")
            
        self.field = type(self).exc_holder.get_class('exchange')(self.nx)
        

    def get_var(self, var_name, unit, nunit, factor, amount, conversion=True):
        
        if conversion:
            # var 1: unit conversion
            var1 = {'@name': '__'+unit+'_to_'+nunit+'__',
                    'meanValue': factor}
            type(self).math_rel.append(var1)
        
            # var 2: temp_olca_param
            vars_ = ensure_list(type(self).math_rel)
            ivar, var2 = [(i,v) for i,v in enumerate(vars_) if v['@name']==var_name][0]
            if 'temp_olca_param' in var_name:
                var_name = var_name.replace('temp_olca_param', 'p_')
            var2['@name'] = name = var_name+'_from_'+unit+'_to_'+nunit
            var2['meanValue'] = amount
            var2['formula'] = '(' + var2['formula'] + ')*'+'__'+unit+'_to_'+nunit+'__'
            if var2.get('uncertaintyDistributionType'):
                var2 = self.get_unc(var2, var2['meanValue'], factor)
            type(self).math_rel[ivar] = var2
        
        else:
            vars_ = ensure_list(type(self).math_rel)
            ivar, var2 = [(i,v) for i,v in enumerate(vars_) if v['@name']==var_name][0]
            if 'temp_olca_param' in var_name:
                var_name = var_name.replace('temp_olca_param', 'p_')
            var2['@name'] = name = var_name
            type(self).math_rel[ivar] = var2
            
        return name

    def get_unc(self, x, m, f):
        type_ = x['uncertaintyDistributionType']
        if type_ == 'lognormal':
            pass # Nothing changes with multiplication
        elif type_ == 'normal':
            # X * f -> Var(Xf) = Var(X) * f**2 -> STD(Xf) = STD(X) * f
            x['relativeStandardDeviation95In'] = std95 = float(x['relativeStandardDeviation95In'])/2 * f
            x['minimumAmount'] = m - std95
            x['maximumAmount'] = m + std95
        elif type_ in ('triangular', 'uniform'):
            x['minimumAmount'] = float(x['minimumAmount']) * f
            x['maximumAmount'] = float(x['maximumAmount']) * f
        elif type_ == 'undefined':
            x['relativeStandardDeviation95In'] = std95 = float(x['relativeStandardDeviation95In']) * f
            x['minimumAmount'] = (float(x['minimumAmount']) + float(x['maximumAmount'])) * f/2 - std95
            x['maximumAmount'] = (float(x['minimumAmount']) + float(x['maximumAmount'])) * f/2 + std95
        return x

    def get_uri(self, x, r=('referenceToFlowDataSet', 'flows/')):
        uris = []
        ref = x[r[0]]
        if ref.get('@uri'): uris.append(ref['@uri'].replace('../', ''))
        uris.append(r[1]+ref['@refObjectId']+'.xml')
        uris.append(r[1]+ref['@refObjectId']+'_'+ref.get('@version', '')+'.xml')
        for uri in uris:
            if Path(type(self).ilcd_extracted_dir, uri).is_file():
                self.uri = uri
                break
        else:
            raise Exception(f"URI not found for flow {ref['@refObjectId']}")

    def get_unit(self, olca_unit_id=None):
        def get_struct(f, nms):
            structure = xmltodict.parse(f.read())
            structure = structure[list(structure)[0]]
            nms = [x for x in list(structure) if structure[x] == nms][0].split(':')[-1]
            return structure, nms
        
        with open(Path(type(self).ilcd_extracted_dir, self.uri), 'r') as f:
            file, fn = get_struct(f, "http://lca.jrc.it/ILCD/Flow")
        main = file[fn+':flowInformation'][fn+':quantitativeReference'][fn+':referenceToReferenceFlowProperty']
        units = []
        
        for fp in ensure_list(file[fn+':flowProperties'][fn+':flowProperty']):
            self.get_uri(fp, (fn+':referenceToFlowPropertyDataSet', 'flowproperties/'))
            
            name = 'main' if fp['@dataSetInternalID'] == main else 'sec'
            mv = fp[fn+':meanValue']
            
            with open(Path(type(self).ilcd_extracted_dir, self.uri), 'r') as f:
                file, n = get_struct(f, "http://lca.jrc.it/ILCD/FlowProperty")
            u = file[n+':flowPropertiesInformation'][n+':quantitativeReference']
            self.get_uri(u, (n+':referenceToReferenceUnitGroup', 'unitgroups/'))
            
            with open(Path(type(self).ilcd_extracted_dir, self.uri), 'r') as f:
                file, n = get_struct(f, "http://lca.jrc.it/ILCD/UnitGroup")
            u = file[n+':unitGroupInformation'][n+':quantitativeReference'][n+':referenceToReferenceUnit']
            
            for ug in file[n+':units'][n+':unit']:
                if olca_unit_id:
                    if ug['@olca:unitId'] == olca_unit_id:
                        units.append(('olca', ug[n+':name'], float(ug[n+':meanValue'])))
                if ug['@dataSetInternalID'] == u:
                    units.append((name, ug[n+':name'], float(mv)))
            if not units:
                raise Exception("Unit not found")
        
        from collections import defaultdict
        units_ = defaultdict(list)
        for unit in units:
            units_[unit[0]].append(unit[1:])
        return units_

    def save_file(self, type_='flows'):
        Path(type(self).save_dir, type_).mkdir(exist_ok=True)
        shutil.copy(Path(type(self).ilcd_extracted_dir, self.uri),
                    Path(type(self).save_dir, type_))
        
    def save_original(self, id_, dir_='flows', type_='elementary flow'):
        Path(type(self).save_dir, dir_).mkdir(exist_ok=True)
        shutil.copy(
            Path(Path(__file__).parent.parent.resolve(),
                 type(self).default_files[type_],
                 id_),
            Path(type(self).save_dir, dir_))

class ILCD1ToILCD1BasicFieldMapping(FieldMapping, ABC):

    # Conversion Defaults
    _default_language = 'en'

    # Converter/Factory Defaults
    _default_files = None
    _default_elem_mapping = None
    _ilcd_extracted_dir = None
    _default_class_mapping = Path("Mappings/ilcd1_to_ecs2_classes.json")

    # Configuration Defaults
    _convert_additional_fields = True

    def set_mappings(self, ef_map):
        self._elem_mapping = self._dict_from_file(
            ef_map or type(self)._default_elem_mapping, 'SourceFlowUUID')
        self.ElementaryFlowConversion.elem_flow_mapping = self._elem_mapping

    def __init__(self):
        self.ElementaryFlowConversion = ILCD1ToILCD1ElementaryFlowConversion

    def start_conversion(self):
        self.ElementaryFlowConversion.default_files = type(self)._default_files
        self.ElementaryFlowConversion.ilcd_extracted_dir = type(self)._ilcd_extracted_dir

    def end_conversion(self):
        self.get_statistics()

    def reset_conversion(self):
        pass

    def set_file_info(self, path, save_path):
        self.ElementaryFlowConversion.save_dir = Path(save_path, 'ILCD-algorithm')

    def set_output_class_defaults(self, cl_struct):
        self.ElementaryFlowConversion.exc_holder = cl_struct.exchanges
        self.ElementaryFlowConversion.math_holder = cl_struct.mathematicalRelations

class ILCD1ToILCD1FieldMapping(ILCD1ToILCD1BasicFieldMapping):

    # File pre-mapping attribute
    _flow_internal_refs = None

    def get_statistics(self):
        pass

    def set_file_info(self, *args):
        super().set_file_info(*args)

    def default(self, cl_struct):
        pass

    # Setting variables that help conversions that depend on more than one field
    def start_conversion(self):
        super().start_conversion()

    def reset_conversion(self, end=False):
        for var in self.ElementaryFlowConversion.math_rel:
            vp = self.ElementaryFlowConversion.math_holder.get_class('variableParameter')(var)
            setattr(self.ElementaryFlowConversion.math_holder, 'variableParameter', vp)
            
        if not end:
            super().reset_conversion()

    def end_conversion(self):
        self.reset_conversion(end=True)
        super().end_conversion()

    def place_index(self, x, i): # The correct way would be to redo the validation step so it can receive indexes and place one whenever necessary
        if '@lang' in list(x):
            i += 1
            return x | {'@index': i}
        for k,v in x.items():
            if isinstance(v, dict):
                x[k] = self.place_index(v, i)
            elif isinstance(v, list):
                n = []
                for f in v:
                    n.append(self.place_index(f, i))
                x[k] = n
        return x

    def mapping(self):
        _keys = {
            '/processDataSet/processInformation/dataSetInformation':
                lambda cl_struct, x: setattr(cl_struct, 'dataSetInformation', cl_struct.DataSetInformation(self.place_index(x, 0))),
            '/processDataSet/processInformation/quantitativeReference':
                lambda cl_struct, x: setattr(cl_struct, 'quantitativeReference', cl_struct.QuantitativeReference(self.place_index(x, 0))),
            '/processDataSet/processInformation/time':
                lambda cl_struct, x: setattr(cl_struct, 'time', cl_struct.Time(self.place_index(x, 0))),
            '/processDataSet/processInformation/technology':
                lambda cl_struct, x: setattr(cl_struct, 'technology', cl_struct.Technology(self.place_index(x, 0))),
            '/processDataSet/processInformation/geography':
                lambda cl_struct, x: setattr(cl_struct, 'geography', cl_struct.Geography(self.place_index(x, 0))),
            '/processDataSet/processInformation/mathematicalRelations': # Can't be set here due to changes
                lambda cl_struct, x: setattr(self.ElementaryFlowConversion, 'math_rel', x.get('variableParameter', [])), # Done later
            '/processDataSet/modellingAndValidation':
                lambda cl_struct, x: setattr(cl_struct, 'modellingAndValidation', cl_struct.ModellingAndValidation(self.place_index(x, 0))),
            '/processDataSet/administrativeInformation':
                lambda cl_struct, x: setattr(cl_struct, 'administrativeInformation', cl_struct.AdministrativeInformation(self.place_index(x, 0))),
            '/processDataSet/exchanges/exchange':
                lambda cl_struct, x: setattr(cl_struct.exchanges, 'exchange', self.ElementaryFlowConversion(self.place_index(x, 0)).field)
        }

        return _keys

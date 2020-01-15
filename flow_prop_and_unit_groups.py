# -*- coding: utf-8 -*-
"""
Created on Sun Jan 12 21:05:29 2020

Criação da database de propriedade de fluxos e unidades

@author: JP
"""

#auxílio na importação dos arquivos Ecospold2 (.spold)
import glob
#trabalho com json (leitura e escrita)
import json
#trabalho com xml (leitura e escrita)
from lxml import etree
#library de interação com o sistema
import os
#funções adicionais
import additional_functions as af
#trabalho com csv (leitura e escrita)
import csv

#inicialização
def inicialization(NS5, NS7, XMLNS, nsmap):    
    flow_prop_mapping(NS5, XMLNS, nsmap)
    unit_mapping(NS7, XMLNS, nsmap)

#inicialização e conversão dos arquivos de propriedades dos fluxos (somente usado uma vez para criar a database)
def flow_prop_mapping(NS5, XMLNS, nsmap):
    textPath = r'C:\Users\JP\Desktop\ILCD Conversion\ILCD - conversão\flow_properties'
    
    for f in glob.glob(os.path.join(textPath,'*.json')):
        with open(f) as json_file:
            file = json.load(json_file)
            
            #inicialização do dataset de propriedades do fluxo
            flowPropertyDataSet = etree.Element(NS5 + "flowPropertyDataSet", version = "1.1", nsmap = nsmap)
            
            #flowPropertyDataSet
            flowPropertiesInformation = af.subelement('flowPropertiesInformation', flowPropertyDataSet, NS5)
            administrativeInformationFP = af.subelement('adiministrativeInformation', flowPropertyDataSet, NS5)
            
            #flowPropertiesInformation[0]
            dataSetInformationFP = af.subelement('dataSetInformation', flowPropertiesInformation, NS5)
            
            UUIDFP = af.subelement('UUID', dataSetInformationFP, XMLNS)
            UUIDFP.text = file['@id']
            
            nameFP = af.subelement('name', dataSetInformationFP, XMLNS)
            nameFP.set('{http://www.w3.org/XML/1998/namespace}lang', 'en')
            nameFP.text = file['name']
            
            classificationInformationFP = af.subelement('classificationInformation', dataSetInformationFP, NS5)
            classificationFP = af.subelement('classification', classificationInformationFP, XMLNS)
            classFP = af.subelement('classFP', classificationFP, XMLNS)
            classFP.set('level',"0")
            classFP.set('classId', file['category'].get('@id'))
            classFP.text = file['category'].get('name')
            
            #flowPropertiesInformation[1]
            quantitativeReferenceFP = af.subelement('quanatitativeReference', flowPropertiesInformation, NS5)
            
            referenceToReferenceUnitGroup = af.subelement('referenceToReferenceUnitGroup', quantitativeReferenceFP, NS5)
            af.referencia(referenceToReferenceUnitGroup, 'unit group data set', file['unitGroup'].get('@id'), XMLNS, file['unitGroup'].get('name'))
            
            #administrativeInformation[0]
            dataEntryByFP = af.subelement('dataEntryBy', administrativeInformationFP, NS5)
            
            referenceToDataSetFormatFP = af.subelement('referenceToDataSetFormat', dataEntryByFP, XMLNS)
            af.referencia(referenceToDataSetFormatFP, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', XMLNS, 'ILCD Format', '01.01.000')
            
            #administrativeInformation[1]
            publicationAndOwnershipFP = af.subelement('publicationAndOwnership', administrativeInformationFP, NS5)
            
            dataSetVersionFP = af.subelement('dataSetVersionFP', publicationAndOwnershipFP, XMLNS)
            dataSetVersionFP.text = "00.00.000"
            
            permanentDataSetURIFP = af.subelement('permanentDataSetURI', publicationAndOwnershipFP, XMLNS)
            permanentDataSetURIFP.text = "http://openlca.org/ilcd/resource/flowproperties/" + file['@id']
            
            #salvar arquivo na pasta para database de propriedades de fluxos
            file_property = textPath + '\\' + UUIDFP.text + '.xml'
            with open(file_property, 'wb') as fproc:
                fproc.write(etree.tostring(flowPropertyDataSet, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))

#inicialização e conversão dos arquivos de unidades (somente usado uma vez para criar a database)
def unit_mapping(NS7, XMLNS, nsmap):
    textPath = r'C:\Users\JP\Desktop\ILCD Conversion\ILCD - conversão\unit_groups'
    
    for f in glob.glob(os.path.join(textPath,'*.json')):
        with open(f) as json_file:
            file = json.load(json_file)
            
            #inicialização do dataset de grupos de unidades
            unitGroupDataSet = etree.Element(NS7 + "unitGroupDataSet", version = "1.1", nsmap = nsmap)
            
            #unitGroupDataSet
            unitGroupInformation = af.subelement('unitGroupInformation', unitGroupDataSet, NS7)
            administrativeInformationUG = af.subelement('adiministrativeInformation', unitGroupDataSet, NS7)
            units = af.subelement('units', unitGroupDataSet, NS7)
            
            #unitGroupInformation[0]
            dataSetInformationUG = af.subelement('dataSetInformation', unitGroupInformation, NS7)
            
            UUIDUG = af.subelement('UUID', dataSetInformationUG, XMLNS)
            UUIDUG.text = file['@id']
            
            nameUG = af.subelement('name', dataSetInformationUG, XMLNS)
            nameUG.set('{http://www.w3.org/XML/1998/namespace}lang', 'en')
            nameUG.text = file['name']
            
            classificationInformationUG = af.subelement('classificationInformation', dataSetInformationUG, NS7)
            classificationUG = af.subelement('classification', classificationInformationUG, XMLNS)
            classUG = af.subelement('classFP', classificationUG, XMLNS)
            classUG.set('level',"0")
            classUG.set('classId', file['category'].get('@id'))
            classUG.text = file['category'].get('name')
            
            #unitGroupInformation[1]
            quantitativeReferenceUG = af.subelement('quanatitativeReference', unitGroupInformation, NS7)
            
            referenceToReferenceUnit = af.subelement('referenceToReferenceUnit', quantitativeReferenceUG, NS7)
            referenceToReferenceUnit.text = "0"
            
            #administrativeInformation[0]
            dataEntryByUG = af.subelement('dataEntryBy', administrativeInformationUG, NS7)
            
            referenceToDataSetFormatUG = af.subelement('referenceToDataSetFormat', dataEntryByUG, XMLNS)
            af.referencia(referenceToDataSetFormatUG, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', XMLNS, 'ILCD Format', '01.01.000')
            
            #administrativeInformation[1]
            publicationAndOwnershipUG = af.subelement('publicationAndOwnership', administrativeInformationUG, NS7)
            
            dataSetVersionUG = af.subelement('dataSetVersionFP', publicationAndOwnershipUG, XMLNS)
            dataSetVersionUG.text = "00.00.000"
            
            permanentDataSetURIUG = af.subelement('permanentDataSetURI', publicationAndOwnershipUG, XMLNS)
            permanentDataSetURIUG.text = "http://openlca.org/ilcd/resource/unitgroups/" + file['@id']
            
            #units[n] sendo n o número de unidades equivalentes [ex: Massa tem kg, g, ton ...]
            j=0
            for l_unit in file['units']:
                
                #Parte feita apenas uma vez para organizar uma lista de unidades para conversão
                with open('conversion.csv', mode='a') as conv_csv:
                    conv_csv_w = csv.writer(conv_csv, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
                    conv_csv_w.writerow([l_unit.get('name'), file['defaultFlowProperty'].get('@id'), file['defaultFlowProperty'].get('name'), file["@id"]])
                
                j = j+1
                unit = af.subelement('unit', units, NS7)
                
                if l_unit.get("referenceUnit") == True:
                    unit.set("dataSetInternalID", "0")
                else:
                    unit.set("dataSetInternalID", str(j))
                    
                nameUnit = af.subelement('name', unit, NS7)
                nameUnit.text = l_unit.get("name")
                
                meanValueUnit = af.subelement('meanValue', unit, NS7)
                meanValueUnit.text = str(l_unit.get('conversionFactor'))
            
            #salvar arquivo na pasta para database de propriedades de fluxos
            file_process = textPath + '\\' + UUIDUG.text + '.xml'
            with open(file_process, 'wb') as fproc:
                #print(file_process)
                fproc.write(etree.tostring(unitGroupDataSet, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))
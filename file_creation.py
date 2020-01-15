# -*- coding: utf-8 -*-
"""
Created on Sun Jan 12 21:12:51 2020

Criação dos arquivos de bibliografia e contatos

@author: JP
"""

#trabalho com xml (leitura e escrita)
from lxml import etree
#funções adicionais
import additional_functions as af
#library de interação com o sistema
import os

#criação do arquivo de cada um dos contatos    
def contacts(UUIDcontact, root, NS4, XMLNS, name, email):

    #contactDataSet
    contactInformation = af.subelement("contactInformation", root, NS4)
    administrativeInformationCT = af.subelement('administrativeInformation', root, NS4)
    
    #contactInformation[0]
    dataSetInformationCT = af.subelement('dataSetInformation', contactInformation, NS4)
    
    UUIDCT = af.subelement('UUID', dataSetInformationCT, XMLNS)
    UUIDCT.text = UUIDcontact
    
    NameCT = af.subelement('name', dataSetInformationCT, XMLNS)
    NameCT.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    NameCT.text = name
    
    emailCT = af.subelement('email', dataSetInformationCT, NS4)
    emailCT.text = email

    #administrativeInformation[0]
    dataEntryByCT = af.subelement('dataEntryBy', administrativeInformationCT, NS4)
    
    referenceToDataSetFormatCT = af.subelement('referenceToDataSetFormat', dataEntryByCT, XMLNS)
    af.referencia(referenceToDataSetFormatCT, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', XMLNS, 'ILCD Format', '01.01.000')
    
    #administrativeInformation[1]
    publicationAndOwnershipCT = af.subelement('publicationAndOwnership', administrativeInformationCT, NS4)
    
    dataSetVersionCT = af.subelement('dataSetVersion', publicationAndOwnershipCT, XMLNS)
    dataSetVersionCT.text = "00.00.000"
    
    permanentDataSetURICT = af.subelement('permanentDataSetURI', publicationAndOwnershipCT, XMLNS)
    #PROB: colocar o endereço do IBICT aqui
    permanentDataSetURICT.text = 'http://sicv.acv.ibict.br'
    
    #criar pasta se necessário
    try:
        os.mkdir("./ILCD-algorithm/contacts")
    except OSError:
        pass
    
    #salvar arquivo na pasta de contatos
    file_contact = "./ILCD-algorithm/contacts/" + UUIDcontact + ".xml"
    with open(file_contact, 'wb') as Flow:
        Flow.write(etree.tostring(root, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))
    
#criação do arquivo de cada uma das bibliografias
def sources(UUIDsource, root, NS6, XMLNS, citation):
    
    #sourceDataSet
    sourceInformation = af.subelement("sourceInformation", root, NS6)
    administrativeInformationSR = af.subelement('administrativeInformation', root, NS6)
    
    #sourceInformation[0]
    dataSetInformationSR = af.subelement('dataSetInformation', sourceInformation, NS6)
    
    UUIDSR = af.subelement('UUID', dataSetInformationSR, XMLNS)
    UUIDSR.text = UUIDsource
    
    shortName = af.subelement('shortName', dataSetInformationSR, XMLNS)
    shortName.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    shortName.text = citation

    sourceCitation = af.subelement('sourceCitation', dataSetInformationSR, NS6)
    sourceCitation.text = citation
    
    #administrativeInformation[0] (verificação se o source não é o próprio do ILCD)
    if UUIDsource != "a97a0155-0234-4b87-b4ce-a45da52f2a40":
        dataEntryBySR = af.subelement('dataEntryBy', administrativeInformationSR, NS6)
        referenceToDataSetFormatSR = af.subelement('referenceToDataSetFormat', dataEntryBySR, XMLNS)
        af.referencia(referenceToDataSetFormatSR, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', XMLNS, 'ILCD Format', '01.01.000')
    
    #administrativeInformation[1]
    publicationAndOwnershipSR = af.subelement('publicationAndOwnership', administrativeInformationSR, NS6)
    
    dataSetVersionSR = af.subelement('dataSetVersion', publicationAndOwnershipSR, XMLNS)
    dataSetVersionSR.text = "00.00.000"
    
    permanentDataSetURISR = af.subelement('permanentDataSetURI', publicationAndOwnershipSR, XMLNS)
    #PROB: colocar o endereço do IBICT aqui
    permanentDataSetURISR.text = 'http://sicv.acv.ibict.br'
      
    #criar pasta se necessário
    try:
        os.mkdir("./ILCD-algorithm/sources")
    except OSError:
        pass
     
    #salvar arquivo na pasta de bibliografias
    file_flow = "./ILCD-algorithm/sources/" + UUIDsource + ".xml"
    with open(file_flow, 'wb') as Flow:
        Flow.write(etree.tostring(root, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))

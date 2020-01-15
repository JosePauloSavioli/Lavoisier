# -*- coding: utf-8 -*-
"""
Created on Sun Jan 12 21:10:53 2020

Funções adicionais para a conversão

@author: JP
"""

#trabalho com xml (leitura e escrita)
from lxml import etree

#criação de um subelemento dentro do xml
def subelement(name, parent, namespace):
    sub = etree.SubElement(parent, namespace + name)
    return sub

#criação de um subelemento de referência
def referencia(reference, type_r, refObjectId, NS, short_d, version = '01.00.000'):
    reference.set('type', type_r)
    reference.set('refObjectId', refObjectId)
    reference.set('version', version)
    
    if type_r == 'contact data set':
        folder = '../contacts/'
    elif type_r == 'source data set':
        folder = '../sources/'
    elif type_r == 'flow data set':
        folder = '../flows/'
    elif type_r == 'flow property data set':
        folder = '../flowproperties/'
    elif type_r == 'unit group data set':
        folder = '../unitgroups/'
    else:
        raise Exception ("Este tipo de arquivo não existe")
    
    reference.set('uri', folder + refObjectId + '.xml')
    
    if short_d is not None:
        short_description_2 = subelement('shortDescription', reference, NS)
        short_description_2.set('{http://www.w3.org/XML/1998/namespace}lang','en')
        short_description_2.text = short_d
    
#classificação listada segundo o ISIC
def do_classification(text, name, classification, XMLNS):
    clas0 = subelement('class', classification, XMLNS)
    clas0.set('level','0')
    clas0.set('name',name)
    clas1 = subelement('class', classification, XMLNS)
    clas1.set('level','1')
    clas1.set('name',name)
    clas2 = subelement('class', classification, XMLNS)
    clas2.set('level','2')
    clas2.set('name',name)
    clas3 = subelement('class', classification, XMLNS)
    clas3.set('level','3')
    clas3.set('name',name)
    
    t = 2
    lvl = ['']*4
    
    #achar no arquivo ISIC.txt a correspondência da classificação para colocar no ILCD
    with open(r"./ISIC.txt") as f:
        div_text = text.split(':')
        for line in f:
            if div_text[0][:-t] == line.split(':::')[0]:
                lvl[t] = div_text[0][:-t] + ':' + line.split(':::')[1]
                t = t-1
            elif div_text[0] == line.split(':::')[0]:
                lvl[3] = line.split(':::')[2]
                lvl[0] = div_text[0] + ':' + line.split(':::')[1]
                break
            
    clas0.text,clas1.text,clas2.text,clas3.text = lvl[3],lvl[2],lvl[1],lvl[0]

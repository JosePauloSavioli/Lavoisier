#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 24 08:33:35 2021

Main convertion application, uses the mapping of "mapping.py" to loop through
    all possible elements of the Ecospold2 xml and execute the commands of the
    main map dictionary

@author: jotape42p
"""

import logging
log = logging.getLogger(__name__)

from lxml import etree as ET
from re import search

# Basic additional functions
from Lavoisier.collection import str_, create_folder, root_, sub, texts, do_uncertainty, do_reference
# Complex additional functions
from Lavoisier.collection import flow_set_and_internal_ID, flow_allocation_info, set_parameters_and_variables
# Triggered functions (See mapping.py file - they're called by eval on line 296)
from Lavoisier.collection import review, bool_, time_year, class_, pedigree, f_property, type_product, flow_ref, elem_f_property, elementary_flow_info, compartment
# Functions to create additional files
from Lavoisier.additional_files import create_contact, create_source

def convert_spold(map_, e_tree, i_tree, original_tree, o_t, al):
    '''
    This is the main function, it is responsible for the declaration of ILCD 
    fields and assignment of Ecospold2 information to ILCD fields
    ''' 
    
    from Lavoisier.conversion_caller import save_dir
    
    def order_exchange_subelements(elem):
        return {'referenceToFlowDataSet':0,
                 'location':1,
                 'functionType':2,
                 'exchangeDirection':3,
                 'referenceToVariable':4,
                 'meanAmount':5,
                 'resultingAmount':6,
                 'minimumAmount':7,
                 'maximumAmount':8,
                 'uncertaintyDistributionType':9,
                 'relativeStandardDeviation95In':10,
                 'allocations':11,
                 'dataSourceType':12,
                 'dataDerivationTypeStatus':13,
                 'referencesToDataSource':14,
                 'generalComment':15}.get(elem.tag)
    
    # Main loop through all elements of the mapping dictionary
    for key,level in map_.items():
        
        
        # Check special mapping of intermadiate flows
        if key == 'IntermFlows':
            
            log.debug("Converting intermediate flows")
            
            # Counter of non reference flows and boolean if reference flow was done
            #   for flow internal ID setting
            countNonReference, referencePassed, alInfoActivation, ref_exc = 1, False, False, None
            # Set of all ids of variables, properties and equations
            id_ = set()
            
            # Loop through all intermediate exchanges to create flow elements on ILCD and new flowDataSet files
            for flow in e_tree.iterfind(str_(['intermediateExchange'])):
                
                # Creation of flow and internal ID setting
                exc, countNonReference, referencePassed, alInfoActivation, ref_exc = flow_set_and_internal_ID(i_tree, 
                                                                                   flow.find('{http://www.EcoInvent.org/EcoSpold02}outputGroup'), 
                                                                                   countNonReference, 
                                                                                   referencePassed,
                                                                                   alInfoActivation,
                                                                                   flow, ref_exc)
                
                log.debug(f"\tConverting {flow.find('{http://www.EcoInvent.org/EcoSpold02}name').text}: {flow.get('id')}")
                
                # Allocation check
                if al is not None:
                    if flow.get('id') in (ids_[0][0] for ids_ in al):
                        flow_allocation_info(al, exc)
                # If Reference and it doesn't have an allocation master property
                elif alInfoActivation:
                    alInfoActivation = False
                    flow_allocation_info(((("_", 0), 1),), exc)
                    
                # Recursive call for flow specific mapping inside processDataSet of ILCD
                convert_spold(level, root_(flow), exc, i_tree, o_t, al)
                
                # Creation of new xml tree for the flowDataSet
                flow_tree = ET.ElementTree(ET.Element("flowDataSet", version = '1.1', nsmap = {None: "http://lca.jrc.it/ILCD/Flow",
                                                                                               'c': "http://lca.jrc.it/ILCD/Common"}))
                
                # Recursive call for flow specific mapping inside flowDataSet of ILCD
                convert_spold(level.get('map_f'), root_(flow), flow_tree, i_tree, o_t, al) 
                
                # Get all variables, equations and parameters in the flow and set all references and variableParameters
                id_.update(set_parameters_and_variables(o_t, flow_tree, original_tree, flow, exc, id_))
                
                log.debug("\tSuccessfully converted flow variables")
                
                # Do uncertainty calculations for the flow
                x = exc.find("generalComment")
                do_uncertainty(root_(flow), exc, flow.get('amount'), 1, isGeneralComment = x if x is not None else '')
                
                # Organize general comment
                if x is not None:
                    if x.text is not None:
                        if len(x.text) > 500:
                            xpedigree = x.text.split('). ')[0] + '). '
                            xtext = '). '.join(x.text.split('). ')[1:])
                            if len(xpedigree) > 70:
                                xtext, xpedigree = xpedigree, ''
                            gc = i_tree.find("//dataSetInformation/{http://lca.jrc.it/ILCD/Common}generalComment")
                            if gc is not None:
                                gc.text += '\n' + 'Comment for ' + flow_tree.find('//dataSetInformation/name/baseName').text + ': ' + xtext
                                x.text = xpedigree + "Exchange comment placed in dataset's general comment for passing the number of characters"
                            else:
                                gc = ET.SubElement(i_tree.find('//dataSetInformation'), '{http://lca.jrc.it/ILCD/Common}generalComment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                                gc.text = 'Comment for ' + flow_tree.find('//dataSetInformation/name/baseName').text + ': ' + xtext
                                x.text = xpedigree + "Exchange comment placed in dataset's general comment for passing the number of characters"
                    
                # Organize exchange data
                exc[:] = sorted(exc, key=order_exchange_subelements)
                
                # Create flow folder on save directory
                create_folder(save_dir+"/flows")
                
                # Save flowDataSet to zip folder
                with open(save_dir+"/flows/"+flow_tree.find('//dataSetInformation/{http://lca.jrc.it/ILCD/Common}UUID').text+".xml", 'wb') as f:
                    f.write(ET.tostring(flow_tree, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))
                    
                log.debug("\tSuccessfully converted flow\n")
        	
        # Check special mapping of elementary flows (uses the counter from intermediate flows)            
        elif key == 'ElemFlows':
            
            log.debug("Converting elementary flows")
            
            # Loop through all elementary exchanges to create flow elements on ILCD and new flowDataSet files
            for flow in e_tree.iterfind(str_(['elementaryExchange'])):
                
                # Creation of flow and internal ID setting
                exc, countNonReference, referencePassed, alInfoActivation, ref_exc = flow_set_and_internal_ID(i_tree, 
                                                                                   flow.find('{http://www.EcoInvent.org/EcoSpold02}outputGroup'), 
                                                                                   countNonReference, 
                                                                                   referencePassed,
                                                                                   alInfoActivation,
                                                                                   flow, ref_exc)
                log.debug(f"\tConverting {flow.find('{http://www.EcoInvent.org/EcoSpold02}name').text}: {flow.get('id')}")
                # Recursive call for flow specific mapping inside processDataSet of ILCD
                convert_spold(level, root_(flow), exc, i_tree, o_t, al)
                
                # Creation of new xml tree for the flowDataSet
                flow_tree = ET.ElementTree(ET.Element("flowDataSet", version = '1.1', nsmap = {None: "http://lca.jrc.it/ILCD/Flow",
                                                                                               'c': "http://lca.jrc.it/ILCD/Common"}))
                
                # Recursive call for flow specific mapping inside flowDataSet of ILCD
                convert_spold(level.get('map_f'), root_(flow), flow_tree, i_tree, o_t, al)
                
                # Get all variables, equations and parameters in the flow and set all references and variableParameters
                id_.update(set_parameters_and_variables(o_t, flow_tree, original_tree, flow, exc, id_))
                
                log.debug("\tSuccessfully converted flow variables")
                # Do uncertainty calculations for the flow
                x = exc.find("generalComment")
                do_uncertainty(root_(flow), exc, flow.get('amount'), 1, isGeneralComment = x if x is not None else '')
                
                # Organize general comment
                if x is not None:
                    if x.text is not None:
                        if len(x.text) > 500:
                            xpedigree = x.text.split('). ')[0] + '). '
                            xtext = '). '.join(x.text.split('). ')[1:])
                            if len(xpedigree) > 70:
                                xtext, xpedigree = xpedigree, ''
                            gc = i_tree.find("//dataSetInformation/{http://lca.jrc.it/ILCD/Common}generalComment")
                            if gc is not None:
                                gc.text += '\n' + 'Comment for ' + flow_tree.find('//dataSetInformation/name/baseName').text + ': ' + xtext
                                x.text = xpedigree + "Exchange comment placed in dataset's general comment for passing the number of characters"
                            else:
                                gc = ET.SubElement(i_tree.find('//dataSetInformation'), '{http://lca.jrc.it/ILCD/Common}generalComment', {"{http://www.w3.org/XML/1998/namespace}lang":'en'})
                                gc.text = 'Comment for ' + flow_tree.find('//dataSetInformation/name/baseName').text + ': ' + xtext
                                x.text = xpedigree + "Exchange comment placed in dataset's general comment for passing the number of characters"
                    
                # Organize exchange data
                exc[:] = sorted(exc, key=order_exchange_subelements)
                
                # Create flow folder on save directory
                create_folder(save_dir+"/flows")
                
                # Save flowDataSet to zip folder
                with open(save_dir+"/flows/"+flow_tree.find('//dataSetInformation/{http://lca.jrc.it/ILCD/Common}UUID').text+".xml", 'wb') as f:
                    f.write(ET.tostring(flow_tree, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))
                    
                log.debug("\tSuccessfully converted flow\n")
        
        # Check all parameters to get variables and equations         
        elif key == 'Parameters':
            
            log.debug("Converting parameters")
            
            for param in e_tree.iterfind(str_(['parameter'])):
                id_.update(set_parameters_and_variables(None, None, original_tree, param, None, id_, 0))
        
        # Specific statement to ignore map_f mapping if in a recursive call
        elif key == 'map_f':
            log.debug("\tChange map_f")
            continue
        
        # Call for any other normal mapping functions
        else:
            for info in level.values():
                
                # Check if element was already created in the ilcd tree
                # If it has the element, don't make it even if the bound verification is true
                if info.get('duplicate_verification'):
                    if i_tree.find(info.get('duplicate_verification')[0]) is not None:
                        continue
                
                # Check if element has to be created
                if info.get('bound_verification'):
                    if e_tree.find(str_(info.get('bound_verification'))) is not None:
                        if isinstance(i_tree, ET._Element):
                            #print(info)
                            #print("LEN", len(info.get('args')))
                            if len(info.get('args')) == 2:
                                el = ET.SubElement(i_tree, *info.get('args'))
                            elif len(info.get('args')) == 3:
                                el = ET.SubElement(i_tree.find(info.get('args')[1]), info.get('args')[0], info.get('args')[2])
                        else:
                            el = sub(i_tree, *info.get('args'))
                    else:
                        continue
                
                # Check if it has to create a subelement of a tree root element
                elif isinstance(i_tree, ET._Element):
                    el = ET.SubElement(i_tree, *info.get('args'))
                
                # Create subelement
                else:
                    el = sub(i_tree, *info.get('args'))
                
                
                # Check for info in attributes for created element
                if info.get('attrib'):
                    for i in info.get('attrib'):
                        
                        # Check if element is optional in Ecospold2
                        if i[1]:
                            if e_tree.find(str_(i[2])) is not None:
                                if search('@',i[2][-1]):
                                    el.set(i[0], e_tree.find(str_(i[2]))).get(search('\[@([A-z]+)\]', i[2][-1]).group(1))
                                else:
                                    at = texts(e_tree, str_(i[2]))
                                    el.set(i[0], at)
                                    
                        # Else element is mandatory in Ecospold2
                        else:
                            if search('@',i[2][-1]):
                                el.set(i[0], e_tree.find(str_(i[2]))).get(search('\[@([A-z]+)\]', i[2][-1]).group(1))
                            else:
                                at = texts(e_tree, str_(i[2]))
                                el.set(i[0], at)
                                
                # Check for special text on created element
                if info.get('text'):
                    ref = ''
                    for i in info.get('text'):
                        
                        # 1.Check if it is simple text or a tuple of commands
                        if isinstance(i,str):
                            # 2.Check if it has an uuid and needs a reference specific text
                            if not info.get('ref_uuid'):
                                if el.text is None:
                                    el.text = i
                                else:
                                    el.text += i
                            # 2.Else simple text
                            else:
                                ref += i
                        # 1.Else execute tuple of commands 
                        else:
                            # 3.Check if it is optional on Ecospold2 or it is many fields of text
                            if i[0]:
                                # 4.Check if tuple command is to find all subelements of text and place in the same text field
                                if i[2] == 'findall':
                                    tex_ = [0]*50
                                    for comment in e_tree.findall(str_(i[1])):
                                        for child in comment:
                                            if child.text is not None:
                                                numb = int(child.get('index', -1))
                                                if numb > 49:
                                                    numb = -2
                                                if 'imageUrl' in child.tag:
                                                    tex_[numb] = 'ImageURL: ' + child.text
                                                else:
                                                    tex_[numb] = child.text
                                    tex_ = [t for t in tex_ if isinstance(t, str)]
                                    t = '\n'.join(tex_)
                                # 4. Elif tuple command is to find all text within an element of that name (ex: tag)
                                elif i[2] == 'findtext':
                                    tex_ = ''
                                    for comment in e_tree.findall(str_(i[1])):
                                        if comment.text is not None:
                                            tex_ = tex_ + comment.text + '; '
                                    t = tex_
                                # 4. Elif tuple command is to find all subelements of text and place in different instances of the same element
                                elif i[2] == 'findname':
                                    fields = e_tree.findall(str_(i[1]))
                                    for comment in fields:
                                        if el.text is not None:
                                            el.text += '; ' + comment.text
                                        else:
                                            el.text = comment.text
                                        #if comment != fields[-1]:
                                        #    el = sub(i_tree, *info.get('args'))
                                    continue
                                # 4. Else no tuple command for text loops, only check if the text exists 
                                else:
                                    if e_tree.find(str_(i[1])) is not None:
                                        if search('@',i[1][-1]):
                                            t = e_tree.find(str_(i[1])).get(search('\[@([A-z]+)\]', i[1][-1]).group(1))
                                        else:
                                            t = texts(e_tree, str_(i[1]))
                                    else:
                                        continue
                            # 3.Else text is mandatory on Ecospold2
                            else:
                                if search('@',i[1][-1]):
                                    if e_tree.find(str_(i[1])) is not None:
                                        t = e_tree.find(str_(i[1])).get(search('\[@([A-z]+)\]', i[1][-1]).group(1))
                                        if i[1][-1] == 'intermediateExchange[@casNumber]' and len(t) < 11:
                                            t = '0'*(11-len(t)) + t
                                    elif i[1][-1] == 'dataGeneratorAndPublication[@dataPublishedIn]':
                                        t = '2'
                                    else:
                                        continue
                                else:
                                    t = texts(e_tree, str_(i[1]))
                            
                            # Check if there is a related mapping table to the field
                            if i[2]:
                                if i[2] not in ('findall', 'findname', 'findtext'):
                                    table = info[i[2]]
                                    t = table.get(t)
                            
                            # Place text on element if it is not a reference
                            if not info.get('ref_uuid'):
                                if el.text is None:
                                    el.text = t
                                elif t is None:
                                    pass
                                else:
                                    el.text += t
                            # Else specific reference text [used in info.get('ref_uuid') line]
                            else:
                                ref += t

                # Check if created element is a reference
                if info.get('ref_uuid'):
                    
                    ref_uuid = info.get('ref_uuid')
                    
                    # Check if it is an existing UUID reference on Ecospold2
                    if isinstance(ref_uuid, list):
                        ref_uuid = e_tree.find(str_(ref_uuid)).get(search('\[@([A-z]+)\]', ref_uuid[-1]).group(1))
                    
                    # Set reference element
                    do_reference(el, info.get('ref_type'), ref_uuid, ref)
                    
                    # If reference needs to add an additional file (sourceDataSet or contactDataSet)
                    if info.get('add_file'):
                        
                        log.debug(f"\t\t -> Creating {info.get('add_file')} file")
                        
                        # SourceDataSet
                        if info.get('add_file') == 'source':
                            
                            # Creates a new source dataset
                            create_source(ET.ElementTree(ET.Element("sourceDataSet", version = '1.1', nsmap = {None: "http://lca.jrc.it/ILCD/Source",
                                                                                                         'c': "http://lca.jrc.it/ILCD/Common"})),
                                            ref_uuid, original_tree, ref)
                        
                        # ContactDataSet
                        elif info.get('add_file') == 'contact':
                            
                            # Specific check for author @isActive boolean
                            if el.tag == "{http://lca.jrc.it/ILCD/Common}referenceToPersonOrEntityEnteringTheData":
                                if o_t.find('//{http://www.EcoInvent.org/EcoSpold02}dataEntryBy[@isActiveAuthor]') is not None:
                                    act = 'Is Active Author: ' + o_t.find('//{http://www.EcoInvent.org/EcoSpold02}dataEntryBy').get('isActiveAuthor')
                            else:
                                act = None
                                
                            # Creates a new contact dataset
                            create_contact(ET.ElementTree(ET.Element("contactDataSet", version = '1.1', nsmap = {None: "http://lca.jrc.it/ILCD/Contact",
                                                                                                           'c': "http://lca.jrc.it/ILCD/Common"})),
                                            ref_uuid, original_tree, *ref.split(', email: '), {'active': act})
                
                # Check function triggers for the created element
                if info.get('specific'):
                    
                    log.debug(f"\t\tRunning -> Function {info.get('specific').get('func')}")
                    
                    # Eval function
                    func = eval(info.get('specific').get('func'))
                    
                    # Call function with specific different parameters
                    if info.get('specific').get('pass') == 1:
                        func(e_tree, el, i_tree, info.get('specific').get('args'))
                    elif info.get('specific').get('pass') == 2:
                        func(e_tree, el, original_tree, info.get('specific').get('args'))
                    elif info.get('specific').get('pass') == 3:
                        func(e_tree, el, i_tree, original_tree, info.get('specific').get('args'))
                    elif info.get('specific').get('pass') == 4:
                        func(o_t, e_tree, el, original_tree, info.get('specific').get('args'))
                    else:
                        func(e_tree, el, info.get('specific').get('args'))
                        
                        


# -*- coding: utf-8 -*-
"""
Created on Sat Oct 12 11:58:41 2019

@author: JP
"""

from lxml import etree
import uuid
import time

def namespaces(link):
    ns = link
    NS = "{%s}" %link
    return ns, NS

def subelement(name, parent, namespace):
    sub = etree.SubElement(parent, namespace + name)
    return sub

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
    with open(r"./ISIC.txt") as f:
        div_text = text.split(':')
        for line in f:
            #line = line.rsplit()
            if div_text[0][:-t] == line.split(':::')[0]:
                lvl[t] = div_text[0][:-t] + ':' + line.split(':::')[1]
                t = t-1
            elif div_text[0] == line.split(':::')[0]:
                lvl[3] = line.split(':::')[2]
                lvl[0] = div_text[0] + ':' + line.split(':::')[1]
                break
    
    clas0.text,clas1.text,clas2.text,clas3.text = lvl[3],lvl[2],lvl[1],lvl[0]
                

if __name__ == '__main__':
    
    #declaring root for ILCD
    #naming namespaces
    xmlns, XMLNS = namespaces("http://lca.jrc.it/ILCD/Common")
    ns2, NS2 = namespaces("http://lca.jrc.it/ILCD/Process")
    ns3, NS3 = namespaces("http://lca.jrc.it/ILCD/Flow")
    ns4, NS4 = namespaces("http://lca.jrc.it/ILCD/Contact")
    ns5, NS5 = namespaces("http://lca.jrc.it/ILCD/FlowProperty")
    ns6, NS6 = namespaces("http://lca.jrc.it/ILCD/Source")
    ns7, NS7 = namespaces("http://lca.jrc.it/ILCD/UnitGroup")
    ns8, NS8 = namespaces("http://iai.kit.edu/ILCD/ProductModel")
    ns9, NS9 = namespaces("http://lca.jrc.it/ILCD/Wrapper")
    olca, OLCA = namespaces("http://openlca.org/ilcd-extensions")
    #mapping the namespaces
    nsmap = {None : xmlns, 'ns2' : ns2, 'ns3' : ns3, 'ns4' : ns4, 'ns5' : ns5, 'ns6' : ns6, 'ns7' : ns7, 'ns8' : ns8, 'ns9' : ns9, 'olca' : olca}
    #declaring root with namespaces
    processDataSet = etree.Element(NS2 + 'processDataSet', version = "1.1", nsmap = nsmap)
    
    #declaring first childs
    processInformation = subelement('processInformation', processDataSet, NS2)
    modellingAndValidation = subelement('modellingAndValidation', processDataSet, NS2)
    administrativeInformation = subelement('administrativeInformation', processDataSet, NS2)
    exchanges = subelement('exchanges', processDataSet, NS2)
    
    #calling Ecospold2 file
    #calling parser
    parser = etree.XMLParser(remove_blank_text = True)
    #uploading Ecospold2 file onto a tree
    Ecospold2_tree = etree.parse('./application of plant protection product, by field sprayer, BR, 2012 - 2014.spold', parser)
    #declaring root and subroots for Ecospold2
    ecoSpold = Ecospold2_tree.getroot()
    activityDescription = ecoSpold[0][0]
    flowData = ecoSpold[0][1]
    modellingAndValidationECO = ecoSpold[0][2]
    administrativeInformationECO = ecoSpold[0][3]
    #print(etree.tostring(activityDataset, pretty_print = True).decode())
    
    #correspondences from processInformation on ILCD
    dataSetInformation = subelement('dataSetInformation', processInformation, NS2)
    
    UUID = subelement('UUID', dataSetInformation, XMLNS)
    UUID.text = activityDescription[0].attrib["activityNameId"]
    
    name = subelement('name', dataSetInformation, NS2)
    baseName = subelement('baseName', name, NS2)
    baseName.attrib['{http://www.w3.org/XML/1998/namespace}lang'] = "en"
    baseName.text = activityDescription[0][0].text
    
    classificationInformation = subelement('classificationInformation', dataSetInformation, NS2)
    classification = subelement('classification', classificationInformation, XMLNS)
    class_name = activityDescription[1][0].text
    class_value = activityDescription[1][1].text
    do_classification(class_value, class_name, classification, XMLNS)
    
    generalComment = subelement('generalComment', dataSetInformation, XMLNS)
    generalComment.attrib['{http://www.w3.org/XML/1998/namespace}lang'] = "en"
    list_for_special_activity = ['ordinary transforming activity','market activity','IO activity','residual activity','production mix','import activity','supply mix','export activity','re-Export activity','correction activity','market group']
    if activityDescription[0].attrib['inheritanceDepth'] == "0":
        is_child = "parent"
        uuid_parent = "None"
    elif activityDescription[0].attrib['inheritanceDepth'] == "1":
        is_child = "geography child"
        uuid_parent = activityDescription[0].attrib['parentActivityId']
    elif activityDescription[0].attrib['inheritanceDepth'] == "2":
        is_child = "technological child"
        uuid_parent = activityDescription[0].attrib['parentActivityId']
    elif activityDescription[0].attrib['inheritanceDepth'] == "3":
        is_child = "macroeconomic child"
        uuid_parent = activityDescription[0].attrib['parentActivityId']
    if activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}tag') is not None:
        tag_t = activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}tag')
    else:
        tag_t = "None"
    generalComment.text = "Type of process: " + list_for_special_activity[int(activityDescription[0].attrib['specialActivityType'])] + "; Relation Ecospold2: " + is_child + " from " + uuid_parent + "; Tags: " + tag_t + '\n' + activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}generalComment/{http://www.EcoInvent.org/EcoSpold02}text').text
    
    if activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}synonyms') is not None:
        synonyms = subelement('synonyms', dataSetInformation, XMLNS)
        synonyms.text = activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}synonyms')
    
    print(activityDescription[0].get('dataSetIcon'))
    
    #CHECK THE VALIDITY OF THIS
    if activityDescription[0].get('dataSetIcon') is not None:
        referenceToExternalDocument = subelement('referenceToExternalDocument', dataSetInformation, NS2)
        referenceToExternalDocument.set('type','source data set')
        referenceToExternalDocument.set('refObjectId', uuid.uuid4())
        referenceToExternalDocument.set('uri', activityDescription[0].attrib['datasetIcon'])
    
    quantitativeInformation = subelement('quantitativeInformation', processInformation, NS2)
    #CHECK IF ITS THE ONLY ONE
    quantitativeInformation.set('type', 'Reference flow(s)')
    referenceToReferenceFlow = subelement('referenceToReferenceFlow', quantitativeInformation, NS2)
    referenceToReferenceFlow.text = "0"
    
    #CHECK THE INPUT TYPE OF VARIABLE
    tim_ = subelement('time', processInformation, NS2)
    startDateEco = activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}timePeriod').attrib['startDate']
    endDateEco = activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}timePeriod').attrib['endDate']
    stdILCD = time.strptime(startDateEco, '%Y-%m-%d')
    endILCD = time.strptime(endDateEco, '%Y-%m-%d')
    tim_.attrib['{http://openlca.org/ilcd-extensions}startDate'] = str(int(time.mktime(stdILCD)))
    tim_.attrib['{http://openlca.org/ilcd-extensions}endDate'] = str(int(time.mktime(endILCD)))
    
    referenceYear = subelement('referenceYear', tim_, XMLNS)
    referenceYear.text = str(stdILCD.tm_year)
    dataSetValidUntil = subelement('dataSetValidUntil', tim_, XMLNS)
    dataSetValidUntil.text = str(endILCD.tm_year)
    timeRepresentativenessDescription = subelement('timeRepresentativenessDescription', tim_, XMLNS)
    timeRepresentativenessDescription.attrib['{http://www.w3.org/XML/1998/namespace}lang'] = 'en'
    if activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}timePeriod').attrib['isDataValidForEntirePeriod'] == "true":
        is_valid = "Data is valid for the entire period"
    else:
        is_valid = "Data is not valid for the entire period, check this comment for more information"
    timeRepresentativenessDescription.text = is_valid + '\n' + activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}timePeriod/{http://www.EcoInvent.org/EcoSpold02}comment/{http://www.EcoInvent.org/EcoSpold02}text').text
    
    geography = subelement('geography', processInformation, NS2)
    locationOfOperationSupplyOrProduction = subelement('locationOfOperationSupplyOrProduction', geography, NS2)
    #CHECK IF LATITUDE AND LONGITUDE ARE MANDATORY
    locationOfOperationSupplyOrProduction.set('location',activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}geography/{http://www.EcoInvent.org/EcoSpold02}shortname').text)
    descriptionOfRestrictions = subelement('descriptionOfRestrictions', locationOfOperationSupplyOrProduction, NS2)
    descriptionOfRestrictions.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    descriptionOfRestrictions.text = activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}geography/{http://www.EcoInvent.org/EcoSpold02}comment/{http://www.EcoInvent.org/EcoSpold02}text').text
    
    technology = subelement('technology', processInformation, NS2)
    list_of_technologies = ['Undefined','New','Modern','Current','Old','Outdated']
    technologyDescriptionAndIncludedProcesses = subelement('technologyDescriptionAndIncludedProcesses', technology, NS2)
    technologyDescriptionAndIncludedProcesses.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    technologyDescriptionAndIncludedProcesses.text = "The technology level of this process is: " + list_of_technologies[int(activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}technology').attrib['technologyLevel'])] + "\nThe included activities go from: " + activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}includedActivitiesStart').text + " to: " + activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}includedActivitiesEnd').text
    technologyApplicability = subelement('technologyApplicability', technology, NS2)
    technologyApplicability.text = activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}technology/{http://www.EcoInvent.org/EcoSpold02}comment/{http://www.EcoInvent.org/EcoSpold02}text').text
    
    LCIMethodAndAllocation = subelement('LCIMethodAndAllocation', modellingAndValidation, NS2)
    typeOfDataSet = subelement('typeOfDataSet', LCIMethodAndAllocation, NS2)
    #CHECK FOR OTHER TYPES DIFFERENTIATION
    list_of_type_process = ['','Unit Process, Single Process','LCI Result']
    typeOfDataSet.text = list_of_type_process[int(activityDescription[0].attrib['type'])]
    
    LCIMethodPrinciple = subelement('LCIMethodPrinciple', LCIMethodAndAllocation, NS2)
    #CHECK THE VALUES
    LCIMethodPrinciple.text = "Other"
    
    LCIMethodApproach = subelement('LCIMethodApproach', LCIMethodAndAllocation, NS2)
    LCIMethodApproach.text = modellingAndValidationECO[0].find('{http://www.EcoInvent.org/EcoSpold02}systemModelName').text
    
    dataSourcesTreatmentAndRepresentativeness = subelement('dataSourcesTreatmentAndRepresentativeness', modellingAndValidation, NS2)
    
    annualSupplyOrProductionVolume = subelement('annualSupplyOrProductionVolume', modellingAndValidation, NS2)
    #CHECK FOR EACH EXCHANGE
    annualSupplyOrProductionVolume.text = ""
    #VERIFY
    deviationsFromCutOffAndCompletenessPrinciples = subelement('deviationsFromCutOffAndCompletenessPrinciples', modellingAndValidation, NS2)
    deviationsFromCutOffAndCompletenessPrinciples.text = "None"
    #VERIFY
    deviationsFromSelectionAndCombinationPrinciples = subelement('deviationsFromSelectionAndCombinationPrinciples', modellingAndValidation, NS2)
    deviationsFromSelectionAndCombinationPrinciples.text = "None"
    
    dataTreatmentAndExtrapolation = subelement('dataTreatmentAndExtrapolation', modellingAndValidation, NS2)
    dataTreatmentAndExtrapolation.text = modellingAndValidationECO[0].find('{http://www.EcoInvent.org/EcoSpold02}extrapolations').text
    
    samplingProcedure = subelement('samplingProcedure', modellingAndValidation, NS2)
    samplingProcedure.text = modellingAndValidationECO[0].find('{http://www.EcoInvent.org/EcoSpold02}samplingProcedure').text
    
    percentageSupplyOrProductionCovered = subelement('percentageSupplyOrProductionCovered', modellingAndValidation, NS2)
    percentageSupplyOrProductionCovered.text =  modellingAndValidationECO[0].attrib['percent']
    
    #CHECK HOW YOU DO A GROUP FOR ENTIRE REVIEW DETAILS
    validation = subelement('validation', modellingAndValidation, NS2)
    review = subelement('review', validation, NS2)
    referenceToNameOfReviewerAndInstitution = subelement('referenceToNameOfReviewerAndInstitution', review, XMLNS)
    referenceToNameOfReviewerAndInstitution.set('type', 'contact data set')
    referenceToNameOfReviewerAndInstitution.set('uri', modellingAndValidationECO.find('{http://www.EcoInvent.org/EcoSpold02}review').attrib['reviewerId'])
    short_description_2 = subelement('shortDescription', referenceToNameOfReviewerAndInstitution, XMLNS)
    short_description_2.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    short_description_2.text = modellingAndValidationECO.find('{http://www.EcoInvent.org/EcoSpold02}review').attrib['reviewerName']
    
    #TO DO FOR ALL THE REVIEWERS
    reviewDetails = subelement('reviewDetails', review, XMLNS)
    # + modellingAndValidationECO.find('{http://www.EcoInvent.org/EcoSpold02}review/{http://www.EcoInvent.org/EcoSpold02}details/{http://www.EcoInvent.org/EcoSpold02}text').text -> NULL TEXT IN FILE
    reviewDetails.text = "Date of last review: " + modellingAndValidationECO.find('{http://www.EcoInvent.org/EcoSpold02}review').attrib['reviewDate'] + '; Major version: ' + modellingAndValidationECO.find('{http://www.EcoInvent.org/EcoSpold02}review').attrib['reviewedMajorRelease'] + '.' + modellingAndValidationECO.find('{http://www.EcoInvent.org/EcoSpold02}review').attrib['reviewedMajorRevision'] + '; Minor version: ' + modellingAndValidationECO.find('{http://www.EcoInvent.org/EcoSpold02}review').attrib['reviewedMinorRelease'] + '.' + modellingAndValidationECO.find('{http://www.EcoInvent.org/EcoSpold02}review').attrib['reviewedMinorRevision']
    otherDetails = subelement('otherDetails', review, XMLNS)
    otherDetails.text = modellingAndValidationECO.find('{http://www.EcoInvent.org/EcoSpold02}review/{http://www.EcoInvent.org/EcoSpold02}otherDetails').text
    
    #CHECK VALUES
    comissionerAndGoals = subelement('comissionerAndGoals', administrativeInformation, XMLNS)
    intendedApplications = subelement('intendedApplications', comissionerAndGoals, XMLNS)
    intendedApplications.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    intendedApplications.text = "Can be used for any types of LCA studies"
    
    dataGenerator = subelement('dataGenerator', administrativeInformation, NS2)
    referenceToPersonOrEntityGeneratingTheDataSet = subelement('referenceToPersonOrEntityGeneratingTheDataSet', dataGenerator, XMLNS)
    #CHECK HOW TO MAKE URI, UUID AND CONTACTS POSSIBLE
    referenceToPersonOrEntityGeneratingTheDataSet.set('type', 'contact data set')
    referenceToPersonOrEntityGeneratingTheDataSet.set('uri',administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['personId'])
    short_description_1 = subelement('shortDescription', referenceToPersonOrEntityGeneratingTheDataSet, XMLNS)
    short_description_1.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    short_description_1.text = administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['personName']
    
    dataEntryBy = subelement('dataEntryBy', administrativeInformation, NS2)
    #CHECK IF IT IS THE CREATION ONE
    timeStamp = subelement('timeStamp', dataEntryBy, XMLNS)
    timeStamp.text = administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}fileAttributes').attrib['creationTimestamp']
    #TO DO A DEF FOR REFERENCES
    referenceToDataSetFormat = subelement('referenceToDataSetFormat', dataEntryBy, XMLNS)
    referenceToDataSetFormat.set('type', 'source data set')
    referenceToDataSetFormat.set('refObjectId','a97a0155-0234-4b87-b4ce-a45da52f2a40') #ILCD one
    short_description_3 = subelement('shortDescription', referenceToDataSetFormat, XMLNS)
    short_description_3.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    short_description_3.text = "ILCD format"
    
    referenceToPersonOrEntityEnteringTheData = subelement('referenceToPersonOrEntityEnteringTheData', dataEntryBy, XMLNS)
    referenceToPersonOrEntityEnteringTheData.set('type', 'contact data set')
    referenceToPersonOrEntityEnteringTheData.set('uri', administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataEntryBy').attrib['personId'])
    short_description_4 = subelement('shortDescription', referenceToPersonOrEntityEnteringTheData, XMLNS)
    short_description_4.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    short_description_4.text = administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataEntryBy').attrib['personName']
    
    publicationAndOwnership = subelement('publicationAndOwnership', administrativeInformation, NS2)
    dateOfLastRevision = subelement('dateOfLastRevision', publicationAndOwnership, XMLNS)
    dateOfLastRevision.text = administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}fileAttributes').attrib['lastEditTimestamp']
    #CHECK THE TEXT ON THE VERSIONS TO SEE IF ITS CORRECT HERE AND IN THE OTHER DETAILS
    dataSetVersion = subelement('dataSetVersion', publicationAndOwnership, XMLNS)
    dataSetVersion.text = administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}fileAttributes').attrib['majorRelease'] + administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}fileAttributes').attrib['majorRevision']
    
    referenceToUnchangedPublication = subelement('referenceToUnchangedPublication', publicationAndOwnership, XMLNS)
    referenceToUnchangedPublication.set('type', 'source data set')
    referenceToUnchangedPublication.set('uri', administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['publishedSourceId'])
    
    copyright_ = subelement('copyright', publicationAndOwnership, XMLNS)
    if administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['isCopyrightProtected'] == 'true':
        copyright_.text = "true"
    else:
        copyright_.text = "false"
    accessRestrictions = subelement('accessRestrictions', publicationAndOwnership, XMLNS)
    list_of_restrictions = ['public','license','results only','restricted']
    accessRestrictions.text = "This dataset is accessible by: " + list_of_restrictions[int(administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['accessRestrictedTo'])]
    
    print(etree.tostring(processDataSet, pretty_print = True).decode())
    
    with open("./ILCD.xml", 'wb') as f:
        f.write(etree.tostring(processDataSet, pretty_print = True, xml_declaration = True, encoding='UTF-8', standalone="yes"))
    
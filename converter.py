# -*- coding: utf-8 -*-
"""

Conversão de dados de Ecospold2 para ILCD para o IBICT
BKT são as coisas a fazer

"""

#BKT Talvez referências tenham o campo version como requisitado, ver isso (valor geralmente 01.00.000)
#BKT Fazer def para referências
#BKT Relacionar UUID de propriedades e de Unidades do Ecospold2

#importação das bibliotecas (lxml para ler e editar xml, uuid para gerar uuid,
#                           time para mexer com datas)

from lxml import etree
import uuid
import time
import math
import zipfile

#definição das duas variáveis para upar o namespace do arquivo xml

def namespaces(link):
    ns = link
    NS = "{%s}" %link
    return ns, NS

#definição de um subelemento com seu namespace

def subelement(name, parent, namespace):
    sub = etree.SubElement(parent, namespace + name)
    return sub

#conversão da classificação segundo ISIC do Ecospold2 para ILCD

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
                
#função main

if __name__ == '__main__':
    
    #zip
    ILCD_zip = zipfile.ZipFile('./ILCD.zip', 'w')
    
    #declaração dos namespaces do ILCD
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
    
    #mapeamento dos namespaces
    nsmap = {None : xmlns, 'ns2' : ns2, 'ns3' : ns3, 'ns4' : ns4, 'ns5' : ns5,
             'ns6' : ns6, 'ns7' : ns7, 'ns8' : ns8, 'ns9' : ns9, 'olca' : olca}
    nsmap_2 = {None : xmlns, 'ns2' : ns2, 'ns3' : ns3, 'ns4' : ns4, 'ns5' : ns5,
             'ns6' : ns6, 'ns7' : ns7, 'ns8' : ns8}
    
    #declaração do elemento raiz e namespaces
    processDataSet = etree.Element(NS2 + 'processDataSet', version = "1.1", nsmap = nsmap)
    
    #declaração da primeira hierarquia de elementos
    processInformation = subelement('processInformation', processDataSet, NS2)
    modellingAndValidation = subelement('modellingAndValidation', processDataSet, NS2)
    administrativeInformation = subelement('administrativeInformation', processDataSet, NS2)
    exchanges = subelement('exchanges', processDataSet, NS2)

    #parser para ler arquivo Ecospold2
    parser = etree.XMLParser(remove_blank_text = True)
    
    #criando árvore do arquivo Ecospold2
    Ecospold2_tree = etree.parse('./eucalyptus seedling production, in heated greenhouse, BR, 2010 - 2020.spold', parser)
    
    #declação do elemento raiz e elementos da primeira hierarquia do Ecospold2
    ecoSpold = Ecospold2_tree.getroot()
    activityDescription = ecoSpold[0][0]
    flowDataECO = ecoSpold[0][1]
    modellingAndValidationECO = ecoSpold[0][2]
    administrativeInformationECO = ecoSpold[0][3]
    
    #Correspondências para processInformation no ILCD
    dataSetInformation = subelement('dataSetInformation', processInformation, NS2)
    
    #UUID
    UUID = subelement('UUID', dataSetInformation, XMLNS)
    UUID.text = activityDescription[0].attrib["activityNameId"]
    
    #name
    name = subelement('name', dataSetInformation, NS2)
    baseName = subelement('baseName', name, NS2)
    baseName.attrib['{http://www.w3.org/XML/1998/namespace}lang'] = "en"
    baseName.text = activityDescription[0][0].text
    
    #classification
    classificationInformation = subelement('classificationInformation', dataSetInformation, NS2)
    classification = subelement('classification', classificationInformation, XMLNS)
    class_name = activityDescription[1][0].text
    class_value = activityDescription[1][1].text
    do_classification(class_value, class_name, classification, XMLNS)
    
    #generalComment
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
    
    #synonyms
    if activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}synonyms') is not None:
        synonyms = subelement('synonyms', dataSetInformation, XMLNS)
        synonyms.text = activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}synonyms')
    
    #referenceToExternalDocument -> dataSetIcon
    if activityDescription[0].get('dataSetIcon') is not None:
        referenceToExternalDocument = subelement('referenceToExternalDocument', dataSetInformation, NS2)
        referenceToExternalDocument.set('type','source data set')
        Ref_iD = uuid.uuid4()
        referenceToExternalDocument.set('refObjectId', Ref_iD)
        referenceToExternalDocument.set('uri', '../sources/' + Ref_iD)
    
    #QuantitativeInformation
    #BKT Não é o único caso de informação quantitativa (existem Functional Unit, Other Parameter, Production Period)
    #Usado no caso somente Reference Flow
    quantitativeInformation = subelement('quantitativeInformation', processInformation, NS2)
    quantitativeInformation.set('type', 'Reference flow(s)')
    referenceToReferenceFlow = subelement('referenceToReferenceFlow', quantitativeInformation, NS2)
    referenceToReferenceFlow.text = "0"
    
    #Time
    #BKT Terei que checar no teste se o olca é colocado aqui ou se ele tem o namespace encima (não seria só para o OpenLCA as datas, testar sem)
    tim_ = subelement('time', processInformation, NS2)
    startDateEco = activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}timePeriod').attrib['startDate']
    endDateEco = activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}timePeriod').attrib['endDate']
    stdILCD = time.strptime(startDateEco, '%Y-%m-%d')
    endILCD = time.strptime(endDateEco, '%Y-%m-%d')
    #tim_.attrib['{http://openlca.org/ilcd-extensions}startDate'] = str(int(time.mktime(stdILCD)))
    #tim_.attrib['{http://openlca.org/ilcd-extensions}endDate'] = str(int(time.mktime(endILCD)))
    
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
    
    #Geography
    #BKT Latitude e Longitude opcionais para o caso de áreas de estudo, não localidades (não colocar caso sejam países no caso do Ecoinvent)
    geography = subelement('geography', processInformation, NS2)
    locationOfOperationSupplyOrProduction = subelement('locationOfOperationSupplyOrProduction', geography, NS2)
    locationOfOperationSupplyOrProduction.set('location',activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}geography/{http://www.EcoInvent.org/EcoSpold02}shortname').text)
    descriptionOfRestrictions = subelement('descriptionOfRestrictions', locationOfOperationSupplyOrProduction, NS2)
    descriptionOfRestrictions.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    descriptionOfRestrictions.text = activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}geography/{http://www.EcoInvent.org/EcoSpold02}comment/{http://www.EcoInvent.org/EcoSpold02}text').text
    
    #Technology
    technology = subelement('technology', processInformation, NS2)
    list_of_technologies = ['Undefined','New','Modern','Current','Old','Outdated']
    technologyDescriptionAndIncludedProcesses = subelement('technologyDescriptionAndIncludedProcesses', technology, NS2)
    technologyDescriptionAndIncludedProcesses.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    technologyDescriptionAndIncludedProcesses.text = "The technology level of this process is: " + list_of_technologies[int(activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}technology').attrib['technologyLevel'])] + "\nThe included activities go from: " + activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}includedActivitiesStart').text + " to: " + activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}includedActivitiesEnd').text
    technologyApplicability = subelement('technologyApplicability', technology, NS2)
    technologyApplicability.text = activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}technology/{http://www.EcoInvent.org/EcoSpold02}comment/{http://www.EcoInvent.org/EcoSpold02}text').text
    
    #LCI Method and Allocation
    LCIMethodAndAllocation = subelement('LCIMethodAndAllocation', modellingAndValidation, NS2)
    #BKT Não sei como diferenciar neste caso entre os 5 tipos do ILCD para os dois tipos do Ecospold
    typeOfDataSet = subelement('typeOfDataSet', LCIMethodAndAllocation, NS2)
    list_of_type_process = ['','Unit process, black box','LCI result']
    typeOfDataSet.text = list_of_type_process[int(activityDescription[0].attrib['type'])]

    #BKT Tem cinco valores neste caso: (Other, Not Applicable, Consequential with attributional components, consequential e attributional) -> Modelar conforme nome no Ecospold2    
    LCIMethodPrinciple = subelement('LCIMethodPrinciple', LCIMethodAndAllocation, NS2)
    LCIMethodPrinciple.text = "Other"
    
    #BKT Colocar aqui os valores do energyValue se houverem, pode haver erros devido ao campo ser enumerado no ILCD
    LCIMethodApproach = subelement('LCIMethodApproach', LCIMethodAndAllocation, NS2)
    LCIMethodApproach.text = modellingAndValidationECO[0].find('{http://www.EcoInvent.org/EcoSpold02}systemModelName').text
    
    #data Sources ...
    #BKT Colocar todos os campos (verificar os requisitados realmente)
    dataSourcesTreatmentAndRepresentativeness = subelement('dataSourcesTreatmentAndRepresentativeness', modellingAndValidation, NS2)
    
    #BKT não é obrigatório, mas não tem um campo específico de valor para ele
    annualSupplyOrProductionVolume = subelement('annualSupplyOrProductionVolume', dataSourcesTreatmentAndRepresentativeness, NS2)
    
    #BKT None entra quando não há desvios
    deviationsFromCutOffAndCompletenessPrinciples = subelement('deviationsFromCutOffAndCompletenessPrinciples', dataSourcesTreatmentAndRepresentativeness, NS2)
    deviationsFromCutOffAndCompletenessPrinciples.text = "None"
    #BKT None entra quando não há desvios
    deviationsFromSelectionAndCombinationPrinciples = subelement('deviationsFromSelectionAndCombinationPrinciples', dataSourcesTreatmentAndRepresentativeness, NS2)
    deviationsFromSelectionAndCombinationPrinciples.text = "None"
    
    dataTreatmentAndExtrapolation = subelement('dataTreatmentAndExtrapolation', dataSourcesTreatmentAndRepresentativeness, NS2)
    dataTreatmentAndExtrapolation.text = modellingAndValidationECO[0].find('{http://www.EcoInvent.org/EcoSpold02}extrapolations').text
    
    samplingProcedure = subelement('samplingProcedure', dataSourcesTreatmentAndRepresentativeness, NS2)
    samplingProcedure.text = modellingAndValidationECO[0].find('{http://www.EcoInvent.org/EcoSpold02}samplingProcedure').text
    
    percentageSupplyOrProductionCovered = subelement('percentageSupplyOrProductionCovered', dataSourcesTreatmentAndRepresentativeness, NS2)
    #BKT Mudar de attrib para get
    percentageSupplyOrProductionCovered.text = modellingAndValidationECO[0].attrib.get('percent')
    
    #BKT Haviam grupos na diferenciação do xml, mas não há no xml em si, então sem grupos por hora
    validation = subelement('validation', modellingAndValidation, NS2)
    
    #Loop para reviews
    for rev in range(len(modellingAndValidationECO)):
        if modellingAndValidationECO[rev].tag == "{http://www.EcoInvent.org/EcoSpold02}review":
            review = subelement('review', validation, NS2)
            referenceToNameOfReviewerAndInstitution = subelement('referenceToNameOfReviewerAndInstitution', review, XMLNS)
            referenceToNameOfReviewerAndInstitution.set('type', 'contact data set')
            referenceToNameOfReviewerAndInstitution.set('refObjectId', modellingAndValidationECO[rev].attrib['reviewerId'])
            referenceToNameOfReviewerAndInstitution.set('uri', '../contacts/' + modellingAndValidationECO[rev].attrib['reviewerId'])
            short_description_2 = subelement('shortDescription', referenceToNameOfReviewerAndInstitution, XMLNS)
            short_description_2.set('{http://www.w3.org/XML/1998/namespace}lang','en')
            short_description_2.text = modellingAndValidationECO[rev].attrib['reviewerName']
            reviewDetails = subelement('reviewDetails', review, XMLNS)
            reviewDetails.text = "Date of last review: " + modellingAndValidationECO[rev].attrib['reviewDate'] + '; Major version: ' + modellingAndValidationECO[rev].attrib['reviewedMajorRelease'] + '.' + modellingAndValidationECO[rev].attrib['reviewedMajorRevision'] + '; Minor version: ' + modellingAndValidationECO[rev].attrib['reviewedMinorRelease'] + '.' + modellingAndValidationECO[rev].attrib['reviewedMinorRevision']
            otherDetails = subelement('otherReviewDetails', review, XMLNS)
            otherDetails.text = modellingAndValidationECO[rev].find('{http://www.EcoInvent.org/EcoSpold02}otherDetails').text
            
    #BKT Olhar as referências aos financiadores (onde isso pode entrar no dataset do Ecospold2)
    comissionerAndGoals = subelement('comissionerAndGoals', administrativeInformation, XMLNS)
    intendedApplications = subelement('intendedApplications', comissionerAndGoals, XMLNS)
    intendedApplications.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    intendedApplications.text = "Can be used for any types of LCA studies"
    
    #dataGenerator
    dataGenerator = subelement('dataGenerator', administrativeInformation, NS2)
    referenceToPersonOrEntityGeneratingTheDataSet = subelement('referenceToPersonOrEntityGeneratingTheDataSet', dataGenerator, XMLNS)
    referenceToPersonOrEntityGeneratingTheDataSet.set('type', 'contact data set')
    referenceToPersonOrEntityGeneratingTheDataSet.set('refObjectId', administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['personId'])
    referenceToPersonOrEntityGeneratingTheDataSet.set('uri', '../contacts/' + administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['personId'])
    short_description_1 = subelement('shortDescription', referenceToPersonOrEntityGeneratingTheDataSet, XMLNS)
    short_description_1.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    short_description_1.text = administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['personName']
    
    #dataEntryBy
    dataEntryBy = subelement('dataEntryBy', administrativeInformation, NS2)
    #BKT Colocando o 'lastEditTimeStamp' como primeiro arquivo
    timeStamp = subelement('timeStamp', dataEntryBy, XMLNS)
    timeStamp.text = administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}fileAttributes').attrib['creationTimestamp']
    referenceToDataSetFormat = subelement('referenceToDataSetFormat', dataEntryBy, XMLNS)
    referenceToDataSetFormat.set('type', 'source data set')
    referenceToDataSetFormat.set('refObjectId','a97a0155-0234-4b87-b4ce-a45da52f2a40') #do ILCD
    referenceToDataSetFormat.set('uri',"../sources/a97a0155-0234-4b87-b4ce-a45da52f2a40.xml") #Versão colocada no final dos arquivos ILCD, checar "../sources/a97a0155-0234-4b87-b4ce-a45da52f2a40_01.01.000.xml"
    short_description_3 = subelement('shortDescription', referenceToDataSetFormat, XMLNS)
    short_description_3.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    short_description_3.text = "ILCD format"
    
    referenceToPersonOrEntityEnteringTheData = subelement('referenceToPersonOrEntityEnteringTheData', dataEntryBy, XMLNS)
    referenceToPersonOrEntityEnteringTheData.set('type', 'contact data set')
    referenceToPersonOrEntityEnteringTheData.set('refObjectId', administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataEntryBy').attrib['personId'])
    referenceToPersonOrEntityEnteringTheData.set('uri', '../contacts/' + administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataEntryBy').attrib['personId'])
    short_description_4 = subelement('shortDescription', referenceToPersonOrEntityEnteringTheData, XMLNS)
    short_description_4.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    short_description_4.text = administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataEntryBy').attrib['personName']
    
    publicationAndOwnership = subelement('publicationAndOwnership', administrativeInformation, NS2)
    dateOfLastRevision = subelement('dateOfLastRevision', publicationAndOwnership, XMLNS)
    dateOfLastRevision.text = administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}fileAttributes').attrib['lastEditTimestamp']
    #BKT Major Updates; Minor Revisions no dataSetVersion (00.00.000), últimos 3 números são para checagem interna
    dataSetVersion = subelement('dataSetVersion', publicationAndOwnership, XMLNS)
    dataSetVersion.text = "0" + administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}fileAttributes').attrib['majorRelease'] + ".0" + administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}fileAttributes').attrib['minorRevision'] + ".000"
    
    referenceToUnchangedPublication = subelement('referenceToUnchangedPublication', publicationAndOwnership, XMLNS)
    referenceToUnchangedPublication.set('type', 'source data set')
    referenceToUnchangedPublication.set('refObjectId', administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['publishedSourceId'])
    referenceToUnchangedPublication.set('uri', "../sources/" + administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['publishedSourceId'])
    
    copyright_ = subelement('copyright', publicationAndOwnership, XMLNS)
    if administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['isCopyrightProtected'] == 'true':
        copyright_.text = "true"
    else:
        copyright_.text = "false"
    accessRestrictions = subelement('accessRestrictions', publicationAndOwnership, XMLNS)
    list_of_restrictions = ['public','license','results only','restricted']
    accessRestrictions.text = "This dataset is accessible by: " + list_of_restrictions[int(administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['accessRestrictedTo'])]
    
    #exchanges
    #verificação se há relações matemáticas
    
    mathematicalRelations = subelement('mathematicalRelations', processInformation, NS2)
    
    count = 0
    for ex in range(len(flowDataECO)):
        
        if flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}intermediateExchange" or flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}elementaryExchange":
            exchange = subelement("exchange", exchanges, NS2)
            
            #creating a flow file
            flowDataSet = etree.Element(NS3 + 'flowDataSet', version = "1.1", nsmap = nsmap_2)
            
            flowInformation = subelement('flowInformation', flowDataSet, NS3)
            modellingAndValidationF = subelement('modellingAndValidation', flowDataSet, NS3)
            administrativeInformationF = subelement('administrativeInformation', flowDataSet, NS3)
            flowProperties = subelement('flowProperties', flowDataSet, NS3)

            dataSetInformationF = subelement('dataSetInformation', flowInformation, NS3)
            
            UUIDF = subelement('UUID', dataSetInformationF, XMLNS)
            Ref_ex_iD = uuid.uuid4()
            UUIDF.text = str(Ref_ex_iD)
            
            nameF = subelement('name', dataSetInformationF, NS3)
            baseNameF = subelement('baseName', nameF, XMLNS)
            baseNameF.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text
            
            generalComment_F = subelement('generalComment', dataSetInformationF, XMLNS)
            generalComment_F.text = "Este dataset de fluxo foi convertido do formato Ecospold2 para ILCD"
            if flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}tag'):
                generalComment_F.text = generalComment_F.text + ";\t" + flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}tag').text
            
            if flowDataECO[ex].attrib.get('casNumber') is not None:
                CASNumber = subelement('CASNumber', dataSetInformationF, NS3)
                CASNumber.text = flowDataECO[ex].attrib.get('casNumber')
            
            if flowDataECO[ex].attrib.get('formula') is not None:
                sumFormula = subelement('sumFormula', dataSetInformationF, NS3)
                sumFormula.text = flowDataECO[ex].attrib.get('formula')
                
            if flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}synonym'):
                synonymsF = subelement('synonyms', dataSetInformationF, NS3)
                synonyms.text = flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}synonym').text
            
            for classif in flowDataECO[ex].iterfind('{http://www.EcoInvent.org/EcoSpold02}classification'):
                classificationInformationF = subelement('classificationInformation', dataSetInformationF, NS3)
                classificationInformationF.set('name', classif.find('{http://www.EcoInvent.org/EcoSpold02}classificationSystem').text)
                classF = subelement('class', classificationInformationF, NS3)
                classF.set('level', "0")
                classF.text = classif.find('{http://www.EcoInvent.org/EcoSpold02}classificationValue').text
                
            quantitativeInformationF = subelement('quantitativeInformation', flowInformation, NS3)
            
            referenceToReferenceFlowProperty = subelement('referenceToReferenceFlowProperty', quantitativeInformationF, NS3)
            referenceToReferenceFlowProperty.text = "0"
            
            LCIMethodF = subelement('LCIMethod', modellingAndValidationF, NS3)
            typeOfDataSetF = subelement('typeOfDataSet', LCIMethodF, NS3)
            
            dataEntryByF = subelement('dataEntryBy', administrativeInformationF, NS3)
            referenceToDataSetFormatF = subelement('referenceToDataSetFormat', dataEntryByF, NS3)
            referenceToDataSetFormatF.set('type', 'source data set')
            referenceToDataSetFormatF.set('refObjectId','a97a0155-0234-4b87-b4ce-a45da52f2a40') #do ILCD
            referenceToDataSetFormatF.set('uri',"../sources/a97a0155-0234-4b87-b4ce-a45da52f2a40.xml")
            short_description_3 = subelement('shortDescription', referenceToDataSetFormatF, XMLNS)
            short_description_3.set('{http://www.w3.org/XML/1998/namespace}lang','en')
            short_description_3.text = "ILCD format"
            
            publicationAndOwnershipF = subelement('publicationAndOwnership', administrativeInformationF, NS3)
            dataSetVersionF = subelement('dataSetVersion', publicationAndOwnershipF, XMLNS)
            dataSetVersionF.text = "00.00.000"
            permanentDataSetURI = subelement('permanentDataSetURI', publicationAndOwnershipF, XMLNS)
            permanentDataSetURI.text = "http://openlca.org/ilcd/resource/flows/e8f942ff-7b62-4639-ac4a-f922c74c151c"
            
            flowProperty = subelement('flowProperty', flowProperties, NS3)
            flowProperty.set('dataSetInternalID', '0')
            meanValueF = subelement('meanValue', flowProperty, NS3)
            meanValueF.text = "1"
            generalCommentFFF = subelement('generalComment', flowProperty, NS3)
            generalCommentFFF.text = "Unidade: " + flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}unitName').text
            
            referenceToFlowPropertyDataSet = subelement('referenceToFlowProperty', flowProperty, NS3)
            referenceToFlowPropertyDataSet.set('type', 'flow property data set')
            FP_uuid = uuid.uuid4()
            referenceToFlowPropertyDataSet.set('refObjectId', str(FP_uuid))
            referenceToFlowPropertyDataSet.set('uri',"../flowproperties/" + str(FP_uuid) + ".xml")
            
            if flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}intermediateExchange":
                typeOfDataSetF.text = "Product flow"
            elif flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}elementaryExchange":
                typeOfDataSetF.text = "Elementary flow"
                
            #input ou output
            exchangeDirection = subelement('exchangeDirection', exchange, NS2)
            if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}inputGroup"):
                exchangeDirection.text = "input"
                #BKT pode-se ter mais tipos de fluxos (mais 2)
                
            elif flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}outputGroup"):
                exchangeDirection.text = "output" 
            
            #BKT ver como colocar certo a ordem e se isso é preciso
            if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}compartment"):
                classificationInformationF = subelement('classificationInformation', dataSetInformationF, NS3)
                elementaryFlowCategorization = subelement('elementaryFlowCategorization', classificationInformationF, XMLNS)
                catF = subelement('category', elementaryFlowCategorization, XMLNS)
                catF2 = subelement('category', elementaryFlowCategorization, XMLNS)
                catF.set('level', "0")
                catF2.set('level', "1")
                catF.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}compartment/{http://www.EcoInvent.org/EcoSpold02}compartment").text
                catF2.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}compartment/{http://www.EcoInvent.org/EcoSpold02}subcompartment").text
            
            #variables everywhere
            var = 0
            for prop in flowDataECO[ex].iterfind('{http://www.EcoInvent.org/EcoSpold02}property'):
                var = var + 1
                if prop.attrib.get('variableName') is not None:
                    variableParameter = subelement('variableParameter', mathematicalRelations, NS2)
                    variableParameter.set('name', prop.attrib.get('variableName'))
                    meanValue = subelement('meanValue', variableParameter, NS2)
                    meanValue.text = prop.attrib.get('amount')
                
                flowProperty = subelement('flowProperty', flowProperties, NS3)
                flowProperty.set('dataSetInternalID', str(var))
                meanValueF = subelement('meanValue', flowProperty, NS3)
                meanValueF.text = prop.attrib.get('amount')
                generalCommentFF = subelement('generalComment', flowProperty, NS3)
                generalCommentFF.text = "Unidade: " + prop.find("{http://www.EcoInvent.org/EcoSpold02}unitName").text + ";\tEste dado é específico para o formato Ecospold2"
            
            if flowDataECO[ex].attrib.get('variableName') is not None:
                variableParameter = subelement('variableParameter', mathematicalRelations, NS2)
                variableParameter.set('name', flowDataECO[ex].attrib['variableName'])
                meanValue = subelement('meanValue', variableParameter, NS2)
                meanValue.text = flowDataECO[ex].attrib['amount']
                comment = subelement('comment', variableParameter, NS2)
                if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty"):
                    uncertaintyDistribution = subelement("uncertaintyDistributionType", variableParameter, NS2)
                    if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty"):    
                        uncertaintyDistribution.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].tag.split('}')[1]
                    if uncertaintyDistribution.text == "lognormal":
                        uncertaintyDistribution.text = "log-normal"
                    relativeStandardDeviation95In = subelement("relativeStandardDeviation95In", exchange, NS2)
                    minimumAmount = subelement("minimumAmount", variableParameter, NS2)
                    maximumAmount = subelement("maximumAmount", variableParameter, NS2)
                    if uncertaintyDistribution.text == "log-normal":
                        relativeStandardDeviation95In.text = str(math.exp(float(flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['varianceWithPedigreeUncertainty'])**(1/2))**2)
                        minimumAmount.text = str(float(meanValue.text)/float(relativeStandardDeviation95In.text))
                        maximumAmount.text = str(float(meanValue.text)*float(relativeStandardDeviation95In.text))
                    elif uncertaintyDistribution.text == "normal":
                        relativeStandardDeviation95In.text = str(2*(float(flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['varianceWithPedigreeUncertainty'])**(1/2)))
                        minimumAmount.text = str(float(meanValue.text)-float(relativeStandardDeviation95In.text))
                        maximumAmount.text = str(float(meanValue.text)+float(relativeStandardDeviation95In.text))
                    elif uncertaintyDistribution.text == "triangular" or uncertaintyDistribution.text == "uniform":
                        minimumAmount.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['minValue']
                        maximumAmount.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['maxValue'] 
                    elif uncertaintyDistribution.text == "undefined":
                        continue
                    else:
                        comment.text = comment.text + "A incerteza deste dataset não é suportada pelo ILCD (Beta, Gamma ou Binomial)"
                
            if flowDataECO[ex].attrib.get('productionVolumeMathematicalRelation') is not None:
                variableParameter = subelement('variableParameter', mathematicalRelations, NS2)
                variableParameter.set('name', 'mathematical relation of the production of ' + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text)
                meanValue = subelement('meanValue', variableParameter, NS2)
                meanValue.text = flowDataECO[ex].attrib['productionVolumeAmount']
                formula = subelement('formula', variableParameter, NS2)
                formula.text = flowDataECO[ex].attrib['productionVolumeMathematicalRelation']
                comment = subelement('comment', variableParameter, NS2)
                
                if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}productionVolumeComment"):
                    comment.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}productionVolumeComment").text
                    
                if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}productionVolumeUncertainty"):
                    uncertaintyDistribution = subelement("uncertaintyDistributionType", variableParameter, NS2)
                    if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty"):    
                        uncertaintyDistribution.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].tag.split('}')[1]
                    if uncertaintyDistribution.text == "lognormal":
                        uncertaintyDistribution.text = "log-normal"
                    relativeStandardDeviation95In = subelement("relativeStandardDeviation95In", variableParameter, NS2)
                    minimumAmount = subelement("minimumAmount", variableParameter, NS2)
                    maximumAmount = subelement("maximumAmount", variableParameter, NS2)
                    if uncertaintyDistribution.text == "log-normal":
                        relativeStandardDeviation95In.text = str(math.exp(float(flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['varianceWithPedigreeUncertainty'])**(1/2))**2)
                        minimumAmount.text = str(float(meanValue.text)/float(relativeStandardDeviation95In.text))
                        maximumAmount.text = str(float(meanValue.text)*float(relativeStandardDeviation95In.text))
                    elif uncertaintyDistribution.text == "normal":
                        relativeStandardDeviation95In.text = str(2*(float(flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['varianceWithPedigreeUncertainty'])**(1/2)))
                        minimumAmount.text = str(float(meanValue.text)-float(relativeStandardDeviation95In.text))
                        maximumAmount.text = str(float(meanValue.text)+float(relativeStandardDeviation95In.text))
                    elif uncertaintyDistribution.text == "triangular" or uncertaintyDistribution.text == "uniform":
                        minimumAmount.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['minValue']
                        maximumAmount.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['maxValue'] 
                    elif uncertaintyDistribution.text == "undefined":
                        continue
                    else:
                        comment.text = comment.text + "A incerteza deste dataset não é suportada pelo ILCD (Beta, Gamma ou Binomial)"
    
            if flowDataECO[ex].attrib.get('productionVolumeVariableName') is not None:
                variableParameter = subelement('variableParameter', mathematicalRelations, NS2)
                variableParameter.set('name', 'production of ' + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text)
                meanValue = subelement('meanValue', variableParameter, NS2)
                meanValue.text = flowDataECO[ex].attrib['productionVolumeAmount']
            
            #reference
            if flowDataECO[ex][-1].tag == "{http://www.EcoInvent.org/EcoSpold02}outputGroup" and flowDataECO[ex][-1].text == "0":
                exchange.set('dataSetInternalID', '0')
                typeOfDataSetF.text = "Product flow"
                #BKT colocar no Flowdataset o suplly no caso de uma aparição em outro intermediate
                annualSupplyOrProductionVolume.text = flowDataECO[ex].attrib.get('productionVolumeAmount')
            else:
                count = count + 1
                exchange.set('dataSetInternalID', str(count))
            #do things
            referenceToFlowDataSet = subelement("referenceToFlowDataSet", exchange, NS2)
            referenceToFlowDataSet.set('type', 'flow data set')

            referenceToFlowDataSet.set('refObjectID', str(Ref_ex_iD))
            referenceToFlowDataSet.set('uri', '../flows/' + str(Ref_ex_iD))
            short_description_10 = subelement('shortDescription', referenceToFlowDataSet, XMLNS)
            short_description_10.set('{http://www.w3.org/XML/1998/namespace}lang','en')
            short_description_10.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text
            
            if flowDataECO[ex].attrib.get('sourceId') is not None:
                referenceToDataSource = subelement('referenceToDataSource', exchange, NS2)
                referenceToDataSource.set('type', 'source data set')
                referenceToDataSource.set('refObjectID', flowDataECO[ex].attrib.get('sourceId'))
                referenceToDataSource.set('uri', '../sources/' + flowDataECO[ex].attrib.get('sourceId'))
                subReference = subelement('subelement', referenceToDataSource, NS2)
                subReference.text = flowDataECO[ex].attrib.get('pageNumbers')
            
            exchangeDirection = subelement("exchangeDirection", exchange, NS2)
            #colocar um if pode ser mais compreensivo
            exchangeDirection.text = str(flowDataECO[ex][-1].tag).split('}')[1][:-5].capitalize()
            
            #values
            meanAmount = subelement("meanAmount", exchange, NS2)
            resultingAmount = subelement("resultingAmount", exchange, NS2)
            meanAmount.text = flowDataECO[ex].attrib['amount']
            resultingAmount.text = flowDataECO[ex].attrib['amount']
            
            #BKT colocar os parâmetros da Pedigree
            generalComment_unc = subelement("generalComment", exchange, NS2)
            pedigree = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty/{http://www.EcoInvent.org/EcoSpold02}pedigreeMatrix")
            if pedigree is not None:
                generalComment_unc.text = "Pedigree Matrix for this exchange: (" + pedigree.attrib["reliability"] + ',' + pedigree.attrib["completeness"] + ',' + pedigree.attrib["temporalCorrelation"] + ',' + pedigree.attrib["geographicalCorrelation"] + ',' + pedigree.attrib["furtherTechnologyCorrelation"] + '). The variance generated by the Pedigree matrix and basic uncertainties were: ' + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['varianceWithPedigreeUncertainty']
                if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}comment"):
                   generalComment_unc.text =  generalComment_unc.text + '/tComentário geral: ' + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}comment")
            
            uncertaintyDistribution = subelement("uncertaintyDistributionType", exchange, NS2)
            if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty"):    
                uncertaintyDistribution.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].tag.split('}')[1]
            if uncertaintyDistribution.text == "lognormal":
                uncertaintyDistribution.text = "log-normal"
            relativeStandardDeviation95In = subelement("relativeStandardDeviation95In", exchange, NS2)
            minimumAmount = subelement("minimumAmount", exchange, NS2)
            maximumAmount = subelement("maximumAmount", exchange, NS2)
            if uncertaintyDistribution.text == "log-normal":
                relativeStandardDeviation95In.text = str(math.exp(float(flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['varianceWithPedigreeUncertainty'])**(1/2))**2)
                minimumAmount.text = str(float(meanAmount.text)/float(relativeStandardDeviation95In.text))
                maximumAmount.text = str(float(meanAmount.text)*float(relativeStandardDeviation95In.text))
            elif uncertaintyDistribution.text == "normal":
                relativeStandardDeviation95In.text = str(2*(float(flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['varianceWithPedigreeUncertainty'])**(1/2)))
                minimumAmount.text = str(float(meanAmount.text)-float(relativeStandardDeviation95In.text))
                maximumAmount.text = str(float(meanAmount.text)+float(relativeStandardDeviation95In.text))
            elif uncertaintyDistribution.text == "triangular" or uncertaintyDistribution.text == "uniform":
                minimumAmount.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['minValue']
                maximumAmount.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['maxValue'] 
            elif uncertaintyDistribution.text == "undefined":
                continue
            else:
                if pedigree is not None:
                    generalComment_unc.text = generalComment_unc.text + "A incerteza deste dataset não é suportada pelo ILCD (Beta, Gamma ou Binomial)"

            #maths
            #BKT colocar o productionVolume quando houver no LCI
            #BKT problemas ao abrir as relações matemáticas
            if flowDataECO[ex].attrib.get('isCalculatedAmount') == "true":
                meanAmount.text = "1.0"
                variableParameter = subelement('variableParameter', mathematicalRelations, NS2)
                variableParameter.set('name', flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text + " relation")
                formula = subelement('formula', variableParameter, NS2)
                formula.text = flowDataECO[ex].attrib.get('mathematicalRelation')
                meanValue = subelement('meanValue', variableParameter, NS2)
                meanValue.text = flowDataECO[ex].attrib.get('amount')
                referenceToVariable = subelement('referenceToVariable', exchange, NS2)
                referenceToVariable.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text + " relation"
        
            file_flow = "./" + UUIDF.text + ".xml"
            #file_flow = "./" + str(Ref_ex_iD) + ".xml"
            with open(file_flow, 'wb') as Flow:
                Flow.write(etree.tostring(flowDataSet, pretty_print = True, xml_declaration = True, encoding='UTF-8', standalone="yes"))
                ILCD_zip.write(file_flow, 'ILCD\\flows\\' + file_flow, zipfile.ZIP_DEFLATED)
        
        elif flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}parameter":
            
            variableParameter = subelement('variableParameter', mathematicalRelations, NS2)
            variableParameter.set('name', flowDataECO[ex].attrib['variableName'])
            
            if flowDataECO[ex].attrib.get('isCalculatedAmount') == 'true':
                formula = subelement('formula', variableParameter, NS2)
                formula.text = flowDataECO[ex].attrib.get('mathematicalRelation')
                
            meanValue = subelement('meanValue', variableParameter, NS2)
            meanValue.text = flowDataECO[ex].attrib.get('amount')
            
            #BKT element is not None
            comment = subelement('comment', variableParameter, NS2)
            comment.set('{http://www.w3.org/XML/1998/namespace}lang','en')
            if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}unitName"):
                comment.text = "Unidade: " + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}unitName").text
            if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}comment"):
                comment.text = comment.text + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}comment").text
            
            if flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}uncertainty'):
                
                uncertaintyDistribution = subelement("uncertaintyDistributionType", variableParameter, NS2)
                if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty"):    
                    uncertaintyDistribution.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].tag.split('}')[1]
                if uncertaintyDistribution.text == "lognormal":
                    uncertaintyDistribution.text = "log-normal"
                    
                relativeStandardDeviation95In = subelement("relativeStandardDeviation95In", variableParameter, NS2)
                minimumAmount = subelement("minimumAmount", variableParameter, NS2)
                maximumAmount = subelement("maximumAmount", variableParameter, NS2)
                
                if uncertaintyDistribution.text == "log-normal":
                    relativeStandardDeviation95In.text = str(math.exp(float(flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['varianceWithPedigreeUncertainty'])**(1/2))**2)
                    minimumAmount.text = str(float(meanAmount.text)/float(relativeStandardDeviation95In.text))
                    maximumAmount.text = str(float(meanAmount.text)*float(relativeStandardDeviation95In.text))
                elif uncertaintyDistribution.text == "normal":
                    relativeStandardDeviation95In.text = str(2*(float(flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['varianceWithPedigreeUncertainty'])**(1/2)))
                    minimumAmount.text = str(float(meanAmount.text)-float(relativeStandardDeviation95In.text))
                    maximumAmount.text = str(float(meanAmount.text)+float(relativeStandardDeviation95In.text))
                elif uncertaintyDistribution.text == "triangular" or uncertaintyDistribution.text == "uniform":
                    minimumAmount.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['minValue']
                    maximumAmount.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['maxValue'] 
                elif uncertaintyDistribution.text == "undefined":
                    continue
                else:
                    comment.text = comment.text + "A incerteza deste dataset não é suportada pelo ILCD (Beta, Gamma ou Binomial)"
        
    #print(etree.tostring(processDataSet, pretty_print = True).decode())
    
    #BKT talvez eliminar todos os elementos em branco do dataset
    file_process = "./" + activityDescription[0].attrib["activityNameId"] + '.xml'
    with open(file_process, 'wb') as f:
        f.write(etree.tostring(processDataSet, pretty_print = True, xml_declaration = True, encoding='UTF-8', standalone="yes"))
        ILCD_zip.write(file_process, 'ILCD\\processes\\' + file_process, zipfile.ZIP_DEFLATED)
    
    ILCD_zip.close()

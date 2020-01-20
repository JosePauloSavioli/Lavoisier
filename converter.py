# -*- coding: utf-8 -*-
"""

Conversão de dados de Ecospold2 para ILCD para o IBICT

PROB = Problema

"""

#BKT verificação com o relaxlxml dos arquivos xsd
#BKT Verificar LCIA e possíveis agregações de produtos (adicional)
#BKT verificar fórmulas e parâmetros

#importação das bibliotecas

#trabalho com xml (leitura e escrita)
from lxml import etree
#trabalho com uuid's (geração)
import uuid
#trabalho com variáveis de tempo
import time
#library básica para cálculos matemáticos
import math
#criação e interação com arquivos zip (criação do arquivo ILCD)
import zipfile
#library de interação com o sistema
import os
#trabalho com csv (leitura e escrita)
import csv
#trabalho com transferência de arquivos
import shutil

#bibliotecas de arquivos

#funções adicionais
import additional_functions as af
#funções para criação de arquivos de contato e bibliografia
import file_creation as fc
#funções para criação da database de propriedades de fluxos e grupos de unidades (usada somente na primeira vez para criar a database)
#import flow_prop_and_unit_groups as fau

#criar o zip do arquivo final ILCD a partir dos arquivos iniciais
def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

#criação dos namescapes dos arquivos xml
def namespaces(link):
    ns = link
    NS = "{%s}" %link
    return ns, NS

def incerteza(flowDataECO, meanValue, parent, NS, gc):

    if flowDataECO.find("{http://www.EcoInvent.org/EcoSpold02}uncertainty") is not None:
        if gc is not None:
            minimumAmount = af.subelement("minimumAmount", parent, NS)
            maximumAmount = af.subelement("maximumAmount", parent, NS)
        else:
            minimumAmount = af.subelement("minimumValue", parent, NS)
            maximumAmount = af.subelement("maximumValue", parent, NS)
        uncertaintyDistribution = af.subelement("uncertaintyDistributionType", parent, NS)
        uncertaintyDistribution.text = flowDataECO.find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].tag.split('}')[1]
    
        if uncertaintyDistribution.text == "lognormal":
            uncertaintyDistribution.text = "log-normal"
        
        relativeStandardDeviation95In = af.subelement("relativeStandardDeviation95In", parent, NS)
        
        
        if uncertaintyDistribution.text == "log-normal":
            relativeStandardDeviation95In.text = str(round(math.exp(float(flowDataECO.find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['varianceWithPedigreeUncertainty'])**(1/2))**2,3))
            minimumAmount.text = str(float(meanValue.text)/float(relativeStandardDeviation95In.text))
            maximumAmount.text = str(float(meanValue.text)*float(relativeStandardDeviation95In.text))
        elif uncertaintyDistribution.text == "normal":
            relativeStandardDeviation95In.text = str(round(2*(float(flowDataECO.find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['varianceWithPedigreeUncertainty'])**(1/2),3)))
            minimumAmount.text = str(float(meanValue.text)-float(relativeStandardDeviation95In.text))
            maximumAmount.text = str(float(meanValue.text)+float(relativeStandardDeviation95In.text))
        elif uncertaintyDistribution.text == "triangular" or uncertaintyDistribution.text == "uniform":
            minimumAmount.text = flowDataECO.find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['minValue']
            maximumAmount.text = flowDataECO.find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['maxValue'] 
        elif uncertaintyDistribution.text == "undefined":
            pass
        else:
            comment = af.subelement('comment', parent, NS)
            comment.text = "A incerteza deste dataset não é suportada pelo ILCD (Beta, Gamma ou Binomial)"

def f_property(flowProperty, unitName, internal_id, m_v):
    
    flowProperty.set('dataSetInternalID', internal_id)
    
    #flowProperty[0]
    referenceToFlowPropertyDataSet = af.subelement('referenceToFlowPropertyDataSet', flowProperty, NS3)
    
    with open('conversion_3.csv') as conv_csv_unit:
        conv_r = csv.reader(conv_csv_unit, delimiter = ',')
        for row in conv_r:
            r = [row[0]] + row[4:]
            if unitName in r:
                ref_id_unit = row[1]
                ref_id_name = row[2]
                ref_id_unit_id = row[3]
                break
    af.referencia(referenceToFlowPropertyDataSet, 'flow property data set', ref_id_unit, XMLNS, ref_id_name)

    #flowProperty[1] - valor estipulado por mim pois ele vai ser multiplicado pela quantidade de fluxo do processDataSet
    meanValueF = af.subelement('meanValue', flowProperty, NS3)
    meanValueF.text = m_v
    
    return ref_id_unit, ref_id_unit_id, m_v

if __name__ == '__main__':
    
    #inicialização do zip
    ILCD_zip = zipfile.ZipFile('./ILCD.zip', 'w')
    
    #inicialização da pasta fonte do ILCD.zip
    try:
        os.mkdir("./ILCD-algorithm")
    except OSError:
        pass
    
    #parser para ler arquivo Ecospold2
    parser = etree.XMLParser(remove_blank_text = True)
    
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
    
    #inicialização da database de propriedades de fluxos e unidades (somente uma vez)
    #fau.inicialization(NS5, NS7, XMLNS, nsmap)
    
    #criando árvore do arquivo Ecospold2
    Ecospold2_tree = etree.parse('./eucalyptus seedling production, in heated greenhouse, BR, 2010 - 2020.spold', parser)
    
    #elemento raiz do arquivo Ecospold2
    ecoSpold = Ecospold2_tree.getroot()
    
    #subelementos iniciais do arquivo Ecospold2
    activityDescription = ecoSpold[0][0]
    flowDataECO = ecoSpold[0][1]
    modellingAndValidationECO = ecoSpold[0][2]
    administrativeInformationECO = ecoSpold[0][3]
    
    #elemento raiz do dataset ILCD
    processDataSet = etree.Element(NS2 + 'processDataSet', version = "1.1", nsmap = nsmap)

    #declaração dos subelementos iniciais ILCD (O subelemento LCIAResults não foi incluído por se tratarem de datasets de processos)
    processInformation = af.subelement('processInformation', processDataSet, NS2)
    modellingAndValidation = af.subelement('modellingAndValidation', processDataSet, NS2)
    administrativeInformation = af.subelement('administrativeInformation', processDataSet, NS2)
    exchanges = af.subelement('exchanges', processDataSet, NS2)
    
    #processInformation[0] - dataSetInformation
    dataSetInformation = af.subelement('dataSetInformation', processInformation, NS2)
    
    #Campos não incluidos no dataSetInformation: 
        #identifierOfSubDataSet: Identifica se o dataset pertence a um conjunto maior de datasets, como um LCI completo
        #complementingProcesses: Identifica os processos complementares do LCI ao qual o dataset pertence se tiver o campo identifierOfSubDataSet
    
    #dataSetInformation[0] - UUID do processo
    UUID = af.subelement('UUID', dataSetInformation, XMLNS)
    UUID.text = activityDescription[0].attrib["activityNameId"]
    
    #dataSetInformation[1] - nome do processo (dentro do baseName)
    name = af.subelement('name', dataSetInformation, NS2)
    baseName = af.subelement('baseName', name, NS2)
    baseName.attrib['{http://www.w3.org/XML/1998/namespace}lang'] = "en"
    baseName.text = activityDescription[0][0].text
    
    #dataSetInformation[2] - sinônimos se houver
    if activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}synonyms') is not None:
        synonyms = af.subelement('synonyms', dataSetInformation, XMLNS)
        synonyms.text = activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}synonyms')
    
    #dataSetInformation[3] - classificação (hierarquia na database - função especial) [somente a classificação ISIC foi abordada]
    classificationInformation = af.subelement('classificationInformation', dataSetInformation, NS2)
    classification = af.subelement('classification', classificationInformation, XMLNS)
    
    classes = [c for c in activityDescription if c.tag == '{http://www.EcoInvent.org/EcoSpold02}classification']
    for cl_info in classes:
        if cl_info[0].text == 'ISIC rev.4 ecoinvent':
            #class_name = cl_info[0].text
            class_value = cl_info[1].text
    af.do_classification(class_value, classification, XMLNS)
    
    #dataSetInformation[4] - comentário (contém o tipo espcífico de atividade, dependência de outros datasets (Child), as tags e o texto do comentário geral do Ecospold2)
    generalComment = af.subelement('generalComment', dataSetInformation, XMLNS)
    generalComment.attrib['{http://www.w3.org/XML/1998/namespace}lang'] = "en"
    generalComment.text = ''
    
    list_for_special_activity = ['ordinary transforming activity','market activity','IO activity','residual activity','production mix','import activity','supply mix','export activity','re-Export activity','correction activity','market group']
    if activityDescription[0].attrib['inheritanceDepth'] == "0":
        is_child = "parent"
        uuid_parent = "none"
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
    
    generalComment.text = "Type of process: " + list_for_special_activity[int(activityDescription[0].attrib['specialActivityType'])] + "; Relation Ecospold2: " + is_child + " from " + uuid_parent + "\nTags: " + tag_t
    
    for gc_elem in activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}generalComment'):
        if gc_elem.tag == '{http://www.EcoInvent.org/EcoSpold02}imageUrl':
            generalComment.text = generalComment.text + '\nImageURL: ' + gc_elem.text
        else:
            generalComment.text = generalComment.text + '\n' + gc_elem.text
    
    #dataSetInformation[5] - aqui serão colocadas a publicação que gerou o dataset e ícones de dataset (dataSetIcon) se presente
    referenceToExternalDocumentation = af.subelement('referenceToExternalDocumentation', dataSetInformation, NS2)
    
    if administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['dataPublishedIn'] == "0":
        publication_status = "Dataset finalised; unpublished"
    elif administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['dataPublishedIn'] == "1":
        publication_status = "Data set finalised; subsystems published"
    elif administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['dataPublishedIn'] == "2":
        publication_status = "Data set finalised; entirely published"
    
    af.referencia(referenceToExternalDocumentation, 'source data set', administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['publishedSourceId'], XMLNS, publication_status)
    
    if activityDescription[0].get('dataSetIcon') is not None:
        referenceToExternalDocument = af.subelement('referenceToExternalDocument', dataSetInformation, NS2)
        ID_dataSetIcon = uuid.uuid4()
        af.referencia(referenceToExternalDocument, 'source data set', ID_dataSetIcon, XMLNS, "dataSetIcon")
        fc.sources(ID_dataSetIcon, etree.Element(NS6 + "sourceDataSet", version = "1.1", nsmap=nsmap), NS6, XMLNS, "dataSetIcon")
    
    #processInformation[1] - quantitativeInformation (Somente se usa o caso do ReferenceFlow pois é a única informação do Ecospold2, mas é possível colocar por exemplo a unidade funcional como um adicional)
    quantitativeInformation = af.subelement('quantitativeReference', processInformation, NS2)
    quantitativeInformation.set('type', 'Reference flow(s)')
    
    #Campos não incluidos no quantitativeInformation:
        #functionalUnitOrOther: Descrição da unidade funcional ou do parâmetro dado em quantitativeInformation[@type] quando não for 'Reference flow(s)'
    
    #quantitativeInformation[0]
    referenceToReferenceFlow = af.subelement('referenceToReferenceFlow', quantitativeInformation, NS2)
    referenceToReferenceFlow.text = "0"
    
    #processInformation[2] - Time
    tim_ = af.subelement('time', processInformation, NS2)
    
    #time[0] e [1] - primeira parte para acessar a data do Ecospold2
    startDateEco = activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}timePeriod').attrib['startDate']
    endDateEco = activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}timePeriod').attrib['endDate']
    stdILCD = time.strptime(startDateEco, '%Y-%m-%d')
    endILCD = time.strptime(endDateEco, '%Y-%m-%d')
    
    referenceYear = af.subelement('referenceYear', tim_, XMLNS)
    referenceYear.text = str(stdILCD.tm_year)
    
    dataSetValidUntil = af.subelement('dataSetValidUntil', tim_, XMLNS)
    if endILCD.tm_mon > 6:
        dataSetValidUntil.text = str(endILCD.tm_year + 1)
    else:
        dataSetValidUntil.text = str(endILCD.tm_year)
    
    #time[2]
    timeRepresentativenessDescription = af.subelement('timeRepresentativenessDescription', tim_, XMLNS)
    timeRepresentativenessDescription.attrib['{http://www.w3.org/XML/1998/namespace}lang'] = 'en'
    
    if activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}timePeriod').attrib['isDataValidForEntirePeriod'] == "true":
        is_valid = "Data is valid for the entire period"
    else:
        is_valid = "Data is not valid for the entire period, check this comment for more information"
    
    if activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}timePeriod/{http://www.EcoInvent.org/EcoSpold02}comment/{http://www.EcoInvent.org/EcoSpold02}text').text is not None:
        timeRepresentativenessDescription.text = is_valid + '\n' + activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}timePeriod/{http://www.EcoInvent.org/EcoSpold02}comment/{http://www.EcoInvent.org/EcoSpold02}text').text
    
    #processInformation[3] - Geography
    
    #Campos não incluidos no geography:
        #subLocationOfOperationSupplyOrProduction: Não há informações adicionais sobre as sub-localizações, se estas tiverem no comentário do Ecospold2, serão colocadas como comentário no ILCD também 
        #locationOfOperationSupplyOrProduction[@latitudeAndLongitude]: Não há informações sobre lat ou long nos campos do Ecospold2
    
    geography = af.subelement('geography', processInformation, NS2)
    
    #geography[0]
    locationOfOperationSupplyOrProduction = af.subelement('locationOfOperationSupplyOrProduction', geography, NS2)
    locationOfOperationSupplyOrProduction.set('location',activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}geography/{http://www.EcoInvent.org/EcoSpold02}shortname').text)
    
    descriptionOfRestrictions = af.subelement('descriptionOfRestrictions', locationOfOperationSupplyOrProduction, NS2)
    descriptionOfRestrictions.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    descriptionOfRestrictions.text = activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}geography/{http://www.EcoInvent.org/EcoSpold02}comment/{http://www.EcoInvent.org/EcoSpold02}text').text
    
    #processInformation[4] - Technology
    
    #Campos não incluidos no technology: (mathematicalRelations estão na parte de fluxos pois se encontram junto destes no Ecospold2)
        #referenceToIncludedProcesses: Este campo só tem valores se o processo for uma 'complete LCI' ou semelhante que engloba varios processos, sendo onde estes processos, se existirem como dataset, são nomeados. Como esta conversão engloba apenas o processo, este campo não será utilizado
        #referenceToTechnologyFlowDiagramOrPicture: Figuras presentes no comentário como URL serão colocadas no campo referenceToTechnologyPictogramme
    
    technology = af.subelement('technology', processInformation, NS2)
    
    #technology[0]
    list_of_technologies = ['Undefined','New','Modern','Current','Old','Outdated']
    technologyDescriptionAndIncludedProcesses = af.subelement('technologyDescriptionAndIncludedProcesses', technology, NS2)
    technologyDescriptionAndIncludedProcesses.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    technologyDescriptionAndIncludedProcesses.text = "The technology level of this process is: " + list_of_technologies[int(activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}technology').attrib['technologyLevel'])] + "\nThe included activities go from: " + activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}includedActivitiesStart').text + " to: " + activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}includedActivitiesEnd').text
    
    #technology[1] e [2]
    technologyApplicability = af.subelement('technologicalApplicability', technology, NS2)
    technologyApplicability.text = activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}technology/{http://www.EcoInvent.org/EcoSpold02}comment/{http://www.EcoInvent.org/EcoSpold02}text').text
    
    #technology[2]
    for ta_elem in activityDescription.find('{http://www.EcoInvent.org/EcoSpold02}technology/{http://www.EcoInvent.org/EcoSpold02}comment'):
        if ta_elem.tag == '{http://www.EcoInvent.org/EcoSpold02}imageUrl':
            referenceToTechnologyPictogramme = af.subelement('referenceToTechnologyPictogramme', technology, XMLNS)
            ID_tech = uuid.uuid4()
            af.referencia(referenceToTechnologyPictogramme, 'source data set', ID_tech, XMLNS, 'Comment URL')
        else:
            technologyApplicability.text = technologyApplicability.text + '\n' + ta_elem.text
   
    #modellingAndValidation[0] - LCIMethodAndAllocation
    
    #Campos não incluidos no LCIMethodAndAllocation:
        #deviationsFromModellingConstants: Não há campo no Ecospold2 com esta informação
        #referenceToLCAMethodDetails: Não há um campo com referência bibliográfica do método utilizado na ACV dentro do Ecospold2
    
    LCIMethodAndAllocation = af.subelement('LCIMethodAndAllocation', modellingAndValidation, NS2)
    
    #LCIMethodAndAllocation[0] - (os tipos de dataset no ILCD são 4, mas no Ecospold são apenas 2, então a conversão é feita apenas para os dois)
    typeOfDataSet = af.subelement('typeOfDataSet', LCIMethodAndAllocation, NS2)
    list_of_type_process = ['','Unit process, black box','LCI result']
    typeOfDataSet.text = list_of_type_process[int(activityDescription[0].attrib['type'])]

    #LCIMethodAndAllocation[1], [2], [3] e [4] - (neste caso [LCIMethodPrinciple] são 5 tipos de modelos de sistema no ILCD e 3 no Ecospold2, então a conversão é feita para os 3)
        #Como os LCIMethodApproach são uma informação enumerada e muito específica da propriedade utilizada na alocação, este será colocado como other pois não tenho como saber
    LCIMethodPrinciple = af.subelement('LCIMethodPrinciple', LCIMethodAndAllocation, NS2)
    deviationsFromLCIMethodPrinciples = af.subelement('deviationsFromLCIMethodPrinciple', LCIMethodAndAllocation, NS2)
    LCIMethodApproach = af.subelement('LCIMethodApproaches', LCIMethodAndAllocation, NS2)
    
    deviationsFromLCIMethodPrinciples.text = 'Ecospold original system model: ' + modellingAndValidationECO[0].find('{http://www.EcoInvent.org/EcoSpold02}systemModelName').text
    if activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}allocationComment') is not None:
        deviationsFromLCIMethodApproach = af.subelement('deviationsFromLCIMethodApproaches', LCIMethodAndAllocation, NS2)
        deviationsFromLCIMethodApproach.text = activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}allocationComment').text
    
    if modellingAndValidationECO[0].find('{http://www.EcoInvent.org/EcoSpold02}systemModelName').text == 'Undefined':
        LCIMethodPrinciple.text = "Not applicable"
        LCIMethodApproach.text = "Not applicable"
    elif modellingAndValidationECO[0].find('{http://www.EcoInvent.org/EcoSpold02}systemModelName').text == 'Attributional, average current suppliers, revenue allocation':
        LCIMethodPrinciple.text = "Attributional"
        LCIMethodApproach.text = "Other"
    elif modellingAndValidationECO[0].find('{http://www.EcoInvent.org/EcoSpold02}systemModelName').text == 'Consequential, small-scale, long-term decisions':
        LCIMethodPrinciple.text = "Consequential"
        LCIMethodApproach.text = "Other"
    
    #LCIMethodAndAllocation[5] - (os valores de energyValue, se existentes, são colocados neste campo)
    if activityDescription[0].attrib.get('energyValue') is not None:
        modellingConstants = af.subelement('modellingConstants', LCIMethodAndAllocation, NS2)
        modellingConstants.text = activityDescription[0].find('{http://www.EcoInvent.org/EcoSpold02}allocationComment').attrib.get('energyValue')
    
    #modellingAndValidation[1] - DataSourcesTreatmentAndRepresentativeness
    
    #Campos não incluídos no dataSourcesTreatmentAndRepresentativeness: (annualSupplyOrProductionVolume dado por fluxo [pois a informação no Ecospold2 está no fluxo])
        #deviationsFromCutOffAndCompletenessPrinciples: Não há campo no Ecospold2
        #deviationsFromSelectionAndCombinationPrinciples: Não há campo no Ecospold2
        #deviationsFromTreatmentAndExtrapolation: Não há campo no Ecospold2
        #referenceToDataHandlingPrinciples: Não há uma referência quanto a como a LCI foi tratada na forma de bibliografia no Ecospold2
        #referenceToDataSource: PROB: Colocar a documentação de apoio ou o artigo publicado neste campo quando terminar para indicar como foi feita a metodologia de conversão
        #dataCollectionPeriod: Não há um campo com o período de coleta dos dados no Ecospold2
        #useAdviceForDataSet: Não há campo no Ecospold2
        
    dataSourcesTreatmentAndRepresentativeness = af.subelement('dataSourcesTreatmentAndRepresentativeness', modellingAndValidation, NS2)
    
    #dataSourcesTreatmentAndRepresentativeness[0]
    dataCutOffAndCompletenessPrinciples = af.subelement('dataCutOffAndCompletenessPrinciples', dataSourcesTreatmentAndRepresentativeness, NS2)
    dataCutOffAndCompletenessPrinciples.text = "None"
    
    #dataSourcesTreatmentAndRepresentativeness[1]
    dataSelectionAndCombinationPrinciples = af.subelement('dataSelectionAndCombinationPrinciples', dataSourcesTreatmentAndRepresentativeness, NS2)
    dataSelectionAndCombinationPrinciples.text = "None"
    
    #dataSourcesTreatmentAndRepresentativeness[2]
    dataTreatmentAndExtrapolation = af.subelement('dataTreatmentAndExtrapolationsPrinciples', dataSourcesTreatmentAndRepresentativeness, NS2)
    dataTreatmentAndExtrapolation.text = modellingAndValidationECO[0].find('{http://www.EcoInvent.org/EcoSpold02}extrapolations').text
    
    #dataSourcesTreatmentAndRepresentativeness[3]
    if modellingAndValidationECO[0].attrib.get('percent') is not None:
        percentageSupplyOrProductionCovered = af.subelement('percentageSupplyOrProductionCovered', dataSourcesTreatmentAndRepresentativeness, NS2)
        percentageSupplyOrProductionCovered.text = modellingAndValidationECO[0].attrib.get('percent')
    
    #modellingAndValidation[2] - Completeness
    
    #Campos não incluídos no completeness: (muitos campos não são incluídos pois a completeza se refere à AICV e em quais impactos que cada fluxo elemental impacta)
        #Os campos do completeness são abordados nos fluxos
        
    completeness = af.subelement('completeness', modellingAndValidation, NS2)
    
    #completeness[0] - (como é um dataset do ecoinvent, coloquei como todos os fluxos relevantes abordados)
    completenessProductModel = af.subelement('completenessProductModel', completeness, NS2)
    completenessProductModel.text = "All relevant flows quantified"

    #modellingAndValidation[3] - Validation
    
    #Campos não incluídos no validation: (o review no ILCD tem muitos campos para análise de como foi feito a revisão em cada parte da acv, mas estes campos não existem no Ecospold2, onde a informação esta em dois campos de texto genéricos)
        #scope[@name]/method[@name]: não há campo no Ecospold2 com nomes dos métodos utilizados no review
        #referenceToCompleteReviewRoport: não há campo com o Id da referência para bibliografia de revisão
        #scope[@name]/dataQualityIndicators: Apesar de haver a matriz Pedigree dos fluxos do dataset, como o fluxo principal não a possui, não da pra colocar ela neste campo
        
    validation = af.subelement('validation', modellingAndValidation, NS2)
    
    #validation[0] - (loop para cada review)
    for rev in range(len(modellingAndValidationECO)):
        if modellingAndValidationECO[rev].tag == "{http://www.EcoInvent.org/EcoSpold02}review":
            review = af.subelement('review', validation, NS2)
            
            #review[1]
            reviewDetails = af.subelement('reviewDetails', review, XMLNS)
            reviewDetails.text = "Date of last review: " + modellingAndValidationECO[rev].attrib['reviewDate'] + '; Major version: ' + modellingAndValidationECO[rev].attrib['reviewedMajorRelease'] + '.' + modellingAndValidationECO[rev].attrib['reviewedMajorRevision'] + '; Minor version: ' + modellingAndValidationECO[rev].attrib['reviewedMinorRelease'] + '.' + modellingAndValidationECO[rev].attrib['reviewedMinorRevision']
            
            #review[0]
            referenceToNameOfReviewerAndInstitution = af.subelement('referenceToNameOfReviewerAndInstitution', review, XMLNS)  
            af.referencia(referenceToNameOfReviewerAndInstitution, 'contact data set', modellingAndValidationECO[rev].attrib['reviewerId'], XMLNS, modellingAndValidationECO[rev].attrib['reviewerName'])
            
            contactDataSet = etree.Element(NS4 + 'contactDataSet', version = "1.1", nsmap=nsmap)
            fc.contacts(modellingAndValidationECO[rev].attrib['reviewerId'], contactDataSet, NS4, XMLNS, modellingAndValidationECO[rev].attrib['reviewerName'], modellingAndValidationECO[rev].attrib['reviewerEmail'])
            
            #review[2]
            otherDetails = af.subelement('otherReviewDetails', review, XMLNS)
            otherDetails.text = modellingAndValidationECO[rev].find('{http://www.EcoInvent.org/EcoSpold02}otherDetails').text
            
    
    #modellingAndValidation[4] - ComplianceDeclarations
    #Seu campo compliance e suas ramificações como reviewCompliance não possuem campo no Ecospold2 [apesar de que o ecoinvent possui ferramentas para averiguar a conformidade]
    
    #administrativeInformation[0] - ComissionerAndGoals
    
    #Campos não incluidos no comissionerAndGoals:
        #referenceToComissioner: Não há informação em campos do Ecospold2 sobre financiadores do projeto
        #project: Não há no Ecospold2 o nome do projeto
    
    comissionerAndGoals = af.subelement('commissionerAndGoal', administrativeInformation, XMLNS)
    
    #comissionerAndGoals[0]
    intendedApplications = af.subelement('intendedApplications', comissionerAndGoals, XMLNS)
    intendedApplications.set('{http://www.w3.org/XML/1998/namespace}lang','en')
    intendedApplications.text = "Can be used for any types of LCA studies"
    
    #administrativeInformation[1] - DataGenerator
    dataGenerator = af.subelement('dataGenerator', administrativeInformation, NS2)
    
    #dataGenerator[0]
    referenceToPersonOrEntityGeneratingTheDataSet = af.subelement('referenceToPersonOrEntityGeneratingTheDataSet', dataGenerator, XMLNS)
    af.referencia(referenceToPersonOrEntityGeneratingTheDataSet, 'contact data set', administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['personId'], XMLNS, administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['personName'])
    
    contactDataSet = etree.Element(NS4 + 'contactDataSet', version = "1.1", nsmap=nsmap)
    fc.contacts(administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['personId'], contactDataSet, NS4, XMLNS, administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['personName'], administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['personEmail'])
    
    #administrativeInformation[2] - DataEntryBy
    
    #Campos não incluidos no dataEntryBy:
        #referenceToDataSetApproval: Não há correspondência no Ecospold2, uma opção seria colocar o source do próprio ecoinvent, mas o arquivo .spold não tem ele
        #referenceToConvertedOriginalDataSetFrom: Não há correspondência no Ecospold2, uma opção seria colocar o source do próprio ecoinvent, mas o arquivo .spold não tem ele
    
    dataEntryBy = af.subelement('dataEntryBy', administrativeInformation, NS2)
    
    #dataEntryBy[0]
    timeStamp = af.subelement('timeStamp', dataEntryBy, XMLNS)
    t_stamp = time.localtime()
    t_stamp_string = time.strftime("%Y-%m-%dT%H:%M:%S", t_stamp)
    timeStamp.text = t_stamp_string
    
    #dataEntryBy[1]
    referenceToDataSetFormat = af.subelement('referenceToDataSetFormat', dataEntryBy, XMLNS)
    af.referencia(referenceToDataSetFormat, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', XMLNS, 'ILCD Format', '01.01.000')
    
    fc.sources("a97a0155-0234-4b87-b4ce-a45da52f2a40", etree.Element(NS6 + "sourceDataSet", version = "1.1", nsmap=nsmap), NS6, XMLNS, "ILCD Format")
    
    #dataEntryBy[2]
    referenceToPersonOrEntityEnteringTheData = af.subelement('referenceToPersonOrEntityEnteringTheData', dataEntryBy, XMLNS)
    af.referencia(referenceToPersonOrEntityEnteringTheData, 'contact data set', administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataEntryBy').attrib['personId'], XMLNS, administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataEntryBy').attrib['personName'])
    
    contactDataSet = etree.Element(NS4 + 'contactDataSet', version = "1.1", nsmap=nsmap)
    fc.contacts(administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataEntryBy').attrib['personId'], contactDataSet, NS4, XMLNS, administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataEntryBy').attrib['personName'], administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataEntryBy').attrib['personEmail'])
    
    #administrativeInformation[3] - PublicationAndOwnership
    
    #Campos não incluidos no dataEntryBy:
        #referenceToPrecedingDataSetVersion: Não há a informação no Ecospold2 do UUID das versões anteriores
        #referenceToRegistrationAuthority: Não há um campo da autoridade de registro do ecoinvent
        #registrationNumber: Não há campo no Ecospold2
        #referenceToOwnershipOfDataSet: Acredito ser o ecoinvent, mas não tenho dados disso
        
    publicationAndOwnership = af.subelement('publicationAndOwnership', administrativeInformation, NS2)
    
    #publicationAndOwnership[0]
    dateOfLastRevision = af.subelement('dateOfLastRevision', publicationAndOwnership, XMLNS)
    dateOfLastRevision.text = administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}fileAttributes').attrib['lastEditTimestamp']
    
    #publicationAndOwnership[1] - (Major Updates . Minor Revisions . 000 no dataSetVersion (00.00.000), últimos 3 números são para checagem interna)
    dataSetVersion = af.subelement('dataSetVersion', publicationAndOwnership, XMLNS)
    dataSetVersion.text = "0" + administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}fileAttributes').attrib['majorRelease'] + ".0" + administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}fileAttributes').attrib['minorRevision'] + ".000"
    
    #publicationAndOwnership[2] - PROB: checar se é plausível colocar assim
    permanentDataSetURI = af.subelement('permanentDataSetURI', publicationAndOwnership, XMLNS)
    permanentDataSetURI.text = 'http://sicv.acv.ibict.br'
    
    #publicationAndOwnership[3] - PROB: Talvez grupos sejam Commom
    workflowAndPublicationStatus = af.subelement('workflowAndPublicationStatus', publicationAndOwnership, XMLNS)
    if administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['dataPublishedIn'] == "0":
        workflowAndPublicationStatus.text = "Dataset finalised; unpublished"
    elif administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['dataPublishedIn'] == "1":
        workflowAndPublicationStatus.text = "Data set finalised; subsystems published"
    elif administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['dataPublishedIn'] == "2":
        workflowAndPublicationStatus.text = "Data set finalised; entirely published"
    
    #publicationAndOwnership[4]
    referenceToUnchangedPublication = af.subelement('referenceToUnchangedRepublication', publicationAndOwnership, XMLNS)
    af.referencia(referenceToUnchangedPublication, 'source data set', administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['publishedSourceId'], XMLNS, administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['publishedSourceId'])

    lista = []
    if administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['publishedSourceId'] not in lista:
        lista.append(administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['publishedSourceId'])
        citation_publication = administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['publishedSourceFirstAuthor'] + " (" + administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['publishedSourceYear'] + ")"
        fc.sources(administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['publishedSourceId'], etree.Element(NS6 + "sourceDataSet", version = "1.1", nsmap=nsmap), NS6, XMLNS, citation_publication)
    
    #publicationAndOwnership[5]
    copyright_ = af.subelement('copyright', publicationAndOwnership, XMLNS)
    
    if administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['isCopyrightProtected'] == 'true':
        copyright_.text = "true"
    else:
        copyright_.text = "false"
    
    #publicationAndOwnership[6]
    if administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib.get('companyId') is not None:
        referenceToEntitiesWithExclusiveAccess = af.subelement('referenceToEntitiesWithExclusiveAccess', publicationAndOwnership, XMLNS)
        af.referencia(referenceToEntitiesWithExclusiveAccess, 'contact data set', administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['companyId'], XMLNS, administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib.get('companyCode'))
    
        contactDataSet = etree.Element(NS4 + 'contactDataSet', version = "1.1", nsmap=nsmap)
        fc.contacts(administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['companyId'], contactDataSet, NS4, XMLNS, administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib.get('companyCode'), '')
    
    #publicationAndOwnership[7] e [8]
    licenseType = af.subelement('licenseType', publicationAndOwnership, XMLNS)
    accessRestrictions = af.subelement('accessRestrictions', publicationAndOwnership, XMLNS)
    list_of_restrictions = ['Free of charge for all users and uses','License fee','Other','Other']
    licenseType.text = list_of_restrictions[int(administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['accessRestrictedTo'])]
    accessRestrictions.text = "License type for this dataset: " + list_of_restrictions[int(administrativeInformationECO.find('{http://www.EcoInvent.org/EcoSpold02}dataGeneratorAndPublication').attrib['accessRestrictedTo'])]
    
    #exchanges[0] - Exchange (mathematical relations declared here)
    mathematicalRelations = af.subelement('mathematicalRelations', processInformation, NS2)
    count = 0
    alloc_frac = []
    prod_volume = 0
    allocation = []
    variable_list = []
    
    for ex in range(len(flowDataECO)):
        
        if flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}intermediateExchange" or flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}elementaryExchange":
            exchange = af.subelement("exchange", exchanges, NS2)
            
            if flowDataECO[ex][-1].tag == "{http://www.EcoInvent.org/EcoSpold02}outputGroup" and flowDataECO[ex][-1].text == "0":
                exchange.set('dataSetInternalID', '0')
            else:
                count = count + 1
                exchange.set('dataSetInternalID', str(count))
            
            
            
            #elemento raiz do arquivo de fluxo
            flowDataSet = etree.Element(NS3 + 'flowDataSet', version = "1.1", nsmap = nsmap_2)
            
            #subelementos básicos do arquivo de fluxo
            flowInformation = af.subelement('flowInformation', flowDataSet, NS3) #sem elementos de geografia ou tecnologia
            modellingAndValidationF = af.subelement('modellingAndValidation', flowDataSet, NS3)
            administrativeInformationF = af.subelement('administrativeInformation', flowDataSet, NS3)
            flowProperties = af.subelement('flowProperties', flowDataSet, NS3)
            
            #flowInformation[0] - DataSetInformation
            dataSetInformationF = af.subelement('dataSetInformation', flowInformation, NS3)
            
            #dataSetInformation[0]
            UUIDF = af.subelement('UUID', dataSetInformationF, XMLNS)
            #dataSetInformation[1]
            nameF = af.subelement('name', dataSetInformationF, NS3)
            baseNameF = af.subelement('baseName', nameF, NS3)
            
            if flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}intermediateExchange":
                UUIDF.text = flowDataECO[ex].attrib.get('intermediateExchangeId')
                baseNameF.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text
                if flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}synonym') is not None:
                    synonymsF = af.subelement('synonyms', dataSetInformationF, NS3)
                    synonymsF.text = flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}synonym').text
                if flowDataECO[ex].attrib.get('casNumber') is not None:
                    CASNumber = af.subelement('CASNumber', dataSetInformationF, NS3)
                    CASNumber.text = flowDataECO[ex].attrib.get('casNumber')
                            
            elif flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}elementaryExchange":
                
                #Usa-se aqui a tabela de conversão da Greendelta
                with open('Id_elementary_exchanges.csv') as elem_csv_unit:
                    elem_r = csv.reader(elem_csv_unit, delimiter = ',')
                    for row in elem_r:
                        if row[0] == flowDataECO[ex].attrib.get('elementaryExchangeId'):
                            
                            UUIDF.text = row[1]
                            baseNameF.text = row[2]
                            
                            if row[3] != '':
                                CASNumber = af.subelement('CASNumber', dataSetInformationF, NS3)
                                CASNumber.text = row[3]
                                
                            if row[4] != '':
                                synonymsF = af.subelement('synonyms', dataSetInformationF, NS3)
                                synonymsF.text = row[4]
                                
                            break
                        
                    #Caso o fluxo elementar não esteja na tabela de conversão, os dados são criados    
                    if UUIDF.text is None:
                        UUIDF.text = flowDataECO[ex].attrib.get('elementaryExchangeId')
                        baseNameF.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text
                        if flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}synonym') is not None:
                            synonymsF = af.subelement('synonyms', dataSetInformationF, NS3)
                            synonymsF.text = flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}synonym').text
                        if flowDataECO[ex].attrib.get('casNumber') is not None:
                            CASNumber = af.subelement('CASNumber', dataSetInformationF, NS3)
                            CASNumber.text = flowDataECO[ex].attrib.get('casNumber')
                        
            #dataSetInformation[3] - (PROB: sem @catId pois ele não é obrigatório e não consegui encontrar uma referência dele)
            if flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}elementaryExchange":
                classificationInformationF = af.subelement('classificationInformation', dataSetInformationF, NS3)
                
                elementaryFlowCategorization = af.subelement('elementaryFlowCategorization', classificationInformationF, XMLNS) #sem nome ou URI para categorias
                
                with open('compartment.csv') as conv_csv_unit_one:
                    conv_r_1 = csv.reader(conv_csv_unit_one, delimiter = ';')
                    for row_ in conv_r_1:
                        if row_[0] == flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}compartment").attrib.get('subcompartmentId'):
                            compartment = row_[1]
                            subcompartment = row_[2]
                            break
                
                category_1 = af.subelement('category', elementaryFlowCategorization, XMLNS)
                category_1.set('level', '0')
                category_1.text = "Elementary flows"
                category_2 = af.subelement('category', elementaryFlowCategorization, XMLNS)
                category_2.set('level', '1')
                category_2.text = compartment
                category_3 = af.subelement('category', elementaryFlowCategorization, XMLNS)
                category_3.set('level', '2')
                category_3.text = subcompartment
            
            #dataSetInformation[4] - on UUID call
            
            
            #dataSetInformation[5]
            if flowDataECO[ex].attrib.get('formula') is not None:
                sumFormula = af.subelement('sumFormula', dataSetInformationF, NS3)
                sumFormula.text = flowDataECO[ex].attrib.get('formula')
            
            #dataSetInformation[6]
            generalComment_F = af.subelement('generalComment', dataSetInformationF, XMLNS)
            if flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}intermediateExchange":
                generalComment_F.text = "EcoSpold 2 exchange, ID = " + flowDataECO[ex].attrib.get('intermediateExchangeId')
            if flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}elementaryExchange":
                generalComment_F.text = "EcoSpold 2 exchange, ID = " + flowDataECO[ex].attrib.get('elementaryExchangeId')
            
            if flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}tag'):
                generalComment_F.text = generalComment_F.text + ";\nTags: " + flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}tag').text
            
            #flowInformation[1] - QuantitativeReference
            quantitativeReferenceF = af.subelement('quantitativeReference', flowInformation, NS3)
            
            #quantitativeReference[0]
            referenceToReferenceFlowProperty = af.subelement('referenceToReferenceFlowProperty', quantitativeReferenceF, NS3)
            referenceToReferenceFlowProperty.text = "0"
            
            #modellingAndValidation[0] - LCIMethod
            
            #Campos não utilizados:
                #complianceDeclarations: mesmo motivo do processDataSet, não há dados no arquivo Ecospold2
                
            LCIMethodF = af.subelement('LCIMethod', modellingAndValidationF, NS3)
            
            #LCIMethod[0]
            typeOfDataSetF = af.subelement('typeOfDataSet', LCIMethodF, NS3)
            
            if flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}intermediateExchange":
                typeOfDataSetF.text = "Product flow"
            elif flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}elementaryExchange":
                typeOfDataSetF.text = "Elementary flow"
            
            #administrativeInformation[0] - DataEntryBy
            
            #Campos não utilizados:
                #referenceToPersonOrEntityEnteringTheData: mesmo motivo do processDataSet, não há dados no arquivo Ecospold2
                
            dataEntryByF = af.subelement('dataEntryBy', administrativeInformationF, NS3)
            
            #dataEntryBy[0]
            timeStampF = af.subelement('timeStamp', dataEntryByF, XMLNS)
            t_stamp_1 = time.localtime()
            t_stamp_string_1 = time.strftime("%Y-%m-%dT%H:%M:%S", t_stamp)
            timeStampF.text = t_stamp_string_1
            
            #dataEntryBy[1]
            referenceToDataSetFormatF = af.subelement('referenceToDataSetFormat', dataEntryByF, XMLNS)
            af.referencia(referenceToDataSetFormatF, 'source data set', 'a97a0155-0234-4b87-b4ce-a45da52f2a40', XMLNS, 'ILCD Format', '01.01.000')
            
            #administrativeInformation[1] - PublicationAndOwnership
            
            #Campos não utilizados:
                #referenceToPrecidingDataSetVersion: mesmo motivo do processDataSet, não há dados no arquivo Ecospold2
                #referenceToOwnershipOfDataset: Não há informação sobre no arquivo Ecospold2
                
            publicationAndOwnershipF = af.subelement('publicationAndOwnership', administrativeInformationF, NS3)
            
            #publicationAndOwnership[0]
            dataSetVersionF = af.subelement('dataSetVersion', publicationAndOwnershipF, XMLNS)
            dataSetVersionF.text = "00.00.000"
            
            #publicationAndOwnership[1]
            permanentDataSetURI = af.subelement('permanentDataSetURI', publicationAndOwnershipF, XMLNS)
            if flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}intermediateExchange":
                permanentDataSetURI.text = "http://openlca.org/ilcd/resource/flows/" + flowDataECO[ex].attrib.get('intermediateExchangeId')
            if flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}elementaryExchange":
                permanentDataSetURI.text = "http://openlca.org/ilcd/resource/flows/" + flowDataECO[ex].attrib.get('elementaryExchangeId')


            #flowProperties[0] - FlowProperty
            ref_id_unit, ref_id_unit_id = [''], ['']
            m_v_2 = None
            
            if flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}intermediateExchange":
                flowProperty = af.subelement('flowProperty', flowProperties, NS3)
                ref_id_unit[0], ref_id_unit_id[0], m_v = f_property(flowProperty, flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}unitName").text, '0', "1.0")
            
            elif flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}elementaryExchange":
                with open("factor_c.csv") as factor_csv:
                    factor = csv.reader(factor_csv, delimiter = ',')
                    for row in factor:
                        c = 0
                        if row[0] == flowDataECO[ex].attrib.get('elementaryExchangeId'):
                            c = 1
                            flowProperty = af.subelement('flowProperty', flowProperties, NS3)
                            ref_id_unit[0], ref_id_unit_id[0], m_v_2 = f_property(flowProperty, row[2], '0', row[1])
                            flowProperty_2 = af.subelement('flowProperty', flowProperties, NS3)
                            ref_2, ref_2_id, m_v = f_property(flowProperty_2, flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}unitName").text, '1', "1.0")
                            ref_id_unit.append(ref_2)
                            ref_id_unit_id.append(ref_2_id)
                            break
                        
                    if c == 0:
                        flowProperty = af.subelement('flowProperty', flowProperties, NS3)
                        ref_id_unit[0], ref_id_unit_id[0], m_v = f_property(flowProperty, flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}unitName").text, '0', "1.0")
                            
            
            
                        
            #apesar de ter campos de incerteza ou de comentários sobre o fluxo, estes não serão usados na conversão pois não tem dados equivalentes no arquivo Ecospold2
            
            
            
            #Campos sem utilização no exchange:
                #location: apesar de poder fazer uma localização a partir dos nomes e do elemento geografia, não é um trabalho necessário
                #functionType: é um dado específico do ILCD sobre a alocação do fluxo que é difícil de se obter com o Ecospold2
                #dataSourceType: não tem um campo com o dado no Ecospold2
                #dataDerivationTypeStatus: não tem um campo com o dado no Ecospold2
                
            
            #exchange[0]
            referenceToFlowDataSet = af.subelement("referenceToFlowDataSet", exchange, NS2)
            af.referencia(referenceToFlowDataSet, 'flow data set', UUIDF.text, XMLNS, flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text)
            
            #exchange[1]
            if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}inputGroup") is not None:
                exchangeDirection = af.subelement('exchangeDirection', exchange, NS2)
                exchangeDirection.text = "Input"
            elif flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}outputGroup") is not None:
                exchangeDirection = af.subelement('exchangeDirection', exchange, NS2)
                exchangeDirection.text = "Output" 
            
            #criação das variáveis para a mathematical relations
            
            #1. Das propriedades
            var = 0
            for prop in flowDataECO[ex].iterfind('{http://www.EcoInvent.org/EcoSpold02}property'):
                var = var + 1
                
                if prop.attrib.get('variableName') is not None:
                    variableParameter_prop = af.subelement('variableParameter', mathematicalRelations, NS2)
                    if prop.attrib.get('variableName') in variable_list:
                        variableParameter_prop.set('name', prop.attrib.get('variableName') + "_2")
                    else:
                        variableParameter_prop.set('name', prop.attrib.get('variableName'))
                        variable_list.append(prop.attrib.get('variableName'))
                    
                    meanValue = af.subelement('meanValue', variableParameter_prop, NS2)
                    meanValue.text = prop.attrib.get('amount')
                    
                    if prop.find('{http://www.EcoInvent.org/EcoSpold02}comment') is not None:
                        comment = af.subelement('comment', variableParameter_prop, NS2)
                        comment.text = prop.find('{http://www.EcoInvent.org/EcoSpold02}comment').text
            
            #2. Dos fluxos
            if flowDataECO[ex].attrib.get('variableName') is not None:
                
                variableParameter_f = af.subelement('variableParameter', mathematicalRelations, NS2)
                
                if flowDataECO[ex].attrib['variableName'] in variable_list:
                    variableParameter_f.set('name', flowDataECO[ex].attrib['variableName'] + "_2")
                else:
                    variableParameter_f.set('name', flowDataECO[ex].attrib['variableName'])
                    variable_list.append(flowDataECO[ex].attrib['variableName'])
                
                meanValue = af.subelement('meanValue', variableParameter_f, NS2)
                meanValue.text = flowDataECO[ex].attrib['amount']
                
                #comment = af.subelement('comment', variableParameter_f, NS2)
                
                if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty") is not None:
                    incerteza(flowDataECO[ex], meanValue, variableParameter_f, NS2, None)
                
                referenceToVariable = af.subelement('referenceToVariable', exchange, NS2)
                referenceToVariable.text = flowDataECO[ex].attrib['variableName']
                
            #3. Das relações matemáticas dos volumes de produção    
            if flowDataECO[ex].attrib.get('productionVolumeMathematicalRelation') is not None:
                variableParameter_pvmr = af.subelement('variableParameter', mathematicalRelations, NS2)
                
                if 'math_production ' + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text in variable_list:
                    variableParameter_pvmr.set('name', 'math_production ' + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text + "_2")
                else:
                    variableParameter_pvmr.set('name', 'math_production ' + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text)
                    variable_list.append('math_production ' + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text)
                
                formula = af.subelement('formula', variableParameter_pvmr, NS2)
                formula.text = flowDataECO[ex].attrib['productionVolumeMathematicalRelation']
                
                meanValue = af.subelement('meanValue', variableParameter_pvmr, NS2)
                meanValue.text = flowDataECO[ex].attrib['productionVolumeAmount']
                    
                if flowDataECO[ex].attrib.get("{http://www.EcoInvent.org/EcoSpold02}productionVolumeUncertainty"):
                    incerteza(flowDataECO[ex], meanValue, variableParameter_pvmr, NS2, None)
            
            #4. Dos volumes de produção  
            if flowDataECO[ex].attrib.get('productionVolumeAmount') is not None:
                
                annualSupplyOrProductionVolume = af.subelement('annualSupplyOrProductionVolume', dataSourcesTreatmentAndRepresentativeness, NS2)
                annualSupplyOrProductionVolume.text = "Annual Production of " + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text + " is " + flowDataECO[ex].attrib['productionVolumeAmount']
                
                #checar as variáveis antes do loop para exchanges para mais informações
                if LCIMethodPrinciple.text == "Attributional":
                    
                    if prod_volume == 0:
                        allocations = af.subelement('allocations', exchange, NS2)
                        
                    prod_volume = prod_volume + 1
                    
                    allocation[prod_volume] = af.subelement('allocation', allocations, NS2)
                    
                    for prop in flowDataECO[ex].iterfind('{http://www.EcoInvent.org/EcoSpold02}property'):
                        if prop.attrib.get('propertyId') == activityDescription[0].attrib.get('masterAllocationPropertyId'):
                            alloc_frac.append(int(prop.attrib.get('amount')))
                            
                    allocation[prod_volume].set('internalReferenceToCoProduct', str(count))
                
                if flowDataECO[ex].attrib.get('productionVolumeVariableName') is not None:
                
                    variableParameter_pv = af.subelement('variableParameter', mathematicalRelations, NS2)
                    
                    if flowDataECO[ex].attrib.get('productionVolumeVariableName') in variable_list:
                        variableParameter_pv.set('name', flowDataECO[ex].attrib.get('productionVolumeVariableName') + "_2")
                    else:
                        variableParameter_pv.set('name', flowDataECO[ex].attrib.get('productionVolumeVariableName'))
                        variable_list.append(flowDataECO[ex].attrib.get('productionVolumeVariableName'))
                    
                    meanValue = af.subelement('meanValue', variableParameter_pv, NS2)
                    meanValue.text = flowDataECO[ex].attrib['productionVolumeAmount']
                    
                    comment = af.subelement('comment', variableParameter_pv, NS2)
                
                    if flowDataECO[ex].attrib.get("{http://www.EcoInvent.org/EcoSpold02}productionVolumeComment") is not None:
                        comment.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}productionVolumeComment").text
            
            
            
            pedigree = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty/{http://www.EcoInvent.org/EcoSpold02}pedigreeMatrix")
            
            #Os valores reais do fluxo
            meanAmount_real = af.subelement("meanAmount", exchange, NS2)
            resultingAmount_real = af.subelement("resultingAmount", exchange, NS2)
            
            if flowDataECO[ex].attrib.get('variableName') is not None:
                meanAmount_real.text = '1.0'
            else:
                meanAmount_real.text = flowDataECO[ex].attrib['amount']
            
            if m_v_2 is not None:
                resultingAmount_real.text = m_v_2
            else:
                resultingAmount_real.text = flowDataECO[ex].attrib['amount']
            #incerteza do fluxo
            incerteza(flowDataECO[ex], meanAmount_real, exchange, NS2, '')
            
            if flowDataECO[ex].attrib.get('isCalculatedAmount') == "true":
                meanAmount_real.text = "1.0"
                
                variableParameter = af.subelement('variableParameter', mathematicalRelations, NS2)
                
                if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text[:40] + " relation" in variable_list:
                    variableParameter.set('name', flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text[:40] + " relation" + "_2")
                else:
                    variableParameter.set('name', flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text[:40] + " relation")
                    variable_list.append(flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}name").text[:40] + " relation")
                
                formula = af.subelement('formula', variableParameter, NS2)
                formula.text = flowDataECO[ex].attrib.get('mathematicalRelation')
                
                meanValue = af.subelement('meanValue', variableParameter, NS2)
                meanValue.text = flowDataECO[ex].attrib.get('amount')
            
            #bibliografia do fluxo
            if flowDataECO[ex].attrib.get("sourceId") is not None:
                if flowDataECO[ex].attrib.get("sourceId") not in lista:
                    lista.append(flowDataECO[ex].attrib.get("sourceId"))
                    sourceDataSet = etree.Element(NS6 + 'sourceDataSet', version = "1.1", nsmap=nsmap)
                    citation = flowDataECO[ex].attrib.get("sourceFirstAuthor") + " (" + flowDataECO[ex].attrib.get("sourceYear") + ")"
                    fc.sources(lista[-1], sourceDataSet, NS6, XMLNS, citation)
                
                referencesToDataSource = af.subelement('referencesToDataSource', exchange, NS2)
                referenceToDataSource = af.subelement('referenceToDataSource', referencesToDataSource, NS2)
                af.referencia(referenceToDataSource, 'source data set', flowDataECO[ex].attrib.get('sourceId'), NS2, flowDataECO[ex].attrib.get('pageNumbers'))
            
            generalComment_unc = af.subelement("generalComment", exchange, NS2)
            generalComment_unc_2 = af.subelement("generalComment", exchange, NS2)
            
            if pedigree is not None:
                generalComment_unc.text = "Pedigree:(" + pedigree.attrib["reliability"] + ',' + pedigree.attrib["completeness"] + ',' + pedigree.attrib["temporalCorrelation"] + ',' + pedigree.attrib["geographicalCorrelation"] + ',' + pedigree.attrib["furtherTechnologyCorrelation"] + '). Pedigree variance: ' + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}uncertainty")[0].attrib['varianceWithPedigreeUncertainty']
                if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}comment") is not None:
                    generalComment_unc_2.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}comment").text
            
            #fazer pastas
            try:
                os.mkdir("./ILCD-algorithm/flows")
            except OSError:
                pass
            
            try:
                os.mkdir("./ILCD-algorithm/flowproperties")
            except OSError:
                pass
            
            for unit in ref_id_unit:
                shutil.copy("./ILCD - conversão/flow_properties/" + unit + '.xml', "./ILCD-algorithm/flowproperties")
            
            try:
                os.mkdir("./ILCD-algorithm/unitgroups")
            except OSError:
                pass
            
            for unit_id in ref_id_unit_id:
                shutil.copy("./ILCD - conversão/unit_groups/" + unit_id + '.xml', "./ILCD-algorithm/unitgroups")
            
            #salvar arquivo de fluxo (flowDataSet)
            file_flow = "./ILCD-algorithm/flows/" + UUIDF.text + ".xml"
            with open(file_flow, 'wb') as Flow:
                Flow.write(etree.tostring(flowDataSet, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))
        
        
        
        elif flowDataECO[ex].tag == "{http://www.EcoInvent.org/EcoSpold02}parameter":
            
            variableParameter = af.subelement('variableParameter', mathematicalRelations, NS2)
            variableParameter.set('name', flowDataECO[ex].attrib['variableName'])
            
            if flowDataECO[ex].attrib.get('isCalculatedAmount') == 'true':
                formula = af.subelement('formula', variableParameter, NS2)
                formula.text = flowDataECO[ex].attrib.get('mathematicalRelation')
                
            meanValue = af.subelement('meanValue', variableParameter, NS2)
            meanValue.text = flowDataECO[ex].attrib.get('amount')
            
            if flowDataECO[ex].find('{http://www.EcoInvent.org/EcoSpold02}uncertainty') is not None:
                incerteza(flowDataECO[ex], meanValue, variableParameter, NS2, None)
            
            comment = af.subelement('comment', variableParameter, NS2)
            comment.set('{http://www.w3.org/XML/1998/namespace}lang','en')
            
            if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}unitName") is not None:
                comment.text = "Unidade: " + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}unitName").text
            if flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}comment") is not None:
                if comment.text is not None:
                    comment.text = comment.text + '\n' + flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}comment").text
                else:
                    comment.text = flowDataECO[ex].find("{http://www.EcoInvent.org/EcoSpold02}comment").text
    
    
    #dataSourcesTreatmentAndRepresentativeness[4]
    samplingProcedure = af.subelement('samplingProcedure', dataSourcesTreatmentAndRepresentativeness, NS2)
    samplingProcedure.text = modellingAndValidationECO[0].find('{http://www.EcoInvent.org/EcoSpold02}samplingProcedure').text
    
    #dataSourcesTreatmentAndRepresentativeness[5]
    uncertaintyAdjustments = af.subelement('uncertaintyAdjustments', dataSourcesTreatmentAndRepresentativeness, NS2)
    uncertaintyAdjustments.text = "Uncertainties calculated using a basic uncertainty (or informed) and a Pedigree Matrix additional uncertainty (log-normal) as it is in the standard procedure on Ecospold2 datasets (ecoinvent association)"
    
    #cálculo da fração de alocação 
    for it in range(prod_volume):
        allocation[it].set('allocatedFraction', alloc_frac[it]/sum(alloc_frac))
    
    #criação da pasta de processos
    try:
        os.mkdir("./ILCD-algorithm/processes")
    except OSError:
        pass
    
    #salvar arquivo de processo (processDataSet)
    file_process = "./ILCD-algorithm/processes/" + activityDescription[0].attrib["activityNameId"] + '.xml'
    with open(file_process, 'wb') as f:
        f.write(etree.tostring(processDataSet, pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes"))
    
    #criar .zip do ILCD
    zipdir("./ILCD-algorithm", ILCD_zip)
    
    #fechar arquivo .zip criado
    ILCD_zip.close()
    

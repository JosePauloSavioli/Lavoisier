#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated, Literal, get_args, get_origin
from pydantic import BaseModel, TypeAdapter

from .calculation_engines import DIMENSION_FIELDS, QuantityFactory, _standard as canonical_distribution
from .models.lca import (
    Actor,
    AnyCategoryRegistry,
    BIBODocumentClass,
    BIBOProperty,
    CategorySystemDataSet,
    CommentWithRole,
    CurrencyUnit,
    DCTermsProperty,
    Exchange,
    ExtensionCategoricalProperty,
    ExtensionCategorySystemFileReference,
    ExtensionCompositeProperty,
    ExtensionPropertyRegistry,
    ExtensionQuantitativeProperty,
    FileInformation,
    FileVersioning,
    Flowable,
    IncludedProcess,
    Model,
    Modelling,
    NonReviewActivity,
    OtherActorIdentification,
    OtherSourceIdentification,
    ParameterizationDataSet,
    ProcessDataSet,
    ProductionSystemDataSet,
    ProjectDataSet,
    QuantityFormula,
    QuantityInputFromEntry,
    RegistryDataSet,
    RegistryReference,
    ResultingQuantity,
    ReviewActivity,
    SimpleQuantityInput,
    SingleCategory,
    SingleQuantity,
    Source,
    SourceAuthor,
    SourceSemanticExtension,
    StandardPropertyRegistry,
    StandardPropertyValue,
    Timestamps,
    UCUMUnit,
)

from .data import pedigree
from .units import pint_to_ilcd_def
from .utils import uuid_from_string, uuid_from_uuid
from .ECS2_canonical_data import (
    CANONICAL_KEY,
    ENERGY,
    INHERITANCE,
    OUTPUT_GROUP,
    PROCESS_TYPE,
    SPECIAL_ACTIVITY,
    TECHNOLOGY,
)


STANDARD_REGISTRY = TypeAdapter(StandardPropertyRegistry)
STANDARD_VALUE = TypeAdapter(StandardPropertyValue)
CATEGORY_SYSTEM_DATASET = TypeAdapter(CategorySystemDataSet)


def _union_models(alias):
    value = alias.__value__
    if get_origin(value) is Annotated:
        value = get_args(value)[0]
    return get_args(value)


def _literal_model(model):
    data = {}
    for name, field in model.model_fields.items():
        if not field.is_required():
            continue
        annotation = field.annotation
        if get_origin(annotation) is Literal:
            data[name] = get_args(annotation)[0]
        elif get_origin(annotation) is tuple:
            data[name] = tuple(_literal_model(value) for value in get_args(annotation))
        else:
            raise TypeError(f'Cannot construct canonical registry field {model.__name__}.{name}')
    return model(**data)


STANDARD_PROPERTY_MODELS = {
    get_args(model.model_fields['id'].annotation)[0]: model
    for model in _union_models(StandardPropertyRegistry)
    if hasattr(model, 'model_fields')
    and 'id' in model.model_fields
    and get_origin(model.model_fields['id'].annotation) is Literal
}
STANDARD_PROPERTY_CATEGORY_SYSTEMS = {
    get_args(model.model_fields['property'].annotation)[0]:
    get_args(model.model_fields['categorySystem'].annotation)[0]
    for model in _union_models(StandardPropertyValue)
    if hasattr(model, 'model_fields')
    and 'property' in model.model_fields
    and get_origin(model.model_fields['property'].annotation) is Literal
    and 'categorySystem' in model.model_fields
    and get_origin(model.model_fields['categorySystem'].annotation) is Literal
}
STANDARD_CATEGORY_REGISTRY_MODELS = {
    get_args(model.model_fields['id'].annotation)[0]: model
    for model in _union_models(AnyCategoryRegistry)
    if hasattr(model, 'model_fields')
    and get_origin(model.model_fields['id'].annotation) is Literal
}


UCUM_REGISTRY = '08eb4445-1582-4b75-9995-6847ebb2b94b'
ISO4217_REGISTRY = 'c81a7de5-7176-43b8-b4e7-99c5c29cba2a'
BCP47_REGISTRY = 'b4500324-3bff-433e-bbd9-4d0d2a6ea8ed'

STANDARD_CATEGORY_REGISTRY_NAMES = {
    'ActivityIndex': 'c17624df-9e4d-4a3d-aebd-476c936f9c76',
    'ActivityNames': 'c17624df-9e4d-4a3d-aebd-476c936f9c76',
    'IntermediateExchanges': 'b900739f-d99c-4700-9c04-b09c5e3b4633',
    'ElementaryExchanges': '56d9507a-28c5-452d-9d0d-8f62482781ce',
    'Compartments': '43b6c40c-f055-4a86-9f98-5c5a58f95d4c',
    'Geographies': '8e23a4c6-284f-4f1b-b67b-88f1d56c5d31',
    'MacroEconomicScenarios': '64905f6a-5218-4287-9ec9-7a81150c5ab3',
    'SystemModels': 'b565dbf7-39c5-4f4f-98e7-ce797ddea6c9',
}


STANDARD_PROPERTIES = {
    '6ee6a892-7c74-432f-a65d-261691d9f562': ('validity', 'composite'),
    '406bf044-7c7d-4a66-af04-4e19b1296cf3': ('valid from', 'categorical'),
    '68e86569-fe18-4283-9a6a-4b9e4246021f': ('valid until', 'categorical'),
    '5ca53a8e-426c-484d-aa48-d3e91730bd9b': ('Copernicus CORINE land-cover classification', 'categorical'),
    '24964ee1-b167-4921-90d9-1b7aa18394ae': ('additional variance from pedigree matrix', 'quantitative'),
    '2aa79563-670b-448a-9edf-28f4954dfc74': ('density', 'quantitative'),
    '3a0af1d6-04c3-41c6-a3da-92c4f61e0eaa': ('dry mass', 'quantitative'),
    '42b3c201-539f-4891-97cc-66156ac53083': ('flow input-output type', 'categorical'),
    '4e598c59-fec6-412d-9227-2c7929ce1985': ('temporal scope', 'quantitative'),
    '4fdbc2e4-439f-4f9f-9efe-3494f8693658': ('concentration', 'quantitative'),
    '5119af08-62a1-4cb3-aa30-527cd72b5d90': ('elementary flow context', 'composite'),
    '5027f4e3-6af1-47c9-b151-12088a5200b0': ('natural resource compartment type', 'categorical'),
    '542f6612-0aa9-4d52-82c0-7bb0f6c21d19': ('market coverage', 'quantitative'),
    '35478f20-e60e-4aad-82a9-1fcf0f4aea98': ('major elementary flow context', 'categorical'),
    '55e46169-4f58-4204-a574-20703fdc02c4': ('CAS number', 'categorical'),
    '5ac08789-7f70-439a-b60e-18c0d612d4ac': ('energy content', 'quantitative'),
    '5cc54527-0cb9-4180-82cc-d13240e94e50': ('flow LCA type', 'categorical'),
    '63435e58-cd43-4c7b-a916-b49bdf2aef49': ('pedigree matrix', 'categorical'),
    '6393c14b-db78-445d-a47b-c0cb866a1b25': ('carbon content, non-fossil', 'quantitative'),
    '67bba357-b663-452c-874e-4f0c063a3647': ('soil compartment type', 'categorical'),
    '67f102e2-9cb6-4d20-aa16-bf74d8a03326': ('wet mass', 'quantitative'),
    '69bbe11a-4501-41ba-b3bf-2271e2ad155f': ('content', 'quantitative'),
    '735f3642-52b0-4f1c-90b3-78b0f7bafbeb': ('elementary flow direction', 'categorical'),
    '85194c11-6de9-4272-a7ff-c64aa0bea6ea': ('inheritance depth', 'categorical'),
    '85b28e60-bd7b-4d15-92b6-c6e59a2ae9eb': ('natural resource renewability', 'categorical'),
    '8868d6d3-6776-443b-90eb-c9ad9119348b': ('water compartment type', 'categorical'),
    '9398d975-d406-4276-9755-8c01804a9d61': ('settlement type', 'categorical'),
    '9767911c-ab5d-4eff-b150-215ca2a2ecb9': ('allocation model', 'categorical'),
    '99a6248f-dbb0-49dc-a4ad-23abab6ba25f': ('geographical scope', 'composite'),
    'a158ab98-408a-430e-9cba-4bce9b85b9e1': ('ISIC Rev. 4 classification', 'categorical'),
    'a4146cc4-35d8-4a5e-8c75-9d3b717b4a24': ('macroeconomic scenario', 'categorical'),
    'a9358458-9724-4f03-b622-106eda248916': ('water content', 'quantitative'),
    'd1a05915-1dd0-44b0-bc1b-f389e2ac3e52': ('capacity', 'quantitative'),
    'b3b96e47-db1f-496c-b73d-55b91716a5e7': ('production volume', 'quantitative'),
    'b629e5bf-48a8-4410-9103-f5cda1d9f729': ('political boundary', 'categorical'),
    'c3988d68-211f-49f4-85c8-cbc47b30f83b': ('CPC classification', 'categorical'),
    'c74c3729-e577-4081-b572-a283d2561a75': ('carbon content, fossil', 'quantitative'),
    'd695f836-5059-4e63-b6f0-bd093bc0e7f8': ('by-product classification', 'categorical'),
    'da8735d7-e473-4c5b-8532-25bc40aba761': ('special activity type', 'categorical'),
    'eb06d312-7738-42b2-a6c9-ac1fe9a018f4': ('is reference', 'categorical'),
    'f765f62d-81e0-4072-8c5f-e5ee771cb63d': ('fuel use', 'quantitative'),
    'f84fa310-200d-4359-bc12-7b99c4659ec6': ('atmospheric release height', 'categorical'),
    '6cd90a91-83d9-4c97-b4ec-aac59c8553ea': ('process LCA type', 'categorical'),
    '6d9e1462-80e3-4f10-b3f4-71febd6f1168': ('water in wet mass', 'quantitative'),
    '6cb57f90-10b6-406c-8d19-ac777ec074fa': ('variance', 'quantitative'),
    '51d9968a-d5d3-41e7-9fcd-f127f54ab761': ('ecoinvent elementary flow context', 'categorical'),
    '107b99d0-ba7e-4825-b1c7-e4a25f2bfd08': ('ecoinvent geographical scope', 'categorical'),
    '51d34877-ad44-47b9-b157-12b8b05f8c3b': ('is ecoinvent RoW (rest-of-world)', 'categorical'),
    'ffb442e6-9601-417e-b8f5-08061ed41441': ('technology level', 'categorical'),
    'ed3b8a28-02a1-4a78-95d5-b6b1c3910d23': ('chemical formula', 'categorical'),
    '2c74cc35-dcef-4f9e-bda0-89d275526454': ('price', 'quantitative'),
    '1eabd6d5-adc3-4e72-8430-a9679630abf8': ('molar mass', 'quantitative'),
    '7e79e7af-71de-41a3-9dad-862e37cbe9ca': ('is data valid for entire period', 'categorical'),
    'b97e1868-4c04-4d7e-bd0c-45c79ddc8299': ('energy value basis', 'categorical'),
    'c1df2e5f-15a7-433f-a7cb-9e41add21c57': ('ecoinvent activity-name identity', 'categorical'),
    '0f21f048-7d0d-43df-a54a-716397a7fba6': ('ecoinvent intermediate-flow identity', 'categorical'),
    '86ff6198-5381-46ec-b250-c3fb405b3303': ('ecoinvent elementary-flow identity', 'categorical'),
    'f20ad8f9-ed0e-4f66-8329-033ea94a1ce9': ('ecoinvent parameter identity', 'categorical'),
    '744c9fd5-db05-4f96-ae49-0371dfdeda1f': ('ecoinvent property identity', 'categorical')
}


STANDARD_PROPERTY_CONTEXTS = {
    '6ee6a892-7c74-432f-a65d-261691d9f562': ['process'],
    '406bf044-7c7d-4a66-af04-4e19b1296cf3': ['process'],
    '68e86569-fe18-4283-9a6a-4b9e4246021f': ['process'],
    '5ca53a8e-426c-484d-aa48-d3e91730bd9b': ['flow'],
    '24964ee1-b167-4921-90d9-1b7aa18394ae': ['exchange', 'parameter'],
    '2aa79563-670b-448a-9edf-28f4954dfc74': ['flow'],
    '3a0af1d6-04c3-41c6-a3da-92c4f61e0eaa': ['flow'],
    '42b3c201-539f-4891-97cc-66156ac53083': ['exchange'],
    '4e598c59-fec6-412d-9227-2c7929ce1985': ['exchange', 'process'],
    '4fdbc2e4-439f-4f9f-9efe-3494f8693658': ['flow'],
    '5027f4e3-6af1-47c9-b151-12088a5200b0': ['exchange'],
    '5119af08-62a1-4cb3-aa30-527cd72b5d90': ['exchange'],
    '542f6612-0aa9-4d52-82c0-7bb0f6c21d19': ['process'],
    '35478f20-e60e-4aad-82a9-1fcf0f4aea98': ['exchange'],
    '55e46169-4f58-4204-a574-20703fdc02c4': ['flow'],
    '5ac08789-7f70-439a-b60e-18c0d612d4ac': ['flow'],
    '5cc54527-0cb9-4180-82cc-d13240e94e50': ['exchange'],
    '63435e58-cd43-4c7b-a916-b49bdf2aef49': ['exchange', 'parameter'],
    '6393c14b-db78-445d-a47b-c0cb866a1b25': ['flow'],
    '67bba357-b663-452c-874e-4f0c063a3647': ['exchange'],
    '67f102e2-9cb6-4d20-aa16-bf74d8a03326': ['flow'],
    '69bbe11a-4501-41ba-b3bf-2271e2ad155f': ['flow'],
    '735f3642-52b0-4f1c-90b3-78b0f7bafbeb': ['exchange'],
    '85194c11-6de9-4272-a7ff-c64aa0bea6ea': ['process'],
    '85b28e60-bd7b-4d15-92b6-c6e59a2ae9eb': ['exchange'],
    '8868d6d3-6776-443b-90eb-c9ad9119348b': ['exchange'],
    '9398d975-d406-4276-9755-8c01804a9d61': ['exchange'],
    '9767911c-ab5d-4eff-b150-215ca2a2ecb9': ['productionSystem'],
    '99a6248f-dbb0-49dc-a4ad-23abab6ba25f': ['exchange', 'process'],
    'a158ab98-408a-430e-9cba-4bce9b85b9e1': ['process'],
    'a4146cc4-35d8-4a5e-8c75-9d3b717b4a24': ['productionSystem', 'process'],
    'a9358458-9724-4f03-b622-106eda248916': ['flow'],
    'b3b96e47-db1f-496c-b73d-55b91716a5e7': ['exchange'],
    'b629e5bf-48a8-4410-9103-f5cda1d9f729': ['exchange', 'process'],
    'c3988d68-211f-49f4-85c8-cbc47b30f83b': ['flow'],
    'c74c3729-e577-4081-b572-a283d2561a75': ['flow'],
    'd1a05915-1dd0-44b0-bc1b-f389e2ac3e52': ['flow'],
    'd695f836-5059-4e63-b6f0-bd093bc0e7f8': ['flow'],
    'da8735d7-e473-4c5b-8532-25bc40aba761': ['process'],
    'eb06d312-7738-42b2-a6c9-ac1fe9a018f4': ['exchange'],
    'f765f62d-81e0-4072-8c5f-e5ee771cb63d': ['flow'],
    'f84fa310-200d-4359-bc12-7b99c4659ec6': ['exchange'],
    '6cb57f90-10b6-406c-8d19-ac777ec074fa': ['exchange', 'parameter'],
    '6cd90a91-83d9-4c97-b4ec-aac59c8553ea': ['process'],
    '6d9e1462-80e3-4f10-b3f4-71febd6f1168': ['flow'],
    '51d34877-ad44-47b9-b157-12b8b05f8c3b': ['process'],
    '51d9968a-d5d3-41e7-9fcd-f127f54ab761': ['exchange'],
    '107b99d0-ba7e-4825-b1c7-e4a25f2bfd08': ['exchange', 'process'],
    'ffb442e6-9601-417e-b8f5-08061ed41441': ['process'],
    'ed3b8a28-02a1-4a78-95d5-b6b1c3910d23': ['flow'],
    '2c74cc35-dcef-4f9e-bda0-89d275526454': ['flow'],
    '1eabd6d5-adc3-4e72-8430-a9679630abf8': ['flow'],
    '7e79e7af-71de-41a3-9dad-862e37cbe9ca': ['process'],
    'b97e1868-4c04-4d7e-bd0c-45c79ddc8299': ['process'],
    'c1df2e5f-15a7-433f-a7cb-9e41add21c57': ['process'],
    '0f21f048-7d0d-43df-a54a-716397a7fba6': ['flow'],
    '86ff6198-5381-46ec-b250-c3fb405b3303': ['flow'],
    'f20ad8f9-ed0e-4f66-8329-033ea94a1ce9': ['parameter'],
    '744c9fd5-db05-4f96-ae49-0371dfdeda1f': ['flow'],
}

ECS2_STANDARD_PROPERTIES = {
    '3a0af1d6-04c3-41c6-a3da-92c4f61e0eaa': '3a0af1d6-04c3-41c6-a3da-92c4f61e0eaa',
    '4d205f54-5f33-455c-a2bb-4650f1755e74': 'd1a05915-1dd0-44b0-bc1b-f389e2ac3e52',
    '6393c14b-db78-445d-a47b-c0cb866a1b25': '6393c14b-db78-445d-a47b-c0cb866a1b25',
    '67f102e2-9cb6-4d20-aa16-bf74d8a03326': '67f102e2-9cb6-4d20-aa16-bf74d8a03326',
    '6bc8ac5e-cc4c-45fb-93dc-53c0e45091df': '5ac08789-7f70-439a-b60e-18c0d612d4ac',
    '6d9e1462-80e3-4f10-b3f4-71febd6f1168': '6d9e1462-80e3-4f10-b3f4-71febd6f1168',
    'a9358458-9724-4f03-b622-106eda248916': 'a9358458-9724-4f03-b622-106eda248916',
    'c74c3729-e577-4081-b572-a283d2561a75': 'c74c3729-e577-4081-b572-a283d2561a75',
    'e40445b1-8aba-4282-851d-9c2d28b1a5c1': '2aa79563-670b-448a-9edf-28f4954dfc74',
}


STANDARD_CATEGORY_SYSTEMS = {
    'CORINE': 'b5cc481c-d0b4-4a1f-9b9b-f408f2b4113a',
    'CPC': '79b46f42-87df-4229-9ece-3e8140ca18d8',
    'ISIC': 'daabd84a-ed83-4851-87de-d39c21668d2a',
    'macroEconomicScenario': '64905f6a-5218-4287-9ec9-7a81150c5ab3',
    'pedigree': '21252d11-0d48-484f-9ea0-0ea320b3b2aa',
    'byProduct': '870f8b92-c608-4799-a75e-a46de92da782',
}


UN_M49_REGISTRY = 'd11d8db1-8e7d-4041-baff-7ebd0d2fca68'
ECOINVENT_SOURCE_ID = 'bbf9cfb4-e253-4419-9d84-f206a3b64de7'
ECOINVENT_ACTOR = uuid_from_uuid(ECOINVENT_SOURCE_ID, CANONICAL_KEY, 'flow_conversion_1')
VARIANCE_PROPERTY = '6cb57f90-10b6-406c-8d19-ac777ec074fa'
ECOINVENT_CONTEXT_PROPERTY = '51d9968a-d5d3-41e7-9fcd-f127f54ab761'
ECOINVENT_GEOGRAPHY_PROPERTY = '107b99d0-ba7e-4825-b1c7-e4a25f2bfd08'
ECOINVENT_ROW_PROPERTY = '51d34877-ad44-47b9-b157-12b8b05f8c3b'

DEFAULT_RIGHTS_URIS = {
    'copyright': 'https://support.ecoinvent.org/eula',
    'access': 'https://support.ecoinvent.org/licensing',
}

ACCESS_RESTRICTIONS = {
    0: 'public',
    1: 'licensees',
    2: 'results only',
    3: 'restricted',
}

DATA_PUBLISHED_IN = {
    0: 'data as such not published elsewhere',
    1: 'data of some unit processes or subsystems are published',
    2: 'data published entirely in this source',
}

ECOINVENT_IDENTITY_PROPERTIES = {
    'ActivityNames': 'c1df2e5f-15a7-433f-a7cb-9e41add21c57',
    'IntermediateExchanges': '0f21f048-7d0d-43df-a54a-716397a7fba6',
    'ElementaryExchanges': '86ff6198-5381-46ec-b250-c3fb405b3303',
    'Parameters': 'f20ad8f9-ed0e-4f66-8329-033ea94a1ce9',
    'Properties': '744c9fd5-db05-4f96-ae49-0371dfdeda1f',
}


SOURCE_EXTENSIONS = {
    'volumeNo': BIBOProperty.http___purl_org_ontology_bibo_volume,
    'shortName': BIBOProperty.http___purl_org_ontology_bibo_shortTitle,
    'nameOfEditors': BIBOProperty.http___purl_org_ontology_bibo_editorList,
    'publisher': DCTermsProperty.http___purl_org_dc_terms_publisher,
    'comment': DCTermsProperty.http___purl_org_dc_terms_description,
}


class ECS2ToCanonical:


    def __init__(self, source, config):
        self.source = source
        self.config = config
        self.quantities = QuantityFactory(
            sample_count=config.get('sample_count', 1000),
            seed=config.get('seed'),
        )
        self.master = {}
        self.classification_values = {}
        self.subcompartments = {}
        self.categories = {}
        self.category_systems = {}
        self.properties = {}
        self.units = {}
        self.sources = {}
        self.actors = {}
        self.flows = {}
        self.parameters = []
        self.exchange_quantities = {}
        self.exchange_refs = {}
        self.formula_refs = {}
        self.formula_cache = {}
        self.unit_conversion_refs = {}
        self._index()


    def convert(self):
        activity = self.source.activityDescription.activity
        source_id = activity.get_value('id')
        name = self._text(activity.get_value('activityName')).split(',')[0].strip()

        self.process_id = self._id(source_id)
        self.parameterization_id = self._generated_id('parameterization', source_id)
        self.parameter_model_id = self._generated_id('parameterization-model', source_id)
        self.production_system_id = self._generated_id('production-system', source_id)
        self.project_id = self._generated_id('project', source_id)
        self.registry_id = self._generated_id('registry', source_id)
        self.generated_timestamp = datetime.now(timezone.utc)

        process_properties = self._process_properties(self.process_id)
        validity = self._validity_property(self.process_id)
        if validity is not None:
            process_properties.append(validity)
        exchanges = self._exchanges(process_properties)

        process = ProcessDataSet(
            id=self.process_id,
            datasetType='process',
            name=name,
            comments=self._process_comments() or None,
            properties=process_properties or None,
            registry=self._file_reference('registry', self.registry_id),
            exchanges=exchanges,
            aggregatedProcesses=self._aggregated_processes(name),
            fileInformation=self._file_information(self.process_id, source_id, 'process'),
        )

        parameterization = self._parameterization(name, source_id)
        production_system = self._production_system(source_id, exchanges, parameterization)
        project = self._project(name, source_id, production_system)
        registry = self._registry(source_id)

        return {
            'project': project,
            'productionSystems': {production_system.id: production_system},
            'processes': {process.id: process},
            'parameterizations': (
                {parameterization.id: parameterization}
                if parameterization else {}
            ),
            'registries': {registry.id: registry},
            'categorySystems': self._category_system_datasets(),
        }

    def _registry_values(self, name, dependencies):
        values = getattr(self, name)
        return [value for id_, value in values.items() if id_ in dependencies[name]]

    def _category_registry_values(self, dependencies, prefix=None):
        if prefix:
            self._standard_category_registry(prefix)
            dependencies['categories'].add(prefix)
        values = self._registry_values('categories', dependencies)
        if not prefix:
            return values
        return [self.categories[prefix]] + [
            value
            for id_, value in self.categories.items()
            if id_ in dependencies['categories'] and id_ != prefix
        ]

    def _dependencies(self, *values):
        dependencies = {
            'categories': set(),
            'properties': set(),
            'sources': set(),
            'units': set(),
        }

        def walk(value):
            if isinstance(value, BaseModel):
                walk(value.model_dump(exclude_none=True))
                return

            if isinstance(value, dict):
                property_id = value.get('property')
                if property_id in self.properties:
                    dependencies['properties'].add(property_id)

                for field in ('categorySystem', 'processRegistry', 'exchangeRegistry'):
                    category_id = value.get(field)
                    if category_id in self.categories:
                        dependencies['categories'].add(category_id)

                for field in ('unit', 'expectedUnit'):
                    unit_id = value.get(field)
                    if unit_id in self.units:
                        dependencies['units'].add(unit_id)
                        self._standard_category_registry(self.units[unit_id].codeSystem)
                        dependencies['categories'].add(self.units[unit_id].codeSystem)

                for source_entry in value.get('sourceEntries') or []:
                    source_id = source_entry.get('reference') if isinstance(source_entry, dict) else None
                    if source_id in self.sources:
                        dependencies['sources'].add(source_id)

                for item in value.values():
                    walk(item)
                return

            if isinstance(value, (list, tuple, set)):
                for item in value:
                    walk(item)

        for value in values:
            walk(value)
        return dependencies

    def _parameterization(self, name, source_id):
        if not self.parameters:
            return None

        return ParameterizationDataSet(
            id=self.parameterization_id,
            datasetType='parameterization',
            models=[Model(
                id=self.parameter_model_id,
                name=f'{name} calculations',
                parameters=self.parameters,
            )],
            registry=self._file_reference('registry', self.registry_id),
            fileInformation=self._file_information(self.parameterization_id, source_id, 'parameterization'),
        )

    def _production_system(self, source_id, exchanges, parameterization):
        properties = self._production_system_properties()
        linking = self._background_linking() or {}

        return ProductionSystemDataSet(
            id=self.production_system_id,
            datasetType='productionSystem',
            processInstances=[{
                'id': self._file_reference('process', self.process_id),
            }],
            parameterizations=(
                [self._file_reference('parameter', parameterization.id)]
                if parameterization else None
            ),
            linking=linking,
            properties=properties or None,
            registry=self._file_reference('registry', self.registry_id),
            fileInformation=self._file_information(
                self.production_system_id,
                source_id,
                'productionSystem',
            ),
        )


    def _production_system_properties(self):
        representativeness = self.source.modellingAndValidation.get_value('representativeness')
        if not representativeness:
            return []

        properties = []
        system_model = representativeness.get_value('systemModelId')
        if system_model:
            master = self.master['systemModel'].get(system_model)
            value = (
                self._text(master.get_value('name'))
                if master
                else self._text(representativeness.get_value('systemModelName'))
            ) or self._master_name('SystemModels', system_model) or system_model
            properties.append(self._standard(
                self.production_system_id,
                '9767911c-ab5d-4eff-b150-215ca2a2ecb9',
                self._category(
                    self._category_registry('SystemModels'),
                    value,
                    entry_id=system_model,
                ),
            ))
        context = representativeness.get_value('systemModelContextId')
        if context:
            properties.append(self._extension(
                self.production_system_id,
                'ECS2 system model context id',
                context,
                context=['productionSystem'],
            ))
        return properties

    def _background_linking(self):
        rows = []
        process_categories = self._category_registry('ActivityIndex')
        exchange_categories = self._category_registry('IntermediateExchanges')

        for exchange in self._many(self.source.flowData, 'intermediateExchange'):
            activity_link = exchange.get_value('activityLinkId')
            if not activity_link:
                continue

            input_group = exchange.get_value('inputGroup')
            output_group = exchange.get_value('outputGroup')
            if input_group is None and output_group is None:
                continue

            source_flow_id = exchange.get_value('intermediateExchangeId')
            flow_id = self._id(source_flow_id)
            activity = self.master['activityIndexEntry'].get(activity_link)
            geography = None
            model = None
            if activity:
                geography_id = activity.get_value('geographyId')
                geography_master = self.master['geography'].get(geography_id)
                geography = self._text(geography_master.get_value('shortname')) if geography_master else None
                model_id = activity.get_value('systemModelId')
                model_master = self.master['systemModel'].get(model_id)
                model = self._text(model_master.get_value('shortname')) if model_master else None

            external = {
                'processId': self._category(
                    process_categories,
                    self._master_name('ActivityIndex', activity_link) or activity_link,
                    entry_id=activity_link,
                ),
                'exchangeId': self._category(
                    exchange_categories,
                    self.flows[flow_id].name,
                    entry_id=source_flow_id,
                ),
                'processRegistry': process_categories,
                'exchangeRegistry': exchange_categories,
                'geography': geography,
                'model': model,
            }
            exchange_id = self._id(exchange.get_value('id'))
            exchange_key = 'inputExchangeId' if input_group is not None else 'outputExchangeId'
            rows.append({
                'id': {
                    'processId': self._file_reference('process', self.process_id),
                    exchange_key: self._entry_reference('exchange', exchange_id),
                },
                'values': [{'id': external, 'value': Decimal('1')}],
            })

        return {'backgroundPartialLinkingMatrices': [{'linking': rows}]} if rows else None


    def _project(self, name, source_id, production_system):
        file = self.source.administrativeInformation.fileAttributes
        language = file.get_value('defaultLanguage') or self.config.get('default_language', 'en')
        provenance = self._provenance()
        source_ids = self._publication_sources()
        rights = self._rights()

        self._standard_category_registry(BCP47_REGISTRY)

        return ProjectDataSet(
            id=self.project_id,
            datasetType='project',
            name=name,
            language={
                'referenceSystem': BCP47_REGISTRY,
                'value': language,
            },
            registry=self._file_reference('registry', self.registry_id),
            modelling=self._project_modelling(),
            provenance=provenance,
            rights=rights,
            productionSystems=[
                self._file_reference('productionSystem', production_system.id)
            ],
            sourceEntries=self._source_entries(source_ids),
            fileInformation=self._file_information(self.project_id, source_id, 'project'),
        )


    def _registry(self, source_id):
        self._standard_category_registry(BCP47_REGISTRY)
        self._standard_category_registry(UCUM_REGISTRY)

        categories = [
            self.categories[BCP47_REGISTRY],
            self.categories[UCUM_REGISTRY],
        ]
        categories.extend(
            value
            for id_, value in self.categories.items()
            if id_ not in {BCP47_REGISTRY, UCUM_REGISTRY}
        )

        return RegistryDataSet(
            id=self.registry_id,
            datasetType='registry',
            fileInformation=self._file_information(self.registry_id, source_id, 'registry'),
            categories=categories,
            flowables=list(self.flows.values()),
            units=list(self.units.values()),
            actors=list(self.actors.values()) or None,
            properties=list(self.properties.values()) or None,
            sources=list(self.sources.values()) or None,
        )


    def _project_modelling(self):
        representativeness = self.source.modellingAndValidation.get_value('representativeness')
        sampling = self._text(self._field(representativeness, 'samplingProcedure')) if representativeness else None
        extrapolations = self._text(self._field(representativeness, 'extrapolations')) if representativeness else None
        return Modelling(
            samplingComment=sampling or 'Not specified in ECS2 dataset',
            extrapolationsComment=extrapolations or 'Not specified in ECS2 dataset',
        )


    def _publication_sources(self):
        publication = self.source.administrativeInformation.dataGeneratorAndPublication
        source_ids = self._source_ids(
            publication,
            field='publishedSourceId',
            year_field='publishedSourceYear',
            author_field='publishedSourceFirstAuthor',
            pages_field='pageNumbers',
            title='Published source associated with the ecoinvent dataset',
        )
        published = publication.get_value('dataPublishedIn')
        if published is not None:
            published = DATA_PUBLISHED_IN.get(int(published), str(published))
            for source_id in source_ids:
                self._add_entity_property(
                    self.sources,
                    source_id,
                    self._extension(
                        source_id,
                        'ecoinvent data published in',
                        published,
                        context=['source'],
                    ),
                )
        return source_ids

    def _rights(self):
        if self.config.get('rights'):
            return self.config['rights']

        publication = self.source.administrativeInformation.dataGeneratorAndPublication
        uris = {**DEFAULT_RIGHTS_URIS, **self.config.get('rights_uris', {})}
        rights = {}

        copyright_ = publication.get_value('isCopyrightProtected')
        if copyright_ is not None:
            rights['copyright'] = {
                'referenceToCopyrightStatementURI': uris['copyright'],
                'isCopyrightProtected': copyright_ is True or str(copyright_).lower() in ('true', '1'),
            }

        access = publication.get_value('accessRestrictedTo')
        if access is not None:
            access = int(access)
            data = {
                'accessModel': ACCESS_RESTRICTIONS.get(access, str(access)),
                'referenceToPolicyURI': uris['access'],
            }
            if access == 3:
                restricted = [
                    self._actor(company_id, actor_type='organization', name=publication.get_value('companyCode'))
                    for company_id in self._many_value(publication, 'companyId')
                ]
                if restricted:
                    data['restrictedTo'] = restricted
            rights['access'] = data

        return rights

    def _add_entity_property(self, collection, id_, property_):
        data = collection[id_].model_dump(by_alias=True, exclude_none=True)
        properties = data.get('properties', [])
        if not any(value.get('id') == property_.id for value in properties):
            properties.append(property_.model_dump(by_alias=True, exclude_none=True))
        data['properties'] = properties
        collection[id_] = type(collection[id_]).model_validate(data)


    def _ecoinvent_actor(self):
        actor = self.actors.get(ECOINVENT_ACTOR)
        data = actor.model_dump(by_alias=True, exclude_none=True) if actor else {
            'id': ECOINVENT_ACTOR,
        }
        data['actorType'] = 'organization'
        data['name'] = 'ecoinvent'

        identifiers = [
            identifier for identifier in data.get('identifiers', [])
            if not (
                identifier.get('system') == 'ecoinvent actor id'
                and identifier.get('value') == ECOINVENT_SOURCE_ID
            )
        ]
        for identifier in (
            {'system': 'ecoinvent company id', 'value': ECOINVENT_SOURCE_ID},
            {'system': 'ecoinvent company code', 'value': 'ECOINV'},
        ):
            if identifier not in identifiers:
                identifiers.append(identifier)
        data['identifiers'] = identifiers
        self.actors[ECOINVENT_ACTOR] = Actor.model_validate(data)
        return ECOINVENT_ACTOR

    def _actor(self, source_id=None, actor_type='individual', name=None, email=None):
        if source_id == ECOINVENT_SOURCE_ID:
            return self._ecoinvent_actor()

        master = None
        if source_id:
            master = self.master['person'].get(source_id) or self.master['company'].get(source_id)

        canonical_id = self._id(source_id) if source_id else self._generated_id('actor', actor_type, name, email)
        person = source_id in self.master['person']
        company = source_id in self.master['company']

        if company:
            actor_type = 'organization'

        name = self._text(name) or (
            self._text(master.get_value('name')) if master else None
        ) or (
            self._text(master.get_value('code')) if company else None
        ) or source_id or 'Unknown ECS2 actor'

        emails = self._texts(email)
        if not emails and master:
            emails = self._texts(master.get_value('email'))

        identifiers = []
        if source_id:
            identifiers.append(OtherActorIdentification(
                system=(
                    'ecoinvent person id'
                    if person else
                    'ecoinvent company id'
                    if company else
                    'ecoinvent actor id'
                ),
                value=source_id,
            ))

        organization = self._text(master.get_value('companyName')) if person else None
        website = self._text(master.get_value('website')) if company else None
        code = self._text(master.get_value('code')) if company else None
        if code:
            identifiers.append(OtherActorIdentification(
                system='ecoinvent company code',
                value=code,
            ))

        if canonical_id in self.actors:
            actor = self.actors[canonical_id]
            data = actor.model_dump(by_alias=True, exclude_none=True)
            if actor.name == source_id or actor.name == 'Unknown ECS2 actor':
                data['name'] = name
            if actor_type == 'organization':
                data['actorType'] = 'organization'
            if organization and not actor.organizationName:
                data['organizationName'] = organization
            if emails and not actor.emails:
                data['emails'] = [
                    value if value.startswith('mailto:') else f'mailto:{value}'
                    for value in emails
                ]
            if website and not actor.websites and website.startswith(('http://', 'https://')):
                data['websites'] = [website]
            existing = {(value['system'], value['value']) for value in data.get('identifiers', [])}
            data['identifiers'] = data.get('identifiers', []) + [
                value.model_dump(by_alias=True, exclude_none=True)
                for value in identifiers
                if (value.system, value.value) not in existing
            ]
            self.actors[canonical_id] = Actor.model_validate(data)
            return canonical_id

        self.actors[canonical_id] = Actor(
            id=canonical_id,
            actorType=actor_type,
            name=name,
            organizationName=organization,
            identifiers=identifiers or None,
            emails=[
                value if value.startswith('mailto:') else f'mailto:{value}'
                for value in emails
            ] or None,
            websites=[website] if website and website.startswith(('http://', 'https://')) else None,
        )
        return canonical_id

    def _software_actor(self):
        generator = self.source.administrativeInformation.fileAttributes.get_value('fileGenerator')
        if not generator:
            return None
        match = re.fullmatch(r'(.+?)\s+(\d+(?:\.\d+)+)', str(generator).strip())
        name = match.group(1) if match else str(generator).strip()
        version = match.group(2) if match else None
        actor_id = self._generated_id('software', generator)
        if actor_id not in self.actors:
            self.actors[actor_id] = Actor(
                id=actor_id,
                actorType='software',
                name=name,
                version=version,
            )
        return actor_id

    def _activity_date(self, value=None):
        value = value or self.source.administrativeInformation.fileAttributes.get_value('creationTimestamp') or self.source.administrativeInformation.fileAttributes.get_value('fileTimestamp')
        if isinstance(value, datetime):
            return self._aware(value)
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                parsed = datetime.fromisoformat(f'{value}T00:00:00+00:00')
            return self._aware(parsed)
        return datetime.now(timezone.utc)


    def _metadata_comments(self, obj, prefix, fields):
        comments = []
        for field in fields:
            value = obj.get_value(field)
            if self._present(value):
                comments.append(CommentWithRole(
                    role=f'{prefix}.{field}',
                    text=str(value),
                ))
        return comments

    def _review_version(self, review):
        return '.'.join(str(review.get_value(field)) for field in (
            'reviewedMajorRelease',
            'reviewedMinorRelease',
            'reviewedMajorRevision',
            'reviewedMinorRevision',
        ))

    def _provenance(self):
        activities = []
        modelling = self.source.modellingAndValidation

        for index, review in enumerate(self._many(modelling, 'review')):
            if not self.config.get('convert_system_review', True) and review.get_value('reviewerEmail') == 'support@ecoinvent.org':
                continue
            actor_ids = []
            reviewers = self._many_value(review, 'reviewerId')
            for reviewer in reviewers:
                name = review.get_value('reviewerName')
                actor_ids.append(self._actor(
                    reviewer,
                    actor_type=(
                        'organization'
                        if reviewer not in self.master['person'] and 'system' in str(name).lower()
                        else 'individual'
                    ),
                    name=name,
                    email=review.get_value('reviewerEmail'),
                ))
            if not actor_ids:
                actor_ids.append(self._actor(
                    actor_type='organization' if 'system' in str(review.get_value('reviewerName')).lower() else 'individual',
                    name=review.get_value('reviewerName'),
                    email=review.get_value('reviewerEmail'),
                ))

            version = self._review_version(review)
            comments = self._comments(review.get_value('details'), 'details')
            comments.extend(self._comments(review.get_value('otherDetails'), 'otherDetails'))
            comments.extend(self._metadata_comments(review, 'review', ('reviewerContextId',)))
            automated = review.get_value('reviewerEmail') == 'support@ecoinvent.org'
            activities.append(ReviewActivity(
                id=self._generated_id(self.project_id, 'review', index),
                activityType={'typeSystem': 'standard', 'value': 'dataReview'},
                actors=actor_ids,
                date={'start': self._activity_date(review.get_value('reviewDate'))},
                reviewType={
                    'reviewSystem': 'other',
                    'value': 'ecoinvent automated validation' if automated else 'ecoinvent review',
                },
                reviewedVersion=version,
                comments=comments or None,
            ))

        admin = self.source.administrativeInformation
        entry = admin.dataEntryBy
        publication = admin.dataGeneratorAndPublication
        timestamp = self._activity_date()

        entry_actors = [
            self._actor(person_id, name=entry.get_value('personName'), email=entry.get_value('personEmail'))
            for person_id in self._many_value(entry, 'personId')
        ]
        if not entry_actors:
            entry_actors = [self._actor(name=entry.get_value('personName'), email=entry.get_value('personEmail'))]
        active = entry.get_value('isActiveAuthor')
        if active is not None:
            for actor_id in entry_actors:
                self._add_entity_property(
                    self.actors,
                    actor_id,
                    self._extension(
                        actor_id,
                        'ecoinvent is active author',
                        active,
                        context=['actor'],
                    ),
                )
        entry_comments = self._metadata_comments(entry, 'data entry', ('personContextId',))
        file = admin.fileAttributes
        for index, context in enumerate(self._many(file, 'requiredContext')):
            entry_comments.append(CommentWithRole(role=f'requiredContext.{index}', text=str(context.get_dict())))
        activities.append(NonReviewActivity(
            id=self._generated_id(self.project_id, 'data-entry'),
            activityType={'typeSystem': 'standard', 'value': 'dataEntry'},
            actors=entry_actors,
            date={'start': timestamp},
            comments=entry_comments or None,
        ))

        publication_actors = [
            self._actor(person_id, name=publication.get_value('personName'), email=publication.get_value('personEmail'))
            for person_id in self._many_value(publication, 'personId')
        ]
        company_actors = [self._actor(company_id, actor_type='organization') for company_id in self._many_value(publication, 'companyId')]
        software = self._software_actor()
        generation_actors = publication_actors + ([software] if software else [])
        if generation_actors:
            activities.append(NonReviewActivity(
                id=self._generated_id(self.project_id, 'data-generation'),
                activityType={'typeSystem': 'standard', 'value': 'dataGeneration'},
                actors=generation_actors,
                date={'start': timestamp},
            ))

        publication_comments = self._metadata_comments(
            publication,
            'publication',
            (
                'personContextId', 'publishedSourceIdOverwrittenByChild',
                'publishedSourceContextId', 'companyIdOverwrittenByChild', 'companyContextId',
            ),
        )
        publication_activity_actors = publication_actors or company_actors
        if publication_activity_actors:
            activities.append(NonReviewActivity(
                id=self._generated_id(self.project_id, 'data-publication'),
                activityType={'typeSystem': 'standard', 'value': 'dataPublication'},
                actors=publication_activity_actors,
                date={'start': timestamp},
                comments=publication_comments or None,
            ))

        return {'activities': activities}


    def _index(self):
        keys = (
            'activityName',
            'geography',
            'systemModel',
            'macroEconomicScenario',
            'classificationSystem',
            'compartment',
            'company',
            'person',
            'source',
            'units',
            'property',
            'elementaryExchange',
            'intermediateExchange',
            'parameter',
        )
        for key in keys:
            self.master[key] = {
                item.get_value('id'): item
                for item in self._many(self.source.userMaster, key)
                if item.get_value('id')
            }

        for key in ('intermediateExchange', 'elementaryExchange'):
            for exchange in self._many(self.source.flowData, key):
                source_id = exchange.get_value('id')
                if source_id:
                    self.exchange_refs[source_id] = exchange

        self.master['activityIndexEntry'] = {
            item.get_value('id'): item
            for item in self._many(self.source.userMaster, 'activityIndexEntry')
            if item.get_value('id')
        }

        for compartment in self.master['compartment'].values():
            for subcompartment in self._many(compartment, 'subcompartment'):
                self.subcompartments[subcompartment.get_value('id')] = subcompartment

        for system in self.master['classificationSystem'].values():
            for value in self._many(system, 'classificationValue'):
                self.classification_values[value.get_value('id')] = (system, value)

    def _id(self, source_id):
        return uuid_from_uuid(source_id, CANONICAL_KEY, 'flow_conversion_1')

    def _generated_id(self, *parts):
        return uuid_from_string('ECS2:' + ':'.join(str(part) for part in parts))

    def _field(self, obj, key, default=None):
        if obj is None:
            return default
        if hasattr(obj, 'get_value'):
            return obj.get_value(key, default)
        if isinstance(obj, dict):
            return obj.get(key, default)
        return default

    def _value(self, value):
        while hasattr(value, 'value'):
            value = value.value()
        return value

    def _many(self, obj, key):
        value = self._field(obj, key)
        if value is None:
            return []
        return value if isinstance(value, list) else [value]

    def _texts(self, value):
        if value is None:
            return []
        value = self._value(value)
        if hasattr(value, 'VALID'):
            value = self._field(value, 'text', [])
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, dict):
            text = value.get('#text')
            text = self._value(text)
            return [str(text)] if text is not None and str(text).strip() else []
        texts = []
        for item in value:
            texts.extend(self._texts(item))
        return texts

    def _text(self, value, default=None):
        texts = self._texts(value)
        return texts[0] if texts else default

    def _present(self, value):
        return value is not None and (not isinstance(value, str) or bool(value.strip()))


    def _comments(self, value, name=None):
        variables = []
        if value:
            for variable in self._field(value, 'variable') or []:
                variable_name = self._value(variable.get('@name'))
                variable_value = self._value(variable.get('#text'))
                if self._present(variable_name):
                    data = {'name': str(variable_name)}
                    if self._present(variable_value):
                        data['value'] = str(variable_value)
                    variables.append(data)

        return [
            CommentWithRole(
                text=text,
                role=name,
                variables=variables or None,
            )
            for text in self._texts(value)
        ]


    def _text_and_image_properties(self, owner, value, name, target, context=None):
        if not value:
            return
        for index, image in enumerate(self._texts(self._field(value, 'imageUrl'))):
            target.append(self._extension(
                owner,
                f'ECS2 {name} image URL',
                image,
                index,
                context=context,
            ))

    def _category_registry(self, name, id_=None):
        id_ = STANDARD_CATEGORY_REGISTRY_NAMES.get(name, id_ or self._generated_id('category', name))
        if id_ in STANDARD_CATEGORY_REGISTRY_MODELS:
            return self._standard_category_registry(id_)
        if id_ not in self.categories:
            self.categories[id_] = ExtensionCategorySystemFileReference(
                fileId=id_,
                referenceType='internalFile',
                targetType='categorySystem',
            )
            self.category_systems[id_] = {
                'id': id_,
                'name': f'ecoinvent {name}',
                'entries': {},
            }
        return id_

    def _standard_category_registry(self, id_):
        if id_ not in self.categories:
            self.categories[id_] = _literal_model(STANDARD_CATEGORY_REGISTRY_MODELS[id_])
        return id_

    def _category_system_datasets(self):
        datasets = {}
        for id_, data in self.category_systems.items():
            if not data['entries']:
                continue
            datasets[id_] = CATEGORY_SYSTEM_DATASET.validate_python({
                'id': id_,
                'name': data['name'],
                'datasetType': 'categorySystem',
                'categorySystemType': 'single',
                'entries': list(data['entries'].values()),
            })
        return datasets


    def _property_registry(self, id_, name, type_, context=None):
        if id_ in self.properties:
            if id_ not in STANDARD_PROPERTY_MODELS and context:
                data = self.properties[id_].model_dump(by_alias=True, exclude_none=True, mode='json')
                data['context'] = list(dict.fromkeys((data.get('context') or []) + context))
                self.properties[id_] = ExtensionPropertyRegistry.model_validate(data)
            return id_
        if id_ in STANDARD_PROPERTY_MODELS:
            name, type_ = STANDARD_PROPERTIES[id_]
            data = {
                'id': id_,
                'name': name,
                'type': type_,
            }
            if id_ in STANDARD_PROPERTY_CONTEXTS:
                data['context'] = STANDARD_PROPERTY_CONTEXTS[id_]
            self.properties[id_] = STANDARD_REGISTRY.validate_python(data)
        else:
            data = {
                'id': id_,
                'name': name,
                'type': type_,
            }
            if context:
                data['context'] = context
            self.properties[id_] = ExtensionPropertyRegistry(**data)
        return id_


    def _standard(self, owner, property_id, value=None, index=0, comments=None, **extra):
        if property_id not in STANDARD_PROPERTY_MODELS:
            raise ValueError(f'Canonical standard property is not defined: {property_id}')
        self._property_registry(property_id, *STANDARD_PROPERTIES[property_id])
        data = {
            'id': self._generated_id(owner, property_id, index),
            'property': property_id,
            **extra,
        }
        category_system = STANDARD_PROPERTY_CATEGORY_SYSTEMS.get(property_id)
        if category_system:
            self._standard_category_registry(category_system)
            data['categorySystem'] = category_system
        if value is not None and STANDARD_PROPERTIES[property_id][1] == 'categorical' and not isinstance(value, BaseModel):
            value = SingleCategory(categoryType='singleCategory', label=value)
        if value is not None:
           data['value'] = (
                value.model_dump(by_alias=True, exclude_none=True)
                if hasattr(value, 'model_dump')
                else value
            )
        if comments:
            data['comments'] = comments
        return STANDARD_VALUE.validate_python(data)


    def _category(self, category_system, label, entry_id=None, code=None):
        if category_system in STANDARD_CATEGORY_REGISTRY_MODELS:
            self._standard_category_registry(category_system)
        elif category_system in self.category_systems:
            entry = {
                'entryId': entry_id,
                'code': code,
                'label': label,
            }
            key = entry_id or (code, label)
            previous = self.category_systems[category_system]['entries'].get(key)
            if previous and previous != entry:
                raise ValueError(f'Conflicting category entry: {category_system} {key}')
            self.category_systems[category_system]['entries'][key] = entry
        return SingleCategory(
            categoryType='singleCategory',
            entryId=entry_id,
            code=code,
            label=label,
        )


    def _extension(self, owner, name, value, index=0, category=None, property_id=None, comments=None, entry_id=None, code=None, context=None):
        property_id = property_id or self._generated_id('property', name)
        self._property_registry(property_id, name, 'categorical', context)
        if category:
            value = self._category(category, value, entry_id, code)
        elif not isinstance(value, BaseModel):
            if not isinstance(value, (str, bool)):
                value = str(value)
            value = SingleCategory(categoryType='singleCategory', label=value)
        return ExtensionCategoricalProperty(
            id=self._generated_id(owner, property_id, index),
            property=property_id,
            categorySystem=category,
            value=value,
            comments=comments or None,
        )


    def _extension_quantity(self, owner, name, quantity, index=0, property_id=None, comments=None, context=None):
        property_id = property_id or self._generated_id('property', name)
        self._property_registry(property_id, name, 'quantitative', context)
        return ExtensionQuantitativeProperty(
            id=self._generated_id(owner, property_id, index),
            property=property_id,
            value=quantity,
            comments=comments or None,
        )


    def _extension_composite(self, owner, name, properties, index=0, comments=None, source_ids=None, context=None):
        property_id = self._generated_id('property', name)
        self._property_registry(property_id, name, 'composite', context)
        return ExtensionCompositeProperty(
            id=self._generated_id(owner, property_id, index),
            property=property_id,
            properties=properties,
            comments=comments or None,
            sourceEntries=self._source_entries(source_ids),
        )

    def _source_property(self, owner, name, source_id, registry, index=0, context=None):
        return self._extension(
            owner,
            name,
            SingleCategory(
                categoryType='singleCategory',
                entryId=source_id,
                label=self._master_name(registry, source_id) or source_id,
            ),
            index=index,
            context=context,
        )

    def _ecoinvent_identity(self, owner, source_id, registry, index=0, label=None):
        property_id = ECOINVENT_IDENTITY_PROPERTIES[registry]
        label = label or self._master_name(registry, source_id) or source_id

        if registry in STANDARD_CATEGORY_REGISTRY_NAMES:
            category_system = self._category_registry(registry)
            value = self._category(category_system, label, entry_id=source_id)
        else:
            value = SingleCategory(
                categoryType='singleCategory',
                entryId=source_id,
                label=label,
            )

        if property_id in STANDARD_PROPERTY_MODELS:
            return self._standard(
                owner,
                property_id,
                value,
                index=index,
            )
        return self._extension(
            owner,
            STANDARD_PROPERTIES[property_id][0],
            value,
            index=index,
            property_id=property_id,
            context=STANDARD_PROPERTY_CONTEXTS.get(property_id),
        )

    def _master_name(self, registry, source_id):
        if registry == 'Classifications':
            item = self.classification_values.get(source_id)
            item = item[1] if item else None
        elif registry == 'Compartments':
            item = self.subcompartments.get(source_id)
        elif registry == 'ActivityIndex':
            item = self.master['activityIndexEntry'].get(source_id)
            if item:
                activity_name = item.get_value('activityNameId')
                item = self.master['activityName'].get(activity_name)
        else:
            key = {
                'ActivityNames': 'activityName',
                'Geographies': 'geography',
                'SystemModels': 'systemModel',
                'MacroEconomicScenarios': 'macroEconomicScenario',
                'Companies': 'company',
                'Persons': 'person',
                'Sources': 'source',
                'Units': 'units',
                'Properties': 'property',
                'ElementaryExchanges': 'elementaryExchange',
                'IntermediateExchanges': 'intermediateExchange',
                'Parameters': 'parameter',
            }.get(registry)
            item = self.master.get(key, {}).get(source_id) if key else None

        if not item:
            return None
        for field in ('name', 'title', 'shortname', 'code'):
            value = self._text(self._field(item, field))
            if value:
                return value
            value = item.get_value(field)
            if value:
                return str(value)
        return None


    def _name_properties(self, owner, name, context):
        parts = name.split(', ')
        base = parts[0].strip()
        return [
            self._extension(
                owner,
                f'property_{base}_name_{index}',
                value.strip(),
                context=[context],
            )
            for index, value in enumerate(parts[1:])
            if value.strip()
        ]

    def _corine_code(self, value):
        if not value:
            return None
        match = re.fullmatch(r'\s*CORINE\s+([1-5]\d{0,2}(?:[a-z]\d?)?)\s*', str(value), re.IGNORECASE)
        return match.group(1).lower() if match else None

    def _corine(self, owner, value):
        code = self._corine_code(value)
        if not code:
            return None

        category = STANDARD_CATEGORY_SYSTEMS['CORINE']
        self._standard_category_registry(category)

        return self._standard(
            owner,
            '5ca53a8e-426c-484d-aa48-d3e91730bd9b',
            self._category(
                category,
                str(value).strip(),
                code=code,
            ),
        )


    def _unit(self, source_id=None, name=None):
        master = self.master['units'].get(source_id) if source_id else None
        source_name = self._text(master.get_value('name')) if master else None
        source_name = source_name or name or 'dimensionless'
        canonical_id = self._id(source_id) if source_id else self._generated_id('unit', source_name)

        if canonical_id in self.units:
            return self.units[canonical_id], Decimal('1')

        override = self.config.get('unit_mapping', {}).get(source_id, self.config.get('unit_mapping', {}).get(source_name))
        if override:
            short_name, factor = override if isinstance(override, (tuple, list)) else (override, 1)
            short_name = self._clean_ucum(short_name)
            unit = UCUMUnit(
                codeSystem=UCUM_REGISTRY,
                dimensionality=self._dimensionality(short_name),
                id=canonical_id,
                shortName=short_name,
                semanticName=source_name if short_name != source_name else None,
                unitType='physical',
            )
            factor = Decimal(str(factor))
        else:
            currency = re.fullmatch(r'([A-Z]{3})(?:\(|)?(\d{4})(?:\)|)?(?:basic)?', source_name.replace(' ', ''))
            if currency:
                unit = CurrencyUnit(
                    codeSystem=ISO4217_REGISTRY,
                    id=canonical_id,
                    shortName=currency.group(1),
                    unitType='currency',
                    year=currency.group(2),
                )
                factor = Decimal('1')
            else:
                short_name, factor = self._ucum(source_id, source_name)
                unit = UCUMUnit(
                    codeSystem=UCUM_REGISTRY,
                    dimensionality=self._dimensionality(short_name),
                    id=canonical_id,
                    shortName=short_name,
                    semanticName=source_name if short_name != source_name else None,
                    unitType='physical',
                )

        self.units[canonical_id] = unit
        self.quantities.add_unit(unit)
        return unit, factor

    def _dimensionality(self, unit):
        return {
            DIMENSION_FIELDS[str(name)]: int(exponent)
            for name, exponent in self.quantities.from_ucum(1, unit).dimensionality.items()
            if exponent
        }


    def _ucum(self, source_id, name):
        if source_id in pint_to_ilcd_def:
            value = pint_to_ilcd_def[source_id][2]
            value = value.replace('m**3', 'm3').replace('m**2', 'm2')
            value = value.replace('item', '1').replace('*', '.')
            value = value.replace('day', 'd')
            if value == 'EUR2000':
                return '1', Decimal('1')
            return self._clean_ucum(value), Decimal('1')

        value = name.strip()
        factor = Decimal('1')
        replacements = {
            'dimensionless': '1',
            '% (obsolete)': '%',
            'month': 'mo',
            'year': 'a',
            'hour': 'h',
            'day': 'd',
            'l': 'L',
            'ha': 'har',
            'unit': '1',
            'guest night': '1',
            'point score': '1',
            'kWh': 'kW.h',
            'kWp': 'kW',
            'TEU': 'm3',
            'Eq': 'g',
        }
        if value == 'TEU':
            factor = Decimal('38.5')
        if value in replacements:
            return replacements[value], factor

        value = value.replace('metric ton', 't')
        value = value.replace('year', 'a').replace('yr', 'a')
        value = value.replace('hour', 'h')
        value = value.replace('kWh', 'kW.h').replace('kWp', 'kW')
        value = value.replace('Nm3', 'm3').replace('mÂ³', 'm3').replace('mÂ²', 'm2')
        value = re.sub(r'kg\s+(?:NH3-N|N2O-N|NO3-N|NOx|N2O|N|P2O5|PO4|P|TAN|vehicle)', 'kg', value)
        value = re.sub(r'(?<![A-Za-z])(?:head|seedling|units?|person)(?![A-Za-z])', '1', value)
        value = re.sub(r'(?<![A-Za-z])ha(?![A-Za-z])', 'har', value)
        value = re.sub(r'(?<![A-Za-z])l(?![A-Za-z])', 'L', value)
        value = value.replace('*', '.')
        value = self._clean_ucum(value)

        if value == 'kg/hp.h':
            return 'kg/(kW.h)', Decimal('1') / Decimal('0.745699872')
        if value == 'kW/TEU':
            return 'kW/m3', Decimal('1') / Decimal('38.5')
        if value == 'BTU/kg':
            return '[Btu_IT]/kg', factor
        if value == 'OLD_MJ/kg':
            return 'MJ/kg', factor
        if 'PMH' in value:
            value = value.replace('PMH', '1')
        if value == 'K':
            return 'K', factor
        return value, factor

    def _clean_ucum(self, value):
        value = value.replace('²', '2').replace('³', '3')
        value = value.replace(' ', '')
        value = value.replace('..', '.')
        value = value.replace('/har.a', '/(har.a)')
        value = value.replace('/m2.a', '/(m2.a)')
        value = value.replace('/kg.km', '/(kg.km)')
        value = value.replace('/1.km', '/km')
        value = value.replace('/1', '')
        value = value.replace('1.', '').replace('.1', '')
        return value or '1'

    def _quantity(self, owner, obj, properties, label='amount', amount_field='amount', unit_field='unitId', unit_name_field='unitName', uncertainty_field='uncertainty', context='exchange'):
        amount = obj.get_value(amount_field)
        unit_id = obj.get_value(unit_field)
        unit_name = self._text(self._field(obj, unit_name_field)) if unit_name_field else None
        unit, factor = self._unit(unit_id, unit_name)
        uncertainty = self._uncertainty(owner, self._field(obj, uncertainty_field), properties, label, factor, context) if uncertainty_field else None
        return SingleQuantity(
            amount=Decimal(str(amount)) * factor,
            quantityType='singleQuantity',
            unit=unit.id,
            uncertainty=uncertainty,
        )

    def _scaled_distribution(self, name, parameters, factor):
        distribution = canonical_distribution(name, parameters)
        if factor == 1:
            return distribution
        return {
            'uncertaintyType': 'transformedProbabilityDistribution',
            'distribution': distribution,
            'scale': factor,
            'offset': Decimal('0'),
        }


    def _uncertainty(self, owner, uncertainty, properties, label, factor=Decimal('1'), context='exchange'):
        if not uncertainty:
            return None

        pedigree_matrix = uncertainty.get_value('pedigreeMatrix')
        if pedigree_matrix:
            values = [
                pedigree_matrix.get_value('reliability'),
                pedigree_matrix.get_value('completeness'),
                pedigree_matrix.get_value('temporalCorrelation'),
                pedigree_matrix.get_value('geographicalCorrelation'),
                pedigree_matrix.get_value('furtherTechnologyCorrelation'),
            ]
            code = ''.join(str(value) for value in values)
            properties.append(self._standard(
                owner,
                '63435e58-cd43-4c7b-a916-b49bdf2aef49',
                self._category(
                    STANDARD_CATEGORY_SYSTEMS['pedigree'],
                    code,
                ),
                index=f'{label}:pedigree',
            ))
            additional = sum(
                Decimal(str(pedigree[name][value - 1]))
                for name, value in zip(
                    ('Reliability', 'Completeness', 'Temporal correlation', 'Geographical correlation', 'Further technological correlation'),
                    values,
                )
            )
            dimensionless, _ = self._unit(name='dimensionless')
            properties.append(self._standard(
                owner,
                '24964ee1-b167-4921-90d9-1b7aa18394ae',
                self.quantities.to_entry(
                    self.quantities.scalar(additional, dimensionless.id),
                    dimensionless.id,
                ),
                index=f'{label}:pedigree-variance',
            ))

        for comment in self._texts(uncertainty.get_value('comment')):
            properties.append(self._extension(
                owner,
                f'ECS2 {label} uncertainty comment',
                comment,
                index=f'{label}:{len(properties)}',
                context=[context],
            ))

        for type_ in ('lognormal', 'normal', 'triangular', 'uniform', 'gamma', 'beta', 'binomial', 'undefined'):
            data = uncertainty.get_value(type_)
            if not data:
                continue

            source_variance = data.get_value('variance')
            if source_variance is not None:
                dimensionless, _ = self._unit(name='dimensionless')
                properties.append(self._standard(
                    owner,
                    VARIANCE_PROPERTY,
                    self.quantities.to_entry(
                        self.quantities.scalar(Decimal(str(source_variance)), dimensionless.id),
                        dimensionless.id,
                    ),
                    index=f'{label}:variance',
                ))

            if type_ == 'normal':
                return self._scaled_distribution('Normal', {
                    'mean': Decimal(str(data.get_value('meanValue'))),
                    'variance': Decimal(str(data.get_value('varianceWithPedigreeUncertainty'))),
                }, factor)

            if type_ == 'lognormal':
                median = Decimal(str(data.get_value('meanValue')))
                if median > 0:
                    return self._scaled_distribution('Lognormal', {
                        'median': median,
                        'stdevLog': Decimal(str(data.get_value('varianceWithPedigreeUncertainty'))).sqrt(),
                    }, factor)

            if type_ == 'triangular':
                minimum = Decimal(str(data.get_value('minValue')))
                mode = Decimal(str(data.get_value('mostLikelyValue')))
                maximum = Decimal(str(data.get_value('maxValue')))
                if minimum <= mode <= maximum and minimum < maximum:
                    return self._scaled_distribution('Triangular', {
                        'lowerLimit': minimum,
                        'shape': mode,
                        'upperLimit': maximum,
                    }, factor)

            if type_ == 'uniform':
                minimum = Decimal(str(data.get_value('minValue')))
                maximum = Decimal(str(data.get_value('maxValue')))
                if minimum < maximum:
                    return self._scaled_distribution('Uniform', {
                        'minimum': minimum,
                        'maximum': maximum,
                    }, factor)

            if type_ == 'gamma':
                scale = Decimal(str(data.get_value('scale'))) * factor
                return {
                    'uncertaintyType': 'truncatedProbabilityDistribution',
                    'minimum': Decimal(str(data.get_value('minValue'))) * factor,
                    'distribution': canonical_distribution('Gamma', {
                        'shape': Decimal(str(data.get_value('shape'))),
                        'rate': Decimal('1') / scale,
                    }),
                }

            self._preserve_uncertainty(owner, label, type_, data, properties, context)
            return None

        return None

    def _preserve_uncertainty(self, owner, label, type_, data, properties, context):
        properties.append(self._extension(owner, f'ECS2 {label} uncertainty type', type_, index=f'{label}:type', context=[context]))
        for field in data.VALID:
            value = data.get_value(field)
            if self._present(value):
                properties.append(self._extension(owner, f'ECS2 {label} uncertainty {field}', value, index=f'{label}:{field}', context=[context]))


    def _source(self, source):
        source_id = source.get_value('id')
        extensions = []
        for field, property_ in SOURCE_EXTENSIONS.items():
            values = self._texts(source.get_value(field)) if field == 'comment' else [source.get_value(field)]
            for value in values:
                if value is not None and str(value).strip():
                    extensions.append(SourceSemanticExtension(property=property_, value=str(value)))

        for field, property_ in (
            ('journal', DCTermsProperty.http___purl_org_dc_terms_isPartOf),
            ('issueNo', BIBOProperty.http___purl_org_ontology_bibo_issue),
            ('titleOfAnthology', DCTermsProperty.http___purl_org_dc_terms_isPartOf),
            ('placeOfPublications', DCTermsProperty.http___purl_org_dc_terms_spatial),
        ):
            value = source.get_value(field)
            if value:
                extensions.append(SourceSemanticExtension(property=property_, value=str(value)))

        return self._ensure_source(
            source_id,
            title=source.get_value('title'),
            first_author=source.get_value('firstAuthor'),
            additional_authors=source.get_value('additionalAuthors'),
            year=source.get_value('year'),
            pages=source.get_value('pageNumbers'),
            source_type=source.get_value('sourceType'),
            extensions=extensions,
        )

    def _ensure_source(self, source_id, title=None, first_author=None, additional_authors=None, year=None, pages=None, source_type=None, extensions=None):
        canonical_id = self._id(source_id)
        extensions = list(extensions or [])

        source_year = year
        if source_year and not re.fullmatch(r'\d{4}', str(source_year)):
            extensions.append(SourceSemanticExtension(
                property=DCTermsProperty.http___purl_org_dc_terms_date,
                value=str(source_year),
            ))
            source_year = None

        source_pages = pages
        if source_pages and not re.fullmatch(r'([A-Za-z]?\d+|[IVXLCDMivxlcdm]+)([-â€“]([A-Za-z]?\d+|[IVXLCDMivxlcdm]+))?', str(source_pages)):
            extensions.append(SourceSemanticExtension(
                property=BIBOProperty.http___purl_org_ontology_bibo_pages,
                value=str(source_pages),
            ))
            source_pages = None

        authors = []
        if self._present(first_author):
            authors.append(SourceAuthor(name=str(first_author)))
        if self._present(additional_authors):
            authors.append(SourceAuthor(name=str(additional_authors)))

        identifiers = [OtherSourceIdentification(
            system='ecoinvent source id',
            value=source_id,
        )]
        if source_type is not None:
            identifiers.append(OtherSourceIdentification(
                system='ecoinvent source type',
                value=str(source_type),
            ))

        if canonical_id in self.sources:
            source = self.sources[canonical_id]
            data = source.model_dump(by_alias=True, exclude_none=True)
            if title and (
                str(source.title).startswith('ecoinvent source ')
                or source.title == 'Published source associated with the ecoinvent dataset'
            ):
                data['title'] = title
            if source_year and source.year is None:
                data['year'] = str(source_year)
            if source_pages and source.pages is None:
                data['pages'] = str(source_pages)

            existing = {value['name'] for value in data.get('authors', [])}
            new = [
                value.model_dump(by_alias=True, exclude_none=True)
                for value in authors if value.name not in existing
            ]
            if new:
                data['authors'] = data.get('authors', []) + new

            existing = {(value['system'], value['value']) for value in data.get('identifiers', [])}
            data['identifiers'] = data.get('identifiers', []) + [
                value.model_dump(by_alias=True, exclude_none=True)
                for value in identifiers
                if (value.system, value.value) not in existing
            ]

            existing = {(value['property'], value['value']) for value in data.get('extensions', [])}
            new = [
                value.model_dump(by_alias=True, exclude_none=True)
                for value in extensions
                if (value.property, value.value) not in existing
            ]
            if new:
                data['extensions'] = data.get('extensions', []) + new
            self.sources[canonical_id] = Source.model_validate(data)
            return canonical_id

        self.sources[canonical_id] = Source(
            id=canonical_id,
            sourceType=BIBODocumentClass.bibo_Document,
            title=title or f'ecoinvent source {source_id}',
            authors=authors or None,
            year=source_year,
            pages=source_pages,
            identifiers=identifiers,
            extensions=extensions or None,
        )
        return canonical_id


    def _source_ids(self, obj, field='sourceId', year_field='sourceYear', author_field='sourceFirstAuthor', pages_field='pageNumbers', title=None):
        ids = []
        for source_id in self._many_value(obj, field):
            ids.append(self._ensure_source(
                source_id,
                title=title,
                first_author=obj.get_value(author_field) if author_field else None,
                year=obj.get_value(year_field) if year_field else None,
                pages=obj.get_value(pages_field) if pages_field else None,
            ))
            master = self.master['source'].get(source_id)
            if master:
                self._source(master)
        return ids

    def _many_value(self, obj, field):
        value = obj.get_value(field)
        if value is None:
            return []
        return value if isinstance(value, list) else [value]


    def _process_properties(self, process_id):
        description = self.source.activityDescription
        activity = description.activity
        properties = []
        name = self._text(activity.get_value('activityName'))

        for index, activity_name_id in enumerate(self._many_value(activity, 'activityNameId')):
            properties.append(self._ecoinvent_identity(
                process_id, activity_name_id, 'ActivityNames', index, name
            ))

        properties.extend(self._name_properties(process_id, name, 'process'))
        self._text_and_image_properties(process_id, activity.get_value('generalComment'), 'general comment', properties, ['process'])

        type_ = activity.get_value('type')
        if type_ in PROCESS_TYPE:
            properties.append(self._standard(process_id, '6cd90a91-83d9-4c97-b4ec-aac59c8553ea', PROCESS_TYPE[type_]))
        else:
            properties.append(self._extension(process_id, 'ECS2 process type', type_, context=['process']))

        special = activity.get_value('specialActivityType')
        if special in SPECIAL_ACTIVITY:
            properties.append(self._standard(process_id, 'da8735d7-e473-4c5b-8532-25bc40aba761', SPECIAL_ACTIVITY[special]))

        inheritance = activity.get_value('inheritanceDepth')
        if inheritance in INHERITANCE:
            properties.append(self._standard(process_id, '85194c11-6de9-4272-a7ff-c64aa0bea6ea', INHERITANCE[inheritance]))
        elif self._present(inheritance):
            properties.append(self._extension(process_id, 'ECS2 inheritance depth', inheritance, context=['process']))

        if activity.get_value('parentActivityId'):
            properties.append(self._source_property(process_id, 'ecoinvent parent activity id', activity.get_value('parentActivityId'), 'ActivityIndex'))

        if activity.get_value('masterAllocationPropertyId'):
            properties.append(self._source_property(process_id, 'ecoinvent master allocation property id', activity.get_value('masterAllocationPropertyId'), 'Properties'))

        for index, classification in enumerate(self._many(description, 'classification')):
            properties.extend(self._classification(process_id, classification, index, 'process'))

        properties.extend(self._geography(process_id))
        properties.extend(self._time(process_id))
        properties.extend(self._macro_scenario(process_id))
        properties.extend(self._representativeness_properties(process_id))

        technology = description.technology
        technology_level = TECHNOLOGY.get(technology.get_value('technologyLevel'), technology.get_value('technologyLevel'))
        if self._present(technology_level):
            properties.append(self._standard(
                process_id,
                'ffb442e6-9601-417e-b8f5-08061ed41441',
                str(technology_level).lower(),
            ))

        energy = activity.get_value('energyValues')
        if energy is not None:
            properties.append(self._standard(
                process_id,
                'b97e1868-4c04-4d7e-bd0c-45c79ddc8299',
                ENERGY.get(energy, str(energy)),
            ))

        for field in ('activityNameContextId', 'parentActivityContextId', 'masterAllocationPropertyContextId', 'datasetIcon'):
            value = activity.get_value(field)
            if self._present(value):
                properties.append(self._extension(process_id, f'ECS2 {field}', value, context=['process']))

        value = activity.get_value('masterAllocationPropertyIdOverwrittenByChild')
        if self._present(value):
            properties.append(self._extension(process_id, 'ECS2 masterAllocationPropertyIdOverwrittenByChild', value, context=['process']))

        for index, synonym in enumerate(self._texts(activity.get_value('synonym'))):
            properties.append(self._extension(process_id, 'ECS2 activity synonym', synonym, index, context=['process']))
        for index, tag in enumerate(self._many_value(activity, 'tag')):
            properties.append(self._extension(process_id, 'ECS2 activity tag', tag, index, context=['process']))

        self._text_and_image_properties(process_id, activity.get_value('allocationComment'), 'allocation comment', properties, ['process'])
        self._text_and_image_properties(process_id, technology.get_value('comment'), 'technology comment', properties, ['process'])
        self._text_and_image_properties(process_id, description.geography.get_value('comment'), 'geography comment', properties, ['process'])
        self._text_and_image_properties(process_id, description.timePeriod.get_value('comment'), 'time period comment', properties, ['process'])

        return properties

    def _process_comments(self):
        description = self.source.activityDescription
        activity = description.activity
        comments = []
        comments.extend(self._comments(activity.get_value('generalComment'), 'generalComment'))
        comments.extend(self._comments(activity.get_value('allocationComment'), 'allocationComment'))
        comments.extend(self._comments(description.technology.get_value('comment'), 'technology.comment'))
        comments.extend(self._comments(description.geography.get_value('comment'), 'geography.comment'))
        comments.extend(self._comments(description.timePeriod.get_value('comment'), 'timePeriod.comment'))
        comments.extend(self._comments(description.macroEconomicScenario.get_value('comment'), 'macroEconomicScenario.comment'))
        comments.extend(self._comments(activity.get_value('includedActivitiesStart'), 'includedActivitiesStart'))
        comments.extend(self._comments(activity.get_value('includedActivitiesEnd'), 'includedActivitiesEnd'))

        geography_id = description.geography.get_value('geographyId')
        master = self.master['geography'].get(geography_id)
        if master:
            comments.extend(self._comments(master.get_value('comment'), 'geography.masterComment'))
        return comments


    def _classification(self, owner, classification, index=0, context=None):
        source_id = classification.get_value('classificationId')
        system_name = self._text(classification.get_value('classificationSystem'), 'classification')
        value = self._text(classification.get_value('classificationValue'), source_id)
        properties = []
        code, separator, label = value.partition(':')
        code = code.strip() if separator else None
        label = label.strip() if separator else value.strip()
        normalized = system_name.lower()

        if normalized == 'cpc':
            properties.append(self._standard(
                owner,
                'c3988d68-211f-49f4-85c8-cbc47b30f83b',
                self._category(
                    STANDARD_CATEGORY_SYSTEMS['CPC'],
                    label,
                    entry_id=source_id,
                    code=code,
                ),
                index=index,
            ))
        elif 'isic' in normalized:
            properties.append(self._standard(
                owner,
                'a158ab98-408a-430e-9cba-4bce9b85b9e1',
                self._category(
                    STANDARD_CATEGORY_SYSTEMS['ISIC'],
                    label,
                    entry_id=source_id,
                    code=code,
                ),
                index=index,
            ))
        elif 'by-product' in normalized and value in ('allocatable product', 'Recyclable', 'Waste'):
            properties.append(self._standard(
                owner,
                'd695f836-5059-4e63-b6f0-bd093bc0e7f8',
                self._category(
                    STANDARD_CATEGORY_SYSTEMS['byProduct'],
                    label,
                    entry_id=source_id,
                    code=code,
                ),
                index=index,
            ))
        else:
            properties.append(self._extension(
                owner,
                f'ECS2 classification {system_name}',
                SingleCategory(
                    categoryType='singleCategory',
                    entryId=source_id,
                    code=code,
                    label=label,
                ),
                index=index,
                property_id=self._generated_id('property', 'classification', system_name),
                context=[context] if context else None,
            ))

        source_context = classification.get_value('classificationContextId')
        if source_context:
            properties.append(self._extension(
                owner,
                'ECS2 classification context id',
                source_context,
                index=index,
                context=[context] if context else None,
            ))
        return properties


    def _geography(self, owner):
        geography = self.source.activityDescription.geography
        source_id = geography.get_value('geographyId')
        master = self.master['geography'].get(source_id)
        short_name = self._text(geography.get_value('shortname')) or source_id
        full_name = (self._text(master.get_value('name')) if master else None) or short_name
        ecoinvent_registry = self._category_registry('Geographies')

        scope = [self._standard(
            owner,
            ECOINVENT_GEOGRAPHY_PROPERTY,
            self._category(
                ecoinvent_registry,
                full_name,
                entry_id=source_id,
                code=short_name,
            ),
        )]

        is_row = short_name.strip().lower() == 'row' or str(full_name).strip().lower() == 'rest of world'
        if is_row:
            scope.append(self._standard(owner, ECOINVENT_ROW_PROPERTY, True))
        else:
            un_code = master.get_value('uNCode') if master else None
            if short_name.upper() == 'GLO':
                un_code = '001'
                full_name = 'Global'
            if self._present(un_code):
                if UN_M49_REGISTRY not in self.categories:
                    self.categories[UN_M49_REGISTRY] = RegistryReference(
                        id=UN_M49_REGISTRY,
                        name='UN M49 Code',
                        referenceType='registry',
                        uri='https://unstats.un.org/unsd/methodology/m49/',
                    )
                scope.append(self._standard(
                    owner,
                    'b629e5bf-48a8-4410-9103-f5cda1d9f729',
                    self._category(
                        UN_M49_REGISTRY,
                        full_name,
                        code=str(un_code).zfill(3),
                    ),
                ))

        properties = [self._standard(
            owner,
            '99a6248f-dbb0-49dc-a4ad-23abab6ba25f',
            properties=scope,
        )]

        if master:
            degree, _ = self._unit(name='deg')
            for field in ('latitude', 'longitude'):
                value = master.get_value(field)
                if value is not None:
                    quantity = self.quantities.to_entry(self.quantities.scalar(value, degree.id), degree.id)
                    properties.append(self._extension_quantity(owner, field, quantity, context=['process']))
            for field in ('ISOTwoLetterCode', 'ISOThreeLetterCode', 'uNRegionCode', 'uNSubregionCode'):
                value = master.get_value(field)
                if self._present(value):
                    properties.append(self._extension(owner, f'ecoinvent geography {field}', value, context=['process']))

        context = geography.get_value('geographyContextId')
        if context:
            properties.append(self._extension(owner, 'ECS2 geography context id', context, context=['process']))
        return properties


    def _time(self, owner):
        time = self.source.activityDescription.timePeriod
        value = time.get_value('isDataValidForEntirePeriod')
        if value is None:
            return []
        return [self._standard(
            owner,
            '7e79e7af-71de-41a3-9dad-862e37cbe9ca',
            value,
        )]


    def _macro_scenario(self, owner):
        scenario = self.source.activityDescription.macroEconomicScenario
        source_id = scenario.get_value('macroEconomicScenarioId')
        name = self._text(scenario.get_value('name'))
        properties = [self._standard(
            owner,
            'a4146cc4-35d8-4a5e-8c75-9d3b717b4a24',
            self._category(
                STANDARD_CATEGORY_SYSTEMS['macroEconomicScenario'],
                name or self._master_name('MacroEconomicScenarios', source_id) or source_id,
                entry_id=source_id,
            ),
        )]
        context = scenario.get_value('macroEconomicScenarioContextId')
        if context:
            properties.append(self._extension(owner, 'ECS2 macro-economic scenario context id', context, context=['process']))
        return properties

    def _representativeness_properties(self, owner):
        representativeness = self.source.modellingAndValidation.get_value('representativeness')
        if not representativeness:
            return []

        properties = []
        percent = representativeness.get_value('percent')
        if percent is not None:
            unit, _ = self._unit(name='%')
            quantity = self.quantities.to_entry(self.quantities.scalar(percent, unit.id), unit.id)
            properties.append(self._standard(
                owner,
                '542f6612-0aa9-4d52-82c0-7bb0f6c21d19',
                quantity,
            ))
        return properties

    def _aggregated_processes(self, name):
        activity = self.source.activityDescription.activity
        description = '\n'.join(
            self._texts(activity.get_value('includedActivitiesStart')) +
            self._texts(activity.get_value('includedActivitiesEnd'))
        ) or None
        return [IncludedProcess(processName=name, description=description)]


    def _validity_property(self, owner):
        time = self.source.activityDescription.timePeriod
        start = time.get_value('startDate')
        end = time.get_value('endDate')
        if start is None or end is None:
            return None

        def label(value):
            return value.isoformat() if hasattr(value, 'isoformat') else str(value)

        valid_from = self._standard(
            owner,
            '406bf044-7c7d-4a66-af04-4e19b1296cf3',
            label(start),
            index='valid-from',
        )
        valid_until = self._standard(
            owner,
            '68e86569-fe18-4283-9a6a-4b9e4246021f',
            label(end),
            index='valid-until',
        )
        return self._standard(
            owner,
            '6ee6a892-7c74-432f-a65d-261691d9f562',
            index='validity',
            properties=[valid_from, valid_until],
        )


    def _file_information(self, file_id, source_id, dataset_type):
        file = self.source.administrativeInformation.fileAttributes
        if dataset_type == 'process':
            creation = file.get_value('creationTimestamp') or file.get_value('fileTimestamp')
            last_edit = file.get_value('lastEditTimestamp') or file.get_value('fileTimestamp')
            creation = self._aware(creation)
            last_edit = self._aware(last_edit)
            if last_edit < creation:
                creation = last_edit
            revision = int(file.get_value('majorRevision')) * 10 + int(file.get_value('minorRevision'))
            dataset_version = f"{file.get_value('majorRelease')}.{file.get_value('minorRelease')}.{revision}"
            schema_version = self._semantic_version(file.get_value('internalSchemaVersion') or '2.0')
        else:
            creation = last_edit = self.generated_timestamp
            dataset_version = self._semantic_version(self.config.get('canonical_dataset_version', '0.1.0'))
            schema_version = self._semantic_version(self.config.get('canonical_schema_version', '0.1.0'))

        downloadable = self.config['downloadable_uri']
        if callable(downloadable):
            downloadable = downloadable(source_id, file_id)
        else:
            downloadable = downloadable.format(id=file_id, source_id=source_id, dataset_type=dataset_type)

        return FileInformation(
            downloadableURI=downloadable,
            timestamp=Timestamps(creation=creation, lastEdit=last_edit),
            versioning=FileVersioning(
                datasetVersion=dataset_version,
                schemaVersion=schema_version,
            ),
        )

    def _aware(self, value):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    def _semantic_version(self, value):
        parts = str(value).split('.')
        parts = (parts + ['0', '0'])[:3]
        return '.'.join(str(int(part)) for part in parts)

    @staticmethod
    def _source_entries(source_ids, role=None):
        if not source_ids:
            return None
        return [
            {
                'reference': source_id,
                **({'role': role} if role else {}),
            }
            for source_id in source_ids
        ]


    def _file_reference(self, target_type, file_id):
        return {
            'referenceType': 'internalFile',
            'fileId': file_id,
            'targetType': target_type,
        }

    def _parameter_reference(self, parameter_id):
        return {
            'referenceType': 'internal',
            'targetType': 'parameter',
            'parameterId': parameter_id,
            'fileId': self.parameterization_id,
        }

    def _entry_reference(self, target_type, entry_id):
        key = 'exchangeId' if target_type == 'exchange' else 'propertyId'
        return {
            'referenceType': 'internal',
            'fileId': self.process_id,
            'targetType': target_type,
            key: entry_id,
        }

    @staticmethod
    def _formula_arguments(value):
        arguments = []
        start = 0
        depth = 0
        quote = None
        escape = False

        for index, character in enumerate(value):
            if quote:
                if escape:
                    escape = False
                elif character == '\\':
                    escape = True
                elif character == quote:
                    quote = None
                continue

            if character in "'\"":
                quote = character
            elif character == '(':
                depth += 1
            elif character == ')':
                depth -= 1
            elif character == ',' and depth == 0:
                arguments.append(value[start:index].strip())
                start = index + 1

        arguments.append(value[start:].strip())
        return arguments

    @staticmethod
    def _formula_string(value):
        value = value.strip()
        if len(value) < 2 or value[0] not in "'\"" or value[-1] != value[0]:
            raise ValueError(f'Expected quoted ECS2 formula string, got: {value}')
        return value[1:-1]

    @staticmethod
    def _formula_call(value, name):
        start = value.rfind(name + '(')
        if start < 0:
            return None

        open_ = start + len(name)
        depth = 0
        quote = None
        escape = False

        for index in range(open_, len(value)):
            character = value[index]

            if quote:
                if escape:
                    escape = False
                elif character == '\\':
                    escape = True
                elif character == quote:
                    quote = None
                continue

            if character in "'\"":
                quote = character
            elif character == '(':
                depth += 1
            elif character == ')':
                depth -= 1
                if depth == 0:
                    return start, index + 1, value[open_ + 1:index]

        raise ValueError(f'Unclosed ECS2 {name} expression: {value[start:]}')

    def _unit_conversion_factor(self, source_name, target_name):
        source, source_factor = self._unit(name=source_name)
        target, target_factor = self._unit(name=target_name)

        if source.unitType != 'physical' or target.unitType != 'physical':
            raise ValueError(
                f'Unsupported ECS2 UnitConversion between {source_name!r} and {target_name!r}'
            )

        quantity = self.quantities.scalar(source_factor, source.id)
        converted = self.quantities.convert(quantity, target.id)
        return Decimal(str(converted.magnitude)) / target_factor

    def _unit_conversion_reference(self, source_name, target_name):
        key = source_name, target_name
        if key in self.unit_conversion_refs:
            return self.unit_conversion_refs[key]

        factor = self._unit_conversion_factor(source_name, target_name)
        unit, _ = self._unit(name='dimensionless')
        parameter_id = self._generated_id(
            'parameter',
            'ECS2 UnitConversion',
            source_name,
            target_name,
        )
        variable = f'_ecs2_uc_{str(parameter_id).replace("-", "")}'
        self.parameters.append(SimpleQuantityInput(
            id=parameter_id,
            parameterType='simpleInput',
            resultType='quantity',
            name=f'Conversion from {source_name} to {target_name}',
            variableName=variable,
            entry=SingleQuantity(
                quantityType='singleQuantity',
                amount=factor,
                unit=unit.id,
            ),
        ))
        self.unit_conversion_refs[key] = variable
        return variable

    def _formula_unit_conversions(self, formula):
        while True:
            call = self._formula_call(formula, 'UnitConversion')
            if call is None:
                return formula

            start, end, content = call
            arguments = self._formula_arguments(content)
            if len(arguments) != 3:
                raise ValueError(f'Invalid ECS2 UnitConversion: {formula[start:end]}')

            value, source_name, target_name = arguments
            source_name = self._formula_string(source_name)
            target_name = self._formula_string(target_name)
            try:
                value = str(Decimal(value.replace(',', '.').replace('_', '')))
            except Exception:
                pass
            variable = self._unit_conversion_reference(source_name, target_name)
            formula = formula[:start] + f'(({value}) * {variable})' + formula[end:]

    def _formula_reference(self, source_id, production_volume=False):
        key = source_id, production_volume
        if key in self.formula_refs:
            return self.formula_refs[key]

        exchange = self.exchange_refs.get(source_id)
        if exchange is None:
            raise ValueError(f'ECS2 Ref points to unknown exchange: {source_id}')

        exchange_id = self._id(source_id)
        if production_volume:
            source_flow_id = exchange.get_value('intermediateExchangeId')
            if not source_flow_id or exchange.get_value('productionVolumeAmount') is None:
                raise ValueError(
                    f'ECS2 Ref points to missing production volume: {source_id}'
                )
            entry_id = self._generated_id(
                exchange_id,
                'b3b96e47-db1f-496c-b73d-55b91716a5e7',
                'production-volume',
            )
            target_type = 'property'
            suffix = '_production_volume'
        else:
            entry_id = exchange_id
            target_type = 'exchange'
            suffix = ''

        variable = f'_ecs2_ref_{source_id.replace("-", "")}{suffix}'
        parameter_id = self._generated_id(
            'parameter',
            'ECS2 Ref',
            source_id,
            'production-volume' if production_volume else 'amount',
        )
        self.parameters.append(QuantityInputFromEntry(
            id=parameter_id,
            parameterType='inputFromEntry',
            resultType='quantity',
            variableName=variable,
            entryId=self._entry_reference(target_type, entry_id),
        ))
        self.formula_refs[key] = variable
        return variable

    def _formula_references(self, formula):
        pattern = re.compile(
            r"Ref\(\s*['\"]([^'\"]+)['\"]"
            r"(?:\s*,\s*['\"]([^'\"]+)['\"])?\s*\)"
        )

        def replace(match):
            kind = match.group(2)
            if kind not in (None, 'ProductionVolume'):
                raise ValueError(f'Unsupported ECS2 Ref type: {kind}')
            return self._formula_reference(
                match.group(1),
                production_volume=kind == 'ProductionVolume',
            )

        return pattern.sub(replace, formula)


    def _formula(self, formula, formula_id=None):
        if not formula:
            return formula

        formula = formula.strip()
        formula = re.sub(r'(?<=\d),(?=\d)', '.', formula)
        formula = self._formula_unit_conversions(formula)
        formula = self._formula_references(formula)
        formula = re.sub(
            r'((?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*%',
            r'(\1 / 100)',
            formula,
        )
        if '%' in formula:
            raise ValueError(f'Unsupported ECS2 percentage expression: {formula}')
        return self._formula_correction(formula, formula_id)

    def _formula_correction(self, formula, formula_id):
        if formula_id is None:
            return formula

        corrections = self.config.get('formula_corrections', {})
        correction = corrections.get(str(formula_id))
        if correction is None:
            correction = corrections.get(str(self._id(formula_id)))
        if correction is None:
            return formula
        if callable(correction):
            return correction(formula)
        if isinstance(correction, str):
            return correction
        for source, target in correction.items():
            formula = formula.replace(source, target)
        return formula

    def _formula_cache_key(self, formula, variable, quantity, metadata):
        values = []
        for item in metadata or []:
            value = item.model_dump(by_alias=True, exclude_none=True)
            value.pop('id', None)
            values.append(repr(value))
        return (
            formula,
            variable,
            quantity.model_dump_json(by_alias=True, exclude_none=True),
            tuple(values),
        )


    def _parameterize_entry(
        self,
        entry_id,
        obj,
        quantity,
        target_type,
        variable_field='variableName',
        formula_field='mathematicalRelation',
        calculated_field='isCalculatedAmount',
        metadata=None,
    ):
        variable = obj.get_value(variable_field) if variable_field else None
        source_formula = obj.get_value(formula_field) if formula_field else None
        source_formula_id = obj.get_value('parameterId') or obj.get_value('id')
        formula = self._formula(source_formula, source_formula_id)
        calculated = obj.get_value(calculated_field) if calculated_field else None

        if formula:
            key = self._formula_cache_key(formula, variable or None, quantity, metadata)
            parameter_id = self.formula_cache.get(key)
            if parameter_id is None:
                parameter_id = self._generated_id('parameter', target_type, entry_id, 'formula')
                properties = list(metadata or [])
                self.parameters.append(QuantityFormula(
                    id=parameter_id,
                    parameterType='formula',
                    resultType='quantity',
                    variableName=variable or None,
                    formula=formula,
                    expectedUnit=quantity.unit,
                    resultingEntry=quantity,
                    properties=properties or None,
                ))
                self.formula_cache[key] = parameter_id
            if metadata is not None:
                metadata.clear()
            return ResultingQuantity(
                quantityType='resultingQuantity',
                parameter=self._parameter_reference(parameter_id),
            )

        if variable:
            parameter_id = self._generated_id('parameter', target_type, entry_id, 'input')
            properties = []
            if calculated:
                properties.append(self._extension(parameter_id, 'ECS2 isCalculatedAmount', calculated))
            self.parameters.append(QuantityInputFromEntry(
                id=parameter_id,
                parameterType='inputFromEntry',
                resultType='quantity',
                variableName=variable,
                entryId=self._entry_reference(target_type, entry_id),
                properties=properties or None,
            ))

        return quantity


    def _parameter(self, parameter, index):
        source_parameter_id = parameter.get_value('parameterId')
        parameter_id = self._id(source_parameter_id)
        properties = [self._ecoinvent_identity(
            parameter_id,
            source_parameter_id,
            'Parameters',
            index,
        )]

        for field in ('parameterContextId', 'unitContextId'):
            value = parameter.get_value(field)
            if self._present(value):
                properties.append(self._extension(parameter_id, f'ECS2 parameter {field}', value))

        metadata = []
        name = self._text(parameter.get_value('name'))
        quantity = self._quantity(
            parameter_id,
            parameter,
            metadata,
            label=f'parameter {name or index}',
            context='parameter',
        )
        properties.extend(metadata)

        properties.extend(self._source_reference_metadata(parameter_id, parameter, prefix='parameter'))

        source_formula = parameter.get_value('mathematicalRelation')
        formula = self._formula(source_formula, source_parameter_id)
        calculated = parameter.get_value('isCalculatedAmount')
        if not formula and calculated:
            properties.append(self._extension(parameter_id, 'ECS2 isCalculatedAmount', calculated))

        common = {
            'id': parameter_id,
            'resultType': 'quantity',
            'name': name or None,
            'variableName': parameter.get_value('variableName') or None,
            'properties': properties or None,
            'comments': self._comments(parameter.get_value('comment'), 'comment') or None,
            'sourceEntries': self._source_entries(self._source_ids(parameter)),
        }
        if formula:
            self.parameters.append(QuantityFormula(
                **common,
                parameterType='formula',
                formula=formula,
                expectedUnit=quantity.unit,
                resultingEntry=quantity,
            ))
        else:
            self.parameters.append(SimpleQuantityInput(
                **common,
                parameterType='simpleInput',
                entry=quantity,
            ))

    def _exchanges(self, process_properties):
        exchanges = []
        for exchange in self._many(self.source.flowData, 'intermediateExchange'):
            exchanges.append(self._exchange(exchange, 'intermediate'))
        for exchange in self._many(self.source.flowData, 'elementaryExchange'):
            exchanges.append(self._exchange(exchange, 'elementary'))
        for index, parameter in enumerate(self._many(self.source.flowData, 'parameter')):
            self._parameter(parameter, index)
        for index, impact in enumerate(self._many(self.source.flowData, 'impactIndicator')):
            self._preserve_impact(impact, index, process_properties)
        return exchanges


    def _exchange(self, exchange, flow_type):
        source_flow_id = exchange.get_value(f'{flow_type}ExchangeId')
        exchange_id = self._id(exchange.get_value('id'))
        source_properties = self._property_sources(exchange, flow_type, source_flow_id)
        property_metadata = []
        flow_id = self._flow(
            source_flow_id,
            flow_type,
            exchange,
            source_properties,
            exchange_id,
            property_metadata,
        )
        properties = [
            self._standard(exchange_id, '5cc54527-0cb9-4180-82cc-d13240e94e50', flow_type),
        ]

        input_group = exchange.get_value('inputGroup')
        output_group = exchange.get_value('outputGroup')
        if input_group is not None:
            properties.append(self._standard(exchange_id, '42b3c201-539f-4891-97cc-66156ac53083', 'input'))
        elif output_group is not None:
            properties.append(self._standard(exchange_id, '42b3c201-539f-4891-97cc-66156ac53083', 'output'))
            if flow_type == 'intermediate' and output_group not in (0, 2):
                properties.append(self._extension(
                    exchange_id,
                    'ECS2 output group',
                    OUTPUT_GROUP.get(output_group, output_group),
                    context=['exchange'],
                ))
        else:
            properties.append(self._extension(exchange_id, 'ECS2 input-output group', 'unspecified', context=['exchange']))

        if flow_type == 'intermediate':
            if output_group == 0:
                properties.append(self._standard(
                    exchange_id,
                    'eb06d312-7738-42b2-a6c9-ac1fe9a018f4',
                    True,
                ))
            properties.extend(self._intermediate_exchange(exchange_id, exchange))
        else:
            direction = 'resource extraction' if input_group is not None else 'emission'
            properties.append(self._standard(exchange_id, '735f3642-52b0-4f1c-90b3-78b0f7bafbeb', direction))
            properties.extend(self._elementary_context(exchange_id, exchange))

        quantity_properties = []
        quantity = self._quantity(exchange_id, exchange, quantity_properties)
        self.exchange_quantities[exchange_id] = quantity
        quantity = self._parameterize_entry(
            exchange_id,
            exchange,
            quantity,
            'exchange',
            metadata=quantity_properties,
        )
        properties.extend(quantity_properties)
        properties.extend(property_metadata)

        if self.config.get('convert_properties', True):
            properties.extend(self._properties(
                exchange_id,
                source_properties,
                self.flows[flow_id].name,
                standard_only=False,
            ))
        properties.extend(self._property_metadata(exchange_id, source_properties))

        properties.extend(self._transfer_coefficients(exchange_id, exchange))
        properties.extend(self._exchange_metadata(exchange_id, exchange, flow_type))

        return Exchange(
            id=exchange_id,
            flowable=flow_id,
            quantity=quantity,
            properties=properties or None,
            comments=self._comments(exchange.get_value('comment'), 'comment') or None,
            sourceEntries=self._source_entries(self._source_ids(exchange)),
        )


    def _property_sources(self, exchange, flow_type, source_id):
        values = list(self._many(exchange, 'property'))
        seen = {value.get_value('propertyId') for value in values}
        master = self.master[f'{flow_type}Exchange'].get(source_id)
        if master:
            values.extend(
                value for value in self._many(master, 'property')
                if value.get_value('propertyId') not in seen
            )
        return values


    def _flow(self, source_id, flow_type, exchange, source_properties, metadata_owner, property_metadata):
        flow_id = self._id(source_id)
        if flow_id in self.flows:
            return flow_id

        master = self.master[f'{flow_type}Exchange'].get(source_id)
        name = self._text(master.get_value('name')) if master else self._text(exchange.get_value('name'))
        core_name = name.split(',')[0].strip()
        registry = 'IntermediateExchanges' if flow_type == 'intermediate' else 'ElementaryExchanges'
        properties = [
            self._ecoinvent_identity(flow_id, source_id, registry, label=name),
        ]
        properties.extend(self._name_properties(flow_id, name, 'flow'))

        formula = exchange.get_value('formula') or (master.get_value('formula') if master else None)
        corine = self._corine(flow_id, formula)
        if corine:
            properties.append(corine)
        elif flow_type == 'elementary' and self._present(formula):
            properties.append(self._standard(
                flow_id,
                'ed3b8a28-02a1-4a78-95d5-b6b1c3910d23',
                str(formula),
            ))

        for index, classification in enumerate(self._many(exchange, 'classification')):
            properties.extend(self._classification(flow_id, classification, index, 'flow'))

        if self.config.get('convert_properties', True):
            properties.extend(self._properties(
                flow_id,
                source_properties,
                core_name,
                standard_only=True,
                metadata_owner=metadata_owner,
                metadata_target=property_metadata,
            ))

        if master:
            for index, classification in enumerate(self._many(master, 'classification')):
                properties.extend(self._classification(flow_id, classification, index, 'flow'))
            cas = master.get_value('casNumber') or exchange.get_value('casNumber')
            if cas:
                properties.append(self._standard(flow_id, '55e46169-4f58-4204-a574-20703fdc02c4', cas))
            default_variable = master.get_value('defaultVariableName')
            if default_variable:
                properties.append(self._extension(flow_id, 'ECS2 flow defaultVariableName', default_variable, context=['flow']))
            for index, synonym in enumerate(self._texts(master.get_value('synonym'))):
                properties.append(self._extension(flow_id, 'ECS2 flow synonym', synonym, index, context=['flow']))
            if master.get_value('unitContextId'):
                properties.append(self._extension(flow_id, 'ECS2 flow unit context id', master.get_value('unitContextId'), context=['flow']))
            self._text_and_image_properties(flow_id, master.get_value('productInformation'), 'flow product information', properties, ['flow'])
            for index, text in enumerate(self._texts(master.get_value('productInformation'))):
                properties.append(self._extension(flow_id, 'ECS2 flow product information', text, index, context=['flow']))

        if not master and exchange.get_value('casNumber'):
            properties.append(self._standard(
                flow_id,
                '55e46169-4f58-4204-a574-20703fdc02c4',
                exchange.get_value('casNumber'),
            ))

        self.flows[flow_id] = Flowable(
            id=flow_id,
            name=core_name,
            properties=properties or None,
            comments=(self._comments(master.get_value('comment'), 'comment') or None) if master else None,
        )
        return flow_id


    def _intermediate_exchange(self, owner, exchange):
        properties = []
        production_volume = exchange.get_value('productionVolumeAmount')
        if production_volume is not None:
            production_properties = []
            quantity = self._quantity(
                owner,
                exchange,
                production_properties,
                label='production volume',
                amount_field='productionVolumeAmount',
                uncertainty_field='productionVolumeUncertainty',
            )
            production_entry = self._standard(
                owner,
                'b3b96e47-db1f-496c-b73d-55b91716a5e7',
                quantity,
                index='production-volume',
                comments=self._comments(exchange.get_value('productionVolumeComment'), 'productionVolumeComment') or None,
            )
            production_entry.value = self._parameterize_entry(
                production_entry.id,
                exchange,
                production_entry.value,
                'property',
                variable_field='productionVolumeVariableName',
                formula_field='productionVolumeMathematicalRelation',
                calculated_field=None,
                metadata=production_properties,
            )
            production_entry.sourceEntries = self._source_entries(self._source_ids(
                exchange,
                field='productionVolumeSourceId',
                year_field='productionVolumeSourceYear',
                author_field='productionVolumeSourceFirstAuthor',
                pages_field=None,
                title='ecoinvent production volume source',
            ))
            properties.append(production_entry)
            properties.extend(production_properties)

        for field in (
            'intermediateExchangeContextId',
            'activityLinkContextId',
            'activityLinkIdOverwrittenByChild',
            'productionVolumeSourceIdOverwrittenByChild',
            'productionVolumeSourceContextId',
        ):
            value = exchange.get_value(field)
            if self._present(value):
                properties.append(self._extension(owner, f'ECS2 {field}', value, context=['exchange']))
        return properties


    def _elementary_context(self, owner, exchange):
        compartment = exchange.compartment
        major = self._text(compartment.get_value('compartment'))
        sub = self._text(compartment.get_value('subcompartment'))
        sub_id = compartment.get_value('subcompartmentId')
        context = [self._standard(owner, '35478f20-e60e-4aad-82a9-1fcf0f4aea98', major)]

        if major == 'air':
            air = {
                'non-urban air or from high stacks': ('high stacks', 'non-urban'),
                'urban air close to ground': ('close to ground', 'urban'),
                'low population density': (None, 'low population density'),
                'low population density, long-term': (None, 'low population density'),
                'indoor': (None, 'indoor'),
                'lower stratosphere + upper troposphere': ('lower stratosphere + upper troposphere', None),
            }.get(sub, (None, None))
            if air[0]:
                context.append(self._standard(owner, 'f84fa310-200d-4359-bc12-7b99c4659ec6', air[0]))
            if air[1]:
                context.append(self._standard(owner, '9398d975-d406-4276-9755-8c01804a9d61', air[1]))
        elif major == 'soil':
            context.append(self._standard(owner, '67bba357-b663-452c-874e-4f0c063a3647', sub))
        elif major == 'water':
            context.append(self._standard(owner, '8868d6d3-6776-443b-90eb-c9ad9119348b', sub))
        elif major == 'natural resource':
            context.append(self._standard(owner, '5027f4e3-6af1-47c9-b151-12088a5200b0', sub))

        if sub_id:
            context.append(self._standard(
                owner,
                ECOINVENT_CONTEXT_PROPERTY,
                self._category(
                    self._category_registry('Compartments'),
                    f'{major}, {sub}' if major and sub else major or sub or sub_id,
                    entry_id=sub_id,
                ),
            ))

        properties = [self._standard(
            owner,
            '5119af08-62a1-4cb3-aa30-527cd72b5d90',
            properties=context,
        )]

        context_id = compartment.get_value('subcompartmentContextId')
        if context_id:
            properties.append(self._extension(owner, 'ECS2 subcompartment context id', context_id, context=['exchange']))
        elementary_context = exchange.get_value('elementaryExchangeContextId')
        if elementary_context:
            properties.append(self._extension(owner, 'ECS2 elementary exchange context id', elementary_context, context=['exchange']))
        return properties


    def _properties(
        self,
        owner,
        source_properties,
        flow_name=None,
        standard_only=None,
        metadata_owner=None,
        metadata_target=None,
    ):
        properties = []
        for index, source_property in enumerate(source_properties):
            source_id = source_property.get_value('propertyId')
            master = self.master['property'].get(source_id)
            name = (
                self._text(source_property.get_value('name'))
                or (self._text(master.get_value('name')) if master else None)
                or f'ecoinvent property {source_id}'
            )
            property_id, extra = self._standard_property_spec(source_property, master, name, flow_name)
            if standard_only is True and not property_id:
                continue
            if standard_only is False and property_id:
                continue

            quantity_properties = []
            quantity = self._quantity(
                metadata_owner or owner,
                source_property,
                quantity_properties,
                label=f'{name}:{index}',
            )
            comments = self._comments(source_property.get_value('comment'), 'comment') or None

            if property_id:
                entry = self._standard(
                    owner,
                    property_id,
                    quantity,
                    index=index,
                    comments=comments,
                    **extra,
                )
            else:
                entry = self._extension_quantity(
                    owner,
                    name,
                    quantity,
                    index=index,
                    property_id=self._id(source_id) if source_id else None,
                    comments=comments,
                    context=['exchange'],
                )

            entry.value = self._parameterize_entry(
                entry.id,
                source_property,
                entry.value,
                'property',
                metadata=quantity_properties,
            )
            entry.sourceEntries = self._source_entries(self._source_ids(source_property, pages_field=None))
            properties.append(entry)

            if metadata_target is not None:
                metadata_target.extend(quantity_properties)
            else:
                properties.extend(quantity_properties)

            if property_id and source_id != property_id:
                properties.append(self._ecoinvent_identity(
                    owner,
                    source_id,
                    'Properties',
                    index,
                    label=name,
                ))

        return properties


    def _standard_property_spec(self, source_property, master, name, flow_name):
        source_id = source_property.get_value('propertyId')
        property_id = ECS2_STANDARD_PROPERTIES.get(source_id)
        extra = {}
        normalized = name.lower().strip()

        if not property_id and 'density' in normalized:
            property_id = '2aa79563-670b-448a-9edf-28f4954dfc74'
        if property_id == '2aa79563-670b-448a-9edf-28f4954dfc74':
            extra = {
                'densityBasis': next(
                    (basis for basis in ('apparent', 'basic', 'bulk', 'dry', 'loose', 'gas') if basis in normalized),
                    'unspecified',
                ),
                'unitTransformation': {'from': {'length': 3}, 'to': {'mass': 1}},
            }

        if not property_id and (
            'concentration,' in normalized
            or 'mass concentration.' in normalized
            or normalized.startswith('concentration of ')
        ):
            property_id = '4fdbc2e4-439f-4f9f-9efe-3494f8693658'
        if source_id == '3cfb9179-6e58-4cf6-b0fb-3a853eaea89e':
            property_id = '4fdbc2e4-439f-4f9f-9efe-3494f8693658'
        if property_id == '4fdbc2e4-439f-4f9f-9efe-3494f8693658':
            substance = self._substance(name) or flow_name
            if not substance:
                return None, {}
            extra = {'substance': substance}
            basis = self._content_basis(source_property, master)
            if basis:
                extra['fractionContext'] = basis

        if not property_id and normalized.endswith(' content') and normalized != 'energy content':
            property_id = '69bbe11a-4501-41ba-b3bf-2271e2ad155f'
        if property_id == '69bbe11a-4501-41ba-b3bf-2271e2ad155f':
            substance = normalized[:-8].strip()
            if not substance:
                return None, {}
            extra = {'substance': substance}
            basis = self._content_basis(source_property, master)
            if basis:
                extra['contentBasis'] = basis

        if not property_id and ('heating value' in normalized or 'calorific value' in normalized):
            property_id = '5ac08789-7f70-439a-b60e-18c0d612d4ac'
        if property_id == '5ac08789-7f70-439a-b60e-18c0d612d4ac':
            energy = self.source.activityDescription.activity.get_value('energyValues')
            comment = ' '.join(self._texts(master.get_value('comment'))).lower() if master else ''
            measure = ENERGY.get(energy)
            if 'gross' in normalized or 'gross calorific' in comment:
                measure = 'gross calorific value'
            elif 'net' in normalized or 'lower heating' in normalized:
                measure = 'net calorific value'
            if measure not in ('net calorific value', 'gross calorific value'):
                measure = 'unspecified'
            extra = {
                'energyMeasure': measure,
                'unitTransformation': {
                    'from': {'mass': 1},
                    'to': {'length': 2, 'mass': 1, 'time': -2},
                },
            }

        if not property_id and 'fuel use' in normalized:
            property_id = 'f765f62d-81e0-4072-8c5f-e5ee771cb63d'

        if not property_id and normalized in ('price', 'market price'):
            property_id = '2c74cc35-dcef-4f9e-bda0-89d275526454'

        if not property_id and normalized in ('molecular weight', 'molar mass'):
            property_id = '1eabd6d5-adc3-4e72-8430-a9679630abf8'

        return property_id, extra


    def _property_metadata(self, owner, source_properties):
        properties = []
        for index, source_property in enumerate(source_properties):
            source_id = source_property.get_value('propertyId')
            master = self.master['property'].get(source_id)
            name = (
                self._text(source_property.get_value('name'))
                or (self._text(master.get_value('name')) if master else None)
                or f'ecoinvent property {source_id}'
            )

            defining = source_property.get_value('isDefiningValue')
            if defining is not None:
                properties.append(self._extension(
                    owner,
                    f'ECS2 property {name} isDefiningValue',
                    defining,
                    index=index,
                    context=['exchange'],
                ))

            for field in ('propertyContextId', 'unitContextId'):
                value = source_property.get_value(field)
                if self._present(value):
                    properties.append(self._extension(
                        owner,
                        f'ECS2 property {field}',
                        value,
                        index,
                        context=['exchange'],
                    ))

            if not source_property.get_value('variableName') and not source_property.get_value('mathematicalRelation'):
                calculated = source_property.get_value('isCalculatedAmount')
                if calculated:
                    properties.append(self._extension(
                        owner,
                        'ECS2 property isCalculatedAmount',
                        calculated,
                        index,
                        context=['exchange'],
                    ))

            properties.extend(self._source_reference_metadata(owner, source_property, index, prefix='property'))

        return properties


    def _substance(self, name):
        normalized = name.strip()
        if ',' in normalized:
            return normalized.split(',', 1)[1].strip()
        match = re.match(r'(?:mass )?concentration(?: of|\.) (.+)', normalized, re.I)
        return match.group(1).strip() if match else None

    def _content_basis(self, source_property, master):
        comment = ' '.join(self._texts(source_property.get_value('comment')))
        if master:
            comment += ' ' + ' '.join(self._texts(master.get_value('comment')))
        normalized = comment.lower()
        if 'dry matter' in normalized:
            return 'dry-mass fraction'
        if 'fresh matter' in normalized or 'wet matter' in normalized:
            return 'wet-mass fraction'
        unit = self._text(source_property.get_value('unitName'), '').lower()
        if unit in ('dimensionless', 'kg/kg'):
            return 'mass fraction'
        return None


    def _transfer_coefficients(self, owner, exchange):
        properties = []
        dimensionless, _ = self._unit(name='dimensionless')
        for index, coefficient in enumerate(self._many(exchange, 'transferCoefficient')):
            coefficient_owner = self._generated_id(owner, 'transfer-coefficient', index)
            nested = [self._extension(
                coefficient_owner,
                'ECS2 transfer coefficient exchange id',
                coefficient.get_value('exchangeId'),
            )]
            quantity_properties = []
            uncertainty = self._uncertainty(
                coefficient_owner,
                coefficient.get_value('uncertainty'),
                quantity_properties,
                f'transfer coefficient {index}',
            )
            quantity = self.quantities.to_entry(
                self.quantities.scalar(
                    Decimal(str(coefficient.get_value('amount'))),
                    dimensionless.id,
                    uncertainty,
                ),
                dimensionless.id,
            )
            value_entry = self._extension_quantity(
                coefficient_owner,
                'ECS2 transfer coefficient value',
                quantity,
            )
            value_entry.value = self._parameterize_entry(
                value_entry.id,
                coefficient,
                value_entry.value,
                'property',
                variable_field=None,
                metadata=quantity_properties,
            )
            nested.append(value_entry)
            nested.extend(quantity_properties)
            if not coefficient.get_value('mathematicalRelation') and coefficient.get_value('isCalculatedAmount'):
                nested.append(self._extension(
                    coefficient_owner,
                    'ECS2 transfer coefficient isCalculatedAmount',
                    True,
                ))
            nested.extend(self._source_reference_metadata(coefficient_owner, coefficient, prefix='transfer coefficient'))
            properties.append(self._extension_composite(
                owner,
                'ECS2 transfer coefficient',
                nested,
                index=index,
                comments=self._comments(coefficient.get_value('comment'), 'comment') or None,
                source_ids=self._source_ids(coefficient, pages_field=None),
            ))
        return properties


    def _source_reference_metadata(self, owner, obj, index=0, prefix=None):
        properties = []
        name = f'ECS2 {prefix + " " if prefix else ""}'
        for field in ('sourceIdOverwrittenByChild', 'sourceContextId'):
            value = obj.get_value(field)
            if self._present(value):
                properties.append(self._extension(owner, f'{name}{field}', value, index))
        return properties


    def _exchange_metadata(self, owner, exchange, flow_type):
        properties = []
        for field in (
            'specificAllocationPropertyIdOverwrittenByChild',
            'specificAllocationPropertyContextId',
            'unitContextId',
        ):
            value = exchange.get_value(field)
            if self._present(value):
                properties.append(self._extension(
                    owner,
                    f'ECS2 exchange {field}',
                    value,
                    context=['exchange'],
                ))

        formula = exchange.get_value('formula')
        if (
            self._present(formula)
            and not self._corine_code(formula)
            and flow_type != 'elementary'
        ):
            properties.append(self._extension(
                owner,
                'ECS2 exchange formula',
                formula,
                context=['exchange'],
            ))

        if not exchange.get_value('variableName') and not exchange.get_value('mathematicalRelation'):
            calculated = exchange.get_value('isCalculatedAmount')
            if calculated:
                properties.append(self._extension(
                    owner,
                    'ECS2 exchange isCalculatedAmount',
                    calculated,
                    context=['exchange'],
                ))

        allocation = exchange.get_value('specificAllocationPropertyId')
        if allocation:
            properties.append(self._source_property(
                owner,
                'ecoinvent specific allocation property id',
                allocation,
                'Properties',
                context=['exchange'],
            ))
        for index, synonym in enumerate(self._texts(exchange.get_value('synonym'))):
            properties.append(self._extension(
                owner,
                'ECS2 exchange synonym',
                synonym,
                index,
                context=['exchange'],
            ))
        for index, tag in enumerate(self._many_value(exchange, 'tag')):
            properties.append(self._extension(
                owner,
                'ECS2 exchange tag',
                tag,
                index,
                context=['exchange'],
            ))
        properties.extend(self._source_reference_metadata(owner, exchange, prefix='exchange'))
        return properties


    def _preserve_impact(self, impact, index, process_properties):
        owner = self._id(impact.get_value('impactIndicatorId'))
        unit, factor = self._unit(name=self._text(impact.get_value('unitName')))
        quantity = self.quantities.to_entry(
            self.quantities.scalar(Decimal(str(impact.get_value('amount'))) * factor, unit.id),
            unit.id,
        )
        parts = [
            self._source_property(owner, 'ecoinvent impact indicator id', impact.get_value('impactIndicatorId'), 'ImpactIndicators'),
            self._source_property(owner, 'ecoinvent impact method id', impact.get_value('impactMethodId'), 'ImpactMethods'),
            self._source_property(owner, 'ecoinvent impact category id', impact.get_value('impactCategoryId'), 'ImpactCategories'),
            self._extension_quantity(owner, 'ECS2 impact amount', quantity),
        ]
        for field in ('impactMethodName', 'impactCategoryName', 'name'):
            value = self._text(impact.get_value(field))
            if value:
                parts.append(self._extension(owner, f'ECS2 impact {field}', value))
        for field in ('impactIndicatorContextId', 'impactMethodContextId', 'impactCategoryContextId'):
            value = impact.get_value(field)
            if value:
                parts.append(self._extension(owner, f'ECS2 impact {field}', value))
        property_id = self._generated_id('property', 'ECS2 impact indicator')
        self._property_registry(property_id, 'ECS2 impact indicator', 'composite')
        process_properties.append(ExtensionCompositeProperty(
            id=self._generated_id(owner, property_id, index),
            property=property_id,
            properties=parts,
        ))

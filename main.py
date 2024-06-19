import os
from copy import deepcopy
from pathlib import Path

import aas_core_meta
from aas_core_meta.v3 import *
from pyaas2puml.pyaas2puml import AasPumlGenerator
from pyaas2puml.utils import classname, write_file, snake_to_camel

PUML_CLS_DIAGRAMS = (
    (
        Asset_administration_shell, Asset_information, Asset_kind, Specific_asset_ID, Submodel, Qualifier,
        Submodel_element,
        Property),
    (Environment, Asset_administration_shell, Submodel, Concept_description),
    (Administrative_information,),
    (Has_data_specification,),
    (Has_extensions, Referable, Extension,),
    (Has_kind, Modelling_kind,),
    (Has_semantics,),
    (Referable, Identifiable, Administrative_information,),
    (Qualifiable, Qualifier,),
    (Qualifier, Qualifier_kind,),
    (Referable,),
    (Asset_administration_shell, Asset_information, Submodel,),
    (Asset_information, Specific_asset_ID, Resource, Asset_kind,),
    (Submodel, Submodel_element),
    (Submodel_element,),
    (Submodel_element, Relationship_element, Annotated_relationship_element, Data_element, Property,
     Multi_language_property, Range, Blob, File, Reference_element, Capability, Submodel_element_list,
     Submodel_element_collection, Entity, Event_element, Basic_event_element, Operation, Operation_variable,),
    (Relationship_element, Annotated_relationship_element,),
    (Basic_event_element, Direction, State_of_event),
    (Event_payload,),
    (Blob,),
    (Capability,),
    (Data_element, Property, Multi_language_property, Range, Blob, File, Reference_element),
    (Entity, Entity_type,),
    (Event_element,),
    (File,),
    (Multi_language_property,),
    (Operation, Operation_variable),
    (Property,),
    (Range,),
    (Reference_element,),
    (Submodel_element_collection, Submodel_element),
    (Submodel_element_list, Submodel_element),
    (Concept_description,),
    (Environment, Asset_administration_shell, Submodel, Concept_description),
    (Reference, Key, Reference_types),
    (Key, Key_types),
    # (Key, Key_types, Fragment_keys, Generic_fragment_keys, AAS_referables, AAS_referable_non_identifiables, AAS_submodel_elements, AAS_identifiables, Globally_identifiables, Generic_globally_identifiables),
    (Key_types,),
    (AAS_submodel_elements,),
    # image53
    (Data_type_def_XSD,),
    # image56
    # image57
    # image59
    (Asset_information, Specific_asset_ID, Entity, Entity_type, Asset_administration_shell, Submodel, Submodel_element,
     Relationship_element),
    # image89
    # image90
)

# Transform PUML_CLS_DIAGRAMS into a list of class names
PUML_CLS_DIAGRAMS = [[snake_to_camel(classname(cls)) for cls in classes] for classes in PUML_CLS_DIAGRAMS]

DOMAIN_PATH = os.path.dirname(aas_core_meta.__file__)
DOMAIN_MODULE = "aas_core_meta"
DOMAIN_SUBMODULES = ["v3"]

if __name__ == '__main__':
    output_path = Path('output')
    output_path.mkdir(exist_ok=True)
    basic_generator = AasPumlGenerator(DOMAIN_PATH, DOMAIN_MODULE, DOMAIN_SUBMODULES)
    all_domain_items = basic_generator.domain_items
    all_relations = basic_generator.domain_relations

    print("Creating PlantUML files for each set of classes defined in PUML_CLS_DIAGRAMS")
    for i, classes_in_diagram in enumerate(PUML_CLS_DIAGRAMS, 12):
        generator = AasPumlGenerator(DOMAIN_PATH, DOMAIN_MODULE, DOMAIN_SUBMODULES,
                                     deepcopy(all_domain_items), deepcopy(all_relations))
        cls_diagr_file = output_path / f'{i}_{classes_in_diagram[0].split(".")[-1]}.puml'
        print(f"Creating PlantUML file for classes: {classes_in_diagram}")
        puml_content: str = generator.generate_puml(classes_in_diagram)
        write_file(cls_diagr_file, puml_content)

    aas_classes_files = output_path / 'classes'
    aas_classes_files.mkdir(exist_ok=True)

    print("Creating PlantUML file for all classes in the domain module")
    aas_all_classes_file = aas_classes_files / f'{DOMAIN_MODULE}_all.puml'
    generator = AasPumlGenerator(DOMAIN_PATH, DOMAIN_MODULE, DOMAIN_SUBMODULES,
                                 deepcopy(all_domain_items), deepcopy(all_relations))
    write_file(aas_all_classes_file, generator.generate_puml())

    print("Creating PlantUML files for each class in the domain module")
    for item in all_domain_items:
        print("Creating PlantUML file for class:", item)
        cls_diagr_file = aas_classes_files / f'{item.split(".")[-1]}.puml'
        generator = AasPumlGenerator(DOMAIN_PATH, DOMAIN_MODULE, DOMAIN_SUBMODULES,
                                     deepcopy(all_domain_items), deepcopy(all_relations))
        puml_content: str = generator.generate_puml(domain_items_to_keep=[item], to_include_members_from_parents=True)
        write_file(cls_diagr_file, puml_content)

import re
from ast import parse
from inspect import getsource
from pathlib import Path
from typing import Iterable, Union, Optional, Dict, List, Tuple

from py2puml.domain.umlclass import UmlClass
from py2puml.domain.umlenum import UmlEnum
from py2puml.domain.umlitem import UmlItem
from py2puml.domain.umlrelation import UmlRelation, RelType
from py2puml.export.puml import to_puml_content
from py2puml.inspection.inspectpackage import inspect_package
from py2puml.utils import filter_items_and_relations

DOMAIN_PATH = DOMAIN_MODULE = 'aas_core_meta'

PUML_CLS_DIAGRAMS = (
    ('Environment', 'Asset_administration_shell', 'Submodel', 'Concept_description'),
    ('Administrative_information',),
    ('Has_data_specification',),
    ('Has_extensions', 'Extension', 'Referable',),
    ('Has_kind', 'Modelling_kind',),
    ('Has_semantics',),
    ('Referable', 'Identifiable', 'Administrative_information',),
)

REGEX_TO_REPLACE = {
    # Remove the following strings from the PlantUML file
    r"\{static\}": "",
    ":  \n": "\n",
    # Replace the following strings from the PlantUML file
    r"\*\|--": "<\.\.", # Replace compositions with dependencies
    r"Optional\[List\[(.+?)\]\]": "\\1[0..*]",  # Optional[List[...]] -> ...[0..*]
    r"List\[(.+?)\]": "\\1[1..*]",  # List[...] -> ...[1..*]
    r"Optional\[(.+?)\]": "\\1[0..1]",  # Optional[...] -> ...[0..1]
    r"abstract class (.+?) \{":
        r"abstract class \1 <<abstract>> {",  # abstract class ... { -> abstract class ... <<abstract>> {
    r"enum (.+?) \{": r"enum \1 <<enumeration>> {",  # enum ... { -> enum ... <<enumeration>> {
}


def create_puml(output_file: Path, classes: Optional[Iterable[str]] = None,
                create_original_file: bool = False, to_include_members_from_parents: bool = False):
    """Create a PlantUML file from the classes in the domain module.
    :param output_file: the output file
    :param classes: the classes to include in the PlantUML file. If None, all classes are included.
    """
    # create the PlantUML file and write it to the output file
    puml_content: str = ''.join(aas_core_meta_py2puml(DOMAIN_PATH, DOMAIN_MODULE, domain_items_to_keep=classes,
                                                      to_include_members_from_parents=to_include_members_from_parents))
    if create_original_file:
        write_file(output_file.with_name('original_' + output_file.name), puml_content)

    # Apply IDTA specific changes to the PlantUML content and write it to the output file
    idta_puml_content = apply_changes(puml_content)
    write_file(output_file, idta_puml_content)


def read_file(file: Union[str, Path]) -> str:
    with open(file, 'r', encoding='utf8') as f:
        return f.read()


def write_file(file: Union[str, Path], content: str):
    with open(file, 'w', encoding='utf8') as f:
        f.write(content)


def aas_core_meta_py2puml(domain_path: str, domain_module: str, domain_items_to_keep: Optional[List[str]] = None,
                          to_include_members_from_parents: bool = False, sort_members=True) -> Iterable[str]:
    domain_items_by_fqn: Dict[str, UmlItem] = {}
    domain_relations: List[UmlRelation] = []
    inspect_package(domain_path, domain_module, domain_items_by_fqn, domain_relations)

    if to_include_members_from_parents:
        include_members_from_parents(domain_items_by_fqn, domain_relations)

    # Filter only the classes in the list
    if domain_items_to_keep:
        handle_classes_and_relations_filtering(domain_items_by_fqn, domain_relations, domain_items_to_keep)
        domain_items_by_fqn = sort_classes(domain_items_by_fqn, domain_items_to_keep)

    set_aas_core_meta_abstract_classes_as_abstract(domain_items_by_fqn)
    use_values_in_enumerations_as_names(domain_items_by_fqn)
    return to_puml_content(domain_module, domain_items_by_fqn.values(), domain_relations, sort_members)


def include_members_from_parents(domain_items_by_fqn: Dict[str, UmlItem], domain_relations: List[UmlRelation]):
    """Include the members from the parent classes in the child classes."""
    inheritance_rels = [rel for rel in domain_relations if rel.type == RelType.INHERITANCE]
    while len(inheritance_rels) > 0:
        _include_members_from_parents(domain_items_by_fqn, inheritance_rels, inheritance_rels[0])


def _include_members_from_parents(domain_items_by_fqn: Dict[str, UmlItem], inheritance_relations: List[UmlRelation], inheritance_rel):
    parent = domain_items_by_fqn.get(inheritance_rel.source_fqn)
    child = domain_items_by_fqn.get(inheritance_rel.target_fqn)

    parent_inheritance_rels = [rel for rel in inheritance_relations if rel.target_fqn == parent.fqn]
    for rel in parent_inheritance_rels:
        _include_members_from_parents(domain_items_by_fqn, inheritance_relations, rel)

    for attr in parent.attributes:
        if attr in child.attributes:
            continue
        child.attributes.append(attr)
    inheritance_relations.remove(inheritance_rel)



def handle_classes_and_relations_filtering(domain_items: Dict[str, UmlItem], domain_relations: List[UmlRelation],
                                           domain_items_to_keep: List[str]):
    all_inheritances: List[Tuple[str, str]] = get_inheritances(domain_relations)
    filter_items_and_relations(domain_items, domain_relations, domain_items_to_keep)
    remain_inheritances: List[Tuple[str, str]] = get_inheritances(domain_relations)
    removed_inheritances = [inheritance for inheritance in all_inheritances if inheritance not in remain_inheritances]
    add_filtered_out_parent_classes_as_generics(domain_items, removed_inheritances)


def sort_classes(items: Dict[str, UmlItem], items_order: Iterable[str]):
    # Sort the classes in the order as they should appear in the PlantUML file
    return {fqn: items[fqn] for fqn in items_order if fqn in items}


def get_inheritances(domain_relations: List[UmlRelation]) -> List[Tuple[str, str]]:
    return [(rel.source_fqn, rel.target_fqn) for rel in domain_relations if rel.type == RelType.INHERITANCE]


def add_filtered_out_parent_classes_as_generics(domain_items: Dict[str, UmlItem],
                                                removed_inheritances: List[Tuple[str, str]]):
    """Add classes that are filtered out from the PlantUML file and will be not shown in the diagram,
    as generics to the classes that inherit from them.
    """
    for parent, child in removed_inheritances:
        if child in domain_items:
            if domain_items[child].generics:
                domain_items[child].generics = rf"{domain_items[child].generics}\n{parent}"
            else:
                domain_items[child].generics = parent


def set_aas_core_meta_abstract_classes_as_abstract(domain_items: Dict[str, UmlItem]):
    """
    Set the is_abstract attribute to True for abstract classes from aas-core-meta

    This is done, because standard isabstract() function does not work for abstract classes in aas-core-meta,
    as they are not defined as abstract classes in the source code, but marked with a decorator 'abstract'
    """
    for item in domain_items.values():
        if isinstance(item, UmlClass) and has_decorator(item.class_type, 'abstract'):
            item.is_abstract = True


def use_values_in_enumerations_as_names(domain_items: Dict[str, UmlItem]):
    for item in domain_items.values():
        if isinstance(item, UmlEnum):
            for enum_item in item.members:
                enum_item.name = enum_item.value
                enum_item.value = ""


def has_decorator(class_type, decorator_name):
    if class_type is None:
        return
    # Get the source code of the class
    source = getsource(class_type)
    # Parse the source code into an AST
    parsed_ast = parse(source)
    if hasattr(parsed_ast.body[0], 'decorator_list') and parsed_ast.body[0].decorator_list:
        for decorator in parsed_ast.body[0].decorator_list:
            if hasattr(decorator, 'id') and decorator.id == decorator_name:
                return True
    return False


def apply_changes(text: str) -> str:
    text = apply_replacements(REGEX_TO_REPLACE, text)
    text = remove_duplicate_lines(text)
    text = snake_to_camel(text)
    return text


def apply_replacements(replacements: Dict[str, str], text: str):
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text)
    return text


def remove_duplicate_lines(text: str = None, exceptions=("{", "}", "")):
    lines = text.splitlines()
    lines_seen = set()  # Create a set to store seen lines
    unique_lines = []

    # Read input file
    for line in lines:
        if line not in lines_seen or line in exceptions:
            unique_lines.append(line)
            lines_seen.add(line)
    return '\n'.join(unique_lines)


def snake_to_camel(snake_str):
    camel_str = re.sub(r'([a-z])_([a-z])', lambda match: match.group(1) + match.group(2).upper(), snake_str)
    camel_str = re.sub(r'([a-z])_([A-Z])([A-Z]+)',
                       lambda match: match.group(1) + match.group(2).upper() + match.group(3).lower(), camel_str)
    camel_str = re.sub(r'([A-Z]+)_([a-z])', lambda match: match.group(1).lower() + match.group(2).upper(), camel_str)
    camel_str = re.sub(r'([^A-Z])ID([^A-Z])', lambda match: match.group(1) + "id" + match.group(2).upper(), camel_str)
    return camel_str


if __name__ == '__main__':
    # Create the PlantUML for all classes in the domain module
    aas_core_all_file = Path('output/IDTA_aas_core_meta_all.puml')
    create_puml(aas_core_all_file)

    for i, classes in enumerate(PUML_CLS_DIAGRAMS):
        # Create the PlantUML for each set of classes defined in PUML_CLS_DIAGRAMS
        classes = [f'aas_core_meta.v3.{cls}' for cls in classes]
        cls_diagr_file = Path(f'output/IDTA_aas_core_meta_{i}.puml')
        create_puml(cls_diagr_file, classes)

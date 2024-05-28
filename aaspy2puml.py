import re
from ast import parse
from inspect import getsource
from pathlib import Path
from typing import Iterable, Union, Optional, Dict, List

from py2puml.domain.umlclass import UmlClass
from py2puml.domain.umlitem import UmlItem
from py2puml.domain.umlrelation import UmlRelation
from py2puml.export.puml import to_puml_content
from py2puml.inspection.inspectpackage import inspect_package
from py2puml.utils import filter_items_and_relations

DOMAIN_PATH = DOMAIN_MODULE = 'aas_core_meta'
STRS_TO_REMOVE = ["{static}", "aas_core_meta.v3."]

REGEX_TO_REPLACE = {
    # Remove the following strings from the PlantUML file
    r"\{static\}": "",
    r"aas_core_meta\.v3\.": "",
    # Replace the following strings from the PlantUML file
    r"Optional\[List\[(.+?)\]\]": "\\1[0..*]", # Optional[List[...]] -> ...[0..*]
    r"List\[(.+?)\]": "\\1[1..*]", # List[...] -> ...[1..*]
    r"Optional\[(.+?)\]": "\\1[0..1]", # Optional[...] -> ...[0..1]
    r"abstract class (.+?) \{": r"abstract class \1 <<abstract>> {", # abstract class ... { -> abstract class ... <<abstract>> {
    r"enum (.+?) \{": r"enum \1 <<enumeration>> {", # enum ... { -> enum ... <<enumeration>> {
}

PUML_CLS_DIAGRAMS = (
    ('Environment', 'Asset_administration_shell', 'Submodel', 'Concept_description'),
    ('Administrative_information',),
    ('Has_data_specification',),
    ('Has_extensions', 'Extension', 'Referable',),
    ('Has_kind', 'Modelling_kind',),
    ('Has_semantics',),
    ('Referable', 'Identifiable', 'Administrative_information',),
)


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


def set_aas_core_meta_abstract_classes_as_abstract(domain_items: Dict[str, UmlItem]):
    """
    Set the is_abstract attribute to True for abstract classes from aas-core-meta

    This is done, because standard isabstract() function does not work for abstract classes in aas-core-meta,
    as they are not defined as abstract classes in the source code, but marked with a decorator 'abstract'
    """
    for item in domain_items.values():
        if isinstance(item, UmlClass) and has_decorator(item.class_type, 'abstract'):
            item.is_abstract = True


def aas_core_meta_py2puml(domain_path: str, domain_module: str, only_domain_items: Optional[List[str]] = None) -> \
Iterable[str]:
    domain_items_by_fqn: Dict[str, UmlItem] = {}
    domain_relations: List[UmlRelation] = []
    inspect_package(domain_path, domain_module, domain_items_by_fqn, domain_relations)

    # Filter only the classes in the list
    if only_domain_items:
        filter_items_and_relations(domain_items_by_fqn, domain_relations, only_domain_items)

    set_aas_core_meta_abstract_classes_as_abstract(domain_items_by_fqn)

    return to_puml_content(domain_module, domain_items_by_fqn.values(), domain_relations)


def create_puml(output_file: Path, classes: Optional[Iterable[str]] = None):
    """Create a PlantUML file from the classes in the domain module.
    :param output_file: the output file
    :param classes: the classes to include in the PlantUML file. If None, all classes are included.
    """
    # writes the PlantUML content in a file
    with open(output_file, 'w', encoding='utf8') as puml_file:
        puml_file.writelines(aas_core_meta_py2puml(DOMAIN_PATH, DOMAIN_MODULE, only_domain_items=classes))
    apply_changes(output_file, output_file.with_name(output_file.stem + '_IDTA.puml'))


def apply_changes(input: Path, output: Path = None):
    text = read_file(input)
    text = _apply_changes(text)
    write_file(output if output else input, text)


def read_file(file: Union[str, Path]) -> str:
    with open(file, 'r') as f:
        return f.read()


def write_file(file: Union[str, Path], content: str):
    with open(file, 'w') as f:
        f.write(content)


def _apply_changes(text: str) -> str:
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
    return camel_str


if __name__ == '__main__':
    aas_core_all_file = Path('aas_core_meta_all.puml')

    create_puml(aas_core_all_file)

    # List of classes to include
    for i, classes in enumerate(PUML_CLS_DIAGRAMS):
        classes = [f'aas_core_meta.v3.{cls}' for cls in classes]
        cls_diagr_file = Path(f'aas_core_meta_{i}.puml')
        create_puml(cls_diagr_file, classes)

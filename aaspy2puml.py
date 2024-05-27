import re
from pathlib import Path
from typing import Iterable, Union, Optional, Dict

from py2puml.py2puml import py2puml

DOMAIN_PATH = DOMAIN_MODULE = 'aas_core_meta'
STRS_TO_REMOVE = ["{static}", "aas_core_meta.v3."]

REGEX_TO_REPLACE = {
    # Remove the following strings from the PlantUML file
    r"\{static\}": "",
    r"aas_core_meta\.v3\.": "",
    # Replace the following strings from the PlantUML file
    r"Optional\[List\[(.+?)\]\]": "\\1[0..*]",
    r"List\[(.+?)\]": "\\1[1..*]",
    r"Optional\[(.+?)\]": "\\1[0..1]",
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


def apply_replacements(replacements: Dict[str, str], text: str):
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text)
    return text


def apply_replacements_from_file(replacements: Dict[str, str], input: Path, output: Path = None):
    with open(input, 'r') as f:
        text = f.read()
    text = apply_replacements(replacements, text)

    if output is None:
        output = input
    with open(output, 'w') as f:
        f.write(text)


def remove_duplicate_lines_from_file(input_file: Path, output_file: Path = None, exceptions=("{\n", "}\n", "\n")):
    lines_seen = set()  # Create a set to store seen lines
    unique_lines = []

    # Read input file
    with open(input_file, 'r') as file:
        for line in file:
            if line not in lines_seen or line in exceptions:
                unique_lines.append(line)
                lines_seen.add(line)

    if output_file is None:
        output_file = input_file

    # Write output file
    with open(output_file, 'w') as file:
        file.writelines(unique_lines)


def create_puml(output_file: Path, classes: Optional[Iterable[str]] = None):
    """Create a PlantUML file from the classes in the domain module.
    :param output_file: the output file
    :param classes: the classes to include in the PlantUML file. If None, all classes are included.
    """
    # writes the PlantUML content in a file
    with open(output_file, 'w', encoding='utf8') as puml_file:
        puml_file.writelines(py2puml(DOMAIN_PATH, DOMAIN_MODULE, only_domain_items=classes))

    remove_duplicate_lines_from_file(output_file)

    apply_replacements_from_file(REGEX_TO_REPLACE, output_file, output_file.with_name(output_file.stem + '_card.puml'))


if __name__ == '__main__':
    aas_core_all_file = Path('aas_core_meta_all.puml')

    create_puml(aas_core_all_file)

    # List of classes to include
    for i, classes in enumerate(PUML_CLS_DIAGRAMS):
        classes = [f'aas_core_meta.v3.{cls}' for cls in classes]
        cls_diagr_file = Path(f'aas_core_meta_{i}.puml')
        create_puml(cls_diagr_file, classes)

from copy import copy
from typing import Iterable, List

from pyaas2puml.domain.umlclass import UmlClass
from pyaas2puml.domain.umlenum import UmlEnum
from pyaas2puml.domain.umlitem import UmlItem
from pyaas2puml.domain.umlrelation import UmlRelation

PUML_FILE_START = """@startuml
skinparam classAttributeIconSize 0
hide methods

"""
PUML_FILE_END = """@enduml
"""
PUML_ITEM_START_TPL = """{item_type} {item_fqn}{generics} {{
"""
PUML_ATTR_TPL = """  {visibility}{attr_name}: {attr_type}{staticity}
"""
PUML_ITEM_END = """}
"""
PUML_RELATION_TPL = """{source_fqn} {rel_type} {target_fqn}{label}
"""

FEATURE_STATIC = ' {static}'
FEATURE_INSTANCE = ''


def to_puml_content(diagram_name: str, uml_items: List[UmlItem], uml_relations: List[UmlRelation],
                    sort_members: bool = False) -> Iterable[str]:
    yield PUML_FILE_START.format(diagram_name=diagram_name)

    # exports the domain classes and enums
    for uml_item in uml_items:
        if isinstance(uml_item, UmlEnum):
            yield from yeld_puml_enum(uml_item, sort_members)
        elif isinstance(uml_item, UmlClass):
            yield from yeld_puml_class(uml_item, sort_members)
        else:
            raise TypeError(f'cannot process uml_item of type {uml_item.__class__}')

    # exports the domain relationships between classes and enums
    for uml_relation in uml_relations:
        yield PUML_RELATION_TPL.format(
            source_fqn=uml_relation.source_fqn, rel_type=uml_relation.type.value, target_fqn=uml_relation.target_fqn,
            label=uml_relation.label
        )

    yield PUML_FILE_END


def yeld_puml_enum(uml_enum: UmlEnum, sort_members: bool = False) -> Iterable[str]:
    yield PUML_ITEM_START_TPL.format(item_type='enum', item_fqn=uml_enum.fqn,
                                     generics=f'<{uml_enum.generics}>' if uml_enum.generics else '')
    if sort_members:
        uml_enum.members.sort(key=lambda member: member.name.lower())
    for member in uml_enum.members:
        yield PUML_ATTR_TPL.format(visibility="", attr_name=member.name, attr_type=member.value,
                                   staticity=FEATURE_STATIC)
    yield PUML_ITEM_END


def yeld_puml_class(uml_class: UmlClass, sort_members: bool = False) -> Iterable[str]:
    yield PUML_ITEM_START_TPL.format(
        item_type='abstract class' if uml_class.is_abstract else 'class', item_fqn=uml_class.fqn,
        generics=f'<{uml_class.generics}>' if uml_class.generics else ''
    )
    if sort_members:
        uml_class.attributes.sort(key=lambda attr: attr.name.lower())

    remove_duplicated_attrs(uml_class)

    for uml_attr in uml_class.attributes:
        yield PUML_ATTR_TPL.format(
            visibility=uml_attr.visibility,
            attr_name=uml_attr.name,
            attr_type=uml_attr.type,
            staticity=FEATURE_STATIC if uml_attr.static else FEATURE_INSTANCE,
        )
    yield PUML_ITEM_END


def remove_duplicated_attrs(uml_class: UmlClass):
    static_attrs = [attr.name for attr in uml_class.attributes if attr.static]
    for attr in copy(uml_class.attributes):
        if not attr.static and attr.name in static_attrs:
            uml_class.attributes.remove(attr)

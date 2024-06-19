import re
from inspect import getsource
from typing import Iterable, Optional, Dict, List, Tuple

from aas_core_meta.v3 import Referable, Key_types
from pyaas2puml.domain.umlclass import UmlClass
from pyaas2puml.domain.umlenum import UmlEnum
from pyaas2puml.domain.umlitem import UmlItem
from pyaas2puml.domain.umlrelation import UmlRelation, RelType
from pyaas2puml.export.puml import to_puml_content
from pyaas2puml.inspection.inspectmodule import filter_domain_relations
from pyaas2puml.inspection.inspectpackage import inspect_package
from pyaas2puml.utils import classname, has_decorator, snake_to_camel, plural_attribute_to_singular


class AasPumlGenerator:
    REF_RELATION_SUFFIX = ":ref"

    def __init__(self, domain_path: str, domain_module: str, domain_submodules: Iterable[str] = None,
                 domain_items: Dict[str, UmlItem] = None, domain_relations: List[UmlRelation] = None):
        """ Initialize the AAS PlantUML generator.
        :param domain_path: the path to the domain module.
        :param domain_module: the name of the domain module.
        :param domain_submodules: the submodules of the domain module, which should be included in the PlantUML.
        If None, all submodules are included.
        :param domain_items: the domain items to include in the PlantUML. If given the domain module is not inspected.
        :param domain_relations: the domain relations to include in the PlantUML. If given the domain module is not
        inspected.
        """
        self.domain_path = domain_path
        self.domain_module = domain_module
        self.domain_submodules = domain_submodules
        if domain_items is None:
            self.domain_items: Dict[str, UmlItem] = {}
            self.domain_relations: List[UmlRelation] = []
            self._inspect_package()
        else:
            self.domain_items = domain_items
            self.domain_relations = domain_relations

        self.regex_to_replace = {
            # Remove the following strings from the PlantUML file
            r"\{static\}": "",
            ":  \n": "\n",
            # Replace the following strings from the PlantUML file
            fr"{snake_to_camel(domain_module)}\.": "",
            r"\+ID:": "+id:",
            r"Optional\[List\[(.+?)\]\]": "\\1[0..*]",  # Optional[List[...]] -> ...[0..*]
            r"List\[(.+?)\]": "\\1[1..*]",  # List[...] -> ...[1..*]
            r"Optional\[(.+?)\]": "\\1[0..1]",  # Optional[...] -> ...[0..1]
            r"abstract class (.+?) \{":
                r"abstract class \1 <<abstract>> {",  # abstract class ... { -> abstract class ... <<abstract>> {
            r"enum (.+?) \{": r"enum \1 <<enumeration>> {",  # enum ... { -> enum ... <<enumeration>> {
        }
        if domain_submodules:
            for submodule in domain_submodules:
                self.regex_to_replace[fr"{snake_to_camel(submodule)}\."] = ""

    def _inspect_package(self):
        inspect_package(self.domain_path, self.domain_module, self.domain_items, self.domain_relations)
        if self.domain_submodules:
            self._filter_domain_items_from_submodules()
        self._remove_duplicated_relations()
        self._add_reference_relations()
        self._replace_compositions_with_dependencies()
        self._set_aas_core_meta_abstract_classes_as_abstract()
        self._use_values_in_enumerations_as_names()
        self._rename_snake_case_to_camel_case()
        self._rename_plural_attrs_labels_to_singular()

    def _filter_domain_items_from_submodules(self):
        items_from_submodules = []
        for item in self.domain_items:
            for submodule in self.domain_submodules:
                if item.startswith(f"{self.domain_module}.{submodule}."):
                    items_from_submodules.append(item)
                    break
        items_to_remove = [item for item in self.domain_items if item not in items_from_submodules]
        for item in items_to_remove:
            del self.domain_items[item]
        filter_domain_relations(self.domain_items, self.domain_relations)

    def _remove_duplicated_relations(self):
        """Remove duplicated relations from the domain relations."""
        unique_relations = []
        for rel in self.domain_relations:
            if rel not in unique_relations:
                unique_relations.append(rel)
        self.domain_relations = unique_relations

    def _rename_snake_case_to_camel_case(self):
        renamed_domain_items = {}
        for item in self.domain_items.values():
            item.name = snake_to_camel(item.name)
            item.fqn = snake_to_camel(item.fqn) if item.fqn else item.fqn
            if isinstance(item, UmlClass):
                for attr in item.attributes:
                    attr.name = snake_to_camel(attr.name)
                    attr.name = "id" + attr.name.removeprefix("Id") if attr.name.startswith("Id") else attr.name
                    attr.type = snake_to_camel(attr.type) if attr.type else attr.type
            renamed_domain_items[item.fqn] = item
        self.domain_items = renamed_domain_items

        for rel in self.domain_relations:
            rel.source_fqn = snake_to_camel(rel.source_fqn)
            rel.target_fqn = snake_to_camel(rel.target_fqn)
            rel.label_ = snake_to_camel(rel.label_) if rel.label_ else rel.label_

    def _rename_plural_attrs_labels_to_singular(self):
        for item in self.domain_items.values():
            if isinstance(item, UmlClass):
                for attr in item.attributes:
                    attr.name = plural_attribute_to_singular(attr.name)
        for rel in self.domain_relations:
            if rel.label_ and rel.label_.endswith(self.REF_RELATION_SUFFIX):
                attr_name = plural_attribute_to_singular(rel.label_.removesuffix(self.REF_RELATION_SUFFIX))
                rel.label_ = f"{attr_name}{self.REF_RELATION_SUFFIX}"

    def _add_reference_relations(self):
        domain_classes_with_invariant_decorator = [i for i in self.domain_items.values() if
                                                   isinstance(i, UmlClass) and has_decorator(i.class_type, "invariant")]
        for item in domain_classes_with_invariant_decorator:
            # Get the source code of the class
            source = getsource(item.class_type)
            # Get list of decorators source code
            decorators = source[:source.find("\nclass ")].lstrip("@").split("\n@")
            # Make a list of invariant decorators source code
            invariants = [decorator for decorator in decorators if decorator.split("(")[0] == "invariant"]
            # In each decorator search for 'is_model_reference_to' and for its args (including list comprehensions)
            for invariant_src in invariants:
                if "is_model_reference_to" not in invariant_src:
                    continue

                # Get the args of the 'is_model_reference_to' or 'is_model_reference_to_referable' func
                if "is_model_reference_to_referable" in invariant_src:
                    is_model_ref_to_regex = r"is_model_reference_to_referable\(\s*(\S+)\s*\)"
                    is_model_ref_to_search = re.search(is_model_ref_to_regex, invariant_src)
                    ref_attr = is_model_ref_to_search.group(1)
                    target_cls = classname(Referable)
                elif "is_model_reference_to" in invariant_src:
                    is_model_ref_to_regex = r"is_model_reference_to\(\s*(\S+)\s*,\s*(\S+)?\s*\)"
                    is_model_ref_to_search = re.search(is_model_ref_to_regex, invariant_src)
                    ref_attr = is_model_ref_to_search.group(1)
                    key_type_attr = is_model_ref_to_search.group(2)
                    target_cls = classname(Key_types).removesuffix(".Key_types") + "." + key_type_attr.split(".")[-1]

                if not ref_attr.startswith("self."):
                    # Search for list comprehension
                    is_model_ref_to_regex_with_list_comprehension = rf"\(\s*{is_model_ref_to_regex}\s*for (.+?) in (\S+)\s*\)"
                    ref_attr = re.search(is_model_ref_to_regex_with_list_comprehension, invariant_src).group(4)
                # Get the class name from the args
                # Create a relation between the current class and found class argument
                self._create_ref_relation(item.fqn, ref_attr.removeprefix("self."), target_cls)

    def _create_ref_relation(self, source_cls, attr, target_cls):
        assert self.domain_items.get(source_cls) is not None, f"Class {source_cls} not found in the domain items"
        assert self.domain_items.get(target_cls) is not None, f"Class {target_cls} not found in the domain items"
        self.domain_relations.append(UmlRelation(source_fqn=source_cls, target_fqn=target_cls, type=RelType.REFERENCE,
                                                 label_=f"{attr}{self.REF_RELATION_SUFFIX}"))

    def _replace_compositions_with_dependencies(self):
        """Replace compositions with dependencies in the domain relations."""
        for rel in self.domain_relations:
            if rel.type == RelType.COMPOSITION:
                rel.type = RelType.DEPENDENCY

    def _set_aas_core_meta_abstract_classes_as_abstract(self):
        """
        Set the is_abstract attribute to True for abstract classes from aas-core-meta

        This is done, because standard isabstract() function does not work for abstract classes in aas-core-meta,
        as they are not defined as abstract classes in the source code, but marked with a decorator 'abstract'
        """
        for item in self.domain_items.values():
            if isinstance(item, UmlClass) and has_decorator(item.class_type, 'abstract'):
                item.is_abstract = True

    def _use_values_in_enumerations_as_names(self):
        for item in self.domain_items.values():
            if isinstance(item, UmlEnum):
                for enum_item in item.members:
                    enum_item.name = enum_item.value
                    enum_item.value = ""

    def generate_puml(self, domain_items_to_keep: Optional[List[str]] = None,
                      to_include_members_from_parents: bool = False,
                      sort_members=False) -> str:
        """Create a PlantUML file from the classes in the domain module.
        :param domain_items_to_keep: the items to include in the PlantUML file. If None, all items are included.
        :param to_include_members_from_parents: include the members from the parent classes in the child classes.
        :param sort_members: sort the members of the classes alphabetically.
        """
        if to_include_members_from_parents:
            self._include_members_from_parents()
        if domain_items_to_keep:
            self._handle_classes_and_relations_filtering(domain_items_to_keep)
        puml_content = ''.join(to_puml_content(self.domain_module, self.domain_items.values(), self.domain_relations,
                                               sort_members)).removesuffix("\n")
        # Apply IDTA specific changes to the PlantUML content and write it to the output file
        idta_puml_content = self._apply_changes(puml_content)
        return idta_puml_content

    def _include_members_from_parents(self):
        """Include the members from the parent classes in the child classes."""
        inheritance_rels = [rel for rel in self.domain_relations if rel.type == RelType.INHERITANCE]
        while len(inheritance_rels) > 0:
            self._incl_members_from_parents(inheritance_rels, inheritance_rels[0])

    def _incl_members_from_parents(self, inheritance_relations: List[UmlRelation], inheritance_rel):
        parent = self.domain_items.get(inheritance_rel.source_fqn)
        child = self.domain_items.get(inheritance_rel.target_fqn)

        parent_inheritance_rels = [rel for rel in inheritance_relations if rel.target_fqn == parent.fqn]
        for rel in parent_inheritance_rels:
            self._incl_members_from_parents(inheritance_relations, rel)

        for attr in parent.attributes:
            if attr in child.attributes:
                continue
            child.attributes.append(attr)
        inheritance_relations.remove(inheritance_rel)

    def _handle_classes_and_relations_filtering(self, domain_items_to_keep: List[str], sort_classes=True):
        all_inheritances: List[Tuple[str, str]] = self._get_inheritances()
        self._filter_items_and_relations(domain_items_to_keep)
        remain_inheritances: List[Tuple[str, str]] = self._get_inheritances()
        removed_inheritances = [inheritance for inheritance in all_inheritances if
                                inheritance not in remain_inheritances]
        self._add_filtered_out_parent_classes_as_generics(removed_inheritances)

        if sort_classes:
            self._sort_classes(domain_items_to_keep)

    def _get_inheritances(self) -> List[Tuple[str, str]]:
        return [(rel.source_fqn, rel.target_fqn) for rel in self.domain_relations if rel.type == RelType.INHERITANCE]

    def _filter_items_and_relations(self, only_domain_items: List[str]):
        for fqn in list(self.domain_items.keys()):
            if fqn not in only_domain_items:
                del self.domain_items[fqn]
        filter_domain_relations(self.domain_items, self.domain_relations)

    def _add_filtered_out_parent_classes_as_generics(self, removed_inheritances: List[Tuple[str, str]]):
        """Add classes that are filtered out from the PlantUML file and will be not shown in the diagram,
        as generics to the classes that inherit from them.
        """
        for parent, child in removed_inheritances:
            if child in self.domain_items:
                if self.domain_items[child].generics:
                    self.domain_items[child].generics = rf"{self.domain_items[child].generics}\n{parent}"
                else:
                    self.domain_items[child].generics = parent

    def _sort_classes(self, items_order: Iterable[str]):
        # Sort the classes in the order as they should appear in the PlantUML file
        sorted_domain_items = {fqn: self.domain_items[fqn] for fqn in items_order if fqn in self.domain_items}
        self.domain_items = sorted_domain_items

    def _apply_changes(self, text: str) -> str:
        for pattern, repl in self.regex_to_replace.items():
            text = re.sub(pattern, repl, text)
        return text


def pyaas2puml(domain_path: str, domain_module: str) -> Iterable[str]:
    generator = AasPumlGenerator(domain_path, domain_module)
    return generator.generate_puml()

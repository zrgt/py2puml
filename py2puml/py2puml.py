from typing import Dict, Iterable, List, Optional

from py2puml.domain.umlitem import UmlItem
from py2puml.domain.umlrelation import UmlRelation
from py2puml.export.puml import to_puml_content
from py2puml.inspection.inspectpackage import inspect_package
from py2puml.utils import filter_items_and_relations


def py2puml(domain_path: str, domain_module: str, only_domain_items: Optional[List[str]] = None) -> Iterable[str]:
    domain_items_by_fqn: Dict[str, UmlItem] = {}
    domain_relations: List[UmlRelation] = []
    inspect_package(domain_path, domain_module, domain_items_by_fqn, domain_relations)

    if only_domain_items:
        filter_items_and_relations(domain_items_by_fqn, domain_relations, only_domain_items)

    return to_puml_content(domain_module, domain_items_by_fqn.values(), domain_relations)

from dataclasses import dataclass
from typing import List, Type, Optional

from py2puml.domain.umlitem import UmlItem


@dataclass
class UmlAttribute:
    name: str
    type: str
    static: bool

    def __eq__(self, other):
        return self.name == other.name and self.type == other.type and self.static == other.static

    @property
    def visibility(self) -> str:
        if self.name.startswith("__"):
            return '-'
        elif self.name.startswith("_"):
            return '#'
        else:
            return '+'


@dataclass
class UmlClass(UmlItem):
    attributes: List[UmlAttribute]
    is_abstract: bool = False
    generics: str = ""
    class_type: Optional[Type] = None

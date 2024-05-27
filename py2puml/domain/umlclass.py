from dataclasses import dataclass
from typing import List

from py2puml.domain.umlitem import UmlItem


@dataclass
class UmlAttribute:
    name: str
    type: str
    static: bool

    @property
    def visibility(self) -> str:
        if self.name.startswith("__"):
            return '-'
        elif self.name.startswith("__"):
            return '#'
        else:
            return '+'


@dataclass
class UmlClass(UmlItem):
    attributes: List[UmlAttribute]
    is_abstract: bool = False

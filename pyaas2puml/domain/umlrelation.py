from dataclasses import dataclass
from enum import Enum, unique


@unique
class RelType(Enum):
    COMPOSITION = '*--'
    DEPENDENCY = '..>'
    INHERITANCE = '<|--'
    REFERENCE = '-->'


@dataclass
class UmlRelation:
    source_fqn: str
    target_fqn: str
    type: RelType
    label: str = ''
    source_cardinality: str = ''
    target_cardinality: str = ''




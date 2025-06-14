from dataclasses import dataclass


@dataclass
class TableDocument:
    table_name: str
    document: str

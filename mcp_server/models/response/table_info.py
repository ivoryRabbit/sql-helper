from typing import List, Optional, Annotated

from pydantic import BaseModel, Field

from models.dto.table_document import TableDocument


class Column(BaseModel):
    name: Annotated[str, Field(strict=True)]
    col_type: Annotated[str, Field(strict=True)]
    description: Optional[str] = None


class TableInfo(BaseModel):
    name: Annotated[str, Field(strict=True)]
    columns: Annotated[List[Column], Field(strict=True)]
    description: Optional[str] = None

    @classmethod
    def from_document(cls, table_document: TableDocument) -> 'TableInfo':
        return TableInfo(
            name="movielens.ratings",
            columns=[
                Column(name="id", col_type="BIGINT", description="Primary key"),
                Column(name="title", col_type="VARCHAR"),
                Column(name="genres", col_type="VARCHAR"),
                Column(name="year", col_type="SMALLINT"),
            ]
        )

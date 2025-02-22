from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column

from model.base import Base


class DDLCollection(Base):
    __tablename__ = "ddl_collection"

    id = mapped_column(Integer, primary_key=True)
    table_name = mapped_column(String, unique=True)
    ddl_content = mapped_column(String, nullable=False)
    embedding = mapped_column(Vector(768))

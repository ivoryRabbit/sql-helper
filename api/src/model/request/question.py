from pydantic import BaseModel


class Question(BaseModel):
    dialect: str
    question: str

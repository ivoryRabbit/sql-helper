import re
from typing import List, Optional, Any

import sqlparse

from src.core.interface.assistant import Assistant
from src.core.interface.vector_store import VectorStore


class SQLAgent:
    def __init__(
        self,
        assistant: Assistant,
        vector_store: VectorStore,
        *,
        dialect: str = "SQL",
        language: Optional[str] = None,
        max_tokens: int = 1000,
        print_log: bool = False,
    ):
        self.assistant = assistant
        self.vector_store = vector_store

        self.dialect = dialect
        self.language = language
        self.max_tokens = max_tokens
        self.print_log = print_log

    def _log(self, message: Any, title: str = "INFO") -> None:
        if self.print_log is True:
            print(f"{title}: {message}")

    def _response_language(self) -> str:
        if self.language is None:
            return ""

        return f"Respond in the {self.language} language."

    def generate_suggestions(self, n_results: int = 5) -> List[str]:
        question_sql = self.vector_store.get_similar_question_sql(question="", n_results=n_results)
        return [q["question"] for q in question_sql]

    def generate_sql(self, question: str) -> str:
        ddl_list = self.vector_store.get_related_ddl(question, n_results=5)
        doc_list = self.vector_store.get_related_doc(question, n_results=5)
        question_sql_list = self.vector_store.get_similar_question_sql(question, n_results=5)

        initial_prompt = (
            f"You are a {self.dialect} expert. "
            f"Please help to generate a SQL query to answer the question. "
            f"Your response should ONLY be based on the given context and follow the response guidelines and format instructions. "
        )

        initial_prompt = self.add_ddl_to_prompt(initial_prompt, ddl_list)
        initial_prompt = self.add_doc_to_prompt(initial_prompt, doc_list)

        initial_prompt += (
            "===Response Guidelines \n"
            "1. If the provided context is sufficient, please generate a valid SQL query without any explanations for the question. \n"
            "2. If the provided context is almost sufficient but requires knowledge of a specific string in a particular column, please generate an intermediate SQL query to find the distinct strings in that column. Prepend the query with a comment saying intermediate_sql \n"
            "3. If the provided context is insufficient, please explain why it can't be generated. \n"
            "4. Please use the most relevant table(s) and columns from those tables. \n"
            "5. If the question has been asked and answered before, please repeat the answer exactly as it was given before. \n"
        )

        prompts = [self.assistant.generate_system_message(initial_prompt)]

        for example in question_sql_list:
            prompts.append(self.assistant.generate_user_message(example["question"]))
            prompts.append(self.assistant.generate_assistant_message(example["sql"]))

        prompts.append(self.assistant.generate_user_message(question))
        self._log(title="SQL Prompt", message=prompts)

        llm_response = self.assistant.submit_prompts(prompts)
        self._log(title="LLM Response", message=llm_response)

        return self.extract_sql(llm_response)

    def extract_sql(self, llm_response: str) -> str:

        # If the llm_response contains a CTE (with clause), extract the last sql between WITH and ;
        sqls = re.findall(r"WITH.*?;", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            self._log(title="Extracted SQL", message=f"{sql}")
            return sql

        # If the llm_response is not markdown formatted, extract last sql by finding select and ; in the response
        sqls = re.findall(r"SELECT.*?;", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            self._log(title="Extracted SQL", message=f"{sql}")
            return sql

        # If the llm_response contains a markdown code block, with or without the sql tag, extract the last sql from it
        sqls = re.findall(r"```sql\n(.*)```", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            self._log(title="Extracted SQL", message=f"{sql}")
            return sql

        sqls = re.findall(r"```(.*)```", llm_response, re.DOTALL)
        if sqls:
            sql = sqls[-1]
            self._log(title="Extracted SQL", message=f"{sql}")
            return sql

        return llm_response

    def is_sql_valid(self, sql: str) -> bool:
        parsed = sqlparse.parse(sql)
        self._log(message="Check if the SQL is valid")

        for statement in parsed:
            if statement.get_type() == 'SELECT':
                return True

        return False

    def generate_followup_questions(
        self, question: str, sql: str, n_questions: int = 5, **kwargs
    ) -> list:
        prompts = [
            self.assistant.generate_system_message(
                f"You are a helpful data assistant. "
                f"The user asked the question: '{question}'\n\nThe SQL query for this question was: {sql}\n\n"
            ),
            self.assistant.generate_user_message(
                f"Generate a list of {n_questions} followup questions that the user might ask about this data. "
                f"Respond with a list of questions, one per line. "
                f"Do not answer with any explanations -- just the questions. "
                f"Remember that there should be an unambiguous SQL query that can be generated from the question. "
                f"Prefer questions that are answerable outside of the context of this conversation. "
                f"Prefer questions that are slight modifications of the SQL query that was generated that allow digging deeper into the data. "
                f"Each question will be turned into a button that the user can click to generate a new SQL query so don't use 'example' type questions. "
                f"Each question must have a one-to-one correspondence with an instantiated SQL query." +
                self._response_language()
            ),
        ]

        llm_response = self.assistant.submit_prompts(prompts)

        numbers_removed = re.sub(r"^\d+\.\s*", "", llm_response, flags=re.MULTILINE)
        return numbers_removed.split("\n")

    def _approx_count_tokens(self, string: str) -> float:
        return len(string) / 4

    def add_ddl_to_prompt(self, initial_prompt: str, ddl_list: list[str]) -> str:
        if ddl_list:
            initial_prompt += "\n===Tables \n"

        for ddl in ddl_list:
            if (
                self._approx_count_tokens(initial_prompt)
                + self._approx_count_tokens(ddl)
                < self.max_tokens
            ):
                initial_prompt += f"{ddl}\n\n"

        return initial_prompt

    def add_doc_to_prompt(self, initial_prompt: str, doc_list: list[str]) -> str:
        if doc_list:
            initial_prompt += "\n===Additional Context \n\n"

        for doc in doc_list:
            if (
                self._approx_count_tokens(initial_prompt)
                + self._approx_count_tokens(doc)
                < self.max_tokens
            ):
                initial_prompt += f"{doc}\n\n"

        return initial_prompt

    def add_sql_to_prompt(self, initial_prompt: str, sql_list: list[dict[str, str]]) -> str:
        if sql_list:
            initial_prompt += "\n===Question-SQL Pairs\n\n"

        for question in sql_list:
            if (
                self._approx_count_tokens(initial_prompt)
                + self._approx_count_tokens(question["sql"])
                < self.max_tokens
            ):
                initial_prompt += f"{question['question']}\n{question['sql']}\n\n"

        return initial_prompt

    def get_followup_questions_prompt(
        self,
        question: str,
        ddl_list: list,
        doc_list: list,
            question_sql_list: list,
    ) -> list:
        initial_prompt = f"The user initially asked the question: '{question}': \n\n"

        initial_prompt = self.add_ddl_to_prompt(initial_prompt, ddl_list)

        initial_prompt = self.add_doc_to_prompt(initial_prompt, doc_list)

        initial_prompt = self.add_sql_to_prompt(initial_prompt, question_sql_list)

        message_log = [
            self.assistant.generate_system_message(initial_prompt),
            self.assistant.generate_user_message(
                "Generate a list of followup questions that the user might ask about this data. "
                "Respond with a list of questions, one per line. "
                "Do not answer with any explanations -- just the questions."
            )
        ]

        return message_log

    def generate_question(self, sql: str) -> str:
        prompts = [
            self.assistant.generate_system_message(
                "The user will give you SQL and you will try to guess what the business question this query is answering. "
                "Return just the question without any additional explanation. "
                "Do not reference the table name in the question."
            ),
            self.assistant.generate_user_message(sql),
        ]

        response = self.assistant.submit_prompts(prompts)
        return response

    def ask(self, question: Optional[str] = None, auto_train: bool = True) -> Optional[str]:
        if question is None:
            question = input("Enter a question: ")

        try:
            sql = self.generate_sql(question=question)
        except Exception as e:
            print(e)
            return None

        if auto_train is True:
            self.vector_store.add_question_sql(question=question, sql=sql)

        return sql

    def train(
        self,
        question: str,
        ddl: Optional[str] = None,
        doc: Optional[str] = None,
        sql: Optional[str] = None,
    ) -> str:
        if ddl:
            self._log(title="Adding ddl:", message=ddl)
            return self.vector_store.add_ddl(ddl)

        if doc:
            self._log(title="Adding doc:", message=doc)
            return self.vector_store.add_doc(doc)

        if sql:
            if question is None:
                question = self.generate_question(sql)
                self._log(f"Question is generated with sql: {question}")
            return self.vector_store.add_question_sql(question=question, sql=sql)

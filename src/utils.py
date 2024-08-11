import sqlparse


def read_sql(path: str) -> str:
    with open(path, mode="r") as file:
        sql = file.read()

    return sqlparse.format(sql, indent_tabs=True, keyword_case="upper")

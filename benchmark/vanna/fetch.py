import sqlparse
import streamlit as st
from vanna.remote import VannaDefault


vn = VannaDefault(
    api_key=st.secrets.get("VANNA_API_KEY"),
    model=st.secrets.get("VANNA_MODEL_NAME"),
)


def read_sql(path: str) -> str:
    with open(path, mode="r") as file:
        sql = file.read()

    return sqlparse.format(sql, indent_tabs=True, keyword_case="upper")


# vn.remove_training_data(id="349318-sql")
# vn.remove_training_data(id="200162-ddl")
# vn.remove_training_data(id="200161-ddl")

dm_vendor_item_ddl = read_sql("./sql/dm_vendor_item.sql")
dm_vendor_ddl = read_sql("./sql/dm_vendor.sql")
sellable_sql = read_sql("./sql/sellable.sql")

vn.train(ddl=dm_vendor_item_ddl)
vn.train(ddl=dm_vendor_ddl)
vn.train(sql=sellable_sql)

print(vn.get_training_data())

answer = vn.ask("Show me how many sellable vendor items there are for each vendor type.")

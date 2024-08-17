import streamlit as st

from src.client.controller.data import *


def render_page() -> None:
    st.title("Data")
    is_editable = st.toggle("Edit mode")

    st.header("DDLs", divider=True)

    for (id, summary, ddl) in get_all_ddl().itertuples(index=False):
        with st.expander(id, expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.code(ddl, language="sql")
            with col2:
                st.code(summary, language="markdown")

            st.button(
                "Delete",
                on_click=delete_ddl,
                args=(id, ),
                disabled=not is_editable,
                use_container_width=True,
                key=f"delete_{id}",
            )

    with st.popover("Add DDL", disabled=not is_editable, use_container_width=True):
        with st.form("DDL form"):
            table_name = st.text_input("Table name")

            col1, col2 = st.columns(2)

            with col1:
                ddl = st.text_area("DDL")
            with col2:
                summary = st.text_area("Summary")

            is_submitted = st.form_submit_button("Add", use_container_width=True)

            if is_submitted is True:
                create_ddl(table_name, ddl, summary)
                st.rerun()

    st.header("SQLs", divider=True)

    for (id, question, sql) in get_all_sql().itertuples(index=False):
        with st.expander(id, expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.code(question, language="markdown")
            with col2:
                st.code(sql, language="sql")

            st.button(
                "Delete",
                on_click=delete_sql,
                args=(id, ),
                disabled=not is_editable,
                use_container_width=True,
                key=f"delete_{id}",
            )

    with st.popover("Add SQL", disabled=not is_editable, use_container_width=True):
        with st.form("SQL form"):
            sql_alias = st.text_input("SQL alias")

            col1, col2 = st.columns(2)

            with col1:
                question = st.text_area("Question")
            with col2:
                sql = st.text_area("SQL")

            is_submitted = st.form_submit_button("Add", use_container_width=True)

            if is_submitted is True:
                create_sql(sql_alias, question, sql)
                st.rerun()

    st.header("Docs", divider=True)

    for (id, documentation, _) in get_all_doc().itertuples(index=False):
        with st.expander(id, expanded=False):
            st.code(documentation, language="markdown")

            st.button(
                "Delete",
                on_click=delete_doc,
                args=(id, ),
                disabled=not is_editable,
                use_container_width=True,
                key=f"delete_{id}",
            )

    with st.popover("Add Doc", disabled=not is_editable, use_container_width=True):
        with st.form("Doc form"):
            doc_name = st.text_input("Doc name")

            doc = st.text_area("Doc")

            is_submitted = st.form_submit_button("Add", use_container_width=True)

            if is_submitted is True:
                create_doc(doc_name, doc)
                st.rerun()


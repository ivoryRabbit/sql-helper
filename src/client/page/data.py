import streamlit as st


def render_page() -> None:
    st.title("Data")

    st.header("Tables", divider=True)
    with st.expander("table1", expanded=False):
        summary, ddl = st.columns(2)

        with summary:
            st.code(
                """
                ===table name
                temp
                
                === explanation
                temporary table
                
                === column info
                
                """,
                language="markdown"
            )

        with ddl:
            st.code(
                """
                SELECT 1
                FROM dual
                """,
                language="sql"
            )

    st.expander("table2", expanded=False)
    st.expander("table3", expanded=False)

    st.header("SQLs", divider=True)
    st.expander("SQL1", expanded=False)
    st.expander("SQL2", expanded=False)
    st.expander("SQL3", expanded=False)




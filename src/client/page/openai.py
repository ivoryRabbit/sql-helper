import streamlit as st

from src.client.component import (
    generate_sql_cached,
    is_sql_valid_cached
)


def refresh_chat_history() -> None:
    st.session_state["messages"] = []


def render_page() -> None:
    st.sidebar.button("Reset", on_click=lambda: refresh_chat_history(), use_container_width=True)
    st.title("SQL Helper")

    # Initialize chat history
    if "messages" not in st.session_state:
        refresh_chat_history()

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.code(message["content"], language="sql", line_numbers=True)
            else:
                st.markdown(message["content"])

    question = st.chat_input("Ask me a question about your data")

    # React to user input
    if question:
        with st.chat_message("user"):
            st.markdown(question)

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": question})

        sql = generate_sql_cached(question=question)

        if sql:
            with st.chat_message("assistant"):
                if is_sql_valid_cached(sql=sql):
                    st.code(sql, language="sql", line_numbers=True)
                else:
                    st.markdown(sql)
        else:
            assistant_message_error = st.chat_message("assistant")
            assistant_message_error.error("I wasn't able to generate SQL for that question")

        # Display assistant response in chat message container
        st.session_state.messages.append({"role": "assistant", "content": sql})

import streamlit as st

from src.client.component import (
    generate_suggestions_cached,
    generate_sql_cached,
    is_sql_valid_cached
)


def refresh_chat_history() -> None:
    st.session_state["messages"] = []


def render_page() -> None:
    st.title("SQL Helper")
    st.sidebar.button("Reset", on_click=lambda: refresh_chat_history(), use_container_width=True)

    if "messages" not in st.session_state:
        refresh_chat_history()

    if len(st.session_state.messages) > 10:
        st.session_state.messsages.pop(0)

    if "question" not in st.session_state:
        st.session_state.question = None

    def set_messages(question: str) -> None:
        st.session_state.messages.append({"role": "user", "content": question})

        sql = generate_sql_cached(question=question)

        if is_sql_valid_cached(sql=sql):
            st.session_state.messages.append({"role": "assistant", "content": sql})

    def set_user_input() -> None:
        set_messages(st.session_state.user_input)

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.code(message["content"], language="sql", line_numbers=True)
            else:
                st.markdown(message["content"])

    # Suggest questions
    with st.chat_message("assistant"):
        if st.button("Click to show suggested questions"):
            questions = generate_suggestions_cached()

            for question in questions:
                st.button(question, on_click=set_messages, args=(question, ))

    st.chat_input(
        "Ask me a question about your data",
        key="user_input",
        on_submit=set_user_input,
    )

    # # React to user input
    # if question:
    #     with st.chat_message("user"):
    #         st.markdown(question)
    #
    #     # Add user message to chat history
    #     st.session_state.messages.append({"role": "user", "content": question})
    #
    #     sql = generate_sql_cached(question=question)
    #
    #     if sql:
    #         with st.chat_message("assistant"):
    #             if is_sql_valid_cached(sql=sql):
    #                 st.code(sql, language="sql", line_numbers=True)
    #             else:
    #                 st.markdown(sql)
    #     else:
    #         assistant_message_error = st.chat_message("assistant")
    #         assistant_message_error.error("I wasn't able to generate SQL for that question")
    #
    #     # Display assistant response in chat message container
    #     st.session_state.messages.append({"role": "assistant", "content": sql})

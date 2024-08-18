from collections import deque

import streamlit as st

from src.client.controller.chat import (
    generate_suggestions_cached,
    generate_sql_cached,
    is_sql_valid_cached,
    generate_followup_cached,
)


def refresh_chat_history() -> None:
    st.session_state["messages"] = deque(maxlen=6)


def get_answer(question: str):
    st.session_state.messages.append({"role": "user", "content": question, "is_sql": False})

    answer = generate_sql_cached(question=question)
    is_sql = is_sql_valid_cached(sql=answer)

    st.session_state.messages.append({"role": "assistant", "content": answer, "is_sql": is_sql})
    return answer, is_sql


def render_page() -> None:
    st.title("SQL Helper")
    st.sidebar.button("Reset", on_click=refresh_chat_history, use_container_width=True)

    if "messages" not in st.session_state:
        refresh_chat_history()

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["is_sql"] is True:
                st.code(message["content"], language="sql", line_numbers=True)
            else:
                st.markdown(message["content"])

    user_question = st.chat_input("Ask me a question about your data")

    if user_question is not None:
        with st.chat_message("user"):
            st.markdown(user_question)

        answer, is_sql = get_answer(user_question)
        with st.chat_message("assistant"):
            if is_sql is True:
                st.code(answer, language="sql", line_numbers=True)
            else:
                st.markdown(answer)

    with st.chat_message("assistant"):
        if st.button("Click to show suggested questions"):
            suggestions = generate_suggestions_cached()

            for suggestion in suggestions:
                st.button(suggestion, on_click=get_answer, args=(suggestion, ))

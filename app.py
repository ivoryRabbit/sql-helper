import time
from typing import Optional

import streamlit as st

from component import (
    generate_questions_cached,
    generate_sql_cached,
    run_sql_cached,
    generate_plotly_code_cached,
    generate_plot_cached,
    generate_followup_cached,
    should_generate_chart_cached,
    is_sql_valid_cached,
    generate_summary_cached
)

st.set_page_config(layout="wide")

st.sidebar.title("Output Settings")
st.sidebar.checkbox("Show SQL", value=True, key="show_sql")
st.sidebar.checkbox("Show Table", value=True, key="show_table")
st.sidebar.checkbox("Show Plotly Code", value=True, key="show_plotly_code")
st.sidebar.checkbox("Show Chart", value=True, key="show_chart")
st.sidebar.checkbox("Show Summary", value=True, key="show_summary")
st.sidebar.checkbox("Show Follow-up Questions", value=True, key="show_followup")
st.sidebar.button("Reset", on_click=lambda: set_question(), use_container_width=True)

st.title("SQL Helper")


def set_question(question: Optional[str] = None) -> None:
    st.session_state["my_question"] = question


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.code(message["content"], language="sql", line_numbers=True)
        else:
            st.markdown(message["content"])

my_question = st.chat_input("Ask me a question about your data")

with st.chat_message("assistant"):
    if suggestion := st.button("Click to show suggested questions"):
        st.session_state["my_question"] = None

        questions = generate_questions_cached()

        for i, question in enumerate(questions):
            time.sleep(0.05)
            button = st.button(
                question,
                on_click=set_question,
                args=(question, ),
            )

my_question = st.session_state.get("my_question", default=None)

# if my_question is None:
#     my_question = st.chat_input("Ask me a question about your data")

# React to user input
if my_question:
    with st.chat_message("user"):
        st.markdown(my_question)
        st.session_state["my_question"] = None

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": my_question})

    sql = generate_sql_cached(question=my_question)

    if sql:
        with st.chat_message("assistant"):
            if is_sql_valid_cached(sql=sql):
                st.code(sql, language="sql", line_numbers=True)
    else:
        assistant_message_error = st.chat_message("assistant")
        assistant_message_error.error("I wasn't able to generate SQL for that question")

    # Display assistant response in chat message container
    st.session_state.messages.append({"role": "assistant", "content": sql})

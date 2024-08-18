from dataclasses import dataclass

import streamlit as st


@dataclass
class AssistantConfig:
    name: str

    def __post_init__(self):
        self.api_key = st.secrets[self.name]["API_KEY"]
        self.model_name = st.secrets[self.name]["MODEL_NAME"]


OPENAI = AssistantConfig("OpenAI")
COHERE = AssistantConfig("Cohere")
CLAUDE = AssistantConfig("Claude")


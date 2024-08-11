from typing import List, Dict

from src.core.interface.assistant import Assistant


class MockAssistant(Assistant):
    def generate_system_message(self, message: str) -> Dict[str, str]:
        return {"role": "system", "content": message}

    def generate_user_message(self, message: str) -> Dict[str, str]:
        return {"role": "user", "content": message}

    def generate_assistant_message(self, message: str) -> Dict[str, str]:
        return {"role": "assistant", "content": message}

    def submit_prompts(self, prompts: List[Dict[str, str]]) -> str:
        return """
            SELECT temp_id, COUNT(1)
            FROM temp_table_name
            WHERE dt = 20240808
            GROUP BY 1
        """

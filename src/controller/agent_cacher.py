
from src.setup.cache import RedisDataSource
from src.agent.custom_agent import LearningAgent


class AgentManager:
    def __init__(self):
        self.cache = RedisDataSource()

    def get_agent(self, session_id, llm_type):
        cached = self.cache.read(f"agent:{session_id}")
        agent = LearningAgent(llm_type)
        if cached and "chat_history" in cached:
            agent.chat_history = [
                msg for msg in cached["chat_history"]
                if isinstance(msg, dict) and "role" in msg and "content" in msg
            ]
        return agent

    def save_agent(self, session_id, agent):
        self.cache.write(f"agent:{session_id}", {
            "chat_history": [
                {"role": msg["role"], "content": msg["content"]}
                for msg in agent.chat_history
            ]
        })

# from src.setup.cache import RedisDataSource
from src.setup.json_cache import SimpleJsonDataSource
from src.agent.custom_agent import LearningAgent
import logging

class AgentManager:
    def __init__(self):
        # self.cache = RedisDataSource()
        self.cache = SimpleJsonDataSource()
        self.agents = {}  # In-memory cache of active agents
        logging.info("AgentManager initialized with JSON cache")

    def get_agent(self, session_id, llm_type):
        # Check if agent exists in memory cache first
        cache_key = f"{session_id}:{llm_type}"
        if cache_key in self.agents:
            logging.info(f"Retrieved agent from memory cache: {session_id}")
            return self.agents[cache_key]
        
        # Try to load from persistent cache
        cached = self.cache.read(f"agent:{session_id}")
        agent = LearningAgent(llm_type)
        
        if cached and "chat_history" in cached:
            try:
                # Restore chat history
                agent.chat_history = [
                    msg for msg in cached["chat_history"]
                    if isinstance(msg, dict) and "role" in msg and "content" in msg
                ]
                logging.info(f"Loaded chat history from cache for session: {session_id}")
            except Exception as e:
                logging.error(f"Error loading chat history: {e}")
                agent.chat_history = []
        
        # Store in memory cache
        self.agents[cache_key] = agent
        logging.info(f"Created new agent for session: {session_id}, LLM: {llm_type}")
        return agent

    def save_agent(self, session_id, agent):
        try:
            # Prepare data for caching
            cache_data = {
                "chat_history": [
                    {"role": msg.get("role", ""), "content": msg.get("content", "")}
                    for msg in agent.chat_history
                    if isinstance(msg, dict) and msg.get("role") and msg.get("content")
                ],
                "llm_type": agent.llm.__class__.__name__ if hasattr(agent, 'llm') else "unknown",
                "session_id": session_id,
                "last_updated": self._get_current_timestamp()
            }
            
            # Save to cache
            self.cache.write(f"agent:{session_id}", cache_data)
            logging.info(f"Saved agent to cache: {session_id}")
            
        except Exception as e:
            logging.error(f"Error saving agent to cache: {e}")

    def _get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()

    def list_active_sessions(self):
        """List all active agent sessions"""
        sessions = []
        for cache_key, agent in self.agents.items():
            session_id, llm_type = cache_key.split(":")
            sessions.append({
                "session_id": session_id,
                "llm_type": llm_type,
                "chat_history_length": len(agent.chat_history),
                "has_file_tools": hasattr(agent, 'file_tools')
            })
        return sessions

    def cleanup_old_sessions(self, max_age_hours=24):
        """Clean up old sessions from memory cache"""
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        sessions_to_remove = []
        for cache_key in list(self.agents.keys()):
            # For now, we don't have timestamps in memory cache
            # In a real implementation, you'd track when agents were created
            pass
        
        logging.info(f"Cleanup would remove {len(sessions_to_remove)} sessions")
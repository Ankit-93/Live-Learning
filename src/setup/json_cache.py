import os
import json
from datetime import datetime
from pathlib import Path
import hashlib
from src.controller.customlogger import logging

class SimpleJsonDataSource:
    """Simple JSON-based data source for chat memory storage"""
    
    def __init__(self, storage_path: str = "./sessions"):
        self.storage_path = storage_path
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
    
    def _get_filename(self, session_id: str) -> str:
        """Generate filename from session_id"""
        safe_id = hashlib.md5(session_id.encode()).hexdigest()[:16]
        return os.path.join(self.storage_path, f"{safe_id}.json")
    
    def read(self, session_id: str) -> dict:
        """Read session data"""
        filename = self._get_filename(session_id)
        
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logging.info(f"JSON Read: session_id={session_id}, found=True")
                return data
            except json.JSONDecodeError as e:
                logging.error(f"JSON Read Error: {e}")
                return {}
        
        logging.info(f"JSON Read: session_id={session_id}, found=False")
        return {}
    
    def write(self, session_id: str, data: dict) -> bool:
        """Write session data"""
        try:
            filename = self._get_filename(session_id)
            
            # Add timestamp
            data_with_meta = {
                "session_id": session_id,
                "updated_at": datetime.now().isoformat(),
                **data
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_with_meta, f, indent=2, ensure_ascii=False)
            
            logging.info(f"JSON Write: session_id={session_id}, data_keys={list(data.keys())}")
            return True
            
        except Exception as e:
            logging.error(f"JSON Write Error: {e}")
            return False
    
    def delete(self, session_id: str) -> bool:
        """Delete session data"""
        try:
            filename = self._get_filename(session_id)
            if os.path.exists(filename):
                os.remove(filename)
                logging.info(f"JSON Delete: session_id={session_id}")
                return True
            return False
        except Exception as e:
            logging.error(f"JSON Delete Error: {e}")
            return False
    
    def list_all(self) -> list:
        """List all sessions"""
        sessions = []
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                filepath = os.path.join(self.storage_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    sessions.append({
                        "session_id": data.get("session_id", "unknown"),
                        "filename": filename,
                        "updated_at": data.get("updated_at"),
                        "size": os.path.getsize(filepath)
                    })
                except:
                    continue
        return sessions


# Usage example in your existing code
def test_usage():
    # Replace Redis with JSON
    # data_source = RedisDataSource()  # Old
    data_source = SimpleJsonDataSource(storage_path="./data/sessions")  # New
    
    # Read and write operations remain the same
    session_id = "test_123"
    data = {"chat_history": [], "llm_type": "OpenAI"}
    
    # Write
    data_source.write(session_id, data)
    
    # Read
    retrieved = data_source.read(session_id)
    print(retrieved)
    
    # List all
    all_sessions = data_source.list_all()
    print(f"Total sessions: {len(all_sessions)}")

if __name__ == "__main__":
    test_usage()
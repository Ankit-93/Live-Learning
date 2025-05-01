import os, redis
from dotenv import load_dotenv
from src.controller.customlogger import logging

load_dotenv()


class RedisDataSource:
    def __init__(self, host='localhost', port=6379, db=0):
        self.host = os.environ.get("REDIS_HOST")
        self.username = os.environ.get("REDIS_USERNAME")
        self.password = os.environ.get("REDIS_PASSWORD")
        self.port = os.environ.get("REDIS_PORT")
        self.client = redis.Redis(host=self.host,
                                  username=self.username,
                                  password=self.password,
                                  port=self.port,
                                  decode_responses=True)

    def read(self, session_id):
        cache_data = self.client.get(session_id)
        logging.info(f"Redis Read: session_id={session_id}, found={bool(cache_data)}")
        return eval(cache_data) if cache_data else {}

    def write(self, session_id, data):
        try:
            self.client.set(session_id, str(data))
            logging.info(f"Redis Write: session_id={session_id}, data_keys={list(data.keys())}")
        except Exception as e:
            logging.error(f"Redis Write Error: {e}")
            print(data)


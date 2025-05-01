import os
from src.controller.customlogger import logging
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.llms.openai import OpenAI
from llama_index.llms.huggingface import HuggingFaceLLM
from mistralai import Mistral
from llama_index.core.llms import ChatMessage
from dotenv import load_dotenv
load_dotenv()


class MistralWrapper:
    def __init__(self):
        self.client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
        self.model = "mistral-large-latest"

    def complete(self, messages, **kwargs):
        chat_response = self.client.chat.complete(
                        model= self.model,
                        messages = [{"role":"user", "content":messages}])
        return chat_response.choices[0].message.content

## --- LLMCall ---
class LLMCall:
    def __init__(self, llm_type="OpenAi", config=None):
        self.llm_type = llm_type
        self.config = config or {}
        self.api_key_google = os.getenv("GOOGLE_API_KEY")
        self.client = self.get_llm()

    def get_llm(self):
        if self.llm_type == "OpenAi":
            logging.info("Initializing OpenAI LLM")
            return self._get_openai_llm()
        elif self.llm_type == "Google":
            logging.info("Initializing Google Gemini LLM")
            return self._get_google_llm()
        elif self.llm_type == "HuggingFace":
            logging.info("Initializing HuggingFace LLM")
            return self._get_huggingface_llm()
        elif self.llm_type == "Mistral":
            logging.info("Initializing HuggingFace LLM")
            return self._get_mistral()
        else:
            raise ValueError(f"Unsupported LLM type: {self.llm_type}")

    def _get_openai_llm(self):
        return OpenAI(
            model=self.config.get("model", "gpt-3.5-turbo-0613"),
            api_key=self.config.get("api_key"),
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens", 1024)
        )

    def _get_google_llm(self):
        return GoogleGenAI(
            model="models/gemini-1.5-flash",
        )
    
    def _get_mistral(self):
        return MistralWrapper()


    def _get_huggingface_llm(self):
        return HuggingFaceLLM(
            model_name="HuggingFaceH4/zephyr-7b-beta",
            tokenizer_name="HuggingFaceH4/zephyr-7b-beta",
            context_window=self.config.get("context_window", 2048),
            max_new_tokens=self.config.get("max_new_tokens", 256)
        )
    
    
    def get_client(self):
        return self.client
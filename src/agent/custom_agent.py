import re, ast
import logging

import re
import json
import logging
from typing import List, Dict

from llama_index.core.tools.types import ToolOutput
from src.agent.agenttools import ChatBotFunctionTools


class LearningAgent:
    def __init__(self, llm_value: str):
        tool_builder = ChatBotFunctionTools(llm_type=llm_value)
        self.llm = tool_builder.generator
        self.tools = tool_builder.get_tools()
        self.chat_history: List[Dict[str, str]] = []
        self.max_history = 20

    def extract_json_from_markdown(self, markdown_text: str):
        try:
            match = re.search(r"```json\s*(\{.*?\})\s*```", markdown_text, re.DOTALL)
            if not match:
                raise ValueError("No JSON block found in markdown")
            return json.loads(match.group(1))
        except Exception as e:
            logging.error(f"Could not parse JSON: {e}")
            return None

    def determine_tools(self, query: str):
        previous_questions = "\n".join(
            [msg["content"] for msg in self.chat_history if msg["role"] == "user"]
        ) if self.chat_history else "No previous questions"

        prompt = f"""Analyze this learning query and select appropriate tools also form the condensed query based on
                    previous_questions and Query:
                    For Choosing tool properly analyze the condensed query and then decide. Choose multiple if its necessary based on condensed query
                    Its mandatory to select to atleast 1 tool
                    Query: {query}
                    Previous Query: {previous_questions}
                    Available Tools: {list(self.tools.keys())}
                    Return dictionary of tool names and condensed query as dictionary in the below format:
                            ```json
                            {{
                              "condensed_query": condensed query considering chat history and user query as string,
                              "tool_names": tool names as comma-separated list
                            }}
                            ```
                 Do Not add additional text"""
        response = self.llm.complete(prompt)
        try:
            response = response.text
        except:
            response = response
        parsed = self.extract_json_from_markdown(response)
        condensed_query = parsed["condensed_query"]
        tools = [t.strip() for t in parsed['tool_names'].split(",") if t.strip() in self.tools]
        return tools if tools else ['llm_query'], condensed_query

    def execute_tools(self, tools: List[str], query: str) -> tuple[str, str]:
        tool_results, content_results = [], []
        for tool in tools:
            try:
                tool_output = self.tools[tool](query)
                content = tool_output.content if isinstance(tool_output, ToolOutput) else str(tool_output)
                tool_results.append(tool)
                content_results.append(content)
            except Exception as e:
                logging.error(f"Tool {tool} failed: {str(e)}")
                tool_results.append(tool)
                content_results.append(f"Error: {str(e)}")

        if len(tool_results) > 1:
            combined = "\n\n".join(f"**{t}**:\n{c}" for t, c in zip(tool_results, content_results))
            explanation = self.tools["concept_combiner"](content_results)
            return "multiple", f"{combined}\n\n**Combined Analysis**:\n{explanation}"
        return tool_results[0], content_results[0]

    def process_query(self, query: str) -> tuple[List[Dict[str, str]], str, str]:
        tools, condensed_query = self.determine_tools(query)
        tool_used, response = self.execute_tools(tools, condensed_query)
        self.chat_history += [{"role": "user", "content": query}, {"role": "assistant", "content": response}]
        self.chat_history = self.chat_history[-(self.max_history * 2):]
        return self.chat_history, tool_used, response


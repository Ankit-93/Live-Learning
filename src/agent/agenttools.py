from llama_index.core.tools import FunctionTool
from src.setup.utils import retry
from src.controller.customlogger import logging
from src.llm.source_llm import LLMCall


class ChatBotFunctionTools:
    def __init__(self, llm_type="google"):
        self.generator = LLMCall(llm_type).get_llm()

    @retry(max_retries=5, delay=1)
    def machine_learning_concept(self, query):
        logging.info(f"Tool Call: machine_learning_concept('{query}')")
        prompt = (
            "You are a Machine Learning teacher.\n"
            "Explain the following ML concept in:\n"
            "The explaination should include geometrical or mathematical intuition"
            "Try to keep answer crisp and compact"
            f"User Query: {query}"
        )
        return self.generator.complete(prompt)

    @retry(max_retries=5, delay=1)
    def math_concept(self, query):
        logging.info(f"Tool Call: math_concept('{query}')")
        prompt = (
            "You are a Math teacher.\n"
            "Explain the following mathematics behind the Machine Learning algorithm in details with each step by step :\n"
            "Try to keep answer crisp and compact"
            f"User Query: {query}"
        )
        return self.generator.complete(prompt)

    @retry(max_retries=5, delay=1)
    def deep_learning_architecture(self, arch):
        logging.info(f"Tool Call: deep_learning_architecture('{arch}')")
        prompt = f"Explain the {arch} neural network architecture with diagram description"
        return self.generator.complete(prompt)

    @retry(max_retries=5, delay=1)
    def visualize_algorithm(self, algo):
        logging.info(f"Tool Call: visualize_algorithm('{algo}')")
        prompt = f"Create visualization code that demonstrates how {algo} works"
        return self.generator.complete(prompt)

    @retry(max_retries=5, delay=1)
    def concept_combiner(self, concepts):
        logging.info(f"Tool Call: concept_combiner('{concepts}')")
        prompt = f"Explain the relationship between these concepts: {', '.join(concepts)}"
        return self.generator.complete(prompt)

    @retry(max_retries=5, delay=1)
    def llm_query(self, concepts):
        logging.info(f"Tool Call: llm_query('{concepts}')")
        prompt = f"You are an Expert to Answer the following question respond to the best of your knowledge: {', '.join(concepts)}"
        return self.generator.complete(prompt)

    @retry(max_retries=5, delay=1)
    def get_tools(self):
        return {
            "ml_concept": FunctionTool.from_defaults(fn=self.machine_learning_concept),
            "dl_architecture": FunctionTool.from_defaults(fn=self.deep_learning_architecture),
            "algo_visualizer": FunctionTool.from_defaults(fn=self.visualize_algorithm),
            "concept_combiner": FunctionTool.from_defaults(fn=self.concept_combiner),
            "math_concept": FunctionTool.from_defaults(fn=self.math_concept),
            "llm_query": FunctionTool.from_defaults(fn=self.llm_query)
        }



# class LearningAgent:
#     """Core agent that orchestrates tool usage for learning system"""
#
#     def __init__(self, llm_value):
#         self.llm = LLMCall(llm_type=llm_value).get_llm()
#         self.tools = self._setup_tools()
#         self.chat_history: List[Dict[str, str]] = []  # Stores properly formatted messages
#         self.max_history = 20
#
#     def _setup_tools(self) -> Dict[str, FunctionTool]:
#         """Initialize all learning tools"""
#         return {
#             **self._setup_ml_tools(),
#             **self._setup_dl_tools(),
#             **self._setup_graph_tools(),
#             **self._setup_utility_tools()
#         }
#
#     def _setup_ml_tools(self) -> Dict[str, FunctionTool]:
#         """Machine Learning tools"""
#
#         def ml_concept_explainer(query: str) -> str:
#             prompt = f"Explain this ML concept in simple terms with examples: {query}"
#             return self.llm.complete(prompt).text
#
#         return {
#             "ml_concept": FunctionTool.from_defaults(fn=ml_concept_explainer)
#         }
#
#     def _setup_dl_tools(self) -> Dict[str, FunctionTool]:
#         """Deep Learning tools"""
#
#         def dl_architecture(arch: str) -> str:
#             prompt = f"Explain the {arch} neural network architecture with diagram description"
#             return self.llm.complete(prompt).text
#
#         return {
#             "dl_architecture": FunctionTool.from_defaults(fn=dl_architecture)
#         }
#
#     def _setup_graph_tools(self) -> Dict[str, FunctionTool]:
#         """Graph/Visualization tools"""
#
#         def visualize_algorithm(algo: str) -> str:
#             prompt = f"Create visualization code that demonstrates how {algo} works"
#             return self.llm.complete(prompt).text
#
#         return {
#             "algo_visualizer": FunctionTool.from_defaults(fn=visualize_algorithm)
#         }
#
#     def _setup_utility_tools(self) -> Dict[str, FunctionTool]:
#         """Utility tools"""
#
#         def concept_combiner(concepts: List[str]) -> str:
#             prompt = f"Explain the relationship between these concepts: {', '.join(concepts)}"
#             return self.llm.complete(prompt).text
#
#         return {
#             "concept_combiner": FunctionTool.from_defaults(fn=concept_combiner)
#         }
#
#     def extract_json_from_markdown(self, markdown_text):
#         """
#         Extract and parse JSON content from a markdown-style code block.
#         Handles formats like ```json ... ```
#         """
#         try:
#             # Extract JSON block using regex
#             match = re.search(r"```json\s*(\{.*?\})\s*```", markdown_text, re.DOTALL)
#             if not match:
#                 raise ValueError("No JSON block found in markdown")
#
#             json_str = match.group(1)
#             return json.loads(json_str)
#         except Exception as e:
#             print(f"[ERROR] Could not parse JSON: {e}")
#             return None
#
#     def determine_tools(self, query: str):
#         """Decide which tools to use based on query"""
#         previous_questions = ""
#         if self.chat_history:
#             previous_questions = "\n".join([msg["content"] for msg in self.chat_history if msg["role"] == "user"][:-1]) \
#                 if self.chat_history else "No previous questions"
#         prompt = f"""Analyze this learning query and select appropriate tools also form the condensed query based on
#                     previous_questions and Query:
#                     Query: {query}
#                     Previous Query: {previous_questions}
#                     Available Tools: {list(self.tools.keys())}
#                     Return dictionary of tool names and condensed query as dictionary in the below format:
#                             ```json
#                             {{
#                               "condensed_query": condensed query considering chat history and user query as string,
#                               "tool_names": tool names as comma-separated list
#                             }}
#                             ```
#                     Do Not add additional text"""
#
#         response = self.llm.complete(prompt).text
#         response = self.extract_json_from_markdown(response)
#         return [t.strip() for t in response['tool_names'].split(",") if t.strip() in self.tools], response["condensed_query"]
#
#     def execute_tools(self, tools: List[str], query: str) -> tuple[str, str]:
#         """Execute multiple tools and combine results"""
#         tool_results = []
#         content_results = []
#
#         for tool in tools:
#             try:
#                 tool_output = self.tools[tool](query)
#                 content = tool_output.content if isinstance(tool_output, ToolOutput) else str(tool_output)
#                 tool_results.append(tool)
#                 content_results.append(content)
#             except Exception as e:
#                 logging.error(f"Tool {tool} failed: {str(e)}")
#                 tool_results.append(tool)
#                 content_results.append(f"Error: {str(e)}")
#
#         if len(tool_results) > 1:
#             combined = "\n\n".join(f"**{t}**:\n{c}" for t, c in zip(tool_results, content_results))
#             explanation = self.tools["concept_combiner"](content_results)
#             return "multiple", f"{combined}\n\n**Combined Analysis**:\n{explanation}"
#         return tool_results[0], content_results[0]
#
#     def process_query(self, query: str) -> tuple[List[Dict[str, str]], str, str]:
#         """Process query and return properly formatted messages"""
#         tools, condensed_query = self.determine_tools(query)
#         logging.info(f"Selected tools: {tools}")
#
#         tool_used, response = self.execute_tools(tools, condensed_query)
#
#         # Format messages for Gradio Chatbot
#         user_msg = {"role": "user", "content": query.title()}
#         assistant_msg = {"role": "assistant", "content": response}
#
#         self.chat_history.extend([user_msg, assistant_msg])
#         if len(self.chat_history) > self.max_history * 2:  # *2 for user+assistant pairs
#             self.chat_history = self.chat_history[-(self.max_history * 2):]
#
#         return self.chat_history, tool_used, response

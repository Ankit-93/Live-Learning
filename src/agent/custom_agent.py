import re
import json
import logging
from typing import List, Dict
from llama_index.core.tools.types import ToolOutput
from src.agent.agenttools import ChatBotFunctionTools
from src.agent.file_operation_tools import FileOperationTools  # New import

class LearningAgent:
    def __init__(self, llm_value: str):
        # Initialize both tool sets
        self.chatbot_tools = ChatBotFunctionTools(llm_type=llm_value)
        self.file_tools = FileOperationTools(llm_type=llm_value)
        self.llm = self.chatbot_tools.generator
        
        # Combine both tool sets
        self.tools = self._get_all_tools()
        
        self.chat_history: List[Dict[str, str]] = []
        self.max_history = 20
        self.uploaded_files_info = []  # Store info about uploaded files

    def _get_all_tools(self):
        """Combine chatbot tools and file operation tools"""
        chat_tools = self.chatbot_tools.get_tools()
        file_tools = self.file_tools.get_tools()
        
        # Prefix file tools to avoid conflicts
        prefixed_file_tools = {}
        for name, tool in file_tools.items():
            prefixed_file_tools[f"file_{name}"] = tool
        
        # Combine both
        all_tools = {}
        all_tools.update(chat_tools)
        all_tools.update(prefixed_file_tools)
        
        logging.info(f"Total tools available: {len(all_tools)}")
        return all_tools

    def extract_json_from_markdown(self, markdown_text: str):
        try:
            match = re.search(r"```json\s*(\{.*?\})\s*```", markdown_text, re.DOTALL)
            if not match:
                # Try without markdown code block
                match = re.search(r"(\{.*?\})", markdown_text, re.DOTALL)
                if not match:
                    raise ValueError("No JSON block found")
            return json.loads(match.group(1))
        except Exception as e:
            logging.error(f"Could not parse JSON: {e}")
            # Return default structure
            return {
                "condensed_query": markdown_text,
                "tool_names": "llm_query"
            }

    def store_uploaded_files(self, files_info: List[Dict]):
        """Store uploaded files in the file tools"""
        if not files_info:
            return
        
        for file_info in files_info:
            filename = file_info.get('name', '')
            content = file_info.get('data', b'')
            file_type = file_info.get('type', '')
            
            if filename and content:
                # Store in file tools
                result = self.file_tools.store_file(filename, content, file_type)
                self.uploaded_files_info.append({
                    'filename': filename,
                    'type': file_type,
                    'size': len(content)
                })
                logging.info(f"Stored file: {filename}")

    def determine_tools(self, query: str):
        previous_questions = "\n".join(
            [msg["content"] for msg in self.chat_history if msg["role"] == "user"]
        ) if self.chat_history else "No previous questions"

        # Check if query involves file operations
        file_keywords = ['excel', 'csv', 'pdf', 'file', 'upload', 'sheet', 'column', 
                        'row', 'sum', 'average', 'mean', 'median', 'filter', 
                        'compare', 'extract', 'graph', 'chart', 'plot', 'visualize']
        
        has_file_context = any(keyword in query.lower() for keyword in file_keywords)
        has_uploaded_files = len(self.uploaded_files_info) > 0
        
        # List available files
        available_files = ""
        if has_uploaded_files:
            available_files = "Available files:\n" + "\n".join([
                f"- {f['filename']} ({f['type']}, {f['size']} bytes)" 
                for f in self.uploaded_files_info
            ])
        
        prompt = f"""Analyze this query and select appropriate tools. Choose multiple if necessary.
                    
                    Query: {query}
                    Previous Conversation: {previous_questions}
                    {available_files}
                    
                    Has file context: {has_file_context}
                    Has uploaded files: {has_uploaded_files}
                    
                    Available Tools: {list(self.tools.keys())}
                    
                    For file-related queries, consider these specific tools:
                    - file_excel_column_operation: For calculations on Excel columns (sum, mean, median, etc.)
                    - file_read_excel_file: To read and analyze Excel files
                    - file_read_pdf_file: To extract text from PDFs
                    - file_compare_pdfs: To compare two PDF files
                    - file_filter_excel_data: To filter Excel data based on conditions
                    - file_csv_operations: For CSV file operations
                    - file_generate_data_visualization: To create charts/graphs
                    
                    For learning/concept queries, use the regular tools.
                    
                    Return JSON in this format:
                    ```json
                    {{
                      "condensed_query": "condensed version of query",
                      "tool_names": "comma-separated list of tool names",
                      "reasoning": "brief explanation of tool selection"
                    }}
                    ```
                    
                    Always select at least 1 tool."""
        
        response = self.llm.complete(prompt)
        try:
            response_text = response.text
        except AttributeError:
            response_text = str(response)
        
        parsed = self.extract_json_from_markdown(response_text)
        condensed_query = parsed.get("condensed_query", query)
        tool_names_str = parsed.get("tool_names", "llm_query")
        
        # Parse tool names
        tools = [t.strip() for t in tool_names_str.split(",") if t.strip() in self.tools]
        
        # If no valid tools found, default to appropriate tool
        if not tools:
            if has_file_context and has_uploaded_files:
                # Check what type of file operation is needed
                if 'pdf' in query.lower() and 'compare' in query.lower():
                    tools = ['file_compare_pdfs']
                elif 'pdf' in query.lower():
                    tools = ['file_read_pdf_file']
                elif any(term in query.lower() for term in ['sum', 'average', 'mean', 'median', 'min', 'max']):
                    tools = ['file_excel_column_operation']
                elif any(term in query.lower() for term in ['filter', 'where', 'condition']):
                    tools = ['file_filter_excel_data']
                elif any(term in query.lower() for term in ['chart', 'graph', 'plot', 'visualize']):
                    tools = ['file_generate_data_visualization']
                else:
                    tools = ['file_read_excel_file']
            else:
                tools = ['llm_query']
        
        logging.info(f"Selected tools: {tools}")
        return tools, condensed_query

    def execute_tools(self, tools: List[str], query: str) -> tuple[str, str]:
        tool_results, content_results = [], []
        
        for tool in tools:
            try:
                logging.info(f"Executing tool: {tool}")
                
                # Special handling for file tools that need additional parameters
                if tool.startswith('file_'):
                    tool_result = self._execute_file_tool(tool.replace('file_', ''), query)
                else:
                    # Regular chatbot tool
                    tool_output = self.tools[tool](query)
                    tool_result = tool_output.content if isinstance(tool_output, ToolOutput) else str(tool_output)
                
                tool_results.append(tool)
                content_results.append(tool_result)
                
            except Exception as e:
                logging.error(f"Tool {tool} failed: {str(e)}")
                tool_results.append(tool)
                content_results.append(f"Error: {str(e)}")

        # Combine results if multiple tools
        if len(tool_results) > 1:
            combined = "\n\n".join(f"**{t}**:\n{c}" for t, c in zip(tool_results, content_results))
            
            # Only use concept_combiner if it's available and not for file operations
            if "concept_combiner" in self.tools and not any(t.startswith('file_') for t in tool_results):
                try:
                    explanation = self.tools["concept_combiner"](content_results)
                    combined += f"\n\n**Combined Analysis**:\n{explanation}"
                except:
                    pass
            
            return "multiple", combined
        
        return tool_results[0], content_results[0]

    def _execute_file_tool(self, tool_name: str, query: str):
        """Execute file operation tools with appropriate parameters"""
        
        # Get list of uploaded files
        available_files = self.file_tools.list_uploaded_files()
        if not available_files:
            return "No files uploaded. Please upload files first."
        
        # Simple heuristic to extract parameters from query
        query_lower = query.lower()
        
        if tool_name == "read_excel_file":
            # Try to find Excel file in query
            excel_files = [f for f in available_files if f['type'] == 'excel']
            if not excel_files:
                return "No Excel files found. Please upload an Excel file first."
            
            filename = excel_files[0]['name']
            return str(self.file_tools.read_excel_file(filename))
        
        elif tool_name == "excel_column_operation":
            # Extract column and operation from query
            excel_files = [f for f in available_files if f['type'] == 'excel']
            if not excel_files:
                return "No Excel files found."
            
            filename = excel_files[0]['name']
            
            # Simple extraction of column name and operation
            operations = {
                'sum': ['sum', 'total', 'add'],
                'mean': ['average', 'mean', 'avg'],
                'median': ['median'],
                'min': ['min', 'minimum', 'smallest'],
                'max': ['max', 'maximum', 'largest'],
                'count': ['count', 'number of']
            }
            
            column = None
            operation = 'sum'  # default
            
            # Try to find column name (capitalized words or quoted strings)
            words = query.split()
            for word in words:
                if word.isupper() or (word[0].isupper() and len(word) > 2):
                    column = word
                    break
            
            # Try to find operation
            for op, keywords in operations.items():
                if any(keyword in query_lower for keyword in keywords):
                    operation = op
                    break
            
            if not column:
                return f"Please specify which column to operate on. Available operations: {', '.join(operations.keys())}"
            
            return str(self.file_tools.excel_column_operation(filename, None, column, operation))
        
        elif tool_name == "compare_pdfs":
            pdf_files = [f for f in available_files if f['type'] == 'pdf']
            if len(pdf_files) < 2:
                return "Need at least 2 PDF files to compare"
            
            filename1 = pdf_files[0]['name']
            filename2 = pdf_files[1]['name']
            return str(self.file_tools.compare_pdfs(filename1, filename2))
        
        elif tool_name == "read_pdf_file":
            pdf_files = [f for f in available_files if f['type'] == 'pdf']
            if not pdf_files:
                return "No PDF files found"
            
            filename = pdf_files[0]['name']
            return str(self.file_tools.read_pdf_file(filename))
        
        elif tool_name == "generate_data_visualization":
            # This would need more sophisticated parameter extraction
            return "Please specify: chart type (bar, line, scatter, histogram, pie), x_column, and optional y_column"
        
        else:
            # For other file tools, just call with query
            file_tool_method = getattr(self.file_tools, tool_name, None)
            if file_tool_method:
                return str(file_tool_method(query))
            
            return f"File tool {tool_name} not found"

    def process_query(self, query: str, uploaded_files: List[Dict] = None) -> tuple[List[Dict[str, str]], str, str]:
        """Process query with optional uploaded files"""
        
        # Store any uploaded files
        if uploaded_files:
            self.store_uploaded_files(uploaded_files)
        
        # Determine and execute tools
        tools, condensed_query = self.determine_tools(query)
        tool_used, response = self.execute_tools(tools, condensed_query)
        
        # Update chat history
        self.chat_history += [
            {"role": "user", "content": query},
            {"role": "assistant", "content": response}
        ]
        
        # Trim history if too long
        self.chat_history = self.chat_history[-(self.max_history * 2):]
        
        return self.chat_history, tool_used, response
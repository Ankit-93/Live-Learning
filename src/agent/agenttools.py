import pandas as pd
import numpy as np
import json
import csv
import PyPDF2
import pdfplumber
import re
from io import BytesIO, StringIO
from typing import Dict, List, Any, Optional, Tuple, Union
import base64
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging
import tempfile
import os
from pathlib import Path
import textwrap

class FileOperationTools:
    """Tools for generic file operations including Excel, PDF, CSV, JSON, etc."""
    
    def __init__(self, llm_type="google"):
        self.llm_type = llm_type
        self.uploaded_files = {}  # Store files by filename
        logging.info(f"FileOperationTools initialized with LLM type: {llm_type}")
    
    def store_file(self, filename: str, file_content: bytes, file_type: str = None) -> str:
        """Store uploaded file in memory"""
        self.uploaded_files[filename] = {
            'content': file_content,
            'type': file_type or self._detect_file_type(filename),
            'size': len(file_content),
            'timestamp': datetime.now().isoformat()
        }
        logging.info(f"File stored: {filename}, type: {file_type}, size: {len(file_content)} bytes")
        return f"File '{filename}' stored successfully"
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from extension"""
        ext = filename.lower().split('.')[-1]
        file_types = {
            'xlsx': 'excel', 'xls': 'excel', 'csv': 'csv',
            'pdf': 'pdf', 'txt': 'text', 'json': 'json',
            'jpg': 'image', 'jpeg': 'image', 'png': 'image',
            'docx': 'document', 'pptx': 'presentation'
        }
        return file_types.get(ext, 'unknown')
    
    def list_uploaded_files(self) -> List[Dict]:
        """List all uploaded files"""
        files = []
        for filename, info in self.uploaded_files.items():
            files.append({
                'name': filename,
                'type': info['type'],
                'size': f"{info['size']:,} bytes",
                'uploaded': info['timestamp']
            })
        return files
    
    def read_excel_file(self, filename: str, sheet_name: str = None) -> Dict:
        """Read Excel file and return DataFrame information"""
        if filename not in self.uploaded_files:
            return {"error": f"File '{filename}' not found"}
        
        try:
            file_content = self.uploaded_files[filename]['content']
            
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(BytesIO(file_content), sheet_name=sheet_name)
            else:
                # Read first sheet
                excel_file = pd.ExcelFile(BytesIO(file_content))
                sheet_name = excel_file.sheet_names[0]
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Prepare summary
            summary = {
                'filename': filename,
                'sheet_name': sheet_name,
                'shape': df.shape,
                'columns': list(df.columns),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'missing_values': df.isnull().sum().to_dict(),
                'head': df.head(5).to_dict(orient='records'),
                'info': f"DataFrame has {df.shape[0]} rows and {df.shape[1]} columns"
            }
            
            # Add basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                summary['statistics'] = df[numeric_cols].describe().to_dict()
            
            return summary
            
        except Exception as e:
            logging.error(f"Error reading Excel file: {e}")
            return {"error": f"Error reading Excel file: {str(e)}"}
    
    def excel_column_operation(self, filename: str, sheet_name: str, column: str, 
                               operation: str) -> Dict:
        """Perform operations on Excel column"""
        if filename not in self.uploaded_files:
            return {"error": f"File '{filename}' not found"}
        
        try:
            file_content = self.uploaded_files[filename]['content']
            
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(BytesIO(file_content), sheet_name=sheet_name)
            else:
                excel_file = pd.ExcelFile(BytesIO(file_content))
                sheet_name = excel_file.sheet_names[0]
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            if column not in df.columns:
                return {"error": f"Column '{column}' not found. Available columns: {list(df.columns)}"}
            
            result = {}
            
            if operation == "sum":
                if pd.api.types.is_numeric_dtype(df[column]):
                    result['sum'] = float(df[column].sum())
                else:
                    result['error'] = f"Cannot sum non-numeric column '{column}'"
            
            elif operation == "mean":
                if pd.api.types.is_numeric_dtype(df[column]):
                    result['mean'] = float(df[column].mean())
                else:
                    result['error'] = f"Cannot calculate mean for non-numeric column '{column}'"
            
            elif operation == "median":
                if pd.api.types.is_numeric_dtype(df[column]):
                    result['median'] = float(df[column].median())
                else:
                    result['error'] = f"Cannot calculate median for non-numeric column '{column}'"
            
            elif operation == "min":
                result['min'] = str(df[column].min())
            
            elif operation == "max":
                result['max'] = str(df[column].max())
            
            elif operation == "count":
                result['count'] = int(df[column].count())
                result['unique_count'] = int(df[column].nunique())
            
            elif operation == "unique_values":
                unique_vals = df[column].unique()
                result['unique_values'] = list(unique_vals)[:50]  # Limit to first 50
                result['count'] = len(unique_vals)
            
            elif operation == "describe":
                if pd.api.types.is_numeric_dtype(df[column]):
                    result['description'] = df[column].describe().to_dict()
                else:
                    result['description'] = {
                        'count': int(df[column].count()),
                        'unique': int(df[column].nunique()),
                        'top': str(df[column].mode().iloc[0]) if not df[column].mode().empty else None,
                        'freq': int(df[column].value_counts().iloc[0]) if not df[column].value_counts().empty else None
                    }
            
            elif operation == "missing":
                missing_count = df[column].isnull().sum()
                result['missing_count'] = int(missing_count)
                result['missing_percentage'] = float((missing_count / len(df)) * 100)
            
            else:
                result['error'] = f"Operation '{operation}' not supported"
            
            # Add column info
            result['column'] = column
            result['dtype'] = str(df[column].dtype)
            result['total_rows'] = len(df)
            
            return result
            
        except Exception as e:
            logging.error(f"Error performing column operation: {e}")
            return {"error": f"Error performing operation: {str(e)}"}
    
    def filter_excel_data(self, filename: str, sheet_name: str, 
                          conditions: List[Dict]) -> Dict:
        """Filter Excel data based on conditions"""
        if filename not in self.uploaded_files:
            return {"error": f"File '{filename}' not found"}
        
        try:
            file_content = self.uploaded_files[filename]['content']
            
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(BytesIO(file_content), sheet_name=sheet_name)
            else:
                excel_file = pd.ExcelFile(BytesIO(file_content))
                sheet_name = excel_file.sheet_names[0]
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Apply conditions
            mask = pd.Series([True] * len(df))
            
            for condition in conditions:
                col = condition.get('column')
                op = condition.get('operator')
                value = condition.get('value')
                
                if col not in df.columns:
                    return {"error": f"Column '{col}' not found"}
                
                if op == "equals":
                    mask &= (df[col] == value)
                elif op == "not_equals":
                    mask &= (df[col] != value)
                elif op == "greater_than":
                    mask &= (df[col] > float(value))
                elif op == "less_than":
                    mask &= (df[col] < float(value))
                elif op == "contains":
                    mask &= df[col].astype(str).str.contains(str(value), case=False, na=False)
                elif op == "starts_with":
                    mask &= df[col].astype(str).str.startswith(str(value), na=False)
                elif op == "ends_with":
                    mask &= df[col].astype(str).str.endswith(str(value), na=False)
                elif op == "in":
                    mask &= df[col].isin(value if isinstance(value, list) else [value])
            
            filtered_df = df[mask]
            
            return {
                'filename': filename,
                'sheet_name': sheet_name,
                'original_rows': len(df),
                'filtered_rows': len(filtered_df),
                'filtered_data': filtered_df.head(20).to_dict(orient='records'),  # Limit to 20 rows
                'conditions': conditions
            }
            
        except Exception as e:
            logging.error(f"Error filtering Excel data: {e}")
            return {"error": f"Error filtering data: {str(e)}"}
    
    def read_pdf_file(self, filename: str) -> Dict:
        """Extract text from PDF file"""
        if filename not in self.uploaded_files:
            return {"error": f"File '{filename}' not found"}
        
        try:
            file_content = self.uploaded_files[filename]['content']
            text = ""
            
            # Try pdfplumber first (better for text extraction)
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                num_pages = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {i+1} ---\n{page_text}\n"
            
            # If pdfplumber didn't extract much, try PyPDF2
            if len(text.strip()) < 100:
                with BytesIO(file_content) as file_stream:
                    pdf_reader = PyPDF2.PdfReader(file_stream)
                    num_pages = len(pdf_reader.pages)
                    for i in range(num_pages):
                        page = pdf_reader.pages[i]
                        page_text = page.extract_text()
                        text += f"\n--- Page {i+1} ---\n{page_text}\n"
            
            # Clean up text
            text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespace
            text = text.strip()
            
            # Extract metadata
            with BytesIO(file_content) as file_stream:
                try:
                    pdf_reader = PyPDF2.PdfReader(file_stream)
                    metadata = pdf_reader.metadata or {}
                except:
                    metadata = {}
            
            return {
                'filename': filename,
                'num_pages': num_pages,
                'text_length': len(text),
                'preview': text[:1000] + "..." if len(text) > 1000 else text,
                'metadata': {str(k): str(v) for k, v in metadata.items()},
                'word_count': len(text.split())
            }
            
        except Exception as e:
            logging.error(f"Error reading PDF file: {e}")
            return {"error": f"Error reading PDF: {str(e)}"}
    
    def compare_pdfs(self, filename1: str, filename2: str) -> Dict:
        """Compare two PDF files"""
        if filename1 not in self.uploaded_files:
            return {"error": f"File '{filename1}' not found"}
        if filename2 not in self.uploaded_files:
            return {"error": f"File '{filename2}' not found"}
        
        try:
            # Extract text from both PDFs
            pdf1_result = self.read_pdf_file(filename1)
            pdf2_result = self.read_pdf_file(filename2)
            
            if 'error' in pdf1_result:
                return pdf1_result
            if 'error' in pdf2_result:
                return pdf2_result
            
            # Get full text (need to read again for comparison)
            file_content1 = self.uploaded_files[filename1]['content']
            file_content2 = self.uploaded_files[filename2]['content']
            
            text1 = ""
            text2 = ""
            
            # Extract text from both PDFs using pdfplumber
            with pdfplumber.open(BytesIO(file_content1)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text1 += page_text + "\n"
            
            with pdfplumber.open(BytesIO(file_content2)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text2 += page_text + "\n"
            
            # Clean texts
            text1 = re.sub(r'\s+', ' ', text1).strip()
            text2 = re.sub(r'\s+', ' ', text2).strip()
            
            # Calculate similarity (simple approach)
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            common_words = words1.intersection(words2)
            all_words = words1.union(words2)
            
            similarity = len(common_words) / len(all_words) if all_words else 0
            
            # Find differences
            unique_to_pdf1 = words1 - words2
            unique_to_pdf2 = words2 - words1
            
            # Page count comparison
            with BytesIO(file_content1) as f1, BytesIO(file_content2) as f2:
                pdf1 = PyPDF2.PdfReader(f1)
                pdf2 = PyPDF2.PdfReader(f2)
                pages1 = len(pdf1.pages)
                pages2 = len(pdf2.pages)
            
            return {
                'similarity_percentage': round(similarity * 100, 2),
                'file1': {
                    'name': filename1,
                    'pages': pages1,
                    'word_count': len(text1.split()),
                    'char_count': len(text1)
                },
                'file2': {
                    'name': filename2,
                    'pages': pages2,
                    'word_count': len(text2.split()),
                    'char_count': len(text2)
                },
                'common_words_count': len(common_words),
                'unique_to_file1_count': len(unique_to_pdf1),
                'unique_to_file2_count': len(unique_to_pdf2),
                'page_difference': abs(pages1 - pages2),
                'word_difference': abs(len(text1.split()) - len(text2.split())),
                'unique_to_file1_preview': list(unique_to_pdf1)[:10],
                'unique_to_file2_preview': list(unique_to_pdf2)[:10]
            }
            
        except Exception as e:
            logging.error(f"Error comparing PDFs: {e}")
            return {"error": f"Error comparing PDFs: {str(e)}"}
    
    def extract_pdf_sections(self, filename: str, search_terms: List[str]) -> Dict:
        """Extract specific sections from PDF based on search terms"""
        if filename not in self.uploaded_files:
            return {"error": f"File '{filename}' not found"}
        
        try:
            file_content = self.uploaded_files[filename]['content']
            text = ""
            
            # Extract text with page numbers
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                pages_text = []
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append({
                            'page': i + 1,
                            'text': page_text
                        })
                        text += f"PAGE {i+1}:\n{page_text}\n\n"
            
            # Search for terms
            results = {}
            for term in search_terms:
                term_lower = term.lower()
                matches = []
                
                for page_info in pages_text:
                    page_text_lower = page_info['text'].lower()
                    if term_lower in page_text_lower:
                        # Find context around the term
                        idx = page_text_lower.find(term_lower)
                        start = max(0, idx - 200)
                        end = min(len(page_info['text']), idx + len(term) + 200)
                        context = page_info['text'][start:end]
                        
                        # Highlight the term
                        context = context.replace(term, f"**{term}**")
                        
                        matches.append({
                            'page': page_info['page'],
                            'context': context,
                            'position': idx
                        })
                
                results[term] = {
                    'found': len(matches) > 0,
                    'count': len(matches),
                    'matches': matches[:5]  # Limit to 5 matches per term
                }
            
            return {
                'filename': filename,
                'search_results': results,
                'total_pages': len(pages_text),
                'search_terms': search_terms
            }
            
        except Exception as e:
            logging.error(f"Error extracting PDF sections: {e}")
            return {"error": f"Error extracting sections: {str(e)}"}
    
    def csv_operations(self, filename: str, operation: str, **kwargs) -> Dict:
        """Perform operations on CSV files"""
        if filename not in self.uploaded_files:
            return {"error": f"File '{filename}' not found"}
        
        try:
            file_content = self.uploaded_files[filename]['content']
            
            # Read CSV
            try:
                df = pd.read_csv(BytesIO(file_content))
            except:
                # Try with different encoding
                text_content = file_content.decode('utf-8', errors='ignore')
                df = pd.read_csv(StringIO(text_content))
            
            if operation == "summary":
                return {
                    'filename': filename,
                    'shape': df.shape,
                    'columns': list(df.columns),
                    'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                    'head': df.head().to_dict(orient='records'),
                    'missing_values': df.isnull().sum().to_dict()
                }
            
            elif operation == "filter":
                column = kwargs.get('column')
                value = kwargs.get('value')
                operator = kwargs.get('operator', 'equals')
                
                if column not in df.columns:
                    return {"error": f"Column '{column}' not found"}
                
                if operator == "equals":
                    filtered = df[df[column] == value]
                elif operator == "contains":
                    filtered = df[df[column].astype(str).str.contains(str(value), na=False)]
                elif operator == "greater_than":
                    filtered = df[df[column] > float(value)]
                elif operator == "less_than":
                    filtered = df[df[column] < float(value)]
                else:
                    return {"error": f"Operator '{operator}' not supported"}
                
                return {
                    'original_rows': len(df),
                    'filtered_rows': len(filtered),
                    'filtered_data': filtered.head(20).to_dict(orient='records')
                }
            
            elif operation == "aggregate":
                group_by = kwargs.get('group_by')
                aggregate_col = kwargs.get('aggregate_col')
                agg_func = kwargs.get('agg_func', 'sum')
                
                if group_by not in df.columns:
                    return {"error": f"Group by column '{group_by}' not found"}
                if aggregate_col not in df.columns:
                    return {"error": f"Aggregate column '{aggregate_col}' not found"}
                
                if agg_func == "sum":
                    result = df.groupby(group_by)[aggregate_col].sum()
                elif agg_func == "mean":
                    result = df.groupby(group_by)[aggregate_col].mean()
                elif agg_func == "count":
                    result = df.groupby(group_by)[aggregate_col].count()
                elif agg_func == "max":
                    result = df.groupby(group_by)[aggregate_col].max()
                elif agg_func == "min":
                    result = df.groupby(group_by)[aggregate_col].min()
                else:
                    return {"error": f"Aggregation function '{agg_func}' not supported"}
                
                return {
                    'aggregation': result.reset_index().to_dict(orient='records'),
                    'group_by': group_by,
                    'aggregate_column': aggregate_col,
                    'function': agg_func
                }
            
            else:
                return {"error": f"Operation '{operation}' not supported"}
            
        except Exception as e:
            logging.error(f"Error performing CSV operation: {e}")
            return {"error": f"Error performing CSV operation: {str(e)}"}
    
    def json_operations(self, filename: str, operation: str, **kwargs) -> Dict:
        """Perform operations on JSON files"""
        if filename not in self.uploaded_files:
            return {"error": f"File '{filename}' not found"}
        
        try:
            file_content = self.uploaded_files[filename]['content']
            data = json.loads(file_content)
            
            if operation == "keys":
                def get_keys(obj, path=""):
                    keys = []
                    if isinstance(obj, dict):
                        for key in obj.keys():
                            new_path = f"{path}.{key}" if path else key
                            keys.append(new_path)
                            keys.extend(get_keys(obj[key], new_path))
                    elif isinstance(obj, list) and len(obj) > 0:
                        keys.extend(get_keys(obj[0], f"{path}[0]"))
                    return keys
                
                return {
                    'filename': filename,
                    'keys': get_keys(data),
                    'structure_type': type(data).__name__
                }
            
            elif operation == "extract":
                path = kwargs.get('path')
                if not path:
                    return {"error": "Path parameter required"}
                
                # Navigate to path
                parts = path.split('.')
                current = data
                for part in parts:
                    if part.endswith(']'):
                        # Handle array indexing
                        key = part[:part.index('[')]
                        idx = int(part[part.index('[')+1:part.index(']')])
                        current = current[key][idx]
                    else:
                        current = current.get(part)
                        if current is None:
                            return {"error": f"Path '{path}' not found"}
                
                return {
                    'path': path,
                    'value': current,
                    'type': type(current).__name__
                }
            
            elif operation == "count":
                def count_items(obj):
                    if isinstance(obj, dict):
                        return sum(count_items(v) for v in obj.values())
                    elif isinstance(obj, list):
                        return sum(count_items(item) for item in obj)
                    else:
                        return 1
                
                return {
                    'total_items': count_items(data),
                    'structure_type': type(data).__name__
                }
            
            else:
                return {"error": f"Operation '{operation}' not supported"}
            
        except Exception as e:
            logging.error(f"Error performing JSON operation: {e}")
            return {"error": f"Error performing JSON operation: {str(e)}"}
    
    def text_operations(self, filename: str, operation: str, **kwargs) -> Dict:
        """Perform operations on text files"""
        if filename not in self.uploaded_files:
            return {"error": f"File '{filename}' not found"}
        
        try:
            file_content = self.uploaded_files[filename]['content']
            text = file_content.decode('utf-8', errors='ignore')
            
            if operation == "word_count":
                words = text.split()
                unique_words = set(words)
                
                return {
                    'filename': filename,
                    'total_words': len(words),
                    'unique_words': len(unique_words),
                    'characters': len(text),
                    'lines': text.count('\n') + 1
                }
            
            elif operation == "search":
                search_term = kwargs.get('term')
                if not search_term:
                    return {"error": "Search term required"}
                
                lines = text.split('\n')
                matches = []
                
                for i, line in enumerate(lines):
                    if search_term.lower() in line.lower():
                        matches.append({
                            'line_number': i + 1,
                            'line': line.strip(),
                            'context': '...' + line[max(0, line.lower().find(search_term.lower()) - 50):
                                                    line.lower().find(search_term.lower()) + len(search_term) + 50] + '...'
                        })
                
                return {
                    'filename': filename,
                    'search_term': search_term,
                    'total_matches': len(matches),
                    'matches': matches[:20]  # Limit to 20 matches
                }
            
            elif operation == "summary":
                # Simple text summary (first 500 chars)
                return {
                    'filename': filename,
                    'preview': text[:500] + "..." if len(text) > 500 else text,
                    'total_length': len(text),
                    'word_count': len(text.split())
                }
            
            else:
                return {"error": f"Operation '{operation}' not supported"}
            
        except Exception as e:
            logging.error(f"Error performing text operation: {e}")
            return {"error": f"Error performing text operation: {str(e)}"}
    
    def generate_data_visualization(self, filename: str, chart_type: str, 
                                    x_column: str, y_column: str = None) -> Dict:
        """Generate data visualization from file"""
        if filename not in self.uploaded_files:
            return {"error": f"File '{filename}' not found"}
        
        try:
            file_content = self.uploaded_files[filename]['content']
            file_type = self.uploaded_files[filename]['type']
            
            # Read data based on file type
            if file_type == 'excel':
                df = pd.read_excel(BytesIO(file_content))
            elif file_type == 'csv':
                df = pd.read_csv(BytesIO(file_content))
            else:
                return {"error": f"Visualization not supported for {file_type} files"}
            
            # Check columns exist
            if x_column not in df.columns:
                return {"error": f"Column '{x_column}' not found"}
            if y_column and y_column not in df.columns:
                return {"error": f"Column '{y_column}' not found"}
            
            plt.figure(figsize=(10, 6))
            
            if chart_type == "bar":
                if y_column:
                    # Group by x_column and aggregate y_column
                    data = df.groupby(x_column)[y_column].mean().reset_index()
                    plt.bar(data[x_column], data[y_column])
                else:
                    # Count plot
                    counts = df[x_column].value_counts().head(20)  # Limit to top 20
                    plt.bar(counts.index, counts.values)
                plt.xticks(rotation=45)
                plt.xlabel(x_column)
                plt.ylabel(y_column if y_column else 'Count')
                plt.title(f"{chart_type.title()} Chart: {x_column} vs {y_column if y_column else 'Count'}")
            
            elif chart_type == "line":
                if not y_column:
                    return {"error": "Line chart requires y_column"}
                # Sort by x_column for line chart
                df_sorted = df.sort_values(x_column)
                plt.plot(df_sorted[x_column], df_sorted[y_column], marker='o')
                plt.xlabel(x_column)
                plt.ylabel(y_column)
                plt.title(f"Line Chart: {x_column} vs {y_column}")
            
            elif chart_type == "scatter":
                if not y_column:
                    return {"error": "Scatter plot requires y_column"}
                plt.scatter(df[x_column], df[y_column])
                plt.xlabel(x_column)
                plt.ylabel(y_column)
                plt.title(f"Scatter Plot: {x_column} vs {y_column}")
            
            elif chart_type == "histogram":
                plt.hist(df[x_column].dropna(), bins=20, edgecolor='black')
                plt.xlabel(x_column)
                plt.ylabel('Frequency')
                plt.title(f"Histogram of {x_column}")
            
            elif chart_type == "pie":
                counts = df[x_column].value_counts().head(10)  # Limit to top 10
                plt.pie(counts.values, labels=counts.index, autopct='%1.1f%%')
                plt.title(f"Pie Chart: Distribution of {x_column}")
            
            else:
                return {"error": f"Chart type '{chart_type}' not supported"}
            
            plt.tight_layout()
            
            # Save plot to bytes
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            plt.close()
            buf.seek(0)
            
            # Encode image to base64
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            
            return {
                'filename': filename,
                'chart_type': chart_type,
                'x_column': x_column,
                'y_column': y_column,
                'image_base64': img_base64,
                'data_preview': df[[x_column, y_column] if y_column else [x_column]].head(10).to_dict(orient='records')
            }
            
        except Exception as e:
            logging.error(f"Error generating visualization: {e}")
            return {"error": f"Error generating visualization: {str(e)}"}
    
    def get_tools(self):
        """Return all available tools"""
        return {
            "store_file": self.store_file,
            "list_uploaded_files": self.list_uploaded_files,
            "read_excel_file": self.read_excel_file,
            "excel_column_operation": self.excel_column_operation,
            "filter_excel_data": self.filter_excel_data,
            "read_pdf_file": self.read_pdf_file,
            "compare_pdfs": self.compare_pdfs,
            "extract_pdf_sections": self.extract_pdf_sections,
            "csv_operations": self.csv_operations,
            "json_operations": self.json_operations,
            "text_operations": self.text_operations,
            "generate_data_visualization": self.generate_data_visualization
        }
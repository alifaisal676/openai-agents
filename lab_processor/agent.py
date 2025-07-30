
from langsmith import traceable
"""
Agent for processing a single lab report image into structured data using OpenAI tools.
"""
import json
import time
import logging
from pathlib import Path
from openai import OpenAI

from .config import GROQ_API_KEY, GROQ_BASE_URL, MODEL_NAME, MAX_TOKENS, TIMEOUT, TEMPERATURE, SYSTEM_PROMPT, MAX_ITERATIONS,LANGCHAIN_API_KEY,LANGCHAIN_PROJECT,LANGCHAIN_TRACING_V2
from .tools import extract_text_from_image, structure_text_data, validate_structured_data, save_ocr_output, save_structured_data







logger = logging.getLogger(__name__)
client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


class LabReportAgent:
    
    def __init__(self):
        self.tools = [
            {"type": "function", "function": {"name": "extract_text", "description": "Extract text from lab report image", "parameters": {"type": "object", "properties": {"image_path": {"type": "string", "description": "Path to image file"}}, "required": ["image_path"]}}},
            {"type": "function", "function": {"name": "structure_data", "description": "Convert text to structured JSON", "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Raw text to structure"}}, "required": ["text"]}}},
            {"type": "function", "function": {"name": "validate_data", "description": "Validate structured data", "parameters": {"type": "object", "properties": {"data": {"type": "object", "description": "Data to validate"}}, "required": ["data"]}}}
        ]
        self.tool_functions = {
            "extract_text": extract_text_from_image,
            "structure_data": structure_text_data,
            "validate_data": validate_structured_data
        }



    @traceable(name="process_image")
    def process_image(self, image_path: str, output_file: str) -> dict:
        
        start = time.time()
        image_name = Path(image_path).name
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Process this lab report: {image_path}"}
        ]
        final_data = None
        for i in range(MAX_ITERATIONS):
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    max_tokens=MAX_TOKENS,
                    timeout=TIMEOUT,
                    temperature=TEMPERATURE
                )
                msg = response.choices[0].message
                self._add_message(messages, msg)
                if msg.tool_calls:
                    final_data = self._handle_tools(msg.tool_calls, messages, image_path, output_file)
                    if final_data:
                        break
                else:
                    break
            except Exception as e:
                logger.error(f"Agent iteration {i+1} failed: {e}")
                if i == MAX_ITERATIONS - 1:
                    return self._fail_result(image_name, str(e), start)
        duration = time.time() - start
        if final_data:
            return {
                "status": "success",
                "image": image_name,
                "patient_name": final_data.get("patient_name", "Unknown"),
                "output_file": Path(output_file).name,
                "duration": duration,
                "data": final_data
            }
        return self._fail_result(image_name, "Processing incomplete", start)
    
    

    def _add_message(self, messages, msg):
        entry = {"role": msg.role, "content": msg.content}
        if msg.tool_calls:
            entry["tool_calls"] = [
                {"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        messages.append(entry)



    def _handle_tools(self, tool_calls, messages, image_path, output_file):
        final_data = None
        output_dir = Path(output_file).parent
        image_stem = Path(image_path).stem
        for tool_call in tool_calls:
            fname = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            try:
                if fname in self.tool_functions:
                    result = self.tool_functions[fname](**args)
                    if fname == "extract_text":
                        save_ocr_output(result, output_dir, image_stem)
                    elif fname == "validate_data":
                        save_structured_data(result, Path(output_file))
                        final_data = result
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": fname,
                        "content": json.dumps(result) if isinstance(result, dict) else str(result)
                    })
                else:
                    self._add_tool_error(messages, tool_call.id, fname, "Unknown tool")
            except Exception as e:
                self._add_tool_error(messages, tool_call.id, fname, str(e))
        return final_data
    
    

    def _add_tool_error(self, messages, tool_call_id, fname, error):
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": fname,
            "content": f"Error: {error}"
        })
        
        

    def _fail_result(self, image_name, error, start):
        return {
            "status": "failed",
            "image": image_name,
            "error": error,
            "duration": time.time() - start
        }

"""
Agent-based processor for individual lab reports.
"""
import json
import time
import logging
from pathlib import Path
from openai import OpenAI

from .config import GROQ_API_KEY, GROQ_BASE_URL, MODEL_NAME, MAX_TOKENS, TIMEOUT, TEMPERATURE, SYSTEM_PROMPT, MAX_ITERATIONS
from .tools import extract_text_from_image, structure_text_data, validate_structured_data, save_ocr_output, save_structured_data

logger = logging.getLogger(__name__)
client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)

class LabReportAgent:
    """Agent for processing individual lab reports using OpenAI SDK tools."""
    
    def __init__(self):
        self.tools = self._setup_tools()
        self.tool_functions = {
            "extract_text": extract_text_from_image,
            "structure_data": structure_text_data,
            "validate_data": validate_structured_data
        }
    
    def _setup_tools(self):
        """Define available tools for the agent."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "extract_text",
                    "description": "Extract text from lab report image",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "image_path": {"type": "string", "description": "Path to image file"}
                        },
                        "required": ["image_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "structure_data",
                    "description": "Convert text to structured JSON",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Raw text to structure"}
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_data",
                    "description": "Validate structured data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data": {"type": "object", "description": "Data to validate"}
                        },
                        "required": ["data"]
                    }
                }
            }
        ]
    
    def process_image(self, image_path: str, output_file: str) -> dict:
        """Process a single lab report image."""
        start_time = time.time()
        image_name = Path(image_path).name
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Process this lab report: {image_path}"}
        ]
        
        final_data = None
        
        for iteration in range(MAX_ITERATIONS):
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
                
                message = response.choices[0].message
                self._add_message_to_conversation(messages, message)
                
                if message.tool_calls:
                    final_data = self._handle_tool_calls(
                        message.tool_calls, messages, image_path, output_file
                    )
                    if final_data:
                        break
                else:
                    # Agent finished without tool calls
                    break
                    
            except Exception as e:
                logger.error(f"Agent iteration {iteration + 1} failed: {e}")
                if iteration == MAX_ITERATIONS - 1:
                    return self._create_error_result(image_name, str(e), start_time)
        
        duration = time.time() - start_time
        
        if final_data:
            return {
                "status": "success",
                "image": image_name,
                "patient_name": final_data.get("patient_name", "Unknown"),
                "output_file": Path(output_file).name,
                "duration": duration,
                "data": final_data
            }
        else:
            return self._create_error_result(image_name, "Processing incomplete", start_time)
    
    def _add_message_to_conversation(self, messages: list, message):
        """Add agent message to conversation history."""
        msg_dict = {"role": message.role, "content": message.content}
        
        if message.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                }
                for tc in message.tool_calls
            ]
        
        messages.append(msg_dict)
    
    def _handle_tool_calls(self, tool_calls, messages, image_path, output_file):
        """Execute tool calls and handle results."""
        final_data = None
        output_dir = Path(output_file).parent
        image_stem = Path(image_path).stem
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            try:
                if function_name in self.tool_functions:
                    result = self.tool_functions[function_name](**args)
                    
                    # Handle special cases
                    if function_name == "extract_text":
                        save_ocr_output(result, output_dir, image_stem)
                    elif function_name == "validate_data":
                        save_structured_data(result, Path(output_file))
                        final_data = result
                    
                    # Add result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(result) if isinstance(result, dict) else str(result)
                    })
                else:
                    self._add_error_response(messages, tool_call.id, function_name, "Unknown tool")
                    
            except Exception as e:
                self._add_error_response(messages, tool_call.id, function_name, str(e))
        
        return final_data
    
    def _add_error_response(self, messages, tool_call_id, function_name, error):
        """Add error response to conversation."""
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": function_name,
            "content": f"Error: {error}"
        })
    
    def _create_error_result(self, image_name, error, start_time):
        """Create error result dictionary."""
        return {
            "status": "failed",
            "image": image_name,
            "error": error,
            "duration": time.time() - start_time
        }

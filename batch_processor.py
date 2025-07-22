"""
Batch Lab Report Processor
Processes multiple lab report images using the same OpenAI SDK multi-agent approach as structure2.py.

Architecture: Same as structure2.py - OpenAI SDK Agent with tools for each image
- Uses agent conversation loop with tool calling
- OCR → LLM Structure → Validation workflow via agent tools
- Maintains consistent agent architecture across single and batch processing
"""

import json
import os
import logging
import time
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Optional
from pydantic import BaseModel, ValidationError
from pathlib import Path

# --- Configure Logging ---
logging.basicConfig(
    level=logging.WARNING,  # Reduced logging level
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Only console output, no file logging
    ]
)
logger = logging.getLogger(__name__)

# --- Load API Key and Set Up Client ---
load_dotenv()
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# --- Define Pydantic Models (Same as structure2.py) ---
class LabTest(BaseModel):
    test_name: str
    value: Optional[str]  # Changed to str to handle text values like "Present", "Absent", "Clear"
    unit: str
    reference_range: str

class LabReport(BaseModel):
    patient_name: str
    age: str
    gender: str
    doctor_name: str
    date: str
    comments: str
    test_results: List[LabTest]

# --- Tool: OCR Lab Report (Same as structure2.py) ---
def ocr_lab_report_image(image_path: str) -> str:
    start_time = time.time()
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        duration = time.time() - start_time
        logger.warning(f"OCR completed in {duration:.1f}s. Text length: {len(text)} chars")
        return text
    except Exception as e:
        logger.error(f"OCR failed: {str(e)}")
        raise

# --- Tool: Structure Using LLM (Same as structure2.py) ---
def llm_structure_lab_report_text(lab_report_text: str) -> dict:
    start_time = time.time()
    try:
        system_prompt = (
            "Extract lab report data as JSON: patient_name, age, gender, doctor_name, date, comments, "
            "test_results (list with test_name, value, unit, reference_range). "
            "Keep 'value' as string for qualitative results (Present/Absent/Clear). "
            "Use empty string for missing fields. Return only JSON."
        )
        user_prompt = f"Extract JSON from:\n{lab_report_text}"
        
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800,  # Reduced for efficiency
            timeout=10,  # Faster timeout
            temperature=0.1  # More deterministic
        )
        
        duration = time.time() - start_time
        import re
        match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
        if match:
            json_str = match.group(0)
            result = json.loads(json_str)
            logger.warning(f"LLM structuring completed in {duration:.1f}s")
            return result
        else:
            logger.error("Could not extract JSON from LLM response")
            return {"error": "Could not extract JSON", "raw": response.choices[0].message.content}
            
    except Exception as e:
        logger.error(f"LLM structuring failed: {str(e)}")
        return {"error": f"LLM structuring failed: {str(e)}"}

# --- Tool: Post-process and Validate (Same as structure2.py) ---
def postprocess_lab_report_data(structured_data: dict) -> dict:
    try:
        validated = LabReport(**structured_data)
        result = validated.model_dump()
        logger.warning("Data validation successful")
        return result
    except ValidationError as ve:
        logger.error(f"Validation failed, using original data: {len(ve.errors())} errors")
        return structured_data  # Return original data instead of error
    except Exception as e:
        logger.error(f"Post-processing failed: {str(e)}")
        return structured_data

# --- Duplicate Detection Helper ---
def is_already_processed(image_path: str, output_dir: Path) -> bool:
    """
    Check if an image has already been processed to avoid duplicates.
    Returns True if both structured JSON and OCR files exist.
    """
    image_name = Path(image_path).stem
    
    # Check for structured JSON file
    json_file = output_dir / f"{image_name}_structured.json"
    
    # Check for OCR file in ocr_outputs subdirectory
    ocr_dir = output_dir / "ocr_outputs"
    ocr_file = ocr_dir / f"{image_name}_ocr.txt"
    
    if json_file.exists() and ocr_file.exists():
        logger.warning(f"⏭️  Skipping {image_name} - already processed (found {json_file.name} and ocr_outputs/{ocr_file.name})")
        return True
    elif json_file.exists():
        logger.warning(f"⚠️  Partial processing found for {image_name} - JSON exists but OCR missing, will reprocess")
        return False
    elif ocr_file.exists():
        logger.warning(f"⚠️  Partial processing found for {image_name} - OCR exists but JSON missing, will reprocess")
        return False
    else:
        return False

# --- Single Image Agent Processor (Same logic as structure2.py but with custom output) ---
def process_single_image_with_agent(image_path: str, output_file: str) -> dict:
    """Process a single image using the same OpenAI SDK agent approach as structure2.py"""
    overall_start_time = time.time()
    image_name = Path(image_path).name
    
    logger.warning(f"Starting agent processing for: {image_name}")
    
    # Set up agent conversation (Same as structure2.py)
    messages = [
        {"role": "system", "content": (
            "You are an efficient medical lab report processing assistant. You have 3 tools:\n"
            "1. ocr_lab_report_image - Extract text from images\n"
            "2. llm_structure_lab_report_text - Convert text to structured JSON\n"
            "3. postprocess_lab_report_data - Validate data\n\n"
            "CRITICAL: Work efficiently. For images: OCR→structure→validate in sequence. "
            "Call each tool exactly once. No redundant calls. Process quickly and decisively."
        )}
    ]
    
    messages.append({"role": "user", "content": f"Process this lab report image: {image_path}"})

    # Tool definitions for the agent (Same as structure2.py)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "ocr_lab_report_image",
                "description": "Extract text from a lab report image using OCR",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to the lab report image file"
                        }
                    },
                    "required": ["image_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "llm_structure_lab_report_text",
                "description": "Convert raw lab report text into structured JSON format",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab_report_text": {
                            "type": "string",
                            "description": "Raw text content of the lab report"
                        }
                    },
                    "required": ["lab_report_text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "postprocess_lab_report_data",
                "description": "Validate and clean structured lab report data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "structured_data": {
                            "type": "object",
                            "description": "The structured lab report data to validate"
                        }
                    },
                    "required": ["structured_data"]
                }
            }
        }
    ]

    tool_functions = {
        "ocr_lab_report_image": ocr_lab_report_image,
        "llm_structure_lab_report_text": llm_structure_lab_report_text,
        "postprocess_lab_report_data": postprocess_lab_report_data
    }

    # Agent conversation loop (Same as structure2.py)
    max_iterations = 3  # Reduced from 5 for efficiency
    iteration = 0
    final_data = None
    
    while iteration < max_iterations:
        iteration += 1
        
        try:
            # Get agent response
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=800,  # Further reduced for efficiency
                timeout=10,  # Reduced timeout
                temperature=0.1  # Lower temperature for more focused responses
            )
            
            message = response.choices[0].message
            
            # Add message to conversation (but handle the object properly)
            message_dict = {
                "role": message.role,
                "content": message.content
            }
            if message.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            messages.append(message_dict)
            
            # Check if agent wants to use tools
            if message.tool_calls:
                logger.warning(f"Agent calling {len(message.tool_calls)} tool(s) for {image_name}")
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool
                    if function_name in tool_functions:
                        try:
                            result = tool_functions[function_name](**function_args)
                            
                            # Handle special cases for file saving
                            if function_name == "ocr_lab_report_image":
                                # Save OCR outputs to organized ocr_outputs subdirectory
                                output_dir = Path(output_file).parent
                                ocr_dir = output_dir / "ocr_outputs"
                                ocr_dir.mkdir(exist_ok=True)
                                
                                ocr_filename = Path(output_file).name.replace('_structured.json', '_ocr.txt')
                                ocr_output_file = ocr_dir / ocr_filename
                                
                                with open(ocr_output_file, "w", encoding="utf-8") as f:
                                    f.write(result)
                            
                            # If this is the final validation step, save the result immediately
                            if function_name == "postprocess_lab_report_data":
                                try:
                                    with open(output_file, "w", encoding="utf-8") as f:
                                        json.dump(result, f, indent=2)
                                    logger.warning(f"Final data saved to {output_file}")
                                    final_data = result
                                    
                                    total_time = time.time() - overall_start_time
                                    logger.warning(f"Agent processing completed for {image_name} in {total_time:.1f}s")
                                    
                                    return {
                                        "status": "success",
                                        "image": image_name,
                                        "patient_name": result.get("patient_name", "Unknown"),
                                        "output_file": Path(output_file).name,
                                        "ocr_file": f"ocr_outputs/{Path(ocr_output_file).name}",
                                        "duration": total_time,
                                        "final_data": result
                                    }
                                except Exception as save_error:
                                    logger.error(f"Failed to save data for {image_name}: {str(save_error)}")
                            
                            # Add tool result to conversation
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": json.dumps(result) if isinstance(result, dict) else str(result)
                            })
                            
                        except Exception as e:
                            logger.error(f"Tool {function_name} failed for {image_name}: {str(e)}")
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": f"Error: {str(e)}"
                            })
                    else:
                        logger.error(f"Unknown tool: {function_name}")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": "Error: Unknown tool"
                        })
            
            else:
                # Agent provided final response without tool calls
                total_time = time.time() - overall_start_time
                
                # Try to extract structured data from conversation if not already saved
                if final_data is None:
                    for msg in reversed(messages):
                        if (isinstance(msg, dict) and 
                            msg.get("role") == "tool" and 
                            msg.get("name") == "postprocess_lab_report_data" and 
                            not str(msg.get("content", "")).startswith("Error:")):
                            try:
                                structured_data = json.loads(msg["content"])
                                with open(output_file, "w", encoding="utf-8") as f:
                                    json.dump(structured_data, f, indent=2)
                                final_data = structured_data
                                break
                            except:
                                continue
                
                logger.warning(f"Agent processing completed for {image_name} in {total_time:.1f}s")
                
                return {
                    "status": "success" if final_data else "partial",
                    "image": image_name,
                    "patient_name": final_data.get("patient_name", "Unknown") if final_data else "Unknown",
                    "output_file": Path(output_file).name,
                    "duration": total_time,
                    "final_data": final_data,
                    "agent_response": message.content
                }
                
        except Exception as e:
            logger.error(f"Agent iteration {iteration} failed for {image_name}: {str(e)}")
            if iteration >= max_iterations:
                total_time = time.time() - overall_start_time
                return {
                    "status": "failed",
                    "image": image_name,
                    "error": str(e),
                    "duration": total_time
                }
            continue
    
    # If we reach here, max iterations exceeded
    total_time = time.time() - overall_start_time
    return {
        "status": "incomplete",
        "image": image_name,
        "duration": total_time,
        "message": f"Processing incomplete after {max_iterations} iterations"
    }

# --- Batch Processing Function ---
def batch_process_lab_reports(input_dir: str, output_dir: str) -> dict:
    """
    Process multiple lab report images using OpenAI SDK multi-agent approach.
    Each image gets the full agent conversation loop with tools.
    """
    batch_start_time = time.time()
    
    print("\n" + "="*70)
    print("🤖 BATCH LAB REPORT PROCESSOR - OpenAI SDK Multi-Agent Approach")
    print("="*70)
    print(f"📁 Input Directory: {input_dir}")
    print(f"💾 Output Directory: {output_dir}")
    
    # Setup directories
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Find all image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
    image_files = [
        f for f in input_path.glob('*') 
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    print(f"🔍 Found {len(image_files)} image files to process")
    print("="*70)
    
    # Process each image using the agent approach
    results = {
        'successful_processes': [],
        'failed_processes': [],
        'skipped_processes': []  # Track skipped files
    }
    
    for i, image_file in enumerate(image_files, 1):
        print(f"\n🔄 Processing {i}/{len(image_files)}: {image_file.name}")
        print("-" * 50)
        
        # Generate output file name
        output_file = output_path / f"{image_file.stem}_structured.json"
        
        # Check if already processed (duplicate detection)
        if is_already_processed(str(image_file), output_path):
            # Create a skipped result entry
            skipped_result = {
                "status": "skipped",
                "image": image_file.name,
                "reason": "already_processed",
                "output_file": output_file.name,
                "ocr_file": f"ocr_outputs/{image_file.stem}_ocr.txt"
            }
            results['skipped_processes'].append(skipped_result)
            print(f"⏭️  SKIPPED: Already processed - 0.00s")
            continue
        
        # Process with agent
        result = process_single_image_with_agent(str(image_file), str(output_file))
        
        if result["status"] == "success":
            results['successful_processes'].append(result)
            print(f"✅ SUCCESS: {result['patient_name']} - {result['duration']:.2f}s")
        else:
            results['failed_processes'].append(result)
            print(f"❌ FAILED: {result.get('error', 'Unknown error')} - {result['duration']:.2f}s")
    
    # Calculate batch statistics
    total_duration = time.time() - batch_start_time
    successful_count = len(results['successful_processes'])
    failed_count = len(results['failed_processes'])
    skipped_count = len(results['skipped_processes'])
    processed_count = successful_count + failed_count  # Actually processed (not skipped)
    
    batch_summary = {
        'processing_summary': {
            'total_images': len(image_files),
            'successful': successful_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'actually_processed': processed_count,
            'total_duration': f"{total_duration:.1f}s",
            'average_per_image': f"{total_duration/max(processed_count, 1):.1f}s",
            'average_per_processed': f"{total_duration/max(processed_count, 1):.1f}s"
        }
    }
    
    # Combine results
    final_results = {**batch_summary, **results}
    
    # Save processing summary
    summary_file = output_path / "processing_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    # Print final summary
    print("\n" + "="*70)
    print("📊 BATCH PROCESSING SUMMARY")
    print("="*70)
    print(f"📁 Total Images Found: {len(image_files)}")
    print(f"✅ Successfully Processed: {successful_count}")
    print(f"⏭️  Skipped (Already Done): {skipped_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"🔄 Actually Processed: {processed_count}")
    print(f"⏱️  Total Time: {total_duration:.1f}s")
    print(f"📈 Average per Processed: {total_duration/max(processed_count, 1):.1f}s")
    print(f"💾 Summary saved to: {summary_file}")
    
    if results['skipped_processes']:
        print(f"\n⏭️  Skipped files (already processed):")
        for skipped in results['skipped_processes']:
            print(f"  - {skipped['image']}")
    
    print("="*70)
    
    return final_results

if __name__ == "__main__":
    # Configuration
    INPUT_DIR = "lab_images"
    OUTPUT_DIR = "processed_reports"
    
    try:
        results = batch_process_lab_reports(INPUT_DIR, OUTPUT_DIR)
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        print(f"Error: {str(e)}")

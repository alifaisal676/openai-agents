import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from ocr_tool import ocr_image
from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))



@dataclass
class AgentResponse:
    """Response from an agent"""
    content: str
    agent_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class Agent:
    """
    Base Agent class
    Each agent has a name, instructions, and optional handoffs to other agents
    """
    
    def __init__(self, name: str, instructions: str, handoffs: List['Agent'] = None, client=None):
        self.name = name
        self.instructions = instructions
        self.handoffs = handoffs or []
        self.client = client or groq_client
        self.tools = []  # Shared tools
    
    def add_tool(self, tool):
        """Add a shared tool to this agent"""
        self.tools.append(tool)
    
    def run(self, message: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Main agent execution method
        
        """
        try:
            # Prepare context for the agent
            full_context = self._prepare_context(message, context or {})
            
            # Execute the agent's main logic
            response = self._execute(full_context)
            
            # Check if handoff is needed
            handoff_result = self._check_handoff(response, message, context)
            if handoff_result:
                return handoff_result
            
            return AgentResponse(
                content=response,
                agent_name=self.name,
                success=True
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"Error in {self.name}: {str(e)}",
                agent_name=self.name,
                success=False,
                error=str(e)
            )
    
    def _prepare_context(self, message: str, context: Dict[str, Any]) -> str:
        """Prepare the full context for the agent"""
        return f"""
{self.instructions}

Context: {json.dumps(context, indent=2)}

User Input: {message}
"""
    
    def _execute(self, context: str) -> str:
       
        completion = self.client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": context}
            ]
        )
        return completion.choices[0].message.content.strip()
    
    def _check_handoff(self, response: str, original_message: str, context: Dict[str, Any]) -> Optional[AgentResponse]:
        """Check if this agent should hand off to another agent"""
        # This will be overridden by specialized agents
        return None

class OCRTool:
    """Shared OCR tool that can be used by any agent"""
    
    def __init__(self, name: str = "ocr_tool"):
        self.name = name
    
    def extract_text(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            return ocr_image(image_path)
        except Exception as e:
            return f"OCR Error: {str(e)}"
    
    def __call__(self, image_path: str) -> str:
        """Make the tool callable"""
        return self.extract_text(image_path)

class TriageAgent(Agent):
    """
    Triage Agent - Routes documents to appropriate specialist agents
 
    """
    
    def __init__(self, lab_agent: 'LabReportAgent', prescription_agent: 'DoctorPrescriptionAgent', ocr_tool: OCRTool):
        super().__init__(
            name="triage_agent",
            instructions="Handoff to the appropriate agent based on the type of medical document. Classify as either lab report or doctor prescription."
        )
        
        # Set up handoffs (like in OpenAI example)
        self.handoffs = [lab_agent, prescription_agent]
        self.lab_agent = lab_agent
        self.prescription_agent = prescription_agent
        self.ocr_tool = ocr_tool
        
        # Add OCR tool
        self.add_tool(ocr_tool)
    
    def run(self, input_data: Union[str, Dict], is_image: bool = True) -> AgentResponse:
        """
        Process input and handoff to appropriate agent
        """
        try:
            # Step 1: Extract text if image
            if is_image:
                if isinstance(input_data, dict) and 'image_path' in input_data:
                    image_path = input_data['image_path']
                else:
                    image_path = str(input_data)
                document_text = self.ocr_tool.extract_text(image_path)
            else:
                document_text = str(input_data)
            
            # Step 2: Classify document type
            classification = self._classify_document(document_text)
            
            # Step 3: Handoff to appropriate agent
            handoff_result = self._handoff_to_specialist(classification, document_text)
            
            return handoff_result
            
        except Exception as e:
            return AgentResponse(
                content=f"Triage error: {str(e)}",
                agent_name=self.name,
                success=False,
                error=str(e)
            )
    
    def _classify_document(self, text: str) -> str:
        """Classify the document type"""
        classification_prompt = f"""
        You are a medical document classifier.
        
        Classify this document as either:
        - "LabReport" (for laboratory results, blood tests, diagnostic tests)
        - "DoctorPrescription" (for medication prescriptions, treatment plans)
        
        Return ONLY one word: "LabReport" or "DoctorPrescription"
        
        Document text:
        {text}
        """
        
        completion = self.client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[
                {"role": "system", "content": "You are a medical document classifier. Return only 'LabReport' or 'DoctorPrescription'."},
                {"role": "user", "content": classification_prompt}
            ]
        )
        
        result = completion.choices[0].message.content.strip()
        
        # Normalize result
        if "labreport" in result.lower():
            return "LabReport"
        elif "doctorprescription" in result.lower():
            return "DoctorPrescription"
        else:
            return "Unknown"
    
    def _handoff_to_specialist(self, classification: str, document_text: str) -> AgentResponse:
        """Handoff to the appropriate specialist agent"""
        
        if classification == "LabReport":
            # Handoff to lab report agent
            return self.lab_agent.run(document_text, is_image=False)
            
        elif classification == "DoctorPrescription":
            # Handoff to prescription agent
            return self.prescription_agent.run(document_text, is_image=False)
            
        else:
            return AgentResponse(
                content=f"Unknown document type: {classification}",
                agent_name=self.name,
                success=False,
                error=f"Could not classify document type: {classification}"
            )

class LabReportAgent(Agent):
    """
    Lab Report Agent - Processes laboratory reports
    """
    
    def __init__(self, ocr_tool: OCRTool):
        super().__init__(
            name="lab_report_agent",
            instructions="You extract structured data from laboratory reports. Return valid JSON with test results."
        )
        self.ocr_tool = ocr_tool
        self.add_tool(ocr_tool)
    
    def run(self, input_data: Union[str, Dict], is_image: bool = False) -> AgentResponse:
        """Process lab report and return structured data"""
        try:
            # Get document text
            if is_image:
                if isinstance(input_data, dict) and 'image_path' in input_data:
                    document_text = self.ocr_tool.extract_text(input_data['image_path'])
                else:
                    document_text = self.ocr_tool.extract_text(str(input_data))
            else:
                document_text = str(input_data)
            
            # Process with specialized prompt
            structured_data = self._extract_lab_data(document_text)
            
            return AgentResponse(
                content="Lab report processed successfully",
                agent_name=self.name,
                success=True,
                data=structured_data
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"Lab report processing error: {str(e)}",
                agent_name=self.name,
                success=False,
                error=str(e)
            )
    
    def _extract_lab_data(self, text: str) -> Dict[str, Any]:
        """Extract structured lab data"""
        prompt = f"""
        Extract laboratory test results from this report and return valid JSON only.
        
        Format:
        {{
          "tests": [
            {{
              "test_name": "Test name",
              "result": "Result value",
              "unit": "Unit",
              "reference_range": "Normal range",
              "status": "normal/abnormal/critical"
            }}
          ],
          "patient_info": {{
            "name": "Patient name",
            "date": "Test date"
          }}
        }}
        
        Lab Report:
        {text}
        """
        
        completion = self.client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[
                {"role": "system", "content": "Extract lab data and return valid JSON only. No explanations."},
                {"role": "user", "content": prompt}
            ]
        )
        
        result = completion.choices[0].message.content.strip()
        
        # Clean up markdown formatting if present
        if result.startswith("```json"):
            result = result.replace("```json", "").replace("```", "").strip()
        elif result.startswith("```"):
            result = result.replace("```", "").strip()
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            # Return raw result if JSON parsing fails
            return {"raw_response": result, "parsing_error": "Could not parse as JSON"}

class DoctorPrescriptionAgent(Agent):
    """
    Doctor Prescription Agent - Processes prescriptions
    """
    
    def __init__(self, ocr_tool: OCRTool):
        super().__init__(
            name="doctor_prescription_agent", 
            instructions="You extract structured data from doctor prescriptions. Return valid JSON with medication details."
        )
        self.ocr_tool = ocr_tool
        self.add_tool(ocr_tool)
    
    def run(self, input_data: Union[str, Dict], is_image: bool = False) -> AgentResponse:
        """Process prescription and return structured data"""
        try:
            # Get document text
            if is_image:
                if isinstance(input_data, dict) and 'image_path' in input_data:
                    document_text = self.ocr_tool.extract_text(input_data['image_path'])
                else:
                    document_text = self.ocr_tool.extract_text(str(input_data))
            else:
                document_text = str(input_data)
            
            # Process with specialized prompt
            structured_data = self._extract_prescription_data(document_text)
            
            return AgentResponse(
                content="Prescription processed successfully",
                agent_name=self.name,
                success=True,
                data=structured_data
            )
            
        except Exception as e:
            return AgentResponse(
                content=f"Prescription processing error: {str(e)}",
                agent_name=self.name,
                success=False,
                error=str(e)
            )
    
    def _extract_prescription_data(self, text: str) -> Dict[str, Any]:
        """Extract structured prescription data"""
        prompt = f"""
        Extract prescription information from this document and return valid JSON only.
        
        Format:
        {{
          "doctor_info": {{
            "name": "Doctor name",
            "specialty": "Specialty",
            "license": "License number"
          }},
          "patient_info": {{
            "name": "Patient name",
            "age": "Age",
            "id": "Patient ID"
          }},
          "medications": [
            {{
              "name": "Medication name",
              "dosage": "Dosage",
              "frequency": "How often",
              "duration": "How long",
              "instructions": "Special instructions"
            }}
          ],
          "date": "Prescription date"
        }}
        
        Prescription:
        {text}
        """
        
        completion = self.client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[
                {"role": "system", "content": "Extract prescription data and return valid JSON only. No explanations."},
                {"role": "user", "content": prompt}
            ]
        )
        
        result = completion.choices[0].message.content.strip()
        
        # Clean up markdown formatting if present
        if result.startswith("```json"):
            result = result.replace("```json", "").replace("```", "").strip()
        elif result.startswith("```"):
            result = result.replace("```", "").strip()
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            # Return raw result if JSON parsing fails
            return {"raw_response": result, "parsing_error": "Could not parse as JSON"}

# Initialize the agent system (like in OpenAI example)
def create_medical_triage_system():
    """
    Create the complete agent system
    """
    # Create shared OCR tool
    ocr_tool = OCRTool()
    
    # Create specialist agents
    lab_agent = LabReportAgent(ocr_tool)
    prescription_agent = DoctorPrescriptionAgent(ocr_tool)
    
    # Create triage agent with handoffs (like OpenAI example)
    triage_agent = TriageAgent(lab_agent, prescription_agent, ocr_tool)
    
    return triage_agent

# Main system instance
medical_triage_agent = create_medical_triage_system()

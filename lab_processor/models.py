from typing import List, Optional
from pydantic import BaseModel, ValidationError

class LabTest(BaseModel):
    test_name: str
    value: Optional[str] = ""
    unit: str = ""
    reference_range: str = ""

class LabReport(BaseModel):
    patient_name: str
    age: str = ""
    gender: str = ""
    doctor_name: str = ""
    date: str = ""
    comments: str = ""
    test_results: List[LabTest] = []

def validate_lab_data(data: dict) -> dict:
   
    try:
        validated = LabReport(**data)
        return validated.model_dump()
    except ValidationError:
        # Return original data if validation fails
        return data

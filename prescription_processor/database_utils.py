"""
📚 Database Utilities Module
Handles medicine database operations and fuzzy matching.
"""

import re
from rapidfuzz import fuzz, process
import logging

def load_trusted_medicine_database(database_file_path):
    """📚 Load medicine database from JavaScript file"""
    with open(database_file_path, 'r', encoding='utf-8') as database_file:
        javascript_content = database_file.read()
    
    # Extract medicine names from JavaScript array
    array_pattern = re.search(r'var\s+\w+\s*=\s*\[(.*?)\];', javascript_content, re.DOTALL)
    if not array_pattern:
        return []
    
    medicine_names = re.findall(r'"([^"]*)"', array_pattern.group(1))
    return medicine_names

def cross_reference_with_known_medicines(extracted_medicines, medicine_database):
    """🔍 Cross-reference extracted medicines with database using fuzzy matching"""
    cross_referenced_medicines = []
    
    for medicine_data in extracted_medicines:
        medicine_name = medicine_data.get('medicine', '').strip()
        if not medicine_name:
            continue
            
        # Find best database match
        best_database_match, match_confidence, _ = process.extractOne(
            medicine_name, 
            medicine_database, 
            scorer=fuzz.ratio
        )
        
        verified_medicine = medicine_data.copy()
        
        # Use database name if high confidence match
        if match_confidence >= 90:
            verified_medicine['medicine'] = best_database_match
            
        verified_medicine['confidence'] = match_confidence
        cross_referenced_medicines.append(verified_medicine)
    
    return cross_referenced_medicines

def parse_lab_report(text: str, client) -> str:
    prompt = f"""
You are a lab report parser.

Your task is to output only valid JSON, nothing else.

Extract lab results in this format:
[
  {{
    "test_name": "...",
    "result": "...",
    "unit": "...",
    "reference_range": "..."
  }}
]

❌ Do not explain your reasoning.
❌ Do not add any notes.
✅ Only output valid JSON.

If data is missing, set fields to empty string.

Text:
\"\"\"
{text}
\"\"\"
"""

    completion = client.chat.completions.create(
        model="gemma2-9b-it",
        messages=[
            {"role": "system", "content": "You output JSON only."},
            {"role": "user", "content": prompt}
        ]
    )
   

    return completion.choices[0].message.content.strip()



def parse_prescription(text: str, client) -> str:

    prompt = f"""
You are a prescription parser.

Your task is to output only valid JSON, nothing else.

Extract medication data in this format:
{{
  "medications": [
    {{
      "name": "...",
      "dosage": "...",
      "instructions": "..."
    }}
  ]
}}

❌ Do not explain your reasoning.
❌ Do not add any notes.
✅ Only output valid JSON.

If data is missing, set fields to empty string.

Text:
\"\"\"
{text}
\"\"\"
"""
    completion = client.chat.completions.create(
        model="gemma2-9b-it" ,
        messages=[
            {"role": "system", "content": "Return only valid JSON. No extra text."},
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message.content.strip()


    
from api import groq_client

def classify_document(text: str, client) -> str:
    """
    Classifies the text into LabReport or DoctorPrescription.
    Returns exactly 'LabReport' or 'DoctorPrescription'.
    """

    system_message = (
        "You are a classification engine. "
        "Your ONLY valid outputs are exactly:\n\n"
        "LabReport\n"
        "DoctorPrescription\n\n"
        "Return ONLY one of these two words. "
        "Do not add any other text. Do not explain. Do not use sentences."
    )

    user_prompt = f"""
  just a single word label  
Return ONLY one of these exact labels:

LabReport
DoctorPrescription

Text:
{text}
"""

    completion = client.chat.completions.create(
        model="gemma2-9b-it",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ]
    )

    label = completion.choices[0].message.content.strip()

    # Normalize by removing spaces and lowercasing
    label_clean = label.replace(" ", "").lower()

    if "labreport" in label_clean:
        return "LabReport"
    elif "doctorprescription" in label_clean:
        return "DoctorPrescription"
    else:
        return"Unexpected classification output"
        # raise ValueError("Invalid classification output.")


# # TESTiING CLASSIFIER 
# with open('output.txt', 'r', encoding='utf-8') as f:
#     text= f.read()
# print(classify_document(text, groq_client))
# # print(classify_document("This is a doctor's prescription for medication.", groq_client))
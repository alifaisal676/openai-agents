from openai import OpenAI
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"                                              # I have replaced the base url with the Groq API endpoint
)



#  Define your local calculator function
def calculator(operation, num1, num2):
    try:
        num1 = float(num1)
        num2 = float(num2)
        if operation == "add":
            return num1 + num2
        elif operation == "subtract":
            return num1 - num2
        elif operation == "multiply":
            return num1 * num2
        elif operation == "divide":
            return num1 / num2 if num2 != 0 else "Oops! You can't divide by zero."
        else:
            return "Sorry, I didn’t understand that operation."
    except ValueError:
        return "Hmm, those don’t look like valid numbers."

# Describe the function schema for the LLM
functions = [
    {
        "name": "calculator",
        "description": "Perform basic arithmetic operations",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The arithmetic operation to perform"
                },
                "num1": {
                    "type": "number",
                    "description": "The first number"
                },
                "num2": {
                    "type": "number",
                    "description": "The second number"
                },
            },
            "required": ["operation", "num1", "num2"]
        }
    }
]

#  Get user question from input
user_question = input("Ask your question: ")

#  Construct initial conversation messages
messages = [
    {
        "role": "system",
        "content": (
            "You are a friendly, helpful assistant who can do math calculations. "
            "If needed, use the calculator tool to ensure correct answers."
        )
    },
    {
        "role": "user",
        "content": user_question
    }
]

#  First call to model: see if it wants to call a function
response = client.chat.completions.create(
    model="llama3-70b-8192",  # Or your Groq-supported model
    messages=messages,
    functions=functions,
    function_call="auto"
)

#  Check if the model wants to call our function
if response.choices[0].finish_reason == "function_call":
    function_call = response.choices[0].message.function_call
    print("\n🤖 Decided to call:", function_call.name)
    print("With arguments:", function_call.arguments)

    # Parse arguments from JSON
    args = json.loads(function_call.arguments)

    # Call our local calculator with the given arguments
    result = calculator(args["operation"], args["num1"], args["num2"])
    print("\n🧮 Calculator result:", result)

    # Send the function result back to the model for a friendly reply
    follow_up_response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            *messages,
            {"role": "assistant", "content": None, "function_call": function_call},
            {"role": "function", "name": "calculator", "content": str(result)}
        ]
    )

    # Print final response to user
    print("\n🤖", follow_up_response.choices[0].message.content)

else:
    # Model chose not to call a function, just replied directly
    print("\n🤖", response.choices[0].message.content)

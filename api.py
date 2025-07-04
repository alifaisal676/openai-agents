from groq import Groq
# from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


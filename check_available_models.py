import google.generativeai as genai
import os
from dotenv import load_dotenv
# Or use `os.getenv('GOOGLE_API_KEY')` to fetch an environment variable.
load_dotenv()
genai.configure(api_key=os.environ.get('API_KEY'))

for m in genai.list_models():
  if 'generateContent' in m.supported_generation_methods:
    print(m.name)
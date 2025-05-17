from dotenv import load_dotenv
import os

load_dotenv()
class Config:
   api_key = os.getenv("API_KEY")
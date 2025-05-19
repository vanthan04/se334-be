from dotenv import load_dotenv
import os

load_dotenv()
class Config:
   use_groq = True  # Chuyển thành False để dùng local
   api_key = os.getenv("API_KEY")
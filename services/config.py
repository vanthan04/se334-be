import os
from dotenv import load_dotenv

load_dotenv()  # Load từ file .env

class Config:
    DB_URI = os.getenv("DB_URI")

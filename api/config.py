from dotenv import load_dotenv
import os

load_dotenv()
class Config:
   base_url = os.getenv("BASE_URL")  # Cập nhật biến môi trường cho base_url
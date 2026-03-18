from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set")

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./resume.db')
ALLOWED_ORIGINS = os.getenv(
    'ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000'
).split(',')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
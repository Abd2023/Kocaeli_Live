import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "kocaeli_live_db")
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY")

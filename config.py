import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
LOG_CHANNEL = os.getenv('LOG_CHANNEL')
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
LOG_CHANNEL = int(os.getenv('LOG_CHANNEL'))
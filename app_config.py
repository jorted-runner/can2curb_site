import os
from dotenv import load_dotenv
load_dotenv()
DATABASE_URI = 'sqlite:///can2curb.sqlite3'
ADMIN_EMAILS = os.environ.get('ADMIN_EMAILS')
SECRET_KEY = os.environ.get("SECRET_KEY")
import os
from dotenv import load_dotenv

load_dotenv()

# DATABASE_URL = "mysql+pymysql://root:''@localhost:3306/grammrlyst"
DATABASE_URL = "mysql+pymysql://root@localhost:3306/grammrlyst"

JWT_SECRET_KEY = "SUPER_SECRET_KEY"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

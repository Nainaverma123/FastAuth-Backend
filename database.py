import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname= os.getenv("dbname"),
    user= os.getenv("user"),
    password= os.getenv("password"),
    host= os.getenv("host"),
    port= os.getenv("port")
)

cursor = conn.cursor()

print ("Database connection successful")

    
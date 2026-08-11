import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitacora_web.settings')

import django
from django.conf import settings

django.setup()

import pyodbc

conn_str = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    f"SERVER={os.getenv('DB_SERVER')},{os.getenv('DB_PORT','1433')} ;"
    f"DATABASE={os.getenv('DB_NAME')} ;"
    f"UID={os.getenv('DB_USER')} ;"
    f"PWD={os.getenv('DB_PASSWORD')} ;"
    f"Encrypt={os.getenv('DB_ENCRYPT','no')} ;"
    f"TrustServerCertificate={os.getenv('DB_TRUST_SERVER_CERTIFICATE','yes')} ;"
    f"Connection Timeout={os.getenv('DB_TIMEOUT','8')} ;"
)
print('Connection string:', conn_str)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' AND TABLE_NAME LIKE '%registro%' ORDER BY TABLE_SCHEMA, TABLE_NAME")
    rows = cursor.fetchall()
    print('Found', len(rows), 'tables:')
    for row in rows:
        print(row.TABLE_SCHEMA, row.TABLE_NAME)
    cursor.close()
    conn.close()
except Exception as exc:
    import traceback
    traceback.print_exc()

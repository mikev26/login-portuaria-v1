import os
import django
from contextlib import closing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitacora_web.settings')
django.setup()

from bitacora.db import get_connection

conn = get_connection()
with closing(conn.cursor()) as cursor:
    cursor.execute("""
        SELECT 
            o.name AS sp_name,
            m.definition
        FROM sys.sql_modules m
        JOIN sys.objects o ON m.object_id = o.object_id
        WHERE m.definition LIKE '%dim_tarifa%'
          AND o.type = 'P'
        ORDER BY o.name
    """)
    rows = cursor.fetchall()
    print("Stored procedures touching dim_tarifa:")
    for r in rows:
        print(f" - {r[0]}")
        definition = r[1].lower()
        if "update" in definition:
            print("   Contains UPDATE!")

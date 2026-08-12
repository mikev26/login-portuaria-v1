import os
import django
from contextlib import closing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitacora_web.settings')
django.setup()

from bitacora.db import get_connection

conn = get_connection()
with closing(conn.cursor()) as cursor:
    for proc_name in ["SPJ_insert_Tarifas"]:
        print(f"\n=== Parameters for {proc_name} ===")
        cursor.execute("""
            SELECT 
                p.name AS parameter_name,
                t.name AS type_name,
                p.max_length,
                p.is_output
            FROM sys.parameters p
            JOIN sys.types t ON p.system_type_id = t.system_type_id AND p.user_type_id = t.user_type_id
            WHERE p.object_id = OBJECT_ID(?)
            ORDER BY p.parameter_id
        """, f"dbo.{proc_name}")
        rows = cursor.fetchall()
        for r in rows:
            print(f" Name: {r[0]}, Type: {r[1]}, MaxLength: {r[2]}, IsOutput: {r[3]}")

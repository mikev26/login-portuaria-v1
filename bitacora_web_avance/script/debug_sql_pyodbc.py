import pyodbc

conn_str = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=192.168.3.17,1433;'
    'DATABASE=dim_sis_puerto_v1;'
    'UID=UserGSoep;'
    'PWD=GSoep*2026*;'
    'Encrypt=no;'
    'TrustServerCertificate=yes;'
    'Connection Timeout=8;'
)
print('Connecting with', conn_str)

conn = pyodbc.connect(conn_str)
cur = conn.cursor()

for query, label in [
    ("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' AND TABLE_NAME LIKE '%combust%' ORDER BY TABLE_SCHEMA, TABLE_NAME", 'TABLES LIKE %combust%'),
    ("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' AND TABLE_NAME LIKE '%registro%combust%' ORDER BY TABLE_SCHEMA, TABLE_NAME", 'TABLES LIKE %registro%combust%'),
    ("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME LIKE '%combust%' ORDER BY TABLE_SCHEMA, TABLE_NAME", 'VIEWS LIKE %combust%'),
    ("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME LIKE '%registro%combust%' ORDER BY TABLE_SCHEMA, TABLE_NAME", 'VIEWS LIKE %registro%combust%'),
]:
    print('\n' + label)
    cur.execute(query)
    rows = cur.fetchall()
    print('Found', len(rows))
    for row in rows:
        print(row.TABLE_SCHEMA, row.TABLE_NAME)

cur.close()
conn.close()

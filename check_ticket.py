import django, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'morenapos'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'morenapos.settings')
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ticket' ORDER BY ORDINAL_POSITION")
    cols = cursor.fetchall()
    print("=== COLUMNAS DE ticket ===")
    for c in cols:
        print(f'{c[0]:35s} {c[1]}')
    
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ticket' AND COLUMN_NAME LIKE '%sede%'")
    sede_cols = cursor.fetchall()
    print("\n=== COLUMNAS RELACIONADAS CON SEDE ===")
    for c in sede_cols:
        print(c[0])
    
    cursor.execute("SELECT TOP 5 * FROM ticket")
    rows = cursor.fetchall()
    print(f"\n=== MUESTRA (5 registros) ===")
    for row in rows:
        print(row)

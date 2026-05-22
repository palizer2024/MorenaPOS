import sys, os
sys.path.insert(0, 'd:/MorenaPOS')
sys.path.insert(0, 'd:/MorenaPOS/morenapos')
os.environ['DJANGO_SETTINGS_MODULE'] = 'morenapos.settings'

import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT TOP 5 Id, NombreCompleto, TipoDocumento, NroDocumento, Domicilio FROM Cliente WHERE Estado = 1 AND NroDocumento LIKE '7187%' ORDER BY Id")
    rows = cursor.fetchall()
    print(f"Encontrados: {len(rows)}")
    for r in rows:
        print(f"#{r[0]}: {r[1]} | {r[2]}: {r[3]} | {r[4]}")

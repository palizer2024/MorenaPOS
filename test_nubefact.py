import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'morenapos'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'morenapos.settings')
import django; django.setup()
from django.db import connection
import requests, json

with connection.cursor() as cursor:
    cursor.execute('SELECT Ruta, Token FROM sede WHERE Id = 1')
    row = cursor.fetchone()
    ruta = row[0].rstrip('/')
    token = row[1]
    print(f'Ruta: {ruta}')
    print(f'Token: {token[:30]}...')
    
    endpoint = f'{ruta}/consulta/dni'
    headers = {'Authorization': f'Token token={token}', 'Content-Type': 'application/json'}
    payload = {'dni': '29726709'}
    
    print(f'\nEndpoint: {endpoint}')
    
    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        print(f'Status: {resp.status_code}')
        print(f'Response: {resp.text[:1000]}')
    except Exception as e:
        print(f'Error: {type(e).__name__}: {e}')

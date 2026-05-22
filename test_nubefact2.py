import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'morenapos'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'morenapos.settings')
import django; django.setup()
from django.db import connection
import requests, json

with connection.cursor() as cursor:
    cursor.execute('SELECT Ruta, Token FROM sede WHERE Id = 1')
    row = cursor.fetchone()
    ruta_base = row[0].rstrip('/')
    token = row[1]
    
    # Try different endpoint patterns
    patterns = [
        f'{ruta_base}/consulta/dni',
        f'https://api.nubefact.com/api/v1/consulta/dni',
        f'https://api.nubefact.com/api/v1/dni',
        f'https://api.nubefact.com/api/v1/ruc',
    ]
    
    headers = {'Authorization': f'Token token={token}', 'Content-Type': 'application/json'}
    
    for ep in patterns:
        try:
            payload = {'dni': '29726709'} if 'dni' in ep else {'ruc': '20123456789'}
            resp = requests.post(ep, json=payload, headers=headers, timeout=10)
            print(f'{ep}')
            print(f'  Status: {resp.status_code}')
            print(f'  Body: {resp.text[:200]}')
            print()
        except Exception as e:
            print(f'{ep}')
            print(f'  Error: {e}')
            print()

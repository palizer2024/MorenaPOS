import django, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'morenapos'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'morenapos.settings')
django.setup()
from django.db import connection

c = connection.cursor()
c.execute("SELECT Id, Nombre, Identificador FROM sede WHERE Id = %s", [1])
print('Sede 1:', c.fetchall())
c.execute("SELECT Id, Nombre, Identificador FROM sede WHERE Id = %s", [2])
print('Sede 2:', c.fetchall())
c.execute("SELECT Id, Nombre, Identificador FROM sede WHERE Id = %s", [3])
print('Sede 3:', c.fetchall())

import django, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'morenapos'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'morenapos.settings')
django.setup()
from django.db import connection

c = connection.cursor()

# ticketdet.Id_Producto -> producto.Id -> producto.Id_ProductoGeneral -> productogeneral.Id -> productogeneral.Nombre
c.execute("""
    SELECT TOP 5 
        td.Id_Ticket,
        td.Id_Producto,
        p.Id as ProductoId,
        p.Id_ProductoGeneral,
        pg.Id as ProdGeneralId,
        pg.Nombre,
        td.Cantidad,
        td.PrecioUnitario,
        td.Total
    FROM ticketdet td
    LEFT JOIN producto p ON p.Id = td.Id_Producto
    LEFT JOIN productogeneral pg ON pg.Id = p.Id_ProductoGeneral
    WHERE td.Id_Ticket = 836031
""")
print('Ticket 836031 con JOIN producto -> productogeneral:')
for r in c.fetchall():
    print(f'  {r}')

c.execute("""
    SELECT TOP 5 
        td.Id_Ticket,
        td.Id_Producto,
        p.Id as ProductoId,
        p.Id_ProductoGeneral,
        pg.Nombre,
        td.Cantidad,
        td.PrecioUnitario,
        td.Total
    FROM ticketdet td
    LEFT JOIN producto p ON p.Id = td.Id_Producto
    LEFT JOIN productogeneral pg ON pg.Id = p.Id_ProductoGeneral
    WHERE td.Id_Ticket = 835956
""")
print('\nTicket 835956:')
for r in c.fetchall():
    print(f'  {r}')

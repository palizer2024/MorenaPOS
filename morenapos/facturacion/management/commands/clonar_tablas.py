"""
Management command para clonar datos de las tablas originales
(comprobante, comprobantedet, sede) a las tablas clonadas
(comprobanteclonada, comprobantedetclonada, sedeclonada).

Uso:
    python manage.py clonar_tablas                     # Clona todo
    python manage.py clonar_tablas --solo-sedes        # Solo sedes
    python manage.py clonar_tablas --solo-comprobantes # Solo comprobantes
    python manage.py clonar_tablas --force             # Re-clona aunque ya existan
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from facturacion.models import (
    Comprobante, Comprobantedet,
    SedeClonada, ComprobanteClonado, ComprobanteDetClonado,
)


class Command(BaseCommand):
    help = 'Clona datos de tablas originales a tablas clonadas para facturación electrónica'

    def add_arguments(self, parser):
        parser.add_argument(
            '--solo-sedes',
            action='store_true',
            help='Clonar solo la tabla sede',
        )
        parser.add_argument(
            '--solo-comprobantes',
            action='store_true',
            help='Clonar solo las tablas comprobante y comprobantedet',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar re-clonación aunque los registros ya existan',
        )

    def handle(self, *args, **options):
        solo_sedes = options['solo_sedes']
        solo_comprobantes = options['solo_comprobantes']
        force = options['force']

        self.stdout.write(self.style.SUCCESS('=== INICIO CLONACIÓN DE TABLAS ==='))
        self.stdout.write(f'Fecha: {timezone.now()}')

        if not solo_comprobantes:
            self._clonar_sedes(force)

        if not solo_sedes:
            self._clonar_comprobantes(force)
            self._clonar_detalles(force)

        self.stdout.write(self.style.SUCCESS('=== CLONACIÓN COMPLETADA ==='))

    def _clonar_sedes(self, force):
        """
        Clona registros de sede -> sedeclonada.
        Usa raw SQL porque el modelo Sede en core.models no tiene db_column
        y no mapea correctamente con las columnas reales de la BD.
        """
        self.stdout.write('\n--- Clonando sedes... ---')

        with connection.cursor() as cursor:
            cursor.execute("SELECT Id, Nombre, ValorIgv, Identificador, SerieFactura, "
                           "SerieBoleta, CorrelativoBoleta, CorrelativoFactura, "
                           "SerieNotaCreditoBoleta, CorrelativoNotaCreditoBoleta, "
                           "SerieNotaCreditoFactura, CorrelativoNotaCreditoFactura, "
                           "Ruta, Token, SerieTicket, CorrelativoTicket, "
                           "NombreImpresora, Created, Modified, UserCreated, "
                           "UserModified, Estado FROM sede")
            rows = cursor.fetchall()

        self.stdout.write(f'Sedes originales encontradas: {len(rows)}')

        creadas = 0
        saltadas = 0

        for row in rows:
            (id_sede, nombre, valorigv, identificador, seriefactura,
             serieboleta, correlativoboleta, correlativofactura,
             serienotacreditoboleta, correlativonotacreditoboleta,
             serienotacreditofactura, correlativonotacreditofactura,
             ruta, token, serieticket, correlativoticket,
             nombreimpresora, created, modified, usercreated,
             usermodified, estado) = row

            existe = SedeClonada.objects.filter(id_sede_original=id_sede).exists()

            if existe and not force:
                saltadas += 1
                continue

            if existe and force:
                SedeClonada.objects.filter(id_sede_original=id_sede).delete()

            SedeClonada.objects.create(
                id_sede_original=id_sede,
                nombre=nombre,
                valor_igv=valorigv,
                identificador=identificador,
                serie_factura=seriefactura,
                serie_boleta=serieboleta,
                correlativo_boleta=correlativoboleta,
                correlativo_factura=correlativofactura,
                serie_nota_credito_boleta=serienotacreditoboleta,
                correlativo_nota_credito_boleta=correlativonotacreditoboleta,
                serie_nota_credito_factura=serienotacreditofactura,
                correlativo_nota_credito_factura=correlativonotacreditofactura,
                ruta=ruta,
                token=token,
                serie_ticket=serieticket,
                correlativo_ticket=correlativoticket,
                nombre_impresora=nombreimpresora,
                created=created,
                user_created=usercreated,
                estado=estado,
            )
            creadas += 1

        self.stdout.write(self.style.SUCCESS(f'Sedes clonadas: {creadas}'))
        if saltadas > 0:
            self.stdout.write(f'Sedes saltadas (ya existían): {saltadas}')

    def _clonar_comprobantes(self, force):
        """Clona registros de comprobante -> comprobanteclonada."""
        self.stdout.write('\n--- Clonando comprobantes... ---')

        comprobantes = Comprobante.objects.all()
        self.stdout.write(f'Comprobantes originales encontrados: {comprobantes.count()}')

        creados = 0
        saltados = 0

        for comp in comprobantes:
            existe = ComprobanteClonado.objects.filter(
                id_comprobante_original=comp.id
            ).exists()

            if existe and not force:
                saltados += 1
                continue

            if existe and force:
                # Eliminar también los detalles clonados asociados
                clonado = ComprobanteClonado.objects.get(
                    id_comprobante_original=comp.id
                )
                ComprobanteDetClonado.objects.filter(
                    id_comprobante_clonado=clonado.id
                ).delete()
                clonado.delete()

            ComprobanteClonado.objects.create(
                id_comprobante_original=comp.id,
                id_cliente=comp.id_cliente_id,
                id_sede=comp.id_sede,
                turno=comp.turno,
                referenciaticket=comp.referenciaticket,
                serie=comp.serie,
                correlativo=comp.correlativo,
                tipocomprobante=comp.tipocomprobante,
                total=comp.total,
                enviosunat=comp.enviosunat,
                identificador=comp.identificador,
                usercreated=comp.usercreated,
                created=comp.created,
                estado=comp.estado,
            )
            creados += 1

        self.stdout.write(self.style.SUCCESS(f'Comprobantes clonados: {creados}'))
        if saltados > 0:
            self.stdout.write(f'Comprobantes saltados (ya existían): {saltados}')

    def _clonar_detalles(self, force):
        """Clona registros de comprobantedet -> comprobantedetclonada."""
        self.stdout.write('\n--- Clonando detalles de comprobante... ---')

        detalles = Comprobantedet.objects.select_related('id_comprobante').all()
        self.stdout.write(f'Detalles originales encontrados: {detalles.count()}')

        creados = 0
        saltados = 0
        sin_comprobante_clonado = 0

        for det in detalles:
            # Buscar el comprobante clonado correspondiente
            try:
                comp_clonado = ComprobanteClonado.objects.get(
                    id_comprobante_original=det.id_comprobante_id
                )
            except ComprobanteClonado.DoesNotExist:
                sin_comprobante_clonado += 1
                continue

            existe = ComprobanteDetClonado.objects.filter(
                id_detalle_original=det.id
            ).exists()

            if existe and not force:
                saltados += 1
                continue

            if existe and force:
                ComprobanteDetClonado.objects.filter(
                    id_detalle_original=det.id
                ).delete()

            ComprobanteDetClonado.objects.create(
                id_detalle_original=det.id,
                id_comprobante_clonado=comp_clonado,
                id_producto=det.id_producto,
                descripcion=det.descripcion,
                tipoventa=det.tipoventa,
                codproductosunat=det.codproductosunat,
                cantidad=det.cantidad,
                preciounitario=det.preciounitario,
                total=det.total,
            )
            creados += 1

        self.stdout.write(self.style.SUCCESS(f'Detalles clonados: {creados}'))
        if saltados > 0:
            self.stdout.write(f'Detalles saltados (ya existían): {saltados}')
        if sin_comprobante_clonado > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'Detalles sin comprobante clonado asociado: {sin_comprobante_clonado}'
                )
            )

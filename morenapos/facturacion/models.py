"""
Modelos para la aplicación facturacion.
Incluye modelos para las tablas existentes (comprobante, comprobantedet, cliente)
y sus versiones clonadas (comprobanteclonada, comprobantedetclonada, sedeclonada).
"""
from django.db import models


# =============================================================================
# MODELOS ORIGINALES (tablas existentes en la BD, managed = False)
# =============================================================================

class Cliente(models.Model):
    """
    Tabla: cliente
    Clientes registrados en el sistema.
    """
    id = models.AutoField(db_column='Id', primary_key=True)
    nombrecompleto = models.CharField(db_column='NombreCompleto', max_length=500)
    tipodocumento = models.CharField(db_column='TipoDocumento', max_length=50)
    nrodocumento = models.CharField(db_column='NroDocumento', max_length=50)
    domicilio = models.CharField(db_column='Domicilio', max_length=500, blank=True, null=True)
    telefono = models.CharField(db_column='Telefono', max_length=50, blank=True, null=True)
    email = models.CharField(db_column='Email', max_length=50, blank=True, null=True)
    usercreated = models.CharField(db_column='UserCreated', max_length=50)
    created = models.DateTimeField(db_column='Created')
    estado = models.BooleanField(db_column='Estado')

    class Meta:
        managed = False
        db_table = 'cliente'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"{self.nombrecompleto} ({self.nrodocumento})"


class Comprobante(models.Model):
    """
    Tabla: comprobante
    Comprobantes de venta (facturas, boletas, tickets).
    """
    id = models.AutoField(db_column='Id', primary_key=True)
    id_cliente = models.ForeignKey(
        Cliente, models.DO_NOTHING, db_column='Id_Cliente'
    )
    id_sede = models.IntegerField(db_column='Id_Sede')
    turno = models.CharField(db_column='Turno', max_length=50)
    referenciaticket = models.CharField(db_column='ReferenciaTicket', max_length=50)
    serie = models.CharField(db_column='Serie', max_length=10)
    correlativo = models.IntegerField(db_column='Correlativo')
    tipocomprobante = models.CharField(db_column='TipoComprobante', max_length=50)
    total = models.DecimalField(db_column='Total', max_digits=6, decimal_places=2)
    enviosunat = models.IntegerField(db_column='EnvioSunat')
    identificador = models.IntegerField(db_column='Identificador')
    usercreated = models.CharField(db_column='UserCreated', max_length=50)
    created = models.DateTimeField(db_column='Created')
    estado = models.BooleanField(db_column='Estado')

    class Meta:
        managed = False
        db_table = 'comprobante'
        verbose_name = 'Comprobante'
        verbose_name_plural = 'Comprobantes'

    def __str__(self):
        return f"{self.serie}-{self.correlativo} ({self.tipocomprobante})"


class Comprobantedet(models.Model):
    """
    Tabla: comprobantedet
    Detalle de cada comprobante (líneas de producto).
    """
    id = models.AutoField(db_column='Id', primary_key=True)
    id_comprobante = models.ForeignKey(
        Comprobante, models.DO_NOTHING, db_column='Id_Comprobante'
    )
    id_producto = models.IntegerField(db_column='Id_Producto')
    descripcion = models.CharField(db_column='Descripcion', max_length=500)
    tipoventa = models.CharField(db_column='TipoVenta', max_length=50)
    codproductosunat = models.CharField(db_column='CodProductoSunat', max_length=15)
    cantidad = models.IntegerField(db_column='Cantidad')
    preciounitario = models.DecimalField(db_column='PrecioUnitario', max_digits=6, decimal_places=2)
    total = models.DecimalField(db_column='Total', max_digits=6, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'comprobantedet'
        verbose_name = 'Detalle de Comprobante'
        verbose_name_plural = 'Detalles de Comprobante'

    def __str__(self):
        return f"{self.descripcion} x{self.cantidad}"


# =============================================================================
# MODELOS CLONADOS (tablas nuevas, managed = True para que Django las cree)
# =============================================================================

class SedeClonada(models.Model):
    """
    Tabla: sedeclonada
    Copia de seguridad de la tabla sede para facturación electrónica.
    Django creará esta tabla automáticamente (managed = True).
    """
    id_sede_original = models.IntegerField(unique=True, help_text="ID de la sede original")
    nombre = models.CharField(max_length=500)
    valor_igv = models.DecimalField(max_digits=18, decimal_places=2)
    identificador = models.IntegerField()
    serie_factura = models.CharField(max_length=50)
    serie_boleta = models.CharField(max_length=50)
    correlativo_boleta = models.IntegerField()
    correlativo_factura = models.IntegerField()
    serie_nota_credito_boleta = models.CharField(max_length=50)
    correlativo_nota_credito_boleta = models.IntegerField()
    serie_nota_credito_factura = models.CharField(max_length=50)
    correlativo_nota_credito_factura = models.IntegerField()
    ruta = models.TextField()
    token = models.TextField()
    serie_ticket = models.CharField(max_length=50)
    correlativo_ticket = models.IntegerField()
    nombre_impresora = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    user_created = models.CharField(max_length=50)
    user_modified = models.CharField(max_length=50, blank=True, null=True)
    estado = models.BooleanField(default=True)
    fecha_clonacion = models.DateTimeField(auto_now_add=True, help_text="Fecha en que se clonó")

    class Meta:
        db_table = 'sedeclonada'
        verbose_name = 'Sede Clonada'
        verbose_name_plural = 'Sedes Clonadas'

    def __str__(self):
        return f"[CLON] {self.nombre}"

    def get_next_correlativo(self, serie):
        """
        Obtener el próximo correlativo para la serie dada.
        Autoincrementa el correlativo después de obtenerlo.
        """
        if serie == 'FA':
            next_correlativo = self.correlativo_factura + 1
            self.correlativo_factura = next_correlativo
        elif serie == 'BO':
            next_correlativo = self.correlativo_boleta + 1
            self.correlativo_boleta = next_correlativo
        elif serie == 'NC-BO':
            next_correlativo = self.correlativo_nota_credito_boleta + 1
            self.correlativo_nota_credito_boleta = next_correlativo
        elif serie == 'NC-FA':
            next_correlativo = self.correlativo_nota_credito_factura + 1
            self.correlativo_nota_credito_factura = next_correlativo
        else:
            next_correlativo = 0
        
        self.save()
        return next_correlativo


class ComprobanteClonado(models.Model):
    """
    Tabla: comprobanteclonada
    Copia de seguridad de la tabla comprobante para facturación electrónica.
    Django creará esta tabla automáticamente (managed = True).
    """
    id_comprobante_original = models.IntegerField(
        unique=True, help_text="ID del comprobante original"
    )
    id_cliente = models.IntegerField(help_text="ID del cliente en la tabla original")
    id_sede = models.IntegerField()
    turno = models.CharField(max_length=50)
    referenciaticket = models.CharField(max_length=50)
    serie = models.CharField(max_length=10)
    correlativo = models.IntegerField()
    tipocomprobante = models.CharField(max_length=50)
    total = models.DecimalField(max_digits=6, decimal_places=2)
    enviosunat = models.IntegerField(default=0)
    identificador = models.IntegerField()
    usercreated = models.CharField(max_length=50)
    created = models.DateTimeField()
    estado = models.BooleanField(default=True)
    fecha_clonacion = models.DateTimeField(auto_now_add=True, help_text="Fecha en que se clonó")
    enviado_sunat = models.BooleanField(default=False, help_text="Indica si ya se envió a SUNAT")
    respuesta_sunat = models.TextField(blank=True, null=True, help_text="Respuesta de SUNAT (XML/JSON)")
    fecha_envio_sunat = models.DateTimeField(blank=True, null=True, help_text="Fecha de envío a SUNAT")

    class Meta:
        db_table = 'comprobanteclonada'
        verbose_name = 'Comprobante Clonado'
        verbose_name_plural = 'Comprobantes Clonados'

    def __str__(self):
        return f"[CLON] {self.serie}-{self.correlativo} ({self.tipocomprobante})"


class ComprobanteDetClonado(models.Model):
    """
    Tabla: comprobantedetclonada
    Copia de seguridad de la tabla comprobantedet para facturación electrónica.
    Django creará esta tabla automáticamente (managed = True).
    """
    id_detalle_original = models.IntegerField(
        unique=True, help_text="ID del detalle original"
    )
    id_comprobante_clonado = models.ForeignKey(
        ComprobanteClonado, on_delete=models.CASCADE, db_column='id_comprobante_clonado',
        help_text="Comprobante clonado al que pertenece este detalle"
    )
    id_producto = models.IntegerField()
    descripcion = models.CharField(max_length=500)
    tipoventa = models.CharField(max_length=50)
    codproductosunat = models.CharField(max_length=15)
    cantidad = models.IntegerField()
    preciounitario = models.DecimalField(max_digits=6, decimal_places=2)
    total = models.DecimalField(max_digits=6, decimal_places=2)
    fecha_clonacion = models.DateTimeField(auto_now_add=True, help_text="Fecha en que se clonó")

    class Meta:
        db_table = 'comprobantedetclonada'
        verbose_name = 'Detalle de Comprobante Clonado'
        verbose_name_plural = 'Detalles de Comprobante Clonados'

    def __str__(self):
        return f"[CLON] {self.descripcion} x{self.cantidad}"

"""
Modelos para la aplicación core.
Estos modelos reflejan las tablas existentes en la base de datos Azure SQL.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _


class Sede(models.Model):
    """
    Tabla: sede
    Representa una sede o local del restaurante.
    """
    id = models.BigAutoField(primary_key=True)
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
    created = models.DateTimeField()
    modified = models.DateTimeField(blank=True, null=True)
    user_created = models.CharField(max_length=50)
    user_modified = models.CharField(max_length=50)
    estado = models.BooleanField()
    
    class Meta:
        managed = False
        db_table = 'sede'
        verbose_name = 'Sede'
        verbose_name_plural = 'Sedes'
    
    def __str__(self):
        return self.nombre
    
    @property
    def activa(self):
        """Propiedad para compatibilidad con código existente."""
        return self.estado


class Rol(models.Model):
    """
    Tabla: rol
    Roles de usuario en el sistema (administrador, cajero, supervisor, etc.)
    """
    id = models.AutoField(primary_key=True, db_column='id_rol')
    nombre = models.CharField(max_length=50, db_column='nombre_rol')
    descripcion = models.TextField(blank=True, null=True)
    nivel_acceso = models.IntegerField(default=1, db_column='nivel_acceso')
    activo = models.BooleanField(default=True, db_column='activo')
    
    class Meta:
        db_table = 'rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    """
    Tabla: usuario
    Extiende el modelo de usuario de Django para incluir campos personalizados.
    """
    # Campos adicionales para la tabla usuario existente
    id_usuario = models.AutoField(primary_key=True, db_column='id_usuario')
    dni = models.CharField(max_length=20, unique=True, db_column='dni', blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True, db_column='telefono')
    direccion = models.TextField(blank=True, null=True, db_column='direccion')
    fecha_nacimiento = models.DateField(blank=True, null=True, db_column='fecha_nacimiento')
    activo = models.BooleanField(default=True, db_column='activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_column='fecha_creacion')
    fecha_actualizacion = models.DateTimeField(auto_now=True, db_column='fecha_actualizacion')
    
    # Sobrescribir campos de AbstractUser para mapear a la base de datos existente
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        db_column='username',
    )
    email = models.EmailField(_("email address"), blank=True, null=True, db_column='email')
    first_name = models.CharField(_("first name"), max_length=150, blank=True, db_column='nombres')
    last_name = models.CharField(_("last name"), max_length=150, blank=True, db_column='apellidos')
    
    # Relación con rol
    rol = models.ForeignKey(
        Rol,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_rol'
    )
    
    # Configuración para usar campos personalizados
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    # Resolver conflictos de related_name
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
        related_name="usuario_set",
        related_query_name="usuario",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="usuario_set",
        related_query_name="usuario",
    )
    
    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class UsuarioSede(models.Model):
    """
    Tabla: usuario_sede
    Relación muchos a muchos entre usuarios y sedes.
    """
    id = models.AutoField(primary_key=True, db_column='id_usuario_sede')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario')
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    activo = models.BooleanField(default=True, db_column='activo')
    fecha_asignacion = models.DateTimeField(auto_now_add=True, db_column='fecha_asignacion')
    
    class Meta:
        db_table = 'usuario_sede'
        verbose_name = 'Usuario por Sede'
        verbose_name_plural = 'Usuarios por Sede'
        unique_together = ('usuario', 'sede')
    
    def __str__(self):
        return f"{self.usuario.username} - {self.sede.nombre}"


class PermisoRol(models.Model):
    """
    Tabla: permiso_rol
    Asigna permisos específicos a roles.
    """
    id = models.AutoField(primary_key=True, db_column='id_permiso_rol')
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='id_rol')
    permiso = models.CharField(max_length=100, db_column='permiso')
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True, db_column='activo')
    
    class Meta:
        db_table = 'permiso_rol'
        verbose_name = 'Permiso por Rol'
        verbose_name_plural = 'Permisos por Rol'
        unique_together = ('rol', 'permiso')
    
    def __str__(self):
        return f"{self.rol.nombre} - {self.permiso}"
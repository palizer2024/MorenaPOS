"""
Migración para corregir columnas datetimeoffset en tablas clonadas.

El driver django-mssql-backend crea DateTimeField como datetimeoffset en SQL Server,
pero pyodbc en Linux no soporta el tipo ODBC -155 (datetimeoffset).
Esta migración convierte esas columnas a datetime2 que sí es soportado.

Afecta:
  - sedeclonada: created, modified, fecha_clonacion
  - comprobanteclonada: fecha_clonacion, fecha_envio_sunat
  - comprobantedetclonada: fecha_clonacion
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0001_initial'),
    ]

    operations = [
        # ── sedeclonada ──────────────────────────────────────────────────────
        migrations.RunSQL(
            sql="""
                IF EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'sedeclonada'
                      AND COLUMN_NAME = 'created'
                      AND DATA_TYPE = 'datetimeoffset'
                )
                BEGIN
                    ALTER TABLE sedeclonada
                        ALTER COLUMN created datetime2 NOT NULL;
                END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                IF EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'sedeclonada'
                      AND COLUMN_NAME = 'modified'
                      AND DATA_TYPE = 'datetimeoffset'
                )
                BEGIN
                    ALTER TABLE sedeclonada
                        ALTER COLUMN modified datetime2 NOT NULL;
                END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                IF EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'sedeclonada'
                      AND COLUMN_NAME = 'fecha_clonacion'
                      AND DATA_TYPE = 'datetimeoffset'
                )
                BEGIN
                    ALTER TABLE sedeclonada
                        ALTER COLUMN fecha_clonacion datetime2 NOT NULL;
                END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # ── comprobanteclonada ───────────────────────────────────────────────
        migrations.RunSQL(
            sql="""
                IF EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'comprobanteclonada'
                      AND COLUMN_NAME = 'fecha_clonacion'
                      AND DATA_TYPE = 'datetimeoffset'
                )
                BEGIN
                    ALTER TABLE comprobanteclonada
                        ALTER COLUMN fecha_clonacion datetime2 NOT NULL;
                END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                IF EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'comprobanteclonada'
                      AND COLUMN_NAME = 'fecha_envio_sunat'
                      AND DATA_TYPE = 'datetimeoffset'
                )
                BEGIN
                    ALTER TABLE comprobanteclonada
                        ALTER COLUMN fecha_envio_sunat datetime2 NULL;
                END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                IF EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'comprobanteclonada'
                      AND COLUMN_NAME = 'created'
                      AND DATA_TYPE = 'datetimeoffset'
                )
                BEGIN
                    ALTER TABLE comprobanteclonada
                        ALTER COLUMN created datetime2 NOT NULL;
                END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # ── comprobantedetclonada ────────────────────────────────────────────
        migrations.RunSQL(
            sql="""
                IF EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'comprobantedetclonada'
                      AND COLUMN_NAME = 'fecha_clonacion'
                      AND DATA_TYPE = 'datetimeoffset'
                )
                BEGIN
                    ALTER TABLE comprobantedetclonada
                        ALTER COLUMN fecha_clonacion datetime2 NOT NULL;
                END
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

# Bitácora Electrónica — avance Django + SQL Server

Esta versión parte del proyecto entregado y reemplaza los datos simulados por una capa preparada para consumir procedimientos almacenados de SQL Server mediante `pyodbc`.

## Regla de acceso implementada

El acceso requiere dos comprobaciones:

1. El procedimiento institucional de login valida usuario y contraseña en `op_claves`.
2. El usuario devuelto debe aparecer en el procedimiento de turnos activos, basado en:

```sql
fecha_s IS NULL AND activo <> 7 AND Bitacora = 1
```

Por eso, cuando un nuevo inspector sea incorporado a la vista y tenga turno activo, Django lo reconocerá automáticamente; no existe una lista fija de inspectores en Python.

## Funciones incluidas

- Login y sesiones Django.
- Cierre de sesión por POST.
- Acceso restringido a inspectores con turno habilitado.
- Consumo de procedimientos con parámetros seguros.
- Listado de buques industriales.
- Listado de buques artesanales.
- Selector dinámico según el tipo de novedad.
- Modo demostración para presentar el avance sin conexión institucional.
- Scripts SQL de diagnóstico y procedimientos de solo lectura.

## Pendientes que requieren información de la base

1. Nombre, parámetros y columnas de salida del procedimiento real de autenticación.
2. Procedimiento que devuelve el historial de novedades de un turno.
3. Procedimiento que guarda una novedad.
4. Reglas para iniciar y cerrar turnos desde la nueva interfaz, si aplica.

## Instalación en Windows

No copies ni compartas la carpeta `venv` del proyecto anterior. Crea un entorno nuevo:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

También debe estar instalado **Microsoft ODBC Driver 18 for SQL Server**.

Crea la configuración local:

```powershell
Copy-Item .env.example .env
```

Edita `.env` y coloca la contraseña real únicamente en tu equipo. No subas `.env` a GitHub.

Si quieres usar el panel de administración de Django, ejecuta también las migraciones:

```powershell
py manage.py migrate
```

Para levantar la aplicación:

```powershell
py manage.py runserver
```

Abre `http://127.0.0.1:8000/`.

## Presentación inmediata sin SQL Server

En `.env` cambia temporalmente:

```env
DEMO_MODE=true
```

Credenciales de la demostración:

```text
Usuario: inspector.demo
Contraseña: Demo1234
```

Antes de una prueba real vuelve a colocar `DEMO_MODE=false`.

## Orden recomendado en SQL Server

1. Ejecutar `sql/00_diagnostico_login.sql` en `op_claves`.
2. Entregar al desarrollador el resultado del procedimiento de autenticación.
3. Pedir al ingeniero revisar y ejecutar `sql/01_procedimientos_lectura.sql` en `dim_sis_puerto_v1`.
4. Configurar los nombres reales en `.env`.

## Seguridad

- No hay contraseñas reales dentro del código.
- Django no consulta directamente `dim_claves`.
- Los nombres de procedimientos y parámetros se validan antes de ejecutar SQL.
- Los valores de usuario, contraseña e identificadores se envían parametrizados.
- Los procedimientos de lectura no deben concederse a `PUBLIC`.

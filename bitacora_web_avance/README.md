# Bitácora Electrónica — avance Django + SQL Server

Esta versión parte del proyecto entregado y reemplaza los datos simulados por una capa preparada para consumir procedimientos almacenados de SQL Server mediante `pyodbc`.


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


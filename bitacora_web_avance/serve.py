"""Punto de arranque de produccion sobre Waitress.

Waitress es el servidor WSGI recomendado en Windows Server: gunicorn depende de
`fcntl` y no funciona alli. Este archivo existe para que el servicio de Windows
(NSSM) invoque un unico ejecutable sin argumentos:

    venv\\Scripts\\python.exe serve.py

El servidor escucha solo en la interfaz indicada por WAITRESS_HOST, que por
defecto es 127.0.0.1: quien publica el sitio a la red es el reverse proxy que
termina TLS, no este proceso.
"""
import os
from waitress import serve

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "bitacora_web.settings"
)

from bitacora_web.wsgi import application


host = os.getenv("WAITRESS_HOST", "127.0.0.1")
port = int(os.getenv("WAITRESS_PORT", "8001"))

print(f"Waitress escuchando en http://{host}:{port}")

serve(
    application,
    host=host,
    port=port,
    threads=8,
    ident="Bitacora Web",
)

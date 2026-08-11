import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitacora_web.settings')

import django
from django.conf import settings

print('DJANGO_SETTINGS_MODULE:', os.environ.get('DJANGO_SETTINGS_MODULE'))
print('DEMO_MODE:', settings.DEMO_MODE)
print('DB_SERVER:', os.getenv('DB_SERVER'))
print('DB_NAME:', os.getenv('DB_NAME'))
print('COMBUSTIBLE_TABLE:', os.getenv('COMBUSTIBLE_TABLE', 'dbo.dimm_con_maestro_registro_combust'))

try:
    django.setup()
    from bitacora.db import obtener_registros_combustible
    rows = obtener_registros_combustible()
    print('ROWS:', len(rows))
    for i, row in enumerate(rows[:5], 1):
        print(i, row)
except Exception as exc:
    print('EXCEPTION:')
    import traceback
    traceback.print_exc()

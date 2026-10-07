---
description: "Use when changing Ocupación de Espacios, its Buque filter, modal, SQL source, styles, or tests."
applyTo:
  - "bitacora_web_avance/bitacora/views.py"
  - "bitacora_web_avance/bitacora/services/ship_service.py"
  - "bitacora_web_avance/bitacora/templates/bitacora/ocupacion_espacios.html"
  - "bitacora_web_avance/bitacora/static/bitacora/js/ocupacion_espacios.js"
  - "bitacora_web_avance/bitacora/static/bitacora/css/ocupacion_espacios.css"
  - "bitacora_web_avance/bitacora/tests.py"
---

# Ocupación de Espacios

- Keep changes scoped to the Ocupación de Espacios module unless the user asks otherwise.
- Load the vessel list through `obtener_buques_info()` and the configured `SP_INFO_BUQUES` procedure (`dbo.SPJ_InfoBuques` by default). Use only its `Buque` column and expose it as `nombre`, displayed as `Nombre`.
- Do not fabricate vessel codes or IDs when the procedure returns only names. Use the selected names as the filter values unless the stored-procedure contract is explicitly changed.
- Keep vessel selection in the same page. Support multiple selections; only `Aceptar` commits them. `X`, `Cancelar`, Escape, and backdrop close without applying pending changes or navigating.
- Keep database settings in the local `.env`; never copy credentials into source code or instructions. Do not switch to demo mode or replace the SQL source to hide connection failures.
- Verify changes with the focused Ocupación de Espacios tests.
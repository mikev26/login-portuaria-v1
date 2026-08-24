"""Generación del archivo Excel del módulo de practicaje."""

from __future__ import annotations

import io
from typing import Any


COLUMNAS_PRACTICAJE = (
    ("Nro", "nro"),
    ("Registro", "registro"),
    ("Buque", "buque"),
    ("Bandera", "bandera"),
    ("IPB", "ipb"),
    ("Año", "ano"),
    ("Ubicación", "ubicacion"),
    ("Usuario", "usuario"),
    ("Operadora", "operadora"),
    ("TipoManiobra", "tipomaniobra"),
    ("Trimestre", "trimestre"),
    ("Fecha", "fecha"),
)


def crear_excel_practicaje(registros: list[dict[str, Any]]) -> bytes:
    """Construye el Excel con las filas ya mapeadas por el servicio."""
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "datos_practicaje"

    encabezados = [titulo for titulo, _ in COLUMNAS_PRACTICAJE]
    worksheet.append(encabezados)

    for cell in worksheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E79")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for registro in registros:
        worksheet.append([registro.get(clave, "") for _, clave in COLUMNAS_PRACTICAJE])

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    for column_cells in worksheet.columns:
        column_letter = column_cells[0].column_letter
        longest = max(len(str(cell.value or "")) for cell in column_cells)
        worksheet.column_dimensions[column_letter].width = min(max(longest + 2, 12), 30)

    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()

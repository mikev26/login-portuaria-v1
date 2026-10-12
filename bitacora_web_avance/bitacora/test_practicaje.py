from datetime import date
from io import BytesIO
from unittest.mock import patch

import openpyxl
from django.test import TestCase

from bitacora.services.practicaje import obtener_datos_practicaje
from bitacora.services.practicaje_excel import crear_excel_practicaje


class PracticajeDateRangeTests(TestCase):
    def setUp(self):
        session = self.client.session
        session["usuario_id"] = 12
        session.save()

    @patch("bitacora.services.practicaje.execute_procedure")
    def test_service_sends_date_range_parameters(self, execute_procedure):
        execute_procedure.return_value = [{"registro": "R-1", "buque": "Nave"}]

        result = obtener_datos_practicaje(
            date(2026, 1, 1),
            date(2026, 3, 31),
        )

        self.assertEqual(result[0]["registro"], "R-1")
        execute_procedure.assert_called_once_with(
            "dbo.SPJ_DatosPracticaje",
            (
                ("@s_fechaInit", date(2026, 1, 1)),
                ("@s_fechaFin", date(2026, 3, 31)),
            ),
        )

    @patch(
        "bitacora.practicaje_views.obtener_datos_practicaje",
        return_value=[{"nro": 1, "registro": "R-1"}],
    )
    def test_search_uses_date_range_and_enables_export_with_rows(self, get_data):
        response = self.client.get(
            "/datos-practicaje/",
            {"fecha_inicio": "2026-01-01", "fecha_fin": "2026-03-31"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="fecha_inicio"')
        self.assertContains(response, 'name="fecha_fin"')
        self.assertContains(response, 'data-has-rows="true"')
        self.assertNotContains(response, 'name="sano"')
        self.assertNotContains(response, 'name="sTrimestre"')
        get_data.assert_called_once_with(date(2026, 1, 1), date(2026, 3, 31))

    @patch("bitacora.practicaje_views.obtener_datos_practicaje")
    def test_invalid_range_does_not_query_or_enable_export(self, get_data):
        response = self.client.get(
            "/datos-practicaje/",
            {"fecha_inicio": "2026-04-01", "fecha_fin": "2026-03-31"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "La fecha inicial no puede ser posterior")
        self.assertContains(response, 'data-has-rows="false"')
        get_data.assert_not_called()

    def test_export_button_is_disabled_without_completed_search(self):
        response = self.client.get("/datos-practicaje/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="export-button"')
        self.assertContains(response, "disabled")
        self.assertContains(response, 'data-has-rows="false"')

    def test_excel_title_includes_selected_date_range(self):
        content = crear_excel_practicaje(
            [],
            fecha_inicio="2026-01-01",
            fecha_fin="2026-03-31",
        )
        workbook = openpyxl.load_workbook(BytesIO(content))

        self.assertIn(
            "DEL 2026-01-01 AL 2026-03-31",
            workbook.active["A1"].value,
        )

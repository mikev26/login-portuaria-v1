import io
from unittest.mock import patch

from django.test import TestCase
import openpyxl


class ProjectSmokeTest(TestCase):
    def test_fuel_report_keeps_date_filters_and_removes_informational_dates(
        self,
    ):
        session = self.client.session
        session["usuario_id"] = 7
        session.save()

        response = self.client.get("/registro-combustible/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "F.Desde")
        self.assertContains(response, "F.Hasta")
        self.assertContains(response, ">Liciencia</th>")
        self.assertContains(response, ">Estado</th>")
        self.assertContains(response, ">Tipo de Vehiculo</th>")
        header_start = response.content.index(b"<thead>")
        header_end = response.content.index(b"</thead>", header_start)
        headers = response.content[header_start:header_end]
        expected_headers = [
            b"Fecha",
            b"Tickets",
            b"Gu\xc3\xada",
            b"Placa",
            b"Chofer",
            b"Liciencia",
            b"CodBuque",
            b"Buque",
            b"Matr\xc3\xadcula",
            b"Galones",
            b"Motivo",
            b"Estado",
            b"Tipo de Vehiculo",
        ]
        positions = [headers.index(header) for header in expected_headers]
        self.assertEqual(positions, sorted(positions))
        self.assertNotContains(response, "header-fecha-desde")
        self.assertNotContains(response, "header-fecha-hasta")
        self.assertNotContains(response, "Fecha Desde")
        self.assertNotContains(response, "Fecha Hasta")

    @patch(
        "bitacora.views.obtener_reporte_combustible",
        return_value=[
            {
                "fecha_ingresa": "2025-02-14T09:59:49.780000",
                "tikect": "T-101",
                "guia": "G-22",
                "idplaca": "ABC-123",
                "chofer": "Conductor",
                "licencia": "LIC-01",
                "codbuque": "B-1",
                "buque": "Mar Azul",
                "matricula": "M-01",
                "galones": 25,
                "motivo": "Prueba",
                "estado": "Activo",
                "tipo_carro": "Camión",
            }
        ],
    )
    def test_fuel_report_ajax_maps_state_and_vehicle_type(
        self,
        mock_obtener_reporte,
    ):
        session = self.client.session
        session["usuario_id"] = 7
        session.save()

        response = self.client.get(
            "/registro-combustible/",
            {
                "fecha_inicio": "2025-02-01",
                "fecha_fin": "2025-02-28",
                "buscar": "1",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        row = response.json()["rows"][0]
        self.assertEqual(row["licencia"], "LIC-01")
        self.assertEqual(row["estado"], "Activo")
        self.assertEqual(row["tipo_carro"], "Camión")
        self.assertEqual(mock_obtener_reporte.call_count, 1)

    @patch(
        "bitacora.views._obtener_datos_exportacion",
        return_value={
            "fecha_desde": "2025-02-01",
            "fecha_hasta": "2025-02-28",
            "registros": [
                {
                    "fecha_ingresa": "2025-02-14T09:59:49.780000",
                    "c_tikect": "T-101",
                    "guia": "G-22",
                    "idplaca": "ABC-123",
                    "chofer": "Conductor",
                    "licencia": "LIC-01",
                    "codbuque": "B-1",
                    "buque": "Mar Azul",
                    "matricula": "M-01",
                    "galones": 25,
                    "motivo": "Prueba",
                    "estado": "Activo",
                    "tipo_carro": "Camión",
                }
            ],
        },
    )
    def test_fuel_excel_writes_required_headers_and_date_time_format(
        self,
        mock_export_data,
    ):
        session = self.client.session
        session["usuario_id"] = 7
        session.save()

        response = self.client.get("/registro-combustible/exportar-excel/")

        self.assertEqual(response.status_code, 200)
        workbook = openpyxl.load_workbook(io.BytesIO(response.content))
        worksheet = workbook.active
        self.assertEqual(
            [worksheet.cell(7, column).value for column in range(1, 14)],
            [
                "Fecha",
                "Tickets",
                "Guía",
                "Placa",
                "Chofer",
                "Liciencia",
                "CodBuque",
                "Buque",
                "Matrícula",
                "Galones",
                "Motivo",
                "Estado",
                "Tipo de Vehiculo",
            ],
        )
        self.assertEqual(
            worksheet["A8"].value.strftime("%Y-%m-%d %H:%M:%S"),
            "2025-02-14 09:59:49",
        )
        self.assertEqual(worksheet["A8"].value.microsecond, 0)
        self.assertEqual(
            worksheet["A8"].number_format,
            "yyyy-mm-dd hh:mm:ss",
        )
        self.assertEqual(worksheet["L8"].value, "Activo")
        self.assertEqual(worksheet["M8"].value, "Camión")
        mock_export_data.assert_called_once()

    def test_login_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bitácora Electrónica")

    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_login_success_creates_session_and_redirects(self, mock_validar, mock_turnos):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Jefe de turno"}]

        response = self.client.post(
            "/",
            {"usuario": "inspector.demo", "clave": "Demo1234"},
        )

        self.assertRedirects(response, "/bitacora/")
        session = self.client.session
        self.assertEqual(session["usuario_id"], 7)
        self.assertEqual(session["usuario_login"], "inspector.demo")
        self.assertEqual(session["usuario_nombre"], "Inspector Demo")
        self.assertEqual(session["usuario_cargo"], "Jefe de turno")

    @patch("bitacora.views.validar_usuario")
    def test_login_rejects_invalid_credentials(self, mock_validar):
        mock_validar.return_value = None

        response = self.client.post(
            "/",
            {"usuario": "maUsuario1", "clave": "123456"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Usuario o contraseña incorrectos.")

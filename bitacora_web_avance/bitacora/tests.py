from unittest.mock import patch

from django.test import TestCase, override_settings


@override_settings(DEMO_MODE=True)
class ProjectSmokeTest(TestCase):
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

    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def _authenticate(self, mock_validar, mock_turnos):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Inspector"}]

        response = self.client.post(
            "/",
            {"usuario": "inspector.demo", "clave": "Demo1234"},
        )
        self.assertRedirects(response, "/bitacora/")

    def test_tarifa_page_loads(self):
        self._authenticate()

        response = self.client.get("/tarifario/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tarifario")

    def test_report_page_loads(self):
        self._authenticate()

        response = self.client.get("/reporte/inec/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reportes INEC")

    def test_api_buscar_partida_requires_login(self):
        response = self.client.get("/api/buscar-partida/")
        self.assertEqual(response.status_code, 401)

    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_api_buscar_partida_returns_matching_results(self, mock_validar, mock_turnos):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Jefe de turno"}]

        # Authenticate via mocked login
        self.client.post(
            "/",
            {"usuario": "inspector.demo", "clave": "Demo1234"},
        )

        # Query with matching code "17"
        response = self.client.get("/api/buscar-partida/?codigo=17")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["data"]), 1)
        # Check that the first item contains key "codigo"
        self.assertIn("codigo", data["data"][0])

        # Query with no match "999"
        response = self.client.get("/api/buscar-partida/?codigo=999")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 0)

    @patch("bitacora.views.obtener_tarifas_existentes")
    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_tarifa_view_loads_tariffs_list(self, mock_validar, mock_turnos, mock_tarifas):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Jefe de turno"}]
        mock_tarifas.return_value = [
            {
                "id": "1",
                "codigo": "117",
                "activa": True,
                "tasa": "TASA CABOTAJE",
                "tasa_id": "5",
                "tarifa": "USO DE FACILIDADES DE ACCESO DE BUQUES",
                "partida_cod": "17.02.02.00.",
                "partida_desc": "Rentas por Arrendamientos de Bienes",
                "partida_cedula": "170202",
                "formula": "(Eslora * 1.25) * Dia",
                "detalle": "Tarifa regulada para barcos pesqueros y de cabotaje",
                "valor": "0.13",
                "s_ante": "10",
                "se_cobra_iva": False,
                "senae_cod": "S-99",
                "senae_desc": "Regulación nacional de cabotaje",
                "calc_param": "eslora",
                "calc_unidad": "dia",
                "ticket_srv": "ninguno",
                "json_data": '{"id": "1", "codigo": "117", "tasa": "TASA CABOTAJE", "tarifa": "USO DE FACILIDADES DE ACCESO DE BUQUES"}'
            }
        ]

        # Authenticate via mocked login
        self.client.post(
            "/",
            {"usuario": "inspector.demo", "clave": "Demo1234"},
        )

        response = self.client.get("/tarifa/")
        self.assertEqual(response.status_code, 200)

        response_popup = self.client.get("/tarifa/listado/")
        self.assertEqual(response_popup.status_code, 200)
        self.assertContains(response_popup, "Listado de Tarifas Existentes")
        self.assertContains(response_popup, "TASA CABOTAJE")
        self.assertContains(response_popup, "117")

    @patch("bitacora.views.guardar_tarifa")
    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_guardar_tarifa_view_calls_sp_and_returns_success(self, mock_validar, mock_turnos, mock_guardar):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Jefe de turno"}]
        mock_guardar.return_value = 1
        
        # Authenticate via mocked login
        self.client.post(
            "/",
            {"usuario": "inspector.demo", "clave": "Demo1234"},
        )
        
        response = self.client.post(
            "/tarifa/guardar/",
            {
                "codigo": "118",
                "tarifa": "TARIFA DE PRUEBA UNITARIA",
                "valor": "12.34",
                "partida_cod": "17.02.02.00.",
                "partida_id": "49",
                "tasa_id": "5",
                "formula": "TARIFA * 1.5",
                "detalle": "Prueba unitaria del guardado",
                "calc_unidad": "dia",
                "calc_param": "eslora",
                "iva": "1",
                "ticket_srv": "ninguno",
                "activa": "1",
            }
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["resul"], 1)
        mock_guardar.assert_called_once_with(
            idtarifa=0,
            codigo="118",
            tarifa="TARIFA DE PRUEBA UNITARIA",
            valor="12.34",
            partida_cod="17.02.02.00.",
            partida_id="49",
            tasa_id="5",
            formula="TARIFA * 1.5",
            detalle="Prueba unitaria del guardado",
            hora_dia=1,
            eslora_tneto=1,
            iva=1,
            ticket=0,
            activo=1,
            cambio_factura=0,
            aplica_inflacion=0,
        )

    @patch("bitacora.views.anular_tarifa")
    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_anular_tarifa_view_calls_db_and_returns_success(self, mock_validar, mock_turnos, mock_anular):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Jefe de turno"}]
        mock_anular.return_value = True

        # Authenticate via mocked login
        self.client.post(
            "/",
            {"usuario": "inspector.demo", "clave": "Demo1234"},
        )

        response = self.client.post(
            "/tarifa/anular/",
            {"id": "42"}
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        mock_anular.assert_called_once_with("42")

    @patch("bitacora.views.obtener_tarifas_existentes")
    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_exportar_tarifas_view_generates_excel(self, mock_validar, mock_turnos, mock_tarifas):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Jefe de turno"}]
        mock_tarifas.return_value = [
            {
                "codigo": "01",
                "tarifa": "USO DE MUELLES",
                "valor": "0.16",
                "formula": "TARIFA x ESLORA",
                "detalle": "Detalle de prueba",
                "partida_cod": "13.02.04.",
                "partida_desc": "PARTIDA DE PRUEBA",
            }
        ]

        # Authenticate via mocked login
        self.client.post(
            "/",
            {"usuario": "inspector.demo", "clave": "Demo1234"},
        )

        response = self.client.get("/tarifa/exportar/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        self.assertIn("attachment", response["Content-Disposition"])

    @patch("bitacora.views.guardar_inflacion")
    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_guardar_tarifa_inflacion_view_success(self, mock_validar, mock_turnos, mock_guardar):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Jefe de turno"}]
        mock_guardar.return_value = 1

        # Authenticate via mocked login
        self.client.post(
            "/",
            {"usuario": "inspector.demo", "clave": "Demo1234"},
        )

        # 1. Test saving > 0% inflation without date (should fail because date is always required)
        response = self.client.post(
            "/tarifa/inflacion/guardar/",
            {"porcentaje": "2.50"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": False, "error": "Debe especificar la fecha de inflación."})

        # 2. Test saving > 0% inflation with valid date but no detail (should succeed)
        response = self.client.post(
            "/tarifa/inflacion/guardar/",
            {"porcentaje": "2.50", "fecha_inflacion": "2026-08-26"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True, "resul": 1})
        
        from datetime import date
        current_year = date.today().year
        mock_guardar.assert_any_call(2.50, current_year, 7, detalle="", fecha_inflacion="2026-08-26")

        # 3. Test saving 0% inflation without date (should fail)
        response = self.client.post(
            "/tarifa/inflacion/guardar/",
            {"porcentaje": "0.00"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": False, "error": "Debe especificar la fecha de inflación."})

        # 4. Test saving 0% inflation with date but without detail (should fail because detail is required for 0%)
        response = self.client.post(
            "/tarifa/inflacion/guardar/",
            {"porcentaje": "0.00", "fecha_inflacion": "2026-08-26"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": False, "error": "Debe especificar el detalle o justificación cuando el porcentaje de inflación es 0%."})

        # 5. Test saving 0% inflation with detail and invalid date (should fail)
        response = self.client.post(
            "/tarifa/inflacion/guardar/",
            {"porcentaje": "0.00", "detalle": "Detalle de prueba", "fecha_inflacion": "2026/08/26"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": False, "error": "La fecha de inflación debe tener un formato válido (AAAA-MM-DD)."})

        # 6. Test saving 0% inflation with detail and valid date (should succeed)
        response = self.client.post(
            "/tarifa/inflacion/guardar/",
            {"porcentaje": "0.00", "detalle": "Detalle de prueba", "fecha_inflacion": "2026-08-26"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True, "resul": 1})
        mock_guardar.assert_any_call(0.00, current_year, 7, detalle="Detalle de prueba", fecha_inflacion="2026-08-26")

    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_guardar_tarifa_inflacion_view_invalid_percentage(self, mock_validar, mock_turnos):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Jefe de turno"}]

        # Authenticate
        self.client.post(
            "/",
            {"usuario": "inspector.demo", "clave": "Demo1234"},
        )

        # Negative percentage
        response = self.client.post(
            "/tarifa/inflacion/guardar/",
            {"porcentaje": "-1.50"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": False, "error": "El porcentaje debe estar entre 0.00 y 100.00."})

        # Not a number
        response = self.client.post(
            "/tarifa/inflacion/guardar/",
            {"porcentaje": "abc"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": False, "error": "El porcentaje de inflación debe ser un número válido."})

    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_exportar_tarifa_inflacion_pdf_view_authenticated(self, mock_validar, mock_turnos):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Jefe de turno"}]

        # Authenticate
        self.client.post(
            "/",
            {"usuario": "inspector.demo", "clave": "Demo1234"},
        )

        response = self.client.get(
            "/tarifa/inflacion/exportar-pdf/",
            {"porcentaje": "1.91", "anio": "2026", "fecha_inflacion": "2026-01-08"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("Tarifario_Inflacion_2026.pdf", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_exportar_tarifa_inflacion_pdf_view_unauthenticated(self):
        response = self.client.get("/tarifa/inflacion/exportar-pdf/")
        self.assertEqual(response.status_code, 302)

    @patch("bitacora.services.email_service.EmailMessage")
    def test_enviar_correo_ajuste_inflacion(self, mock_email_message):
        from bitacora.services.email_service import enviar_correo_ajuste_inflacion

        mock_instance = mock_email_message.return_value
        mock_instance.send.return_value = 1

        sample_tarifas = [
            {"codigo": "T01", "tarifa": "Uso de Muelle", "valor": 10.0}
        ]

        result = enviar_correo_ajuste_inflacion(
            porcentaje=2.50,
            anio=2026,
            fecha_inflacion="2026-08-26",
            detalle="Ajuste anual de prueba",
            usuario_nombre="Inspector Demo",
            tarifas=sample_tarifas,
        )

        self.assertTrue(result)
        mock_email_message.assert_called_once()
        mock_instance.attach.assert_called_once()
        mock_instance.send.assert_called_once()

    @patch("bitacora.views.obtener_tarifas_existentes")
    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_tarifa_inflacion_view_loads_all_active_tariffs(self, mock_validar, mock_turnos, mock_tarifas):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Jefe de turno"}]
        mock_tarifas.return_value = [
            {"id": "1", "codigo": "T01", "tarifa": "Tarifa Inflacion Si", "valor": "100.0000", "aplica_inflacion": 1},
            {"id": "2", "codigo": "T02", "tarifa": "Tarifa Inflacion No", "valor": "200.0000", "aplica_inflacion": 0},
        ]

        # Iniciar sesión
        self.client.post("/", {"usuario": "inspector.demo", "clave": "Demo1234"})

        response = self.client.get("/tarifa/inflacion/")
        self.assertEqual(response.status_code, 200)
        # Verifica que se consultó con estado=1 (todas las tarifas activas)
        mock_tarifas.assert_called_with(estado=1)
        # Verifica que en el HTML se renderizan ambas y con su respectivo data-aplica-inflacion
        content = response.content.decode("utf-8")
        self.assertIn('data-aplica-inflacion="1"', content)
        self.assertIn('data-aplica-inflacion="0"', content)
        self.assertIn("Tarifa Inflacion Si", content)
        self.assertIn("Tarifa Inflacion No", content)

    def test_generar_pdf_tarifario_inflacion_with_mixed_active_tariffs(self):
        from bitacora.services.pdf_inflacion import generar_pdf_tarifario_inflacion

        sample_tarifas = [
            {"codigo": "T01", "tarifa": "Con Inflacion", "valor": "100.00", "aplica_inflacion": 1},
            {"codigo": "T02", "tarifa": "Sin Inflacion", "valor": "50.00", "aplica_inflacion": 0},
        ]
        pdf_bytes = generar_pdf_tarifario_inflacion(
            tarifas=sample_tarifas,
            anio=2026,
            porcentaje=5.0,
            fecha_inflacion="2026-09-01",
            detalle="Prueba mixta",
        )
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_obtener_historico_tarifas_demo_mode(self):
        from bitacora.services.tarifario import (
            obtener_historico_tarifas,
            obtener_listado_cabeceras_historico,
        )

        with self.settings(DEMO_MODE=True):
            cabeceras = obtener_listado_cabeceras_historico()
            self.assertIsInstance(cabeceras, list)
            self.assertGreaterEqual(len(cabeceras), 1)
            self.assertEqual(cabeceras[0]["id_tarifaCab"], 1)

            historico = obtener_historico_tarifas(id_cabotaje=1, ano=2026)
            self.assertIsInstance(historico, list)
            self.assertGreaterEqual(len(historico), 2)
            self.assertEqual(historico[0]["codigo"], "01")
            self.assertEqual(historico[0]["aplica_inflacion"], 1)

    @patch("bitacora.services.tarifario.get_connection")
    def test_obtener_historico_tarifas_db_rows(self, mock_get_connection):
        from bitacora.services.tarifario import obtener_historico_tarifas

        mock_conn = mock_get_connection.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.description = [
            ("Nro", None, None, None, None, None, None),
            ("Tasa", None, None, None, None, None, None),
            ("Sctarifa", None, None, None, None, None, None),
            ("tarifa", None, None, None, None, None, None),
            ("valor", None, None, None, None, None, None),
            ("valor_anterior", None, None, None, None, None, None),
            ("inflacion", None, None, None, None, None, None),
            ("porcentajeInflacion", None, None, None, None, None, None),
            ("TarifaInflacion", None, None, None, None, None, None),
            ("ValorFinalTarifa", None, None, None, None, None, None),
            ("idtarifa", None, None, None, None, None, None),
            ("idtasa", None, None, None, None, None, None),
            ("activo", None, None, None, None, None, None),
            ("id_tarifaCab", None, None, None, None, None, None),
            ("ano", None, None, None, None, None, None),
            ("ano_anterior", None, None, None, None, None, None),
            ("fechaInflacion", None, None, None, None, None, None),
            ("detalle", None, None, None, None, None, None),
        ]
        mock_cursor.fetchall.return_value = [
            (1, "TASA CABOTAJE", "01", "USO DE MUELLES", "0.1600", "0.1600", 1, 2.0, "0.0032", "0.1632", 1, 5, 1, 6, 2026, 2025, "2026-08-27", "Prueba")
        ]

        with self.settings(DEMO_MODE=False):
            res = obtener_historico_tarifas(id_cabotaje=6, ano=2026)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]["id_tarifaCab"], 6)
            self.assertEqual(res[0]["activo"], True)

    @patch("bitacora.views.obtener_historico_tarifas")
    def test_obtener_historico_tarifas_view(self, mock_obtener):
        mock_obtener.return_value = [
            {
                "id_tarifaCab": 8,
                "ano": 2026,
                "ano_anterior": 2025,
                "fecha_inflacion": "2026-08-31",
                "porcentaje_inflacion": 1.02,
                "porcentaje_actual": 1.02,
                "detalle": "Hola",
            }
        ]
        self._authenticate()
        response = self.client.get("/tarifa/inflacion/historico/?anio=2026")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["metadata"]["porcentaje_inflacion"], 1.02)
        self.assertEqual(json_data["metadata"]["detalle"], "Hola")

    @patch("bitacora.views.obtener_listado_cabeceras_historico")
    def test_obtener_historico_tarifas_view_listar_cabeceras(self, mock_listado):
        mock_listado.return_value = [
            {
                "id_tarifaCab": 8,
                "ano": 2026,
                "porcentaje_actual": 2.5,
                "detalle": "Ajuste 2026",
                "fecha_inflacion": "2026-01-15",
                "fecha_registro": "2026-01-15 10:30",
            }
        ]
        self._authenticate()
        response = self.client.get("/tarifa/inflacion/historico/?listar_cabeceras=1")
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(len(json_data["cabeceras"]), 1)
        self.assertEqual(json_data["cabeceras"][0]["ano"], 2026)

    @patch("bitacora.views.obtener_historico_tarifas")
    def test_exportar_tarifa_inflacion_pdf_view_historico(self, mock_obtener):
        mock_obtener.return_value = [
            {
                "codigo": "306",
                "tarifa": "Prueba de tarifa exitosa",
                "valor": "10.5320",
                "valor_anterior": "10.5320",
                "aplica_inflacion": 0,
                "tarifa_inflacion": "0.0000",
                "valor_final": "10.5320",
                "id_tarifaCab": 6,
                "ano": 2026,
                "porcentaje_actual": 0.10,
                "fecha_inflacion": "2026-08-27",
                "detalle": "Prueba historico PDF",
            }
        ]
        self._authenticate()
        response = self.client.get("/tarifa/inflacion/exportar-pdf/?anio=2026&es_historico=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("Tarifario_Inflacion_Historico_2026.pdf", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))







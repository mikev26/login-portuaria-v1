from unittest.mock import patch

from django.test import TestCase, override_settings

from bitacora.services.datos_abiertos import obtener_reporte_datos_abiertos


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

    @override_settings(DEMO_MODE=False)
    @patch("bitacora.services.datos_abiertos.execute_procedure")
    def test_datos_abiertos_backend_uses_numeric_semester_for_sp(self, mock_execute):
        mock_execute.return_value = [
            {
                "REGISTRO": 101,
                "CODBUQUE": "B-99",
                "MATRÍCULA": "M-345",
                "BUQUE": "Estrella del Mar",
                "TipoNave": "Pesquero",
                "Arribo": "2026-05-08 07:15:00",
                "Zarpe": "2026-05-09 18:40:00",
                "Bandera": "ECUADOR",
                "TRB": "10.50",
                "TRN": "8.10",
                "Agencia": "AGENCIA PORTUARIA MANTA S.A.",
                "TotalDescarga": "2450",
            }
        ]

        resultado = obtener_reporte_datos_abiertos(2026, "1er")

        self.assertEqual(resultado[0]["Registro"], 101)
        mock_execute.assert_called_once_with(
            "dbo.SPJ_DatosAbiertosTPyC",
            (("@sPeriodo", 2026), ("@sSemestre", 1)),
        )

    @patch("bitacora.views.obtener_reporte_datos_abiertos")
    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_datos_abiertos_loads_and_filters(self, mock_validar, mock_turnos, mock_reporte):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Inspector"}]
        mock_reporte.return_value = [
            {
                "REGISTRO": 101,
                "CODBUQUE": "B-99",
                "MATRÍCULA": "M-345",
                "BUQUE": "Estrella del Mar",
                "TipoNave": "Pesquero",
                "Arribo": "2026-05-08 07:15:00",
                "Zarpe": "2026-05-09 18:40:00",
                "Bandera": "ECU",
                "TRB": "10.50",
                "TRN": "8.10",
                "Agencia": "APM",
                "TotalDescarga": "2450",
            }
        ]

        self.client.post(
            "/",
            {"usuario": "inspector.demo", "clave": "Demo1234"},
        )

        response = self.client.get("/datos-abiertos/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Datos Abiertos")

        response_ajax = self.client.get(
            "/datos-abiertos/?anio=2026&semestre=1er&buscar=1",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response_ajax.status_code, 200)
        json_data = response_ajax.json()
        self.assertEqual(json_data["anio"], "2026")
        self.assertEqual(json_data["semestre"], "1er")
        self.assertEqual(len(json_data["rows"]), 1)
        self.assertEqual(json_data["rows"][0]["Registro"], 101)
        self.assertEqual(json_data["rows"][0]["CodBuque"], "B-99")
        self.assertEqual(json_data["rows"][0]["Total Descarga"], "2450")


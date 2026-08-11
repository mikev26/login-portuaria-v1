from unittest.mock import patch

from django.test import TestCase


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
        self.assertContains(response, "Listado de Tarifas Existentes")
        self.assertContains(response, "TASA CABOTAJE")
        self.assertContains(response, "117")

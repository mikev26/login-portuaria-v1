from datetime import date
from unittest.mock import patch

from django.test import TestCase, override_settings

from bitacora.services.db_connection import (
    DatabaseConfigurationError,
    DatabaseContractError,
    get_connection,
    pyodbc,
)
from bitacora.services.datos_abiertos import obtener_reporte_datos_abiertos
from bitacora.services.ship_service import (
    obtener_buques_info,
    obtener_registros_ocupacion,
)


@override_settings(DEMO_MODE=True)
class ProjectSmokeTest(TestCase):
    @patch("bitacora.services.ship_service.execute_procedure")
    @patch("bitacora.services.ship_service.timezone.localdate")
    def test_obtener_registros_ocupacion_uses_fixed_dates_and_database(
        self,
        mock_localdate,
        mock_execute_procedure,
    ):
        mock_localdate.return_value = date(2026, 10, 7)
        mock_execute_procedure.return_value = [
            {
                "scregistro": "REG-001",
                "buque": "Mar Azul",
                "otra_columna": "No exponer",
            }
        ]

        registros = obtener_registros_ocupacion()

        self.assertEqual(
            registros,
            [{"scregistro": "REG-001", "buque": "Mar Azul"}],
        )
        mock_execute_procedure.assert_called_once_with(
            "dbo.SPJ_ReporteRegistroBuques",
            (
                ("@s_fechaInit", date(2010, 1, 1)),
                ("@s_fechaFin", date(2026, 10, 8)),
            ),
            database_name="dim_sis_puerto_v1",
        )

    @patch("bitacora.services.ship_service.execute_procedure")
    def test_obtener_registros_ocupacion_rejects_missing_columns(
        self,
        mock_execute_procedure,
    ):
        mock_execute_procedure.return_value = [
            {"scregistro": "REG-001", "nombre": "Mar Azul"}
        ]

        with self.assertRaisesRegex(
            DatabaseContractError,
            "scregistro y buque",
        ):
            obtener_registros_ocupacion()

    @patch.dict(
        "os.environ",
        {
            "DB_SERVER": "sql.example.test",
            "DB_NAME": "port_database",
            "DB_USER": "app-user",
            "DB_PASSWORD": "test-password",
            "DB_TRUSTED_CONNECTION": "no",
        },
    )
    @patch("bitacora.services.db_connection.pyodbc.connect")
    def test_connection_error_identifies_network_and_vpn_checks(
        self,
        mock_connect,
    ):
        mock_connect.side_effect = pyodbc.OperationalError(
            "08001",
            "network endpoint unavailable",
        )

        with self.assertRaisesRegex(
            DatabaseConfigurationError,
            "red o VPN institucional",
        ):
            get_connection()

    def test_login_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bitácora Electrónica")

    @patch("bitacora.services.ship_service.execute_procedure")
    @patch("bitacora.services.ship_service.validated_procedure")
    def test_obtener_buques_info_returns_only_ship_names(
        self,
        mock_validated_procedure,
        mock_execute_procedure,
    ):
        mock_validated_procedure.return_value = "dbo.SPJ_InfoBuques"
        mock_execute_procedure.return_value = [
            {"buque": "Mar Azul", "idbuque": 14},
            {"buque": "  ", "idbuque": 15},
            {"otra_columna": "Ignorar"},
        ]

        buques = obtener_buques_info()

        self.assertEqual(buques, [{"nombre": "Mar Azul"}])
        mock_validated_procedure.assert_called_once_with("SP_INFO_BUQUES")
        mock_execute_procedure.assert_called_once_with("dbo.SPJ_InfoBuques")

    @patch("bitacora.views.obtener_buques_info")
    def test_occupacion_view_renders_buque_selection_modal(self, mock_obtener_buques):
        mock_obtener_buques.return_value = [{"nombre": "Mar Azul"}]
        session = self.client.session
        session["usuario_id"] = 7
        session.save()

        response = self.client.get("/ocupacion-espacios/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["buques"], [{"nombre": "Mar Azul"}])
        self.assertContains(response, 'id="buquesModal"')
        self.assertContains(response, ">Nombre</th>")
        mock_obtener_buques.assert_called_once_with()

    @patch("bitacora.views.obtener_buques_info", return_value=[])
    def test_occupacion_view_renders_register_modal_and_api_url(
        self,
        mock_obtener_buques,
    ):
        session = self.client.session
        session["usuario_id"] = 7
        session.save()

        response = self.client.get("/ocupacion-espacios/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="registrosModal"')
        self.assertContains(response, 'id="registrosModalBody"')
        self.assertContains(response, "ocupacion-espacios/registros/")
        self.assertContains(response, ">Registro</th>")
        self.assertContains(response, ">Buque</th>")
        mock_obtener_buques.assert_called_once_with()

    @patch(
        "bitacora.views.obtener_registros_ocupacion",
        return_value=[{"scregistro": "REG-001", "buque": "Mar Azul"}],
    )
    def test_occupacion_register_api_returns_only_requested_fields(
        self,
        mock_obtener_registros,
    ):
        session = self.client.session
        session["usuario_id"] = 7
        session.save()

        response = self.client.get("/ocupacion-espacios/registros/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"registros": [{"scregistro": "REG-001", "buque": "Mar Azul"}]},
        )
        mock_obtener_registros.assert_called_once_with()

    def test_occupacion_register_api_requires_login(self):
        response = self.client.get("/ocupacion-espacios/registros/")

        self.assertEqual(response.status_code, 401)

    @patch("bitacora.views.obtener_buques_info")
    def test_occupacion_view_handles_database_connection_error_gracefully(self, mock_obtener_buques):
        mock_obtener_buques.side_effect = DatabaseConfigurationError(
            "No fue posible conectar a SQL Server."
        )
        session = self.client.session
        session["usuario_id"] = 7
        session.save()

        response = self.client.get("/ocupacion-espacios/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["buques"], [])
        self.assertContains(response, 'id="ocupacionBuquesData"')

    @patch("bitacora.views.obtener_buques_info", return_value=[])
    def test_occupacion_view_serializes_empty_ship_list_as_array(
        self,
        mock_obtener_buques,
    ):
        session = self.client.session
        session["usuario_id"] = 7
        session.save()

        response = self.client.get("/ocupacion-espacios/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<script id="ocupacionBuquesData" type="application/json">[]</script>',
            html=True,
        )
        mock_obtener_buques.assert_called_once_with()

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

    @patch("bitacora.views.validar_usuario")
    def test_login_displays_network_guidance_when_sql_server_is_unreachable(
        self,
        mock_validar,
    ):
        mock_validar.side_effect = DatabaseConfigurationError(
            "No fue posible alcanzar SQL Server por la red "
            "(ODBC 08001). Conéctese a la red o VPN institucional."
        )

        response = self.client.post(
            "/",
            {"usuario": "usuario.institucional", "clave": "no-real-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ODBC 08001")
        self.assertContains(response, "VPN institucional")

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

        response = self.client.get("/tarifa/")

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
            ptipo=1,
        )

    @patch("bitacora.views.guardar_tarifa")
    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_guardar_tarifa_ptipo_mapping(self, mock_validar, mock_turnos, mock_guardar):
        mock_validar.return_value = {"idusuario": 7, "usuario": "demo", "nombre": "Demo", "cargo": "Inspector"}
        mock_turnos.return_value = [{"cargo": "Jefe de turno"}]
        mock_guardar.return_value = 1
        self.client.post("/", {"usuario": "demo", "clave": "Demo1234"})

        casos = [
            ("eslora", 1, 1),
            ("ton_bruto", 0, 2),
            ("t_neto", 2, 4),
            ("otros", 0, 3),
            ("desconocido", 0, 3),
        ]

        for param_val, expected_ptipo, expected_eslora in casos:
            mock_guardar.reset_mock()
            res = self.client.post("/tarifa/guardar/", {
                "codigo": "199",
                "tarifa": f"TARIFA {param_val}",
                "valor": "10.00",
                "partida_cod": "17.02.02.00.",
                "partida_id": "49",
                "tasa_id": "5",
                "formula": "TARIFA * 1",
                "detalle": "Detalle",
                "calc_unidad": "dia",
                "calc_param": param_val,
                "iva": "0",
                "ticket_srv": "ninguno",
                "activa": "1",
            })
            self.assertEqual(res.status_code, 200)
            self.assertEqual(mock_guardar.call_args[1]["ptipo"], expected_ptipo, f"Fallo ptipo para param={param_val}")
            self.assertEqual(mock_guardar.call_args[1]["eslora_tneto"], expected_eslora, f"Fallo eslora_tneto para param={param_val}")

    @patch("bitacora.views.guardar_tarifa")
    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_guardar_tarifa_view_missing_partida_or_formula(self, mock_validar, mock_turnos, mock_guardar):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Jefe de turno"}]
        self.client.post("/", {"usuario": "inspector.demo", "clave": "Demo1234"})

        # Sin partida_cod
        res1 = self.client.post("/tarifa/guardar/", {
            "codigo": "118",
            "tarifa": "TARIFA PRUEBA",
            "tasa_id": "5",
            "partida_cod": "",
            "formula": "TARIFA * 1.5",
        })
        self.assertEqual(res1.status_code, 200)
        self.assertFalse(res1.json()["success"])
        self.assertIn("Faltan campos obligatorios", res1.json()["error"])

        # Sin formula
        res2 = self.client.post("/tarifa/guardar/", {
            "codigo": "118",
            "tarifa": "TARIFA PRUEBA",
            "tasa_id": "5",
            "partida_cod": "17.02.02.00.",
            "formula": "",
        })
        self.assertEqual(res2.status_code, 200)
        self.assertFalse(res2.json()["success"])
        self.assertIn("Faltan campos obligatorios", res2.json()["error"])
        mock_guardar.assert_not_called()

        # Con valor negativo
        res3 = self.client.post("/tarifa/guardar/", {
            "codigo": "118",
            "tarifa": "TARIFA PRUEBA",
            "tasa_id": "5",
            "partida_cod": "17.02.02.00.",
            "formula": "TARIFA * 1.5",
            "valor": "-10.50",
        })
        self.assertEqual(res3.status_code, 200)
        self.assertFalse(res3.json()["success"])
        self.assertIn("no puede ser negativo", res3.json()["error"])
        mock_guardar.assert_not_called()

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

    @patch("bitacora.views.enviar_correo_ajuste_inflacion")
    @patch("bitacora.views.guardar_inflacion")
    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_guardar_tarifa_inflacion_view_success(self, mock_validar, mock_turnos, mock_guardar, mock_email):
        mock_validar.return_value = {
            "idusuario": 7,
            "usuario": "inspector.demo",
            "nombre": "Inspector Demo",
            "cargo": "Inspector",
        }
        mock_turnos.return_value = [{"cargo": "Inspector"}]
        mock_guardar.return_value = 1

        session = self.client.session
        session["usuario_id"] = 7
        session.save()

        # Test positive inflation
        response_pos = self.client.post(
            "/tarifa/inflacion/guardar/",
            {"porcentaje": "2.5", "fecha_inflacion": "2026-01-15", "detalle": "Ajuste positivo"}
        )
        self.assertEqual(response_pos.status_code, 200)
        self.assertTrue(response_pos.json()["success"])

        # Test negative inflation
        response_neg = self.client.post(
            "/tarifa/inflacion/guardar/",
            {"porcentaje": "-2.5", "fecha_inflacion": "2026-01-15", "detalle": "Ajuste negativo"}
        )
        self.assertEqual(response_neg.status_code, 200)
        self.assertTrue(response_neg.json()["success"])

    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_datos_abiertos_exportar_sin_busqueda_previa(self, mock_validar, mock_turnos):
        mock_validar.return_value = {"idusuario": 7, "usuario": "demo", "nombre": "Demo", "cargo": "Inspector"}
        mock_turnos.return_value = [{"cargo": "Inspector"}]
        self.client.post("/", {"usuario": "demo", "clave": "Demo1234"})

        response = self.client.get("/datos-abiertos/exportar-excel/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["messages"][0]["text"], "Primero debe realizar una búsqueda antes de exportar la información.")

    @patch("bitacora.views.obtener_reporte_datos_abiertos")
    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_datos_abiertos_exportar_sin_registros(self, mock_validar, mock_turnos, mock_reporte):
        mock_validar.return_value = {"idusuario": 7, "usuario": "demo", "nombre": "Demo", "cargo": "Inspector"}
        mock_turnos.return_value = [{"cargo": "Inspector"}]
        mock_reporte.return_value = []
        self.client.post("/", {"usuario": "demo", "clave": "Demo1234"})

        response = self.client.get("/datos-abiertos/exportar-excel/?anio=2026&semestre=1er&buscar=1", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["messages"][0]["text"], "No existen registros para exportar.")

    @patch("bitacora.views.obtener_reporte_datos_abiertos")
    @patch("bitacora.views.obtener_turnos_usuario")
    @patch("bitacora.views.validar_usuario")
    def test_datos_abiertos_exportar_exitoso(self, mock_validar, mock_turnos, mock_reporte):
        mock_validar.return_value = {"idusuario": 7, "usuario": "demo", "nombre": "Demo", "cargo": "Inspector"}
        mock_turnos.return_value = [{"cargo": "Inspector"}]
        mock_reporte.return_value = [
            {
                "Registro": 101,
                "CodBuque": "B-99",
                "Matrícula": "M-345",
                "Buque": "Estrella del Mar",
                "TipoNave": "Pesquero",
                "Arribo": "2026-05-08",
                "Zarpe": "2026-05-09",
                "Bandera": "ECU",
                "TRB": 10.5,
                "TRN": 8.1,
                "Agencia": "APM",
                "TotalDescarga": 2450,
            }
        ]
        self.client.post("/", {"usuario": "demo", "clave": "Demo1234"})

        response = self.client.get("/datos-abiertos/exportar-excel/?anio=2026&semestre=1er&buscar=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn("F004_GSW_DATO", response["Content-Disposition"])

let listaBuques = [];
        document.addEventListener("DOMContentLoaded", function() {
            fetch('/api/buques')
                .then(response => response.json())
                .then(data => {
                    if (Array.isArray(data)) {
                        listaBuques = data;
                    } else if (data.buques && Array.isArray(data.buques)) {
                        listaBuques = data.buques;
                    } else {
                        let claveArreglo = Object.keys(data).find(k => Array.isArray(data[k]));
                        listaBuques = claveArreglo ? data[claveArreglo] : [];
                    }
                    console.log("Buques cargados exitosamente:", listaBuques.length);
                })
                .catch(error => console.error("Error al cargar buques:", error));
        });

        // Función JavaScript para activar la descarga del reporte conectándose al Flask
        function descargarReporteBuques(ubicacion) {
            const tipoInfo = document.querySelector('input[name="tipoInformacion"]:checked').value;
            const url = `/api/exportar-buques?ubicacion=${ubicacion}&tipo=${tipoInfo}`;
            
            const a = document.createElement('a');
            a.href = url;
            a.download = '';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }

        const inputBuscador = document.getElementById('buscadorBuque');
        const listaSugerencias = document.getElementById('sugerenciasLista');

        inputBuscador.addEventListener('input', function() {
            let texto = this.value.toLowerCase().trim();
            listaSugerencias.innerHTML = '';
            if (texto.length === 0) return;

            let filtrados = listaBuques.filter(b => {
                let nombreBuque = b.buque || "";
                return nombreBuque.toLowerCase().includes(texto);
            });

            filtrados.slice(0, 10).forEach(buque => {
                let nombre = buque.buque || "Sin nombre";
                let idBuq = buque.idbuque;

                let item = document.createElement('div');
                item.className = 'dropdown-item';
                item.innerText = nombre;

                item.addEventListener('click', function() {
                    inputBuscador.value = nombre;
                    listaSugerencias.innerHTML = '';

                    llenarDatos(buque);
                    cargarDatosRegistro(idBuq);
                });

                listaSugerencias.appendChild(item);
            });
        });

        inputBuscador.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();

                let texto = this.value.toLowerCase().trim();

                let encontrado = listaBuques.find(b => {
                    let nombre = b.buque || "";
                    return (
                        nombre.toLowerCase() === texto ||
                        nombre.toLowerCase().includes(texto)
                    );
                });

                if (encontrado) {
                    let idBuq = encontrado.idbuque;

                    listaSugerencias.innerHTML = '';

                    inputBuscador.value = encontrado.buque || "";

                    llenarDatos(encontrado);
                    cargarDatosRegistro(idBuq);
                }
            }
        });

        document.addEventListener('click', function(e) {
            if (!inputBuscador.contains(e.target) && !listaSugerencias.contains(e.target)) {
                listaSugerencias.innerHTML = '';
            }
        });

        function llenarDatos(b) {
            document.getElementById('lblCodBuque').innerText = b.codbuque || '-';
            document.getElementById('lblMatricula').innerText = b.matricula || '-';
            document.getElementById('lblBandera').innerText = b.bandera || '-';
            document.getElementById('lblTipoNave').innerText = b.tipo_nave || '-';
            document.getElementById('lblEslora').innerText = b.eslora || '-';
            document.getElementById('lblManga').innerText = b.manga || '-';
            document.getElementById('lblCalado').innerText = b.calado || '-';
            document.getElementById('lblTRB').innerText = b.trb || '-';
            document.getElementById('lblTRN').innerText = b.trn || '-';

            document.getElementById('lblDetalle').innerText =
                (b.detalle && String(b.detalle).trim() !== "")
                    ? b.detalle
                    : 'Sin observaciones registradas.';

            document.getElementById('lblAgencia').innerText = b.agencia || '-';
            document.getElementById('lblArmador').innerText = b.armador || '-';
            document.getElementById('lblTelfArmador').innerText = b.telf_armador || '-';
            document.getElementById('lblUsuario').innerText = b.usuario || '-';
            document.getElementById('lblTelfUsuario').innerText = b.telf_usuario || '-';

            let saldo = b.debe !== undefined && b.debe !== null
                ? parseFloat(b.debe)
                : 0;

            document.getElementById('lblDebe').innerText =
                "$" + (isNaN(saldo) ? "0.00" : saldo.toFixed(2));
        }

        function cargarDatosRegistro(idBuque) {
            if (!idBuque) return;
            fetch(`/api/registros?buque=${idBuque}`)
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('tablaHistoricosBody');
                    tbody.innerHTML = '';

                    let arrayRegistros = [];
                    if (Array.isArray(data)) {
                        arrayRegistros = data;
                    } else if (data.registros && Array.isArray(data.registros)) {
                        arrayRegistros = data.registros;
                    } else {
                        let claveArreglo = Object.keys(data).find(k => Array.isArray(data[k]));
                        arrayRegistros = claveArreglo ? data[claveArreglo] : [];
                    }

                    if (arrayRegistros.length === 0) {
                        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted fst-italic py-4">Sin datos históricos por el momento...</td></tr>`;
                        document.getElementById('tablaOperadoresBody').innerHTML = `<tr><td colspan="8" class="text-center text-muted fst-italic py-4">No hay operadores para este buque.</td></tr>`;
                        return;
                    }

                    arrayRegistros.forEach((reg, index) => {
                        let llaves = Object.keys(reg);
                        let claveSolicitud = llaves.find(k => k.toLowerCase().includes('solic'));
                        let solicitudTexto = claveSolicitud ? reg[claveSolicitud] : (reg.solicitud || reg.Solicitud || reg.nro_solicitud || reg.idsolicitud || reg.id_solicitud || '-');
                        
                        let claveRegistro = llaves.find(k => k.toLowerCase().includes('reg') || k.toLowerCase().includes('sreg'));
                        let idRegistro = claveRegistro ? reg[claveRegistro] : (reg.registro || reg.sregistro || reg.idregistro || '-');

                        let valFechaArribo = reg.fecha_arrivo || reg.fecha_arribo || reg.arribo;
                        let fechaArribo = valFechaArribo ? new Date(valFechaArribo).toLocaleString() : '-';

                        let valFechaZarpe = reg.fecha_zarpe || reg.zarpe;
                        let fechaZarpe = valFechaZarpe ? new Date(valFechaZarpe).toLocaleString() : 'En puerto / NULL';
                        
                        let agencia = reg.agencia || reg.nombre_agencia || '-';

                        if (index === 0) {
                            document.getElementById('lblSolicitud').innerText = solicitudTexto;
                            document.getElementById('lblFechaArrivo').innerText = fechaArribo;
                            document.getElementById('lblFechaZarpe').innerText = fechaZarpe;
                            document.getElementById('lblAgenciaReg').innerText = agencia;
                            
                            if (solicitudTexto && solicitudTexto !== '-') {
                                cargarOperadoresPorSolicitud(solicitudTexto);
                            }
                        }

                        let tr = document.createElement('tr');
                        tr.innerHTML = `<td class="fw-semibold">${solicitudTexto}</td><td>${idRegistro}</td><td>${fechaArribo}</td><td>${fechaZarpe}</td><td>${agencia}</td>`;
                        tbody.appendChild(tr);
                    });
                })
                .catch(error => console.error("Error al cargar datos históricos:", error));
        }

        function cargarOperadoresPorSolicitud(idsolicitud) {
            fetch(`/api/operadores_movimiento?idsolicitud=${idsolicitud}`)
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('tablaOperadoresBody');
                    tbody.innerHTML = '';

                    let arrayOps = [];
                    if (Array.isArray(data)) {
                        arrayOps = data;
                    } else if (data.operadores && Array.isArray(data.operadores)) {
                        arrayOps = data.operadores;
                    } else {
                        let claveArreglo = Object.keys(data).find(k => Array.isArray(data[k]));
                        arrayOps = claveArreglo ? data[claveArreglo] : [];
                    }

                    if (arrayOps.length === 0) {
                        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted fst-italic py-4">No hay operadores relacionados para esta solicitud.</td></tr>`;
                        return;
                    }

                    arrayOps.forEach(op => {
                        let idsolicitudVal = op.idsolicitud || op.solicitud || '-';
                        let usuario = op.usuario || op.nombre_usuario || '-';
                        let tipoOperador = op.tipoOperador || op.tipooperador || '-';
                        let idoperador = op.idoperador || '-';
                        let idusuario = op.idusuario || '-';
                        let codigo = op.Codigo || op.codigo ||'-';
                        let estado = op.Estado || op.estado || '-';
                        
                        let valVence = op.vence || op.fecha_vencimiento;
                        let vence = valVence ? new Date(valVence).toLocaleDateString() : '-';

                        let tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${idsolicitudVal}</td>
                            <td>${usuario}</td>
                            <td>${tipoOperador}</td>
                            <td>${idoperador}</td>
                            <td>${idusuario}</td>
                            <td class="fw-semibold">${codigo}</td>
                            <td><span class="badge bg-secondary">${estado}</span></td>
                            <td>${vence}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                })
                .catch(error => console.error("Error al cargar operadores por solicitud:", error));
        }

        function abrirModalOperadores() {
            var modal = new bootstrap.Modal(document.getElementById('modalOperadores'));
            modal.show();

            fetch('/api/operadores_listados')
                .then(response => response.json())
                .then(data => {
                    let arrayModal = [];
                    if (Array.isArray(data)) {
                        arrayModal = data;
                    } else if (data.operadores && Array.isArray(data.operadores)) {
                        arrayModal = data.operadores;
                    } else {
                        let claveArreglo = Object.keys(data).find(k => Array.isArray(data[k]));
                        arrayModal = claveArreglo ? data[claveArreglo] : [];
                    }

                    if (arrayModal.length === 0) return;
                    
                    let keys = Object.keys(arrayModal[0]);
                    let thead = document.querySelector('#tablaModalOperadores thead');
                    let tbody = document.querySelector('#tablaModalOperadores tbody');
                    
                    thead.innerHTML = '<tr>' + keys.map(k => `<th>${k}</th>`).join('') + '</tr>';
                    tbody.innerHTML = '';

                    arrayModal.forEach(op => {
                        let tr = document.createElement('tr');
                        tr.innerHTML = keys.map(k => `<td>${op[k] !== null ? op[k] : '-'}</td>`).join('');
                        tbody.appendChild(tr);
                    });
                })
                .catch(error => console.error("Error al cargar listado general de operadores:", error));
        }

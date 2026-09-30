document.addEventListener('DOMContentLoaded', () => {
        const selectAnio = document.getElementById('selectAnio');
        const inputInflacion = document.getElementById('inputInflacion');
        const btnAplicar = document.getElementById('btnAplicar');
        const btnExportar = document.getElementById('btnExportar');
        const btnGuardar = document.getElementById('btnGuardar');
        const headerValorTarifa = document.getElementById('headerValorTarifa');
        const placeholderMessage = document.getElementById('placeholderMessage');
        const tablaTarifasWrapper = document.getElementById('tablaTarifasWrapper');
        const inputDetalle = document.getElementById('inputDetalle');
        const inputFechaInflacion = document.getElementById('inputFechaInflacion');
        const btnHistorial = document.getElementById('btnHistorial');
        
        // Elementos del Modal Personalizado de Confirmación de Guardado
        const confirmModalOverlay = document.getElementById('confirmModalOverlay');
        const modalMessageText = document.getElementById('modalMessageText');
        const btnModalClose = document.getElementById('btnModalClose');
        const btnModalCancel = document.getElementById('btnModalCancel');
        const btnModalConfirm = document.getElementById('btnModalConfirm');

        // Elementos del Modal de Alerta de Fecha Fuera de Enero
        const dateAlertModalOverlay = document.getElementById('dateAlertModalOverlay');
        const dateAlertMessageText = document.getElementById('dateAlertMessageText');
        const btnDateAlertClose = document.getElementById('btnDateAlertClose');
        const btnDateAlertCorrect = document.getElementById('btnDateAlertCorrect');
        const btnDateAlertContinue = document.getElementById('btnDateAlertContinue');

        // Elementos del Modal 1 (Ingreso de Año)
        const historicoModalOverlay = document.getElementById('historicoModalOverlay');
        const inputModalAno = document.getElementById('inputModalAno');
        const btnHistoricoModalClose = document.getElementById('btnHistoricoModalClose');
        const btnHistoricoModalCancel = document.getElementById('btnHistoricoModalCancel');
        const btnHistoricoModalCargar = document.getElementById('btnHistoricoModalCargar');

        // Elementos del Modal 2 (Tabla de Resultados Históricos)
        const resultadoHistoricoModalOverlay = document.getElementById('resultadoHistoricoModalOverlay');
        const btnResultadoHistoricoModalClose = document.getElementById('btnResultadoHistoricoModalClose');
        const btnResultadoHistoricoModalCerrar = document.getElementById('btnResultadoHistoricoModalCerrar');
        const btnResultadoHistoricoSelectAll = document.getElementById('btnResultadoHistoricoSelectAll');
        const btnResultadoHistoricoAceptar = document.getElementById('btnResultadoHistoricoAceptar');
        const chkModalSelectAllHeader = document.getElementById('chkModalSelectAllHeader');
        const tablaResultadoHistoricoBody = document.getElementById('tablaResultadoHistoricoBody');
        const lblHistoricoModalAno = document.getElementById('lblHistoricoModalAno');
        const headerModalTarifaAnioAnterior = document.getElementById('headerModalTarifaAnioAnterior');
        const headerModalTarifaAnioActual = document.getElementById('headerModalTarifaAnioActual');

        // Elementos de Modo Histórico en Pantalla Principal
        const btnVolverRegistro = document.getElementById('btnVolverRegistro');
        const tablaTarifasBody = document.getElementById('tablaTarifasBody');
        const originalTablaTarifasHTML = tablaTarifasBody ? tablaTarifasBody.innerHTML : '';

        let modoHistoricoActivo = false;
        let historicoSeleccionadoData = null;
        let historicoSeleccionadasList = [];
        let lastDataHistoricoResponse = null;

        let resultadoHistoricoAnoActual = null;
        let resultadoHistoricoIdActual = null;

        const mesesNombres = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ];

        function openHistoricoModal() {
            if (inputModalAno) {
                inputModalAno.value = '';
            }
            if (historicoModalOverlay) {
                historicoModalOverlay.classList.add('active');
                setTimeout(() => {
                    if (inputModalAno) inputModalAno.focus();
                }, 100);
            }
        }

        function closeHistoricoModal() {
            if (historicoModalOverlay) {
                historicoModalOverlay.classList.remove('active');
            }
        }

        function closeResultadoHistoricoModal() {
            if (resultadoHistoricoModalOverlay) {
                resultadoHistoricoModalOverlay.classList.remove('active');
            }
        }

        if (btnHistorial) {
            btnHistorial.addEventListener('click', openHistoricoModal);
        }
        if (btnHistoricoModalClose) btnHistoricoModalClose.addEventListener('click', closeHistoricoModal);
        if (btnHistoricoModalCancel) btnHistoricoModalCancel.addEventListener('click', closeHistoricoModal);
        if (historicoModalOverlay) {
            historicoModalOverlay.addEventListener('click', (e) => {
                if (e.target === historicoModalOverlay) closeHistoricoModal();
            });
        }

        if (btnResultadoHistoricoModalClose) btnResultadoHistoricoModalClose.addEventListener('click', closeResultadoHistoricoModal);
        if (btnResultadoHistoricoModalCerrar) btnResultadoHistoricoModalCerrar.addEventListener('click', closeResultadoHistoricoModal);
        if (resultadoHistoricoModalOverlay) {
            resultadoHistoricoModalOverlay.addEventListener('click', (e) => {
                if (e.target === resultadoHistoricoModalOverlay) closeResultadoHistoricoModal();
            });
        }

        async function cargarHistoricoPorAno() {
            const val = inputModalAno ? inputModalAno.value.trim() : '';
            if (!val || isNaN(val) || parseInt(val, 10) < 2000 || parseInt(val, 10) > 2100) {
                showToast('Por favor ingrese un año válido (ejemplo: 2026).', 'warning');
                if (inputModalAno) inputModalAno.focus();
                return;
            }

            const anoIngresado = parseInt(val, 10);
            if (btnHistoricoModalCargar) {
                btnHistoricoModalCargar.disabled = true;
                btnHistoricoModalCargar.style.opacity = '0.7';
            }

            try {
                showToast(`Consultando registro histórico del Año ${anoIngresado}...`, 'info');
                const url = "{% url 'tarifa_inflacion_historico' %}?anio=" + anoIngresado;
                const resp = await fetch(url);
                const data = await resp.json();

                if (!data.success) {
                    showToast(data.error || `No se encontraron registros históricos para el año ${anoIngresado}.`, 'error');
                    return;
                }

                // Cerrar modal 1 (ingreso)
                closeHistoricoModal();

                const meta = data.metadata || {};
                const anioActual = meta.ano || anoIngresado;
                const anioAnterior = meta.ano_anterior || (anioActual - 1);

                resultadoHistoricoAnoActual = anioActual;
                resultadoHistoricoIdActual = data.id_cabotaje || meta.id_tarifaCab;

                if (lblHistoricoModalAno) lblHistoricoModalAno.textContent = `Año ${anioActual}`;
                if (headerModalTarifaAnioAnterior) headerModalTarifaAnioAnterior.textContent = `TARIFA ${anioAnterior}`;
                if (headerModalTarifaAnioActual) headerModalTarifaAnioActual.textContent = `TARIFA ${anioActual}`;

                // Guardar la respuesta recibida
                lastDataHistoricoResponse = data;

                // Resetear selector y estado del encabezado
                if (chkModalSelectAllHeader) {
                    chkModalSelectAllHeader.checked = false;
                    chkModalSelectAllHeader.indeterminate = false;
                }
                if (btnResultadoHistoricoSelectAll) {
                    btnResultadoHistoricoSelectAll.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg> Seleccionar Todo`;
                }

                // Poblar la tabla de tarifas dentro del Modal 2
                if (tablaResultadoHistoricoBody && data.tarifas) {
                    tablaResultadoHistoricoBody.innerHTML = '';
                    data.tarifas.forEach(t => {
                        const tr = document.createElement('tr');
                        tr.className = 'fila-historico-interactiva';
                        tr.style.borderBottom = '1px solid #f1f5f9';
                        tr.style.cursor = 'pointer';
                        tr.title = 'Haga clic para seleccionar o deseleccionar esta tarifa';

                        const usuarioFila = t.nombre || t.usuario_nombre || (t.id_usuario !== undefined && t.id_usuario !== null && String(t.id_usuario).trim() !== '' ? t.id_usuario : (meta.id_usuario || '-'));
                        const fechaRegFila = t.fecha_registro || meta.fecha_registro || '-';

                        const valAnteriorNum = parseFloat(t.valor_anterior || t.valor || 0);
                        const valInflacionNum = parseFloat(t.tarifa_inflacion || 0);
                        const valFinalNum = parseFloat(t.valor_final || 0);

                        const txtInflacion = t.aplica_inflacion == 1
                            ? `$ ${valInflacionNum.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 4})}`
                            : '-';

                        tr.innerHTML = `
                            <td style="padding: 10px 10px; text-align: center; font-weight: 600; color: #475569;">${t.nro || ''}</td>
                            <td style="padding: 10px 10px; text-align: center; font-weight: 700; color: var(--navy);" title="ID Usuario: ${t.id_usuario || ''}">${usuarioFila}</td>
                            <td style="padding: 10px 10px; text-align: center; color: #0284c7; font-size: 12px; font-weight: 500;">${fechaRegFila}</td>
                            <td style="padding: 10px 10px; text-align: center; font-weight: 700; color: #1e293b;">${t.codigo || ''}</td>
                            <td style="padding: 10px 10px; font-weight: 500; color: #1e293b;">${t.tarifa || ''}</td>
                            <td style="padding: 10px 10px; text-align: right; color: #475569;">$ ${valAnteriorNum.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 4})}</td>
                            <td style="padding: 10px 10px; text-align: right; color: #64748b; font-weight: 500;">${txtInflacion}</td>
                            <td style="padding: 10px 10px; text-align: right; font-weight: 700; color: var(--navy-deep);">$ ${valFinalNum.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 4})}</td>
                            <td style="padding: 8px 10px; text-align: center;">
                                <input type="checkbox" class="chk-tarifa-historica" style="width: 17px; height: 17px; cursor: pointer; accent-color: var(--navy); vertical-align: middle;">
                            </td>
                        `;

                        const chk = tr.querySelector('.chk-tarifa-historica');
                        chk._tarifaData = t;

                        chk.addEventListener('change', () => {
                            actualizarEstadoBotonesSeleccion();
                        });

                        tr.addEventListener('click', (e) => {
                            if (e.target !== chk) {
                                chk.checked = !chk.checked;
                                actualizarEstadoBotonesSeleccion();
                            }
                        });

                        tablaResultadoHistoricoBody.appendChild(tr);
                    });
                }

                // Abrir Modal 2
                if (resultadoHistoricoModalOverlay) {
                    resultadoHistoricoModalOverlay.classList.add('active');
                }

                showToast(`Histórico del Año ${anioActual} cargado en ventana modal.`, 'success');

            } catch (err) {
                console.error(err);
                showToast('Error al comunicar con el servidor para consultar el histórico.', 'error');
            } finally {
                if (btnHistoricoModalCargar) {
                    btnHistoricoModalCargar.disabled = false;
                    btnHistoricoModalCargar.style.opacity = '1';
                }
            }
        }

        function actualizarEstadoBotonesSeleccion() {
            const allCheckboxes = tablaResultadoHistoricoBody ? tablaResultadoHistoricoBody.querySelectorAll('.chk-tarifa-historica') : [];
            if (!allCheckboxes.length) return;
            const total = allCheckboxes.length;
            const checkedCount = Array.from(allCheckboxes).filter(c => c.checked).length;
            if (chkModalSelectAllHeader) {
                chkModalSelectAllHeader.checked = (checkedCount === total);
                chkModalSelectAllHeader.indeterminate = (checkedCount > 0 && checkedCount < total);
            }
            if (btnResultadoHistoricoSelectAll) {
                if (checkedCount === total) {
                    btnResultadoHistoricoSelectAll.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M19 5v14H5V5h14m0-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/></svg> Deseleccionar Todo`;
                } else {
                    btnResultadoHistoricoSelectAll.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg> Seleccionar Todo`;
                }
            }
        }

        if (btnResultadoHistoricoSelectAll) {
            btnResultadoHistoricoSelectAll.addEventListener('click', () => {
                const allCheckboxes = tablaResultadoHistoricoBody ? tablaResultadoHistoricoBody.querySelectorAll('.chk-tarifa-historica') : [];
                if (!allCheckboxes.length) return;
                const allChecked = Array.from(allCheckboxes).every(c => c.checked);
                const nuevoEstado = !allChecked;
                allCheckboxes.forEach(c => c.checked = nuevoEstado);
                actualizarEstadoBotonesSeleccion();
            });
        }

        if (chkModalSelectAllHeader) {
            chkModalSelectAllHeader.addEventListener('change', () => {
                const allCheckboxes = tablaResultadoHistoricoBody ? tablaResultadoHistoricoBody.querySelectorAll('.chk-tarifa-historica') : [];
                allCheckboxes.forEach(c => c.checked = chkModalSelectAllHeader.checked);
                actualizarEstadoBotonesSeleccion();
            });
        }

        if (btnResultadoHistoricoAceptar) {
            btnResultadoHistoricoAceptar.addEventListener('click', () => {
                const checkedList = tablaResultadoHistoricoBody 
                    ? Array.from(tablaResultadoHistoricoBody.querySelectorAll('.chk-tarifa-historica:checked')).map(c => c._tarifaData).filter(Boolean)
                    : [];
                
                if (checkedList.length === 0) {
                    showToast('Por favor seleccione al menos una tarifa con la casilla de verificación.', 'warning');
                    return;
                }

                aplicarTarifasHistoricasSeleccionadas(checkedList, lastDataHistoricoResponse);
            });
        }

        if (btnHistoricoModalCargar) {
            btnHistoricoModalCargar.addEventListener('click', cargarHistoricoPorAno);
        }

        if (inputModalAno) {
            inputModalAno.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    cargarHistoricoPorAno();
                }
            });
        }

        // ======================================================================
        // Lógica de Selección de Histórico hacia Pantalla Principal
        // ======================================================================
        function aplicarTarifasHistoricasSeleccionadas(tarifasAjuste, dataResponse) {
            if (!tarifasAjuste || !tarifasAjuste.length) return;
            const meta = (dataResponse && dataResponse.metadata) ? dataResponse.metadata : {};
            const firstItem = tarifasAjuste[0];

            // 1. Llenar inputs de cabecera en la pantalla principal
            let fVal = firstItem.fecha_inflacion || firstItem.fecha_registro || meta.fecha_inflacion || meta.fecha_registro || '';
            if (fVal.includes(' ')) {
                fVal = fVal.split(' ')[0]; // Convertir formato fecha para input date (YYYY-MM-DD)
            }
            if (inputFechaInflacion) {
                inputFechaInflacion.value = fVal;
                inputFechaInflacion.disabled = true;
            }

            const anioVal = String(firstItem.ano || meta.ano || resultadoHistoricoAnoActual || '');
            if (selectAnio && anioVal) {
                let hasOption = false;
                for (let i = 0; i < selectAnio.options.length; i++) {
                    if (selectAnio.options[i].value === anioVal) {
                        hasOption = true;
                        break;
                    }
                }
                if (!hasOption) {
                    const opt = document.createElement('option');
                    opt.value = anioVal;
                    opt.textContent = anioVal;
                    selectAnio.appendChild(opt);
                }
                selectAnio.value = anioVal;
                selectAnio.disabled = true;
            }

            const inflacionVal = parseFloat(firstItem.porcentaje_actual !== undefined && firstItem.porcentaje_actual !== null ? firstItem.porcentaje_actual : (firstItem.porcentaje_inflacion || meta.porcentaje_inflacion || 0));
            if (inputInflacion) {
                inputInflacion.value = inflacionVal.toFixed(2);
                inputInflacion.disabled = true;
            }

            if (inputDetalle) {
                inputDetalle.value = firstItem.detalle || meta.detalle || '';
                inputDetalle.disabled = true;
            }

            // 2. Encabezados de año de la tabla
            const numAnio = parseInt(anioVal, 10) || currentYear;
            const numAnioAnt = firstItem.ano_anterior || meta.ano_anterior || (numAnio - 1);
            if (headerTarifaAnioAnterior) headerTarifaAnioAnterior.textContent = `Tarifa ${numAnioAnt}`;
            if (headerValorTarifa) headerValorTarifa.textContent = `Tarifa ${numAnio}`;

            // 3. Poblar la tabla de tarifas de la pantalla principal con los elementos seleccionados
            if (tablaTarifasBody) {
                tablaTarifasBody.innerHTML = '';
                tarifasAjuste.forEach((item, idx) => {
                    const tr = document.createElement('tr');
                    tr.dataset.baseVal = item.valor_anterior || item.valor || '0';
                    tr.dataset.aplicaInflacion = item.aplica_inflacion == 1 ? '1' : '0';

                    const valAnterior = parseFloat(item.valor_anterior || item.valor || 0);
                    const valInflacion = parseFloat(item.tarifa_inflacion || 0);
                    const valFinal = parseFloat(item.valor_final || 0);

                    const txtInflacion = item.aplica_inflacion == 1
                        ? `$ ${valInflacion.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 4})}`
                        : '-';
                    const txtTotal = `$ ${valFinal.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 4})}`;

                    tr.innerHTML = `
                        <td class="text-center">${idx + 1}</td>
                        <td class="text-center" style="font-weight: 700;">${item.codigo || ''}</td>
                        <td>${item.tarifa || ''}</td>
                        <td class="text-right">$ ${valAnterior.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 4})}</td>
                        <td class="text-right text-calc-inflacion" style="color: var(--muted); font-weight: 500;">${txtInflacion}</td>
                        <td class="text-right text-calc-total" style="font-weight: 600; color: var(--navy-deep);">${txtTotal}</td>
                    `;
                    tablaTarifasBody.appendChild(tr);
                });
            }

            if (placeholderMessage) placeholderMessage.style.display = 'none';
            if (tablaTarifasWrapper) tablaTarifasWrapper.style.display = 'block';

            // 4. Activar Modo Histórico y Bloquear botones Guardar y Aplicar
            activarModoHistorico(tarifasAjuste, numAnio, tarifasAjuste.length);

            // 5. Cerrar modal de histórico
            closeResultadoHistoricoModal();

            showToast(`Se cargaron ${tarifasAjuste.length} tarifa(s) histórica(s) del Año ${numAnio}. Botones de edición protegidos.`, 'success');
        }

        function activarModoHistorico(tarifasSeleccionadas, anio, totalTarifas) {
            modoHistoricoActivo = true;
            historicoSeleccionadasList = Array.isArray(tarifasSeleccionadas) ? tarifasSeleccionadas : [tarifasSeleccionadas];
            historicoSeleccionadoData = historicoSeleccionadasList[0] || null;

            // Bloquear botón Guardar
            if (btnGuardar) {
                btnGuardar.disabled = true;
                btnGuardar.style.opacity = '0.45';
                btnGuardar.style.cursor = 'not-allowed';
                btnGuardar.setAttribute('title', 'El botón Guardar está bloqueado: está visualizando un registro histórico.');
            }

            // Bloquear botón APLICAR
            if (btnAplicar) {
                btnAplicar.disabled = true;
                btnAplicar.style.opacity = '0.45';
                btnAplicar.style.cursor = 'not-allowed';
                btnAplicar.setAttribute('title', 'El botón Aplicar está bloqueado en modo histórico.');
            }

            // Mostrar botón "Volver a Registro Inflacion" al lado del botón de Historial
            if (btnVolverRegistro) {
                btnVolverRegistro.style.display = 'inline-flex';
            }

            // Mostrar botón "Exportar PDF" únicamente en modo histórico
            if (btnExportar) {
                btnExportar.style.display = 'inline-flex';
            }
        }

        function restaurarModoNormal() {
            modoHistoricoActivo = false;
            historicoSeleccionadasList = [];
            historicoSeleccionadoData = null;

            // Reactivar inputs superiores
            if (inputFechaInflacion) {
                inputFechaInflacion.disabled = false;
                inputFechaInflacion.value = '';
            }
            if (selectAnio) {
                selectAnio.disabled = false;
                selectAnio.value = currentYear;
            }
            if (inputInflacion) {
                inputInflacion.disabled = false;
                inputInflacion.value = '';
            }
            if (inputDetalle) {
                inputDetalle.disabled = false;
                inputDetalle.value = '';
            }

            // Restaurar encabezados de año
            if (headerTarifaAnioAnterior) headerTarifaAnioAnterior.textContent = `Tarifa ${prevYear}`;
            if (headerValorTarifa) headerValorTarifa.textContent = `Tarifa ${currentYear}`;

            // Restaurar tabla original con tarifas activas
            if (tablaTarifasBody && originalTablaTarifasHTML) {
                tablaTarifasBody.innerHTML = originalTablaTarifasHTML;
            }

            // Limpiar columnas calculadas de la tabla
            document.querySelectorAll('#tablaTarifasBody .text-calc-inflacion').forEach(el => el.textContent = '');
            document.querySelectorAll('#tablaTarifasBody .text-calc-total').forEach(el => el.textContent = '');

            // Reactivar botones
            if (btnGuardar) {
                btnGuardar.disabled = false;
                btnGuardar.style.opacity = '1';
                btnGuardar.style.cursor = 'pointer';
                btnGuardar.setAttribute('title', 'Guardar ajuste por inflación');
            }
            if (btnAplicar) {
                btnAplicar.disabled = false;
                btnAplicar.style.opacity = '1';
                btnAplicar.style.cursor = 'pointer';
                btnAplicar.removeAttribute('title');
            }

            // Ocultar botón "Volver a Registro Inflacion"
            if (btnVolverRegistro) {
                btnVolverRegistro.style.display = 'none';
            }

            // Ocultar botón "Exportar PDF"
            if (btnExportar) {
                btnExportar.style.display = 'none';
            }

            showToast('Vista restaurada al registro y simulación de tarifas.', 'info');
        }

        if (btnVolverRegistro) {
            btnVolverRegistro.addEventListener('click', restaurarModoNormal);
        }

        function openDateAlertModal(val) {
            const parts = val.split('-');
            if (parts.length === 3) {
                const mesIdx = parseInt(parts[1], 10) - 1;
                const nombreMes = mesesNombres[mesIdx] || '';
                const anio = parts[0];
                const dia = parts[2];
                dateAlertMessageText.innerHTML = `Ha seleccionado la fecha <strong>${dia}/${parts[1]}/${anio}</strong> (${nombreMes}), la cual no pertenece al mes de <strong>Enero</strong>.`;
            }
            dateAlertModalOverlay.classList.add('active');
        }

        function closeDateAlertModal() {
            dateAlertModalOverlay.classList.remove('active');
        }

        btnDateAlertClose.addEventListener('click', closeDateAlertModal);
        btnDateAlertCorrect.addEventListener('click', () => {
            closeDateAlertModal();
            inputFechaInflacion.value = '';
            inputFechaInflacion.focus();
        });
        btnDateAlertContinue.addEventListener('click', closeDateAlertModal);
        dateAlertModalOverlay.addEventListener('click', (e) => {
            if (e.target === dateAlertModalOverlay) {
                closeDateAlertModal();
            }
        });

        // Verificación al cambiar la fecha en el input
        inputFechaInflacion.addEventListener('change', () => {
            const val = inputFechaInflacion.value;
            if (!val) return;
            const parts = val.split('-');
            if (parts.length === 3 && parts[1] !== '01') {
                openDateAlertModal(val);
            }
        });

        let pendingFormData = null;
        let pendingInflacion = 0;

        function openConfirmModal(porcentaje, formData) {
            pendingFormData = formData;
            pendingInflacion = porcentaje;

            let avisoFecha = '';
            const fecha = inputFechaInflacion ? inputFechaInflacion.value : '';
            if (fecha) {
                const parts = fecha.split('-');
                if (parts.length === 3 && parts[1] !== '01') {
                    const mesIdx = parseInt(parts[1], 10) - 1;
                    const nombreMes = mesesNombres[mesIdx] || '';
                    avisoFecha = `<div style="margin-top: 12px; font-size: 12px; color: #92400e; background: #fffbeb; padding: 8px 12px; border-radius: 6px; border: 1px solid #fde68a; display: flex; align-items: center; gap: 8px;">
                        <span>⚠️ <strong>Aviso:</strong> La fecha (${parts[2]}/${parts[1]}/${parts[0]} - ${nombreMes}) no corresponde al mes de enero.</span>
                    </div>`;
                }
            }

            if (porcentaje > 0) {
                modalMessageText.innerHTML = `¿Está seguro de que desea guardar el ajuste? Esta acción incrementará en un <strong>${porcentaje.toFixed(2)}%</strong> el valor de las tarifas activas con inflación habilitada.${avisoFecha}`;
            } else {
                modalMessageText.innerHTML = `¿Está seguro de que desea guardar el ajuste? Se registrará una inflación del <strong>${porcentaje.toFixed(2)}%</strong> en la cabecera auditora. Al ser un valor menor o igual a 0%, <strong>el valor de las tarifas se mantendrá sin cambios</strong>.${avisoFecha}`;
            }
            confirmModalOverlay.classList.add('active');
        }

        function closeConfirmModal() {
            confirmModalOverlay.classList.remove('active');
            pendingFormData = null;
            pendingInflacion = 0;
        }

        btnModalClose.addEventListener('click', closeConfirmModal);
        btnModalCancel.addEventListener('click', closeConfirmModal);
        
        confirmModalOverlay.addEventListener('click', (e) => {
            if (e.target === confirmModalOverlay) {
                closeConfirmModal();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (historicoModalOverlay && historicoModalOverlay.classList.contains('active')) {
                    closeHistoricoModal();
                } else if (dateAlertModalOverlay && dateAlertModalOverlay.classList.contains('active')) {
                    closeDateAlertModal();
                } else if (confirmModalOverlay && confirmModalOverlay.classList.contains('active')) {
                    closeConfirmModal();
                }
            }
        });

        // 1. Establecer el encabezado de año al año actual y anterior
        const currentYear = new Date().getFullYear();
        const prevYear = currentYear - 1;
        const headerTarifaAnioAnterior = document.getElementById('headerTarifaAnioAnterior');
        if (headerTarifaAnioAnterior) headerTarifaAnioAnterior.textContent = `Tarifa ${prevYear}`;
        if (headerValorTarifa) headerValorTarifa.textContent = `Tarifa ${currentYear}`;

        // 2. Función para aplicar el cálculo de inflación en el frontend
        function calcularInflacion(showToastAlert = false) {
            const inflacion = parseFloat(inputInflacion.value);
            if (isNaN(inflacion) || inflacion < -100 || inflacion > 100) {
                if (showToastAlert) showToast('Por favor ingrese un porcentaje de inflación válido (entre -100.00% y 100.00%).', 'error');
                return;
            }

            const rows = document.querySelectorAll('#tablaTarifasBody tr[data-base-val]');
            rows.forEach(row => {
                const baseVal = parseFloat(row.dataset.baseVal);
                const aplicaInflacion = row.dataset.aplicaInflacion === '1' || row.dataset.aplicaInflacion === 'true';
                if (!isNaN(baseVal)) {
                    let inflacionVal = 0.0;
                    let totalVal = baseVal;
                    if (aplicaInflacion && inflacion > 0) {
                        inflacionVal = baseVal * (inflacion / 100);
                        totalVal = baseVal + inflacionVal;
                    }

                    // Formatear con separadores y decimales
                    row.querySelector('.text-calc-inflacion').textContent = `$ ${inflacionVal.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 4})}`;
                    row.querySelector('.text-calc-total').textContent = `$ ${totalVal.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 4})}`;
                }
            });

            // Mostrar tabla, ocultar mensaje placeholder
            placeholderMessage.style.display = 'none';
            tablaTarifasWrapper.style.display = 'block';

            if (showToastAlert) {
                showToast(`Se aplicó simulación de inflación del ${inflacion.toFixed(2)}% correctamente.`, 'success');
            }
        }

        // Evento del botón APLICAR
        btnAplicar.addEventListener('click', () => {
            if (modoHistoricoActivo) {
                showToast('No se puede aplicar simulación mientras visualiza un registro histórico.', 'warning');
                return;
            }
            calcularInflacion(true);
        });

        // Evento del botón Exportar PDF (Únicamente en modo histórico)
        if (btnExportar) {
            btnExportar.addEventListener('click', () => {
                if (modoHistoricoActivo && historicoSeleccionadasList && historicoSeleccionadasList.length > 0) {
                    showToast(`Generando y descargando PDF con ${historicoSeleccionadasList.length} tarifa(s) histórica(s)...`, 'info');
                    const params = new URLSearchParams();
                    params.append('es_historico', '1');
                    const anio = selectAnio ? selectAnio.value : (resultadoHistoricoAnoActual || currentYear);
                    if (anio) params.append('anio', anio);
                    const cabId = (historicoSeleccionadoData && historicoSeleccionadoData.id_tarifaCab) || resultadoHistoricoIdActual;
                    if (cabId) params.append('id_cabotaje', cabId);
                    
                    const codigos = historicoSeleccionadasList.map(t => String(t.codigo || '').trim()).filter(Boolean).join(',');
                    if (codigos) {
                        params.append('codigos', codigos);
                    }

                    const exportUrl = "{% url 'tarifa_inflacion_exportar_pdf' %}?" + params.toString();
                    window.location.href = exportUrl;
                } else {
                    showToast('La función de exportación directa solo está disponible al consultar un registro histórico.', 'warning');
                }
            });
        }

        // 3. Botón de Guardar -> Bloqueado en modo histórico o abre modal en simulación
        btnGuardar.addEventListener('click', () => {
            if (modoHistoricoActivo) {
                showToast('El botón Guardar está bloqueado: está visualizando un registro histórico ya guardado.', 'warning');
                return;
            }

            const inflacion = parseFloat(inputInflacion.value);
            if (isNaN(inflacion) || inflacion < -100 || inflacion > 100) {
                showToast('Por favor ingrese un porcentaje de inflación válido (entre -100.00% y 100.00%) y presione APLICAR.', 'error');
                return;
            }

            const detalle = inputDetalle.value.trim();
            const fechaInflacion = inputFechaInflacion.value;

            if (!fechaInflacion) {
                showToast('Debe ingresar la fecha de inflación.', 'error');
                inputFechaInflacion.focus();
                return;
            }

            if (inflacion === 0 && !detalle) {
                showToast('Debe ingresar un detalle o justificación cuando el porcentaje de inflación es 0%.', 'error');
                inputDetalle.focus();
                return;
            }

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const formData = new FormData();
            formData.append('porcentaje', inflacion);
            formData.append('anio', selectAnio.value);
            formData.append('detalle', detalle);
            formData.append('fecha_inflacion', fechaInflacion);
            formData.append('csrfmiddlewaretoken', csrfToken);

            openConfirmModal(inflacion, formData);
        });

        // 4. Botón Aceptar del Modal -> Ejecuta guardado en servidor y descarga automática de PDF
        btnModalConfirm.addEventListener('click', () => {
            if (!pendingFormData) return;

            const formDataToSend = pendingFormData;
            const inflacionVal = pendingInflacion;
            closeConfirmModal();

            btnGuardar.disabled = true;

            fetch("{% url 'tarifa_inflacion_guardar' %}", {
                method: "POST",
                body: formDataToSend
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(`Se guardó el ajuste de inflación de ${inflacionVal.toFixed(2)}% correctamente. Descargando reporte PDF...`, 'success');

                    // Descarga automática del reporte PDF generado
                    const anio = formDataToSend.get('anio') || currentYear;
                    const fechaInflacion = formDataToSend.get('fecha_inflacion') || '';
                    const detalle = formDataToSend.get('detalle') || '';

                    const params = new URLSearchParams();
                    params.append('porcentaje', inflacionVal);
                    if (anio) params.append('anio', anio);
                    if (fechaInflacion) params.append('fecha_inflacion', fechaInflacion);
                    if (detalle) params.append('detalle', detalle);

                    const exportUrl = "{% url 'tarifa_inflacion_exportar_pdf' %}?" + params.toString();

                    const link = document.createElement('a');
                    link.href = exportUrl;
                    link.setAttribute('download', `Tarifario_Inflacion_${anio}.pdf`);
                    document.body.appendChild(link);
                    link.click();
                    setTimeout(() => {
                        link.remove();
                    }, 200);

                    setTimeout(() => {
                        window.location.reload();
                    }, 2200);
                } else {
                    showToast(data.error || 'Ocurrió un error al guardar.', 'error');
                    btnGuardar.disabled = false;
                }
            })
            .catch(error => {
                showToast('Error de comunicación con el servidor.', 'error');
                btnGuardar.disabled = false;
            });
        });

        // Función auxiliar para notificaciones Toast
        function showToast(message, type = 'success') {
            const container = document.getElementById('toastContainer');
            if (!container) return;
            
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            let iconSvg = '';
            if (type === 'success') {
                iconSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>';
            } else if (type === 'warning') {
                iconSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>';
            } else if (type === 'info') {
                iconSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-4h-2V7h2v6z"/></svg>';
            } else {
                iconSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4H11V7h2v6z"/></svg>';
            }

            toast.innerHTML = `${iconSvg} <span>${message}</span>`;
            container.appendChild(toast);
            
            setTimeout(() => toast.classList.add('show'), 50);
            
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
});

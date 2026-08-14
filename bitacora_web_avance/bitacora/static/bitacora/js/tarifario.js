  function showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        // Icon matching toast type
        let iconSvg = '';
        if (type === 'success') {
            iconSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>';
        } else if (type === 'warning') {
            iconSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>';
        } else {
            iconSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-4h-2V7h2v6z"/></svg>';
        }

        toast.innerHTML = `${iconSvg} <span>${message}</span>`;
        container.appendChild(toast);
        
        // Trigger reflow for slide in transition
        setTimeout(() => toast.classList.add('show'), 50);
        
        // Remove after 3.5s
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // Format Valor field to 4 decimal places obligatorily
    function formatDecimal(input) {
        const val = parseFloat(input.value);
        if (isNaN(val)) {
            input.value = "0.0000";
        } else {
            input.value = val.toFixed(4);
        }
    }

    // Update styling when a radio button is selected
    function updateRadioSelection(radioEl) {
        const name = radioEl.name;
        // Remove 'selected' class from all options in the same group
        document.querySelectorAll(`input[name="${name}"]`).forEach(input => {
            input.closest('.radio-option').classList.remove('selected');
        });
        // Add to selected
        if (radioEl.checked) {
            radioEl.closest('.radio-option').classList.add('selected');
        }
    }

    // Clear form to initial empty state
    function clearForm() {
        document.getElementById('tarifaId').value = "0";
        document.getElementById('tarifaCodigo').value = "";
        document.getElementById('tarifaCodigo').disabled = false;
        document.getElementById('tarifaCodigo').readOnly = false;
        document.getElementById('tarifaActiva').checked = true;
        document.getElementById('tarifaTasaId').value = "";
        document.getElementById('tarifaTasaDesc').value = "";
        document.getElementById('tarifaName').value = "";
        document.getElementById('tarifaPartidaCod').value = "";
        document.getElementById('tarifaPartidaDesc').value = "";
        document.getElementById('tarifaPartidaCedula').value = "";
        document.getElementById('tarifaPartidaId').value = "";
        document.getElementById('tarifaFormula').value = "";
        document.getElementById('tarifaDetalle').value = "";
        document.getElementById('tarifaValor').value = "0.0000";
        document.getElementById('tarifaIva').checked = false;
        document.getElementById('tarifaPermitirCambio').checked = false;

        // Reset radio choices
        document.querySelector('input[name="calc_param"][value="eslora"]').checked = true;
        document.querySelector('input[name="calc_unidad"][value="dia"]').checked = true;
        document.querySelector('input[name="ticket_srv"][value="ninguno"]').checked = true;

        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            updateRadioSelection(radio);
        });


    }

    async function fetchTasaDescription(idtasa) {
        if (!idtasa) return;
        try {
            const response = await fetch(`/api/buscar-tasa/?idtasa=${encodeURIComponent(idtasa)}`);
            const data = await response.json();
            if (data.success && data.data && data.data.length > 0) {
                const match = data.data.find(t => String(t.idtasa) === String(idtasa)) || data.data[0];
                document.getElementById('tarifaTasaDesc').value = match.tasa || '';
            } else {
                document.getElementById('tarifaTasaDesc').value = '';
            }
        } catch (e) {
            console.error("Error fetching Tasa description:", e);
            document.getElementById('tarifaTasaDesc').value = '';
        }
    }

    async function fetchPartidaDetails(codigo) {
        if (!codigo) return;
        try {
            const response = await fetch(`/api/buscar-partida/?codigo=${encodeURIComponent(codigo)}`);
            const data = await response.json();
            if (data.success && data.data && data.data.length > 0) {
                const match = data.data.find(p => (p.scpartida || p.codigo) === codigo) || data.data[0];
                const desc = match.partidafinanzas || match.descripcion || match.nombre || '';
                const cedula = match.scpartida ? (match.codigo || '') : (match.cedulafinanza || match.cedulaFinanza || '');
                document.getElementById('tarifaPartidaDesc').value = desc;
                document.getElementById('tarifaPartidaCedula').value = cedula;
                document.getElementById('tarifaPartidaId').value = match.idpartida || '';
            } else {
                document.getElementById('tarifaPartidaDesc').value = '';
                document.getElementById('tarifaPartidaCedula').value = '';
                document.getElementById('tarifaPartidaId').value = '';
            }
        } catch (e) {
            console.error("Error fetching Partida details:", e);
            document.getElementById('tarifaPartidaDesc').value = '';
            document.getElementById('tarifaPartidaCedula').value = '';
            document.getElementById('tarifaPartidaId').value = '';
        }
    }

    // Populate form with row data
    function loadTarifaData(data) {
        document.getElementById('tarifaId').value = data.id || "0";
        document.getElementById('tarifaCodigo').value = data.codigo || "";
        document.getElementById('tarifaCodigo').disabled = true;
        document.getElementById('tarifaCodigo').readOnly = true;
        document.getElementById('tarifaActiva').checked = !!data.activa;
        
        document.getElementById('tarifaTasaId').value = data.tasa_id || "";
        if (data.tasa) {
            document.getElementById('tarifaTasaDesc').value = data.tasa;
        } else if (data.tasa_id) {
            document.getElementById('tarifaTasaDesc').value = "Cargando...";
            fetchTasaDescription(data.tasa_id);
        } else {
            document.getElementById('tarifaTasaDesc').value = "";
        }

        document.getElementById('tarifaName').value = data.tarifa || "";
        
        document.getElementById('tarifaPartidaCod').value = data.partida_cod || "";
        document.getElementById('tarifaPartidaId').value = data.partida_id || "";
        if (data.partida_desc && data.partida_cedula) {
            document.getElementById('tarifaPartidaDesc').value = data.partida_desc;
            document.getElementById('tarifaPartidaCedula').value = data.partida_cedula;
        } else if (data.partida_cod) {
            document.getElementById('tarifaPartidaDesc').value = "Cargando...";
            document.getElementById('tarifaPartidaCedula').value = "Cargando...";
            fetchPartidaDetails(data.partida_cod);
        } else {
            document.getElementById('tarifaPartidaDesc').value = "";
            document.getElementById('tarifaPartidaCedula').value = "";
        }
        document.getElementById('tarifaFormula').value = data.formula || "";
        document.getElementById('tarifaDetalle').value = data.detalle || "";
        const valNum = parseFloat(data.valor);
        document.getElementById('tarifaValor').value = isNaN(valNum) ? "0.0000" : valNum.toFixed(4);
        document.getElementById('tarifaIva').checked = !!data.se_cobra_iva;
        document.getElementById('tarifaPermitirCambio').checked = !!data.permitir_cambio_valor;

        // Check correct radio buttons
        const paramRadio = document.querySelector(`input[name="calc_param"][value="${data.calc_param}"]`);
        if (paramRadio) {
            paramRadio.checked = true;
            updateRadioSelection(paramRadio);
        }
        
        const unitRadio = document.querySelector(`input[name="calc_unidad"][value="${data.calc_unidad}"]`);
        if (unitRadio) {
            unitRadio.checked = true;
            updateRadioSelection(unitRadio);
        }

        const ticketRadio = document.querySelector(`input[name="ticket_srv"][value="${data.ticket_srv}"]`);
        if (ticketRadio) {
            ticketRadio.checked = true;
            updateRadioSelection(ticketRadio);
        }
    }

    // Trigger action bar buttons
    function triggerAction(action) {
        if (action === 'save' || action === 'saveNew') {
            const codigo = document.getElementById('tarifaCodigo').value.trim();
            const tarifa = document.getElementById('tarifaName').value.trim();
            const tasa_id = document.getElementById('tarifaTasaId').value.trim();

            if (!codigo || !tarifa || !tasa_id) {
                showToast("Por favor complete los campos obligatorios (Código, Tarifa y Tasa).", "warning");
                return;
            }

            const id = document.getElementById('tarifaId').value;
            const valor = document.getElementById('tarifaValor').value.trim();
            const partida_cod = document.getElementById('tarifaPartidaCod').value.trim();
            const partida_id = document.getElementById('tarifaPartidaId').value.trim();
            const formula = document.getElementById('tarifaFormula').value.trim();
            const detalle = document.getElementById('tarifaDetalle').value.trim();
            
            const calc_unidad = document.querySelector('input[name="calc_unidad"]:checked')?.value || 'cantidad';
            const calc_param = document.querySelector('input[name="calc_param"]:checked')?.value || 'otros';
            const ticket_srv = document.querySelector('input[name="ticket_srv"]:checked')?.value || 'ninguno';
            
            const iva = document.getElementById('tarifaIva').checked ? '1' : '0';
            const activa = document.getElementById('tarifaActiva').checked ? '1' : '0';
            const permitir_cambio_valor = document.getElementById('tarifaPermitirCambio').checked ? '1' : '0';

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrfToken);
            formData.append('id', id);
            formData.append('codigo', codigo);
            formData.append('tarifa', tarifa);
            formData.append('valor', valor);
            formData.append('partida_cod', partida_cod);
            formData.append('partida_id', partida_id);
            formData.append('tasa_id', tasa_id);
            formData.append('formula', formula);
            formData.append('detalle', detalle);
            formData.append('calc_unidad', calc_unidad);
            formData.append('calc_param', calc_param);
            formData.append('iva', iva);
            formData.append('ticket_srv', ticket_srv);
            formData.append('activa', activa);
            formData.append('permitir_cambio_valor', permitir_cambio_valor);

            fetch('/tarifa/guardar/', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(`¡Tarifa [${codigo}] guardada correctamente en el sistema!`);
                    if (action === 'saveNew') {
                        clearForm();
                    }
                } else {
                    showToast(`Error al guardar: ${data.error}`, "warning");
                }
            })
            .catch(error => {
                console.error("Error al guardar:", error);
                showToast("Error de conexión al guardar la tarifa.", "warning");
            });
        } else if (action === 'cancel') {
            const id = document.getElementById('tarifaId').value;
            if (id === "0") {
                showToast("No se puede anular un registro nuevo sin guardar.", "warning");
            } else {
                if (!confirm("¿Está seguro que desea anular esta tarifa? El estado cambiará a inactivo (código 7).")) {
                    return;
                }
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                const formData = new FormData();
                formData.append('csrfmiddlewaretoken', csrfToken);
                formData.append('id', id);

                fetch('/tarifa/anular/', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showToast(`¡Registro ID ${id} anulado correctamente en el sistema!`);
                        clearForm();
                    } else {
                        showToast(`Error al anular: ${data.error}`, "warning");
                    }
                })
                .catch(error => {
                    console.error("Error al anular:", error);
                    showToast("Error de conexión al anular la tarifa.", "warning");
                });
            }
        } else if (action === 'list') {
            const popup = window.open('/tarifa/listado/', 'ListadoTarifas', 'width=950,height=650,scrollbars=yes,resizable=yes');
            if (popup) {
                popup.focus();
            }
        } else if (action === 'new') {
            window.open('/tarifa/', '_blank');
        } else if (action === 'refresh') {
            window.location.reload();
        }
    }

    // Setup interactive events
    document.addEventListener('DOMContentLoaded', () => {

        // Initialize radio styles
        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            updateRadioSelection(radio);
        });

        // Keyboard Shortcuts (F4 and F2)
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F4') {
                e.preventDefault();
                triggerAction('save');
            } else if (e.key === 'F2') {
                e.preventDefault();
                triggerAction('new');
            }
        });
    });

    document.addEventListener('DOMContentLoaded', function() {
        // --- AUTOCOMPLETADO DE PARTIDA ---
        const inputCod = document.getElementById('tarifaPartidaCod');
        const inputDesc = document.getElementById('tarifaPartidaDesc');
        const inputCedula = document.getElementById('tarifaPartidaCedula');
        const autocompleteList = document.getElementById('partidaAutocompleteList');

        if (inputCod && inputDesc && autocompleteList) {
            let debounceTimer;
            let currentFocus = -1;

            // Hide list when clicking outside
            document.addEventListener('click', function(e) {
                if (e.target !== inputCod && e.target !== autocompleteList && !autocompleteList.contains(e.target)) {
                    hideList();
                }
            });

            function showList() {
                autocompleteList.style.display = 'block';
            }

            function hideList() {
                autocompleteList.style.display = 'none';
                currentFocus = -1;
            }

            function addActive(x) {
                if (!x) return false;
                removeActive(x);
                if (currentFocus >= x.length) currentFocus = 0;
                if (currentFocus < 0) currentFocus = (x.length - 1);
                x[currentFocus].classList.add("active");
                x[currentFocus].scrollIntoView({ block: 'nearest' });
            }

            function removeActive(x) {
                for (let i = 0; i < x.length; i++) {
                    x[i].classList.remove("active");
                }
            }

            // Keyboard navigation
            inputCod.addEventListener('keydown', function(e) {
                let x = autocompleteList.getElementsByClassName("autocomplete-item");
                if (e.key === "ArrowDown") {
                    currentFocus++;
                    addActive(x);
                } else if (e.key === "ArrowUp") {
                    currentFocus--;
                    addActive(x);
                } else if (e.key === "Enter") {
                    e.preventDefault();
                    if (currentFocus > -1) {
                        if (x[currentFocus]) x[currentFocus].click();
                    }
                } else if (e.key === "Escape") {
                    hideList();
                }
            });

            async function buscarPartidas(codigo) {
                if (!codigo) {
                    hideList();
                    inputDesc.value = '';
                    inputCedula.value = '';
                    return;
                }

                try {
                    const response = await fetch(`/api/buscar-partida/?codigo=${encodeURIComponent(codigo)}`);
                    const data = await response.json();

                    autocompleteList.innerHTML = '';

                    if (data.success && data.data && data.data.length > 0) {
                        // Buscar coincidencia exacta
                        const exactMatch = data.data.find(p => {
                            const pCod = (p.scpartida || p.codigo || '').trim().toLowerCase();
                            return pCod === codigo.trim().toLowerCase();
                        });

                        if (exactMatch) {
                            const desc = exactMatch.partidafinanzas || exactMatch.descripcion || exactMatch.nombre || exactMatch.detalle || '';
                            const cedula = exactMatch.scpartida ? (exactMatch.codigo || '') : (exactMatch.cedulafinanza || exactMatch.cedulaFinanza || '');
                            inputDesc.value = desc;
                            inputCedula.value = cedula;
                            document.getElementById('tarifaPartidaId').value = exactMatch.idpartida || '';
                            hideList();
                            return; // Coincidencia exacta encontrada, no es necesario listar
                        } else {
                            // Limpiar si se está escribiendo algo no coincidente aún
                            inputDesc.value = '';
                            inputCedula.value = '';
                            document.getElementById('tarifaPartidaId').value = '';
                        }

                        data.data.forEach((partida) => {
                            const item = document.createElement('div');
                            item.className = 'autocomplete-item';
                            
                            const scpartida = partida.scpartida || partida.codigo || '';
                            const desc = partida.partidafinanzas || partida.descripcion || partida.nombre || partida.detalle || '';
                            const cedula = partida.scpartida ? (partida.codigo || '') : (partida.cedulafinanza || partida.cedulaFinanza || '');

                            item.innerHTML = `
                                <div class="item-code">${scpartida}</div>
                                <div class="item-desc">${desc}</div>
                            `;

                            item.addEventListener('click', function() {
                                inputCod.value = scpartida;
                                inputDesc.value = desc;
                                inputCedula.value = cedula;
                                document.getElementById('tarifaPartidaId').value = partida.idpartida || '';
                                hideList();
                            });

                            autocompleteList.appendChild(item);
                        });
                        showList();
                    } else {
                        inputDesc.value = '';
                        inputCedula.value = '';
                        const noResult = document.createElement('div');
                        noResult.className = 'autocomplete-no-results';
                        noResult.textContent = 'No se encontraron partidas';
                        autocompleteList.appendChild(noResult);
                        showList();
                    }
                } catch (error) {
                    console.error('Error al consultar las partidas:', error);
                }
            }

            inputCod.addEventListener('input', function() {
                clearTimeout(debounceTimer);
                const valor = this.value.trim();
                if (!valor) {
                    hideList();
                    inputDesc.value = '';
                    inputCedula.value = '';
                    return;
                }
                debounceTimer = setTimeout(() => {
                    buscarPartidas(valor);
                }, 250);
            });

            // Re-open list on focus/click if it has value
            inputCod.addEventListener('focus', function() {
                const valor = this.value.trim();
                if (valor) {
                    buscarPartidas(valor);
                }
            });
        }

        // --- AUTOCOMPLETADO DE TASA ---
        const inputTasaId = document.getElementById('tarifaTasaId');
        const inputTasaDesc = document.getElementById('tarifaTasaDesc');
        const tasaAutocompleteList = document.getElementById('tasaAutocompleteList');

        if (inputTasaId && inputTasaDesc && tasaAutocompleteList) {
            let debounceTasaTimer;
            let currentTasaFocus = -1;

            async function fetchSiguienteCodigo(idtasa) {
                if (!idtasa) return;
                // Solo cargar si es una nueva tarifa (Id es "0")
                const currentId = document.getElementById('tarifaId').value;
                if (currentId !== "0") return;

                try {
                    const response = await fetch(`/api/siguiente-codigo-tarifa/?idtasa=${encodeURIComponent(idtasa)}`);
                    const data = await response.json();
                    if (data.success && data.siguiente) {
                        document.getElementById('tarifaCodigo').value = data.siguiente;
                    }
                } catch (e) {
                    console.error("Error al obtener el siguiente código:", e);
                }
            }

            // Hide list when clicking outside
            document.addEventListener('click', function(e) {
                if (e.target !== inputTasaId && e.target !== tasaAutocompleteList && !tasaAutocompleteList.contains(e.target)) {
                    hideTasaList();
                }
            });

            function showTasaList() {
                tasaAutocompleteList.style.display = 'block';
            }

            function hideTasaList() {
                tasaAutocompleteList.style.display = 'none';
                currentTasaFocus = -1;
            }

            function addTasaActive(x) {
                if (!x) return false;
                removeTasaActive(x);
                if (currentTasaFocus >= x.length) currentTasaFocus = 0;
                if (currentTasaFocus < 0) currentTasaFocus = (x.length - 1);
                x[currentTasaFocus].classList.add("active");
                x[currentTasaFocus].scrollIntoView({ block: 'nearest' });
            }

            // Keyboard navigation
            inputTasaId.addEventListener('keydown', function(e) {
                let x = tasaAutocompleteList.getElementsByClassName("autocomplete-item");
                if (e.key === "ArrowDown") {
                    currentTasaFocus++;
                    addTasaActive(x);
                } else if (e.key === "ArrowUp") {
                    currentTasaFocus--;
                    addTasaActive(x);
                } else if (e.key === "Enter") {
                    e.preventDefault();
                    if (currentTasaFocus > -1) {
                        if (x[currentTasaFocus]) x[currentTasaFocus].click();
                    }
                } else if (e.key === "Escape") {
                    hideTasaList();
                }
            });

            function removeTasaActive(x) {
                for (let i = 0; i < x.length; i++) {
                    x[i].classList.remove("active");
                }
            }

            async function buscarTasas(idtasa) {
                try {
                    const response = await fetch(`/api/buscar-tasa/?idtasa=${encodeURIComponent(idtasa)}`);
                    const data = await response.json();

                    tasaAutocompleteList.innerHTML = '';

                    if (data.success && data.data && data.data.length > 0) {
                        // Buscar coincidencia exacta por ID de tasa
                        const exactMatch = data.data.find(t => String(t.idtasa).trim() === String(idtasa).trim());
                        if (exactMatch) {
                            inputTasaDesc.value = exactMatch.tasa || '';
                            hideTasaList();
                            fetchSiguienteCodigo(exactMatch.idtasa);
                            return; // Coincidencia exacta encontrada, no es necesario listar
                        } else {
                            // Limpiar si se está escribiendo algo no coincidente aún
                            inputTasaDesc.value = '';
                        }

                        data.data.forEach((tasaObj) => {
                            const item = document.createElement('div');
                            item.className = 'autocomplete-item';

                            const id = tasaObj.idtasa || '';
                            const desc = tasaObj.tasa || '';

                            item.innerHTML = `
                                <div class="item-code">ID: ${id}</div>
                                <div class="item-desc">${desc}</div>
                            `;

                            item.addEventListener('click', function() {
                                inputTasaId.value = id;
                                inputTasaDesc.value = desc;
                                hideTasaList();
                                fetchSiguienteCodigo(id);
                            });

                            tasaAutocompleteList.appendChild(item);
                        });
                        showTasaList();
                    } else {
                        inputTasaDesc.value = '';
                        const noResult = document.createElement('div');
                        noResult.className = 'autocomplete-no-results';
                        noResult.textContent = 'No se encontraron tasas';
                        tasaAutocompleteList.appendChild(noResult);
                        showTasaList();
                    }
                } catch (error) {
                    console.error('Error al consultar las tasas:', error);
                }
            }

            inputTasaId.addEventListener('input', function() {
                clearTimeout(debounceTasaTimer);
                const valor = this.value.trim();
                debounceTasaTimer = setTimeout(() => {
                    buscarTasas(valor);
                }, 250);
            });

            // Focus triggers search with current value (or empty value to list all)
            inputTasaId.addEventListener('focus', function() {
                const valor = this.value.trim();
                buscarTasas(valor);
            });

            // Manual change triggers next sequential code calculation
            inputTasaId.addEventListener('change', function() {
                const valor = this.value.trim();
                if (valor) {
                    fetchSiguienteCodigo(valor);
                }
            });
        }
    });
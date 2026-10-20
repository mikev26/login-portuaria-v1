document.addEventListener("DOMContentLoaded", function() {
    // Referencias a los checkboxes y paneles
    const chkCabotaje = document.getElementById("chkCabotaje");
    const chkEspecificas = document.getElementById("chkEspecificas");
    const chkNaves = document.getElementById("chkNaves");

    const panelCabotaje = document.getElementById("panelCabotaje");
    const panelEspecificas = document.getElementById("panelEspecificas");
    const panelNaves = document.getElementById("panelNaves");

    // Mapeo de idtasa por sección de tarifas
    const TASA_MAP = {
        cabotaje: "5",
        especificas: "7",
        naves: "2"
    };

    function getTarifas() {
        return Array.isArray(window.TARIFAS_DATA) ? window.TARIFAS_DATA : [];
    }

    // Helper para escapar HTML
    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    // Helper global para cerrar todos los desplegables de la pantalla
    function cerrarTodosLosDropdowns() {
        document.querySelectorAll(".tpyc-autocomplete-dropdown").forEach(dd => {
            dd.classList.remove("show");
            dd.innerHTML = "";
        });
        document.querySelectorAll(".tpyc-subpanel").forEach(p => {
            p.classList.remove("is-active-panel");
        });
    }

    // Toggle de visibilidad de paneles según checkbox
    function togglePanels() {
        if (panelCabotaje && chkCabotaje) {
            panelCabotaje.classList.toggle("hidden", !chkCabotaje.checked);
        }
        if (panelEspecificas && chkEspecificas) {
            panelEspecificas.classList.toggle("hidden", !chkEspecificas.checked);
        }
        if (panelNaves && chkNaves) {
            panelNaves.classList.toggle("hidden", !chkNaves.checked);
        }
    }

    if (chkCabotaje) chkCabotaje.addEventListener("change", togglePanels);
    if (chkEspecificas) chkEspecificas.addEventListener("change", togglePanels);
    if (chkNaves) chkNaves.addEventListener("change", togglePanels);

    // =========================================================
    // AUTOCOMPLETADO DE TARIFAS (SPJ_v_tarifas)
    // =========================================================
    function setupTarifaAutocomplete(inputScId, inputNombreId, inputIdTarifaId, dropdownNombreId, idTasa) {
        const inputSc = document.getElementById(inputScId);
        const inputNombre = document.getElementById(inputNombreId);
        const inputIdTarifa = document.getElementById(inputIdTarifaId);
        const dropdownNombre = document.getElementById(dropdownNombreId);

        if (!inputNombre) return;

        function getTarifasPorTasa() {
            const todas = getTarifas();
            return todas.filter(t => {
                const tId = String(t.idtasa !== undefined ? t.idtasa : (t.tasa_id !== undefined ? t.tasa_id : "")).trim();
                const esActiva = t.activa === true || t.activo === 1 || t.activo === "1" || String(t.activa).toLowerCase() === "true";
                return tId === String(idTasa) && esActiva;
            });
        }

        function seleccionarTarifa(item) {
            if (!item) return;
            if (inputSc) inputSc.value = item.sctarifa || item.codigo || "";
            if (inputIdTarifa) inputIdTarifa.value = item.idtarifa || item.id || "";
            inputNombre.value = item.tarifa || "";
            ocultarDropdown();
        }

        function ocultarDropdown() {
            if (dropdownNombre) {
                dropdownNombre.classList.remove("show");
                dropdownNombre.innerHTML = "";
            }
            const parentPanel = inputNombre.closest(".tpyc-subpanel");
            if (parentPanel) {
                parentPanel.classList.remove("is-active-panel");
            }
        }

        // --- Búsqueda / Desplegable por Nombre de Tarifa ---
        function renderDropdownNombre(filterText = "") {
            if (!dropdownNombre) return;
            cerrarTodosLosDropdowns();

            const parentPanel = inputNombre.closest(".tpyc-subpanel");
            if (parentPanel) {
                parentPanel.classList.add("is-active-panel");
            }

            const query = filterText.trim().toLowerCase();
            const lista = getTarifasPorTasa();
            const filtradas = query
                ? lista.filter(t => (t.tarifa || "").toLowerCase().includes(query))
                : lista;

            if (filtradas.length === 0) {
                dropdownNombre.innerHTML = '<div class="tpyc-autocomplete-item" style="color: #94a3b8; cursor: default;">No se encontraron tarifas activas</div>';
                dropdownNombre.classList.add("show");
                return;
            }

            let html = "";
            filtradas.forEach((item, index) => {
                const nombre = escapeHtml(item.tarifa || "");
                html += `<div class="tpyc-autocomplete-item" data-index="${index}">${nombre}</div>`;
            });

            dropdownNombre.innerHTML = html;
            dropdownNombre.classList.add("show");
        }

        inputNombre.addEventListener("focus", function() {
            renderDropdownNombre(this.value);
        });
        inputNombre.addEventListener("click", function() {
            renderDropdownNombre(this.value);
        });
        inputNombre.addEventListener("input", function() {
            renderDropdownNombre(this.value);
            const val = this.value.trim().toLowerCase();
            if (!val) {
                if (inputSc) inputSc.value = "";
                if (inputIdTarifa) inputIdTarifa.value = "";
                return;
            }
            const lista = getTarifasPorTasa();
            const coincidencia = lista.find(t => (t.tarifa || "").trim().toLowerCase() === val);
            if (coincidencia) {
                if (inputSc) inputSc.value = coincidencia.sctarifa || coincidencia.codigo || "";
                if (inputIdTarifa) inputIdTarifa.value = coincidencia.idtarifa || coincidencia.id || "";
            } else {
                if (inputSc) inputSc.value = "";
                if (inputIdTarifa) inputIdTarifa.value = "";
            }
        });

        inputNombre.addEventListener("blur", function() {
            setTimeout(() => {
                const val = inputNombre.value.trim().toLowerCase();
                if (!val) {
                    if (inputSc) inputSc.value = "";
                    if (inputIdTarifa) inputIdTarifa.value = "";
                    return;
                }
                const lista = getTarifasPorTasa();
                const coincidencia = lista.find(t => (t.tarifa || "").trim().toLowerCase() === val);
                if (coincidencia) {
                    inputNombre.value = coincidencia.tarifa || "";
                    if (inputSc) inputSc.value = coincidencia.sctarifa || coincidencia.codigo || "";
                    if (inputIdTarifa) inputIdTarifa.value = coincidencia.idtarifa || coincidencia.id || "";
                } else {
                    inputNombre.value = "";
                    if (inputSc) inputSc.value = "";
                    if (inputIdTarifa) inputIdTarifa.value = "";
                }
            }, 200);
        });

        if (dropdownNombre) {
            dropdownNombre.addEventListener("mousedown", function(e) {
                e.preventDefault();
                const itemElem = e.target.closest(".tpyc-autocomplete-item");
                if (itemElem && !itemElem.hasAttribute("style")) {
                    const idx = parseInt(itemElem.getAttribute("data-index"), 10);
                    const lista = getTarifasPorTasa();
                    const query = inputNombre.value.trim().toLowerCase();
                    const filtradas = query ? lista.filter(t => (t.tarifa || "").toLowerCase().includes(query)) : lista;
                    if (filtradas[idx]) {
                        seleccionarTarifa(filtradas[idx]);
                    }
                }
            });
        }

        if (inputSc) {
            inputSc.addEventListener("input", function() {
                const val = this.value.trim();
                if (!val) {
                    inputNombre.value = "";
                    if (inputIdTarifa) inputIdTarifa.value = "";
                    return;
                }
                const lista = getTarifasPorTasa();
                const coincidencia = lista.find(t => String(t.sctarifa || t.codigo || "").toLowerCase() === val.toLowerCase());
                if (coincidencia) {
                    inputNombre.value = coincidencia.tarifa || "";
                    if (inputIdTarifa) inputIdTarifa.value = coincidencia.idtarifa || coincidencia.id || "";
                } else {
                    if (inputIdTarifa) inputIdTarifa.value = "";
                }
            });
        }

        // Ocultar dropdown si se hace click fuera
        document.addEventListener("click", function(e) {
            if (!inputNombre.contains(e.target) && (!dropdownNombre || !dropdownNombre.contains(e.target))) {
                ocultarDropdown();
            }
        });
    }

    // Inicializar autocompletado para cada categoría (solo abre en Nombre de Tarifa)
    setupTarifaAutocomplete("inputScTarifaCabotaje", "inputNombreTarifaCabotaje", "inputIdTarifaCabotaje", "dropdownNombreTarifaCabotaje", TASA_MAP.cabotaje);
    setupTarifaAutocomplete("inputScTarifaEspecificas", "inputNombreTarifaEspecificas", "inputIdTarifaEspecificas", "dropdownNombreTarifaEspecificas", TASA_MAP.especificas);
    setupTarifaAutocomplete("inputScTarifaNaves", "inputNombreTarifaNaves", "inputIdTarifaNaves", "dropdownNombreTarifaNaves", TASA_MAP.naves);

    // =========================================================
    // AUTOCOMPLETADO DE SERVICIOS (SPJ_v_servicios)
    // =========================================================
    const inputServicio = document.getElementById("inputServicio");
    const inputId = document.getElementById("inputId");
    const inputGrupo = document.getElementById("inputGrupo");
    const inputMedida = document.getElementById("inputMedida");
    const inputIdGrupo = document.getElementById("inputIdGrupo");
    const inputIdMedida = document.getElementById("inputIdMedida");
    const inputDetalleServicio = document.getElementById("inputDetalleServicio");
    const dropdown = document.getElementById("dropdownServiciosTPyC");
    let activeIndex = -1;

    function getServicios() {
        return Array.isArray(window.SERVICIOS_DATA) ? window.SERVICIOS_DATA : [];
    }

    function renderDropdownItems(filterText = "") {
        if (!dropdown) return;
        cerrarTodosLosDropdowns();
        const query = filterText.trim().toLowerCase();
        const lista = getServicios();
        const filtradas = query
            ? lista.filter(s => (s.servicio || "").toLowerCase().includes(query))
            : lista;

        if (filtradas.length === 0) {
            dropdown.innerHTML = '<div class="tpyc-autocomplete-item" style="color: #94a3b8; cursor: default;">No se encontraron servicios</div>';
            dropdown.classList.add("show");
            return;
        }

        let html = "";
        filtradas.forEach((item, index) => {
            const nombre = escapeHtml(item.servicio || "");
            html += `<div class="tpyc-autocomplete-item" data-index="${index}">${nombre}</div>`;
        });

        dropdown.innerHTML = html;
        dropdown.classList.add("show");
        activeIndex = -1;
    }

    function hideDropdown() {
        if (dropdown) {
            dropdown.classList.remove("show");
            dropdown.innerHTML = "";
            activeIndex = -1;
        }
    }

    function seleccionarServicio(itemData) {
        if (!itemData) return;

        if (inputServicio) {
            inputServicio.value = itemData.servicio || "";
        }
        if (inputId) {
            const idServ = itemData.idservicio !== undefined && itemData.idservicio !== null
                ? itemData.idservicio
                : (itemData.id !== undefined && itemData.id !== null ? itemData.id : "");
            inputId.value = idServ;
        }
        if (inputGrupo) {
            // Mostrar nombre del grupo (varchar)
            const valGrupo = (itemData.grupo !== undefined && itemData.grupo !== null && String(itemData.grupo).trim() !== "")
                ? itemData.grupo
                : (itemData.idgrupo !== undefined && itemData.idgrupo !== null ? itemData.idgrupo : "");
            inputGrupo.value = valGrupo;
        }
        if (inputIdGrupo) {
            inputIdGrupo.value = itemData.idgrupo !== undefined && itemData.idgrupo !== null ? itemData.idgrupo : "";
        }
        if (inputMedida) {
            // Mostrar nombre de la unidad de medida (varchar)
            const valMedida = (itemData.medida !== undefined && itemData.medida !== null && String(itemData.medida).trim() !== "")
                ? itemData.medida
                : (itemData.idmedida !== undefined && itemData.idmedida !== null ? itemData.idmedida : "");
            inputMedida.value = valMedida;
        }
        if (inputIdMedida) {
            inputIdMedida.value = itemData.idmedida !== undefined && itemData.idmedida !== null ? itemData.idmedida : "";
        }
        if (inputDetalleServicio) {
            inputDetalleServicio.value = itemData.detalle || "";
        }

        // Cargar estado de checks de tarifas según el servicio
        const esCabotaje = itemData.t_n === 1 || itemData.t_n === "1" || itemData.t_n === true;
        const esEspecificas = itemData.t_e === 1 || itemData.t_e === "1" || itemData.t_e === true;
        const esNaves = itemData.t_i === 1 || itemData.t_i === "1" || itemData.t_i === true;

        if (chkCabotaje) chkCabotaje.checked = esCabotaje;
        if (chkEspecificas) chkEspecificas.checked = esEspecificas;
        if (chkNaves) chkNaves.checked = esNaves;

        // Actualizar visibilidad de paneles
        togglePanels();

        // Función auxiliar para buscar tarifa por idtarifa
        const todasTarifas = getTarifas();
        function buscarTarifaPorId(idTarifaBuscado) {
            if (!idTarifaBuscado || idTarifaBuscado === 0 || idTarifaBuscado === "0") return null;
            return todasTarifas.find(t => String(t.idtarifa || t.id || "") === String(idTarifaBuscado));
        }

        // 1. Cargar Cabotaje
        const inputScCabotaje = document.getElementById("inputScTarifaCabotaje");
        const inputNombreCabotaje = document.getElementById("inputNombreTarifaCabotaje");
        const inputIdTarifaCabotaje = document.getElementById("inputIdTarifaCabotaje");
        if (esCabotaje && itemData.cidtarifa) {
            const tFound = buscarTarifaPorId(itemData.cidtarifa);
            if (tFound) {
                if (inputScCabotaje) inputScCabotaje.value = tFound.sctarifa || tFound.codigo || "";
                if (inputNombreCabotaje) inputNombreCabotaje.value = tFound.tarifa || "";
                if (inputIdTarifaCabotaje) inputIdTarifaCabotaje.value = tFound.idtarifa || tFound.id || itemData.cidtarifa;
            } else {
                if (inputScCabotaje) inputScCabotaje.value = "";
                if (inputNombreCabotaje) inputNombreCabotaje.value = "";
                if (inputIdTarifaCabotaje) inputIdTarifaCabotaje.value = itemData.cidtarifa;
            }
        } else {
            if (inputScCabotaje) inputScCabotaje.value = "";
            if (inputNombreCabotaje) inputNombreCabotaje.value = "";
            if (inputIdTarifaCabotaje) inputIdTarifaCabotaje.value = "";
        }

        // 2. Cargar Especificas
        const inputScEspecificas = document.getElementById("inputScTarifaEspecificas");
        const inputNombreEspecificas = document.getElementById("inputNombreTarifaEspecificas");
        const inputIdTarifaEspecificas = document.getElementById("inputIdTarifaEspecificas");
        if (esEspecificas && itemData.eidtarifa) {
            const tFound = buscarTarifaPorId(itemData.eidtarifa);
            if (tFound) {
                if (inputScEspecificas) inputScEspecificas.value = tFound.sctarifa || tFound.codigo || "";
                if (inputNombreEspecificas) inputNombreEspecificas.value = tFound.tarifa || "";
                if (inputIdTarifaEspecificas) inputIdTarifaEspecificas.value = tFound.idtarifa || tFound.id || itemData.eidtarifa;
            } else {
                if (inputScEspecificas) inputScEspecificas.value = "";
                if (inputNombreEspecificas) inputNombreEspecificas.value = "";
                if (inputIdTarifaEspecificas) inputIdTarifaEspecificas.value = itemData.eidtarifa;
            }
        } else {
            if (inputScEspecificas) inputScEspecificas.value = "";
            if (inputNombreEspecificas) inputNombreEspecificas.value = "";
            if (inputIdTarifaEspecificas) inputIdTarifaEspecificas.value = "";
        }

        // 3. Cargar Naves
        const inputScNaves = document.getElementById("inputScTarifaNaves");
        const inputNombreNaves = document.getElementById("inputNombreTarifaNaves");
        const inputIdTarifaNaves = document.getElementById("inputIdTarifaNaves");
        if (esNaves && itemData.nidtarifa) {
            const tFound = buscarTarifaPorId(itemData.nidtarifa);
            if (tFound) {
                if (inputScNaves) inputScNaves.value = tFound.sctarifa || tFound.codigo || "";
                if (inputNombreNaves) inputNombreNaves.value = tFound.tarifa || "";
                if (inputIdTarifaNaves) inputIdTarifaNaves.value = tFound.idtarifa || tFound.id || itemData.nidtarifa;
            } else {
                if (inputScNaves) inputScNaves.value = "";
                if (inputNombreNaves) inputNombreNaves.value = "";
                if (inputIdTarifaNaves) inputIdTarifaNaves.value = itemData.nidtarifa;
            }
        } else {
            if (inputScNaves) inputScNaves.value = "";
            if (inputNombreNaves) inputNombreNaves.value = "";
            if (inputIdTarifaNaves) inputIdTarifaNaves.value = "";
        }

        hideDropdown();
    }

    if (inputServicio && dropdown) {
        inputServicio.addEventListener("focus", function() {
            renderDropdownItems(this.value);
        });

        inputServicio.addEventListener("click", function() {
            renderDropdownItems(this.value);
        });

        inputServicio.addEventListener("input", function() {
            renderDropdownItems(this.value);
            const query = this.value.trim().toLowerCase();
            const lista = getServicios();
            const exactMatch = lista.find(s => (s.servicio || "").trim().toLowerCase() === query);
            if (!exactMatch) {
                // Es un servicio nuevo o editado manualmente: limpiar ID para creación
                if (inputId) inputId.value = "";
                if (inputIdGrupo) inputIdGrupo.value = "";
                if (inputIdMedida) inputIdMedida.value = "";
            } else {
                // Coincidencia exacta con uno existente: seleccionar sus datos
                seleccionarServicio(exactMatch);
            }
        });

        inputServicio.addEventListener("keydown", function(e) {
            const items = dropdown.querySelectorAll(".tpyc-autocomplete-item:not([style*='cursor: default'])");
            if (!items.length || !dropdown.classList.contains("show")) return;

            if (e.key === "ArrowDown") {
                e.preventDefault();
                activeIndex = (activeIndex + 1) % items.length;
                updateActiveItem(items);
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                activeIndex = (activeIndex - 1 + items.length) % items.length;
                updateActiveItem(items);
            } else if (e.key === "Enter") {
                e.preventDefault();
                if (activeIndex >= 0 && items[activeIndex]) {
                    const idx = parseInt(items[activeIndex].getAttribute("data-index"), 10);
                    const lista = getServicios();
                    const query = inputServicio.value.trim().toLowerCase();
                    const filtradas = query ? lista.filter(s => (s.servicio || "").toLowerCase().includes(query)) : lista;
                    if (filtradas[idx]) {
                        seleccionarServicio(filtradas[idx]);
                    }
                }
            } else if (e.key === "Escape") {
                hideDropdown();
            }
        });

        function updateActiveItem(items) {
            items.forEach((item, idx) => {
                if (idx === activeIndex) {
                    item.classList.add("active");
                    item.scrollIntoView({ block: "nearest" });
                } else {
                    item.classList.remove("active");
                }
            });
        }

        dropdown.addEventListener("click", function(e) {
            const itemElem = e.target.closest(".tpyc-autocomplete-item");
            if (itemElem && !itemElem.hasAttribute("style")) {
                const idx = parseInt(itemElem.getAttribute("data-index"), 10);
                const lista = getServicios();
                const query = inputServicio ? inputServicio.value.trim().toLowerCase() : "";
                const filtradas = query ? lista.filter(s => (s.servicio || "").toLowerCase().includes(query)) : lista;
                if (filtradas[idx]) {
                    seleccionarServicio(filtradas[idx]);
                }
            }
        });

        document.addEventListener("click", function(e) {
            if (!inputServicio.contains(e.target) && !dropdown.contains(e.target)) {
                hideDropdown();
            }
        });
    }

    // =========================================================
    // AUTOCOMPLETADO Y SELECCIÓN ESTRICTA: GRUPO Y MEDIDA
    // =========================================================
    function getGrupos() {
        return Array.isArray(window.GRUPOS_DATA) ? window.GRUPOS_DATA : [];
    }

    function getMedidas() {
        return Array.isArray(window.MEDIDAS_DATA) ? window.MEDIDAS_DATA : [];
    }

    function setupCatalogoAutocomplete(inputId, inputHiddenId, dropdownId, getItemsFn, labelKey, valueKey) {
        const inputElem = document.getElementById(inputId);
        const inputHidden = document.getElementById(inputHiddenId);
        const dropdownElem = document.getElementById(dropdownId);

        if (!inputElem || !dropdownElem) return;

        function cerrarDropdownCatalogo() {
            dropdownElem.classList.remove("show");
            dropdownElem.innerHTML = "";
        }

        function renderDropdownCatalogo(filterText = "") {
            cerrarTodosLosDropdowns();
            const query = filterText.trim().toLowerCase();
            const lista = getItemsFn();
            const filtradas = query
                ? lista.filter(item => (item[labelKey] || "").toLowerCase().includes(query))
                : lista;

            if (filtradas.length === 0) {
                dropdownElem.innerHTML = '<div class="tpyc-autocomplete-item" style="color: #94a3b8; cursor: default;">No se encontraron opciones</div>';
                dropdownElem.classList.add("show");
                return;
            }

            let html = "";
            filtradas.forEach((item, index) => {
                const text = escapeHtml(item[labelKey] || "");
                html += `<div class="tpyc-autocomplete-item" data-index="${index}">${text}</div>`;
            });

            dropdownElem.innerHTML = html;
            dropdownElem.classList.add("show");
        }

        function seleccionarItem(item) {
            if (!item) return;
            inputElem.value = item[labelKey] || "";
            if (inputHidden) {
                inputHidden.value = item[valueKey] !== undefined ? item[valueKey] : "";
            }
            cerrarDropdownCatalogo();
        }

        inputElem.addEventListener("focus", function() {
            renderDropdownCatalogo(this.value);
        });

        inputElem.addEventListener("click", function() {
            renderDropdownCatalogo(this.value);
        });

        inputElem.addEventListener("input", function() {
            renderDropdownCatalogo(this.value);
            const val = this.value.trim().toLowerCase();
            const lista = getItemsFn();
            const coincidencia = lista.find(item => (item[labelKey] || "").toLowerCase() === val);
            if (coincidencia) {
                if (inputHidden) inputHidden.value = coincidencia[valueKey] !== undefined ? coincidencia[valueKey] : "";
            } else {
                if (inputHidden) inputHidden.value = "";
            }
        });

        inputElem.addEventListener("blur", function() {
            // Validación estricta: si lo escrito no coincide exactamente con un elemento existente, limpiamos
            setTimeout(() => {
                const val = inputElem.value.trim().toLowerCase();
                if (!val) {
                    if (inputHidden) inputHidden.value = "";
                    return;
                }
                const lista = getItemsFn();
                const coincidencia = lista.find(item => (item[labelKey] || "").toLowerCase() === val);
                if (coincidencia) {
                    inputElem.value = coincidencia[labelKey] || "";
                    if (inputHidden) inputHidden.value = coincidencia[valueKey] !== undefined ? coincidencia[valueKey] : "";
                } else {
                    inputElem.value = "";
                    if (inputHidden) inputHidden.value = "";
                }
            }, 200);
        });

        dropdownElem.addEventListener("mousedown", function(e) {
            // Prevenir que el blur del input ocurra antes de que se procese el click
            e.preventDefault();
            const itemElem = e.target.closest(".tpyc-autocomplete-item");
            if (itemElem && !itemElem.hasAttribute("style")) {
                const idx = parseInt(itemElem.getAttribute("data-index"), 10);
                const lista = getItemsFn();
                const query = inputElem.value.trim().toLowerCase();
                const filtradas = query ? lista.filter(item => (item[labelKey] || "").toLowerCase().includes(query)) : lista;
                if (filtradas[idx]) {
                    seleccionarItem(filtradas[idx]);
                }
            }
        });

        document.addEventListener("click", function(e) {
            if (!inputElem.contains(e.target) && !dropdownElem.contains(e.target)) {
                cerrarDropdownCatalogo();
            }
        });
    }

    // Inicializar autocompletados para Grupo y Medida
    setupCatalogoAutocomplete("inputGrupo", "inputIdGrupo", "dropdownGrupoServicio", getGrupos, "gruposer", "id");
    setupCatalogoAutocomplete("inputMedida", "inputIdMedida", "dropdownMedidaServicio", getMedidas, "medida", "id");

    // Función Notificación Toast
    function showToast(message, type = 'info') {
        const container = document.getElementById("toastContainer");
        if (!container) return;
        const toast = document.createElement("div");
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
        setTimeout(() => toast.classList.add("show"), 50);
        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Modales de Confirmación y Éxito
    const modalConfirmarCrear = document.getElementById("modalConfirmarCrear");
    const modalCrearTexto = document.getElementById("modalCrearTexto");
    const btnCancelarCrear = document.getElementById("btnCancelarCrear");
    const btnConfirmarCrear = document.getElementById("btnConfirmarCrear");

    const modalConfirmarActualizar = document.getElementById("modalConfirmarActualizar");
    const modalConfirmarTexto = document.getElementById("modalConfirmarTexto");
    const btnCancelarActualizar = document.getElementById("btnCancelarActualizar");
    const btnConfirmarActualizar = document.getElementById("btnConfirmarActualizar");

    const modalExito = document.getElementById("modalExito");
    const modalExitoTitulo = document.getElementById("modalExitoTitulo");
    const modalExitoTexto = document.getElementById("modalExitoTexto");
    const btnCerrarExito = document.getElementById("btnCerrarExito");

    function cerrarModales() {
        if (modalConfirmarCrear) modalConfirmarCrear.classList.add("hidden");
        if (modalConfirmarActualizar) modalConfirmarActualizar.classList.add("hidden");
        if (modalExito) modalExito.classList.add("hidden");
    }

    if (btnCancelarCrear) btnCancelarCrear.addEventListener("click", cerrarModales);
    if (btnCancelarActualizar) btnCancelarActualizar.addEventListener("click", cerrarModales);
    if (btnCerrarExito) btnCerrarExito.addEventListener("click", cerrarModales);

    [modalConfirmarCrear, modalConfirmarActualizar, modalExito].forEach(modal => {
        if (modal) {
            modal.addEventListener("click", function(e) {
                if (e.target === modal) {
                    cerrarModales();
                }
            });
        }
    });

    document.addEventListener("keydown", function(e) {
        if (e.key === "Escape") {
            cerrarModales();
        }
    });

    function mostrarModalExito(titulo, mensaje) {
        if (modalExitoTitulo) modalExitoTitulo.textContent = titulo;
        if (modalExitoTexto) modalExitoTexto.textContent = mensaje;
        if (modalExito) modalExito.classList.remove("hidden");
    }

    // Función que envía los datos (creación o actualización)
    async function enviarGuardadoServicio(payload, esActualizacion) {
        btnGuardar.disabled = true;
        btnGuardar.textContent = esActualizacion ? "Actualizando..." : "Guardando...";

        try {
            const response = await fetch("/tarifa/servicios-tpyc/guardar/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            const result = await response.json();

            if (response.ok && result.success) {
                cerrarModales();

                // Mostrar recuadro en el medio con mensaje exitoso
                const tituloExito = esActualizacion ? "¡Actualizado Exitosamente!" : "¡Guardado Exitosamente!";
                const mensajeExito = result.mensaje || (esActualizacion ? "El servicio se ha actualizado correctamente en el sistema." : "El servicio se ha guardado correctamente en el sistema.");
                mostrarModalExito(tituloExito, mensajeExito);

                if (inputId && result.idservicio) {
                    inputId.value = result.idservicio;
                }

                // Sincronizar autocompletado en memoria
                if (Array.isArray(window.SERVICIOS_DATA)) {
                    const idx = window.SERVICIOS_DATA.findIndex(s => s.idservicio === result.idservicio || s.id === result.idservicio);
                    const itemDataActualizado = {
                        idservicio: result.idservicio,
                        servicio: payload.servicio,
                        idgrupo: payload.idgrupo,
                        grupo: payload.grupo,
                        idmedida: payload.idmedida,
                        medida: payload.medida,
                        detalle: payload.detalle,
                        t_n: payload.t_n,
                        t_e: payload.t_e,
                        t_i: payload.t_i,
                        cidtarifa: payload.cidtarifa,
                        eidtarifa: payload.eidtarifa,
                        nidtarifa: payload.nidtarifa,
                    };

                    if (idx >= 0) {
                        window.SERVICIOS_DATA[idx] = itemDataActualizado;
                    } else {
                        window.SERVICIOS_DATA.push(itemDataActualizado);
                    }
                }
            } else {
                showToast(result.mensaje || "Error al procesar el servicio.", "error");
            }
        } catch (err) {
            console.error("Error en la solicitud:", err);
            showToast("Error de conexión al procesar el servicio.", "error");
        } finally {
            btnGuardar.disabled = false;
            btnGuardar.textContent = "Guardar";
        }
    }

    // Botón Guardar
    const btnGuardar = document.getElementById("btnGuardar");
    if (btnGuardar) {
        btnGuardar.addEventListener("click", function() {
            const servicioVal = inputServicio ? inputServicio.value.trim() : "";
            if (!servicioVal) {
                showToast("Por favor ingrese el nombre del servicio.", "warning");
                if (inputServicio) inputServicio.focus();
                return;
            }

            const grupoVal = inputGrupo ? inputGrupo.value.trim() : "";
            if (!grupoVal) {
                showToast("Por favor seleccione un Grupo válido de la lista.", "warning");
                if (inputGrupo) inputGrupo.focus();
                return;
            }

            const medidaVal = inputMedida ? inputMedida.value.trim() : "";
            if (!medidaVal) {
                showToast("Por favor seleccione una Medida válida de la lista.", "warning");
                if (inputMedida) inputMedida.focus();
                return;
            }

            const isCabotaje = chkCabotaje ? chkCabotaje.checked : false;
            const isEspecificas = chkEspecificas ? chkEspecificas.checked : false;
            const isNaves = chkNaves ? chkNaves.checked : false;

            const inputIdTarifaCabotaje = document.getElementById("inputIdTarifaCabotaje");
            const inputIdTarifaEspecificas = document.getElementById("inputIdTarifaEspecificas");
            const inputIdTarifaNaves = document.getElementById("inputIdTarifaNaves");

            const cidtarifa = isCabotaje && inputIdTarifaCabotaje ? parseInt(inputIdTarifaCabotaje.value || "0", 10) : 0;
            const eidtarifa = isEspecificas && inputIdTarifaEspecificas ? parseInt(inputIdTarifaEspecificas.value || "0", 10) : 0;
            const nidtarifa = isNaves && inputIdTarifaNaves ? parseInt(inputIdTarifaNaves.value || "0", 10) : 0;

            if (isCabotaje && (!cidtarifa || isNaN(cidtarifa) || cidtarifa <= 0)) {
                showToast("Por favor seleccione una tarifa válida para T.Cabotaje o desmarque la casilla.", "warning");
                const inputNombreCab = document.getElementById("inputNombreTarifaCabotaje");
                if (inputNombreCab) inputNombreCab.focus();
                return;
            }
            if (isEspecificas && (!eidtarifa || isNaN(eidtarifa) || eidtarifa <= 0)) {
                showToast("Por favor seleccione una tarifa válida para T.Especificas o desmarque la casilla.", "warning");
                const inputNombreEsp = document.getElementById("inputNombreTarifaEspecificas");
                if (inputNombreEsp) inputNombreEsp.focus();
                return;
            }
            if (isNaves && (!nidtarifa || isNaN(nidtarifa) || nidtarifa <= 0)) {
                showToast("Por favor seleccione una tarifa válida para T.Naves o desmarque la casilla.", "warning");
                const inputNombreNav = document.getElementById("inputNombreTarifaNaves");
                if (inputNombreNav) inputNombreNav.focus();
                return;
            }

            const detalleVal = inputDetalleServicio ? inputDetalleServicio.value.trim() : "";
            const idgrupoVal = inputIdGrupo && inputIdGrupo.value ? parseInt(inputIdGrupo.value, 10) : null;
            const idmedidaVal = inputIdMedida && inputIdMedida.value ? parseInt(inputIdMedida.value, 10) : null;

            const idActualVal = inputId && inputId.value.trim() ? parseInt(inputId.value.trim(), 10) : null;
            const esActualizacion = !!(idActualVal && !isNaN(idActualVal) && idActualVal > 0);

            const payload = {
                idservicio: esActualizacion ? idActualVal : null,
                servicio: servicioVal,
                medida: medidaVal,
                grupo: grupoVal,
                detalle: detalleVal,
                t_n: isCabotaje ? 1 : 0,
                t_e: isEspecificas ? 1 : 0,
                t_i: isNaves ? 1 : 0,
                cidtarifa: isNaN(cidtarifa) ? 0 : cidtarifa,
                eidtarifa: isNaN(eidtarifa) ? 0 : eidtarifa,
                nidtarifa: isNaN(nidtarifa) ? 0 : nidtarifa,
                idgrupo: idgrupoVal,
                idmedida: idmedidaVal,
            };

            if (esActualizacion) {
                // Modal de confirmación para Actualizar
                if (modalConfirmarTexto) {
                    modalConfirmarTexto.innerHTML = `Está a punto de modificar el servicio <strong>"${escapeHtml(servicioVal)}"</strong> (ID: <strong>${idActualVal}</strong>).<br><br>¿Desea guardar los cambios efectuados?`;
                }
                if (modalConfirmarActualizar) {
                    modalConfirmarActualizar.classList.remove("hidden");
                }

                if (btnConfirmarActualizar) {
                    btnConfirmarActualizar.onclick = function() {
                        enviarGuardadoServicio(payload, true);
                    };
                }
            } else {
                // Modal de confirmación para Registrar Nuevo Servicio
                if (modalCrearTexto) {
                    modalCrearTexto.innerHTML = `Está a punto de registrar el nuevo servicio <strong>"${escapeHtml(servicioVal)}"</strong>.<br><br>¿Desea registrarlo en el sistema?`;
                }
                if (modalConfirmarCrear) {
                    modalConfirmarCrear.classList.remove("hidden");
                }

                if (btnConfirmarCrear) {
                    btnConfirmarCrear.onclick = function() {
                        enviarGuardadoServicio(payload, false);
                    };
                }
            }
        });
    }

    // Botón Limpiar
    const btnLimpiar = document.getElementById("btnLimpiar");
    if (btnLimpiar) {
        btnLimpiar.addEventListener("click", function() {
            const form = document.getElementById("formServiciosTPyC");
            if (form) {
                form.reset();
            }
            if (inputIdGrupo) inputIdGrupo.value = "";
            if (inputIdMedida) inputIdMedida.value = "";
            if (inputDetalleServicio) inputDetalleServicio.value = "";
            ["inputScTarifaCabotaje", "inputNombreTarifaCabotaje", "inputIdTarifaCabotaje",
             "inputScTarifaEspecificas", "inputNombreTarifaEspecificas", "inputIdTarifaEspecificas",
             "inputScTarifaNaves", "inputNombreTarifaNaves", "inputIdTarifaNaves"].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.value = "";
            });
            document.querySelectorAll(".tpyc-autocomplete-dropdown").forEach(dd => {
                dd.classList.remove("show");
                dd.innerHTML = "";
            });
            document.querySelectorAll(".tpyc-textarea").forEach(textarea => {
                textarea.value = "";
            });
            togglePanels();
            hideDropdown();
            showToast("Formulario limpiado.", "warning");
        });
    }

    // Estado inicial de paneles
    togglePanels();
});

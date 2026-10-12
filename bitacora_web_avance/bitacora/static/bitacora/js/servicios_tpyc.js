document.addEventListener("DOMContentLoaded", function() {
    // Referencias a los checkboxes y paneles
    const chkCabotaje = document.getElementById("chkCabotaje");
    const chkEspecificas = document.getElementById("chkEspecificas");
    const chkNaves = document.getElementById("chkNaves");

    const panelCabotaje = document.getElementById("panelCabotaje");
    const panelEspecificas = document.getElementById("panelEspecificas");
    const panelNaves = document.getElementById("panelNaves");

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
    // AUTOCOMPLETADO DE SERVICIOS (SPJ_v_servicios)
    // =========================================================
    const inputServicio = document.getElementById("inputServicio");
    const inputId = document.getElementById("inputId");
    const inputGrupo = document.getElementById("inputGrupo");
    const inputMedida = document.getElementById("inputMedida");
    const dropdown = document.getElementById("dropdownServiciosTPyC");
    let activeIndex = -1;

    function getServicios() {
        return Array.isArray(window.SERVICIOS_DATA) ? window.SERVICIOS_DATA : [];
    }

    function renderDropdownItems(filterText = "") {
        if (!dropdown) return;
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

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    function seleccionarServicio(itemData) {
        if (!itemData) return;

        if (inputServicio) {
            inputServicio.value = itemData.servicio || "";
        }
        if (inputId) {
            inputId.value = itemData.idservicio !== undefined && itemData.idservicio !== null ? itemData.idservicio : "";
        }
        if (inputGrupo) {
            const valGrupo = itemData.idgrupo !== undefined && itemData.idgrupo !== null ? itemData.idgrupo : (itemData.grupo || "");
            inputGrupo.value = valGrupo;
        }
        if (inputMedida) {
            const valMedida = itemData.idmedida !== undefined && itemData.idmedida !== null ? itemData.idmedida : (itemData.medida || "");
            inputMedida.value = valMedida;
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

    // Función Notificación Toast
    function showToast(message, type = 'info') {
        const container = document.getElementById("toastContainer");
        if (!container) return;
        const toast = document.createElement("div");
        toast.className = `toast ${type} show`;
        toast.innerHTML = `<span>${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Botón Guardar
    const btnGuardar = document.getElementById("btnGuardar");
    if (btnGuardar) {
        btnGuardar.addEventListener("click", function() {
            showToast("Registro guardado exitosamente.", "success");
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
            togglePanels();
            hideDropdown();
            showToast("Formulario limpiado.", "warning");
        });
    }

    // Estado inicial de paneles
    togglePanels();
});

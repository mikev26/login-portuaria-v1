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

    // Agregar filas a tablas
    document.querySelectorAll(".tpyc-btn-add-row").forEach(button => {
        button.addEventListener("click", function() {
            const targetId = this.getAttribute("data-target");
            const tbody = document.querySelector(`#${targetId} tbody`);
            if (tbody) {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><input type="number" class="tpyc-input" value="0" step="any"></td>
                    <td><input type="text" class="tpyc-input" value="" placeholder="Ingrese descripción"></td>
                    <td><button type="button" class="tpyc-btn-remove-row" title="Eliminar fila">&times;</button></td>
                `;
                tbody.appendChild(tr);
            }
        });
    });

    // Eliminar filas
    document.addEventListener("click", function(e) {
        if (e.target && e.target.classList.contains("tpyc-btn-remove-row")) {
            const tr = e.target.closest("tr");
            if (tr) {
                tr.remove();
            }
        }
    });

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
            showToast("Formulario limpiado.", "warning");
        });
    }

    // Estado inicial de paneles
    togglePanels();
});

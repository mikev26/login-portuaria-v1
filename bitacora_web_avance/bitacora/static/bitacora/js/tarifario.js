// Toast Notification helper
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

    // Format Valor field to 4 decimal places
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
        document.getElementById('tarifaActiva').checked = true;
        document.getElementById('tarifaTasa').value = "";
        document.getElementById('tarifaName').value = "";
        document.getElementById('tarifaPartidaCod').value = "";
        document.getElementById('tarifaPartidaDesc').value = "";
        document.getElementById('tarifaFormula').value = "";
        document.getElementById('tarifaDetalle').value = "";
        document.getElementById('tarifaValor').value = "0.0000";
        document.getElementById('tarifaSAnte').value = "";
        document.getElementById('tarifaIva').checked = false;
        document.getElementById('tarifaSenaeCod').value = "";
        document.getElementById('tarifaSenaeDesc').value = "";

        // Reset radio choices
        document.querySelector('input[name="calc_param"][value="eslora"]').checked = true;
        document.querySelector('input[name="calc_unidad"][value="dia"]').checked = true;
        document.querySelector('input[name="ticket_srv"][value="ninguno"]').checked = true;

        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            updateRadioSelection(radio);
        });

        // Remove active class from table rows
        document.querySelectorAll('#tarifasTable tbody tr').forEach(row => {
            row.style.background = "";
        });
    }

    // Populate form with row data
    function loadTarifaData(data) {
        document.getElementById('tarifaId').value = data.id || "0";
        document.getElementById('tarifaCodigo').value = data.codigo || "";
        document.getElementById('tarifaActiva').checked = !!data.activa;
        document.getElementById('tarifaTasa').value = data.tasa || "";
        document.getElementById('tarifaName').value = data.tarifa || "";
        document.getElementById('tarifaPartidaCod').value = data.partida_cod || "";
        document.getElementById('tarifaPartidaDesc').value = data.partida_desc || "";
        document.getElementById('tarifaFormula').value = data.formula || "";
        document.getElementById('tarifaDetalle').value = data.detalle || "";
        document.getElementById('tarifaValor').value = data.valor || "0.0000";
        document.getElementById('tarifaSAnte').value = data.s_ante || "";
        document.getElementById('tarifaIva').checked = !!data.se_cobra_iva;
        document.getElementById('tarifaSenaeCod').value = data.senae_cod || "";
        document.getElementById('tarifaSenaeDesc').value = data.senae_desc || "";

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
        if (action === 'save') {
            const code = document.getElementById('tarifaCodigo').value.trim();
            const desc = document.getElementById('tarifaName').value.trim();
            if (!code || !desc) {
                showToast("Por favor complete los campos obligatorios (Codigo y Tarifa).", "warning");
                return;
            }
            showToast(`¡Tarifa [${code}] guardada correctamente en el sistema!`);
        } else if (action === 'saveNew') {
            const code = document.getElementById('tarifaCodigo').value.trim();
            if (!code) {
                showToast("Por favor ingrese al menos el Código para guardar.", "warning");
                return;
            }
            showToast(`¡Guardado exitoso! Preparando nueva entrada.`);
            clearForm();
        } else if (action === 'cancel') {
            const id = document.getElementById('tarifaId').value;
            if (id === "0") {
                showToast("No se puede anular un registro nuevo sin guardar.", "warning");
            } else {
                showToast(`Registro ID ${id} anulado correctamente de los registros.`, "warning");
                clearForm();
            }
        } else if (action === 'list') {
            showToast("Abriendo listado general de tarifas...");
        } else if (action === 'select') {
            showToast("Buscando registros en el sistema...");
        } else if (action === 'new') {
            showToast("Formulario limpio para ingreso de nuevos datos.");
            clearForm();
        } else if (action === 'refresh') {
            showToast("Formulario restaurado y actualizado.");
            clearForm();
        }
    }

    // Setup interactive events
    document.addEventListener('DOMContentLoaded', () => {
        // Table row click listener for auto-filling the form
        const rows = document.querySelectorAll('#tarifasTable tbody tr');
        rows.forEach(row => {
            row.addEventListener('click', () => {
                // Highlight selected row
                rows.forEach(r => r.style.background = "");
                row.style.background = "rgba(29, 111, 159, 0.08)";
                
                // Parse JSON data attribute
                const rawData = row.dataset.tarifa;
                if (rawData) {
                    try {
                        const data = JSON.parse(rawData);
                        loadTarifaData(data);
                        showToast(`Tarifa seleccionada: ${data.tasa} (Código ${data.codigo})`);
                    } catch (e) {
                        console.error("Error parsing row data:", e);
                    }
                }
            });
        });

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
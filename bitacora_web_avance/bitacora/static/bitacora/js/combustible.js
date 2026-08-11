document.addEventListener("DOMContentLoaded", function () {
        const form = document.querySelector(".date-range-form");
        const tableBody = document.querySelector("#report-table-body");
        const messagesContainer = document.querySelector("#report-messages");
        const fechaDesdeElement = document.querySelector("#header-fecha-desde");
        const fechaHastaElement = document.querySelector("#header-fecha-hasta");
        const submitButton = form.querySelector("button[type=submit]");
        const exportLink = document.querySelector("#export-link");
        const exportMessage = document.querySelector('#export-message');

        function clearExportMessage() {
            if (exportMessage) {
                exportMessage.innerHTML = '';
            }
        }

        function setExportEnabled(enabled) {
            if (!exportLink) return;
            exportLink.dataset.enabled = enabled ? 'true' : 'false';
            exportLink.style.opacity = enabled ? '1' : '0.55';
            exportLink.style.pointerEvents = enabled ? 'auto' : 'none';
            exportLink.style.cursor = enabled ? 'pointer' : 'not-allowed';
            exportLink.setAttribute('aria-disabled', String(!enabled));
            if (enabled) {
                exportLink.href = exportLink.dataset.exportUrl || exportLink.getAttribute('data-export-url');
            } else {
                exportLink.href = '#';
            }
        }

        if (exportLink) {
            setExportEnabled(false);
            exportLink.addEventListener("click", async function (ev) {
                ev.preventDefault();
                if (exportLink.dataset.enabled !== 'true') {
                    if (exportMessage) {
                        exportMessage.innerHTML = '<div class="message-banner info">Primero debe realizar una búsqueda para exportar la información.</div>';
                    }
                    return;
                }

                const exportUrl = exportLink.dataset.exportUrl || exportLink.getAttribute('data-export-url');
                const validateUrl = exportLink.dataset.validateUrl || exportLink.getAttribute('data-validate-url');
                if (!validateUrl) {
                    clearExportMessage();
                    return;
                }

                try {
                    const resp = await fetch(validateUrl, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
                    });
                    if (!resp.ok) throw new Error('Network');
                    const data = await resp.json();
                    if (data.ok) {
                        clearExportMessage();
                        window.location.href = exportUrl;
                    } else {
                        const cls = data.level === 'error' ? 'error' : 'info';
                        if (exportMessage) {
                            exportMessage.innerHTML = `<div class="message-banner ${cls}">${data.message}</div>`;
                        }
                    }
                } catch (err) {
                    if (exportMessage) {
                        exportMessage.innerHTML = '<div class="message-banner error">No fue posible comunicarse con el servidor. Intente nuevamente.</div>';
                    }
                }
            });
        }

        form.querySelectorAll('input').forEach(function (input) {
            input.addEventListener('input', function () {
                clearExportMessage();
                setExportEnabled(false);
            });
        });

        if (exportLink && tableBody.querySelectorAll('tr').length && !tableBody.querySelector('tr.table-placeholder')) {
            setExportEnabled(true);
        }

        function formatIsoDate(value) {
            if (!value) {
                return "";
            }
            const dateValue = new Date(value);
            if (Number.isNaN(dateValue.getTime())) {
                return value;
            }
            const day = String(dateValue.getDate()).padStart(2, "0");
            const month = String(dateValue.getMonth() + 1).padStart(2, "0");
            const year = dateValue.getFullYear();
            return `${day}/${month}/${year}`;
        }

        function buildMessageHtml(messages) {
            return messages
                .map(msg => `<div class="message-banner ${msg.tags}">${msg.text}</div>`)
                .join("");
        }

        function buildTableRows(rows) {
            if (!rows || !rows.length) {
                return `
                    <tr class="table-placeholder">
                        <td colspan="10">No hay datos disponibles. Seleccione fechas y presione Buscar.</td>
                    </tr>
                `;
            }

            return rows
                .map(row => `
                    <tr>
                        <td>${row.fecha_ingresa}</td>
                        <td>${row.c_tikect}</td>
                        <td>${row.guia}</td>
                        <td>${row.idplaca}</td>
                        <td>${row.chofer}</td>
                        <td>${row.codbuque}</td>
                        <td>${row.buque}</td>
                        <td>${row.matricula}</td>
                        <td>${row.galones}</td>
                        <td>${row.motivo}</td>
                    </tr>
                `)
                .join("");
        }

        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            clearExportMessage();
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = "Buscando...";

            const formData = new FormData(form);
            formData.set("buscar", "1");
            const params = new URLSearchParams(formData);
            const url = `${window.location.pathname}?${params.toString()}`;

            try {
                const response = await fetch(url, {
                    method: "GET",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json",
                    },
                });
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                const data = await response.json();

                messagesContainer.innerHTML = buildMessageHtml(data.messages);
                fechaDesdeElement.textContent = formatIsoDate(data.fecha_desde);
                fechaHastaElement.textContent = formatIsoDate(data.fecha_hasta);
                tableBody.innerHTML = buildTableRows(data.rows);

                if (exportLink) {
                    const rowsExist = data.rows && data.rows.length;
                    if (rowsExist) {
                        setExportEnabled(true);
                        clearExportMessage();
                    } else {
                        setExportEnabled(false);
                        clearExportMessage();
                    }
                }
            } catch (error) {
                messagesContainer.innerHTML = `<div class="message-banner error">No fue posible comunicarse con el servidor. Intente nuevamente.</div>`;
                tableBody.innerHTML = `
                    <tr class="table-placeholder">
                        <td colspan="10">No hay datos disponibles. Seleccione fechas y presione Buscar.</td>
                    </tr>
                `;
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        });
    });
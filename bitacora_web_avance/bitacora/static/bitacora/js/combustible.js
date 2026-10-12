document.addEventListener("DOMContentLoaded", function () {
        const form = document.querySelector(".date-range-form");
        const tableBody = document.querySelector("#report-table-body");
        const messagesContainer = document.querySelector("#report-messages");
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

        function buildMessageHtml(messages) {
            return messages
                .map(msg => `<div class="message-banner ${escapeHtml(msg.tags)}">${escapeHtml(msg.text)}</div>`)
                .join("");
        }

        function escapeHtml(value) {
            return String(value ?? "").replace(/[&<>"']/g, character => ({
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            })[character]);
        }

        function buildTableRows(rows) {
            if (!rows || !rows.length) {
                return `
                    <tr class="table-placeholder">
                        <td colspan="13">No hay datos disponibles. Seleccione fechas y presione Buscar.</td>
                    </tr>
                `;
            }

            return rows
                .map(row => `
                    <tr>
                        <td>${escapeHtml(row.fecha_ingresa)}</td>
                        <td>${escapeHtml(row.c_tikect)}</td>
                        <td>${escapeHtml(row.guia)}</td>
                        <td>${escapeHtml(row.idplaca)}</td>
                        <td>${escapeHtml(row.chofer)}</td>
                        <td>${escapeHtml(row.licencia)}</td>
                        <td>${escapeHtml(row.codbuque)}</td>
                        <td>${escapeHtml(row.buque)}</td>
                        <td>${escapeHtml(row.matricula)}</td>
                        <td>${escapeHtml(row.galones)}</td>
                        <td>${escapeHtml(row.motivo)}</td>
                        <td>${escapeHtml(row.estado)}</td>
                        <td>${escapeHtml(row.tipo_carro)}</td>
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
                        <td colspan="13">No hay datos disponibles. Seleccione fechas y presione Buscar.</td>
                    </tr>
                `;
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        });
    });
document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector(".date-range-form");
    const tableBody = document.querySelector("#report-table-body");
    const messagesContainer = document.querySelector("#report-messages");
    const anioHeader = document.querySelector("#header-anio");
    const semestreHeader = document.querySelector("#header-semestre");
    const submitButton = form.querySelector("button[type=submit]");
    const exportButton = document.querySelector("#btn-exportar-excel");

    const EMPTY_TABLE_MESSAGE = "No hay datos disponibles. Seleccione año y semestre, y presione Buscar.";
    const NO_RESULTS_MESSAGE = "No existen registros.";

    let hasSearched = false;
    let currentRowsCount = 0;
    let inputsChanged = false;

    // Detectar si la página cargó inicialmente con datos
    const initialRows = tableBody.querySelectorAll("tr:not(.table-placeholder)");
    if (initialRows.length > 0) {
        hasSearched = true;
        currentRowsCount = initialRows.length;
    }

    const anioSelect = form.querySelector("[name=anio]");
    const semestreSelect = form.querySelector("[name=semestre]");

    if (anioSelect) {
        anioSelect.addEventListener("change", () => { inputsChanged = true; });
    }
    if (semestreSelect) {
        semestreSelect.addEventListener("change", () => { inputsChanged = true; });
    }

    function buildMessageHtml(messages) {
        return messages
            .map(msg => `<div class="message-banner ${msg.tags}">${msg.text}</div>`)
            .join("");
    }

    function buildEmptyTableRow(message) {
        return `
            <tr class="table-placeholder">
                <td colspan="12">${message}</td>
            </tr>
        `;
    }

    function buildTableRows(rows) {
        if (!Array.isArray(rows) || rows.length === 0) {
            return buildEmptyTableRow(NO_RESULTS_MESSAGE);
        }

        return rows
            .map(row => `
                <tr>
                    <td>${row["Registro"] ?? ""}</td>
                    <td>${row["CodBuque"] ?? ""}</td>
                    <td>${row["Matrícula"] ?? row["Matricula"] ?? ""}</td>
                    <td>${row["Buque"] ?? ""}</td>
                    <td>${row["Tipo de Nave"] ?? row["TipoNave"] ?? ""}</td>
                    <td>${row["Arribo"] ?? ""}</td>
                    <td>${row["Zarpe"] ?? ""}</td>
                    <td>${row["Bandera"] ?? ""}</td>
                    <td>${row["TRB"] ?? ""}</td>
                    <td>${row["TRN"] ?? ""}</td>
                    <td>${row["Agencia"] ?? ""}</td>
                    <td>${row["Total Descarga"] ?? row["TotalDescarga"] ?? ""}</td>
                </tr>
            `)
            .join("");
    }

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
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

            messagesContainer.innerHTML = buildMessageHtml(data.messages || []);
            anioHeader.textContent = data.anio || "—";
            semestreHeader.textContent = data.semestre || "—";
            tableBody.innerHTML = buildTableRows(data.rows || []);

            hasSearched = true;
            inputsChanged = false;
            currentRowsCount = Array.isArray(data.rows) ? data.rows.length : 0;

            if (!data.rows || !data.rows.length) {
                const noDataMessage = data.messages?.some(m => m.tags === "info")
                    ? data.messages.find(m => m.tags === "info").text
                    : NO_RESULTS_MESSAGE;
                messagesContainer.innerHTML = buildMessageHtml(data.messages && data.messages.length ? data.messages : [{ text: noDataMessage, tags: "info" }]);
                tableBody.innerHTML = buildEmptyTableRow(noDataMessage);
            }

        } catch (error) {
            messagesContainer.innerHTML = `<div class="message-banner error">No fue posible comunicarse con el servidor. Intente nuevamente.</div>`;
            tableBody.innerHTML = buildEmptyTableRow(EMPTY_TABLE_MESSAGE);
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        }
    });

    if (exportButton) {
        exportButton.addEventListener("click", async function () {
            if (!hasSearched || inputsChanged) {
                messagesContainer.innerHTML = buildMessageHtml([
                    { text: "Primero debe realizar una búsqueda antes de exportar la información.", tags: "info" }
                ]);
                return;
            }

            if (currentRowsCount === 0) {
                messagesContainer.innerHTML = buildMessageHtml([
                    { text: "No existen registros para exportar.", tags: "info" }
                ]);
                return;
            }

            const exportUrl = exportButton.dataset.exportUrl || "/datos-abiertos/exportar-excel/";
            const formData = new FormData(form);
            formData.set("buscar", "1");
            const params = new URLSearchParams(formData);
            const fullExportUrl = `${exportUrl}?${params.toString()}`;

            const originalBtnHtml = exportButton.innerHTML;
            exportButton.disabled = true;
            exportButton.textContent = "Exportando...";

            try {
                const response = await fetch(fullExportUrl, {
                    method: "GET",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/json",
                    },
                });

                const contentType = response.headers.get("content-type") || "";

                if (contentType.includes("application/json")) {
                    const data = await response.json();
                    if (data.messages && data.messages.length > 0) {
                        messagesContainer.innerHTML = buildMessageHtml(data.messages);
                    }
                    return;
                }

                if (!response.ok) {
                    throw new Error(`Error en el servidor (${response.status})`);
                }

                const blob = await response.blob();
                const disposition = response.headers.get("content-disposition");
                let filename = "F004_GSW_DATO.xlsx";
                if (disposition && disposition.includes("filename=")) {
                    const match = disposition.match(/filename="?([^"]+)"?/);
                    if (match && match[1]) {
                        filename = match[1];
                    }
                }

                const blobUrl = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = blobUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(blobUrl);

            } catch (error) {
                messagesContainer.innerHTML = buildMessageHtml([
                    { text: "Ocurrió un error al intentar exportar la información. Intente nuevamente.", tags: "error" }
                ]);
            } finally {
                exportButton.disabled = false;
                exportButton.innerHTML = originalBtnHtml;
            }
        });
    }
});


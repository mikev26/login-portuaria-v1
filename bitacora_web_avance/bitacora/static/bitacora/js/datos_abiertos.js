document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector(".date-range-form");
    const tableBody = document.querySelector("#report-table-body");
    const messagesContainer = document.querySelector("#report-messages");
    const submitButton = form?.querySelector("button[type=submit]");
    const exportButton = document.querySelector("#btn-exportar-excel");

    if (!form || !tableBody || !submitButton || !exportButton) {
        return;
    }

    const EMPTY_TABLE_MESSAGE = "No hay datos disponibles. Seleccione año y semestre, y presione Buscar.";
    const NO_RESULTS_MESSAGE = "No existen registros.";
    let messagesTimeout;
    let inputsChanged = false;

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[character]);
    }

    function setMessages(messages) {
        if (!messagesContainer) {
            return;
        }

        window.clearTimeout(messagesTimeout);
        messagesContainer.innerHTML = (messages || [])
            .map(message => `
                <div class="message-banner ${escapeHtml(message.tags || "info")}">
                    ${escapeHtml(message.text)}
                </div>
            `)
            .join("");

        if (messagesContainer.childElementCount > 0) {
            messagesTimeout = window.setTimeout(function () {
                messagesContainer.replaceChildren();
            }, 5000);
        }
    }

    function setExportEnabled(enabled) {
        exportButton.disabled = !enabled;
        exportButton.setAttribute("aria-disabled", String(!enabled));
    }

    function buildEmptyTableRow(message) {
        return `
            <tr class="table-placeholder">
                <td colspan="12">${escapeHtml(message)}</td>
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
                    <td>${escapeHtml(row["Registro"])}</td>
                    <td>${escapeHtml(row["CodBuque"])}</td>
                    <td>${escapeHtml(row["Matrícula"] ?? row["Matricula"])}</td>
                    <td>${escapeHtml(row["Buque"])}</td>
                    <td>${escapeHtml(row["Tipo de Nave"] ?? row["TipoNave"] ?? row["Tipo_de_Nave"])}</td>
                    <td>${escapeHtml(row["Arribo"])}</td>
                    <td>${escapeHtml(row["Zarpe"])}</td>
                    <td>${escapeHtml(row["Bandera"])}</td>
                    <td>${escapeHtml(row["TRB"])}</td>
                    <td>${escapeHtml(row["TRN"])}</td>
                    <td>${escapeHtml(row["Agencia"])}</td>
                    <td>${escapeHtml(row["Total Descarga"] ?? row["TotalDescarga"] ?? row["Total_Descarga"])}</td>
                </tr>
            `)
            .join("");
    }

    const initialRows = tableBody.querySelectorAll("tr:not(.table-placeholder)");
    let currentRowsCount = initialRows.length;
    let hasSearched = currentRowsCount > 0;
    setExportEnabled(hasSearched);

    if (messagesContainer?.childElementCount) {
        setMessages(Array.from(messagesContainer.children).map(message => ({
            text: message.textContent.trim(),
            tags: Array.from(message.classList).find(tag => tag !== "message-banner") || "info"
        })));
    }

    const currentUrl = new URL(window.location.href);
    if (currentUrl.searchParams.has("aviso")) {
        currentUrl.searchParams.delete("aviso");
        window.history.replaceState({}, "", currentUrl);
    }

    form.querySelectorAll("[name=anio], [name=semestre]").forEach(function (control) {
        control.addEventListener("change", function () {
            inputsChanged = true;
            setExportEnabled(false);
            setMessages([]);
        });
    });

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        setExportEnabled(false);
        setMessages([]);

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
            const rows = Array.isArray(data.rows) ? data.rows : [];
            tableBody.innerHTML = buildTableRows(rows);
            currentRowsCount = rows.length;
            hasSearched = true;
            inputsChanged = false;
            setMessages(data.messages || []);
            setExportEnabled(currentRowsCount > 0);
        } catch (error) {
            currentRowsCount = 0;
            hasSearched = false;
            inputsChanged = true;
            tableBody.innerHTML = buildEmptyTableRow(EMPTY_TABLE_MESSAGE);
            setMessages([{
                text: "No fue posible comunicarse con el servidor. Intente nuevamente.",
                tags: "error"
            }]);
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        }
    });

    exportButton.addEventListener("click", async function () {
        if (exportButton.disabled || !hasSearched || inputsChanged || currentRowsCount === 0) {
            return;
        }

        const exportUrl = exportButton.dataset.exportUrl || "/datos-abiertos/exportar-excel/";
        const formData = new FormData(form);
        formData.set("buscar", "1");
        const params = new URLSearchParams(formData);
        const fullExportUrl = `${exportUrl}?${params.toString()}`;
        const originalBtnHtml = exportButton.innerHTML;

        setExportEnabled(false);
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
                setMessages(data.messages || []);
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
                if (match?.[1]) {
                    filename = match[1];
                }
            }

            const blobUrl = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = blobUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(blobUrl);
        } catch (error) {
            setMessages([{
                text: "Ocurrió un error al intentar exportar la información. Intente nuevamente.",
                tags: "error"
            }]);
        } finally {
            exportButton.innerHTML = originalBtnHtml;
            setExportEnabled(hasSearched && !inputsChanged && currentRowsCount > 0);
        }
    });
});

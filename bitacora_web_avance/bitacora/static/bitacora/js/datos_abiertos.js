document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector(".date-range-form");
    const tableBody = document.querySelector("#report-table-body");
    const messagesContainer = document.querySelector("#report-messages");
    const anioHeader = document.querySelector("#header-anio");
    const semestreHeader = document.querySelector("#header-semestre");
    const submitButton = form.querySelector("button[type=submit]");

    const EMPTY_TABLE_MESSAGE = "No hay datos disponibles. Seleccione año y semestre, y presione Buscar.";
    const NO_RESULTS_MESSAGE = "No se encontraron datos para el Año y Semestre seleccionados.";

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
});

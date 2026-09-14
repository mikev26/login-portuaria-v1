document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector(".date-range-form");
    const exportButton = document.querySelector("#export-button");
    const exportMessage = document.querySelector("#export-message");

    if (!form || !exportButton) {
        return;
    }

    function setExportEnabled(enabled) {
        exportButton.disabled = !enabled;
        exportButton.setAttribute("aria-disabled", String(!enabled));
    }

    setExportEnabled(exportButton.dataset.hasRows === "true");

    exportButton.addEventListener("click", async function () {
        if (exportButton.disabled) {
            return;
        }

        try {
            const response = await fetch(exportButton.dataset.validateUrl, {
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json"
                }
            });
            const data = await response.json();
            if (data.ok) {
                window.location.href = exportButton.dataset.exportUrl;
            } else if (exportMessage) {
                exportMessage.innerHTML = `<div class="message-banner info">${data.message}</div>`;
            }
        } catch (error) {
            if (exportMessage) {
                exportMessage.innerHTML = "<div class=\"message-banner error\">No fue posible validar la exportación.</div>";
            }
        }
    });

    form.querySelectorAll("input, select").forEach(function (control) {
        control.addEventListener("input", function () {
            setExportEnabled(false);
            if (exportMessage) {
                exportMessage.innerHTML = "";
            }
        });
        control.addEventListener("change", function () {
            setExportEnabled(false);
            if (exportMessage) {
                exportMessage.innerHTML = "";
            }
        });
    });
});

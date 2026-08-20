document.addEventListener("DOMContentLoaded", function () {

    let filtrosMultiples = {
        buques: [],
        tipos_nave: [],
        armadores: [],
        procedencias: [],
        destinos: [],
        estados: []
    };

    let modalSelectId = null;

    const dataLists = {
        buques: JSON.parse(
            document.getElementById("buques-data").textContent
        ),
        tipos_nave: JSON.parse(
            document.getElementById("tipos-nave-data").textContent
        ),
        armadores: JSON.parse(
            document.getElementById("armadores-data").textContent
        ),
        procedencias: JSON.parse(
            document.getElementById("procedencias-data").textContent
        ),
        destinos: JSON.parse(
            document.getElementById("destinos-data").textContent
        ),
        estados: JSON.parse(
            document.getElementById("estados-data").textContent
        )
    };

    function toggleFilter(name, checkbox) {
        const select = document.getElementById("sel_" + name);
        if (!select) {
            return;
        }
        select.disabled = !checkbox.checked;
    }

    const filtros = [
        "buque",
        "tiponave",
        "armador",
        "procedencia",
        "destino",
        "estado"
    ];

    filtros.forEach(function (nombre) {
        const checkbox = document.getElementById("chk_" + nombre);
        if (!checkbox) {
            return;
        }
        checkbox.addEventListener("change", function () {
            toggleFilter(nombre, checkbox);
        });
    });

    window.openModal = function (title, key) {
        const modal = document.getElementById("multiModal");
        const modalTitle = document.getElementById("modalTitle");
        const modalList = document.getElementById("modalList");

        modalTitle.textContent = "Seleccionar " + title;
        modalList.innerHTML = "";

        const selectMap = {
            buques: "sel_buque",
            tipos_nave: "sel_tiponave",
            armadores: "sel_armador",
            procedencias: "sel_procedencia",
            destinos: "sel_destino",
            estados: "sel_estado"
        };

        modalSelectId = selectMap[key];
        const select = document.getElementById(modalSelectId);

        // Sincronizar desde las opciones seleccionadas del select múltiple
        filtrosMultiples[key] = [];
        if (select) {
            const selectedOptions = Array.from(select.selectedOptions);
            selectedOptions.forEach(function (opt) {
                if (opt.value && opt.value !== "" && !filtrosMultiples[key].includes(opt.value)) {
                    filtrosMultiples[key].push(opt.value);
                }
            });
        }

        // Respaldo con inputs ocultos si estuviera vacío
        if (filtrosMultiples[key].length === 0) {
            const form = document.getElementById("formReporteBuque");
            const hiddenInputs = form.querySelectorAll(`input[name="${modalSelectId}_modal"]`);
            hiddenInputs.forEach(function (input) {
                if (input.value && !filtrosMultiples[key].includes(input.value)) {
                    filtrosMultiples[key].push(input.value);
                }
            });
        }

        const items = dataLists[key] || [];

        if (items.length === 0) {
            modalList.innerHTML = `
                <div class="modal-empty">
                    No existen elementos disponibles.
                </div>
            `;
            modal.style.display = "flex";
            return;
        }

        items.forEach(function (item) {
            const div = document.createElement("div");
            div.className = "modal-option";

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.value = item;
            checkbox.id = "modal_" + key + "_" + item.toString().replace(/[^a-zA-Z0-9]/g, "_");

            if (filtrosMultiples[key].includes(item)) {
                checkbox.checked = true;
            }

            const label = document.createElement("label");
            label.htmlFor = checkbox.id;
            label.textContent = item;

            checkbox.addEventListener("change", function () {
                if (checkbox.checked) {
                    if (!filtrosMultiples[key].includes(checkbox.value)) {
                        filtrosMultiples[key].push(checkbox.value);
                    }
                } else {
                    filtrosMultiples[key] = filtrosMultiples[key].filter(function (valor) {
                        return valor !== checkbox.value;
                    });
                }
            });

            div.appendChild(checkbox);
            div.appendChild(label);
            modalList.appendChild(div);
        });

        modal.style.display = "flex";
    };

    window.acceptModal = function () {
        if (!modalSelectId) {
            return;
        }

        const select = document.getElementById(modalSelectId);
        if (!select) {
            return;
        }

        const modalList = document.getElementById("modalList");
        const checked = modalList.querySelectorAll('input[type="checkbox"]:checked');

        const seleccionados = Array.from(checked).map(function (checkbox) {
            return checkbox.value;
        });

        const keyMap = {
            sel_buque: "buques",
            sel_tiponave: "tipos_nave",
            sel_armador: "armadores",
            sel_procedencia: "procedencias",
            sel_destino: "destinos",
            sel_estado: "estados"
        };

        const key = keyMap[modalSelectId];
        filtrosMultiples[key] = seleccionados;

        select.innerHTML = "";

        if (seleccionados.length === 0) {
            const option = document.createElement("option");
            option.value = "";
            option.textContent = "-- Seleccione --";
            select.appendChild(option);
        } else {
            seleccionados.forEach(function (valor) {
                const option = document.createElement("option");
                option.value = valor;
                option.textContent = valor;
                option.selected = true; // Marcar todas como seleccionadas en el select múltiple
                select.appendChild(option);
            });
        }

        select.disabled = false;

        const checkboxFiltro = document.getElementById(modalSelectId.replace("sel_", "chk_"));
        if (checkboxFiltro) {
            checkboxFiltro.checked = seleccionados.length > 0;
        }

        actualizarFiltrosModal();
        closeModal();
    };

    function actualizarFiltrosModal() {
        const form = document.getElementById("formReporteBuque");
        if (!form) {
            return;
        }

        form.querySelectorAll(".filtro-modal-hidden").forEach(function (elemento) {
            elemento.remove();
        });

        const nombreMap = {
            buques: "sel_buque_modal",
            tipos_nave: "sel_tiponave_modal",
            armadores: "sel_armador_modal",
            procedencias: "sel_procedencia_modal",
            destinos: "sel_destino_modal",
            estados: "sel_estado_modal"
        };

        Object.keys(filtrosMultiples).forEach(function (key) {
            const valores = filtrosMultiples[key];
            if (!valores || valores.length === 0) {
                return;
            }

            const nombre = nombreMap[key];

            valores.forEach(function (valor) {
                const input = document.createElement("input");
                input.type = "hidden";
                input.name = nombre;
                input.value = valor;
                input.className = "filtro-modal-hidden";
                form.appendChild(input);
            });
        });
    }

    filtros.forEach(function (nombre) {
        const select = document.getElementById("sel_" + nombre);
        if (!select) {
            return;
        }

        select.addEventListener("change", function () {
            const keyMap = {
                buque: "buques",
                tiponave: "tipos_nave",
                armador: "armadores",
                procedencia: "procedencias",
                destino: "destinos",
                estado: "estados"
            };

            const key = keyMap[nombre];
            filtrosMultiples[key] = [];

            const form = document.getElementById("formReporteBuque");
            const hiddenName = "sel_" + nombre + "_modal";

            form.querySelectorAll(`input[name="${hiddenName}"]`).forEach(function (input) {
                input.remove();
            });
        });
    });

    window.closeModal = function () {
        const modal = document.getElementById("multiModal");
        if (modal) {
            modal.style.display = "none";
        }
    };

    const modalElement = document.getElementById("multiModal");
    if (modalElement) {
        modalElement.addEventListener("click", function (event) {
            if (event.target === modalElement) {
                closeModal();
            }
        });
    }

});
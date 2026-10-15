(function () {
    const buqueActivo = document.getElementById('filtroBuqueActivo');
    const buqueInput = document.getElementById('filtroBuque');
    const abrirBuques = document.getElementById('abrirBuques');
    const modal = document.getElementById('buquesModal');
    const modalBody = document.getElementById('buquesModalBody');
    const modalSearch = document.getElementById('buscarBuqueModal');
    const selectedCount = document.getElementById('buquesSeleccionados');
    const aceptarBuques = document.getElementById('aceptarBuques');
    const dataElement = document.getElementById('ocupacionBuquesData');

    if (!buqueActivo || !modal || !modalBody || !dataElement) return;

    let buques = [];
    let pendingSelection = new Set();
    let selectedBuques = new Set();

    try {
        buques = JSON.parse(dataElement.textContent || '[]')
            .map((item) => String(item.nombre || item.Buque || item.buque || '').trim())
            .filter(Boolean);
    } catch (error) {
        console.error('No fue posible cargar la lista de buques.', error);
    }

    function updateBuqueControls() {
        const enabled = buqueActivo.checked;
        buqueInput.disabled = !enabled;
        abrirBuques.disabled = !enabled;
        if (!enabled) {
            selectedBuques.clear();
            buqueInput.value = '';
        }
    }

    function updateCount() {
        const count = pendingSelection.size;
        selectedCount.textContent = `${count} seleccionado${count === 1 ? '' : 's'}`;
    }

    function renderBuques() {
        const search = modalSearch.value.trim().toLowerCase();
        const visibles = buques.filter((nombre) => nombre.toLowerCase().includes(search));
        modalBody.innerHTML = '';

        if (!visibles.length) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="2" class="ocupacion-empty-state">No hay buques disponibles para mostrar.</td>';
            modalBody.appendChild(row);
            updateCount();
            return;
        }

        visibles.forEach((nombre) => {
            const row = document.createElement('tr');
            const cellCheck = document.createElement('td');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'buque_seleccionado';
            checkbox.value = nombre;
            checkbox.checked = pendingSelection.has(nombre);
            checkbox.setAttribute('aria-label', `Seleccionar ${nombre}`);
            checkbox.addEventListener('change', () => {
                if (checkbox.checked) {
                    pendingSelection.add(nombre);
                } else {
                    pendingSelection.delete(nombre);
                }
                updateCount();
            });
            cellCheck.appendChild(checkbox);

            const cellName = document.createElement('td');
            cellName.textContent = nombre;
            row.append(cellCheck, cellName);
            modalBody.appendChild(row);
        });
        updateCount();
    }

    function openModal() {
        pendingSelection = new Set(selectedBuques);
        modal.hidden = false;
        modalSearch.value = '';
        renderBuques();
        modalSearch.focus();
    }

    function closeModal() {
        modal.hidden = true;
    }

    buqueActivo.addEventListener('change', updateBuqueControls);
    buqueInput.addEventListener('click', openModal);
    abrirBuques.addEventListener('click', openModal);
    modalSearch.addEventListener('input', renderBuques);
    document.querySelectorAll('[data-close-buques-modal]').forEach((button) => button.addEventListener('click', closeModal));

    aceptarBuques.addEventListener('click', () => {
        selectedBuques = new Set(pendingSelection);
        buqueInput.value = buques.filter((nombre) => selectedBuques.has(nombre)).join(', ');
        closeModal();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !modal.hidden) closeModal();
    });

    updateBuqueControls();
})();

(function () {
    const registroActivo = document.getElementById('filtroRegistroActivo');
    const registroInput = document.getElementById('filtroRegistro');
    const abrirRegistros = document.getElementById('abrirRegistros');
    const modal = document.getElementById('registrosModal');
    const modalBody = document.getElementById('registrosModalBody');
    const modalSearch = document.getElementById('buscarRegistroModal');
    const selectedCount = document.getElementById('registrosSeleccionados');
    const aceptarRegistros = document.getElementById('aceptarRegistros');

    if (!registroActivo || !registroInput || !abrirRegistros || !modal || !modalBody) return;

    let registros = null;
    let loadPromise = null;
    let pendingSelection = new Set();
    let selectedRegistros = new Set();

    function updateCount() {
        const count = pendingSelection.size;
        selectedCount.textContent = `${count} seleccionado${count === 1 ? '' : 's'}`;
    }

    function showStatus(message) {
        modalBody.replaceChildren();
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 3;
        cell.className = 'ocupacion-empty-state';
        cell.textContent = message;
        row.appendChild(cell);
        modalBody.appendChild(row);
    }

    async function loadRegistros() {
        if (registros) return registros;
        if (!loadPromise) {
            loadPromise = fetch(modal.dataset.registrosUrl, {
                headers: { Accept: 'application/json' },
                credentials: 'same-origin'
            })
                .then(async (response) => {
                    const payload = await response.json();
                    if (!response.ok) {
                        throw new Error(payload.error || 'No fue posible cargar los registros.');
                    }
                    if (!Array.isArray(payload.registros)) {
                        throw new Error('La respuesta de registros no tiene el formato esperado.');
                    }
                    registros = payload.registros;
                    return registros;
                })
                .catch((error) => {
                    loadPromise = null;
                    throw error;
                });
        }
        return loadPromise;
    }

    function renderRegistros() {
        const search = modalSearch.value.trim().toLocaleLowerCase();
        const visibles = registros
            .map((registro, index) => ({ registro, index }))
            .filter(({ registro }) => {
                const scregistro = String(registro.scregistro ?? '');
                const buque = String(registro.buque ?? '');
                return `${scregistro} ${buque}`.toLocaleLowerCase().includes(search);
            });

        modalBody.replaceChildren();
        if (!visibles.length) {
            showStatus('No hay registros disponibles para mostrar.');
            updateCount();
            return;
        }

        const fragment = document.createDocumentFragment();
        visibles.forEach(({ registro, index }) => {
            const row = document.createElement('tr');
            const checkCell = document.createElement('td');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'registro_seleccionado';
            checkbox.value = String(registro.scregistro ?? '');
            checkbox.checked = pendingSelection.has(index);
            checkbox.setAttribute(
                'aria-label',
                `Seleccionar registro ${checkbox.value} ${String(registro.buque ?? '')}`.trim()
            );
            checkbox.addEventListener('change', () => {
                if (checkbox.checked) {
                    pendingSelection.add(index);
                } else {
                    pendingSelection.delete(index);
                }
                updateCount();
            });
            checkCell.appendChild(checkbox);

            const registroCell = document.createElement('td');
            registroCell.textContent = String(registro.scregistro ?? '');
            const buqueCell = document.createElement('td');
            buqueCell.textContent = String(registro.buque ?? '');
            row.append(checkCell, registroCell, buqueCell);
            fragment.appendChild(row);
        });
        modalBody.appendChild(fragment);
        updateCount();
    }

    async function openModal() {
        pendingSelection = new Set(selectedRegistros);
        modal.hidden = false;
        modalSearch.value = '';
        showStatus('Cargando registros desde 2010; esta consulta puede tardar unos minutos...');
        modalSearch.focus();

        try {
            await loadRegistros();
            if (!modal.hidden) renderRegistros();
        } catch (error) {
            console.error('No fue posible cargar los registros.', error);
            showStatus(error.message || 'No fue posible cargar los registros. Intente nuevamente.');
        }
    }

    function closeModal() {
        modal.hidden = true;
    }

    function updateRegistroControls() {
        const enabled = registroActivo.checked;
        registroInput.disabled = !enabled;
        abrirRegistros.disabled = !enabled;
        if (!enabled) {
            selectedRegistros.clear();
            registroInput.value = '';
            closeModal();
        }
    }

    registroActivo.addEventListener('change', () => {
        updateRegistroControls();
        if (registroActivo.checked) openModal();
    });
    registroInput.addEventListener('click', openModal);
    abrirRegistros.addEventListener('click', openModal);
    modalSearch.addEventListener('input', () => {
        if (registros) renderRegistros();
    });
    modal.querySelectorAll('[data-close-registros-modal]').forEach((button) => {
        button.addEventListener('click', closeModal);
    });

    aceptarRegistros.addEventListener('click', () => {
        selectedRegistros = new Set(pendingSelection);
        registroInput.value = [...selectedRegistros]
            .map((index) => String(registros[index].scregistro ?? ''))
            .join(', ');
        closeModal();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !modal.hidden) closeModal();
    });

    updateRegistroControls();
})();
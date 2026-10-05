(function () {
    const buqueActivo = document.getElementById('filtroBuqueActivo');
    const buqueInput = document.getElementById('filtroBuque');
    const buqueCodigos = document.getElementById('filtroBuqueCodigos');
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
    let singleSelectionMode = false;

    try {
        buques = JSON.parse(dataElement.textContent || '[]').map((item) => ({
            codigo: item.codigo || item.scbuque || item.idbuque || item.nombre || item.Buque || '',
            nombre: item.Buque || item.buque || item.nombre || item.Nombre || '',
        })).filter((item) => item.nombre);
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
            buqueCodigos.value = '';
        }
    }

    function updateCount() {
        const count = pendingSelection.size;
        selectedCount.textContent = `${count} seleccionado${count === 1 ? '' : 's'}`;
    }

    function renderBuques() {
        const search = modalSearch.value.trim().toLowerCase();
        const visibles = buques.filter((item) => item.nombre.toLowerCase().includes(search));
        modalBody.innerHTML = '';

        if (!visibles.length) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="2" class="ocupacion-empty-state">No hay buques disponibles para mostrar.</td>';
            modalBody.appendChild(row);
            updateCount();
            return;
        }

        visibles.forEach((item) => {
            const row = document.createElement('tr');
            const cellCheck = document.createElement('td');
            const checkbox = document.createElement('input');
            checkbox.type = singleSelectionMode ? 'radio' : 'checkbox';
            checkbox.name = singleSelectionMode ? 'buque_unico' : `buque_${item.codigo}`;
            checkbox.value = item.codigo;
            checkbox.checked = pendingSelection.has(item.codigo);
            checkbox.setAttribute('aria-label', `Seleccionar ${item.nombre}`);
            checkbox.addEventListener('change', () => {
                if (singleSelectionMode) {
                    pendingSelection.clear();
                    if (checkbox.checked) pendingSelection.add(item.codigo);
                    renderBuques();
                } else if (checkbox.checked) {
                    pendingSelection.add(item.codigo);
                } else {
                    pendingSelection.delete(item.codigo);
                }
                updateCount();
            });
            cellCheck.appendChild(checkbox);

            const cellName = document.createElement('td');
            cellName.textContent = item.nombre;
            row.append(cellCheck, cellName);
            modalBody.appendChild(row);
        });
        updateCount();
    }

    function openModal(single = false) {
        singleSelectionMode = single;
        pendingSelection = singleSelectionMode
            ? new Set([...selectedBuques].slice(0, 1))
            : new Set(selectedBuques);
        modal.hidden = false;
        modalSearch.value = '';
        renderBuques();
        modalSearch.focus();
    }

    function closeModal() {
        modal.hidden = true;
    }

    buqueActivo.addEventListener('change', updateBuqueControls);
    buqueInput.addEventListener('click', () => openModal(true));
    abrirBuques.addEventListener('click', () => openModal(false));
    modalSearch.addEventListener('input', renderBuques);
    document.querySelectorAll('[data-close-buques-modal]').forEach((button) => button.addEventListener('click', closeModal));

    aceptarBuques.addEventListener('click', () => {
        selectedBuques = new Set(pendingSelection);
        const selected = buques.filter((item) => selectedBuques.has(item.codigo));
        buqueInput.value = selected.map((item) => item.nombre).join(', ');
        buqueCodigos.value = selected.map((item) => item.codigo).join(',');
        closeModal();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !modal.hidden) closeModal();
    });

    updateBuqueControls();
})();
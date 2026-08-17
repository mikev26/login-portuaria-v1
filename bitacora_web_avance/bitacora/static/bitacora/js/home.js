const industrialShips = JSON.parse(
    document.getElementById('industrialShips')?.textContent || '[]'
);

const artisanalShips = JSON.parse(
    document.getElementById('artisanalShips')?.textContent || '[]'
);

function shipLabel(ship) {
    const parts = [ship.scbuque, ship.nombre, ship.matricula].filter(Boolean);
    return parts.join(' — ');
}

/* ===== SPJ_INSERT_BITACORA ===== */

function clearSelectedShip(form) {
    if (!form) return;

    form.querySelector('.selected-idbuque').value = '';
    form.querySelector('.selected-idregistro').value = '';
    form.querySelector('.selected-scregistro').value = '';
}

function syncSelectedShip(shipSelect) {
    const form = shipSelect.closest('.novedad-form');
    if (!form) return;

    const selectedOption = shipSelect.options[shipSelect.selectedIndex];

    if (!selectedOption?.dataset.ship) {
        clearSelectedShip(form);
        updateSaveButton(form);
        return;
    }

    const ship = JSON.parse(selectedOption.dataset.ship);

    form.querySelector('.selected-idbuque').value = ship.idbuque ?? '';
    form.querySelector('.selected-idregistro').value = ship.idregistro ?? '';
    form.querySelector('.selected-scregistro').value = ship.scbuque ?? '';

    updateSaveButton(form);
}

function refreshShipSelect(typeSelect) {
    const shipSelect = document.getElementById(typeSelect.dataset.shipSelect);
    if (!shipSelect) return;

    const help = document.getElementById(shipSelect.id + 'Help');
    const form = typeSelect.closest('.novedad-form');
    const type = typeSelect.value;

    clearSelectedShip(form);
    shipSelect.innerHTML = '';

    let ships = [];

    if (type === 'industrial') {
        ships = industrialShips;
    } else if (type === 'artesanal') {
        ships = artisanalShips;
    } else {
        shipSelect.disabled = true;
        shipSelect.add(new Option('Seleccione primero un tipo de novedad', ''));
        if (help) help.textContent = '';
        updateSaveButton(form);
        return;
    }

    if (!ships.length) {
        shipSelect.disabled = true;
        shipSelect.add(
            new Option('No existen buques activos para esta categoría', '')
        );

        if (help) {
            help.textContent =
                type === 'artesanal'
                    ? 'La consulta de cabotaje devolvió cero registros activos.'
                    : 'La consulta no devolvió registros.';
        }

        updateSaveButton(form);
        return;
    }

    shipSelect.disabled = false;
    shipSelect.add(new Option('-- Seleccione un buque --', ''));

    ships.forEach((ship) => {
        const option = new Option(
            shipLabel(ship),
            String(ship.idregistro ?? '')
        );

        option.dataset.ship = JSON.stringify(ship);
        shipSelect.add(option);
    });

    if (help) {
        help.textContent = `${ships.length} buque(s) disponible(s).`;
    }

    updateSaveButton(form);
}

function updateSaveButton(form) {
    if (!form) return;

    const button = form.querySelector('.save-novelty-button');
    const type = form.querySelector('.novelty-type')?.value || '';
    const idBuque = form.querySelector('.selected-idbuque')?.value || '';
    const idRegistro = form.querySelector('.selected-idregistro')?.value || '';
    const detalle = form.querySelector('.novelty-detail')?.value.trim() || '';

    const valid =
        (type === 'industrial' || type === 'artesanal') &&
        idBuque &&
        idRegistro &&
        detalle;

    if (button) {
        button.disabled = !valid;
    }
}

/* ===== FIN SPJ_INSERT_BITACORA ===== */

function refreshTurn() {
    const select = document.getElementById('turnoSelect');
    if (!select) return;

    const selected = select.options[select.selectedIndex];

    document.getElementById('turnoInicio').value =
        selected.dataset.inicio || '';

    document.getElementById('turnoFin').value =
        selected.dataset.fin || '.NULL.';

    document
        .querySelectorAll('.panel-turno')
        .forEach((panel) => panel.classList.remove('visible'));

    const currentPanel =
        document.getElementById('turnoPanel' + select.value);

    if (currentPanel) {
        currentPanel.classList.add('visible');
    }
}

function refreshClock() {
    const now = new Date();

    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    const hh = String(now.getHours()).padStart(2, '0');
    const min = String(now.getMinutes()).padStart(2, '0');

    document
        .querySelectorAll('.current-date')
        .forEach((input) => {
            input.value = `${yyyy}-${mm}-${dd}`;
        });

    document
        .querySelectorAll('.current-time')
        .forEach((input) => {
            input.value = `${hh}:${min}`;
        });
}

document.addEventListener('DOMContentLoaded', () => {
    const turnSelect = document.getElementById('turnoSelect');

    if (turnSelect) {
        turnSelect.addEventListener('change', refreshTurn);
    }

    document.querySelectorAll('.novelty-type').forEach((select) => {
        select.addEventListener('change', () => refreshShipSelect(select));
        refreshShipSelect(select);
    });

    document.querySelectorAll('.ship-select').forEach((select) => {
        select.addEventListener('change', () => syncSelectedShip(select));
    });

    document.querySelectorAll('.novelty-detail').forEach((textarea) => {
        textarea.addEventListener('input', () => {
            updateSaveButton(
                textarea.closest('.novedad-form')
            );
        });
    });

    refreshTurn();
    refreshClock();
    setInterval(refreshClock, 30000);
});
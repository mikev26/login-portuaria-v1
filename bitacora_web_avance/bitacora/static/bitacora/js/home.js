const industrialShips = JSON.parse(
    document.getElementById('industrialShips').textContent || '[]'
);

const artisanalShips = JSON.parse(
    document.getElementById('artisanalShips').textContent || '[]'
);


function shipLabel(ship) {
    const parts = [
        ship.scbuque,
        ship.nombre,
        ship.matricula
    ].filter(Boolean);

    return parts.join(' — ');
}


function syncSelectedShip(shipSelect) {
    const form = shipSelect.closest('form');

    if (!form) return;

    const idBuqueInput = form.querySelector('.selected-ship-id');

    if (!idBuqueInput) return;

    const selectedOption =
        shipSelect.options[shipSelect.selectedIndex];

    if (!selectedOption || !selectedOption.dataset.ship) {
        idBuqueInput.value = '';
        return;
    }

    const ship = JSON.parse(selectedOption.dataset.ship);

    idBuqueInput.value = ship.idbuque ?? '';
}


function refreshShipSelect(typeSelect) {
    const shipSelect = document.getElementById(
        typeSelect.dataset.shipSelect
    );

    const help = document.getElementById(
        shipSelect.id + 'Help'
    );

    const form = shipSelect.closest('form');

    const idBuqueInput = form
        ? form.querySelector('.selected-ship-id')
        : null;

    const type = typeSelect.value;

    let ships = [];

    if (type === 'industrial') {
        ships = industrialShips;
    }

    if (type === 'artesanal') {
        ships = artisanalShips;
    }

    // Limpiamos selección anterior
    shipSelect.innerHTML = '';

    if (idBuqueInput) {
        idBuqueInput.value = '';
    }


    // Tipo: inicia turno
    if (type === 'inicio') {
        shipSelect.disabled = true;

        shipSelect.add(
            new Option(
                'No aplica para este tipo de novedad',
                ''
            )
        );

        help.textContent = '';

        return;
    }


    // Industrial o artesanal
    shipSelect.disabled = false;


    // No existen buques
    if (!ships.length) {
        shipSelect.disabled = true;

        shipSelect.add(
            new Option(
                'No existen buques activos para esta categoría',
                ''
            )
        );

        help.textContent =
            type === 'artesanal'
                ? 'La consulta de cabotaje devolvió cero registros activos.'
                : 'La consulta no devolvió registros.';

        return;
    }


    // Opción inicial
    shipSelect.add(
        new Option(
            '-- Seleccione un buque --',
            ''
        )
    );


    // Cargar buques
    ships.forEach((ship) => {

        /*
         * El value del select será idregistro.
         * Los demás datos del buque quedan almacenados
         * dentro de data-ship.
         */
        const option = new Option(
            shipLabel(ship),
            String(ship.idregistro ?? '')
        );

        option.dataset.ship = JSON.stringify(ship);

        shipSelect.add(option);
    });


    help.textContent =
        `${ships.length} buque(s) disponible(s).`;
}


function refreshTurn() {
    const select = document.getElementById('turnoSelect');

    if (!select) return;

    const selected =
        select.options[select.selectedIndex];

    document.getElementById('turnoInicio').value =
        selected.dataset.inicio || '';

    document.getElementById('turnoFin').value =
        selected.dataset.fin || '.NULL.';


    document
        .querySelectorAll('.panel-turno')
        .forEach((panel) => {
            panel.classList.remove('visible');
        });


    const currentPanel = document.getElementById(
        'turnoPanel' + select.value
    );

    if (currentPanel) {
        currentPanel.classList.add('visible');
    }
}


function refreshClock() {
    const now = new Date();

    const yyyy = now.getFullYear();

    const mm = String(
        now.getMonth() + 1
    ).padStart(2, '0');

    const dd = String(
        now.getDate()
    ).padStart(2, '0');

    const hh = String(
        now.getHours()
    ).padStart(2, '0');

    const min = String(
        now.getMinutes()
    ).padStart(2, '0');


    document
        .querySelectorAll('.current-date')
        .forEach((input) => {
            input.value =
                `${yyyy}-${mm}-${dd}`;
        });


    document
        .querySelectorAll('.current-time')
        .forEach((input) => {
            input.value =
                `${hh}:${min}`;
        });
}


document.addEventListener(
    'DOMContentLoaded',
    () => {

        const turnSelect =
            document.getElementById('turnoSelect');


        if (turnSelect) {
            turnSelect.addEventListener(
                'change',
                refreshTurn
            );
        }


        // Cambio entre inicio / industrial / artesanal
        document
            .querySelectorAll('.novelty-type')
            .forEach((select) => {

                select.addEventListener(
                    'change',
                    () => refreshShipSelect(select)
                );

                refreshShipSelect(select);
            });


        // Cuando se selecciona un buque,
        // guardar su idbuque en el input hidden.
        document
            .querySelectorAll('.ship-select')
            .forEach((select) => {

                select.addEventListener(
                    'change',
                    () => syncSelectedShip(select)
                );
            });


        refreshTurn();
        refreshClock();

        setInterval(
            refreshClock,
            30000
        );
    }
);
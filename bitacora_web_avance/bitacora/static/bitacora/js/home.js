const industrialShips = JSON.parse(document.getElementById('industrialShips').textContent || '[]');
    const artisanalShips = JSON.parse(document.getElementById('artisanalShips').textContent || '[]');

    function shipLabel(ship) {
        const parts = [ship.scbuque, ship.nombre, ship.matricula].filter(Boolean);
        return parts.join(' — ');
    }

    function refreshShipSelect(typeSelect) {
        const shipSelect = document.getElementById(typeSelect.dataset.shipSelect);
        const help = document.getElementById(shipSelect.id + 'Help');
        const type = typeSelect.value;
        let ships = [];

        if (type === 'industrial') ships = industrialShips;
        if (type === 'artesanal') ships = artisanalShips;

        shipSelect.innerHTML = '';
        if (type === 'inicio') {
            shipSelect.disabled = true;
            shipSelect.add(new Option('No aplica para este tipo de novedad', ''));
            help.textContent = '';
            return;
        }

        shipSelect.disabled = false;
        if (!ships.length) {
            shipSelect.disabled = true;
            shipSelect.add(new Option('No existen buques activos para esta categoría', ''));
            help.textContent = type === 'artesanal'
                ? 'La consulta de cabotaje devolvió cero registros activos.'
                : 'La consulta no devolvió registros.';
            return;
        }

        shipSelect.add(new Option('-- Seleccione un buque --', ''));
        ships.forEach((ship) => {
            const option = new Option(shipLabel(ship), String(ship.idregistro ?? ''));
            option.dataset.ship = JSON.stringify(ship);
            shipSelect.add(option);
        });
        help.textContent = `${ships.length} buque(s) disponible(s).`;
    }

    function refreshTurn() {
        const select = document.getElementById('turnoSelect');
        if (!select) return;
        const selected = select.options[select.selectedIndex];
        document.getElementById('turnoInicio').value = selected.dataset.inicio || '';
        document.getElementById('turnoFin').value = selected.dataset.fin || '.NULL.';
        document.querySelectorAll('.panel-turno').forEach((panel) => panel.classList.remove('visible'));
        const currentPanel = document.getElementById('turnoPanel' + select.value);
        if (currentPanel) currentPanel.classList.add('visible');
    }

    function refreshClock() {
        const now = new Date();
        const yyyy = now.getFullYear();
        const mm = String(now.getMonth() + 1).padStart(2, '0');
        const dd = String(now.getDate()).padStart(2, '0');
        const hh = String(now.getHours()).padStart(2, '0');
        const min = String(now.getMinutes()).padStart(2, '0');
        document.querySelectorAll('.current-date').forEach((input) => input.value = `${yyyy}-${mm}-${dd}`);
        document.querySelectorAll('.current-time').forEach((input) => input.value = `${hh}:${min}`);
    }

    document.addEventListener('DOMContentLoaded', () => {
        const turnSelect = document.getElementById('turnoSelect');
        if (turnSelect) turnSelect.addEventListener('change', refreshTurn);

        document.querySelectorAll('.novelty-type').forEach((select) => {
            select.addEventListener('change', () => refreshShipSelect(select));
            refreshShipSelect(select);
        });

        refreshTurn();
        refreshClock();
        setInterval(refreshClock, 30000);
    });
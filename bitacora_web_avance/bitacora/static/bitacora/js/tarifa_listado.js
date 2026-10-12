document.addEventListener('DOMContentLoaded', () => {
    const rows = document.querySelectorAll('tbody tr:not(.empty-row)');
    
    // Seleccionador por clic para cargar datos en la ventana principal del tarifario
    rows.forEach(row => {
        row.addEventListener('click', () => {
            const rawData = row.dataset.tarifa;
            if (rawData) {
                try {
                    const data = JSON.parse(rawData);
                    if (window.opener && typeof window.opener.loadTarifaData === 'function') {
                        window.opener.loadTarifaData(data);
                        if (typeof window.opener.showToast === 'function') {
                            window.opener.showToast(`Tarifa [${data.codigo}] cargada correctamente.`);
                        }
                        window.close();
                    } else {
                        alert('No se pudo encontrar la ventana principal del Tarifario.');
                    }
                } catch (e) {
                    console.error("Error al procesar los datos de la fila:", e);
                }
            }
        });
    });

    // Búsqueda y filtrado en vivo en la tabla
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.focus();
        
        searchInput.addEventListener('input', function() {
            const term = this.value.trim().toLowerCase();
            let matchCount = 0;

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(term)) {
                    row.style.display = '';
                    matchCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            const emptyRow = document.getElementById('emptyRow');
            if (emptyRow) {
                if (matchCount === 0 && rows.length > 0) {
                    emptyRow.style.display = '';
                } else {
                    emptyRow.style.display = 'none';
                }
            }
        });
    }
});

/**
 * Aplica filtro (activas / todas) recargando la página con los parámetros adecuados
 */
function aplicarFiltro(val) {
    window.location.href = `?filtro=${val}`;
}

/**
 * Exporta el listado actual de tarifas a Excel respetando los filtros y término de búsqueda
 */
function exportToExcel() {
    const urlParams = new URLSearchParams(window.location.search);
    const filtro = urlParams.get('filtro') || 'activas';
    const searchInput = document.getElementById('searchInput');
    const q = searchInput ? searchInput.value.trim() : '';
    window.location.href = `/tarifa/exportar/?filtro=${filtro}&q=${encodeURIComponent(q)}`;
}
const industrialShips = JSON.parse(
    document.getElementById('industrialShips')?.textContent || '[]'
);

const artisanalShips = JSON.parse(
    document.getElementById('artisanalShips')?.textContent || '[]'
);


/* =========================================================
   ETIQUETA DE BUQUE
   ========================================================= */

function shipLabel(ship) {
    const parts = [
        ship.scbuque,
        ship.nombre,
        ship.matricula
    ].filter(Boolean);

    return parts.join(' — ');
}


/* =========================================================
   LIMPIAR BUQUE SELECCIONADO
   ========================================================= */

function clearSelectedShip(form) {
    if (!form) return;

    const idBuque =
        form.querySelector('.selected-idbuque');

    const idRegistro =
        form.querySelector('.selected-idregistro');

    const scRegistro =
        form.querySelector('.selected-scregistro');


    if (idBuque) {
        idBuque.value = '';
    }

    if (idRegistro) {
        idRegistro.value = '';
    }

    if (scRegistro) {
        scRegistro.value = '';
    }
}


/* =========================================================
   SINCRONIZAR BUQUE SELECCIONADO
   ========================================================= */

function syncSelectedShip(shipSelect) {
    const form =
        shipSelect.closest('.novedad-form');

    if (!form) return;


    const selectedOption =
        shipSelect.options[
            shipSelect.selectedIndex
        ];


    if (!selectedOption?.dataset.ship) {
        clearSelectedShip(form);
        updateSaveButton(form);
        return;
    }


    try {

        const ship = JSON.parse(
            selectedOption.dataset.ship
        );


        const idBuque =
            form.querySelector(
                '.selected-idbuque'
            );

        const idRegistro =
            form.querySelector(
                '.selected-idregistro'
            );

        const scRegistro =
            form.querySelector(
                '.selected-scregistro'
            );


        if (idBuque) {
            idBuque.value =
                ship.idbuque ?? '';
        }


        if (idRegistro) {
            idRegistro.value =
                ship.idregistro ?? '';
        }


        if (scRegistro) {
            scRegistro.value =
                ship.scbuque ?? '';
        }


    } catch (error) {

        console.error(
            'No fue posible leer los datos del buque:',
            error
        );

        clearSelectedShip(form);
    }


    updateSaveButton(form);
}


/* =========================================================
   ACTUALIZAR SELECT DE BUQUES
   ========================================================= */

function refreshShipSelect(typeSelect) {

    const shipSelect =
        document.getElementById(
            typeSelect.dataset.shipSelect
        );


    if (!shipSelect) return;


    const help =
        document.getElementById(
            shipSelect.id + 'Help'
        );


    const form =
        typeSelect.closest(
            '.novedad-form'
        );


    const type =
        typeSelect.value;


    clearSelectedShip(form);

    shipSelect.innerHTML = '';

    let ships = [];


    /* =====================================================
       BUQUE INDUSTRIAL
       ===================================================== */

    if (type === 'industrial') {

        ships = industrialShips;


    /* =====================================================
       BUQUE ARTESANAL
       ===================================================== */

    } else if (type === 'artesanal') {

        ships = artisanalShips;


    /* =====================================================
       SIN TIPO SELECCIONADO
       ===================================================== */

    } else if (!type) {

        shipSelect.disabled = true;

        shipSelect.add(
            new Option(
                'Seleccione primero un tipo de novedad',
                ''
            )
        );


        if (help) {
            help.textContent = '';
        }


        updateSaveButton(form);

        return;


    /* =====================================================
       NOVEDADES QUE NO NECESITAN BUQUE

       - Inicia turno
       - Finaliza turno
       - Novedad
       - Reportes
       - Consignas
       ===================================================== */

    } else {

        shipSelect.disabled = true;

        shipSelect.add(
            new Option(
                'No aplica para este tipo de novedad',
                ''
            )
        );


        if (help) {
            help.textContent = '';
        }


        updateSaveButton(form);

        return;
    }


    /* =====================================================
       NO EXISTEN BUQUES ACTIVOS
       ===================================================== */

    if (!ships.length) {

        shipSelect.disabled = true;


        shipSelect.add(
            new Option(
                'No existen buques activos para esta categoría',
                ''
            )
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


    /* =====================================================
       CARGAR BUQUES DISPONIBLES
       ===================================================== */

    shipSelect.disabled = false;


    shipSelect.add(
        new Option(
            '-- Seleccione un buque --',
            ''
        )
    );


    ships.forEach((ship) => {

        const option =
            new Option(
                shipLabel(ship),
                String(
                    ship.idregistro ?? ''
                )
            );


        option.dataset.ship =
            JSON.stringify(ship);


        shipSelect.add(option);
    });


    if (help) {

        help.textContent =
            `${ships.length} buque(s) disponible(s).`;
    }


    updateSaveButton(form);
}


/* =========================================================
   HABILITAR / DESHABILITAR BOTÓN GUARDAR
   ========================================================= */

function updateSaveButton(form) {

    if (!form) return;


    const button =
        form.querySelector(
            '.save-novelty-button'
        );


    const type =
        form.querySelector(
            '.novelty-type'
        )?.value || '';


    const idBuque =
        form.querySelector(
            '.selected-idbuque'
        )?.value || '';


    const idRegistro =
        form.querySelector(
            '.selected-idregistro'
        )?.value || '';


    const detalle =
        form.querySelector(
            '.novelty-detail'
        )?.value.trim() || '';


    const requiresShip =
        type === 'industrial' ||
        type === 'artesanal';


    let valid = false;


    /* =====================================================
       INDUSTRIAL / ARTESANAL

       Requiere:
       - tipo
       - buque
       - registro
       - detalle
       ===================================================== */

    if (requiresShip) {

        valid = Boolean(
            type &&
            idBuque &&
            idRegistro &&
            detalle
        );


    /* =====================================================
       RESTO DE NOVEDADES

       Requiere:
       - tipo
       - detalle
       ===================================================== */

    } else {

        valid = Boolean(
            type &&
            detalle
        );
    }


    if (button) {
        button.disabled = !valid;
    }
}


/* =========================================================
   CAMBIO DE TURNO ACTIVO
   ========================================================= */

function refreshTurn() {

    const select =
        document.getElementById(
            'turnoSelect'
        );


    if (!select) return;


    const selected =
        select.options[
            select.selectedIndex
        ];


    const turnoInicio =
        document.getElementById(
            'turnoInicio'
        );


    const turnoFin =
        document.getElementById(
            'turnoFin'
        );


    if (turnoInicio) {

        turnoInicio.value =
            selected.dataset.inicio || '';
    }


    if (turnoFin) {

        turnoFin.value =
            selected.dataset.fin || '';
    }


    document
        .querySelectorAll(
            '.panel-turno'
        )
        .forEach((panel) => {

            panel.classList.remove(
                'visible'
            );
        });


    const currentPanel =
        document.getElementById(
            'turnoPanel' + select.value
        );


    if (currentPanel) {

        currentPanel.classList.add(
            'visible'
        );
    }
}


/* =========================================================
   RELOJ BASADO EN LA HORA DEL SERVIDOR

   IMPORTANTE:
   NO usamos la hora actual del computador.

   Django coloca inicialmente en los inputs:
   - fecha_servidor
   - hora_servidor

   A partir de esos valores se hace avanzar visualmente
   el reloj utilizando únicamente el tiempo transcurrido.
   ========================================================= */

let servidorFechaBase = null;
let servidorInicioContador = null;


/* =========================================================
   OBTENER FECHA/HORA INICIAL DEL SERVIDOR
   ========================================================= */

function iniciarRelojServidor() {

    const fechaInput =
        document.querySelector(
            '.current-date'
        );


    const horaInput =
        document.querySelector(
            '.current-time'
        );


    if (!fechaInput || !horaInput) {
        return;
    }


    const fecha =
        fechaInput.value;


    const hora =
        horaInput.value;


    if (!fecha || !hora) {
        return;
    }


    const partesFecha =
        fecha.split('-');


    const partesHora =
        hora.split(':');


    if (
        partesFecha.length !== 3 ||
        partesHora.length < 2
    ) {
        return;
    }


    const anio =
        Number(partesFecha[0]);

    const mes =
        Number(partesFecha[1]);

    const dia =
        Number(partesFecha[2]);

    const horas =
        Number(partesHora[0]);

    const minutos =
        Number(partesHora[1]);


    if (
        Number.isNaN(anio) ||
        Number.isNaN(mes) ||
        Number.isNaN(dia) ||
        Number.isNaN(horas) ||
        Number.isNaN(minutos)
    ) {
        return;
    }


    /*
        La fecha base viene de SQL Server.

        No se utiliza:
            new Date()

        como fuente de la hora actual del computador.
    */

    servidorFechaBase =
        new Date(
            anio,
            mes - 1,
            dia,
            horas,
            minutos,
            0,
            0
        );


    /*
        performance.now() mide únicamente
        tiempo transcurrido.

        No depende de que el usuario tenga
        mal configurada la fecha/hora de Windows.
    */

    servidorInicioContador =
        performance.now();


    actualizarRelojServidor();
}


/* =========================================================
   ACTUALIZAR RELOJ VISIBLE
   ========================================================= */

function actualizarRelojServidor() {

    if (
        !servidorFechaBase ||
        servidorInicioContador === null
    ) {
        return;
    }


    const tiempoTranscurrido =
        performance.now() -
        servidorInicioContador;


    const fechaActual =
        new Date(
            servidorFechaBase.getTime() +
            tiempoTranscurrido
        );


    const yyyy =
        fechaActual.getFullYear();


    const mm =
        String(
            fechaActual.getMonth() + 1
        ).padStart(
            2,
            '0'
        );


    const dd =
        String(
            fechaActual.getDate()
        ).padStart(
            2,
            '0'
        );


    const hh =
        String(
            fechaActual.getHours()
        ).padStart(
            2,
            '0'
        );


    const min =
        String(
            fechaActual.getMinutes()
        ).padStart(
            2,
            '0'
        );


    const fechaTexto =
        `${yyyy}-${mm}-${dd}`;


    const horaTexto =
        `${hh}:${min}`;


    document
        .querySelectorAll(
            '.current-date'
        )
        .forEach((input) => {

            input.value =
                fechaTexto;
        });


    document
        .querySelectorAll(
            '.current-time'
        )
        .forEach((input) => {

            input.value =
                horaTexto;
        });
}


/* =========================================================
   INICIALIZACIÓN
   ========================================================= */

document.addEventListener(
    'DOMContentLoaded',
    () => {

        const turnSelect =
            document.getElementById(
                'turnoSelect'
            );


        /* =====================================================
           CAMBIO DE TURNO
           ===================================================== */

        if (turnSelect) {

            turnSelect.addEventListener(
                'change',
                refreshTurn
            );
        }


        /* =====================================================
           TIPOS DE NOVEDAD
           ===================================================== */

        document
            .querySelectorAll(
                '.novelty-type'
            )
            .forEach((select) => {

                select.addEventListener(
                    'change',
                    () => {

                        refreshShipSelect(
                            select
                        );
                    }
                );


                refreshShipSelect(
                    select
                );
            });


        /* =====================================================
           BUQUES
           ===================================================== */

        document
            .querySelectorAll(
                '.ship-select'
            )
            .forEach((select) => {

                select.addEventListener(
                    'change',
                    () => {

                        syncSelectedShip(
                            select
                        );
                    }
                );
            });


        /* =====================================================
           DETALLE
           ===================================================== */

        document
            .querySelectorAll(
                '.novelty-detail'
            )
            .forEach((textarea) => {

                textarea.addEventListener(
                    'input',
                    () => {

                        updateSaveButton(
                            textarea.closest(
                                '.novedad-form'
                            )
                        );
                    }
                );
            });


        /* =====================================================
           ESTADO INICIAL DEL TURNO
           ===================================================== */

        refreshTurn();


        /* =====================================================
           RELOJ DESDE SQL SERVER
           ===================================================== */

        iniciarRelojServidor();


        /*
            La hora REAL que se guarda al registrar
            la novedad vuelve a consultarse en
            SQL Server desde views.py.
        */

        setInterval(
            actualizarRelojServidor,
            1000
        );
    }
);
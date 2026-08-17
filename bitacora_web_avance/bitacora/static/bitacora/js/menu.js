function setMenuState(isOpen) {
        const menu = document.getElementById('sideMenu');
        const overlay = document.getElementById('menuOverlay');
        const button = document.getElementById('menuButton');

        if (!menu || !overlay || !button) return;

        menu.classList.toggle('open', isOpen);
        overlay.classList.toggle('visible', isOpen);
        document.body.classList.toggle('menu-open', isOpen);

        menu.setAttribute('aria-hidden', String(!isOpen));
        overlay.setAttribute('aria-hidden', String(!isOpen));
        button.setAttribute('aria-expanded', String(isOpen));
    }

    document.addEventListener('DOMContentLoaded', () => {
        const menuButton = document.getElementById('menuButton');
        const menuClose = document.getElementById('menuClose');
        const menuOverlay = document.getElementById('menuOverlay');

        if (menuButton) menuButton.addEventListener('click', () => setMenuState(true));
        if (menuClose) menuClose.addEventListener('click', () => setMenuState(false));
        if (menuOverlay) menuOverlay.addEventListener('click', () => setMenuState(false));

        document.querySelectorAll('.menu-link:not(.menu-dropdown-toggle)').forEach((link) => {
            link.addEventListener('click', () => setMenuState(false));
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') setMenuState(false);
        });

        // Manejo del menú desplegable (Tarifario)
        document.querySelectorAll('.menu-dropdown-toggle').forEach((toggle) => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();

                const dropdown = toggle.closest('.menu-dropdown');
                const content = dropdown.querySelector('.menu-dropdown-content');
                const arrow = toggle.querySelector('.dropdown-arrow');
                const isExpanded = dropdown.classList.contains('expanded');

                if (isExpanded) {
                    dropdown.classList.remove('expanded');
                    toggle.setAttribute('aria-expanded', 'false');
                    content.style.maxHeight = '0px';
                    if (arrow) arrow.style.transform = 'rotate(0deg)';
                } else {
                    dropdown.classList.add('expanded');
                    toggle.setAttribute('aria-expanded', 'true');
                    content.style.maxHeight = content.scrollHeight + 'px';
                    if (arrow) arrow.style.transform = 'rotate(180deg)';
                }
            });
        });
    });
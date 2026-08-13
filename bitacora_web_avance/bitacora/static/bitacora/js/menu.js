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

        document.querySelectorAll('.menu-link').forEach((link) => {
            link.addEventListener('click', () => setMenuState(false));
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') setMenuState(false);
        });
    });
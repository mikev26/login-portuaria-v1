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

document.addEventListener('DOMContentLoaded', () => {
    const openButton = document.getElementById('openPasswordModal');
    const overlay = document.getElementById('passwordModalOverlay');
    const closeButton = document.getElementById('closePasswordModal');
    const cancelButton = document.getElementById('cancelPasswordModal');
    const form = document.getElementById('changePasswordForm');
    const newPassword = document.getElementById('newPassword');
    const confirmPassword = document.getElementById('confirmPassword');
    const message = document.getElementById('passwordMessage');
    const saveButton = document.getElementById('savePasswordButton');

    if (
        !openButton ||
        !overlay ||
        !form ||
        !newPassword ||
        !confirmPassword ||
        !message ||
        !saveButton
    ) {
        return;
    }

    function showMessage(text, type) {
        message.textContent = text;
        message.className = 'password-message ' + type;
    }

    function clearMessage() {
        message.textContent = '';
        message.className = 'password-message';
    }

    function openModal() {
        clearMessage();
        form.reset();

        overlay.classList.add('visible');
        overlay.setAttribute('aria-hidden', 'false');

        if (typeof setMenuState === 'function') {
            setMenuState(false);
        }

        window.setTimeout(() => {
            newPassword.focus();
        }, 50);
    }

    function closeModal() {
        overlay.classList.remove('visible');
        overlay.setAttribute('aria-hidden', 'true');
        form.reset();
        clearMessage();
    }

    openButton.addEventListener('click', openModal);

    if (closeButton) {
        closeButton.addEventListener('click', closeModal);
    }

    if (cancelButton) {
        cancelButton.addEventListener('click', closeModal);
    }

    overlay.addEventListener('click', (event) => {
        if (event.target === overlay) {
            closeModal();
        }
    });

    document.querySelectorAll('.password-eye').forEach((button) => {
        button.addEventListener('click', () => {
            const input = document.getElementById(
                button.dataset.target
            );

            if (!input) {
                return;
            }

            const mostrar = input.type === 'password';

            input.type = mostrar ? 'text' : 'password';

            button.setAttribute(
                'aria-label',
                mostrar
                    ? 'Ocultar contraseña'
                    : 'Mostrar contraseña'
            );

            button.setAttribute(
                'title',
                mostrar
                    ? 'Ocultar contraseña'
                    : 'Mostrar contraseña'
            );
        });
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        clearMessage();

        if (!newPassword.value || !confirmPassword.value) {
            showMessage(
                'Debe completar ambas contraseñas.',
                'error'
            );
            return;
        }

        if (newPassword.value !== confirmPassword.value) {
            showMessage(
                'Las contraseñas no coinciden.',
                'error'
            );
            confirmPassword.focus();
            return;
        }

        saveButton.disabled = true;
        saveButton.textContent = 'Cambiando...';

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            let data = {};

            try {
                data = await response.json();
            } catch (error) {
                data = {};
            }

            if (!response.ok || !data.ok) {
                showMessage(
                    data.message ||
                    'No fue posible cambiar la contraseña.',
                    'error'
                );
                return;
            }

            showMessage(
                data.message ||
                'Contraseña actualizada correctamente.',
                'success'
            );

            newPassword.value = '';
            confirmPassword.value = '';

            window.setTimeout(() => {
                closeModal();
            }, 1600);

        } catch (error) {
            showMessage(
                'No fue posible comunicarse con el servidor.',
                'error'
            );
        } finally {
            saveButton.disabled = false;
            saveButton.textContent = 'Cambiar contraseña';
        }
    });

    document.addEventListener('keydown', (event) => {
        if (
            event.key === 'Escape' &&
            overlay.classList.contains('visible')
        ) {
            closeModal();
        }
    });
});


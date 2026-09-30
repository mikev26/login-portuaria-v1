document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.password-eye').forEach(function(button) {
        button.addEventListener('click', function() {
            const input = document.getElementById(button.dataset.target);
            if (input) {
                input.type = input.type === 'password' ? 'text' : 'password';
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', (event) => {
    const button = document.querySelector('button[type="submit"]');
    if (button.disabled) {
        console.log('Button is initially disabled.');
    }

   document.querySelector('form').addEventListener('input', () => {
        button.disabled = false;
    });
});

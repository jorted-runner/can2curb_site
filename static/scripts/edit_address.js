document.addEventListener('DOMContentLoaded', (event) => {
    const button = document.querySelector('button[type="submit"]');
    if (button.disabled) {
        console.log('Button is initially disabled.');
    }

    // Example event listener that might enable the button
    // Comment out or remove such code to ensure the button remains disabled
    document.querySelector('form').addEventListener('input', () => {
        button.disabled = false;
    });
});

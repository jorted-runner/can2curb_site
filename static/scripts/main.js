document.getElementById('admin_home').addEventListener('click', () => {
    window.location.href = '/admin';
});
if (document.getElementById('build_route')) {
    document.getElementById('build_route').addEventListener('click', () => {
        window.location.href = '/build-route';
    });
}

document.getElementById('view_routes').addEventListener('click', () => {
    window.location.href = '/view-routes';
});

document.getElementById('view_customers').addEventListener('click', () => {
    window.location.href = '/view_customers';
});

document.getElementById('active_route').addEventListener('click', () => {
    window.location.href = '/active_route';
});
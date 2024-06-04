document.addEventListener('DOMContentLoaded', function() {
    var scrollPosition = localStorage.getItem('scrollPosition');
    if (scrollPosition) {
        window.scrollTo(0, scrollPosition);
    }

    document.querySelectorAll('.mark_complete').forEach(function(form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            var scrollPos = window.scrollY;
            var url = form.action;
            var formData = new FormData(form);

            fetch(url, {
                method: 'POST',
                body: formData,
            })
            .then(function(response) {
                if (response.ok) {
                    localStorage.setItem('scrollPosition', scrollPos);
                    window.location.reload();
                } else {
                    return response.text().then(function(text) { throw new Error(text); });
                }
            })
            .catch(function(error) {
                console.error('Error:', error);
                alert('An error occurred while processing the form.');
            });
        });
    });
});
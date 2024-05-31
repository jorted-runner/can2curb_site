document.addEventListener("DOMContentLoaded", () => {
    const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;

    const comparer = (idx, asc) => (a, b) => ((v1, v2) =>
        v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
    )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

    const sortTable = (th, asc) => {
        const table = th.closest('table');
        const tbody = table.querySelector('tbody');
        const thIndex = Array.from(th.parentNode.children).indexOf(th);

        // Remove sort indicators from all headers
        document.querySelectorAll('.table_column_head').forEach(header => {
            header.classList.remove('sort-asc', 'sort-desc');
        });

        // Add the appropriate sort indicator to the clicked header
        th.classList.add(asc ? 'sort-asc' : 'sort-desc');

        Array.from(tbody.querySelectorAll('tr'))
            .sort(comparer(thIndex, asc))
            .forEach(tr => tbody.appendChild(tr));
    };

    document.querySelectorAll('.table_column_head').forEach(th => th.addEventListener('click', () => {
        sortTable(th, this.asc = !this.asc);
    }));

    // Sort by the first column in descending order by default
    const firstColumn = document.querySelector('.table_column_head');
    sortTable(firstColumn, false);  // false indicates descending order

    // Select/Deselect all checkboxes
    const selectAllCheckbox = document.getElementById('select_all');
    selectAllCheckbox.addEventListener('change', () => {
        const checkboxes = document.querySelectorAll('.row-select');
        checkboxes.forEach(checkbox => checkbox.checked = selectAllCheckbox.checked);
    });

    // If all checkboxes are selected manually, also select the "select all" checkbox
    const rowCheckboxes = document.querySelectorAll('.row-select');
    rowCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            if (!checkbox.checked) {
                selectAllCheckbox.checked = false;
            } else if (document.querySelectorAll('.row-select:checked').length === rowCheckboxes.length) {
                selectAllCheckbox.checked = true;
            }
        });
    });
});

document.getElementById('address_form').addEventListener('submit', function(event) {
    event.preventDefault();
    var selectedCheckboxes = document.querySelectorAll('.row-select:checked');
    var selectedValues = [];
    selectedCheckboxes.forEach(function(checkbox) {
        selectedValues.push(checkbox.value);
    });
    var formData = new FormData(document.getElementById('address_form'));
    selectedValues.forEach(function(value) {
        formData.append('selected_addresses', value);
    });
    fetch(this.action, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Failed to save route');
        }
    })
    .then(data => {
        if (data.success) {
            window.location.href = '/admin';
        } else {
            throw new Error('Failed to save route');
        }
    })
    .catch(error => {
        console.error('Error saving route:', error);
    });
    
})

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

    document.getElementById('build_route').addEventListener('click', () => {
        window.location.href = '/build-route'; // Replace with the actual URL for "Build Route"
    });

    document.getElementById('view_routes').addEventListener('click', () => {
        window.location.href = '/view-routes'; // Replace with the actual URL for "View Routes"
    });
});

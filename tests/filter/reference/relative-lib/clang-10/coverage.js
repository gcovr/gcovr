function sortGridTable(rowHeaderColumn) {
    const table = rowHeaderColumn.closest('.Box');
    const rows = Array.from(table.querySelectorAll('.Box-row')).slice(1); // Exclude header row

    const columnIndex = Array.from(rowHeaderColumn.parentNode.children).indexOf(rowHeaderColumn);
    const isAscending = rowHeaderColumn.classList.contains('sorted-ascending');

    rows.sort((a, b) => {
        const cellA =
          a.children[columnIndex].hasAttribute('data-sort')
          ? a.children[columnIndex].getAttribute('data-sort')
          : a.children[columnIndex].textContent.trim().toLowerCase();
        const cellB =
          b.children[columnIndex].hasAttribute('data-sort')
          ? b.children[columnIndex].getAttribute('data-sort')
          : b.children[columnIndex].textContent.trim().toLowerCase();

        let comparison = 0;
        if (!isNaN(parseFloat(cellA)) && !isNaN(parseFloat(cellB))) {
            comparison = parseFloat(cellA) - parseFloat(cellB);
        } else {
            comparison = cellA.localeCompare(cellB);
        }

        if( comparison == 0) {
            // Fallback to first column (ascending) for stable sorting
            const firstCellA = a.children[0].textContent.trim().toLowerCase();
            const firstCellB = b.children[0].textContent.trim().toLowerCase();
            return firstCellA.localeCompare(firstCellB);
        }

        return isAscending ? -comparison : comparison;
    });


    // Remove existing rows
    rows.forEach(row => table.removeChild(row));

    // Append sorted rows
    rows.forEach(row => table.appendChild(row));

    // Update header classes
    Array.from(rowHeaderColumn.parentNode.children).forEach(th => {
        th.classList.remove('sorted-ascending', 'sorted-descending');
    });
    rowHeaderColumn.classList.add(isAscending ? 'sorted-descending' : 'sorted-ascending');
}

/*
This file is inspired by coverage.py's js code.
*/

gcovr = {};

gcovr.fileLoaded = function () {
  gcovr.onClick(".button_toggle_coveredLine", gcovr.toggleLines);
  gcovr.onClick(".button_toggle_uncoveredLine", gcovr.toggleLines);
  gcovr.onClick(".button_toggle_partialCoveredLine", gcovr.toggleLines);
  gcovr.onClick(".button_toggle_excludedLine", gcovr.toggleLines);

  document.querySelectorAll("div.sortable").forEach(header => {
    header.addEventListener("click", () => gcovr.sortGridTable(header));
  });
};

gcovr.onClick = function (selector, handler) {
  document.querySelectorAll(selector).forEach(elt => elt.addEventListener("click", handler));
};

gcovr.toggleLines = function (event) {
  const btn = event.target.closest("button");
  const category = btn.value
  const show = !btn.classList.contains("show_" + category);
  gcovr.setLineVisibility(btn, category, show);
};

gcovr.setLineVisibility = function (btn, category, should_show) {
  const cls = "show_" + category;
  if (should_show) {
    btn.closest("main").querySelectorAll("td." + category).forEach(e => e.classList.add(cls));
    btn.classList.add(cls);
  }
  else {
    btn.closest("main").querySelectorAll("td." + category).forEach(e => e.classList.remove(cls));
    btn.classList.remove(cls);
  }
};

gcovr.sortGridTable = function (rowHeaderColumn) {
    const table = rowHeaderColumn.closest('.Box');
    const rows = Array.from(table.querySelectorAll('.Box-row'));

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

        if (comparison == 0) {
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

document.addEventListener("DOMContentLoaded", () => {
  gcovr.fileLoaded();
});

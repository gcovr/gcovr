/*
This file is inspired by coverage.py's js code.
*/

gcovr = {};

gcovr.fileLoaded = function () {
  gcovr.addOnClickHandler(".button_toggle_coveredLine", gcovr.toggleLines);
  gcovr.addOnClickHandler(".button_toggle_uncoveredLine", gcovr.toggleLines);
  gcovr.addOnClickHandler(".button_toggle_partialCoveredLine", gcovr.toggleLines);
  gcovr.addOnClickHandler(".button_toggle_excludedLine", gcovr.toggleLines);

  gcovr.addOnClickHandler("div.sortable", gcovr.sortGridTable);

  gcovr.source_table_body = document.querySelector(".source-table-container > table > tbody")
  gcovr.initScrollMarkers();
  window.addEventListener("resize", () => {
    gcovr.initScrollMarkers();
  });
};

gcovr.addOnClickHandler = function (selector, handler) {
  document.querySelectorAll(selector).forEach(elt => {
    elt.style.cursor = "pointer";
    elt.addEventListener("click", handler)
  });
};


gcovr.toggleLines = function (event) {
  const btn = event.target.closest("button");
  const category = btn.value
  const show = !btn.classList.contains("show_" + category);
  gcovr.setLineVisibility(btn, category, show);
  gcovr.buildScrollMarkers();
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

gcovr.initScrollMarkers = function () {
  if (gcovr.source_table_body === null) {
    const temp_scroll_marker = document.getElementById("scroll_marker")
    if (temp_scroll_marker) {
      temp_scroll_marker.remove();
    }
  }
  else {
    gcovr.lines_len = gcovr.source_table_body.querySelectorAll("tr").length - 1; // exclude header
    gcovr.buildScrollMarkers();
  }
};

gcovr.buildScrollMarkers = function () {
    const temp_scroll_marker = document.getElementById("scroll_marker")
    if (temp_scroll_marker) temp_scroll_marker.remove();
    // Don't build markers if the window has no scroll bar.
    if (document.body.scrollHeight <= window.innerHeight) {
        return;
    }

    const marker_scale = window.innerHeight / document.body.scrollHeight;
    const line_height = Math.max(3, window.innerHeight / gcovr.lines_len);
    const offset_table_start = gcovr.source_table_body.querySelector("td").getBoundingClientRect().top;

    let previous_line = -99, last_mark, last_top;

    const scroll_marker = document.createElement("div");
    scroll_marker.id = "scroll_marker";
    gcovr.source_table_body.querySelectorAll(
      "tr:has(td.show_coveredLine), tr:has(td.show_uncoveredLine), tr:has(td.show_excludedLine), tr:has(td.show_partialCoveredLine)"
    ).forEach(element => {
        const line_top = Math.floor((offset_table_start + element.offsetTop) * marker_scale);
        const line_number = parseInt(element.querySelector("td > a").textContent);

        if (line_number === previous_line + 1) {
            // If this solid missed block just make previous mark higher.
            last_mark.style.height = `${line_top + line_height - last_top}px`;
        }
        else {
            // Add colored line in scroll_marker block.
            last_mark = document.createElement("div");
            last_mark.id = `m${line_number}`;
            last_mark.classList.add("marker");
            last_mark.style.height = `${line_height}px`;
            last_mark.style.top = `${line_top}px`;
            scroll_marker.append(last_mark);
            last_top = line_top;
        }

        previous_line = line_number;
    });

    // Append last to prevent layout calculation
    document.body.append(scroll_marker);
};

gcovr.sortGridTable = function (event) {
  const rowHeaderColumn = event.target.closest('div.sortable');
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

gcovr.toggle_lines = function (event) {
    const btn = event.target.closest("button");
    const category = btn.value
    const show = !btn.classList.contains("show_" + category);
    coverage.set_line_visibilty(category, show);
    coverage.build_scroll_markers();
    coverage.filters[category] = show;
    try {
        localStorage.setItem(coverage.LINE_FILTERS_STORAGE, JSON.stringify(coverage.filters));
    } catch(err) {}
};

gcovr.set_line_visibilty = function (category, should_show) {
    const cls = "show_" + category;
    const btn = document.querySelector(".button_toggle_" + category);
    if (btn) {
        if (should_show) {
            document.querySelectorAll("#source ." + category).forEach(e => e.classList.add(cls));
            btn.classList.add(cls);
        }
        else {
            document.querySelectorAll("#source ." + category).forEach(e => e.classList.remove(cls));
            btn.classList.remove(cls);
        }
    }
};

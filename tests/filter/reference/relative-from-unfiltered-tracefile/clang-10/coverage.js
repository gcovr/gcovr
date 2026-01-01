/*
This file is inspired by coverage.py's js code.
*/

gcovr = {};

gcovr.file_loaded = function () {
  gcovr.on_click(".button_toggle_coveredLine", gcovr.toggle_lines);
  gcovr.on_click(".button_toggle_uncoveredLine", gcovr.toggle_lines);
  gcovr.on_click(".button_toggle_partialCoveredLine", gcovr.toggle_lines);
  gcovr.on_click(".button_toggle_excludedLine", gcovr.toggle_lines);
};

gcovr.on_click = function (selector, handler) {
  document.querySelectorAll(selector).forEach(elt => elt.addEventListener("click", handler));
};

gcovr.toggle_lines = function (event) {
  const btn = event.target.closest("button");
  const category = btn.value
  const show = !btn.classList.contains("show_" + category);
  gcovr.set_line_visibility(btn, category, show);
};

gcovr.set_line_visibility = function (btn, category, should_show) {
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

document.addEventListener("DOMContentLoaded", () => {
  gcovr.file_loaded();
});

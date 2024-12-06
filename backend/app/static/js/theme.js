document.addEventListener("DOMContentLoaded", function () {
  let theme = document.documentElement.getAttribute("data-theme") || "light";

  if (theme === "dark") {
    document.querySelector("svg.icon-theme-toggle").classList.add("moon");
  }

  window.switchTheme = function () {
    theme = theme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", theme);
    document.cookie = `theme=${theme}`;
    updateButton();
    htmx.trigger("#packages-graph", "dataRefresh");
  };

  window.updateButton = function () {
    const button = document.querySelector("[aria-label]");
    button.setAttribute(
      "aria-label",
      theme === "dark" ? "Turn off dark mode" : "Turn on dark mode"
    );
    const svg = button.querySelector("svg");
    svg.classList.toggle("moon", theme === "dark");
  };
});

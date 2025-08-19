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
    const themeButton = document.querySelector("a[onclick*='switchTheme']");
    if (themeButton) {
      themeButton.setAttribute(
        "aria-label",
        theme === "dark" ? "Turn off dark mode" : "Turn on dark mode"
      );
      const themeSvg = themeButton.querySelector("svg.icon-theme-toggle");
      if (themeSvg) {
        themeSvg.classList.toggle("moon", theme === "dark");
      }
    }
  };
});

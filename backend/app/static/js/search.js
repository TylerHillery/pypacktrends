function submitPackageSearchForm(packageName) {
  document.getElementById("package-search-input").value = packageName;
  htmx.trigger("#package-search-form", "submit");
  htmx.trigger("#package-search-container", "search");
}

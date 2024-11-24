drop index if exists idx_package_name;
drop index if exists idx_package_downloaded_date;
drop table if exists pypi_package_downloads_per_day;

drop index if exists idx_package_uploaded_at;
drop table if exists pypi_packages;

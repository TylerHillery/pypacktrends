pragma journal_mode = wal;
pragma synchronous = normal;

create table pypi_package_downloads_per_day (
    package_name            text    not null,
    package_downloaded_date text    not null,
    downloads               integer not null,
    primary key (package_name, package_downloaded_date)
) strict;

create index idx_package_name
on pypi_package_downloads_per_day (package_name);

create index idx_package_downloaded_date
on pypi_package_downloads_per_day (package_downloaded_date);

create table pypi_packages (
    package_name            text not null primary key,
    latest_package_version  text not null,
    package_summary         text,
    package_home_page       text,
    package_download_url    text,
    package_uploaded_at     text not null
) strict;

create index idx_package_uploaded_at
on pypi_packages (package_uploaded_at);

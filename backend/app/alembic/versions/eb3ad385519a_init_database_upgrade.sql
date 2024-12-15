pragma journal_mode = wal;

create table pypi_package_downloads_weekly_metrics (
    package_name                   text    not null,
    package_downloaded_week        text    not null,
    downloads                      integer not null,
    cumulative_downloads           integer not null,
    first_distribution_week        text    not null,
    weeks_since_first_distribution integer not null,
    synced_at                      text    not null,
    primary key (package_name, package_downloaded_week)
);

create table pypi_packages (
    package_name           text not null primary key,
    latest_package_version text not null,
    package_summary        text,
    package_home_page      text,
    package_download_url   text,
    package_uploaded_at    text not null,
    synced_at              text not null
);

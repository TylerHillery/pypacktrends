with

pypi_package_downloads_per_week as (
    select
        package_name,
        package_downloaded_week,
        downloads,
        sum(downloads) over(partition by package_name order by package_downloaded_week) as cumulative_downloads,
        min(package_downloaded_week) over() as first_pypi_downloaded_week
    from
        {{ ref('pypi_package_downloads_per_week') }}
),

pypi_package_first_distribution_week as (
    select
        package_name,
        date_trunc(date(first_package_uploaded_at), week(monday)) as first_distribution_week,
    from
        {{ ref('pypi_packages') }}
),

weeks_since_first_distribution as (
    select
        downloads.package_name,
        downloads.package_downloaded_week,
        downloads.downloads,
        downloads.cumulative_downloads,
        -- pypi download stats only go back so far so if the first distribution
        -- is before the min week from all packages in PyPI we set it to that first week
        greatest(packages.first_distribution_week, downloads.first_pypi_downloaded_week) as first_distribution_week,
        date_diff(
            downloads.package_downloaded_week,
            greatest(packages.first_distribution_week, downloads.first_pypi_downloaded_week),
            week
        ) + 1 as weeks_since_first_distribution
    from
        pypi_package_downloads_per_week as downloads
        inner join pypi_package_first_distribution_week as packages
            on packages.package_name = downloads.package_name
)

select * from weeks_since_first_distribution

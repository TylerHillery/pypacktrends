with

pypi_package_downloads_per_week as (
    select
        package_name,
        package_downloaded_week,
        downloads,
        sum(downloads) over (
            partition by package_name
            order by package_downloaded_week
        )                                    as cumulative_downloads,
        min(package_downloaded_week) over () as first_pypi_downloaded_week,
        min(package_downloaded_week) over (
            partition by package_name
        )                                    as first_package_downloaded_week
    from
        {{ ref('pypi_package_downloads_per_week') }}
),

pypi_package_first_distribution_week as (
    select
        package_name,
        date_trunc(date(first_package_uploaded_at), week (monday)) as first_distribution_week
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
        -- but sometimes the downloads is there before the min distribution week
        -- which theoritcally should not be possible because how can you download
        -- something before the first distribution but nonethless we need to take the
        -- least of the two
        least(
            greatest(packages.first_distribution_week, downloads.first_pypi_downloaded_week),
            downloads.first_package_downloaded_week
        ) as first_distribution_week
    from
        pypi_package_downloads_per_week as downloads
    inner join pypi_package_first_distribution_week as packages
        on downloads.package_name = packages.package_name
)

select
    *,
    date_diff(
        package_downloaded_week,
        first_distribution_week,
        week
    ) + 1 as weeks_since_first_distribution
from
    weeks_since_first_distribution

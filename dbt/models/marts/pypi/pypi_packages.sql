{{
  config(
    materialized = "table",
    cluster_by = "package_name",
    partition_by = {
      "field": "package_uploaded_at",
      "data_type": "date",
      "granularity": "month"
    }
  )
}}

with
package_distributions_ranked as (
    select
        package_name,
        package_version,
        package_summary,
        package_home_page,
        package_download_url,
        timestamp_trunc(package_uploaded_at, second) as package_uploaded_at,
        row_number() over (partition by package_name order by package_uploaded_at asc) as package_uploaded_at_asc_rank,
        row_number() over (partition by package_name order by package_uploaded_at desc) as package_uploaded_at_desc_rank
    from
        {{ ref('stg_bq_public_data_pypi__distribution_metadata') }}
),

last_package_distributions as (
    select
        package_name,
        package_version as latest_package_version,
        package_summary,
        package_home_page, 
        package_download_url,
        package_uploaded_at,
    from
        package_distributions_ranked
    where
        package_uploaded_at_desc_rank = 1
),

first_package_distributions as (
    select
        package_name,
        package_uploaded_at as first_package_uploaded_at
    from
        package_distributions_ranked
    where
        package_uploaded_at_asc_rank = 1
),

final as ( 
    select
        package_name,
        latest_package_version,
        package_summary,
        package_home_page, 
        package_download_url,
        package_uploaded_at,
        first_package_uploaded_at
    from
        last_package_distributions
        inner join first_package_distributions using(package_name)
)

select * from final


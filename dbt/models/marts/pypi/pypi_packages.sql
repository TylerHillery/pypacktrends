{{
  config(
    materialized = "table",
    cluster_by = "package_name",
    labels = {'dbt_model': 'pypi_packages'}
  )
}}

with

latest_package_distributions as (
    select
        package_name,
        package_version as latest_package_version,
        package_summary,
        package_home_page,
        package_download_url,
        package_uploaded_at,
        package_uploaded_date
    from
        {{ ref('stg_bq_public_data_pypi__distribution_metadata') }}
    qualify
        row_number() over (
            partition by
                package_name
            order by
                package_uploaded_at desc
        ) = 1
)

select * from latest_package_distributions

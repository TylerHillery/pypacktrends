{% set partitions_to_replace = get_partitions_to_replace() %}

{{
  config(
    materialized = "incremental",
    incremental_strategy = 'insert_overwrite',
    on_schema_change = 'append_new_columns',
    full_refresh = false,
    cluster_by = "package_name",
    partitions = partitions_to_replace,
    partition_by = {
      "field": "package_downloaded_date",
      "data_type": "date",
      "granularity": "day"
    }
  )
}}

with

daily_downloads as (
    select
        package_name,
        date(package_downloaded_at) as package_downloaded_date,
        count(*)                    as downloads
    from
        {{ ref('stg_bq_public_data_pypi__file_downloads') }}
    where
        date(package_downloaded_at) in ({{ partitions_to_replace | join(',') }})
    group by
        1, 2
)

select * from daily_downloads

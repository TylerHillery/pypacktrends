{% set partitions_to_replace = get_date_range_bounds() %}

{% set start_date = partitions_to_replace[0] %}
{% set end_date = partitions_to_replace[1] %}

{% set partitions_to_replace = dates_in_range(
    start_date_str=start_date,
    end_date_str=end_date,
    in_fmt="'%Y-%m-%d'",
    out_fmt="'%Y-%m-%d'"
) %}

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
        date(package_downloaded_at) between {{ start_date }} and {{ end_date }}
    group by
        1, 2
)

select * from daily_downloads
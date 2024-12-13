{% set partitions_to_replace = get_date_range_bounds() %}

{% set start_date = partitions_to_replace[0] %}
{% set end_date = partitions_to_replace[1] %}

{% set partitions_to_replace = weeks_in_range(
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
      "field": "package_downloaded_week",
      "data_type": "date",
      "granularity": "day"
    }
  )
}}

with

weekly_downloads as (
    select
        package_name,
        date_trunc(date(package_downloaded_at), week (monday)) as package_downloaded_week,
        count(*)                                               as downloads
    from
        {{ ref('stg_bq_public_data_pypi__file_downloads') }}
    where
        date(package_downloaded_at) between date_trunc(
            {{ start_date }}, week (monday)
        ) and date_trunc(
            {{ end_date }}, week (monday)
        )
    group by
        1, 2
)

select * from weekly_downloads

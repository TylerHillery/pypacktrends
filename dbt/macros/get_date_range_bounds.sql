{% macro get_date_range_bounds() %}
    {% set one_day_ago = (run_started_at - modules.datetime.timedelta(days=1)).strftime("%Y-%m-%d") %}
    {% set start_date = var('start_date', one_day_ago) | string %}
    {% set end_date = var('end_date', one_day_ago) | string %}
    {% do return(["'" ~ start_date ~ "'", "'" ~ end_date ~ "'"]) %}
{% endmacro %}

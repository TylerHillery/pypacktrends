{% macro get_partitions_to_replace() %}
    {% set one_day_ago = (run_started_at - modules.datetime.timedelta(days=1)).strftime("%Y-%m-%d") %}
    {% set start_date = var('start_date', one_day_ago) | string %}
    {% set end_date = var('end_date', one_day_ago) | string %}
    {% do return(dates_in_range(start_date_str=start_date, end_date_str=end_date, in_fmt="%Y-%m-%d", out_fmt="'%Y-%m-%d'")) %}
{% endmacro %}

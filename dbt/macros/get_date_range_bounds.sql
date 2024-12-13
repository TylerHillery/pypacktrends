{% macro get_date_range_bounds() %}
    {% set run_started_week = run_started_at - modules.datetime.timedelta(days=run_started_at.weekday()) %}
    {% set one_week_ago = (run_started_week - modules.datetime.timedelta(weeks=1)).strftime("%Y-%m-%d") %}

    {% set start_date = var('start_date', one_week_ago) | string %}
    {% set end_date = var('end_date', one_week_ago) | string %}

    {% set start_datetime = modules.datetime.datetime.strptime(start_date, "%Y-%m-%d") %}
    {% set end_datetime = modules.datetime.datetime.strptime(end_date, "%Y-%m-%d") %}

    {% set start_week = (start_datetime - modules.datetime.timedelta(days=start_datetime.weekday())).strftime("%Y-%m-%d") %}
    {% set end_week = (end_datetime - modules.datetime.timedelta(days=end_datetime.weekday())).strftime("%Y-%m-%d") %}

    {% do return(["'" ~ start_week ~ "'", "'" ~ end_week ~ "'"]) %}
{% endmacro %}

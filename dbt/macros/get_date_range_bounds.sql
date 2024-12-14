{% macro get_date_range_bounds() %}
    {% set run_started_week = run_started_at - modules.datetime.timedelta(days=run_started_at.weekday()) %}
    {% set run_started_week_str =  run_started_week.strftime("%Y-%m-%d") %}

    {% set one_week_ago = (run_started_week - modules.datetime.timedelta(weeks=1)).strftime("%Y-%m-%d") %}

    {% set start_date = var('start_date', one_week_ago) | string %}
    {% set end_date = var('end_date', run_started_week_str) | string %}

    {% set start_datetime = modules.datetime.datetime.strptime(start_date, "%Y-%m-%d") %}
    {% set end_datetime = modules.datetime.datetime.strptime(end_date, "%Y-%m-%d") %}

    {% set start_week = start_datetime - modules.datetime.timedelta(days=start_datetime.weekday()) %}
    {% set end_week = end_datetime - modules.datetime.timedelta(days=end_datetime.weekday()) %}

    {% if start_week >= end_week %}
        {% do exceptions.raise_compiler_error("start_date week (" ~ start_week.strftime("%Y-%m-%d") ~ ") must be before end_date week (" ~ end_week.strftime("%Y-%m-%d") ~ ")") %}
    {% endif %}

    {% set start_week_str = start_week.strftime("%Y-%m-%d") %}
    {% set end_week_str = end_week.strftime("%Y-%m-%d") %}

    {% if end_week_str > run_started_week_str %}
        {% do exceptions.raise_compiler_error("end_week cannot be greater than the start of the current week (" ~ run_started_week_str ~ ")") %}
    {% endif %}

    {% do return(["'" ~ start_week_str ~ "'", "'" ~ end_week_str ~ "'"]) %}
{% endmacro %}

{% macro weeks_in_range(start_date_str, end_date_str=none, in_fmt="%Y%m%d", out_fmt="%Y%m%d") %}
    {% set end_date_str = start_date_str if end_date_str is none else end_date_str %}

    {% set start_date = convert_datetime(start_date_str, in_fmt) %}
    {% set end_date = convert_datetime(end_date_str, in_fmt) %}

    {% set start_week = start_date - modules.datetime.timedelta(days=start_date.weekday()) %}
    {% set end_week = end_date - modules.datetime.timedelta(days=end_date.weekday()) %}

    {% set day_count = (end_week - start_week).days %}
    {% set week_count = day_count // 7 %}

    {% if week_count < 0 %}
        {% set msg -%}
            Partiton start date is after the end date ({{ start_date }}, {{ end_date }})
        {%- endset %}

        {{ exceptions.raise_compiler_error(msg, model) }}
    {% endif %}

    {% set date_list = [] %}
    {% for i in range(0, week_count + 1) %}
        {% set the_date = (modules.datetime.timedelta(weeks=i) + start_week) %}
        {% if not out_fmt %}
            {% set _ = date_list.append(the_date) %}
        {% else %}
            {% set _ = date_list.append(the_date.strftime(out_fmt)) %}
        {% endif %}
    {% endfor %}

    {{ return(date_list) }}
{% endmacro %}

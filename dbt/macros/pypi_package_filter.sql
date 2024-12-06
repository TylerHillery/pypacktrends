
{% macro pypi_package_filter(column_name) -%}
    {% set package_list = [
        'dask',
        'datafusion',
        'duckdb',
        'getdaft',
        'ibis-framework',
        'pandas',
        'polars',
        'pyspark'
    ] %}

    {%- if target.name != 'prod' -%}
        {{ column_name }} in ('{{ package_list | join("', '") }}')
    {%- endif -%}

{% endmacro %}

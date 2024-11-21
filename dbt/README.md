# PyPack Trends - dbt

## Requirements
* [uv](https://docs.astral.sh/uv/) for Python package and environment management.
* [gcloud cli](https://cloud.google.com/sdk/docs/install) for BigQuery access

## Getting Started
- uv run doesn't work the best with dbt cli so it's best to activate the venv first
    - `uv sync`
    - `.venv/bin/activate`
- Run the `./scripts/setup_dev_env.sh` command to ensure your `BIGQUERY_USER` env var is set and you have access to the production dbt `manifest.json` file so you can run commans such as `clone` and `--defer --state`.

## Overview
This project adheres to the [dbt best practices](https://docs.getdbt.com/best-practices) and closely follows the [how we structure our dbt projects](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview)

- **Staging** — creating our atoms, our initial modular building blocks, from source data
- **Intermediate** — stacking layers of logic with clear and specific purposes to prepare our staging models to join into the entities we want
- **Marts** — bringing together our modular pieces into a wide, rich vision of the entities our organization cares about

## Helpful Commands

### Adding a New Source
```
dbt run-operation generate_source --args '{"schema_name": "pypi", "database_name": "bigquery-public-data", "generate_columns": "true"}'
dbt run-operation generate_base_model --args '{"source_name": "pypi", "table_name": "distribution_metadata"}'
dbt run-operation generate_model_yaml --args '{"model_names": ["stg_bq_public_data__pypi_distribution_metadata"]}'
```

### Backfill Incremental Models
Any incremental models should use the [insert overwrite method with static partitions](https://docs.getdbt.com/reference/resource-configs/bigquery-configs#static-partitions). This is the most cost effective way to run incremental dbt models in BigQuery.

There is a handy `get_partitions_to_replace` function that will return a list of dates to replace. By default, it uses the prior day but it can be overridden by passing in `--vars`
```
dbt compile -s pypi_package_downloads_per_day --vars '{"start_date": 2024-11-01, "end_date": 2024-11-08}'
```
This project never allows full refreshes, and instead if there is any backfilling that needs to be done, this can be performed manually by passing in the time period that needs backfilling and using the prod dbt target.

## Resources:
- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [chat](https://community.getdbt.com/) on Slack for live discussions and support
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices

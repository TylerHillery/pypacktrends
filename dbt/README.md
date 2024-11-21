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

## Resources:
- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [chat](https://community.getdbt.com/) on Slack for live discussions and support
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices

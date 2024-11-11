# PyPack Trends - Infra

## Requirements

* [Pulumi](https://www.pulumi.com/docs/iac/download-install/)
* [Pulumi ESC](https://www.pulumi.com/docs/esc/download-install/)
* [uv](https://docs.astral.sh/uv/) for Python package and environment management.

## General Workflow

There shouldn't be too many pulumi commands that will need be ran locally with the CI/CD pipeline that is place but here are a few that could be helpful

`pulumi preview` to see what impacts you might have on resources
`pulumi stack output droplet:ipv4` to get pulumi stack outputs
`esc env open pypacktrends/prod` to show decrypted secrets

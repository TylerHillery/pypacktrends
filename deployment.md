# PyPack Trends- Deployment

This project is deployed to a Digital Ocean droplet.

Caddy is used as a reverse proxy handling communication to the outside world and HTTPS certificates.

Currently the project has 3 github actions:
1. Test: runs pre-commit hooks and tests on PRs and commits to main
2. CI: runs pulumi preview on PRs and provides adds the summary as a comment on the PR
3. CD: runs pulumi up to deploy any changes to production server

## Setting up Secrets

For pulumi to work your pulumi ESC environment needs to be configured. These are the following variables that need to be set.

```bash
# create a new pulumi ESC environment
pulumi config env init --env pypacktrends/prod

# cloudflare token
# Access
#   Email Routing Rules:Edit
#   Zone:Read
#   DNS:Edit
# used by pulumi to configure a records and email routing
pulumi env set pypacktrends/prod --secret  pulumiConfig.cloudflare:apiToken TOKEN

# digitalocean token
# Access
#   account: read
#   droplet: create, read, delete
#   project: create, read, delete
#   ssh_key: create, read, delete
# used by pulumi to be able to create SSH key and provision droplet
pulumi env set pypacktrends/prod --secret  pulumiConfig.digitalocean:token TOKEN

# github token
# Access
#  repo
#  write:discussion
#  write:packages
# used by pulumi to publish images to ghcr.io and to be able to add comments on PRs
# NOTE: needs to added as a github action secret as well called GH_TOKEN
pulumi env set pypacktrends/prod --secret  pulumiConfig.github:token TOKEN

# pulumi:token
# used by GitHub Actions to be able to run pulumi commands
# NOTE: needs to added as a github action secret as well called PULUMI_TOKEN
pulumi env set pypacktrends/prod --secret  pulumiConfig.pulumi:token TOKEN

# tailscale:auth-key
# tags: prod
# used in cloud init script to add the droplet to my tailnet
pulumi env set pypacktrends/prod --secret  pulumiConfig.tailscale:auth-key TOKEN

# tailscale:oauth-client-id
# Access
#   all ( wasn't sure what scopes to give, not ideal )
# NOTE: needs to added as a github action secret as well called TS_OAUTH_CLIENT_ID
pulumi env set pypacktrends/prod --secret  pulumiConfig.tailscale:oauth-client-id TOKEN

# tailscale:oauth-client-secret
#   all ( wasn't sure what scopes to give, not ideal )
# NOTE: needs to added as a github action secret as well called TS_OAUTH_CLIENT_SECRET
pulumi env set pypacktrends/prod --secret  pulumiConfig.tailscale:oauth-client-secret TOKEN
```

## Configs
All other configs are stored in `./infra/configs.py` it will first check for any env vars that are set in whatever pulumi stack you are currently using. If nothing it set it will the default set after the `or`

The docker-compose.yml also relies on a couple of env vars as well. If you don't provide any it will use the defaults provided. So if you change any of these configs make sure to also update them in the docker-compose yml or pass in the env var when you run docker compose
- `BACKEND_DOCKER_IMAGE_URL`
- `BACKEND_TAG`
- `DOMAIN`
- `BACKEND_CONTAINER_PORT`

## CI GitHub Action
pulumi preview is ran to see what changes will occur if this PR is merged. A summary of the of changes gets added a comment on PR

## CD GitHub Action
pulumi up is ran to deploy any changes that are detected. The most common one will be when the digest of the backer docker image is change it will trigger the remote command to ssh into the VPS and run the following commands.

Make sure to add this to your tailscale ACL so it can access prod nodes:
```
{
    "action": "accept",
    "src":    ["tag:cicd"],
    "dst":    ["tag:prod"],
    "users":  ["github"],
}
```

```
cd {settings.VPS_PROJECT_PATH}
git pull
./scripts/update_service.sh {settings.CONTAINER_REGISTRY_PREFIX} {settings.BACKEND_SERVICE_NAME}
```

Update service script does the following:
- Pulls the latest image
- Gets the dangling image id for specified service
- Gets the container name attached to the dangling image
- Scales up the service to two containers, keeping the current one and adding a new one which will use the new image
- Gets the name of the new container
- Updates the Caddy container variable specific for the service and reloads the caddy file
- Removes the old container
- Removes the old image

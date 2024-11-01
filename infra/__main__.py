import pulumi
import pulumi_digitalocean as digitalocean
import pulumi_docker as docker
from components import DockerImageComponent
from utils import create_docker_resource, get_cloud_init_script

config = pulumi.Config()
BACKEND_PATH = config.get("backend-path") or "../backend"
BACKEND_PORT = config.get_int("backend-port") or 8000
BACKEND_SERVICE_NAME = config.get("backend-service-name") or "backend"
CADDY_PATH = config.get("caddy-path") or "../caddy"
CADDY_SERVICE_NAME = config.get("caddy-service-name") or "caddy"
DIGITALOCEAN_SSH_KEY_ID = config.get_secret_int("digitalocean-ssh-key-id")
DOMAIN = config.get("domain") or "localhost"
GITHUB_USERNAME = config.get("github-username") or "tylerhillery"
GHCR_TOKEN = config.get_secret("ghcr-token")
PROTOCOL = config.get("protocol") or "http"
PULUMI_ACCESS_TOKEN = config.get_secret("pulumi-access-token")
STACK_NAME = pulumi.get_stack()
TAILSCALE_AUTH_KEY = config.get_secret("tailscale-auth-key")

caddy_image = DockerImageComponent(
    stack_name=STACK_NAME,
    service_name=CADDY_SERVICE_NAME,
    context=CADDY_PATH,
    github_username=GITHUB_USERNAME,
    ghcr_token=GHCR_TOKEN,
)

pulumi.export(f"{CADDY_SERVICE_NAME}-image-identifier", caddy_image.image_identifier)

backend_image = DockerImageComponent(
    stack_name=STACK_NAME,
    service_name=BACKEND_SERVICE_NAME,
    context=BACKEND_PATH,
    github_username=GITHUB_USERNAME,
    ghcr_token=GHCR_TOKEN,
)

pulumi.export(
    f"{BACKEND_SERVICE_NAME}-image-identifier", backend_image.image_identifier
)

if STACK_NAME in "cicd":
    user_data = get_cloud_init_script(
        ghcr_token=GHCR_TOKEN,
        github_username=pulumi.Output.from_input(GITHUB_USERNAME),
        pulumi_access_token=PULUMI_ACCESS_TOKEN,
        tailscale_auth_key=TAILSCALE_AUTH_KEY,
    )

    droplet = digitalocean.Droplet(
        "pypacktrends-droplet",
        image="ubuntu-20-04-x64",
        name="pypacktrends-prod",
        region=digitalocean.Region.SFO3,
        size=digitalocean.DropletSlug.DROPLET_S1_VCPU1_GB,
        ssh_keys=[DIGITALOCEAN_SSH_KEY_ID],
        tags=["pypacktrends", "prod"],
        user_data=user_data,
    )
    pulumi.export("pypacktrends-ipv4", droplet.ipv4_address)

if STACK_NAME in ["dev", "prod"]:
    caddy_network = create_docker_resource(docker.Network, CADDY_SERVICE_NAME)
    caddy_data_volume = create_docker_resource(
        docker.Volume, f"{CADDY_SERVICE_NAME}-data"
    )
    caddy_config_volume = create_docker_resource(
        docker.Volume, f"{CADDY_SERVICE_NAME}-config"
    )

    caddy_container = create_docker_resource(
        docker.Container,
        CADDY_SERVICE_NAME,
        image=caddy_image.image_identifier,
        ports=[
            docker.ContainerPortArgs(internal=80, external=80),
            docker.ContainerPortArgs(internal=443, external=443),
        ],
        volumes=[
            docker.ContainerVolumeArgs(
                volume_name=caddy_data_volume.name, container_path="/data"
            ),
            docker.ContainerVolumeArgs(
                volume_name=caddy_config_volume.name, container_path="/config"
            ),
        ],
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(name=caddy_network.name)
        ],
        envs=[
            f"BACKEND_PORT={BACKEND_PORT}",
            f"BACKEND_SERVICE_NAME={BACKEND_SERVICE_NAME}",
            f"DOMAIN={DOMAIN}",
        ],
        restart="always",
    )

    backend_container = create_docker_resource(
        docker.Container,
        BACKEND_SERVICE_NAME,
        image=backend_image.image_identifier,
        ports=[docker.ContainerPortArgs(internal=BACKEND_PORT, external=BACKEND_PORT)],
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(name=caddy_network.name)
        ],
        healthcheck=docker.ContainerHealthcheckArgs(
            tests=[
                "CMD",
                "curl",
                "-f",
                f"http://localhost:{BACKEND_PORT}/health-check/",
            ],
            interval="10s",
            timeout="5s",
            retries="5",
        ),
        restart="unless-stopped",
    )

    pulumi.export("app-url", pulumi.Output.concat(PROTOCOL, "://", DOMAIN))

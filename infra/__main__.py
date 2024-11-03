import pulumi
import pulumi_digitalocean as digitalocean
import pulumi_docker as docker
import pulumi_github as github
import pulumi_tls as tls
from components import DockerImageComponent
from utils import create_docker_resource, get_cloud_init_script


STACK_NAME = pulumi.get_stack()
PROJECT_NAME = pulumi.get_project()

backend_service_config = pulumi.Config("backend-service")
BACKEND_SERVICE_PATH = backend_service_config.get("path") or "../backend"
BACKEND_SERVICE_PORT = backend_service_config.get_int("port") or 8000
BACKEND_SERVICE_NAME = backend_service_config.get("name") or "backend"

caddy_service_config = pulumi.Config("caddy-service")
CADDY_SERVICE_PORT = caddy_service_config.get("path") or "../caddy"
CADDY_SERVICE_NAME = caddy_service_config.get("name") or "caddy"

digitalocean_config = pulumi.Config("digitalocean")
DIGITALOCEAN_TOKEN = digitalocean_config.get_secret("token")

domain_config = pulumi.Config("domain")
DOMAIN_NAME = domain_config.get("name") or "pypacktrends.com"
DOMAIN_PROTOCOL = domain_config.get("protocol") or "https"

github_config = pulumi.Config("github")
GITHUB_USERNAME = github_config.get("username") or "tylerhillery"
GITHUB_TOKEN = github_config.get_secret("token")

pulumi_config = pulumi.Config("pulumi")
PULUMI_ACCESS_TOKEN = pulumi_config.get_secret("token")

tailscale_config = pulumi.Config("tailscale")
TAILSCALE_AUTH_KEY = tailscale_config.get_secret("auth-key")

caddy_image = DockerImageComponent(
    stack_name=STACK_NAME,
    service_name=CADDY_SERVICE_NAME,
    context=CADDY_SERVICE_PORT,
    github_username=GITHUB_USERNAME,
    github_token=GITHUB_TOKEN,
)

pulumi.export(
    f"docker-image-{CADDY_SERVICE_NAME}:image-identifier", caddy_image.image_identifier
)

backend_image = DockerImageComponent(
    stack_name=STACK_NAME,
    service_name=BACKEND_SERVICE_NAME,
    context=BACKEND_SERVICE_PATH,
    github_username=GITHUB_USERNAME,
    github_token=GITHUB_TOKEN,
)

pulumi.export(
    f"docker-image-{BACKEND_SERVICE_NAME}:image-identifier",
    backend_image.image_identifier,
)

if STACK_NAME in "cicd":
    github_actions_secret_do_token = github.ActionsSecret(
        "github-actions-secret-digitalocean-token",
        secret_name="DIGITALOCEAN_TOKEN",
        repository=PROJECT_NAME,
        plaintext_value=DIGITALOCEAN_TOKEN,
    )
    github_actions_secret_pulumi_token = github.ActionsSecret(
        "github-actions-secret-pulumi-token",
        secret_name="PULUMI_ACCESS_TOKEN",
        repository=PROJECT_NAME,
        plaintext_value=PULUMI_ACCESS_TOKEN,
    )

    user_data = get_cloud_init_script(
        github_token=GITHUB_TOKEN,
        pulumi_access_token=PULUMI_ACCESS_TOKEN,
        tailscale_auth_key=TAILSCALE_AUTH_KEY,
    )

    ssh_key = tls.PrivateKey("tls-private-key", algorithm="RSA", rsa_bits=4096)
    pulumi.export("ssh-key:private-key-pem", ssh_key.private_key_pem)

    do_ssh_key = digitalocean.SshKey(
        "digitalocean-ssh-key",
        name=f"pulumi-{PROJECT_NAME}",
        public_key=ssh_key.public_key_openssh,
    )

    droplet = digitalocean.Droplet(
        "digitalocean-droplet",
        image="ubuntu-20-04-x64",
        name=f"{PROJECT_NAME}-prod",
        region=digitalocean.Region.SFO3,
        size=digitalocean.DropletSlug.DROPLET_S1_VCPU1_GB,
        ssh_keys=[do_ssh_key.id],
        user_data=user_data,
        opts=pulumi.ResourceOptions(
            ignore_changes=["user_data"],
        ),
    )
    pulumi.export("droplet:ipv4", droplet.ipv4_address)

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
        network_mode="bridge",
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(name=caddy_network.name)
        ],
        envs=[
            f"BACKEND_PORT={BACKEND_SERVICE_PORT}",
            f"BACKEND_SERVICE_NAME={BACKEND_SERVICE_NAME}",
            f"DOMAIN={DOMAIN_NAME}",
        ],
        restart="always",
    )

    backend_container = create_docker_resource(
        docker.Container,
        BACKEND_SERVICE_NAME,
        image=backend_image.image_identifier,
        ports=[
            docker.ContainerPortArgs(
                internal=BACKEND_SERVICE_PORT, external=BACKEND_SERVICE_PORT
            )
        ],
        network_mode="bridge",
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(name=caddy_network.name)
        ],
        healthcheck=docker.ContainerHealthcheckArgs(
            tests=[
                "CMD",
                "curl",
                "-f",
                f"http://localhost:{BACKEND_SERVICE_PORT}/health-check/",
            ],
            interval="10s",
            timeout="5s",
            retries="5",
        ),
        restart="unless-stopped",
    )

    pulumi.export("app:url", pulumi.Output.concat(DOMAIN_PROTOCOL, "://", DOMAIN_NAME))

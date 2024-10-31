import pulumi
import pulumi_docker as docker

from components import DockerImageComponent
from utils import create_docker_resource

config = pulumi.Config()
BACKEND_PATH = config.get("backend-path") or "../backend"
BACKEND_PORT = config.get_int("backend-port") or 8000
BACKEND_SERVICE_NAME = config.get("backend-service-name") or "backend"
CADDY_PATH = config.get("caddy-path") or "../caddy"
CADDY_SERVICE_NAME = config.get("caddy-service-name") or "caddy"
DOMAIN = config.get("domain") or "localhost"
PROTOCOL = config.get("protocol") or "http"
STACK_NAME = pulumi.get_stack()

pulumi.export("stack-name", STACK_NAME)

caddy_image = DockerImageComponent(
    STACK_NAME, CADDY_SERVICE_NAME, CADDY_PATH, f"{CADDY_PATH}/Dockerfile"
)

pulumi.export(f"{CADDY_SERVICE_NAME}-image-tag", caddy_image.image_tag)

backend_image = DockerImageComponent(
    STACK_NAME, BACKEND_SERVICE_NAME, BACKEND_PATH, f"{BACKEND_PATH}/Dockerfile"
)

pulumi.export(f"{BACKEND_SERVICE_NAME}-image-tag", backend_image.image_tag)


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
        image=caddy_image.image_tag,
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
        image=backend_image.image_tag,
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

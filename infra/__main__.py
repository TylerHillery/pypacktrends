import pulumi
import pulumi_docker as docker
import pulumi_docker_build as docker_build

config = pulumi.Config()
BACKEND_PATH = config.get("backend-path") or "../backend"
BACKEND_PORT = config.get_int("backend-port") or 8000
BACKEND_SERVICE_NAME = config.get("backend-service-name") or "pypacktrends-backend"
CADDY_PATH = config.get("caddy-path") or "../caddy"
CADDY_SERVICE_NAME = config.get("caddy-service-name") or "caddy"
DOMAIN = config.get("domain") or "localhost"
DOCKER_REPOSITORY = config.get("docker-respoitory") or "tylerhillery"
STACK_NAME = pulumi.get_stack()

pulumi.export("stack-name", STACK_NAME)

caddy_network = docker.Network("caddy", name="caddy")

pulumi.export("caddy-network", caddy_network.name)

caddy_data_volume = docker.Volume("caddy-data-volume", name="caddy-data")

pulumi.export("caddy-data-volume", caddy_data_volume.name)

caddy_config_volume = docker.Volume("caddy-config-volume", name="caddy-config")

pulumi.export("caddy-config-volume", caddy_config_volume.name)

caddy_image = docker_build.Image(
    f"{CADDY_SERVICE_NAME}-image",
    tags=[f"{DOCKER_REPOSITORY}/{CADDY_SERVICE_NAME}:{STACK_NAME}"],
    push=False,
    context=docker_build.ContextArgs(location=CADDY_PATH),
    dockerfile=docker_build.DockerfileArgs(location=f"{CADDY_PATH}/Dockerfile"),
    platforms=[docker_build.Platform.LINUX_AMD64],
    exports=[docker_build.ExportArgs(docker=docker_build.ExportDockerArgs())],
)

pulumi.export("caddy-image-ref", caddy_image.ref)

caddy_container = docker.Container(
    f"{CADDY_SERVICE_NAME}-container",
    image=caddy_image.ref,
    name=CADDY_SERVICE_NAME,
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
    networks_advanced=[docker.ContainerNetworksAdvancedArgs(name=caddy_network.name)],
    envs=[
        f"BACKEND_PORT={BACKEND_PORT}",
        f"BACKEND_SERVICE_NAME={BACKEND_SERVICE_NAME}",
        f"DOMAIN={DOMAIN}",
    ],
    restart="always",
)

pulumi.export("caddy-container-name", caddy_container.name)

backend_image = docker_build.Image(
    f"{BACKEND_SERVICE_NAME}-image",
    tags=[f"{DOCKER_REPOSITORY}/{BACKEND_SERVICE_NAME}:{STACK_NAME}"],
    push=False,
    context=docker_build.ContextArgs(location=BACKEND_PATH),
    dockerfile=docker_build.DockerfileArgs(location=f"{BACKEND_PATH}/Dockerfile"),
    platforms=[docker_build.Platform.LINUX_AMD64],
    exports=[docker_build.ExportArgs(docker=docker_build.ExportDockerArgs())],
)

pulumi.export("backend-image-ref", backend_image.ref)

backend_container = docker.Container(
    f"{BACKEND_SERVICE_NAME}-container",
    image=backend_image.ref,
    name=BACKEND_SERVICE_NAME,
    ports=[docker.ContainerPortArgs(internal=BACKEND_PORT, external=BACKEND_PORT)],
    networks_advanced=[docker.ContainerNetworksAdvancedArgs(name=caddy_network.name)],
    healthcheck=docker.ContainerHealthcheckArgs(
        tests=["CMD", "curl", "-f", f"http://localhost:{BACKEND_PORT}/health-check/"],
        interval="10s",
        timeout="5s",
        retries="5",
    ),
    restart="unless-stopped",
)

pulumi.export("backend-container-name", backend_container.name)

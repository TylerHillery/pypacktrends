import pulumi
import pulumi_docker as docker
import pulumi_docker_build as docker_build

config = pulumi.Config()
CONTAINER_REGISTRY_ADDRESS = config.get("container-registry-address") or "ghcr.io"
CONTAINER_REGISTRY_USERNAME = (
    config.get("container-registry-username") or "tylerhillery"
)
CONTAINER_REGISTRY_REPOSITORY = (
    config.get("container-registry-repository") or "pypacktrends"
)
CONTAINER_REGISTRY_TOKEN = config.get_secret("container-registry-token")


class DockerImageComponent(pulumi.ComponentResource):  # type: ignore
    def __init__(
        self,
        stack_name: str,
        service_name: str,
        context: str,
        opts: pulumi.ResourceOptions = None,
    ):
        super().__init__(
            "pkg:index:DockerImageComponent",
            f"{service_name}-docker-image-component",
            None,
            opts,
        )
        self.stack_name = stack_name
        self.image_tag = self.get_image_tag(service_name)
        self.docker_build_image_config = dict(
            resource_name=f"{service_name}-image",
            context=docker_build.ContextArgs(location=context),
            dockerfile=docker_build.DockerfileArgs(location=f"{context}/Dockerfile"),
            platforms=[docker_build.Platform.LINUX_AMD64],
            tags=[self.image_tag],
        )
        self.image = self.get_image_builder()
        self.image_identifier = self.get_image_identifier()

    def get_image_builder(self) -> docker_build.Image | docker.RemoteImage:
        match self.stack_name:
            case "dev":
                return self.build_local_image()
            case "cicd":
                pulumi.export("container-registry-token", CONTAINER_REGISTRY_TOKEN)
                return self.build_and_publish_image()
            case "prod":
                return self.use_remote_image()
            case _:
                raise ValueError("Unknown stack name")

    def get_image_identifier(self) -> str:
        return self.image.image_id if self.stack_name == "prod" else self.image.ref  # type: ignore

    def get_image_tag(self, service_name: str) -> str:
        tag = "latest"
        prefix = f"{CONTAINER_REGISTRY_ADDRESS}/"
        if self.stack_name == "dev":
            tag = self.stack_name
            prefix = ""
        return f"{prefix}{CONTAINER_REGISTRY_USERNAME}/{CONTAINER_REGISTRY_REPOSITORY}/{service_name}:{tag}"

    def build_local_image(self) -> docker_build.Image:
        return docker_build.Image(
            **self.docker_build_image_config,
            push=False,
            exports=[docker_build.ExportArgs(docker=docker_build.ExportDockerArgs())],
        )

    def build_and_publish_image(self) -> docker_build.Image:
        # TODO: see if I can make package public
        return docker_build.Image(
            **self.docker_build_image_config,
            push=True,
            registries=[
                docker_build.RegistryArgs(
                    address=CONTAINER_REGISTRY_ADDRESS,
                    username=CONTAINER_REGISTRY_USERNAME,
                    password=CONTAINER_REGISTRY_TOKEN,
                )
            ],
        )

    def use_remote_image(self) -> docker.RemoteImage:
        # TODO: figure out out to pull from pivate container registry
        registry_image = docker.get_registry_image(name=self.image_tag)
        return docker.RemoteImage(
            self.docker_build_image_config.get("resource_name"),
            name=registry_image.name,
            keep_locally=True,
            pull_triggers=[registry_image.sha256_digest],
        )

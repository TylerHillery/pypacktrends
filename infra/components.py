import pulumi
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
        dockerfile: str,
        opts: pulumi.ResourceOptions = None,
    ):
        super().__init__(
            "pkg:index:DockerImageComponent",
            f"{service_name}-docker-image-component",
            None,
            opts,
        )
        self.stack_name = stack_name
        self.registries = [
            docker_build.RegistryArgs(
                address=CONTAINER_REGISTRY_ADDRESS,
                username=CONTAINER_REGISTRY_USERNAME,
                password=CONTAINER_REGISTRY_TOKEN,
            )
        ]
        self.exports = [docker_build.ExportArgs(docker=docker_build.ExportDockerArgs())]

        self.image_tag = self.get_image_tag(service_name)

        self.docker_build_image_config = dict(
            resource_name=f"{service_name}-image",
            tags=[self.image_tag],
            context=docker_build.ContextArgs(location=context),
            dockerfile=docker_build.DockerfileArgs(location=dockerfile),
            platforms=[docker_build.Platform.LINUX_AMD64],
        )

        self.image = self.get_image_builder()

    def get_image_builder(self) -> docker_build.Image:
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

    def get_image_tag(self, service_name: str) -> str:
        tag = "latest"
        prefix = f"{CONTAINER_REGISTRY_ADDRESS}/"
        if self.stack_name == "dev":
            tag = self.stack_name
            prefix = ""
        return f"{prefix}{CONTAINER_REGISTRY_USERNAME}/{CONTAINER_REGISTRY_REPOSITORY}/{service_name}:{tag}"

    def build_local_image(self) -> docker_build.Image:
        return docker_build.Image(
            **self.docker_build_image_config, push=False, exports=self.exports
        )

    def build_and_publish_image(self) -> docker_build.Image:
        return docker_build.Image(
            **self.docker_build_image_config, push=True, registries=self.registries
        )

    def use_remote_image(self) -> docker_build.image:
        return docker_build.Image(
            **self.docker_build_image_config,
            push=False,
            pull=True,
            exports=self.exports,
            registries=self.registries,
        )

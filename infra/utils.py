from typing import Type, Any
from jinja2 import Environment, FileSystemLoader
import pulumi
import pulumi_docker as docker


def create_docker_resource(
    resource_type: Type[docker.Network | docker.Volume | docker.Container],
    service_name: str,
    **kwargs: Any,
) -> docker.Network | docker.Volume | docker.Container:
    prefix = resource_type.__name__.lower()
    resource_name = f"{prefix}-{service_name}"
    resource = resource_type(resource_name, name=service_name, **kwargs)
    pulumi.export(f"docker-{resource_name}:name", resource.name)
    return resource


def get_cloud_init_script(**kwargs: dict[str, pulumi.Output]) -> Any:
    def render_cloud_init_template(kwargs: dict[str, str]) -> Any:
        env = Environment(loader=FileSystemLoader("./templates"))
        template = env.get_template("cloud-init.yml")
        return template.render(**kwargs)

    return pulumi.Output.all(**kwargs).apply(render_cloud_init_template)

from typing import Type, Any
import pulumi
import pulumi_docker as docker


def create_docker_resource(
    resource_type: Type[docker.Network | docker.Volume | docker.Container],
    service_name: str,
    **kwargs: Any,
) -> docker.Network | docker.Volume | docker.Container:
    suffix = resource_type.__name__.lower()
    resource_name = f"{service_name}-{suffix}"
    resource = resource_type(resource_name, name=service_name, **kwargs)
    pulumi.export(resource_name, resource.name)
    return resource

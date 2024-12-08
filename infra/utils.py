from typing import Any

import pulumi
from jinja2 import Environment, FileSystemLoader


def render_template(template_name: str, **kwargs: str | pulumi.Output | None) -> Any:
    def _render_template(kwargs: dict[str, str]) -> Any:
        env = Environment(loader=FileSystemLoader("./templates"))
        template = env.get_template(template_name)
        return template.render(**kwargs)

    return pulumi.Output.all(**kwargs).apply(_render_template)


def create_cmd(**kwargs: str | pulumi.Output | None) -> Any:
    def _create_cmd(kwargs: dict[str, str]) -> Any:
        return f"""
        cd {kwargs["vps_project_path"]}
        git pull
        SENTRY_DSN='{kwargs["sentry_dsn"]}' ./scripts/update_service.sh {kwargs["container_registry_prefix"]} {kwargs["backend_service_name"]}
    """

    return pulumi.Output.all(**kwargs).apply(_create_cmd)

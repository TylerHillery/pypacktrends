from typing import Any

import pulumi
from jinja2 import Environment, FileSystemLoader


def get_cloud_init_script(**kwargs: str | pulumi.Output | None) -> Any:
    def render_cloud_init_template(kwargs: dict[str, str]) -> Any:
        env = Environment(loader=FileSystemLoader("./templates"))
        template = env.get_template("cloud-init.yml")
        return template.render(**kwargs)

    return pulumi.Output.all(**kwargs).apply(render_cloud_init_template)

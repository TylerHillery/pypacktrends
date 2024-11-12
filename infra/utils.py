from typing import Any

import pulumi
from jinja2 import Environment, FileSystemLoader


def render_template(template_name: str, **kwargs: str | pulumi.Output | None) -> Any:
    def _render_template(kwargs: dict[str, str]) -> Any:
        env = Environment(loader=FileSystemLoader("./templates"))
        template = env.get_template(template_name)
        return template.render(**kwargs)

    return pulumi.Output.all(**kwargs).apply(_render_template)

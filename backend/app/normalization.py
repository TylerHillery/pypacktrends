from typing import Annotated

from pydantic import BeforeValidator


def normalize_package_name(value: str) -> str:
    return value.strip().lower()


NormalizedPackageName = Annotated[str, BeforeValidator(normalize_package_name)]

from typing import Annotated

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from app.core.config import templates

router = APIRouter()

packages = []


@router.get("/packages", response_class=HTMLResponse)
async def list_packages(request: Request):
    return templates.TemplateResponse(
        request=request, name="home/packages.html", context={"packages": packages}
    )


@router.post("/packages", response_class=HTMLResponse)
async def create_package(request: Request, package_name: Annotated[str, Form()]):
    if package_name not in packages:
        packages.append(package_name)
    return templates.TemplateResponse(
        request=request, name="home/packages.html", context={"packages": packages}
    )


@router.delete("/packages", response_class=HTMLResponse)
async def delete_package(request: Request, package_name: str):
    packages.remove(package_name)
    return templates.TemplateResponse(
        request=request, name="home/packages.html", context={"packages": packages}
    )

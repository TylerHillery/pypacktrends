import pulumi


class Settings:
    STACK_NAME: str = pulumi.get_stack()
    PROJECT_NAME: str = pulumi.get_project()

    backend_service_config: pulumi.Config = pulumi.Config("backend-service")
    BACKEND_SERVICE_PATH: str = backend_service_config.get("path") or "../backend"
    BACKEND_SERVICE_PORT: int = backend_service_config.get_int("port") or 8000
    BACKEND_SERVICE_NAME: str = backend_service_config.get("name") or "backend"

    caddy_service_config: pulumi.Config = pulumi.Config("caddy-service")
    CADDY_SERVICE_PATH: str = caddy_service_config.get("path") or "../caddy"
    CADDY_SERVICE_NAME: str = caddy_service_config.get("name") or "caddy"

    digitalocean_config: pulumi.Config = pulumi.Config("digitalocean")
    DIGITALOCEAN_TOKEN: pulumi.Output | None = digitalocean_config.get_secret("token")

    docker_config: pulumi.Config = pulumi.Config("docker")
    CONTAINER_REGISTRY_ADDRESS: str = (
        docker_config.get("container-registry-address") or "ghcr.io"
    )
    CONTAINER_REGISTRY_REPOSITORY: str = (
        docker_config.get("container-registry-repository") or pulumi.get_project()
    )

    domain_config: pulumi.Config = pulumi.Config("domain")
    DOMAIN_NAME: str = domain_config.get("name") or "pypacktrends.com"
    DOMAIN_PROTOCOL: str = domain_config.get("protocol") or "https"

    github_config: pulumi.Config = pulumi.Config("github")
    GITHUB_USERNAME: str = github_config.get("username") or "tylerhillery"
    GITHUB_TOKEN: pulumi.Output | None = github_config.get_secret("token")

    pulumi_config: pulumi.Config = pulumi.Config("pulumi")
    PULUMI_ACCESS_TOKEN: pulumi.Output | None = pulumi_config.get_secret("token")

    tailscale_config: pulumi.Config = pulumi.Config("tailscale")
    TAILSCALE_AUTH_KEY: pulumi.Output | None = tailscale_config.get_secret("auth-key")


settings = Settings()

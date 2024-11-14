import pulumi


class Settings:
    STACK_NAME: str = pulumi.get_stack()
    PROJECT_NAME: str = pulumi.get_project()
    ORG_NAME: str = pulumi.get_organization()

    backend_service_config: pulumi.Config = pulumi.Config("backend-service")
    BACKEND_SERVICE_PATH: str = backend_service_config.get("path") or "../backend"
    BACKEND_SERVICE_PORT: int = backend_service_config.get_int("port") or 8000
    BACKEND_SERVICE_NAME: str = backend_service_config.get("name") or "backend"

    caddy_service_config: pulumi.Config = pulumi.Config("caddy-service")
    CADDY_SERVICE_PATH: str = caddy_service_config.get("path") or "../caddy"
    CADDY_SERVICE_NAME: str = caddy_service_config.get("name") or "caddy"

    cloudflare_config: pulumi.Config = pulumi.Config("cloudflare")
    CLOUDFLARE_API_TOKEN: pulumi.Output | None = cloudflare_config.get_secret(
        "apiToken"
    )

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

    project_config: pulumi.Config = pulumi.Config()
    CLOUDFLARE_FORWARD_EMAIL: str = (
        project_config.get("cloudflare-forward-email") or "tyhillery@gmail.com"
    )
    CLOUDFLARE_ZONE_ID: str = (
        project_config.get("cloudflare-zone-id") or "d973f173bbb9a119f2821c25bb312bef"
    )

    pulumi_config: pulumi.Config = pulumi.Config("pulumi")
    PULUMI_ACCESS_TOKEN: pulumi.Output | None = pulumi_config.get_secret("token")
    PULUMI_OIDC_ISSUER: str = (
        pulumi_config.get("oidc-issuer") or "https://api.pulumi.com/oidc"
    )

    tailscale_config: pulumi.Config = pulumi.Config("tailscale")
    TAILSCALE_AUTH_KEY: pulumi.Output | None = tailscale_config.get_secret("auth-key")
    TAILSCALE_OAUTH_CLIENT_ID: pulumi.Output | None = tailscale_config.get_secret(
        "oauth-client-id"
    )
    TAILSCALE_OAUTH_CLIENT_SECRET: pulumi.Output | None = tailscale_config.get_secret(
        "oauth-client-secret"
    )

    vps_config: pulumi.Config = pulumi.Config("vps")
    VPS_USERNAME: str = vps_config.get("username") or "github"

    @property
    def BACKEND_DOCKER_IMAGE_URL(self) -> str:
        return f"{self.CONTAINER_REGISTRY_PREFIX}/{self.BACKEND_SERVICE_NAME}"

    @property
    def CONTAINER_REGISTRY_PREFIX(self) -> str:
        return (
            f"{self.CONTAINER_REGISTRY_ADDRESS}/"
            f"{self.GITHUB_USERNAME}/"
            f"{self.CONTAINER_REGISTRY_REPOSITORY}"
        )

    @property
    def GITHUB_REPOSITORY(self) -> str:
        return f"https://github.com/{settings.GITHUB_USERNAME}/{self.PROJECT_NAME}"

    @property
    def VPS_PROJECT_PATH(self) -> str:
        return f"/home/{self.VPS_USERNAME}/{self.PROJECT_NAME}"


settings = Settings()

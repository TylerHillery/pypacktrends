import pulumi
import pulumi_command as command
import pulumi_cloudflare as cloudflare
import pulumi_digitalocean as digitalocean
import pulumi_docker_build as docker_build
import pulumi_tls as tls
from config import settings
from utils import get_cloud_init_script

backend_image = docker_build.Image(
    f"docker-build-image-{settings.BACKEND_SERVICE_NAME}",
    context=docker_build.ContextArgs(location=settings.BACKEND_SERVICE_PATH),
    dockerfile=docker_build.DockerfileArgs(
        location=f"{settings.BACKEND_SERVICE_PATH}/Dockerfile"
    ),
    platforms=[docker_build.Platform.LINUX_AMD64],
    tags=[f"{settings.BACKEND_DOCKER_IMAGE_URL}:latest"],
    registries=[
        docker_build.RegistryArgs(
            address=settings.CONTAINER_REGISTRY_ADDRESS,
            username=settings.GITHUB_USERNAME,
            password=settings.GITHUB_TOKEN,
        )
    ],
    push=True,
)

pulumi.export(
    f"docker-build-image-{settings.BACKEND_SERVICE_NAME}:ref",
    backend_image.ref,
)

user_data = get_cloud_init_script(
    container_registry_address=settings.CONTAINER_REGISTRY_ADDRESS,
    github_token=settings.GITHUB_TOKEN,
    github_username=settings.GITHUB_USERNAME,
    project_name=settings.PROJECT_NAME,
    pulumi_access_token=settings.PULUMI_ACCESS_TOKEN,
    tailscale_auth_key=settings.TAILSCALE_AUTH_KEY,
    vps_username=settings.VPS_USERNAME,
    vps_project_path=settings.VPS_PROJECT_PATH,
)

ssh_key = tls.PrivateKey("tls-private-key", algorithm="RSA", rsa_bits=4096)
pulumi.export("ssh-key:private-key-pem", ssh_key.private_key_pem)

do_ssh_key = digitalocean.SshKey(
    "digitalocean-ssh-key",
    name=f"pulumi-{settings.PROJECT_NAME}",
    public_key=ssh_key.public_key_openssh,
)

droplet = digitalocean.Droplet(
    "digitalocean-droplet",
    image="ubuntu-20-04-x64",
    name=f"{settings.PROJECT_NAME}-prod",
    region=digitalocean.Region.SFO3,
    size=digitalocean.DropletSlug.DROPLET_S1_VCPU1_GB,
    ssh_keys=[do_ssh_key.id],
    user_data=get_cloud_init_script(
        github_token=settings.GITHUB_TOKEN,
        github_username=settings.GITHUB_USERNAME,
        project_name=settings.PROJECT_NAME,
        pulumi_access_token=settings.PULUMI_ACCESS_TOKEN,
        tailscale_auth_key=settings.TAILSCALE_AUTH_KEY,
        vps_username=settings.VPS_USERNAME,
    ),
    opts=pulumi.ResourceOptions(
        ignore_changes=["user_data"],
    ),
)
pulumi.export("droplet:ipv4", droplet.ipv4_address)

cloudflare_a_record_root = cloudflare.Record(
    "cloudflare-a-record-root",
    zone_id=settings.CLOUDFLARE_ZONE_ID,
    type="A",
    name="@",
    content=droplet.ipv4_address,
    ttl=60,
    proxied=False,
)

cloudflare_a_record_www = cloudflare.Record(
    "cloudflare-a-record-www",
    zone_id=settings.CLOUDFLARE_ZONE_ID,
    type="A",
    name="www",
    content=droplet.ipv4_address,
    ttl=60,
    proxied=False,
)

cloudfalre_email_routing_catch_all = cloudflare.EmailRoutingCatchAll(
    "cloudfalre-email-routing-catch-all ",
    zone_id=settings.CLOUDFLARE_ZONE_ID,
    name="Catch-All",
    enabled=True,
    matchers=[{"type": "all"}],
    actions=[{"type": "forward", "values": [settings.CLOUDFLARE_FORWARD_EMAIL]}],
)

remote_command = command.remote.Command(
    "remote-command",
    connection=command.remote.ConnectionArgs(
        host=droplet.name,
        user=settings.VPS_USERNAME,
    ),
    create=f"""
        cd {settings.VPS_PROJECT_PATH}
        git pull
        ./scripts/update_service.sh {settings.CONTAINER_REGISTRY_PREFIX} {settings.BACKEND_SERVICE_NAME}
    """,
    triggers=[backend_image.ref],
)
pulumi.export("remote-command:stdout", remote_command.stdout)
pulumi.export("remote-command:stderr", remote_command.stderr)

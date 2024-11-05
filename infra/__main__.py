import pulumi
import pulumi_command as command
import pulumi_cloudflare as cloudflare
import pulumi_digitalocean as digitalocean
import pulumi_docker as docker
import pulumi_tls as tls
from components import DockerImageComponent
from config import settings
from utils import create_docker_resource, get_cloud_init_script

caddy_image = DockerImageComponent(
    service_name=settings.CADDY_SERVICE_NAME,
    context=settings.CADDY_SERVICE_PATH,
)

pulumi.export(
    f"docker-image-{settings.CADDY_SERVICE_NAME}:image-identifier",
    caddy_image.image_identifier,
)

backend_image = DockerImageComponent(
    service_name=settings.BACKEND_SERVICE_NAME,
    context=settings.BACKEND_SERVICE_PATH,
)

pulumi.export(
    f"docker-image-{settings.BACKEND_SERVICE_NAME}:image-identifier",
    backend_image.image_identifier,
)

if settings.STACK_NAME == "cicd":
    user_data = get_cloud_init_script(
        github_token=settings.GITHUB_TOKEN,
        github_username=settings.GITHUB_USERNAME,
        project_name=settings.PROJECT_NAME,
        pulumi_access_token=settings.PULUMI_ACCESS_TOKEN,
        tailscale_auth_key=settings.TAILSCALE_AUTH_KEY,
        vps_username=settings.VPS_USERNAME,
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
        create="""
            cd /opt/pypacktrends/infra
            sudo git pull
            sudo uv run pulumi up --stack prod --refresh --yes
        """,
        environment={
            "PULUMI_ACCESS_TOKEN": settings.PULUMI_ACCESS_TOKEN,
        },
        opts=pulumi.ResourceOptions(depends_on=[caddy_image, backend_image]),
    )
    pulumi.export("remote-command:stdout", remote_command.stdout)
    pulumi.export("remote-command:stderr", remote_command.stderr)


if settings.STACK_NAME in ["dev", "prod"]:
    caddy_network = create_docker_resource(docker.Network, settings.CADDY_SERVICE_NAME)
    caddy_data_volume = create_docker_resource(
        docker.Volume, f"{settings.CADDY_SERVICE_NAME}-data"
    )
    caddy_config_volume = create_docker_resource(
        docker.Volume, f"{settings.CADDY_SERVICE_NAME}-config"
    )

    caddy_container = create_docker_resource(
        docker.Container,
        settings.CADDY_SERVICE_NAME,
        image=caddy_image.image_identifier,
        ports=[
            docker.ContainerPortArgs(internal=80, external=80),
            docker.ContainerPortArgs(internal=443, external=443),
        ],
        volumes=[
            docker.ContainerVolumeArgs(
                volume_name=caddy_data_volume.name, container_path="/data"
            ),
            docker.ContainerVolumeArgs(
                volume_name=caddy_config_volume.name, container_path="/config"
            ),
        ],
        network_mode="bridge",
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(name=caddy_network.name)
        ],
        envs=[
            f"BACKEND_PORT={settings.BACKEND_SERVICE_PORT}",
            f"BACKEND_SERVICE_NAME={settings.BACKEND_SERVICE_NAME}",
            f"DOMAIN={settings.DOMAIN_NAME}",
        ],
        restart="always",
    )

    backend_container = create_docker_resource(
        docker.Container,
        settings.BACKEND_SERVICE_NAME,
        image=backend_image.image_identifier,
        ports=[
            docker.ContainerPortArgs(
                internal=settings.BACKEND_SERVICE_PORT,
            )
        ],
        network_mode="bridge",
        networks_advanced=[
            docker.ContainerNetworksAdvancedArgs(name=caddy_network.name)
        ],
        healthcheck=docker.ContainerHealthcheckArgs(
            tests=[
                "CMD",
                "curl",
                "-f",
                f"http://localhost:{settings.BACKEND_SERVICE_PORT}/health-check/",
            ],
            interval="10s",
            timeout="5s",
            retries="5",
        ),
        restart="unless-stopped",
    )

    pulumi.export(
        "app:url",
        pulumi.Output.concat(settings.DOMAIN_PROTOCOL, "://", settings.DOMAIN_NAME),
    )

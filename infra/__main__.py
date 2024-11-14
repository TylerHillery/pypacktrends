import pulumi
import pulumi_command as command
import pulumi_cloudflare as cloudflare
import pulumi_digitalocean as digitalocean
import pulumi_docker_build as docker_build
import pulumi_github as github
import pulumi_gcp as gcp
import pulumi_tls as tls
from config import settings
from utils import render_template

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

ssh_key = tls.PrivateKey("tls-private-key", algorithm="RSA", rsa_bits=4096)
pulumi.export("ssh-key:private-key-pem", ssh_key.private_key_pem)

do_ssh_key = digitalocean.SshKey(
    "digitalocean-ssh-key",
    name=f"pulumi-{settings.PROJECT_NAME}",
    public_key=ssh_key.public_key_openssh,
)

user_data = render_template(
    template_name="cloud-init.yml",
    container_registry_address=settings.CONTAINER_REGISTRY_ADDRESS,
    github_token=settings.GITHUB_TOKEN,
    github_username=settings.GITHUB_USERNAME,
    project_name=settings.PROJECT_NAME,
    pulumi_access_token=settings.PULUMI_ACCESS_TOKEN,
    tailscale_auth_key=settings.TAILSCALE_AUTH_KEY,
    vps_username=settings.VPS_USERNAME,
    vps_project_path=settings.VPS_PROJECT_PATH,
)
pulumi.export("droplet:user-data", user_data)

droplet = digitalocean.Droplet(
    "digitalocean-droplet",
    image="ubuntu-20-04-x64",
    name=f"{settings.PROJECT_NAME}-prod",
    region=digitalocean.Region.SFO3,
    size=digitalocean.DropletSlug.DROPLET_S1_VCPU1_GB,
    ssh_keys=[do_ssh_key.id],
    user_data=user_data,
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

github_actions_secret_pulumi_token = github.ActionsSecret(
    "github-actions-secret-github-token",
    secret_name="GH_TOKEN",
    repository=settings.PROJECT_NAME,
    plaintext_value=settings.GITHUB_TOKEN,
)

github_actions_secret_pulumi_token = github.ActionsSecret(
    "github-actions-secret-pulumi-token",
    secret_name="PULUMI_ACCESS_TOKEN",
    repository=settings.PROJECT_NAME,
    plaintext_value=settings.PULUMI_ACCESS_TOKEN,
)

github_actions_secret_tailscale_oauth_client_id = github.ActionsSecret(
    "github-actions-secret-tailscale-oauth-client-id",
    secret_name="TS_OAUTH_CLIENT_ID",
    repository=settings.PROJECT_NAME,
    plaintext_value=settings.TAILSCALE_OAUTH_CLIENT_ID,
)

github_actions_secret_tailscale_oauth_client_secret = github.ActionsSecret(
    "github-actions-secret-tailscale-oauth-client-secret",
    secret_name="TS_OAUTH_SECRET",
    repository=settings.PROJECT_NAME,
    plaintext_value=settings.TAILSCALE_OAUTH_CLIENT_SECRET,
)

gcp_project_config = gcp.organizations.get_project()
gcp_project_id = gcp_project_config.number

gcp_iam_workload_identity_pool_pulumi = gcp.iam.WorkloadIdentityPool(
    "gcp-iam-workload-identity-pool-pulumi",
    workload_identity_pool_id="pulumi-oidc",
    display_name="Pulumi OIDC",
)

gcp_iam_workload_identity_pool_provider_pulumi = gcp.iam.WorkloadIdentityPoolProvider(
    "gcp-iam-workload-identity-pool-provider-pulumi",
    workload_identity_pool_id=gcp_iam_workload_identity_pool_pulumi.workload_identity_pool_id,
    workload_identity_pool_provider_id="pulumi-oidc",
    attribute_mapping={
        "google.subject": "assertion.sub",
    },
    oidc=gcp.iam.WorkloadIdentityPoolProviderOidcArgs(
        issuer_uri=settings.PULUMI_OIDC_ISSUER,
        allowed_audiences=[f"gcp:{settings.ORG_NAME}"],
    ),
)

gcp_service_account_pulumi = gcp.serviceaccount.Account(
    "gcp-service-account-pulumi", account_id="pulumi-oidc", display_name="Pulumi OIDC"
)

gcp_project_iam_member_role_editor = gcp.projects.IAMMember(
    "gcp-projects-iammember-editor-role",
    member=gcp_service_account_pulumi.email.apply(
        lambda email: f"serviceAccount:{email}"
    ),
    role="roles/editor",
    project=gcp_project_id,
)

gcp_service_account_iam_binding_pulumi = gcp.serviceaccount.IAMBinding(
    "gcp-service-account-iam-policy-binding-pulumi",
    service_account_id=gcp_service_account_pulumi.name,
    role="roles/iam.workloadIdentityUser",
    members=gcp_iam_workload_identity_pool_pulumi.name.apply(
        lambda name: [f"principalSet://iam.googleapis.com/{name}/*"]
    ),
)
gcp_pulumi_esc_yml = render_template(
    template_name="pulumi_esc_gcp.yml",
    gcp_project=int(gcp_project_id),
    workload_pool_id=gcp_iam_workload_identity_pool_provider_pulumi.workload_identity_pool_id,
    provider_id=gcp_iam_workload_identity_pool_provider_pulumi.workload_identity_pool_provider_id,
    service_account_email=gcp_service_account_pulumi.email,
)

pulumi.export("pulumi:esc-yml-gcp", gcp_pulumi_esc_yml)

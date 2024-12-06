import pulumi
import pulumi_cloudflare as cloudflare
import pulumi_command as command
import pulumi_digitalocean as digitalocean
import pulumi_docker_build as docker_build
import pulumi_gcp as gcp
import pulumi_github as github
import pulumi_tls as tls
from config import settings
from utils import render_template

# Docker Build Image
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
            username=settings.GITHUB_USERNAME.lower(),
            password=settings.GITHUB_TOKEN,
        )
    ],
    push=True,
)

pulumi.export(
    f"docker-build-image-{settings.BACKEND_SERVICE_NAME}:ref",
    backend_image.ref,
)

# Droplet Configs
ssh_key = tls.PrivateKey("tls-private-key", algorithm="RSA", rsa_bits=4096)
pulumi.export("ssh-key:private-key-pem", ssh_key.private_key_pem)

do_ssh_key = digitalocean.SshKey(
    "digitalocean-ssh-key",
    name=f"pulumi-{settings.PROJECT_NAME}",
    public_key=ssh_key.public_key_openssh,
)

user_data = render_template(
    template_name="cloud-init.yml",
    github_username=settings.GITHUB_USERNAME,
    project_name=settings.PROJECT_NAME,
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

# Cloudflare Configs
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

cloudflare_a_record_root_dbt_docs = cloudflare.Record(
    "cloudflare-a-record-root-dbt-docs",
    zone_id=settings.CLOUDFLARE_ZONE_ID,
    type="A",
    name="dbtdocs",
    content=droplet.ipv4_address,
    ttl=60,
    proxied=False,
)

cloudflare_a_record_www_dbt_docs = cloudflare.Record(
    "cloudflare-a-record-www-dbt-docs",
    zone_id=settings.CLOUDFLARE_ZONE_ID,
    type="A",
    name="www.dbtdocs",
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

# GCP OIDC Config for Pulumi
gcp_project_config = gcp.organizations.get_project()
gcp_project_id = gcp_project_config.number
gcp_project_name = gcp_project_config.name

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

gcp_service_account_pulumi_roles = [
    "roles/editor",
    "roles/resourcemanager.projectIamAdmin",
    "roles/iam.workloadIdentityPoolAdmin",
    "roles/iam.serviceAccountAdmin",
]

gcp_project_iam_members_pulumi = [
    gcp.projects.IAMMember(
        f"gcp-projects-iammember-{role.split('/')[-1]}-role-pulumi",
        member=gcp_service_account_pulumi.email.apply(
            lambda email: f"serviceAccount:{email}"
        ),
        role=role,
        project=gcp_project_id,
    )
    for role in gcp_service_account_pulumi_roles
]

gcp_service_account_iam_binding_pulumi = gcp.serviceaccount.IAMBinding(
    "gcp-service-account-iam-policy-binding-pulumi",
    service_account_id=gcp_service_account_pulumi.name,
    role="roles/iam.workloadIdentityUser",
    members=gcp_iam_workload_identity_pool_pulumi.name.apply(
        lambda name: [f"principalSet://iam.googleapis.com/{name}/*"]
    ),
)
gcp_pulumi_esc_yml = render_template(
    template_name="pulumi-esc-gcp.yml",
    gcp_project=int(gcp_project_id),
    workload_pool_id=gcp_iam_workload_identity_pool_provider_pulumi.workload_identity_pool_id,
    provider_id=gcp_iam_workload_identity_pool_provider_pulumi.workload_identity_pool_provider_id,
    service_account_email=gcp_service_account_pulumi.email,
)

# GCP OIDC Config for GitHub Actions
gcp_iam_workload_identity_pool_github_actions = gcp.iam.WorkloadIdentityPool(
    "gcp-iam-workload-identity-pool-github-actions",
    workload_identity_pool_id="github-actions-oidc",
    display_name="GitHub Actions OIDC",
)

gcp_iam_workload_identity_pool_provider_github_actions = gcp.iam.WorkloadIdentityPoolProvider(
    "gcp-iam-workload-identity-pool-provider-github-actions",
    workload_identity_pool_id=gcp_iam_workload_identity_pool_github_actions.workload_identity_pool_id,
    workload_identity_pool_provider_id="github-actions-oidc",
    attribute_condition=f'attribute.repository == "{settings.GITHUB_USERNAME}/{settings.PROJECT_NAME}"',
    attribute_mapping={
        "google.subject": "assertion.sub",
        "attribute.actor": "assertion.actor",
        "attribute.aud": "assertion.aud",
        "attribute.repository": "assertion.repository",
    },
    oidc=gcp.iam.WorkloadIdentityPoolProviderOidcArgs(
        issuer_uri=settings.GITHUB_OIDC_ISSUER,
    ),
)

gcp_service_account_dbt = gcp.serviceaccount.Account(
    "gcp-service-account-dbt", account_id="dbt-service-account", display_name="dbt"
)

gcp_service_account_dbt_roles = [
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/iam.serviceAccountTokenCreator",
]

gcp_project_iam_members_dbt = [
    gcp.projects.IAMMember(
        f"gcp-projects-iammember-{role.split('/')[-1]}-role-dbt",
        member=gcp_service_account_dbt.email.apply(
            lambda email: f"serviceAccount:{email}"
        ),
        role=role,
        project=gcp_project_id,
    )
    for role in gcp_service_account_dbt_roles
]

workload_identity_base_path = gcp_iam_workload_identity_pool_github_actions.workload_identity_pool_id.apply(
    lambda pool_id: f"projects/{gcp_project_id}/locations/global/workloadIdentityPools/{pool_id}"
)

gcp_service_account_iam_binding_github_actions = gcp.serviceaccount.IAMBinding(
    "gcp-service-account-iam-policy-binding-github-actions",
    service_account_id=gcp_service_account_dbt.name,
    role="roles/iam.workloadIdentityUser",
    members=workload_identity_base_path.apply(
        lambda base_path: [
            f"principalSet://iam.googleapis.com/{base_path}/attribute.repository/{settings.GITHUB_USERNAME}/{settings.PROJECT_NAME}"
        ]
    ),
)

workload_identity_provider = workload_identity_base_path.apply(
    lambda base_path: gcp_iam_workload_identity_pool_provider_github_actions.workload_identity_pool_provider_id.apply(
        lambda provider_id: f"{base_path}/providers/{provider_id}"
    )
)

# GitHub Action Secrets Configs
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

github_actions_secret_smokeshow_auth_key = github.ActionsSecret(
    "github-actions-secret-smokeshow-auth-key",
    secret_name="SMOKESHOW_AUTH_KEY",
    repository=settings.PROJECT_NAME,
    plaintext_value=settings.SMOKESHOW_AUTH_KEY,
)

github_secret_gcp_project_name = github.ActionsSecret(
    "github-actions-secret-gcp-project-name",
    secret_name="GCP_PROJECT",
    repository=settings.PROJECT_NAME,
    plaintext_value=gcp_project_name,
)

github_secret_dbt_service_account_email = github.ActionsSecret(
    "github-actions-secret-dbt-service-account-email",
    secret_name="DBT_SERVICE_ACCOUNT_EMAIL",
    repository=settings.PROJECT_NAME,
    plaintext_value=gcp_service_account_dbt.email,
)

github_actions_secret_workload_identity_provider = github.ActionsSecret(
    "github-actions-secret-workload-identity-provider",
    secret_name="WORKLOAD_IDENTITY_PROVIDER",
    repository=settings.PROJECT_NAME,
    plaintext_value=workload_identity_provider,
)

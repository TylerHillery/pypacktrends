import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.core.logger import logger
from app.normalization import normalize_package_name


def capture_package_requested_events(
    packages: list[str],
    time_range: str,
    show_percentage: bool,
    hx_trigger: str | None,
) -> None:
    if not settings.ENABLE_SERVER_ANALYTICS:
        return

    if settings.POSTHOG_API_KEY is None:
        logger.warning("Skipping PostHog package analytics: missing API key")
        return

    normalized_packages = [
        normalize_package_name(package) for package in packages if package.strip()
    ]

    if not normalized_packages:
        return

    capture_url = f"{str(settings.POSTHOG_HOST).rstrip('/')}/capture/"

    for package in normalized_packages:
        payload = {
            "api_key": settings.POSTHOG_API_KEY,
            "event": "package_requested",
            "distinct_id": "server",
            "properties": {
                "package": package,
                "packages": normalized_packages,
                "time_range": time_range,
                "show_percentage": show_percentage,
                "hx_trigger": hx_trigger,
                "source": "server_htmx",
            },
        }

        try:
            req = Request(
                capture_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=2):
                pass
            logger.info(
                "Submitted PostHog package_requested event "
                f"for package='{package}', packages={normalized_packages}, "
                f"time_range='{time_range}', hx_trigger='{hx_trigger}'"
            )
        except (HTTPError, URLError, TimeoutError) as e:
            logger.warning(
                f"Failed to capture PostHog event for package '{package}': {e}"
            )

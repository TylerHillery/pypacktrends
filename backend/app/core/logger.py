import json
import logging.config
from pathlib import Path

logger = logging.getLogger("pypacktrends")

try:
    config_path = Path(__file__).parent / "logger_config.json"
    with open(config_path, "r") as f:
        config = json.load(f)
    logging.config.dictConfig(config)
except Exception as e:
    logging.basicConfig(level=logging.INFO)
    logger.error(f"Failed to load logging config: {e}")

import logging

from core.config import CONFIG
from core.orchestrator import run

# =========================
# Logging
# =========================

LOG_LEVEL = (
    logging.DEBUG
    if CONFIG["system"]["debug"]
    else logging.INFO
)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# =========================
# Silence external libraries
# =========================

logging.getLogger("yfinance").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("peewee").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# =========================
# Main
# =========================

if __name__ == "__main__":
    logger.info("🚀 Starting Trading AI Agent")
    run()

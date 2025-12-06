"""Constants for the Ghostfolio integration."""

DOMAIN = "ghostfolio"

# Configuration keys
CONF_BASE_URL = "base_url"
CONF_ACCESS_TOKEN = "access_token"
CONF_VERIFY_SSL = "verify_ssl"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_PORTFOLIO_NAME = "portfolio_name"
CONF_PERFORMANCE_RANGES = "performance_ranges"

# Default values
DEFAULT_NAME = "Ghostfolio"
DEFAULT_UPDATE_INTERVAL = 15  # minutes
DEFAULT_PERFORMANCE_RANGES = ["max"]

# Supported performance ranges
PERFORMANCE_RANGE_OPTIONS = ["1d", "wtd", "mtd", "ytd", "1y", "max"]

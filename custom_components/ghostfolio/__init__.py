"""The Ghostfolio integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


from .api import GhostfolioAPI
from .const import (
    CONF_PERFORMANCE_RANGES,
    CONF_UPDATE_INTERVAL,
    DEFAULT_PERFORMANCE_RANGES,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ghostfolio from a config entry."""
    api = GhostfolioAPI(
        base_url=entry.data["base_url"],
        access_token=entry.data["access_token"],
        verify_ssl=entry.data.get("verify_ssl", True),
    )

    update_interval = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    performance_ranges = entry.data.get(
        CONF_PERFORMANCE_RANGES, DEFAULT_PERFORMANCE_RANGES
    )
    coordinator = GhostfolioDataUpdateCoordinator(
        hass, api, update_interval, performance_ranges
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: GhostfolioDataUpdateCoordinator = entry.runtime_data
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await coordinator.api.close()
    return unload_ok




class GhostfolioDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Ghostfolio data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: GhostfolioAPI,
        update_interval_minutes: int,
        performance_ranges: list[str],
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=update_interval_minutes),
        )
        self.api = api
        # Deduplicate while keeping order
        self.ranges = list(dict.fromkeys(performance_ranges or DEFAULT_PERFORMANCE_RANGES))

    async def _async_update_data(self):
        """Fetch data from Ghostfolio API."""
        performance_tasks = [
            self.api.get_portfolio_performance(range_param) for range_param in self.ranges
        ]

        performance_results, user_settings = await asyncio.gather(
            asyncio.gather(*performance_tasks),
            self.api.get_user_settings(),
        )

        base_currency = None
        if isinstance(user_settings, dict):
            base_currency = user_settings.get("settings", {}).get("baseCurrency")

        performance_by_range: dict[str, dict] = {}
        first_order_date = None
        for range_param, result in zip(self.ranges, performance_results, strict=False):
            if not isinstance(result, dict):
                continue

            perf = result.get("performance")
            perf_data = perf if isinstance(perf, dict) else result
            performance_by_range[range_param] = perf_data

            if first_order_date is None:
                first_order_date = result.get("firstOrderDate")

            if base_currency is None:
                if isinstance(perf_data, dict):
                    base_currency = perf_data.get("baseCurrency")

        return {
            "base_currency": base_currency,
            "performance": performance_by_range,
            "firstOrderDate": first_order_date,
        }

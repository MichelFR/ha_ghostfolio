"""Sensor platform for Ghostfolio integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import GhostfolioDataUpdateCoordinator
from .const import CONF_PORTFOLIO_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ghostfolio sensor platform."""
    coordinator = config_entry.runtime_data

    entities = [
        GhostfolioCurrentValueSensor(coordinator, config_entry),
        GhostfolioNetPerformanceSensor(coordinator, config_entry),
        GhostfolioNetPerformancePercentSensor(coordinator, config_entry),
        GhostfolioTotalInvestmentSensor(coordinator, config_entry),
        GhostfolioNetPerformanceWithCurrencySensor(coordinator, config_entry),
        GhostfolioNetPerformancePercentWithCurrencySensor(coordinator, config_entry),
    ]

    async_add_entities(entities)


class GhostfolioBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Ghostfolio sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GhostfolioDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        portfolio_name = config_entry.data.get(CONF_PORTFOLIO_NAME, "Ghostfolio")

        # Use portfolio name in device identifier to ensure uniqueness
        device_id = f"ghostfolio_portfolio_{config_entry.entry_id}"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": f"{portfolio_name} Portfolio",
            "manufacturer": "Ghostfolio",
            "model": "Portfolio Tracker",
        }

    @property
    def base_currency(self) -> str:
        """Return the portfolio base currency, defaulting to EUR."""
        if not self.coordinator.data:
            return "EUR"

        currency = None
        if isinstance(self.coordinator.data, dict):
            currency = self.coordinator.data.get("base_currency")
            if not currency:
                performance = self.coordinator.data.get("performance", {})
                if isinstance(performance, dict):
                    currency = performance.get("baseCurrency")

        return currency or "EUR"


class GhostfolioMonetarySensor(GhostfolioBaseSensor):
    """Base class for monetary Ghostfolio sensors."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2

    @property
    def native_unit_of_measurement(self) -> str:
        """Return native unit of measurement based on base currency."""
        return self.base_currency


class GhostfolioCurrentValueSensor(GhostfolioMonetarySensor):
    """Sensor for current portfolio value."""

    _attr_translation_key = "current_value"

    def __init__(self, coordinator: GhostfolioDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"ghostfolio_current_value_{config_entry.entry_id}"

    @property
    def native_value(self) -> float | None:
        """Return the current portfolio value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("performance", {}).get("currentValueInBaseCurrency")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return None
        
        performance = self.coordinator.data.get("performance", {})
        return {
            "current_net_worth": performance.get("currentNetWorth"),
            "first_order_date": self.coordinator.data.get("firstOrderDate"),
        }


class GhostfolioNetPerformanceSensor(GhostfolioMonetarySensor):
    """Sensor for net performance."""

    _attr_translation_key = "net_performance"

    def __init__(self, coordinator: GhostfolioDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"ghostfolio_net_performance_{config_entry.entry_id}"

    @property
    def native_value(self) -> float | None:
        """Return the net performance."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("performance", {}).get("netPerformance")




class GhostfolioNetPerformancePercentSensor(GhostfolioBaseSensor):
    """Sensor for net performance percentage."""

    _attr_translation_key = "net_performance_percentage"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: GhostfolioDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"ghostfolio_net_performance_percent_{config_entry.entry_id}"

    @property
    def native_value(self) -> float | None:
        """Return the net performance percentage."""
        if not self.coordinator.data:
            return None
        percent_value = self.coordinator.data.get("performance", {}).get("netPerformancePercentage")
        return percent_value * 100 if percent_value is not None else None


class GhostfolioTotalInvestmentSensor(GhostfolioMonetarySensor):
    """Sensor for total investment."""

    _attr_translation_key = "total_investment"

    def __init__(self, coordinator: GhostfolioDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"ghostfolio_total_investment_{config_entry.entry_id}"

    @property
    def native_value(self) -> float | None:
        """Return the total investment."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("performance", {}).get("totalInvestment")


class GhostfolioNetPerformanceWithCurrencySensor(GhostfolioMonetarySensor):
    """Sensor for net performance with currency effect."""

    _attr_translation_key = "net_performance_with_currency"

    def __init__(self, coordinator: GhostfolioDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"ghostfolio_net_performance_with_currency_{config_entry.entry_id}"

    @property
    def native_value(self) -> float | None:
        """Return the net performance with currency effect."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("performance", {}).get("netPerformanceWithCurrencyEffect")


class GhostfolioNetPerformancePercentWithCurrencySensor(GhostfolioBaseSensor):
    """Sensor for net performance percentage with currency effect."""

    _attr_translation_key = "net_performance_percentage_with_currency"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: GhostfolioDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"ghostfolio_net_performance_percent_with_currency_{config_entry.entry_id}"

    @property
    def native_value(self) -> float | None:
        """Return the net performance percentage with currency effect."""
        if not self.coordinator.data:
            return None
        percent_value = self.coordinator.data.get("performance", {}).get("netPerformancePercentageWithCurrencyEffect")
        return percent_value * 100 if percent_value is not None else None

"""Sensor platform for Ghostfolio integration."""
from __future__ import annotations

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
from .const import (
    CONF_PERFORMANCE_RANGES,
    CONF_PORTFOLIO_NAME,
    DEFAULT_PERFORMANCE_RANGES,
    DOMAIN,
)


def _build_unique_id(base: str, range_param: str, entry_id: str) -> str:
    """Build a unique_id, omitting the range for 'max' to keep legacy IDs."""
    if range_param.lower() == "max":
        return f"{base}_{entry_id}"
    return f"{base}_{range_param}_{entry_id}"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ghostfolio sensor platform."""
    coordinator = config_entry.runtime_data

    performance_ranges: list[str] = config_entry.data.get(
        CONF_PERFORMANCE_RANGES, DEFAULT_PERFORMANCE_RANGES
    )

    entities: list[SensorEntity] = [
        GhostfolioCurrentValueSensor(coordinator, config_entry),
        GhostfolioTotalInvestmentSensor(coordinator, config_entry),
    ]
    for range_param in performance_ranges:
        entities.extend(
            [
                GhostfolioNetPerformanceSensor(coordinator, config_entry, range_param),
                GhostfolioNetPerformancePercentSensor(
                    coordinator, config_entry, range_param
                ),
                GhostfolioNetPerformanceWithCurrencySensor(
                    coordinator, config_entry, range_param
                ),
                GhostfolioNetPerformancePercentWithCurrencySensor(
                    coordinator, config_entry, range_param
                ),
            ]
        )

    async_add_entities(entities)


class GhostfolioBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Ghostfolio sensors."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: GhostfolioDataUpdateCoordinator, config_entry: ConfigEntry
    ) -> None:
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
        data = self.coordinator.data
        if isinstance(data, dict):
            currency = data.get("base_currency")
            performance = data.get("performance")
            if not currency and isinstance(performance, dict):
                if isinstance(self, GhostfolioRangeSensor):
                    range_data = performance.get(self.range_param)
                    if isinstance(range_data, dict):
                        currency = range_data.get("baseCurrency")
                if not currency:
                    for perf_data in performance.values():
                        if isinstance(perf_data, dict):
                            currency = perf_data.get("baseCurrency")
                            if currency:
                                break

        return currency or "EUR"

    def _first_performance(self) -> dict[str, Any]:
        """Return the first available performance entry."""
        performance = self.coordinator.data.get("performance", {})
        if isinstance(performance, dict):
            for data in performance.values():
                if isinstance(data, dict):
                    return data
        return {}


class GhostfolioRangeSensor(GhostfolioBaseSensor):
    """Base class for Ghostfolio sensors tied to a specific performance range."""

    def __init__(
        self,
        coordinator: GhostfolioDataUpdateCoordinator,
        config_entry: ConfigEntry,
        range_param: str,
    ) -> None:
        """Initialize the range sensor."""
        super().__init__(coordinator, config_entry)
        self.range_param = range_param
        self.range_label = "" if range_param.lower() == "max" else f"{range_param.upper()} "
        self._attr_translation_placeholders = {"range": self.range_label}

    @property
    def performance_data(self) -> dict[str, Any]:
        """Return performance data for this sensor's range."""
        if not self.coordinator.data:
            return {}

        performance = self.coordinator.data.get("performance", {})
        if isinstance(performance, dict):
            range_data = performance.get(self.range_param)
            if isinstance(range_data, dict):
                return range_data
        return {}


class GhostfolioMonetarySensor(GhostfolioRangeSensor):
    """Base class for monetary Ghostfolio sensors."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2

    @property
    def native_unit_of_measurement(self) -> str:
        """Return native unit of measurement based on base currency."""
        return self.base_currency


class GhostfolioCurrentValueSensor(GhostfolioBaseSensor):
    """Sensor for current portfolio value (range-independent)."""

    _attr_translation_key = "current_value"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: GhostfolioDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"ghostfolio_current_value_{config_entry.entry_id}"

    @property
    def native_unit_of_measurement(self) -> str:
        """Return native unit of measurement based on base currency."""
        return self.base_currency

    @property
    def native_value(self) -> float | None:
        """Return the current portfolio value."""
        performance = self._first_performance()
        return performance.get("currentValueInBaseCurrency")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        performance = self._first_performance()
        if not performance:
            return None

        return {
            "current_net_worth": performance.get("currentNetWorth"),
            "first_order_date": self.coordinator.data.get("firstOrderDate"),
        }


class GhostfolioNetPerformanceSensor(GhostfolioMonetarySensor):
    """Sensor for net performance."""

    _attr_translation_key = "net_performance"

    def __init__(
        self,
        coordinator: GhostfolioDataUpdateCoordinator,
        config_entry: ConfigEntry,
        range_param: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, range_param)
        self._attr_unique_id = _build_unique_id(
            "ghostfolio_net_performance", range_param, config_entry.entry_id
        )

    @property
    def native_value(self) -> float | None:
        """Return the net performance."""
        performance = self.performance_data
        return performance.get("netPerformance")


class GhostfolioNetPerformancePercentSensor(GhostfolioRangeSensor):
    """Sensor for net performance percentage."""

    _attr_translation_key = "net_performance_percentage"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: GhostfolioDataUpdateCoordinator,
        config_entry: ConfigEntry,
        range_param: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, range_param)
        self._attr_unique_id = _build_unique_id(
            "ghostfolio_net_performance_percent", range_param, config_entry.entry_id
        )

    @property
    def native_value(self) -> float | None:
        """Return the net performance percentage."""
        percent_value = self.performance_data.get("netPerformancePercentage")
        return percent_value * 100 if percent_value is not None else None


class GhostfolioTotalInvestmentSensor(GhostfolioBaseSensor):
    """Sensor for total investment (range-independent)."""

    _attr_translation_key = "total_investment"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: GhostfolioDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"ghostfolio_total_investment_{config_entry.entry_id}"

    @property
    def native_unit_of_measurement(self) -> str:
        """Return native unit of measurement based on base currency."""
        return self.base_currency

    @property
    def native_value(self) -> float | None:
        """Return the total investment."""
        performance = self._first_performance()
        return performance.get("totalInvestment")


class GhostfolioNetPerformanceWithCurrencySensor(GhostfolioMonetarySensor):
    """Sensor for net performance with currency effect."""

    _attr_translation_key = "net_performance_with_currency"

    def __init__(
        self,
        coordinator: GhostfolioDataUpdateCoordinator,
        config_entry: ConfigEntry,
        range_param: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, range_param)
        self._attr_unique_id = _build_unique_id(
            "ghostfolio_net_performance_with_currency",
            range_param,
            config_entry.entry_id,
        )

    @property
    def native_value(self) -> float | None:
        """Return the net performance with currency effect."""
        performance = self.performance_data
        return performance.get("netPerformanceWithCurrencyEffect")


class GhostfolioNetPerformancePercentWithCurrencySensor(GhostfolioRangeSensor):
    """Sensor for net performance percentage with currency effect."""

    _attr_translation_key = "net_performance_percentage_with_currency"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: GhostfolioDataUpdateCoordinator,
        config_entry: ConfigEntry,
        range_param: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry, range_param)
        self._attr_unique_id = _build_unique_id(
            "ghostfolio_net_performance_percent_with_currency",
            range_param,
            config_entry.entry_id,
        )

    @property
    def native_value(self) -> float | None:
        """Return the net performance percentage with currency effect."""
        percent_value = self.performance_data.get(
            "netPerformancePercentageWithCurrencyEffect"
        )
        return percent_value * 100 if percent_value is not None else None

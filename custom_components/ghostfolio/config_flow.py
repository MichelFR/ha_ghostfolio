"""Config flow for Ghostfolio integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries

from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import GhostfolioAPI
from .const import (
    CONF_ACCESS_TOKEN, 
    CONF_BASE_URL, 
    CONF_PORTFOLIO_NAME,
    CONF_VERIFY_SSL, 
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)


class GhostfolioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ghostfolio."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Test the connection
            api = GhostfolioAPI(
                base_url=user_input[CONF_BASE_URL],
                access_token=user_input[CONF_ACCESS_TOKEN],
                verify_ssl=user_input.get(CONF_VERIFY_SSL, True),
            )

            try:
                # Test authentication
                auth_token = await api.authenticate()
                if auth_token:
                    # Test portfolio access
                    await api.get_portfolio_performance()
                    
                    # Set unique ID based on base URL and portfolio name
                    portfolio_name = user_input.get(CONF_PORTFOLIO_NAME, "Ghostfolio")
                    unique_id = f"{user_input[CONF_BASE_URL]}_{portfolio_name}".replace(" ", "_").lower()
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=user_input[CONF_PORTFOLIO_NAME],
                        data=user_input,
                    )
                else:
                    errors["base"] = "auth_failed"
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PORTFOLIO_NAME, default="Ghostfolio"): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT,
                        )
                    ),
                    vol.Required(CONF_BASE_URL): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.URL,
                        )
                    ),
                    vol.Required(CONF_ACCESS_TOKEN): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.PASSWORD,
                        )
                    ),
                    vol.Optional(CONF_VERIFY_SSL, default=True): BooleanSelector(),
                    vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): NumberSelector(
                        NumberSelectorConfig(
                            mode=NumberSelectorMode.BOX,
                            min=1,
                            max=1440,  # Max 24 hours
                            unit_of_measurement="minutes",
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of the integration."""
        config_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            # Test the connection with new settings
            api = GhostfolioAPI(
                base_url=user_input[CONF_BASE_URL],
                access_token=user_input[CONF_ACCESS_TOKEN],
                verify_ssl=user_input.get(CONF_VERIFY_SSL, True),
            )

            try:
                # Test authentication
                auth_token = await api.authenticate()
                if auth_token:
                    # Test portfolio access
                    await api.get_portfolio_performance()
                    
                    # Set unique ID based on base URL and portfolio name to check for conflicts
                    portfolio_name = user_input.get(CONF_PORTFOLIO_NAME, "Ghostfolio")
                    unique_id = f"{user_input[CONF_BASE_URL]}_{portfolio_name}".replace(" ", "_").lower()
                    await self.async_set_unique_id(unique_id)
                    # Only abort if the unique ID belongs to a different entry
                    self._abort_if_unique_id_mismatch(reason="wrong_account")

                    # Update the configuration entry
                    return self.async_update_reload_and_abort(
                        config_entry,
                        data_updates=user_input,
                    )
                else:
                    errors["base"] = "auth_failed"
            except Exception as ex:
                _LOGGER.exception("Unexpected exception during reconfiguration: %s", ex)
                errors["base"] = "cannot_connect"

        # Pre-fill the form with current values
        current_data = config_entry.data
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_PORTFOLIO_NAME, default="Ghostfolio"): TextSelector(
                            TextSelectorConfig(
                                type=TextSelectorType.TEXT,
                            )
                        ),
                        vol.Required(CONF_BASE_URL): TextSelector(
                            TextSelectorConfig(
                                type=TextSelectorType.URL,
                            )
                        ),
                        vol.Required(CONF_ACCESS_TOKEN): TextSelector(
                            TextSelectorConfig(
                                type=TextSelectorType.PASSWORD,
                            )
                        ),
                        vol.Optional(CONF_VERIFY_SSL, default=True): BooleanSelector(),
                        vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): NumberSelector(
                            NumberSelectorConfig(
                                mode=NumberSelectorMode.BOX,
                                min=1,
                                max=1440,  # Max 24 hours
                                unit_of_measurement="minutes",
                            )
                        ),
                    }
                ),
                current_data,
            ),
            errors=errors,
        )
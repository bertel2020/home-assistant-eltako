"""Config flows for the Eltako integration."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE

from . import gateway
from .const import DOMAIN, ERROR_INVALID_GATEWAY_PATH, LOGGER


class EltakoFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Eltako config flows."""

    VERSION = 1
    MANUAL_PATH_VALUE = "Custom path"

    def __init__(self) -> None:
        """Initialize the Eltako config flow."""
        self.gateway_path = None
        self.discovery_info = None

    async def async_step_import(self, data=None):
        """Import a yaml configuration."""

        if not await self.validate_eltako_conf(data):
            LOGGER.warning(
                "Cannot import yaml configuration: %s is not a valid gateway path",
                data[CONF_DEVICE],
            )
            return self.async_abort(reason="invalid_gateway_path")

        return self.create_eltako_entry(data)

    async def async_step_user(self, user_input=None):
        """Handle an Eltako config flow start."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return await self.async_step_detect()

    async def async_step_detect(self, user_input=None):
        """Propose a list of detected gateways."""
        errors = {}
        if user_input is not None:
            if user_input[CONF_DEVICE] == self.MANUAL_PATH_VALUE:
                return await self.async_step_manual(None)
            if await self.validate_eltako_conf(user_input):
                return self.create_eltako_entry(user_input)
            errors = {CONF_DEVICE: ERROR_INVALID_GATEWAY_PATH}

        bridges = await self.hass.async_add_executor_job(gateway.detect)
        if len(bridges) == 0:
            return await self.async_step_manual(user_input)

        bridges.append(self.MANUAL_PATH_VALUE)
        return self.async_show_form(
            step_id="detect",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(bridges)}),
            errors=errors,
        )

    async def async_step_manual(self, user_input=None):
        """Request manual USB gateway path."""
        default_value = None
        errors = {}
        if user_input is not None:
            if await self.validate_eltako_conf(user_input):
                return self.create_eltako_entry(user_input)
            default_value = user_input[CONF_DEVICE]
            errors = {CONF_DEVICE: ERROR_INVALID_GATEWAY_PATH}

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {vol.Required(CONF_DEVICE, default=default_value): str}
            ),
            errors=errors,
        )

    async def validate_eltako_conf(self, user_input) -> bool:
        """Return True if the user_input contains a valid gateway path."""
        gateway_path = user_input[CONF_DEVICE]
        path_is_valid = await self.hass.async_add_executor_job(
            gateway.validate_path, gateway_path
        )
        return path_is_valid

    def create_eltako_entry(self, user_input):
        """Create an entry for the provided configuration."""
        return self.async_create_entry(title="Eltako", data=user_input)
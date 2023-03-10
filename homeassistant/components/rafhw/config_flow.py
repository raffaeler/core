"""Config flow for rafesp integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import format_mac

from .const import CONF_HOST, CONF_MAC, CONF_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

## adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host

    async def authenticate(self, username: str, password: str) -> bool:
        """Test if we can authenticate with the host."""
        return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    ## validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    hub = PlaceholderHub(data["host"])

    if not await hub.authenticate(data["username"], data["password"]):
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Name of the device"}


# https://developers.home-assistant.io/docs/config_entries_config_flow_handler/
# activate integration: python3 -m script.hassfest
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for rafesp."""

    VERSION = 1

    mac: str | None = None
    port: int | None = None
    host: str
    title: str

    def __init__(self) -> None:
        """Initialize some variables."""
        self.mac = ""
        self.host = ""
        self.port = 80
        self.title = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Entry point for the zeroconf discovery."""
        _LOGGER.warning("Call to async_step_zeroconf: '%s'", discovery_info)
        mac = discovery_info.properties.get("mac")
        if mac is None:
            return self.async_abort(reason="mdns_missing_mac")

        self.mac = format_mac(mac)
        self.host = discovery_info.host
        self.port = discovery_info.port
        # return await self.async_step_confirm(self)
        return await self.async_step_zeroconf_finalize()

    # async def async_step_confirm(self, _: dict[str, Any] | None = None) -> FlowResult:
    #     """Finalize the configuration."""
    #     _LOGGER.warning("Call to async_step_confirm: '%s'", self.host)
    #     return self.async_show_form(
    #         step_id="discovery_confirm", description_placeholders={"name": "rafesp"}
    #     )

    async def async_step_zeroconf_finalize(
        self, _: dict[str, Any] | None = None
    ) -> FlowResult:
        """Finalize the entry."""

        self._abort_if_unique_id_configured()
        await self.async_set_unique_id(self.mac)
        return self.async_create_entry(
            title=self.host,
            data={
                CONF_MAC: self.mac,
                CONF_HOST: self.host,
                CONF_PORT: self.port,
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

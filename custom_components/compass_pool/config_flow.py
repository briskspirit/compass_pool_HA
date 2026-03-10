"""Config flow for Compass WiFi Pool Heater."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD

from .api import CompassApi, CompassAuthError, CompassApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class CompassPoolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Compass WiFi Pool Heater."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step - user enters credentials."""
        errors = {}

        if user_input is not None:
            api = CompassApi(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
            try:
                await api.login()
                devices = await api.get_devices()
            except CompassAuthError:
                errors["base"] = "invalid_auth"
            except CompassApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"Compass Pool ({user_input[CONF_USERNAME]})",
                        data=user_input,
                    )
            finally:
                await api.close()

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

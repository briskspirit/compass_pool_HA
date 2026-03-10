"""Climate platform for Compass WiFi Pool Heater."""

import logging
import time
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    COMPRESSOR_RUNNING,
    DOMAIN,
    FIELD_HEAT_SETPOINT,
    FIELD_MAX_HEAT,
    FIELD_MIN_HEAT,
    FIELD_MODE,
    FIELD_WATER_TEMP,
    FIELD_FAULT_STATUS,
    FIELD_COMPRESSOR,
    MODE_OFF,
    MODE_POOL_HEAT,
    STATUS_HEATING_ACTIVE,
)
from .coordinator import CompassCoordinator

_LOGGER = logging.getLogger(__name__)

# How long to trust optimistic values over cloud data (seconds).
# The device takes ~30-40s to sync with the cloud, so we hold the
# optimistic value for 90s to avoid the UI reverting on stale polls.
OPTIMISTIC_HOLD_SECONDS = 90


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up climate entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for key, coordinator in data["coordinators"].items():
        entities.append(CompassClimateEntity(coordinator, data["api"]))
    async_add_entities(entities)


class CompassClimateEntity(CoordinatorEntity, ClimateEntity):
    """Climate entity for a Compass WiFi pool heat pump."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_target_temperature_step = 1.0
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: CompassCoordinator, api) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{coordinator.thermostat_key}_climate"
        # Optimistic state: {field: (value, timestamp)}
        self._optimistic: dict[str, tuple[Any, float]] = {}

    @property
    def device_info(self) -> DeviceInfo:
        info = self.coordinator.device_info
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.thermostat_key)},
            name=info.get("name", "Compass Pool Heater"),
            manufacturer="ICM Controls / Gulfstream",
            model=info.get("model_name", "ICM_POOL_AND_SPA"),
        )

    @property
    def _state(self) -> dict:
        if self.coordinator.data:
            return self.coordinator.data.get("currentState", {})
        return {}

    def _int(self, field: str, default: int = 0) -> int:
        """Get field value, preferring recent optimistic values."""
        # Check optimistic value first
        if field in self._optimistic:
            val, ts = self._optimistic[field]
            if time.monotonic() - ts < OPTIMISTIC_HOLD_SECONDS:
                return int(val)
            del self._optimistic[field]

        val = self._state.get(field)
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def _set_optimistic(self, field: str, value: Any) -> None:
        self._optimistic[field] = (value, time.monotonic())

    @property
    def current_temperature(self) -> float | None:
        val = self._state.get(FIELD_WATER_TEMP)
        return float(val) if val is not None else None

    @property
    def target_temperature(self) -> float | None:
        md = self._int(FIELD_MODE)
        if md == MODE_POOL_HEAT:
            return float(self._int(FIELD_HEAT_SETPOINT))
        return None

    @property
    def min_temp(self) -> float:
        return float(self._int(FIELD_MIN_HEAT, 50))

    @property
    def max_temp(self) -> float:
        return float(self._int(FIELD_MAX_HEAT, 104))

    @property
    def hvac_mode(self) -> HVACMode:
        md = self._int(FIELD_MODE)
        if md == MODE_POOL_HEAT:
            return HVACMode.HEAT
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        md = self._int(FIELD_MODE)
        if md == MODE_OFF:
            return HVACAction.OFF

        gen9 = self._int(FIELD_FAULT_STATUS)
        compressor = self._int(FIELD_COMPRESSOR)

        if compressor == COMPRESSOR_RUNNING or (gen9 & STATUS_HEATING_ACTIVE):
            return HVACAction.HEATING

        return HVACAction.IDLE

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        md = MODE_POOL_HEAT if hvac_mode == HVACMode.HEAT else MODE_OFF
        await self._api.set_fields(
            self.coordinator.thermostat_key, {FIELD_MODE: md}
        )
        self._set_optimistic(FIELD_MODE, md)
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if ATTR_TEMPERATURE not in kwargs:
            return
        temp = int(kwargs[ATTR_TEMPERATURE])
        await self._api.set_fields(
            self.coordinator.thermostat_key, {FIELD_HEAT_SETPOINT: temp}
        )
        self._set_optimistic(FIELD_HEAT_SETPOINT, temp)
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

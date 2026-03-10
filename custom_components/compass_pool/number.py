"""Number platform for Compass WiFi Pool Heater (adjustable settings)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    FIELD_DEADBAND,
    FIELD_ANTI_SHORT_CYCLE,
    FIELD_DEFROST_END_TEMP,
    FIELD_EVAP_CALIBRATION,
    FIELD_WATER_CALIBRATION,
)
from .coordinator import CompassCoordinator


@dataclass
class CompassNumberConfig:
    """Configuration for a number entity."""

    key: str
    name: str
    field: str
    min_value: float
    max_value: float
    step: float
    unit: str | None
    icon: str
    offset: int  # Value stored = actual + offset (0 for direct fields)


NUMBER_CONFIGS = [
    CompassNumberConfig(
        key="deadband",
        name="Pool Heat/Cool Deadband",
        field=FIELD_DEADBAND,
        min_value=2,
        max_value=8,
        step=1,
        unit=UnitOfTemperature.FAHRENHEIT,
        icon="mdi:thermometer-lines",
        offset=0,
    ),
    CompassNumberConfig(
        key="anti_short_cycle",
        name="Anti Short Cycle Delay",
        field=FIELD_ANTI_SHORT_CYCLE,
        min_value=0,
        max_value=10,
        step=1,
        unit=UnitOfTime.MINUTES,
        icon="mdi:timer-outline",
        offset=0,
    ),
    CompassNumberConfig(
        key="defrost_end_temp",
        name="Defrost End Temperature",
        field=FIELD_DEFROST_END_TEMP,
        min_value=42,
        max_value=50,
        step=1,
        unit=UnitOfTemperature.FAHRENHEIT,
        icon="mdi:snowflake-thermometer",
        offset=0,
    ),
    CompassNumberConfig(
        key="evap_calibration",
        name="Evap Sensor Calibration",
        field=FIELD_EVAP_CALIBRATION,
        min_value=-10,
        max_value=10,
        step=1,
        unit=UnitOfTemperature.FAHRENHEIT,
        icon="mdi:tune",
        offset=10,  # stored = actual + 10
    ),
    CompassNumberConfig(
        key="water_calibration",
        name="Water Sensor Calibration",
        field=FIELD_WATER_CALIBRATION,
        min_value=-10,
        max_value=10,
        step=1,
        unit=UnitOfTemperature.FAHRENHEIT,
        icon="mdi:tune",
        offset=10,  # stored = actual + 10
    ),
]


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up number entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for key, coordinator in data["coordinators"].items():
        for config in NUMBER_CONFIGS:
            entities.append(
                CompassNumberEntity(coordinator, data["api"], config)
            )
    async_add_entities(entities)


class CompassNumberEntity(CoordinatorEntity, NumberEntity):
    """Adjustable numeric setting for the heat pump."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: CompassCoordinator,
        api,
        config: CompassNumberConfig,
    ) -> None:
        super().__init__(coordinator)
        self._api = api
        self._config = config
        self._attr_name = config.name
        self._attr_unique_id = f"{coordinator.thermostat_key}_{config.key}"
        self._attr_native_min_value = config.min_value
        self._attr_native_max_value = config.max_value
        self._attr_native_step = config.step
        self._attr_native_unit_of_measurement = config.unit
        self._attr_icon = config.icon

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
    def native_value(self) -> float | None:
        state = self.coordinator.data or {}
        cs = state.get("currentState", {})
        val = cs.get(self._config.field)
        if val is None:
            return None
        try:
            raw = int(val)
            return float(raw - self._config.offset)
        except (ValueError, TypeError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        raw = int(value) + self._config.offset
        await self._api.set_fields(
            self.coordinator.thermostat_key, {self._config.field: raw}
        )
        await self.coordinator.async_request_refresh()

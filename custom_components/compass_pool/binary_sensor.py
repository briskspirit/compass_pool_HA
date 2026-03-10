"""Binary sensor platform for Compass WiFi Pool Heater."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    COMPRESSOR_RUNNING,
    DOMAIN,
    FIELD_COMPRESSOR,
    FIELD_FAULT_STATUS,
    STATUS_HEATING_ACTIVE,
)
from .coordinator import CompassCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up binary sensor entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for key, coordinator in data["coordinators"].items():
        entities.extend(
            [
                CompassHeatingActiveSensor(coordinator),
                CompassCompressorRunningSensor(coordinator),
            ]
        )
    async_add_entities(entities)


def _device_info(coordinator: CompassCoordinator) -> DeviceInfo:
    info = coordinator.device_info
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.thermostat_key)},
        name=info.get("name", "Compass Pool Heater"),
        manufacturer="ICM Controls / Gulfstream",
        model=info.get("model_name", "ICM_POOL_AND_SPA"),
    )


class CompassHeatingActiveSensor(CoordinatorEntity, BinarySensorEntity):
    """Heating call is active."""

    _attr_has_entity_name = True
    _attr_name = "Heating Active"
    _attr_icon = "mdi:fire"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: CompassCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.thermostat_key}_heating_active"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)

    @property
    def is_on(self) -> bool:
        state = self.coordinator.data or {}
        cs = state.get("currentState", {})
        val = cs.get(FIELD_FAULT_STATUS, 0)
        try:
            return bool(int(val) & STATUS_HEATING_ACTIVE)
        except (ValueError, TypeError):
            return False


class CompassCompressorRunningSensor(CoordinatorEntity, BinarySensorEntity):
    """Compressor is running."""

    _attr_has_entity_name = True
    _attr_name = "Compressor Running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: CompassCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.thermostat_key}_compressor_running"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)

    @property
    def is_on(self) -> bool:
        state = self.coordinator.data or {}
        cs = state.get("currentState", {})
        rmh = cs.get(FIELD_COMPRESSOR, 0)
        try:
            return int(rmh) == COMPRESSOR_RUNNING
        except (ValueError, TypeError):
            return False

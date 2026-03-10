"""Sensor platform for Compass WiFi Pool Heater."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    FIELD_WATER_TEMP,
    FIELD_COIL_TEMP,
    FIELD_FAULT_STATUS,
    FAULT_EVAP_SENSOR,
    FAULT_WATER_SENSOR,
    FAULT_NO_FLOW,
    FAULT_LOW_PRESSURE,
)
from .coordinator import CompassCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensor entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for key, coordinator in data["coordinators"].items():
        entities.extend(
            [
                CompassTemperatureSensor(
                    coordinator,
                    key="water_temperature",
                    name="Water Temperature",
                    field=FIELD_WATER_TEMP,
                ),
                CompassTemperatureSensor(
                    coordinator,
                    key="coil_temperature",
                    name="Coil Temperature",
                    field=FIELD_COIL_TEMP,
                ),
                CompassFaultSensor(coordinator),
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


class CompassTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Temperature sensor (water or coil)."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT

    def __init__(
        self,
        coordinator: CompassCoordinator,
        key: str,
        name: str,
        field: str,
    ) -> None:
        super().__init__(coordinator)
        self._field = field
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.thermostat_key}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)

    @property
    def native_value(self) -> float | None:
        state = self.coordinator.data or {}
        cs = state.get("currentState", {})
        val = cs.get(self._field)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None


class CompassFaultSensor(CoordinatorEntity, SensorEntity):
    """Shows current fault description or OK."""

    _attr_has_entity_name = True
    _attr_name = "Fault"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: CompassCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.thermostat_key}_fault_status"

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self.coordinator)

    @property
    def native_value(self) -> str:
        state = self.coordinator.data or {}
        cs = state.get("currentState", {})
        gen9 = cs.get(FIELD_FAULT_STATUS, 0)
        try:
            gen9 = int(gen9)
        except (ValueError, TypeError):
            return "Unknown"

        faults = []
        if gen9 & FAULT_EVAP_SENSOR:
            faults.append("Evap sensor malfunction")
        if gen9 & FAULT_WATER_SENSOR:
            faults.append("Water sensor malfunction")
        if gen9 & FAULT_NO_FLOW:
            faults.append("No flow")
        if gen9 & FAULT_LOW_PRESSURE:
            faults.append("Low pressure switch")

        return ", ".join(faults) if faults else "OK"

    @property
    def icon(self) -> str:
        if self.native_value == "OK":
            return "mdi:check-circle-outline"
        return "mdi:alert-circle"

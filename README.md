# Compass WiFi Pool Heater - Home Assistant Integration

Custom Home Assistant integration for Compass WiFi / Gulfstream / ICM Controls pool and spa heat pumps that use the [CapTouch WiFi](https://www.captouchwifi.com) cloud service.

## Features

- **Climate control** — Turn heat pump on/off and adjust temperature setpoint
- **Live sensors** — Water temperature, coil temperature
- **Diagnostics** — Fault status (no flow, sensor failures, low pressure), heating active, compressor running
- **Adjustable settings** — Deadband, anti short cycle delay, defrost end temperature, sensor calibration offsets

## Installation

1. Copy the `custom_components/compass_pool` directory into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings > Devices & Services > Add Integration**
4. Search for **Compass WiFi Pool Heater**
5. Enter your Compass WiFi / CapTouch account credentials

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| Climate | `climate` | On/Off, Heat mode, temperature setpoint, current water temp |
| Water Temperature | `sensor` | Live water temperature (°F) |
| Coil Temperature | `sensor` | Live coil/evaporator temperature (°F) |
| Fault | `sensor` | Current fault description ("OK", "No flow", etc.) |
| Heating Active | `binary_sensor` | Whether a heating call is in progress |
| Compressor Running | `binary_sensor` | Whether the compressor is running |
| Deadband | `number` | Pool heat/cool deadband (2-8°F) |
| Anti Short Cycle Delay | `number` | Compressor short cycle protection (0-10 min) |
| Defrost End Temperature | `number` | Temperature to end defrost cycle (42-50°F) |
| Evap Sensor Calibration | `number` | Evaporator sensor offset (-10 to +10°F) |
| Water Sensor Calibration | `number` | Water sensor offset (-10 to +10°F) |

## API Documentation

See [API_ANALYSIS.md](API_ANALYSIS.md) for the full reverse-engineered API protocol documentation, including all device register fields and their meanings.

## Notes

- The integration polls the cloud API every 30 seconds
- After changing settings, the device takes ~30-40 seconds to sync with the cloud. The UI uses optimistic updates so changes appear instantly
- Token-based authentication with automatic re-auth on expiry
- Tested with the ICM_POOL_AND_SPA model (Gulfstream heat pumps)

## Credits

API protocol reverse-engineered from the Compass WiFi Heat Pump Navigator Android app (com.icmcontrols.gulfstream).

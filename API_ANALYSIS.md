# Compass WiFi Heat Pump - API Reverse Engineering Analysis

## Cloud API Endpoint

**Base URL:** `https://www.captouchwifi.com/icm/api/call`

All API calls go through this single endpoint as HTTP POST requests with JSON payloads.

### Authentication

```bash
curl -X POST 'https://www.captouchwifi.com/icm/api/call' \
  -H 'Content-Type: application/json;charset=utf-8' \
  -d '{"action":"login","username":"YOUR_USER","password":"YOUR_PASS"}'
```

**Response:**
```json
{
  "action": "login",
  "username": "YOUR_USER",
  "password": "********",
  "result": "success",
  "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

The token is a 32-char hex string used in all subsequent requests.

---

## Tested & Verified API Actions

### 1. Login

```json
{"action": "login", "username": "...", "password": "..."}
```

### 2. List Devices (`getPasDevices`)

```json
{"action": "getPasDevices", "token": "...", "additionalFields": "special parameter holder"}
```

**Response:**
```json
{
  "action": "getPasDevices",
  "modelIDs": [5],
  "result": "success",
  "devices": [
    {
      "id": "XXXXX",
      "unique_key": "0000CPXXXXXX",
      "name": "pool heater",
      "description": "pool heater",
      "model_name": "ICM_POOL_AND_SPA",
      "zipcode": "XXXXX",
      "owned": "1",
      "owner": "YOUR_USER",
      "online": "1",
      "groups": []
    }
  ]
}
```

### 3. Get Device Status (`thermostatGetDetail`)

```json
{"action": "thermostatGetDetail", "thermostatKey": "0000CPXXXXXX", "token": "..."}
```

**Response** (abbreviated - full response has 180+ fields):
```json
{
  "result": "success",
  "detail": {
    "id": "XXXXX",
    "unique_key": "0000CPXXXXXX",
    "name": "pool heater",
    "model_id": "5",
    "zipcode": "XXXXX",
    "last_online": "2026-03-10 00:11:43",
    "server_time": "2026-03-10 00:11:47",
    "currentState": {
      "MD": 0,          // Operating mode (0=Off, 1=Pool Heat)
      "RSV1": 86,       // Heat setpoint (°F)
      "RMT": 82,        // Water temperature (°F, live sensor)
      "GEN15": 80,      // Coil temperature (°F, live sensor)
      "GEN9": 4,        // Fault/status register (bitfield, see below)
      "RMH": 0,         // Compressor status (0=off, 128=running)
      "HTS": 10,        // Evap sensor calibration (offset-10: actual = value - 10)
      "DB": 10,         // Water sensor calibration (offset-10: actual = value - 10)
      "CAL": 2,         // Anti short cycle delay (minutes)
      "AXD": 50,        // Defrost end temperature (°F)
      "DFU": 2,         // Pool heat/cool deadband (°F)
      "MXH": 104,       // Max heat setpoint limit (°F)
      "MNH": 50,        // Min heat setpoint limit (°F)
      "LKD": 0,         // Locked (0=unlocked, 1=locked)
      "...": "180+ fields total"
    }
  }
}
```

### 4. Set Device Fields (`thermostatSetFields`)

```json
{"action": "thermostatSetFields", "thermostatKey": "0000CPXXXXXX", "token": "...", "fields": {"MD": "0"}}
```

The `fields` parameter is a JSON object with field names as keys and string values.

### 5. Get Alerts (`thermostatGetAlerts`)

```json
{"action": "thermostatGetAlerts", "thermostatKey": "0000CPXXXXXX", "token": "..."}
```

### 6. Get Alert Method (`thermostatGetAlertMethod`)

```json
{"action": "thermostatGetAlertMethod", "thermostatKey": "0000CPXXXXXX", "token": "..."}
```

**Response:**
```json
{"result": "success", "email": 0, "mobile": 0, "text": 0}
```

### 7. Get Shared Users (`thermostatGetShareWith`)

```json
{"action": "thermostatGetShareWith", "thermostatKey": "0000CPXXXXXX", "token": "..."}
```

---

## Untested Actions (from reverse engineering)

| Action | Parameters | Description |
|--------|-----------|-------------|
| `createUser` | `username`, `password`, `name`, `email` | Sign up |
| `accountChangeEmail` | `token`, `username`, `newPassword`, `oldPassword` | Change email |
| `accountChangePassword` | `token`, `username`, `password`, `email` | Change password |
| `accountResetPassword` | `systemToken`, `email` | Request password reset |
| `accountForgetUserName` | `systemToken`, `email`, `username` | Recover username |
| `addThermostat` | `thermostatKey`, `zipcode`, `name`, `description`, `token` | Add device |
| `removeThermostat` | `thermostatKey`, `token` | Remove device |
| `thermostatSetProfile` | `thermostatKey`, `name`, `description`, `zipcode`, `token` | Update profile |
| `thermostatSetModeData` | `thermostatKey`, `token`, `modeData` | Set mode + schedule data |
| `thermostatSetBlock` | `thermostatKey`, `token`, `startAddress`, `length`, `data` | Write register block |
| `thermostatSetAlert` | `thermostatKey`, `token`, `alertType`, `value`, `enabled` | Set alert |
| `thermostatSetAlertMethod` | `thermostatKey`, `token`, `email`, `mobile`, `text` | Set alert method |
| `thermostatSetShareWith` | `thermostatKey`, `token`, `shareWith` | Share control |

---

## Device Field Reference (Verified by Live Testing)

### Live Sensor Readings

| Field | Example | Description |
|-------|---------|-------------|
| `RMT` | 81 | **Water temperature** (°F) |
| `GEN15` | 80 | **Coil temperature** (°F) |
| `GEN9` | 20 | **Fault/status register** (bitfield, see below) |
| `RMH` | 0 | **Compressor status** (0=off, 128=running) |

### Status/Fault Bitfield (`GEN9`)

| Bit | Value | Meaning | Verified |
|-----|-------|---------|----------|
| 0 | 1 | Evap. sensor malfunction | From app code |
| 1 | 2 | Water sensor malfunction | From app code |
| 2 | 4 | No flow | Yes (present when pump off, clears when pump on) |
| 3 | 8 | Low pressure switch | From app code |
| 4 | 16 | Heating call active | Yes (present when MD=1, clears on MD=0) |

Example: `GEN9 = 20` = 16 + 4 = heating active + no flow.
Example: `GEN9 = 0` = no faults, not heating.

### Mode & Setpoint

| Field | Example | Description |
|-------|---------|-------------|
| `MD` | 1 | **Operating mode** (0=Off, 1=Pool Heat) |
| `RSV1` | 86 | **Heat setpoint** (°F) — set to 86, confirmed field changed 85→86 |

### Operational Settings

| Field | Example | Description | Encoding |
|-------|---------|-------------|----------|
| `DFU` | 2 | **Pool Heat/Cool Deadband** (°F) | Direct (changed 2→3→2) |
| `CAL` | 2 | **Anti Short Cycle Delay** (minutes) | Direct (changed 2→4→2) |
| `AXD` | 50 | **Defrost End Temperature** (°F) | Direct (changed 50→48→50) |
| `HTS` | 10 | **Evap Sensor Calibration** (°F) | actual = value - 10 (0°F=10, -1°F=9) |
| `DB` | 10 | **Water Sensor Calibration** (°F) | actual = value - 10 (0°F=10, -2°F=8) |

### Device Limits

| Field | Value | Description |
|-------|-------|-------------|
| `MXH` | 104 | Max heat setpoint limit (°F) |
| `MNH` | 50 | Min heat setpoint limit (°F) |

### Field Encoding Notes

- **Calibration fields use offset encoding:** stored value = actual + 10. So -5°F is stored as 5, 0°F as 10, +5°F as 15.
  - `HTS` = evap sensor calibration (actual = HTS - 10)
  - `DB` = water sensor calibration (actual = DB - 10)
- **All other verified fields** are direct values (no conversion needed)

---

## Home Assistant Integration

### Minimal Required API Calls

1. **Login:** `{"action":"login","username":"...","password":"..."}` → get `token`
2. **List devices:** `{"action":"getPasDevices","token":"...","additionalFields":"special parameter holder"}` → get `unique_key` for each device
3. **Poll status:** `{"action":"thermostatGetDetail","thermostatKey":"<unique_key>","token":"..."}` → full state in `detail.currentState`
4. **Set mode:** `{"action":"thermostatSetFields","thermostatKey":"<unique_key>","token":"...","fields":{"MD":"<value>"}}`
5. **Set setpoint:** `{"action":"thermostatSetFields","thermostatKey":"<unique_key>","token":"...","fields":{"RSV1":"<temp>"}}`

### Notes

- All communication is simple HTTP POST with JSON
- Token appears to be long-lived (no expiry mechanism visible)
- Device takes ~30-40 seconds to sync changes with the cloud
- `thermostatKey` = `unique_key` from device list (format: `0000CP######`)
- The `additionalFields` parameter for `getPasDevices` must be the literal string `"special parameter holder"`
- Field names in the API are **register abbreviations**, not semantic names (e.g., `RMT` = water temp, not "Remote TSTAT")

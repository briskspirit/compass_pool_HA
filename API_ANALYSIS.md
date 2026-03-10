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
      "HTS": 10,        // Evap sensor calibration (offset-10: actual = value - 10)
      "DB": 10,         // Water sensor calibration (offset-10: actual = value - 10)
      "LCS": 47,        // Unknown live reading (changes frequently)
      "FLT": 0,         // Fault code (0 = no fault)
      "LKD": 0,         // Locked (0=unlocked, 1=locked)
      "CF": 0,          // Config flags
      "RMT": 82,        // Water temperature (°F, live sensor)
      "FAN": 0,         // Fan mode
      "SCH": 0,         // Schedule mode
      "CAL": 2,         // Anti short cycle delay (minutes)
      "AXD": 50,        // Defrost end temperature (°F)
      "MXH": 104,       // Max heat setpoint limit (°F)
      "MNH": 50,        // Min heat setpoint limit (°F)
      "CYC": 0,         // Cycle
      "DFG": 0,         // Defrost group/mode
      "DF1": 0,         // Defrost setting 1
      "DF2": 0,         // Defrost setting 2
      "DF3": 0,         // Defrost setting 3
      "DFU": 2,         // Pool heat/cool deadband (°F)
      "DFL": 1,         // Defrost level
      "MODEL1": 57,     // Model info byte 1
      "MODEL2": 48,     // Model info byte 2
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

| Field | Example | Description | Verified |
|-------|---------|-------------|----------|
| `RMT` | 81 | **Water temperature** (°F, live sensor) | Yes - matches app |
| `GEN15` | 80 | **Coil temperature** (°F, live sensor) | Yes - matches app |
| `LCS` | 51 | **Unknown live reading** (changes frequently, not displayed in app) | Observed changing |
| `GEN9` | 20 | **Fault register** (bitfield, see below) | Yes - 4=no flow confirmed |
| `GEN13` | 16 | **Status flag** - appeared as 16 when mode turned ON | Observed |

### Status/Fault Bitfield (`GEN9`)

| Bit | Value | Meaning | Type | Verified |
|-----|-------|---------|------|----------|
| 0 | 1 | Evap. sensor malfunction | Fault | From app code |
| 1 | 2 | Water sensor malfunction | Fault | From app code |
| 2 | 4 | No flow | Fault | Yes (present when pump off, clears when pump on) |
| 3 | 8 | Low pressure switch | Fault | From app code |
| 4 | 16 | Heating call active | Status | Yes (present when MD=1, clears on MD=0) |

Example: `GEN9 = 20` = 16 + 4 = heating active + no flow.
Example: `GEN9 = 0` = no faults, not heating.

### Compressor Status (`RMH`)

| Value | Meaning | Verified |
|-------|---------|----------|
| 0 | Compressor off | Yes |
| 128 | Compressor running | Yes |

### Mode & Setpoint

| Field | Example | Description | Verified |
|-------|---------|-------------|----------|
| `MD` | 1 | **Operating mode** | Yes |
| `RSV1` | 86 | **Heat setpoint** (°F) | Yes - set to 86, field changed 85→86 |
| `RSV2` | 85 | **Cool setpoint** (°F, probable) | Not yet verified |

**Mode values (`MD`):**

| Value | Mode | Verified |
|-------|------|----------|
| 0 | Off | Yes |
| 1 | Pool Heat | Yes |
| 2 | Pool Cool (?) | Not yet |
| 3 | Pool Heat/Cool (?) | Not yet |
| 4 | Spa (?) | Not yet |

### Operational Settings

| Field | Example | Description | Encoding | Verified |
|-------|---------|-------------|----------|----------|
| `DFU` | 2 | **Pool Heat/Cool Deadband** (°F) | Direct | Yes (changed 2→3→2) |
| `CAL` | 2 | **Anti Short Cycle Delay** (minutes) | Direct | Yes (changed 2→4→2) |
| `AXD` | 50 | **Defrost End Temperature** (°F) | Direct | Yes (changed 50→48→50) |
| `HTS` | 10 | **Evap Sensor Calibration** (°F) | actual = value - 10 | Yes (0°F=10, -1°F=9) |
| `DB` | 10 | **Water Sensor Calibration** (°F) | actual = value - 10 | Yes (0°F=10, -2°F=8) |
| `LKD` | 0 | **Locked** (0=unlocked, 1=locked) | Direct | From app code |
| `FAN` | 0 | **Fan** mode | Direct | From app code |
| `SCH` | 0 | **Schedule** mode | Direct | From app code |
| `CF` | 0 | **Config** flags | Direct | From app code |

### Device Limits

| Field | Value | Description |
|-------|-------|-------------|
| `MXH` | 104 | Max heat setpoint limit (°F) |
| `MNH` | 50 | Min heat setpoint limit (°F) |

### Defrost Fields

| Field | Value | Description |
|-------|-------|-------------|
| `DFG` | 0 | Defrost group/mode |
| `DF1` | 0 | Defrost setting 1 |
| `DF2` | 0 | Defrost setting 2 |
| `DF3` | 0 | Defrost setting 3 |
| `STOF` | 1 | (related to DF3) |
| `DFL` | 1 | Defrost level |

### Other Non-Zero Fields

| Field | Value | Notes |
|-------|-------|-------|
| `GEN5` | 41 | Stable, unknown |
| `GEN10` | 255 | Likely bitmask/all-flags-set |
| `HUAC` | 10 | Humidity related (10 = 0 with offset-10 encoding?) |
| `CHGF` | 8 | Change filter interval? |
| `MODEL1-10` | varies | Model identification (57,48,51,1,0,0,0,0,2,3) |

### Schedule Fields (7-day, 4 periods per day)

Day prefixes: `M`=Mon, `T`=Tue, `W`=Wed, `TH`=Thu, `F`=Fri, `SA`=Sat, `SU`=Sun
Period suffixes: `W`=Wake, `L`=Leave, `R`=Return, `S`=Sleep
Value suffixes: `H`=Hour, `M`=Minute, `C`=Cool setpoint, `HT`=Heat setpoint

Example: `MWH`=Monday Wake Hour, `MWM`=Monday Wake Minute, `MWHT`=Monday Wake Heat Temp

### Vacation Fields

| Field | Description |
|-------|-------------|
| `VACST` | Vacation status |
| `VACSY/VACSM/VACSD/VACSH/VACSMI` | Vacation start Year/Month/Day/Hour/Minute |
| `VACEY/VACEM/VACED/VACEH/VACEMI` | Vacation end Year/Month/Day/Hour/Minute |

### Device Info Fields

| Field | Value | Description |
|-------|-------|-------------|
| `MODEL1`-`MODEL10` | 57,48,51,1,0,0,0,0,2,3 | Model identification bytes |
| `MAC1`-`MAC12` | all 0 | MAC address bytes |
| `GEN0`-`GEN17` | various | General purpose registers |
| `CHGF` | 8 | Change filter interval |

### Humidity Fields

| Field | Description |
|-------|-------------|
| `HUNC` | Humidity current |
| `HUAC` | Humidity setpoint |
| `HUDE` | Humidity dehumidify |
| `HUDI` | Humidity display |
| `HUOP` | Humidity operation |
| `HUST` | Humidity status |

### History/Fault Fields

| Field | Description |
|-------|-------------|
| `F100H` | Fault in last 100 hours |
| `F1H` | Fault in last 1 hour |
| `RSFL` | ? |
| `RSWF` | ? |

---

## Home Assistant Integration Summary

### Minimal Required Calls

1. **Login:** `{"action":"login","username":"...","password":"..."}` -> get `token`
2. **List devices:** `{"action":"getPasDevices","token":"...","additionalFields":"special parameter holder"}` -> get `unique_key` for each device
3. **Poll status:** `{"action":"thermostatGetDetail","thermostatKey":"<unique_key>","token":"..."}` -> full state in `detail.currentState`
4. **Set mode:** `{"action":"thermostatSetFields","thermostatKey":"<unique_key>","token":"...","fields":{"MD":"<value>"}}`
5. **Set setpoint:** `{"action":"thermostatSetFields","thermostatKey":"<unique_key>","token":"...","fields":{"RSV1":"<temp>"}}`
6. **Lock/unlock:** `{"action":"thermostatSetFields","thermostatKey":"<unique_key>","token":"...","fields":{"LKD":"1"}}` (or "0")

### Entities to Expose

- **Climate entity:** mode (`MD`), current water temp (`RMT`), heat setpoint (`RSV1`), cool setpoint (`RSV2`?)
- **Sensors:** water temp (`RMT`), coil temp (`GEN15`), last online timestamp
- **Binary sensors:** online status, fault (`GEN9 != 0`), locked (`LKD`)
- **Switches:** lock (`LKD`), schedule (`SCH`)
- **Diagnostics:** fault detail (`GEN9` decoded), deadband (`DFU`), anti-short-cycle (`CAL`), defrost end (`AXD`)

### Field Encoding Notes

- **Calibration fields use offset encoding:** stored value = actual + 10. So -5°F is stored as 5, 0°F as 10, +5°F as 15.
  - `HTS` = evap sensor calibration (actual = HTS - 10)
  - `DB` = water sensor calibration (actual = DB - 10)
  - `HUAC` = possibly humidity calibration (10 = 0 with same offset?)
- **All other fields** appear to be direct values (no conversion needed)

### Notes

- All communication is simple HTTP POST with JSON
- Token appears to be long-lived (no expiry mechanism visible)
- Poll interval: device reports `last_online` vs `server_time` - can detect staleness
- `thermostatKey` = `unique_key` from device list (format: `0000CP######`)
- The `additionalFields` parameter for `getPasDevices` must be the literal string `"special parameter holder"`
- Field names in the API are **register abbreviations**, not semantic names (e.g., `RMT` = water temp, not "Remote TSTAT")

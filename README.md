# Espon Projector Link

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![pre-commit][pre-commit-shield]][pre-commit]
[![Black][black-shield]][black]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Community Forum][forum-shield]][forum]

## Functionality

The platform allows you to control an Epson projector from Home Assistant.

This custom component is designed for Epson Home Cinema Projectors which support TCP sockets. It should work with any Epson projector that supports TCP sockets and ESC/VP21 command protocol. However projectors may not support all the features.

### Supported Features

- Get and set state (on, off, warmup, cooldown)
- Get source list
- Get and set source
- Get and set audio mute
- Get and set auto iris mode
- Get and set color mode
- Get filter hours
- Get lamp hours
- Get current error
- Get horizontal/vertical lens shift, focus, and zoom position (read-only)
- Increase or decrease volume
- Play, pause, or stop media
- Next or previous media

The projector is exposed as a single device with a `media_player` entity plus a `switch` and `sensor`/`select` entities for each supported property you choose to poll. Lens memory, picture memory, and raw commands are exposed as actions on the `media_player` entity. See service documentation at https://github.com/amosyuen/ha-epson-projector-link/blob/main/custom_components/epson_projector_link/services.yaml

Brightness (`BRIGHT`) is intentionally not exposed as an entity: Epson's own command guide doesn't document its accepted value range, and it has been observed returning values well outside a typical 0-100 scale (e.g. 126) on at least one projector, so there's no reliable way to expose a safe control for it.

Lens shift, focus, and zoom are exposed read-only for the same reason: their values are raw internal position/step counts with no documented range, so there's no safe way to offer a `number` entity for setting them. They are only queryable while the projector is powered on and actively projecting (same as other additional properties).

### Settings Memory vs. Lens Position Memory

Epson projectors with a motorized lens generally support two distinct, unrelated memory features, both of which are action-only (there is no way to read back what is currently loaded):

- **Lens Position memory** (`load_lens_memory` action): recalls a saved lens shift/zoom/focus position. 10 slots.
- **Picture/"Advanced" memory** (`load_picture_memory`, `push_picture_memory`, `erase_picture_memory` actions): loads, saves, or deletes a bundle of picture settings (color mode, HDR/dynamic range mode, and similar), i.e. a full picture "profile". This is what the projector's remote calls the "Memory" button. 10 slots.

### Differences from HA Epson Integration

As of September 2022, the main differences with the built in [Home Assistant Epson Integration](https://www.home-assistant.io/integrations/epson/) are:

#### PROS

- Supports push for power state changes
- Support "warmup" and "cooldown" state for projectors
- Queues requests rather than failing if there is an in-flight request
- Supports lens memory
- Supports picture memory
- Supports auto iris mode
- Supports power consumption mode
- Supports source list retrieved from projector instead of static list
- Supports stop media

#### CONS

- Only supports TCP sockets. The HA Epson integration uses HTTP. Developer has mentioned that not all projectors support TCP.

{% if not installed %}

### Differences from the main branch

#### Added

- The projector now registers as a proper Home Assistant **device** (via
  `device_registry.async_get_or_create` and `"integration_type": "device"` in
  the manifest) instead of only showing up as an integration entry.
- New `switch` entity for projector power control.
- New `select` entities for **Auto Iris Mode**, **Color Mode**, and **Power
  Consumption Mode** (created when the corresponding property is enabled in
  "Additional properties to poll").
- New `sensor` entities for **Error** and **Lamp Hours** (diagnostic
  category).
- New read-only `sensor` entities for **Lens Shift Horizontal** (`HLENS`),
  **Lens Shift Vertical** (`LENS`), **Focus** (`FOCUS`), and **Zoom**
  (`ZOOM`), created when the corresponding property is enabled in
  "Additional properties to poll". Exposed read-only (not as `number`
  entities) since Epson doesn't document a value range for them — same
  reasoning as brightness below.
- New `push_picture_memory` and `erase_picture_memory` actions on the
  `media_player` entity, mirroring the existing `load_picture_memory`
  action (`PUSHMEM`/`ERASEMEM`, slots 1-10). These save/delete a bundled
  picture settings profile (color mode, HDR/dynamic range, and similar) —
  the same feature as the projector remote's "Memory" button.
- Support for the projector's **remote password**. When set, it is sent as a
  Password Header (type `0x01`, attribute `0x01`, 16-byte content) on the
  ESC/VP.net CONNECT request, as required by projectors that have a remote
  password configured. Configurable via a new optional `password` field in
  the config flow and options flow. An incorrect or missing password now
  surfaces as a distinct "Invalid authentication" error instead of a generic
  connection failure.

#### Changed

- Replaced the media player's manual `async_track_time_interval` polling with
  two `DataUpdateCoordinator`s — one for power state, one for the other
  polled properties — shared across all entities on the device. Coordinators
  start/stop polling correctly with the config entry lifecycle instead of
  each entity managing its own timers.
- Migrated to the `config_entry.runtime_data` pattern instead of
  `hass.data[DOMAIN]`.
- Fixed a bug where the current input `source` was fetched once but never
  re-polled afterwards (only the source list was refreshed).
- Enabled real `VOLUME_MUTE` support on the media player when mute is polled
  (the code existed previously but the feature flag was never turned on).
- `async_unload_entry` now closes the TCP connection to the projector and
  shuts down both coordinators on unload.
- Bumped minimum supported Home Assistant version to 2024.8 (required for
  `config_entry.runtime_data` and coordinator `config_entry` support).

#### Removed

- Removed the `select_auto_iris_mode`, `select_color_mode`, and
  `select_power_consumption_mode` services — this functionality is now
  exposed as `select` entities instead. `load_lens_memory`,
  `load_picture_memory`, and `send_command` remain as services since they
  take parameters not suited to a single entity.
- Removed the `set_brightness` service and dropped `BRIGHT` (brightness)
  support entirely, including from the underlying `Projector` class. Epson's
  own ESC/VP21 command guide doesn't document its accepted value range, and
  it was observed returning values well outside a plausible 0-100 range
  (e.g. `126`) on real hardware, so there's no reliable way to expose a safe
  control for it.

## Installation

### HACS

1. Install [HACS](https://hacs.xyz/)
2. Go to HACS "Integrations >" section
3. In the lower right click "+ Explore & Download repositories"
4. Search for "Epson Projector Link" and add it
   - HA Restart is not needed since it is configured in UI config flow
5. In the Home Assistant (HA) UI go to "Configuration"
6. Click "Integrations"
7. Click "+ Add Integration"
8. Search for "Epson Projector Link"

### Manual

1. Using the tool of choice open the directory (folder) for your [HA configuration](https://www.home-assistant.io/docs/configuration/) (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `epson_projector_link`.
4. Download _all_ the files from the `custom_components/epson_projector_link/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the Home Assistant (HA) UI go to "Configuration"
8. Click "Integrations"
9. Click "+ Add Integration"
10. Search for "Epson Projector Link"

{% endif %}

## Configuration

Config is done in the HA integrations UI.

Make sure the projector is on if you have not setup your projector to keep network on or are choosing additional properties to poll. Additional properties can only be polled when the projector is on.

### Remote Password

If your projector has a remote password configured (Menu > Network > Network Configuration > Basic > Remote Password), enter it in the "Password" field during setup or from the integration's options. Without it, the projector will refuse the connection.

### Push State

If you want to get push notifications for power state, you must set projector "Standby Mode" to "Standby Mode: Communication On" or some similar state that keeps the network on when off.

Only power state, warnings, and alerts are pushed. All other properties are polled.

### Setup

## Tested Devices

- Epson Home Cinema 5050UB
- Epson EH-TW7400

## Custom Actions

You can send custom actions using the `epson_projector_link.send_command` action. Example action:

```
action: epson_projector_link.send_command
data:
  command: PWR ON
target:
  entity_id: media_player.theater_projector
```

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](https://github.com/amosyuen/ha-epson-projector-link/blob/master/CONTRIBUTING.md)

## Credits

Referred to @pszafer's implementation of epson component https://github.com/pszafer/epson_projector

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[buymecoffee]: https://paypal.me/amosyuen
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/amosyuen/ha-epson-projector-link.svg?style=for-the-badge
[commits]: https://github.com/amosyuen/ha-epson-projector-link/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/amosyuen/ha-epson-projector-link.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40amosyuen-blue.svg?style=for-the-badge
[pre-commit]: https://github.com/pre-commit/pre-commit
[pre-commit-shield]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/amosyuen/ha-epson-projector-link.svg?style=for-the-badge
[releases]: https://github.com/amosyuen/ha-epson-projector-link/releases
[user_profile]: https://github.com/amosyuen

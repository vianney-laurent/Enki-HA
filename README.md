# Enki Integration for Home Assistant

![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg) 
![version](https://img.shields.io/badge/version-v0.1-blue)

A custom component to integrate your Enki Smart Home devices directly into Home Assistant. 
Currently supports **Lights** (On/Off, Brightness, Color Temperature).

This project is a fork and continuation of the original work by [@CyrilP](https://github.com/CyrilP/hass-enki-component).

## Features
- Direct integration via the Enki Cloud API.
- Support for smart lights:
  - Toggle (On/Off)
  - Brightness control
  - Color Temperature control (Kelvin)
- Configuration via the Home Assistant UI (Config Flow).

## Prerequisites
- A working Enki account.
- The email and password used to log into your Enki mobile application.

---

## Installation via HACS (Recommended)

This integration is fully compatible with [HACS](https://hacs.xyz/) (Home Assistant Community Store) as a custom repository.

1. Open Home Assistant and navigate to **HACS** > **Integrations**.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Add the URL of this repository: `https://github.com/vianney-laurent/Enki-HA`
4. Select `Integration` as the Category and click **Add**.
5. Once added, search for **Enki** in HACS and click **Download**.
6. Restart Home Assistant to load the new component.

## Manual Installation

If you prefer not to use HACS:
1. Download this repository as a `.zip` file from GitHub.
2. Unzip it and extract the `custom_components/enki` folder.
3. Copy the `enki` folder into your Home Assistant's `config/custom_components/` directory.
4. Restart Home Assistant.

---

## Configuration

Setting up the Enki integration is entirely done via the Home Assistant graphic interface. No YAML configuration is required.

1. Go to **Settings** > **Devices & Services** > **Integrations**.
2. Click the **+ Add Integration** button in the bottom right corner.
3. Search for **Enki** and select it.
4. Enter your Enki credentials:
   - **Email:** The email address of your Enki account.
   - **Password:** The password of your Enki account.
5. Click **Submit**. Your Enki devices should now be discovered and added as entities in Home Assistant.

---

## Known Limitations / Roadmap
- Currently, only the `light` domain is implemented. Support for switches, covers (shutters), or sensors requires adding new domains to the codebase.
- The component relies on cloud polling (default 10 seconds).

## Troubleshooting & Debugging

If you encounter issues (e.g., devices not responding, authentication errors), you can enable debug logging for this integration to gather more information.

Add the following to your `configuration.yaml` file:

```yaml
logger:
  default: info
  logs:
    custom_components.enki: debug
```

Restart Home Assistant. You should now see detailed connection and API logs from the Enki component in **Settings** > **System** > **Logs**.

## Credits
- Initial API skeleton and light logic by [@CyrilP](https://github.com/CyrilP)
- Enhanced API error handling, UI state syncing, and HACS structure updates by [@vianney-laurent](https://github.com/vianney-laurent)

## License
MIT License. See the `LICENSE` file for details (if available).

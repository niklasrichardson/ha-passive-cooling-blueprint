# Passive Cooling Window Recommendation

A Home Assistant automation blueprint that recommends **when to open** and
**when to close** windows for passive cooling, using nothing more than an
indoor and an outdoor temperature sensor.

When the air outside is meaningfully cooler than a warm room, the blueprint
recommends opening the windows to let that cooler air in. Once the indoor and
outdoor temperatures have converged, it recommends closing them again to keep
the cooler air you captured. You decide what "recommend" means — a phone
notification, a TTS announcement, a light, a script, anything.

> Temperature only. No humidity, no forecasts, no motorised windows. See
> [Limitations](docs/troubleshooting.md#limitations).

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2Fniklasrichardson%2Fha-passive-cooling-blueprint%2Fmain%2Fblueprints%2Fautomation%2Fniklasrichardson%2Fpassive_cooling_window_recommendation.yaml)

---

## Features

- **Open / close recommendations** from one indoor and one outdoor temperature
  sensor — run any action you like (notification, TTS, script, light…).
- **Hysteresis** (separate open/close thresholds) to avoid flapping, a
  **minimum indoor temperature** gate, and a **stability duration** debounce.
- **Optional trend awareness** — close early as the morning warms, keep
  ventilating into the evening cool-down.
- **Global overrides** to tune a whole fleet of rooms from shared helpers.
- **Optional dashboard output** (per-room Open/Closed tiles) plus a
  repeat-notification **latch**.
- No custom integrations; robust handling of unavailable sensors.

## Quick start

New here? Start with the **[Quick start](docs/quickstart.md)** — the shortest
path to a working per-room recommendation.

## Documentation

The full docs live in [`docs/`](docs/README.md):

- **[Quick start](docs/quickstart.md)** — minimal happy path + an add-a-room checklist
- **[Installation](docs/installation.md)** — import the blueprint, one automation per room
- **[How it works](docs/how-it-works.md)** — the algorithm and the science, decision logic, state tracking
- **[Configuration](docs/configuration.md)** — actions, variables, a full example, sensors, °C/°F
- **[Trend awareness](docs/trends.md)** — early close (morning) and evening hold + derivative sensors
- **[Global overrides](docs/global-overrides.md)** — share settings across rooms
- **[Dashboards](docs/dashboards.md)** — recommendation output and native Open/Closed tiles
- **[Setup generator](docs/generator.md)** — a browser tool that writes the helpers/dashboard/automation YAML for your rooms
- **[Testing](docs/testing.md)** — the test rig (sliders, scenarios, scenes)
- **[Troubleshooting & limitations](docs/troubleshooting.md)**

## Development

Validation runs without a Home Assistant instance:

```bash
pip install pyyaml jinja2 yamllint
./scripts/validate.sh
```

See [Testing](docs/testing.md) for what the tests cover and how to exercise the
logic live, and [`CHANGELOG.md`](CHANGELOG.md) for release history.

## Credits

Inspired by Adam Cornforth's
[Dynamic Ventilation blueprint](https://github.com/adamcornforth/ha-open-window-blueprint).
This project is an independent, temperature-only implementation. It is **not** a
fork of, and is **not** officially affiliated with, that project.

## License

[MIT](LICENSE) © 2026 Niklas Richardson

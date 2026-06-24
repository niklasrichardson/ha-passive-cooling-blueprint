# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-24

### Added

- Initial release of the **Passive Cooling Window Recommendation** blueprint
  (`blueprints/automation/niklasrichardson/passive_cooling_window_recommendation.yaml`).
- Recommends opening windows when the room is at or above a configurable minimum
  indoor temperature and the outdoor sensor is at least the open threshold
  cooler.
- Recommends closing windows when the indoor/outdoor difference falls to the
  close threshold or below.
- Separate open and close thresholds for hysteresis to prevent flapping.
- Configurable stability duration (default 5 minutes) via template-trigger
  `for:`.
- Runs actions only when the recommendation changes, using template-trigger edge
  behaviour and no external helper.
- Robust sensor validation with `is_number`: `unknown`, `unavailable`, `none`,
  empty and non-numeric states are never treated as `0`, and no action runs on
  invalid data.
- Generic action selectors for the open and close actions (notifications, TTS,
  scripts, etc.) — no hard-coded notification service.
- Optional additional conditions for the open and close recommendations.
- Variables exposed to actions: `room_name`, `inside_temperature`,
  `outside_temperature`, `temperature_difference`, `minimum_indoor_temperature`,
  `open_threshold`, `close_threshold`, `recommendation`.
- Temperature-sensor entity selectors filtered to `device_class: temperature`,
  number selectors, and a duration selector, organised into input sections.
- Comprehensive `README.md` with import button, per-room setup, action examples,
  Celsius/Fahrenheit guidance, restart behaviour, troubleshooting and
  limitations.
- Validation tooling: `tests/test_blueprint_logic.py` (renders the real trigger
  templates against every specified scenario), `scripts/validate.sh`,
  `.yamllint`, and a `.github/workflows/validate.yml` CI workflow.
- MIT license and credits to Adam Cornforth's Dynamic Ventilation blueprint.

[0.1.0]: https://github.com/niklasrichardson/ha-passive-cooling-blueprint/releases/tag/v0.1.0

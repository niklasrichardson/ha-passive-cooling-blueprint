# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-06-24

### Added

- **Optional trend awareness.** Two new optional inputs accept rate-of-change
  (derivative) sensors for the indoor and outdoor temperatures
  (`inside_temperature_trend`, `outside_temperature_trend`), plus a
  `minimum_convergence_rate` input.
- **Convergence-based early close.** When the indoor/outdoor gap is actively
  closing toward equilibrium (outside catching up faster than the room is
  warming) while inside the hysteresis band, the blueprint now recommends
  closing the windows early to lock in the cooler air before the room warms back
  up — useful as morning temperatures rise.
- New action variables: `inside_trend`, `outside_trend`, `difference_trend`
  (degrees per hour).
- Tests for the trend / early-close behaviour, including the morning
  cold-but-rising case (keeps ventilating) and graceful fallback when a trend
  sensor is invalid or unset.

### Notes

- Trend awareness is entirely optional and off by default. With the trend inputs
  left blank, behaviour is identical to 0.1.0 (instantaneous, temperature only).
- The open recommendation is unchanged; trends refine only the close decision.

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

[0.2.0]: https://github.com/niklasrichardson/ha-passive-cooling-blueprint/releases/tag/v0.2.0
[0.1.0]: https://github.com/niklasrichardson/ha-passive-cooling-blueprint/releases/tag/v0.1.0

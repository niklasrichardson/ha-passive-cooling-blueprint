# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-06-26

### Added

- **Comfort floor.** The minimum indoor temperature is now a *two-sided* comfort
  floor: the blueprint recommends **closing** once the room cools to it
  (`inside ≤ floor`) and only recommends **opening** once the room has warmed a
  new **re-open band** above it (`inside ≥ floor + band`, default band `1.0°`, via
  the new `comfort_reopen_band` input). The band is hysteresis so it doesn't flap
  at the floor. This bounds the evening hold — the room is kept around the floor
  instead of cooling indefinitely.
- **Exhaustive scenario-matrix tests** covering every `difference` band crossed
  with every trend regime (warming / cooling / flat × converging / widening /
  neutral), the comfort floor and re-open band, boundaries, and the no-trend
  cases, plus an open/close mutual-exclusion check.

### Changed

- Renamed the optional **Recommendation output** section to **Status output**
  (and its field to **Status helper**) — display labels only; the input id
  `recommendation_helper` is unchanged, so existing automations keep their link.
- **Default minimum indoor temperature lowered from `22.0` to `19.0`.**
- The minimum indoor temperature changed from a one-sided open gate to a
  two-sided comfort floor (see Added): opening now requires `inside ≥ floor +
  re-open band`, and a new close fires at `inside ≤ floor`.

### Fixed

- **Evening trend false positives (early close and equilibrium close).** The
  trend refinements keyed off the *relative* `difference_trend`, which also moves
  in the evening when the room cools faster than outside under good ventilation —
  producing spurious "close" recommendations. Both are now keyed off the
  **absolute outside trend**:
  - **Early close** (dead-band) now requires outside to be genuinely warming
    (`outside_trend ≥ +rate`), so it only fires in the morning case (fixes a
    spurious close on a room at a `0.7°` dead-band difference).
  - **Evening hold** (close-band) now keeps ventilating when outside is still
    cooler *and* more cooling is available — the gap widening **or** outside still
    cooling (`outside_trend ≤ −rate`) — instead of only when the gap was widening.
    So a room cooling toward a still-dropping outside keeps its windows open.

## [0.5.0] - 2026-06-25

### Added

- **Optional recommendation output for dashboards.** A new `recommendation_helper`
  input (an `input_boolean`) that the automation turns **on** when opening is
  recommended and **off** when closing is recommended, in addition to your
  open/close actions. Leave it blank to disable. Enables a per-room status board
  with native tile cards.
- `examples/recommendation_helpers.yaml` (per-room `input_boolean` plus a
  template `binary_sensor` with `device_class: window` for native Open/Closed
  tiles with an icon, state colour, and the room temperature as an attribute)
  and a tile-based `examples/overview_dashboard.yaml` with an outside-temperature
  tile and per-room recommendation + temperature tiles.
- Tests asserting the helper is an optional `input_boolean` input and that the
  open/close branches set it on/off.
- **Naming-convention examples** in the input descriptions (suggested entity ids
  for the sensors, trend sensors, global helpers and the recommendation helper)
  and a **"The algorithm (and the science behind it)"** README section that
  frames the open/close logic in terms of the control and building-science ideas
  it draws on (differential/"free cooling" control, hysteresis dead-band, a
  comfort gate, debouncing, a derivative/predictive term, and a latch) and gives
  the rules with and without trend sensors.

- **Evening cool-down (trend-aware close suppression).** When trend sensors are
  configured and the indoor/outdoor gap is near equilibrium but *widening*
  (outside dropping faster than the room) while outside is still cooler, the
  equilibrium close is suppressed so an evening cool-down keeps ventilating. If
  outside is warmer (difference ≤ 0) it always closes. The mirror image of the
  morning early close; reuses the minimum convergence rate. Without trend sensors
  the close is unchanged (tip: lower the close threshold toward `0.0`).
- **Recommendation latch (repeat-notification fix).** When a recommendation
  helper is linked, the open trigger is gated on the helper being off and the
  close trigger on it being on. A difference that merely oscillates across a
  threshold (without crossing into the other band) can no longer re-send the
  same recommendation — fixing repeat "open" notifications on rooms sitting at
  the open threshold. Tests simulate an oscillating room firing once (with the
  latch) versus repeatedly (without).

### Notes

- The recommendation is edge-based, so the helper holds the current standing
  recommendation (on = open, off = close); there is no separate "no action"
  state. Optional and off by default — without a helper linked, behaviour is
  unchanged (and threshold oscillation can re-fire).

## [0.4.0] - 2026-06-25

### Added

- **Global overrides for shared settings.** A new optional *Global overrides*
  section lets each setting point at a shared helper entity (typically an
  `input_number`): minimum indoor temperature, open/close difference, minimum
  convergence rate, and stability duration (in minutes). When a global helper is
  linked and holds a valid number it overrides the per-automation value, so a
  fleet of rooms can be tuned from one helper.
- Tests for the override precedence and safe fallback when a global helper is
  blank or invalid.
- `examples/global_helpers.yaml` — ready-to-paste `input_number` definitions for
  all five global override helpers.

### Changed

- Each globalisable setting now resolves its effective value as: linked global
  helper (when valid) → per-automation number → blueprint default. The action
  variables (`minimum_indoor_temperature`, `open_threshold`, `close_threshold`)
  reflect the effective value in use.
- The trigger `for:` (stability duration) is now templated so it can read from
  the optional global stability-duration helper; a blank or invalid helper falls
  back to the per-automation duration.

### Notes

- All global sources are optional and off by default; leaving them blank
  reproduces 0.3.0 behaviour exactly.

## [0.3.0] - 2026-06-25

### Added

- **Copy-paste action examples in the editor.** The open and close action inputs
  now include a ready-to-paste `notify` example (using the `room_name` and
  temperature variables) directly in their descriptions, so you can configure a
  notification without leaving the blueprint editor.
- **Optional Area input with automatic room naming.** A new optional `room_area`
  input lets you pick the room's area; the `room_name` is then derived
  automatically via `area_name()`. The `Room name` field becomes an optional
  override and can be left blank.
- **Testing rig under `examples/`.** A standalone test dashboard and a set of
  scenes (driven by `input_number` helpers) for exercising every branch of the
  open/close/early-close logic without waiting for real weather. See
  `examples/README.md`.

### Changed

- `room_name` is now resolved at runtime: the explicit name if set, otherwise
  the selected area's name, otherwise a generic label.

### Notes

- Blueprints cannot auto-filter an entity picker to a chosen area (that reactive
  filtering is not exposed to blueprints), so the sensor pickers remain manual —
  but Home Assistant's pickers are already searchable and grouped by area.
- The outdoor source remains a temperature sensor (no `weather.*` entity option).

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

[0.5.0]: https://github.com/niklasrichardson/ha-passive-cooling-blueprint/releases/tag/v0.5.0
[0.4.0]: https://github.com/niklasrichardson/ha-passive-cooling-blueprint/releases/tag/v0.4.0
[0.3.0]: https://github.com/niklasrichardson/ha-passive-cooling-blueprint/releases/tag/v0.3.0
[0.2.0]: https://github.com/niklasrichardson/ha-passive-cooling-blueprint/releases/tag/v0.2.0
[0.1.0]: https://github.com/niklasrichardson/ha-passive-cooling-blueprint/releases/tag/v0.1.0

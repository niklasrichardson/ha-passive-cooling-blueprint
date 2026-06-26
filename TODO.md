# TODO

Tracking ideas for future releases. The first release (`0.1.0`) is intentionally
scoped to the temperature-only passive-cooling use case.

## Done in 0.3.0 – 0.5.0

- [x] Optional Area input with automatic room naming (`area_name`). (0.3.0)
- [x] Copy-paste action examples in the editor; testing rig under `examples/`. (0.3.0)
- [x] Global overrides for shared settings across many automations. (0.4.0)
- [x] Optional status output (`input_boolean`) + native tile dashboard. (0.5.0)
- [x] Recommendation latch: gate open/close on the helper to stop repeat
      notifications from threshold oscillation. (0.5.0)
- [x] Evening cool-down: trend-aware suppression of the equilibrium close when
      the gap is widening while outside is still cooler. (0.5.0)
- [x] Docs restructured into a `docs/` set; quick start; browser-based setup
      generator (no Python). (Unreleased)

## Done in 0.2.0

- [x] Optional trend awareness via indoor/outdoor derivative sensors.
- [x] Convergence-based early close (close before equilibrium as the gap shuts).
- [x] `inside_trend` / `outside_trend` / `difference_trend` action variables.
- [x] Tests for trend behaviour and invalid-trend fallback.

## Done in 0.1.0

- [x] Passive cooling window recommendation blueprint (open / close).
- [x] Hysteresis via separate open and close thresholds.
- [x] Minimum indoor temperature gate.
- [x] Stability duration.
- [x] Change-only actions with no external helper (template-trigger edges).
- [x] Robust sensor validation (`is_number`, no invalid-as-zero).
- [x] Generic action selectors + optional additional conditions.
- [x] Documentation, examples, import button, attribution.
- [x] Logic tests, yamllint, and CI workflow.

## Considering for future releases

- [ ] Symmetric early-OPEN: in the evening, anticipate the cool-down and start
      ventilating slightly *before* the full open threshold. Deferred to avoid
      opening into marginal/rising outdoor air. (Note: the evening *close*
      suppression added in 0.5.0 already handles "keep ventilating" once open.)
- [ ] Per-recommendation stability durations (separate open vs close timing).
- [ ] Soft validation/warning when the open threshold is not greater than the
      close threshold (currently only documented).
- [ ] HACS metadata for distribution.
- [ ] HA config-check in CI (instantiate the blueprint with all-optional-blank
      and all-set, run `check_config`) — catches "valid YAML, invalid HA config".

## Explicitly out of scope (per project requirements)

These will **not** be added to this blueprint; they belong to separate projects
if pursued at all:

- Humidity (relative or absolute).
- Weather forecasts, rain sensors, sun-position logic.
- Curtain, blind, motorised-window or HVAC control.
- Custom integration dependencies.
- Hard-coded notification services.

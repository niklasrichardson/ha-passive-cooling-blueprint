# TODO

Tracking ideas for future releases. The first release (`0.1.0`) is intentionally
scoped to the temperature-only passive-cooling use case.

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

- [ ] **Optional state-helper input** (`input_select` / `input_text`) for a
      strict, persistent open→close state machine and explicit state
      re-assertion after a restart. Would keep the helper-free default while
      letting power users opt in. Resolves the two documented edge cases in the
      README "How state is tracked" section.
- [ ] Symmetric early-OPEN: in the evening, anticipate the cool-down and start
      ventilating slightly before the full open threshold when the gap is
      opening up. Deliberately deferred to avoid opening into marginal/rising
      outdoor temperatures; the instantaneous open threshold handles this today.
- [ ] Optional "current recommendation" sensor/attribute for dashboards.
- [ ] Per-recommendation stability durations (separate open vs close timing).
- [ ] Soft validation/warning when the open threshold is not greater than the
      close threshold (currently only documented).
- [ ] Example Lovelace card showing the current recommendation.
- [ ] HACS metadata for distribution.

## Explicitly out of scope (per project requirements)

These will **not** be added to this blueprint; they belong to separate projects
if pursued at all:

- Humidity (relative or absolute).
- Weather forecasts, rain sensors, sun-position logic.
- Curtain, blind, motorised-window or HVAC control.
- Custom integration dependencies.
- Hard-coded notification services.

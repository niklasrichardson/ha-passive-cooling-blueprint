# Testing

## Automated tests

Validation runs without a Home Assistant instance:

```bash
pip install pyyaml jinja2 yamllint
./scripts/validate.sh
```

This lints the YAML and runs `tests/test_blueprint_logic.py`, which parses the
blueprint, renders the **actual** trigger templates with Jinja2, and checks every
scenario in the specification: open, below-minimum, hysteresis hold, close,
invalid sensors, no-repeat, fluctuation stability, a full open→close→open cycle,
the trend-based early close (including the morning cold-but-rising case and
invalid-trend fallback), the evening close suppression, the recommendation latch
(including an oscillating-room simulation), and the global overrides. The same
checks run in CI via `.github/workflows/validate.yml`.

## Testing in Home Assistant

To exercise the logic live without waiting for real weather, the
[`examples/`](../examples) folder provides a ready-made test rig:

- `input_number` helpers you drive by hand (indoor/outdoor temperature and
  trend),
- a standalone dashboard with value sliders, one-tap **scenario buttons**, a live
  **"predicted outcome"** card, and the recommendation/latch toggle,
- **scenes** covering every open / close / early-close / evening case.

Full setup, the scenario matrix, and the workflow are in
[`examples/README.md`](../examples/README.md).

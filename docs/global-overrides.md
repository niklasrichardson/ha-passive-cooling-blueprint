# Global overrides — sharing settings across rooms

If you run many automations and don't want to edit each one when you tune a
threshold, point them at a **shared helper**. The optional *Global overrides*
section accepts a helper entity (typically an `input_number`) for each of:

- minimum indoor temperature,
- open-window difference,
- close-window difference,
- minimum convergence rate,
- stability duration (interpreted in **minutes**).

The effective value for each setting is resolved as:

1. **Global helper** — if you link one and it holds a valid number, it wins.
2. **Per-automation number** — the value on the form, otherwise.
3. **Blueprint default** — baked into that number field.

So set a helper once (e.g. `input_number.passive_cooling_min_indoor_temp`), link
it in every room, and changing the helper updates them all — they pick up the new
value on the next trigger evaluation. To make one room differ, just leave its
global blank and use the number field. An invalid or unavailable helper safely
falls back to the per-automation number, so a broken helper never stops the
automation.

## Ready-made helpers

[`examples/global_helpers.yaml`](../examples/global_helpers.yaml) defines all five
`input_number` helpers (with sensible ranges) ready to paste into your config.
The suggested entity ids are:

| Setting | Helper |
| ------- | ------ |
| Minimum indoor temperature | `input_number.passive_cooling_min_indoor_temp` |
| Open-window difference | `input_number.passive_cooling_open_difference` |
| Close-window difference | `input_number.passive_cooling_close_difference` |
| Minimum convergence rate | `input_number.passive_cooling_convergence_rate` |
| Stability duration (minutes) | `input_number.passive_cooling_stability_minutes` |

The blueprint's input descriptions suggest these same names, so everything lines
up.

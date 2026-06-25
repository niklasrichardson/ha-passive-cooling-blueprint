# Testing rig

A self-contained kit for exercising the **Passive Cooling Window
Recommendation** blueprint without waiting for real weather. You drive four
helper values, and a dashboard shows what the blueprint *should* decide
alongside what your automation actually does.

Files:

- [`test_scenes.yaml`](./test_scenes.yaml) — nine scenes, one per test case.
- [`test_dashboard.yaml`](./test_dashboard.yaml) — a standalone dashboard with
  sliders, a live "predicted outcome" card, and one-tap scenario buttons.

## 1. Create the helpers (Settings → Devices & services → Helpers)

Four **Number** helpers (*Create helper → Number*), range `0`–`45`, step `0.1`,
mode *slider*:

| Helper | Entity id |
| ------ | --------- |
| Test Indoor Temperature | `input_number.test_indoor_temperature` |
| Test Outdoor Temperature | `input_number.test_outdoor_temperature` |
| Test Indoor Temperature Trend | `input_number.test_indoor_temperature_trend` |
| Test Outdoor Temperature Trend | `input_number.test_outdoor_temperature_trend` |

The blueprint's sensor pickers only accept `sensor.*` entities, so mirror each
helper with a **Template** helper (*Create helper → Template → Template a
sensor*):

| Template sensor | State template | Device class |
| --------------- | -------------- | ------------ |
| Test Indoor Temperature | `{{ states('input_number.test_indoor_temperature') }}` | Temperature |
| Test Outdoor Temperature | `{{ states('input_number.test_outdoor_temperature') }}` | Temperature |
| Test Indoor Temperature Trend | `{{ states('input_number.test_indoor_temperature_trend') }}` | *(none)* |
| Test Outdoor Temperature Trend | `{{ states('input_number.test_outdoor_temperature_trend') }}` | *(none)* |

The **temperature** sensors need device class `Temperature` (so they appear in
the blueprint's temperature pickers). The **trend** sensors need no device class
— the trend inputs only filter on `domain: sensor`. Units are cosmetic; the
blueprint reads the raw number and treats trends as °/h.

## 2. Point a test automation at the helpers

Create an automation from the blueprint and set:

- Indoor sensor → `sensor.test_indoor_temperature`
- Outdoor sensor → `sensor.test_outdoor_temperature`
- Indoor trend → `sensor.test_indoor_temperature_trend`
- Outdoor trend → `sensor.test_outdoor_temperature_trend`
- **Stability duration → ~1–2 seconds** (so steps fire quickly; set it back to
  5 minutes for real use)

## 3. Install the scenes and dashboard

- **Scenes:** paste `test_scenes.yaml` into `scenes.yaml` (or append), then
  *Developer Tools → YAML → Reload Scenes*.
- **Dashboard:** *Settings → Dashboards → + Add dashboard → New dashboard from
  scratch*, open it, *Edit → ⋮ → Raw configuration editor*, paste
  `test_dashboard.yaml`. Replace `automation.passive_cooling_test_room` with
  your test automation's entity id.

## The test matrix

Defaults assumed: min indoor **22°**, open **1.0°**, close **0.5°**, convergence
rate **0.1 °/h**. `difference = indoor − outdoor`;
`difference_trend = indoor_trend − outdoor_trend` (negative = gap closing).

| # | Proves | Indoor | In-Trend | Outdoor | Out-Trend | diff / diff-trend | Expected |
|---|--------|--------|----------|---------|-----------|-------------------|----------|
| 1 | Basic OPEN | 25.0 | 0.0 | 20.0 | 0.0 | 5.0 / — | 🪟 Open |
| 2 | Basic CLOSE (equilibrium) | 25.0 | 0.0 | 24.6 | 0.0 | 0.4 / — | 🌡️ Close |
| 3 | Hysteresis hold (dead-band) | 25.0 | 0.0 | 24.2 | 0.0 | 0.8 / 0.0 | Nothing |
| 4 | Min-indoor gate blocks open | 21.0 | 0.0 | 15.0 | 0.0 | 6.0 / — | Nothing |
| 5 | Early CLOSE via trend | 25.0 | 0.0 | 24.3 | 2.0 | 0.7 / −2.0 | 🌡️ Close (early) |
| 6 | Dead-band, not converging | 25.0 | 2.0 | 24.3 | 0.0 | 0.7 / +2.0 | Nothing |
| 7 | Converging but big gap (morning) | 25.0 | 0.0 | 20.0 | 3.0 | 5.0 / −3.0 | 🪟 Open |
| 8 | Noise ignored (sub-threshold) | 25.0 | 0.0 | 24.3 | 0.05 | 0.7 / −0.05 | Nothing |
| 9 | Just over convergence threshold | 25.0 | 0.0 | 24.3 | 0.2 | 0.7 / −0.2 | 🌡️ Close (early) |

(#3 is the baseline scene, so there's no separate button for it.)

## Workflow

1. Tap a **Scenario** button — the **🔮 Predicted outcome** card updates
   immediately; the notification fires after the stability duration.
2. Tap **Baseline** between tests. Triggers fire only on a false→true edge, so
   returning to the neutral baseline re-arms them for a clean next test.
3. If the actual notification disagrees with the predicted card, that's a real
   finding — check *Settings → Automations → (your automation) → Traces* to see
   whether the close fired via `diff ≤ close` or via `early_close`.

## When you're done

- Set the test automation's **Stability duration** back to **5 minutes**.
- Point your real automations at your real sensors.

## Global override helpers

[`global_helpers.yaml`](./global_helpers.yaml) defines the five `input_number`
helpers for the blueprint's optional *Global overrides* section, so you can tune
a whole fleet of rooms from one place. Paste its `input_number:` block into
`configuration.yaml` (or use it as a package), restart, then link each helper in
every automation:

| Blueprint global field | Helper |
| ---------------------- | ------ |
| Minimum indoor temperature | `input_number.passive_cooling_min_indoor_temp` |
| Open-window difference | `input_number.passive_cooling_open_difference` |
| Close-window difference | `input_number.passive_cooling_close_difference` |
| Minimum convergence rate | `input_number.passive_cooling_convergence_rate` |
| Stability duration (minutes) | `input_number.passive_cooling_stability_minutes` |

A linked helper overrides that automation's local number; leave a global blank
to keep using the local value.

## Per-room recommendation tiles

The blueprint's optional **Recommendation helper** output keeps a per-room
`input_boolean` in sync (on = open recommended, off = close), so you can build a
status board with native tile cards — no custom cards required.

[`recommendation_helpers.yaml`](./recommendation_helpers.yaml) sets up two things
per room:

1. an **`input_boolean`** the automation writes to (on = open recommended), and
2. a **template sensor** that reads it and exposes a tidy **`Open`/`Close`**
   state, a window icon that flips with the recommendation, and the room's
   current **temperature** as an attribute.

Then:

1. Paste `recommendation_helpers.yaml` into your config and restart (adjust the
   temperature sensor entity ids to your rooms).
2. In each automation, link its `input_boolean` under *Recommendation output
   (optional)*.
3. Add [`overview_dashboard.yaml`](./overview_dashboard.yaml): a prominent
   outside-temperature tile, then one tile per room showing the recommendation
   and the room temperature together (via the tile's `state_content`).

> Wording vs colour trade-off: this template-sensor approach gives exact
> `Open`/`Close` text plus the temperature on one tile, with the open/closed
> window icon showing state. If you'd rather have automatic state *colour*
> (green when open), use a template `binary_sensor` with `device_class: window`
> instead — but its state reads "Open"/"**Closed**" and can't carry the
> temperature on the same tile.

Because the recommendation only changes on the open/close edges, the helper
holds the **current standing recommendation** — there is no separate "no action"
state (the hysteresis hold simply keeps the last decision).

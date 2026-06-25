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
> [Limitations](#limitations).

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2Fniklasrichardson%2Fha-passive-cooling-blueprint%2Fmain%2Fblueprints%2Fautomation%2Fniklasrichardson%2Fpassive_cooling_window_recommendation.yaml)

---

## Contents

- [What it does](#what-it-does)
- [When it recommends opening](#when-it-recommends-opening-windows)
- [When it recommends closing](#when-it-recommends-closing-windows)
- [Hysteresis: why two thresholds](#hysteresis-why-two-thresholds)
- [Minimum indoor temperature](#minimum-indoor-temperature)
- [Stability duration](#stability-duration)
- [Trend awareness: early close (optional)](#trend-awareness-early-close-optional)
- [Sharing settings across rooms (global overrides)](#sharing-settings-across-rooms-global-overrides)
- [Recommendation output for dashboards (optional)](#recommendation-output-for-dashboards-optional)
- [How state is tracked (and restart behaviour)](#how-state-is-tracked)
- [Installing the blueprint](#installing-the-blueprint)
- [Creating one automation per room](#creating-one-automation-per-room)
- [Configuring actions](#configuring-actions)
- [Variables available to your actions](#variables-available-to-your-actions)
- [Example: full automation](#example-full-automation)
- [Sensor requirements](#sensor-requirements)
- [Celsius and Fahrenheit](#celsius-and-fahrenheit)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)
- [Development and validation](#development-and-validation)
- [Credits](#credits)
- [License](#license)

---

## What it does

The blueprint watches one indoor and one outdoor temperature sensor and runs
**one action when opening becomes recommended** and **one action when closing
becomes recommended**. Actions run only when the recommendation *changes* — you
will not get a notification on every sensor update.

```
Inside: 25.0°C   Outside: 22.0°C   Difference: 3.0°C   ->  Open windows
Inside: 22.4°C   Outside: 22.0°C   Difference: 0.4°C   ->  Close windows
```

One automation handles one room. Add a separate automation per room.

## When it recommends opening windows

All of the following must hold, continuously, for the [stability
duration](#stability-duration):

1. The room is **at or above** the minimum indoor temperature (default
   `22.0°`). No point cooling a room that is already cool.
2. The outdoor sensor is **at least the open threshold cooler** than indoors
   (default `1.0°`), i.e. `inside − outside ≥ open threshold`.
3. Both sensors report valid numbers.

## When it recommends closing windows

The close recommendation fires when, continuously for the stability duration:

1. The indoor/outdoor difference has fallen to **the close threshold or less**
   (default `0.5°`), i.e. `inside − outside ≤ close threshold`. The outside air
   is no longer meaningfully cooler.
2. Both sensors report valid numbers.

## Hysteresis: why two thresholds

If a single threshold controlled both opening and closing, normal sensor jitter
around that value would flip the recommendation back and forth, spamming you
with "open" / "close" / "open" notifications.

Two thresholds create a **dead band** between them where nothing changes:

```
        difference (inside − outside)
  cooler  <───────────────────────────────────────>  warmer
                  close (0.5°)        open (1.0°)
   CLOSE  ──────────┤      hysteresis      ├────────── OPEN
                    │   recommendation     │
                    │   stays as it was    │
```

- Recommend **opening** when the difference reaches the open threshold (`1.0°`).
- Keep recommending open while the difference stays above the close threshold.
- Recommend **closing** only once the difference drops to the close threshold
  (`0.5°`) or below.

**The open threshold must be greater than the close threshold.** Home Assistant
blueprint inputs cannot enforce a relationship between two inputs, so this is
not validated by the UI. If you set them equal or inverted, the dead band
disappears and you lose the anti-flapping protection (the blueprint will still
run safely — it simply behaves like a single-threshold automation). The bundled
tests and the input descriptions both call this out.

## Minimum indoor temperature

Cooler outside air is not a reason to open windows if the room is already
comfortable or cold. The minimum indoor temperature gates the open
recommendation:

```
Inside: 19.0°C   Outside: 16.0°C   ->  Do NOT recommend opening (room is cool)
```

The minimum applies to the **open** recommendation only.

## Stability duration

A recommendation must hold steady for this long before its action runs (default
`5 minutes`). This is implemented with Home Assistant's template-trigger `for:`
option and smooths out brief sensor spikes — a single stray reading will not
trigger a notification.

## Trend awareness: early close (optional)

Plain thresholds are reactive — they wait until the indoor and outdoor
temperatures have *already* converged before recommending a close. On a typical
summer night you ventilate to pull in cool air; as the morning sun arrives the
outside warms and the gap shrinks. By the time the difference collapses to the
close threshold, you may have already let the room warm back up.

Give the blueprint two **rate-of-change sensors** (degrees per hour, one for
indoors and one for outdoors) and it can close the windows *early*, as soon as
it detects the gap is genuinely closing — locking in the cooler air before the
room heats up again.

### The rule, in plain terms

Let `difference = inside − outside`. The gap is **closing** when

```
inside_trend − outside_trend  ≤  −(minimum convergence rate)
```

i.e. the outdoor temperature is catching up to indoors **faster** than the room
itself is warming. When that is true **and** the difference is sitting inside the
hysteresis band (between the close and open thresholds), the blueprint
recommends closing early. This deliberately captures the cases you described:

- **Morning, outside cold but rising, room still warm.** The gap is huge, so
  even though outside is rising you keep ventilating — exactly what you want.
  Only once the gap shrinks into the hysteresis band does the early close kick
  in.
- **Room warming from the sun while outside is still clearly cooler.** Here the
  *difference is growing*, not closing, so ventilation is still winning and the
  windows stay open. The blueprint will not close just because the indoor
  temperature ticked up.
- **Don't make the room hotter than it was.** Closing before full equilibrium
  means you stop pulling in air that is no longer meaningfully cooler.

The open recommendation is **unchanged** by trends — opening still happens on the
instantaneous threshold. Trends refine only the *close* decision.

### Setting up the derivative sensors

Use Home Assistant's built-in [Derivative
helper](https://www.home-assistant.io/integrations/derivative/) (*Settings →
Devices & services → Helpers → Create helper → Derivative sensor*), or YAML:

```yaml
sensor:
  - platform: derivative
    source: sensor.master_bedroom_temperature
    name: Master bedroom temperature trend
    unit_time: h        # degrees per HOUR — important
    time_window: "00:30:00"   # smooth over 30 min to reduce noise
```

Create one for the indoor sensor and one for the outdoor sensor, then select
them under *Trend awareness (optional)*. **Leave them blank to disable trend
awareness entirely** — the blueprint then behaves exactly as the
temperature-only version. If a trend sensor is missing or invalid, the blueprint
safely falls back to the plain equilibrium close.

> **Evening "start ventilating" question.** Opening is intentionally still driven
> by the instantaneous open threshold, so you start ventilating as soon as the
> outside is genuinely cooler — without the risk of opening early into marginal
> or still-rising outdoor air. Symmetric *early open* is noted in `TODO.md` as a
> possible future option.

## Sharing settings across rooms (global overrides)

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
it in every room, and changing the helper updates them all — they pick up the
new value on the next trigger evaluation. To make one room differ, just leave its
global blank and use the number field. An invalid or unavailable helper safely
falls back to the per-automation number, so a broken helper never stops the
automation.

## Recommendation output for dashboards (optional)

The blueprint runs your open/close *actions*, but doesn't itself create an
entity you can put on a dashboard. To get a per-room status you can show, link
an optional **recommendation helper**: an `input_boolean` the automation turns
**on** when opening is recommended and **off** when closing is recommended (in
addition to your normal actions).

- Create one `input_boolean` per room and link it under *Recommendation output*.
- For a polished, fully-native board, mirror each `input_boolean` with a template
  sensor exposing an **`Open`/`Close`** state, a window icon, and the room
  temperature as an attribute — a single tile then shows the recommendation and
  the temperature together. See [`examples/`](./examples) for ready-to-paste
  helpers and a tile dashboard (with an outside-temperature tile).

Because the recommendation only changes on the open/close edges, the helper
holds the **current standing recommendation** (on = open, off = close). There is
no separate "no action" state — the hysteresis hold simply keeps the last
decision. Leave the input blank to disable this entirely.

## How state is tracked

The automation must run an action only when the recommendation **changes**, and
must survive Home Assistant restarts, automation reloads, and flaky sensors.

**Design choice: this blueprint needs no external helper.** It uses two Home
Assistant *template triggers* — one for "open", one for "close". A template
trigger fires only on the **rising edge**, when its template flips from false to
true, and will not fire again until the template has gone false in between. That
edge behaviour *is* the state machine:

- While the room keeps qualifying to open, the open template stays `true`, so
  the open action runs **once** and is not repeated.
- The open and close conditions are separated by the hysteresis dead band,
  where neither template is true, so the current recommendation simply persists
  with no action.
- When the difference collapses into the close band, the close template rises
  and the close action runs once.

**Trade-off — why no helper:** An `input_select`/`input_text` helper could store
an explicit "current recommendation" string. It would let the close action fire
*only* after a preceding open, and would let the automation re-assert state on
startup. The cost is that every user must create and wire up a helper before the
blueprint works. The edge-trigger approach needs zero setup and is reliable for
the core flow, at the price of two documented edge cases:

1. **After a restart or reload, triggers re-arm from a clean slate.** Home
   Assistant evaluates template triggers on startup but does *not* fire them for
   a state that is *already* true — only on the next genuine false→true edge.
   In practice: if "open" was already recommended before the restart and is
   still valid afterwards, the open action will **not** re-run (no duplicate
   notification — usually what you want). The recommendation is re-acted upon at
   the next real change. No stale or duplicate actions occur across restarts,
   reloads, or blueprint updates.
2. **A close can fire without a preceding open** if the difference drifts down
   through the dead band into the close band without ever having reached the
   open threshold. This is uncommon (it needs the room to hover just below the
   open threshold) and the resulting "you can close the windows" advice is
   harmless. If you want a strict open→close machine, gate the close action with
   an [additional condition](#configuring-actions).

If your installation requires a strict, persistent state machine, a future
release may add an optional helper input; see `TODO.md`.

## Installing the blueprint

**One-click import** (requires the repository to be public — see the note
below): click the **Import Blueprint** button at the top of this README, or
paste this URL into *Settings → Automations & scenes → Blueprints → Import
Blueprint*:

```
https://raw.githubusercontent.com/niklasrichardson/ha-passive-cooling-blueprint/main/blueprints/automation/niklasrichardson/passive_cooling_window_recommendation.yaml
```

> **Private repository note.** This repository may currently be private. Home
> Assistant's one-click import fetches the raw GitHub URL anonymously, so it
> only works when the repository is **public**. While it is private, install
> manually instead: copy
> `blueprints/automation/niklasrichardson/passive_cooling_window_recommendation.yaml`
> into your Home Assistant `config/blueprints/automation/niklasrichardson/`
> folder and reload automations (or restart Home Assistant). The import button
> and raw URL above are written for the expected public path and will work once
> the repository is public.

## Creating one automation per room

Each automation instance covers a single room. To cover several rooms, create
several automations from the same blueprint:

1. *Settings → Automations & scenes → Blueprints*.
2. Find **Passive Cooling Window Recommendation** and click **Create
   Automation**.
3. Optionally pick the room's **Area** — the room name is then filled in
   automatically (via `area_name`), so you don't have to type it. Leave the
   **Room name** field blank to use the area's name, or set it to override.
4. Pick that room's indoor and outdoor sensors and tune the thresholds. The
   sensor pickers are searchable and grouped by area, so type the room name to
   narrow them quickly. (A blueprint can't auto-filter those pickers to the area
   you chose — that reactive filtering isn't available to blueprints — but the
   built-in search gets you there.)
5. Repeat for the next room. Give each automation a distinct name, e.g.
   "Passive cooling — Master bedroom".

You can point several rooms at the same shared outdoor sensor (for example a
single garden sensor or an averaged outdoor temperature).

## Configuring actions

The **open** and **close** actions are ordinary Home Assistant action sequences,
chosen with an action selector — so you are not locked into notifications. Use a
mobile notification, a TTS announcement, a script, a scene, a light, or any
combination.

> **Tip:** the open and close action fields in the blueprint editor include a
> ready-to-paste notification example in their descriptions — copy it, swap
> `notify.notify` for your own service, and you're done. The examples below show
> more variations.

**Mobile notification example** (open action):

```yaml
- action: notify.mobile_app_your_phone
  data:
    title: "Passive cooling"
    message: >-
      Open the {{ room_name }} windows — it is
      {{ temperature_difference | round(1) }}° cooler outside.
```

**`script.notify_wrapper` example** (close action) — using your own
notification wrapper script:

```yaml
- action: script.notify_wrapper
  data:
    message: >-
      Close the {{ room_name }} windows.
      Inside is {{ inside_temperature | round(1) }}°,
      outside is {{ outside_temperature | round(1) }}°,
      and the difference is {{ temperature_difference | round(1) }}°.
```

**TTS example** (open action):

```yaml
- action: tts.cloud_say
  data:
    entity_id: media_player.kitchen
    message: "{{ room_name }} is warm and it is cooler outside. Open the windows."
```

**Optional additional conditions.** Under *Additional conditions (optional)* you
can require extra conditions for each recommendation — for example, only notify
when someone is home, or only between sunset and sunrise. Leave them empty to
always allow.

## Variables available to your actions

Both actions can use these variables inside templates. Temperatures are numeric
and ready to format with `| round(1)`:

| Variable                      | Meaning                                              |
| ----------------------------- | ---------------------------------------------------- |
| `room_name`                   | Room name — the override text, else the selected area's name |
| `inside_temperature`          | Current indoor temperature (number)                  |
| `outside_temperature`         | Current outdoor temperature (number)                 |
| `temperature_difference`      | `inside_temperature − outside_temperature` (number)  |
| `minimum_indoor_temperature`  | Configured minimum indoor temperature                |
| `open_threshold`              | Configured open-window difference                    |
| `close_threshold`             | Configured close-window difference                   |
| `inside_trend`                | Indoor rate of change in °/h (`0` if no trend sensor)|
| `outside_trend`               | Outdoor rate of change in °/h (`0` if no trend sensor)|
| `difference_trend`            | `inside_trend − outside_trend` (negative = gap closing)|
| `recommendation`              | `"Open windows"` or `"Close windows"`                |

## Example: full automation

A complete automation that uses the blueprint (input names match the blueprint
exactly):

```yaml
alias: Passive cooling — Master bedroom
use_blueprint:
  path: niklasrichardson/passive_cooling_window_recommendation.yaml
  input:
    # Pick an area to auto-name the room, or set room_name to override it.
    # Both are optional; room_area can be omitted if you set room_name.
    room_area: master_bedroom
    room_name: Master bedroom
    inside_temperature_sensor: sensor.master_bedroom_temperature
    outside_temperature_sensor: sensor.average_outside_temperature
    minimum_indoor_temperature: 22
    open_temperature_difference: 1
    close_temperature_difference: 0.5
    stability_duration:
      minutes: 5
    # Optional trend awareness — omit these three to disable early close.
    inside_temperature_trend: sensor.master_bedroom_temperature_trend
    outside_temperature_trend: sensor.average_outside_temperature_trend
    minimum_convergence_rate: 0.1
    open_action:
      - action: script.notify_wrapper
        data:
          message: >-
            Open the {{ room_name }} windows.
            It is {{ temperature_difference | round(1) }}° cooler outside.
    close_action:
      - action: script.notify_wrapper
        data:
          message: >-
            Close the {{ room_name }} windows.
            The room has reached the outside temperature.
```

## Sensor requirements

- Two `sensor` entities with `device_class: temperature` (the entity pickers
  filter for these). One indoor, one outdoor.
- Both sensors should report in the **same unit** as each other.
- Invalid states — `unknown`, `unavailable`, `none`, empty strings and any
  non-numeric value — are **never treated as `0`**. Neither action runs unless
  both sensors currently hold valid numbers (validated with `is_number`). A
  sensor dropping out will therefore never produce a bogus recommendation.
- **Optional:** two rate-of-change sensors (degrees per hour) to enable
  [early close](#trend-awareness-early-close-optional). An invalid or missing
  trend sensor simply disables the early-close refinement; it never blocks the
  basic open/close behaviour.

## Celsius and Fahrenheit

The blueprint does plain arithmetic on the raw sensor values; it performs **no
unit conversion of its own**. That means it works on Fahrenheit installations,
with two things to keep in mind:

- **Enter every threshold in your sensors' unit.** On a Fahrenheit system the
  defaults (min `22`, open `1.0`, close `0.5`) are Celsius values and make no
  sense — use Fahrenheit equivalents, e.g. minimum `72`, open difference `2`,
  close difference `1`. The number selectors show a generic `°` so they do not
  imply Celsius.
- **Both sensors must use the same unit.** Home Assistant converts a temperature
  sensor's state to the system unit when the sensor declares a
  `unit_of_measurement` and `device_class: temperature`, so in a normal setup
  both sensors already read in your system unit and the difference is correct.
  If you mix a °C sensor and a °F sensor that are *not* being converted, the
  difference is meaningless — make sure both are reported consistently.

## Troubleshooting

- **No notifications at all.** Check both sensors show a number in *Developer
  Tools → States* (not `unavailable`). Confirm the room actually reaches the
  minimum indoor temperature and that the difference reaches the open threshold
  for the full stability duration. Lower the stability duration to test quickly.
- **It notifies but never recommends closing.** The difference may not be
  dropping to the close threshold. Check `temperature_difference` against your
  close threshold in *Developer Tools → Template*.
- **Too many notifications / flapping.** Increase the gap between the open and
  close thresholds (bigger dead band) and/or increase the stability duration.
- **A "close" arrived without an "open" first.** Expected edge case — see
  [How state is tracked](#how-state-is-tracked). Add an additional close
  condition if you need a strict open→close sequence.
- **Nothing fired right after a restart.** Expected — triggers re-arm on the
  next genuine change. See [How state is tracked](#how-state-is-tracked).
- **Test the templates live.** Paste the values into *Developer Tools →
  Template*:
  `{{ is_number(states('sensor.master_bedroom_temperature')) }}`.

## Limitations

This blueprint is deliberately temperature-only (optionally using temperature
*trends*). It does **not** consider:
humidity (relative or absolute), weather forecasts, rain, sun position, indoor
air quality, or occupancy (beyond optional conditions you add yourself). It does
**not** control curtains, blinds, motorised windows, or HVAC — it only *runs the
action you choose*. It depends on no custom integrations.

## Development and validation

Validation runs without a Home Assistant instance:

```bash
pip install pyyaml jinja2 yamllint
./scripts/validate.sh
```

This lints the YAML and runs `tests/test_blueprint_logic.py`, which parses the
blueprint, renders the **actual** trigger templates with Jinja2, and checks
every scenario in the specification (open, below-minimum, hysteresis hold,
close, invalid sensors, no-repeat, fluctuation stability, a full
open→close→open cycle, and the trend-based early close including the morning
cold-but-rising case and invalid-trend fallback). The same checks run in CI via
`.github/workflows/validate.yml`.

### Testing in Home Assistant

To exercise the logic live without waiting for real weather, the
[`examples/`](./examples) folder provides a ready-made test rig — `input_number`
helpers you drive by hand, a standalone dashboard with one-tap scenario buttons
and a live "predicted outcome" card, and scenes covering every open / close /
early-close case. See [`examples/README.md`](./examples/README.md).

## Credits

Inspired by Adam Cornforth's
[Dynamic Ventilation blueprint](https://github.com/adamcornforth/ha-open-window-blueprint).
This project is an independent, temperature-only implementation. It is **not** a
fork of, and is **not** officially affiliated with, that project.

## License

[MIT](LICENSE) © 2026 Niklas Richardson

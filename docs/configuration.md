# Configuration

- [Configuring actions](#configuring-actions)
- [Variables available to your actions](#variables-available-to-your-actions)
- [Example: full automation](#example-full-automation)
- [Sensor requirements](#sensor-requirements)
- [Celsius and Fahrenheit](#celsius-and-fahrenheit)

For what the thresholds and timing inputs *do*, see
[How it works](how-it-works.md). For the optional inputs, see
[Trend awareness](trends.md), [Global overrides](global-overrides.md) and
[Dashboards](dashboards.md).

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

**`script.notify_wrapper` example** (close action) — using your own notification
wrapper script:

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
| `minimum_indoor_temperature`  | Effective minimum indoor temperature                 |
| `open_threshold`              | Effective open-window difference                     |
| `close_threshold`             | Effective close-window difference                    |
| `inside_trend`                | Indoor rate of change in °/h (`0` if no trend sensor)|
| `outside_trend`               | Outdoor rate of change in °/h (`0` if no trend sensor)|
| `difference_trend`            | `inside_trend − outside_trend` (negative = gap closing)|
| `recommendation`              | `"Open windows"` or `"Close windows"`                |

The threshold variables report the **effective** value in use — the linked
[global helper](global-overrides.md) when one is set, otherwise the
per-automation number.

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
    minimum_indoor_temperature: 19
    comfort_reopen_band: 1
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
  [early close](trends.md). An invalid or missing trend sensor simply disables
  the trend refinement; it never blocks the basic open/close behaviour.

## Celsius and Fahrenheit

The blueprint does plain arithmetic on the raw sensor values; it performs **no
unit conversion of its own**. That means it works on Fahrenheit installations,
with two things to keep in mind:

- **Enter every threshold in your sensors' unit.** On a Fahrenheit system the
  defaults (min `19`, re-open band `1.0`, open `1.0`, close `0.5`) are Celsius
  values and make no sense — use Fahrenheit equivalents, e.g. minimum `66`,
  re-open band `2`, open difference `2`, close difference `1`. The number
  selectors show a generic `°` so they do not
  imply Celsius.
- **Both sensors must use the same unit.** Home Assistant converts a temperature
  sensor's state to the system unit when the sensor declares a
  `unit_of_measurement` and `device_class: temperature`, so in a normal setup
  both sensors already read in your system unit and the difference is correct. If
  you mix a °C sensor and a °F sensor that are *not* being converted, the
  difference is meaningless — make sure both are reported consistently.

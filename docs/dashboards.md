# Dashboards — status output (optional)

The blueprint runs your open/close *actions*, but doesn't itself create an entity
you can put on a dashboard. To get a per-room status you can show, link an
optional **status helper**: an `input_boolean` the automation turns **on**
when opening is recommended and **off** when closing is recommended (in addition
to your normal actions).

- Create one `input_boolean` per room and link it under *Status output*.
- For a polished, fully-native board, mirror each `input_boolean` with a template
  `binary_sensor` (`device_class: window`): tiles show **Open/Closed**, a window
  icon, state-based colour, and the room temperature (carried as an attribute) —
  all on one tile, no custom cards.

See [`examples/`](../examples) for ready-to-paste helpers
([`status_helpers.yaml`](../examples/status_helpers.yaml)) and a
tile dashboard ([`overview_dashboard.yaml`](../examples/overview_dashboard.yaml),
with an outside-temperature tile and per-room recommendation + temperature tiles).

Because the recommendation only changes on the open/close edges, the helper holds
the **current standing recommendation** (on = open, off = close). There is no
separate "no action" state — the hysteresis hold simply keeps the last decision.
Leave the input blank to disable this entirely.

## It also stops repeat notifications

Linking a helper does more than feed a dashboard — it **latches** the
recommendation. The open action fires only while the helper is off and the close
action only while it is on, so a room whose indoor/outdoor difference merely
*oscillates across a threshold* (without crossing into the other band) can't
re-send the same recommendation. This is the robust fix for repeated "open"
notifications on rooms sitting right at the open threshold. Without a helper
linked, behaviour is unchanged and such oscillation can re-fire — so linking a
helper per room is recommended if you see repeats.

## Suggested naming

One per room, matching the blueprint's input description and the examples:

```
input_boolean.passive_cooling_<room>   e.g. input_boolean.passive_cooling_master_bedroom
```

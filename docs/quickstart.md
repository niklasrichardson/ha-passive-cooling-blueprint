# Quick start

The shortest path to a working passive-cooling recommendation for one room. For
the optional extras (trends, dashboards, shared helpers), follow the links at the
end.

## 1. Import the blueprint

Click the **Import Blueprint** button in the [README](../README.md), or paste the
raw URL into *Settings → Automations & scenes → Blueprints → Import Blueprint*.
Details: [Installation](installation.md).

## 2. Create an automation for a room

1. *Settings → Automations & scenes → Blueprints* → **Passive Cooling Window
   Recommendation** → **Create Automation**.
2. *(Optional)* pick the room's **Area** to auto-name it.
3. Choose the **indoor** and **outdoor** temperature sensors.
4. Pick an **open action** — the field includes a ready-to-paste notification
   example; just swap `notify.notify` for your own service.
5. Pick a **close action** the same way.
6. **Save.** Leave the thresholds at their defaults to start.

That's a working recommendation: an "open" notification when the room is warm and
outside is cooler, and a "close" when they converge.

## 3. (Optional) Tune it

- Defaults: minimum indoor `22°`, open difference `1.0°`, close difference
  `0.5°`, stability `5 min`. Enter values in the **same unit as your sensors** —
  see [Configuration](configuration.md) and
  [Celsius & Fahrenheit](configuration.md#celsius-and-fahrenheit).
- Repeat "open" alerts on a marginal room? See
  [Troubleshooting](troubleshooting.md), or link a recommendation helper to
  [latch](dashboards.md#it-also-stops-repeat-notifications) it.

## Add another room

> **Many rooms?** The [setup generator](generator.md) turns a list of your rooms
> into ready-to-paste helpers, dashboard and automation YAML — no hand-repeating.

One automation = one room. For each additional room:

- [ ] Create a new automation from the blueprint.
- [ ] Pick that room's **indoor** sensor (the **outdoor** sensor can be shared).
- [ ] Set its open / close actions.
- [ ] Give the automation a distinct name (e.g. "Passive cooling — Study").

## Next steps

- [Trend awareness](trends.md) — close early in the morning, keep ventilating in
  the evening.
- [Global overrides](global-overrides.md) — change a threshold once for every
  room.
- [Dashboards](dashboards.md) — per-room Open/Closed tiles, and the latch that
  stops repeat alerts.

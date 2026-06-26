# Installation

## Installing the blueprint

**One-click import** (requires the repository to be public — see the note below):
click the **Import Blueprint** button in the [README](../README.md), or paste this
URL into *Settings → Automations & scenes → Blueprints → Import Blueprint*:

```
https://raw.githubusercontent.com/niklasrichardson/ha-passive-cooling-blueprint/main/blueprints/automation/niklasrichardson/passive_cooling_window_recommendation.yaml
```

> **Private repository note.** Home Assistant's one-click import fetches the raw
> GitHub URL anonymously, so it only works when the repository is **public**.
> While it is private, install manually instead: copy
> `blueprints/automation/niklasrichardson/passive_cooling_window_recommendation.yaml`
> into your Home Assistant `config/blueprints/automation/niklasrichardson/`
> folder and reload automations (or restart Home Assistant). The import button
> and raw URL are written for the expected public path and will work once the
> repository is public.

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

---

Next: [Configuration](configuration.md) · [How it works](how-it-works.md)

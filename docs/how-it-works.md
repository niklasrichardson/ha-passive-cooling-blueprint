# How it works

- [What it does](#what-it-does)
- [When it recommends opening](#when-it-recommends-opening-windows)
- [When it recommends closing](#when-it-recommends-closing-windows)
- [Hysteresis: why two thresholds](#hysteresis-why-two-thresholds)
- [Minimum indoor temperature](#minimum-indoor-temperature)
- [Stability duration](#stability-duration)
- [The algorithm (and the science behind it)](#the-algorithm-and-the-science-behind-it)
- [How state is tracked](#how-state-is-tracked)

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

All of the following must hold, continuously, for the
[stability duration](#stability-duration):

1. The room is **at or above** the minimum indoor temperature (default `22.0°`).
   No point cooling a room that is already cool.
2. The outdoor sensor is **at least the open threshold cooler** than indoors
   (default `1.0°`), i.e. `inside − outside ≥ open threshold`.
3. Both sensors report valid numbers.

## When it recommends closing windows

The close recommendation fires when, continuously for the stability duration:

1. The indoor/outdoor difference has fallen to **the close threshold or less**
   (default `0.5°`), i.e. `inside − outside ≤ close threshold`. The outside air
   is no longer meaningfully cooler.
2. Both sensors report valid numbers.

(With trend sensors, the close decision is refined — see
[Trend awareness](trends.md) and the algorithm below.)

## Hysteresis: why two thresholds

If a single threshold controlled both opening and closing, normal sensor jitter
around that value would flip the recommendation back and forth, spamming you with
"open" / "close" / "open" notifications.

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
blueprint inputs cannot enforce a relationship between two inputs, so this is not
validated by the UI. If you set them equal or inverted, the dead band disappears
and you lose the anti-flapping protection (the blueprint will still run safely —
it simply behaves like a single-threshold automation). The bundled tests and the
input descriptions both call this out.

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

## The algorithm (and the science behind it)

At heart this is a small **controls layer for night-ventilation cooling** (also
called *night flushing*): ventilate while outdoor air can carry heat out of the
room, and stop before it stops helping. It is deliberately simple, but it is
built from a handful of well-established control and building-science ideas:

- **Differential (ΔT) control — "free cooling".** Decisions are driven by the
  *difference* between indoor and outdoor temperature, the same idea as an
  air-side **economizer** that draws in outdoor air whenever it is cooler than
  inside. (→ the open rule.)
- **Hysteresis — a dead-band.** Two thresholds, not one — exactly how a
  thermostat avoids chattering around a single setpoint. Opening needs a clear
  gap; closing needs the gap to nearly vanish; in between, nothing changes.
  (→ open vs close thresholds.)
- **A comfort gate.** The minimum indoor temperature is a lower comfort bound —
  there is no point cooling a room that is already cool. (→ minimum indoor
  temperature.)
- **Debouncing — a low-pass filter.** The stability duration makes a
  recommendation prove itself before acting, so a single stray reading does not
  fire an action. (→ stability duration.)
- **A derivative term — a step toward predictive control.** Optional trend
  sensors add the *rate of change*. It does not forecast; it asks "which way is
  the gap heading right now?" — closing early when the gap is collapsing
  (morning) and holding open when it is widening (evening). (→
  [trend awareness](trends.md).)
- **A latch — a small state machine.** An optional helper stores the standing
  recommendation, so each edge-triggered recommendation fires once per real
  change rather than re-firing on noise. (→ [recommendation output](dashboards.md).)

Concretely, with `difference = inside − outside` (positive means outside cooler):

```
OPEN   when  inside ≥ minimum indoor temperature
         AND difference ≥ open threshold
CLOSE  when  difference ≤ close threshold
HOLD   otherwise — the hysteresis dead-band (close < difference < open),
             where the current recommendation simply persists
```

**With trend sensors** (these refine the **close** only; opening is always the
instantaneous rule above). Let `difference_trend = inside_trend − outside_trend`
— negative means the gap is *closing*, positive means it is *widening*:

- **Early close (morning).** If `difference` is in the dead-band *and* the gap is
  closing faster than the convergence rate (`difference_trend ≤ −rate`), close
  early instead of waiting for full equilibrium.
- **Evening hold.** If `difference ≤ close threshold` *but* the gap is widening
  (`difference_trend ≥ +rate`) while outside is still cooler (`difference > 0`),
  **do not** close — keep ventilating into the cool-down. If outside is actually
  warmer (`difference ≤ 0`), it always closes regardless of trend.

**With a recommendation helper linked (latch).** Open fires only when the helper
is off (not already open) and close only when it is on (currently open), so a
`difference` that merely oscillates across a threshold can't re-send the same
recommendation.

What it deliberately **does not** model: thermal mass, weather forecasts, airflow
rate (a cracked window ≠ cross-ventilation), or humidity — see
[Limitations](troubleshooting.md#limitations).

## How state is tracked

The automation must run an action only when the recommendation **changes**, and
must survive Home Assistant restarts, automation reloads, and flaky sensors.

**Design choice: this blueprint needs no external helper.** It uses two Home
Assistant *template triggers* — one for "open", one for "close". A template
trigger fires only on the **rising edge**, when its template flips from false to
true, and will not fire again until the template has gone false in between. That
edge behaviour *is* the state machine:

- While the room keeps qualifying to open, the open template stays `true`, so the
  open action runs **once** and is not repeated.
- The open and close conditions are separated by the hysteresis dead band, where
  neither template is true, so the current recommendation simply persists with no
  action.
- When the difference collapses into the close band, the close template rises and
  the close action runs once.

**Trade-off — why no helper by default:** An `input_select`/`input_text` helper
could store an explicit "current recommendation" string. It would let the close
action fire *only* after a preceding open, and would let the automation re-assert
state on startup. The cost is that every user must create and wire up a helper
before the blueprint works. The edge-trigger approach needs zero setup and is
reliable for the core flow, at the price of two documented edge cases:

1. **After a restart or reload, triggers re-arm from a clean slate.** Home
   Assistant evaluates template triggers on startup but does *not* fire them for
   a state that is *already* true — only on the next genuine false→true edge. In
   practice: if "open" was already recommended before the restart and is still
   valid afterwards, the open action will **not** re-run (no duplicate
   notification — usually what you want). The recommendation is re-acted upon at
   the next real change. No stale or duplicate actions occur across restarts,
   reloads, or blueprint updates.
2. **A close can fire without a preceding open** if the difference drifts down
   through the dead band into the close band without ever having reached the open
   threshold. This is uncommon (it needs the room to hover just below the open
   threshold) and the resulting "you can close the windows" advice is harmless.
   If you want a strict open→close machine, gate the close action with an
   [additional condition](configuration.md#configuring-actions).

For a stricter, persistent state machine you can link an optional
[recommendation helper](dashboards.md), which latches the recommendation (open
only when off, close only when on) and survives restarts.

# Trend awareness (optional)

Plain thresholds are reactive — they wait until the indoor and outdoor
temperatures have *already* converged before recommending a close. On a typical
summer night you ventilate to pull in cool air; as the morning sun arrives the
outside warms and the gap shrinks. By the time the difference collapses to the
close threshold, you may have already let the room warm back up.

Give the blueprint two **rate-of-change sensors** (degrees per hour, one for
indoors and one for outdoors) and it can refine the close decision: close the
windows *early* in the morning, and *hold them open* into an evening cool-down.

## The rule, in plain terms

Let `difference = inside − outside`. The gap is **closing** when

```
inside_trend − outside_trend  ≤  −(minimum convergence rate)
```

i.e. the outdoor temperature is catching up to indoors **faster** than the room
itself is warming. When that is true **and** the difference is sitting inside the
hysteresis band (between the close and open thresholds), the blueprint recommends
closing early. This deliberately captures these cases:

- **Morning, outside cold but rising, room still warm.** The gap is huge, so even
  though outside is rising you keep ventilating — exactly what you want. Only once
  the gap shrinks into the hysteresis band does the early close kick in.
- **Room warming from the sun while outside is still clearly cooler.** Here the
  *difference is growing*, not closing, so ventilation is still winning and the
  windows stay open. The blueprint will not close just because the indoor
  temperature ticked up.
- **Don't make the room hotter than it was.** Closing before full equilibrium
  means you stop pulling in air that is no longer meaningfully cooler.
- **Evening cool-down — keep ventilating.** The mirror image: when the gap is near
  equilibrium but *widening* because outside is dropping faster than the room (a
  typical evening), the blueprint **suppresses** the equilibrium close so you keep
  capturing the cooling. If outside is actually *warmer* (difference ≤ 0) it
  always closes, regardless of trend.

The open recommendation is **unchanged** by trends — opening still happens on the
instantaneous threshold. Trends refine only the *close* decision (closing early
when the gap is shrinking, and holding open when it is widening in your favour).

## Setting up the derivative sensors

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

Create one for the indoor sensor and one for the outdoor sensor, then select them
under *Trend awareness (optional)*. **Leave them blank to disable trend awareness
entirely** — the blueprint then behaves exactly as the temperature-only version.
If a trend sensor is missing or invalid, the blueprint safely falls back to the
plain equilibrium close.

> **Evening behaviour.** The evening cool-down is handled on the *close* side:
> when outside is still cooler and actively dropping, the equilibrium close is
> suppressed so you keep ventilating (see the "Evening cool-down" point above).
> *Opening* is still driven by the instantaneous open threshold — you start
> ventilating as soon as outside is genuinely cooler, without the risk of opening
> early into marginal or still-rising outdoor air. A symmetric *early open* is
> noted in [`TODO.md`](../TODO.md) as a possible future option.
>
> No trend sensors? A simple alternative is to lower the close threshold (e.g. to
> `0.0`) so windows stay "open" while outside is cooler and only close once
> outside is no longer cooler.

---

See [How it works](how-it-works.md#the-algorithm-and-the-science-behind-it) for
how trends fit into the full decision logic.

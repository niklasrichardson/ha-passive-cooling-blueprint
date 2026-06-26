# Troubleshooting & limitations

## Troubleshooting

- **No notifications at all.** Check both sensors show a number in *Developer
  Tools → States* (not `unavailable`). Confirm the room actually reaches the
  minimum indoor temperature and that the difference reaches the open threshold
  for the full stability duration. Lower the stability duration to test quickly.
- **It notifies but never recommends closing.** The difference may not be dropping
  to the close threshold. Check `temperature_difference` against your close
  threshold in *Developer Tools → Template*.
- **Too many notifications / flapping.** Increase the gap between the open and
  close thresholds (bigger dead band) and/or increase the stability duration. For
  a room sitting right at a threshold, link a
  [recommendation helper](dashboards.md#it-also-stops-repeat-notifications) to
  latch the recommendation and stop repeats outright.
- **A "close" arrived in the evening while it was getting cooler.** The base rule
  closes at near-equilibrium. With [trend sensors](trends.md) the evening
  cool-down is held open automatically; without them, lower the close threshold
  toward `0.0` so windows stay open while outside is still cooler.
- **A "close" arrived without an "open" first.** Expected edge case — see
  [How state is tracked](how-it-works.md#how-state-is-tracked). Add an additional
  close condition if you need a strict open→close sequence.
- **Nothing fired right after a restart.** Expected — triggers re-arm on the next
  genuine change. See [How state is tracked](how-it-works.md#how-state-is-tracked).
- **Test the templates live.** Paste the values into *Developer Tools → Template*:
  `{{ is_number(states('sensor.master_bedroom_temperature')) }}`.

## Limitations

This blueprint is deliberately temperature-only (optionally using temperature
*trends*). It does **not** consider: humidity (relative or absolute), weather
forecasts, rain, sun position, indoor air quality, or occupancy (beyond optional
conditions you add yourself). It does **not** control curtains, blinds, motorised
windows, or HVAC — it only *runs the action you choose*. It depends on no custom
integrations.

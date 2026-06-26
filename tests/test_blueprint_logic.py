"""Logic tests for the Passive Cooling Window Recommendation blueprint.

These tests do not run a full Home Assistant instance. Instead they:

1. Parse the blueprint YAML (with a custom ``!input`` constructor) and assert
   its structure is well formed.
2. Extract the *actual* ``value_template`` strings from the two template
   triggers and render them with Jinja2, reproducing Home Assistant's
   ``is_number`` / ``states`` / ``float`` behaviour, to check every scenario
   from the project specification.
3. Simulate Home Assistant's template-trigger *edge* behaviour (a trigger fires
   only on a false -> true transition) to prove that actions are not repeated
   while the recommendation is unchanged.

The Jinja2 rendering is faithful to the real template text, so scenario pass /
fail reflects the logic that ships in the blueprint. The edge simulation models
documented Home Assistant behaviour; it does not exercise HA's `for:` debounce.
"""

import math
import os
import unittest

import yaml
from jinja2 import Environment

BLUEPRINT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "blueprints",
    "automation",
    "niklasrichardson",
    "passive_cooling_window_recommendation.yaml",
)


class Input:
    """Sentinel returned by the ``!input`` YAML tag."""

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Input({self.name!r})"


def _input_constructor(loader, node):
    return Input(loader.construct_scalar(node))


class BlueprintLoader(yaml.SafeLoader):
    pass


BlueprintLoader.add_constructor("!input", _input_constructor)


def load_blueprint():
    with open(BLUEPRINT_PATH, "r", encoding="utf-8") as handle:
        return yaml.load(handle, Loader=BlueprintLoader)


# --- Home Assistant template helpers -------------------------------------- #

def ha_is_number(value):
    """Mirror Home Assistant's ``is_number`` test filter/function."""
    if isinstance(value, bool):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def ha_float(value, default=0.0):
    """Mirror Home Assistant's ``float`` filter with a default."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def make_env():
    env = Environment()
    env.filters["float"] = ha_float
    env.tests["number"] = ha_is_number
    return env


def render(
    template_str,
    *,
    inside_state,
    outside_state,
    context,
    inside_trend_state=None,
    outside_trend_state=None,
    extra_states=None,
):
    """Render a trigger value_template the way HA would and return a bool."""
    env = make_env()
    states = {
        context["inside_entity"]: inside_state,
        context["outside_entity"]: outside_state,
    }
    # Only register trend entities when both the input is configured (a non-empty
    # entity id in the context) and a state was supplied for this scenario.
    if context.get("inside_trend_entity") and inside_trend_state is not None:
        states[context["inside_trend_entity"]] = inside_trend_state
    if context.get("outside_trend_entity") and outside_trend_state is not None:
        states[context["outside_trend_entity"]] = outside_trend_state
    # States for any global-override helper entities referenced by this scenario.
    if extra_states:
        states.update(extra_states)
    globals_ = dict(context)
    # An unconfigured trend input is an empty entity id; states('') -> unknown.
    globals_["states"] = lambda entity: states.get(entity, "unknown")
    globals_["is_number"] = ha_is_number
    globals_["is_state"] = lambda entity, value: states.get(entity, "unknown") == value
    result = env.from_string(template_str).render(**globals_).strip()
    return result.lower() == "true"


class BlueprintStructureTests(unittest.TestCase):
    def setUp(self):
        self.doc = load_blueprint()
        self.blueprint = self.doc["blueprint"]

    def test_metadata(self):
        self.assertEqual(self.blueprint["domain"], "automation")
        self.assertIn("Passive Cooling", self.blueprint["name"])
        self.assertIn("min_version", self.blueprint["homeassistant"])

    def test_all_expected_inputs_present(self):
        names = set()
        for section in self.blueprint["input"].values():
            # Every input here is organised into sections.
            self.assertIn("input", section, "inputs must live inside sections")
            names.update(section["input"].keys())
        expected = {
            "room_area",
            "room_name",
            "inside_temperature_sensor",
            "outside_temperature_sensor",
            "minimum_indoor_temperature",
            "comfort_reopen_band",
            "open_temperature_difference",
            "close_temperature_difference",
            "stability_duration",
            "inside_temperature_trend",
            "outside_temperature_trend",
            "minimum_convergence_rate",
            "minimum_indoor_temperature_global",
            "open_temperature_difference_global",
            "close_temperature_difference_global",
            "minimum_convergence_rate_global",
            "stability_duration_global",
            "status_helper",
            "open_action",
            "close_action",
            "open_additional_conditions",
            "close_additional_conditions",
        }
        self.assertEqual(names, expected)

    def test_trend_inputs_are_optional(self):
        inputs = {}
        for section in self.blueprint["input"].values():
            inputs.update(section["input"])
        # Optional trend inputs must declare a default so they can be left blank.
        for key in ("inside_temperature_trend", "outside_temperature_trend"):
            self.assertIn("default", inputs[key], key)
            self.assertEqual(inputs[key]["default"], "")

    def test_room_identity_inputs_are_optional(self):
        inputs = {}
        for section in self.blueprint["input"].values():
            inputs.update(section["input"])
        # Both the area picker and the room-name override must be optional so the
        # name can be derived from the area (or vice versa).
        for key in ("room_area", "room_name"):
            self.assertIn("default", inputs[key], key)
            self.assertEqual(inputs[key]["default"], "")

    def test_global_override_inputs_are_optional(self):
        inputs = {}
        for section in self.blueprint["input"].values():
            inputs.update(section["input"])
        for key in (
            "minimum_indoor_temperature_global",
            "open_temperature_difference_global",
            "close_temperature_difference_global",
            "minimum_convergence_rate_global",
            "stability_duration_global",
        ):
            self.assertIn("default", inputs[key], key)
            self.assertEqual(inputs[key]["default"], "", key)

    def test_status_helper_is_optional_input_boolean(self):
        inputs = {}
        for section in self.blueprint["input"].values():
            inputs.update(section["input"])
        helper = inputs["status_helper"]
        self.assertEqual(helper["default"], "")
        filt = helper["selector"]["entity"]["filter"][0]
        self.assertEqual(filt["domain"], "input_boolean")

    def test_actions_set_status_helper(self):
        # The open branch turns the helper on; the close branch turns it off.
        actions = self.doc["actions"]
        branches = actions[0]["choose"]
        flat = str(branches)
        self.assertIn("input_boolean.turn_on", flat)
        self.assertIn("input_boolean.turn_off", flat)
        # entity_id must be a TEMPLATE (string), not a bare !input. When no helper
        # is linked the input is "", and a literal empty entity_id fails Home
        # Assistant config validation. A template yields an empty list instead.
        for branch in branches:
            then_step = branch["sequence"][0]["then"][0]
            entity_id = then_step["target"]["entity_id"]
            self.assertIsInstance(entity_id, str, "entity_id must be a template string")
            self.assertIn("{{", entity_id, "entity_id must be templated")

    def test_temperature_sensors_filter_for_temperature(self):
        inputs = {}
        for section in self.blueprint["input"].values():
            inputs.update(section["input"])
        for key in ("inside_temperature_sensor", "outside_temperature_sensor"):
            selector = inputs[key]["selector"]["entity"]
            filt = selector["filter"][0]
            self.assertEqual(filt["domain"], "sensor")
            self.assertEqual(filt["device_class"], "temperature")

    def test_open_default_greater_than_close_default(self):
        inputs = {}
        for section in self.blueprint["input"].values():
            inputs.update(section["input"])
        open_default = inputs["open_temperature_difference"]["default"]
        close_default = inputs["close_temperature_difference"]["default"]
        self.assertGreater(open_default, close_default)

    def test_uses_modern_action_keys(self):
        # Modern HA keys, consistent with the declared minimum version.
        self.assertIn("triggers", self.doc)
        self.assertIn("conditions", self.doc)
        self.assertIn("actions", self.doc)


class TriggerTemplateTests(unittest.TestCase):
    """Render the real trigger templates against the spec scenarios."""

    # Trend inputs left blank (empty entity ids) -> trend awareness disabled,
    # i.e. the temperature-only behaviour. Global-source inputs left blank
    # (empty entity ids) -> the per-automation numbers (..._input) are used.
    CONTEXT = {
        "inside_entity": "sensor.inside",
        "outside_entity": "sensor.outside",
        "inside_trend_entity": "",
        "outside_trend_entity": "",
        "min_indoor_input": 22.0,
        "min_indoor_global": "",
        "open_diff_input": 1.0,
        "open_diff_global": "",
        "close_diff_input": 0.5,
        "close_diff_global": "",
        "converge_rate_input": 0.1,
        "converge_rate_global": "",
        "rec_helper": "",
        "reopen_band": 1.0,
    }

    def setUp(self):
        doc = load_blueprint()
        self.templates = {
            trig["id"]: trig["value_template"] for trig in doc["triggers"]
        }

    def open_true(self, inside, outside, **overrides):
        ctx = dict(self.CONTEXT, **overrides)
        return render(
            self.templates["open"],
            inside_state=inside,
            outside_state=outside,
            context=ctx,
        )

    def close_true(self, inside, outside, **overrides):
        ctx = dict(self.CONTEXT, **overrides)
        return render(
            self.templates["close"],
            inside_state=inside,
            outside_state=outside,
            context=ctx,
        )

    def test_scenario_1_open_recommendation(self):
        self.assertTrue(self.open_true("25.0", "22.0"))
        self.assertFalse(self.close_true("25.0", "22.0"))

    def test_scenario_2_below_minimum(self):
        # Below the comfort floor (22 here): never open, and close — the room is
        # already at/below comfort, so stop ventilating.
        self.assertFalse(self.open_true("20.0", "17.0"))
        self.assertTrue(self.close_true("20.0", "17.0"))

    def test_scenario_3_hysteresis_band_remains_open(self):
        # diff 0.8 sits between close (0.5) and open (1.0): neither edge fires.
        self.assertFalse(self.open_true("23.0", "22.2"))
        self.assertFalse(self.close_true("23.0", "22.2"))

    def test_scenario_4_close_recommendation(self):
        self.assertFalse(self.open_true("22.4", "22.0"))
        self.assertTrue(self.close_true("22.4", "22.0"))

    def test_scenario_5_invalid_sensor_inside(self):
        for bad in ("unavailable", "unknown", "none", "", "n/a"):
            self.assertFalse(self.open_true(bad, "22.0"), bad)
            self.assertFalse(self.close_true(bad, "22.0"), bad)

    def test_scenario_5_invalid_sensor_outside(self):
        for bad in ("unavailable", "unknown", "none", "", "n/a"):
            self.assertFalse(self.open_true("25.0", bad), bad)
            self.assertFalse(self.close_true("25.0", bad), bad)

    def test_invalid_states_never_treated_as_zero(self):
        # If "unavailable" were treated as 0, a warm room would wrongly open.
        self.assertFalse(self.open_true("25.0", "unavailable"))

    def test_open_boundary_inclusive(self):
        # Exactly at the open threshold counts as open (>=).
        self.assertTrue(self.open_true("23.0", "22.0"))

    def test_close_boundary_inclusive(self):
        # Exactly at the close threshold counts as close (<=).
        self.assertTrue(self.close_true("22.5", "22.0"))

    def test_open_requires_comfort_floor_plus_band(self):
        # Opening requires the room to reach the comfort floor + re-open band
        # (22 + 1 = 23 here): at exactly that it opens; just below it does not.
        self.assertTrue(self.open_true("23.0", "20.0"))
        self.assertFalse(self.open_true("22.9", "20.0"))

    def test_comfort_floor_close(self):
        # The room at/below the comfort floor closes regardless of outside.
        self.assertTrue(self.close_true("22.0", "10.0"))   # at the floor
        self.assertTrue(self.close_true("21.5", "10.0"))   # below the floor
        # Just above the floor (still within the band), a big gap does not open
        # and the floor close does not fire: hold.
        self.assertFalse(self.open_true("22.5", "10.0"))
        self.assertFalse(self.close_true("22.5", "21.0"))

    def test_fahrenheit_scaled_thresholds(self):
        # Same logic, Fahrenheit values and a Fahrenheit-scaled threshold.
        self.assertTrue(
            self.open_true("77.0", "72.0", min_indoor_input=72.0, open_diff_input=2.0)
        )
        self.assertTrue(
            self.close_true("73.0", "72.5", min_indoor_input=72.0, close_diff_input=1.0)
        )


def simulate_edges(template, sequence, context):
    """Count false->true edges (HA template-trigger fire count)."""
    previous = False
    fires = 0
    for inside_state, outside_state in sequence:
        current = render(
            template,
            inside_state=inside_state,
            outside_state=outside_state,
            context=context,
        )
        if current and not previous:
            fires += 1
        previous = current
    return fires


class EdgeBehaviourTests(unittest.TestCase):
    CONTEXT = TriggerTemplateTests.CONTEXT

    def setUp(self):
        doc = load_blueprint()
        self.templates = {
            trig["id"]: trig["value_template"] for trig in doc["triggers"]
        }

    def test_scenario_6_no_repeated_open_action(self):
        # Stays in the open band across several updates -> exactly one fire.
        sequence = [
            ("25.0", "22.0"),
            ("24.5", "22.0"),
            ("24.0", "22.0"),
            ("23.5", "22.0"),
        ]
        self.assertEqual(
            simulate_edges(self.templates["open"], sequence, self.CONTEXT), 1
        )
        self.assertEqual(
            simulate_edges(self.templates["close"], sequence, self.CONTEXT), 0
        )

    def test_scenario_7_threshold_fluctuation_is_stable(self):
        # Oscillate within the hysteresis band after an initial open. No close
        # should ever fire and open should not re-fire.
        sequence = [
            ("25.0", "22.0"),  # open band -> open fires
            ("23.0", "22.2"),  # hysteresis (0.8)
            ("23.0", "22.1"),  # hysteresis (0.9)
            ("23.0", "22.3"),  # hysteresis (0.7)
            ("23.0", "22.2"),  # hysteresis (0.8)
        ]
        self.assertEqual(
            simulate_edges(self.templates["open"], sequence, self.CONTEXT), 1
        )
        self.assertEqual(
            simulate_edges(self.templates["close"], sequence, self.CONTEXT), 0
        )

    def test_full_open_then_close_cycle(self):
        # Open -> hysteresis -> close -> warm again -> open. Each action once.
        sequence = [
            ("25.0", "22.0"),  # open
            ("23.0", "22.2"),  # hysteresis
            ("22.4", "22.0"),  # close band
            ("22.2", "22.0"),  # still close band
            ("25.0", "22.0"),  # open band again
        ]
        self.assertEqual(
            simulate_edges(self.templates["open"], sequence, self.CONTEXT), 2
        )
        self.assertEqual(
            simulate_edges(self.templates["close"], sequence, self.CONTEXT), 1
        )

    def test_invalid_sensor_does_not_fire_close(self):
        # Open, then sensor drops out: close must NOT fire on invalid data.
        sequence = [
            ("25.0", "22.0"),       # open
            ("unavailable", "22.0"),  # sensor lost
            ("unknown", "22.0"),
        ]
        self.assertEqual(
            simulate_edges(self.templates["close"], sequence, self.CONTEXT), 0
        )


class TrendEarlyCloseTests(unittest.TestCase):
    """Convergence-based early close using optional trend sensors.

    difference = inside - outside. The gap is "closing" when
    (inside_rate - outside_rate) is sufficiently negative, i.e. outside is
    catching up to inside faster than the room is warming.
    """

    CONTEXT = {
        "inside_entity": "sensor.inside",
        "outside_entity": "sensor.outside",
        "inside_trend_entity": "sensor.inside_rate",
        "outside_trend_entity": "sensor.outside_rate",
        "min_indoor_input": 22.0,
        "min_indoor_global": "",
        "open_diff_input": 1.0,
        "open_diff_global": "",
        "close_diff_input": 0.5,
        "close_diff_global": "",
        "converge_rate_input": 0.1,
        "converge_rate_global": "",
        "rec_helper": "",
        "reopen_band": 1.0,
    }

    def setUp(self):
        doc = load_blueprint()
        self.templates = {
            trig["id"]: trig["value_template"] for trig in doc["triggers"]
        }

    def close(self, inside, outside, inside_rate, outside_rate):
        return render(
            self.templates["close"],
            inside_state=inside,
            outside_state=outside,
            inside_trend_state=inside_rate,
            outside_trend_state=outside_rate,
            context=self.CONTEXT,
        )

    def open_(self, inside, outside, inside_rate, outside_rate):
        return render(
            self.templates["open"],
            inside_state=inside,
            outside_state=outside,
            inside_trend_state=inside_rate,
            outside_trend_state=outside_rate,
            context=self.CONTEXT,
        )

    def test_morning_cold_but_rising_outside_keeps_ventilating(self):
        # Outside cold (16) and rising fast, room warm (24): big gap -> stay open,
        # do NOT close even though the gap is technically closing.
        self.assertTrue(self.open_("24.0", "16.0", "0.0", "2.0"))
        self.assertFalse(self.close("24.0", "16.0", "0.0", "2.0"))

    def test_converging_in_hysteresis_band_closes_early(self):
        # diff 0.8 (in the 0.5-1.0 gap) and outside catching up -> early close.
        self.assertFalse(self.open_("22.8", "22.0", "0.0", "1.0"))
        self.assertTrue(self.close("22.8", "22.0", "0.0", "1.0"))

    def test_room_warming_but_outside_still_cooler_stays_open(self):
        # diff 0.8 but the gap is GROWING (room warming, outside steady):
        # ventilation is still winning, so do not close early.
        self.assertFalse(self.close("22.8", "22.0", "1.0", "0.0"))

    def test_slow_convergence_below_rate_does_not_close(self):
        # Gap closing but slower than the minimum convergence rate (0.1/h).
        self.assertFalse(self.close("22.8", "22.0", "0.0", "0.05"))

    def test_equilibrium_closes_when_outside_steady(self):
        # Base equilibrium close fires when outside is steady (no hold-open).
        self.assertTrue(self.close("22.4", "22.0", "0.0", "0.0"))

    def test_equilibrium_holds_when_outside_still_dropping(self):
        # Both dropping fast (outside still actively cooling) -> keep ventilating,
        # the room can keep tracking the falling outdoor temperature down.
        self.assertFalse(self.close("22.4", "22.0", "-5.0", "-5.0"))

    def test_early_close_not_triggered_above_open_band(self):
        # diff 1.5 is in the open band: never an early close there.
        self.assertFalse(self.close("23.5", "22.0", "0.0", "5.0"))

    def test_invalid_trend_sensor_falls_back_to_temperature_only(self):
        # A broken trend sensor must not enable early close, and must not error.
        self.assertFalse(self.close("22.8", "22.0", "unavailable", "unknown"))
        # ...but the base equilibrium close still works.
        self.assertTrue(self.close("22.4", "22.0", "unavailable", "unknown"))

    def test_evening_widening_gap_suppresses_close(self):
        # diff 0.4 (in the close band) but outside dropping fast -> the gap is
        # widening, so keep ventilating instead of closing.
        self.assertFalse(self.close("28.9", "28.5", "0.0", "-1.0"))

    def test_morning_converging_still_closes_at_equilibrium(self):
        # diff 0.4 with outside RISING (gap closing) -> equilibrium close stands.
        self.assertTrue(self.close("22.4", "22.0", "0.0", "1.0"))

    def test_widening_but_outside_warmer_still_closes(self):
        # Outside warmer (diff -0.5): always close, even if it is cooling fast.
        self.assertTrue(self.close("22.0", "22.5", "0.0", "-2.0"))

    def test_widening_below_rate_still_closes(self):
        # Gap widening slower than the convergence rate (0.1/h) -> still closes.
        self.assertTrue(self.close("22.4", "22.0", "0.0", "-0.05"))

    def test_evening_room_cooling_fast_does_not_early_close(self):
        # Evening: diff 0.7 (dead band), but the gap is shrinking only because the
        # ROOM is cooling faster than outside (good ventilation) while outside is
        # DROPPING. The difference trend is negative (-1.0), which the old logic
        # mistook for a morning convergence. It must NOT early close.
        self.assertFalse(self.close("28.3", "27.6", "-2.0", "-1.0"))

    def test_early_close_requires_outside_warming(self):
        # Same converging difference trend, but outside is flat (not warming):
        # the room is simply cooling toward a steady outside -> keep ventilating.
        self.assertFalse(self.close("22.8", "22.0", "-1.0", "0.0"))
        # Outside genuinely rising at/above the rate -> early close as intended.
        self.assertTrue(self.close("22.8", "22.0", "0.0", "0.1"))

    def test_comfort_floor_bounds_evening_hold(self):
        # Evening, outside still cooling (would normally hold open), but the room
        # has reached the comfort floor (22) -> close to avoid over-cooling.
        self.assertTrue(self.close("22.0", "20.0", "-1.0", "-1.0"))


class GlobalOverrideTests(unittest.TestCase):
    """A configured, valid global helper overrides the per-automation number;
    a blank or invalid global falls back to the local number."""

    BASE = {
        "inside_entity": "sensor.inside",
        "outside_entity": "sensor.outside",
        "inside_trend_entity": "",
        "outside_trend_entity": "",
        "min_indoor_input": 22.0,
        "min_indoor_global": "",
        "open_diff_input": 1.0,
        "open_diff_global": "",
        "close_diff_input": 0.5,
        "close_diff_global": "",
        "converge_rate_input": 0.1,
        "converge_rate_global": "",
        "rec_helper": "",
        "reopen_band": 1.0,
    }

    def setUp(self):
        doc = load_blueprint()
        self.templates = {
            trig["id"]: trig["value_template"] for trig in doc["triggers"]
        }

    def test_global_min_indoor_overrides_local(self):
        # Local min 22 would allow opening a 25 deg room; the global helper
        # raises the minimum to 26, which blocks it.
        ctx = dict(self.BASE, min_indoor_global="input_number.global_min")
        self.assertFalse(
            render(
                self.templates["open"],
                inside_state="25.0",
                outside_state="20.0",
                context=ctx,
                extra_states={"input_number.global_min": "26.0"},
            )
        )
        # Same scenario without the global -> local 22 applies -> opens.
        self.assertTrue(
            render(
                self.templates["open"],
                inside_state="25.0",
                outside_state="20.0",
                context=self.BASE,
            )
        )

    def test_global_open_diff_overrides_local(self):
        # 3 deg gap opens under local 1.0; global raises open diff to 5 -> no open.
        ctx = dict(self.BASE, open_diff_global="input_number.global_open")
        self.assertFalse(
            render(
                self.templates["open"],
                inside_state="25.0",
                outside_state="22.0",
                context=ctx,
                extra_states={"input_number.global_open": "5.0"},
            )
        )

    def test_global_close_diff_overrides_local(self):
        # diff 0.8 holds under local close 0.5; global raises close to 1.0 -> closes.
        ctx = dict(self.BASE, close_diff_global="input_number.global_close")
        self.assertTrue(
            render(
                self.templates["close"],
                inside_state="22.8",
                outside_state="22.0",
                context=ctx,
                extra_states={"input_number.global_close": "1.0"},
            )
        )

    def test_invalid_global_falls_back_to_local(self):
        # Global linked but unavailable -> use local 1.0 -> 3 deg gap still opens.
        ctx = dict(self.BASE, open_diff_global="input_number.global_open")
        self.assertTrue(
            render(
                self.templates["open"],
                inside_state="25.0",
                outside_state="22.0",
                context=ctx,
                extra_states={"input_number.global_open": "unavailable"},
            )
        )

    def test_global_convergence_rate_overrides_local(self):
        # diff 0.8 (dead band), difference_trend -0.2.
        ctx = dict(
            self.BASE,
            inside_trend_entity="sensor.in_rate",
            outside_trend_entity="sensor.out_rate",
            converge_rate_global="input_number.global_conv",
        )
        # Global rate 0.5: -0.2 is NOT <= -0.5 -> no early close.
        self.assertFalse(
            render(
                self.templates["close"],
                inside_state="22.8",
                outside_state="22.0",
                inside_trend_state="0.0",
                outside_trend_state="0.2",
                context=ctx,
                extra_states={"input_number.global_conv": "0.5"},
            )
        )
        # Local rate 0.1 (no global): -0.2 <= -0.1 -> early close.
        ctx_local = dict(
            self.BASE,
            inside_trend_entity="sensor.in_rate",
            outside_trend_entity="sensor.out_rate",
        )
        self.assertTrue(
            render(
                self.templates["close"],
                inside_state="22.8",
                outside_state="22.0",
                inside_trend_state="0.0",
                outside_trend_state="0.2",
                context=ctx_local,
            )
        )


class StabilityDurationForTests(unittest.TestCase):
    """The trigger `for:` (stability duration) resolves the global helper
    (interpreted as minutes) when set and valid, otherwise the per-automation
    duration. Output is a whole number of seconds."""

    def setUp(self):
        doc = load_blueprint()
        self.fors = {trig["id"]: trig["for"] for trig in doc["triggers"]}

    def render_for(self, *, stability_dur, stability_global="", extra_states=None):
        env = make_env()
        states = dict(extra_states or {})
        ctx = {
            "stability_dur": stability_dur,
            "stability_global": stability_global,
            "states": lambda entity: states.get(entity, "unknown"),
            "is_number": ha_is_number,
        }
        out = env.from_string(self.fors["open"]).render(**ctx).strip()
        return int(out)

    def test_open_and_close_for_are_identical(self):
        self.assertEqual(self.fors["open"], self.fors["close"])

    def test_local_minutes_only_duration(self):
        # 5 minutes -> 300 seconds; missing day/hour/second keys default to 0.
        self.assertEqual(self.render_for(stability_dur={"minutes": 5}), 300)

    def test_local_compound_duration(self):
        self.assertEqual(
            self.render_for(stability_dur={"hours": 1, "minutes": 2, "seconds": 3}),
            3723,
        )

    def test_global_minutes_override_local(self):
        self.assertEqual(
            self.render_for(
                stability_dur={"minutes": 5},
                stability_global="input_number.global_stability",
                extra_states={"input_number.global_stability": "2"},
            ),
            120,
        )

    def test_invalid_global_falls_back_to_local(self):
        for bad in ("unavailable", "unknown", "none", "", "n/a"):
            self.assertEqual(
                self.render_for(
                    stability_dur={"minutes": 5},
                    stability_global="input_number.global_stability",
                    extra_states={"input_number.global_stability": bad},
                ),
                300,
                bad,
            )


class RecommendationLatchTests(unittest.TestCase):
    """When a recommendation helper is linked it latches the recommendation:
    open fires only while the helper is off, close only while it is on, so a
    difference that merely oscillates across a threshold cannot re-fire."""

    HELPER = "input_boolean.passive_cooling_room"
    BASE = {
        "inside_entity": "sensor.inside",
        "outside_entity": "sensor.outside",
        "inside_trend_entity": "",
        "outside_trend_entity": "",
        "min_indoor_input": 22.0,
        "min_indoor_global": "",
        "open_diff_input": 1.0,
        "open_diff_global": "",
        "close_diff_input": 0.5,
        "close_diff_global": "",
        "converge_rate_input": 0.1,
        "converge_rate_global": "",
        "rec_helper": "",
        "reopen_band": 1.0,
    }

    def setUp(self):
        doc = load_blueprint()
        self.templates = {
            trig["id"]: trig["value_template"] for trig in doc["triggers"]
        }

    def _render(self, which, inside, outside, *, helper_linked, helper_state):
        ctx = dict(self.BASE, rec_helper=self.HELPER if helper_linked else "")
        return render(
            self.templates[which],
            inside_state=inside,
            outside_state=outside,
            context=ctx,
            extra_states={self.HELPER: helper_state},
        )

    def test_open_blocked_when_already_open(self):
        # Open conditions met, but helper already on -> do not re-open.
        self.assertFalse(
            self._render("open", "25.0", "20.0", helper_linked=True, helper_state="on")
        )

    def test_open_allowed_when_not_open(self):
        self.assertTrue(
            self._render("open", "25.0", "20.0", helper_linked=True, helper_state="off")
        )

    def test_close_blocked_when_not_open(self):
        # Close conditions met, but helper off (not currently open) -> no close.
        self.assertFalse(
            self._render("close", "22.4", "22.0", helper_linked=True, helper_state="off")
        )

    def test_close_allowed_when_open(self):
        self.assertTrue(
            self._render("close", "22.4", "22.0", helper_linked=True, helper_state="on")
        )

    def _simulate(self, sequence, *, helper_linked):
        """Replay a sequence, modelling the action toggling the latch helper."""
        helper = "off"
        opens = closes = 0
        prev_open = prev_close = False
        ctx = dict(self.BASE, rec_helper=self.HELPER if helper_linked else "")
        for inside_state, outside_state in sequence:
            extra = {self.HELPER: helper}
            o = render(self.templates["open"], inside_state=inside_state,
                       outside_state=outside_state, context=ctx, extra_states=extra)
            c = render(self.templates["close"], inside_state=inside_state,
                       outside_state=outside_state, context=ctx, extra_states=extra)
            if o and not prev_open:
                opens += 1
                helper = "on"
            elif c and not prev_close:
                closes += 1
                helper = "off"
            prev_open, prev_close = o, c
        return opens, closes

    # A room at the open threshold: inside steady, outside drifting across it.
    OSCILLATION = [
        ("31.2", "30.1"),  # diff 1.1 -> open
        ("31.2", "30.3"),  # diff 0.9 -> dead band
        ("31.2", "30.1"),  # diff 1.1 -> open again
        ("31.2", "30.3"),  # diff 0.9 -> dead band
        ("31.2", "30.1"),  # diff 1.1 -> open again
    ]

    def test_oscillation_repeats_without_helper(self):
        opens, _ = self._simulate(self.OSCILLATION, helper_linked=False)
        self.assertEqual(opens, 3)  # the bug: one notification per re-crossing

    def test_oscillation_fires_once_with_latch(self):
        opens, _ = self._simulate(self.OSCILLATION, helper_linked=True)
        self.assertEqual(opens, 1)  # latched: a single notification


class ComprehensiveScenarioMatrixTests(unittest.TestCase):
    """Exhaustive truth table: every difference band crossed with every trend
    regime, plus boundaries and the no-trend cases. Each row asserts the expected
    open and close outcome with the thresholds min=22, open=1.0, close=0.5,
    rate=0.1. Trend rates are degrees/hour."""

    TREND_CTX = TrendEarlyCloseTests.CONTEXT
    PLAIN_CTX = TriggerTemplateTests.CONTEXT

    def setUp(self):
        doc = load_blueprint()
        self.templates = {t["id"]: t["value_template"] for t in doc["triggers"]}

    def _pair(self, ctx, inside, outside, in_rate=None, out_rate=None):
        kw = dict(inside_state=inside, outside_state=outside, context=ctx)
        if in_rate is not None:
            kw.update(inside_trend_state=in_rate, outside_trend_state=out_rate)
        o = render(self.templates["open"], **kw)
        c = render(self.templates["close"], **kw)
        return o, c

    # (label, inside, outside, in_rate, out_rate, expect_open, expect_close)
    WITH_TREND = [
        # Open band (diff >= 1.0): always open, never close, trend irrelevant.
        ("open/outside-warming", "25", "23.5", "0", "1.0", True, False),
        ("open/outside-cooling", "25", "23.5", "0", "-1.0", True, False),
        ("open/room-cooling-fast", "25", "23.5", "-2.0", "-1.0", True, False),
        # Dead band (0.5 < diff < 1.0): early close ONLY if outside warming.
        ("dead/morning-early-close", "25", "24.2", "0", "1.0", False, True),
        ("dead/evening-room-cooling-fast", "25", "24.2", "-2.0", "-1.0", False, False),
        ("dead/evening-outside-dropping", "25", "24.2", "0", "-1.0", False, False),
        ("dead/outside-flat-room-cooling", "25", "24.2", "-1.0", "0", False, False),
        ("dead/warming-below-rate", "25", "24.2", "0", "0.05", False, False),
        ("dead/room-warming-outside-flat", "25", "24.2", "1.0", "0", False, False),
        ("dead/boundary-early-close", "25", "24.2", "0", "0.1", False, True),
        # Close band (0 < diff <= 0.5): base close UNLESS hold-open.
        ("close/equilibrium-steady", "25", "24.6", "0", "0", False, True),
        ("close/morning-equilibrium", "25", "24.6", "0", "1.0", False, True),
        ("close/evening-widening", "25", "24.6", "0", "-1.0", False, False),
        ("close/evening-room-cooling-fast", "25", "24.6", "-2.0", "-1.0", False, False),
        ("close/room-warming-outside-flat", "25", "24.6", "0.5", "0", False, False),
        ("close/outside-barely-moving", "25", "24.6", "0", "-0.05", False, True),
        ("close/both-dropping-fast-holds", "25", "24.6", "-5.0", "-5.0", False, False),
        # Outside warmer (diff <= 0): always close, never hold.
        ("warmer/outside-cooling-fast", "22", "22.5", "0", "-2.0", False, True),
        ("warmer/steady", "22", "22.5", "0", "0", False, True),
        # Minimum-indoor gate and boundaries.
        # Comfort floor (min 22, re-open band 1.0 -> open gate 23).
        ("floor/below-floor-closes", "21", "18", "0", "0", False, True),
        ("floor/at-floor-closes", "22", "10", "0", "0", False, True),
        ("floor/in-band-holds", "22.5", "10", "0", "0", False, False),
        ("floor/at-floor-plus-band-opens", "23", "22.0", "0", "0", True, False),
        ("boundary/close-threshold-inclusive", "25", "24.5", "0", "0", False, True),
    ]

    # Without trend sensors: pure threshold behaviour.
    NO_TREND = [
        ("open-band", "25", "23.5", True, False),
        ("dead-band-holds", "25", "24.2", False, False),
        ("close-band-closes", "25", "24.6", False, True),
        ("outside-warmer-closes", "22", "22.5", False, True),
        ("below-floor-closes", "21", "18", False, True),
        ("at-floor-closes", "22", "10", False, True),
        ("in-band-holds", "22.5", "10", False, False),
        ("open-boundary-at-floor-plus-band", "23", "22.0", True, False),
        ("close-boundary", "25", "24.5", False, True),
    ]

    def test_with_trend_matrix(self):
        for label, ins, out, ir, orr, eo, ec in self.WITH_TREND:
            with self.subTest(label):
                o, c = self._pair(self.TREND_CTX, ins, out, ir, orr)
                self.assertEqual(o, eo, f"{label}: open expected {eo}, got {o}")
                self.assertEqual(c, ec, f"{label}: close expected {ec}, got {c}")

    def test_no_trend_matrix(self):
        for label, ins, out, eo, ec in self.NO_TREND:
            with self.subTest(label):
                o, c = self._pair(self.PLAIN_CTX, ins, out)
                self.assertEqual(o, eo, f"{label}: open expected {eo}, got {o}")
                self.assertEqual(c, ec, f"{label}: close expected {ec}, got {c}")

    def test_open_and_close_never_both_true(self):
        # Open and close must be mutually exclusive in every trend scenario.
        for label, ins, out, ir, orr, _eo, _ec in self.WITH_TREND:
            with self.subTest(label):
                o, c = self._pair(self.TREND_CTX, ins, out, ir, orr)
                self.assertFalse(o and c, f"{label}: open and close both fired")


if __name__ == "__main__":
    unittest.main(verbosity=2)

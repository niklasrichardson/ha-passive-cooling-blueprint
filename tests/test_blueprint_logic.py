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


def render(template_str, *, inside_state, outside_state, context):
    """Render a trigger value_template the way HA would and return a bool."""
    env = make_env()
    states = {
        context["inside_entity"]: inside_state,
        context["outside_entity"]: outside_state,
    }
    globals_ = dict(context)
    globals_["states"] = lambda entity: states.get(entity, "unknown")
    globals_["is_number"] = ha_is_number
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
            "room_name",
            "inside_temperature_sensor",
            "outside_temperature_sensor",
            "minimum_indoor_temperature",
            "open_temperature_difference",
            "close_temperature_difference",
            "stability_duration",
            "open_action",
            "close_action",
            "open_additional_conditions",
            "close_additional_conditions",
        }
        self.assertEqual(names, expected)

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

    CONTEXT = {
        "inside_entity": "sensor.inside",
        "outside_entity": "sensor.outside",
        "min_indoor": 22.0,
        "open_diff": 1.0,
        "close_diff": 0.5,
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
        self.assertFalse(self.open_true("20.0", "17.0"))
        self.assertFalse(self.close_true("20.0", "17.0"))

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

    def test_minimum_boundary_inclusive(self):
        # Inside exactly at the minimum still qualifies to open.
        self.assertTrue(self.open_true("22.0", "20.0"))

    def test_fahrenheit_scaled_thresholds(self):
        # Same logic, Fahrenheit values and a Fahrenheit-scaled threshold.
        self.assertTrue(
            self.open_true("77.0", "72.0", min_indoor=72.0, open_diff=2.0)
        )
        self.assertTrue(
            self.close_true("73.0", "72.5", min_indoor=72.0, close_diff=1.0)
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


if __name__ == "__main__":
    unittest.main(verbosity=2)

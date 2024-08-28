import json


def assertEqualJson(actual, expected):
    """Compare the JSON representation of 2 Python objects.

    This allows to take into account things like the order of key-value pairs
    in dictionaries, which would not be taken into account when comparing
    dictionaries directly.

    It also generates a better diff in pytest output when enums are involved,
    e.g. geolocation values.
    """
    actual_json = json.dumps(actual, indent=2)
    expected_json = json.dumps(expected, indent=2)
    assert actual_json == expected_json

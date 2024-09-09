import json


def assertEqualSpiderMetadata(actual, expected):
    """Compare 2 JSON schemas of spider metadata.

    The parameter order in the parameter schema is taken into account, given
    how it affects the UI, while the order of other object keys may be
    different.

    It also generates a better diff in pytest output when enums are involved,
    e.g. geolocation values.
    """
    assert tuple(actual["param_schema"]["properties"]) == tuple(
        expected["param_schema"]["properties"]
    )
    actual_json = json.dumps(actual, indent=2, sort_keys=True)
    expected_json = json.dumps(expected, indent=2, sort_keys=True)
    assert actual_json == expected_json

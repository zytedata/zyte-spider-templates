import pytest
from pydantic import ValidationError

from zyte_spider_templates.params import LocationParam


def test_valid_location_param():
    valid_address_dict = {
        "streetAddress": "123 Main St",
        "addressCountry": "US",
        "addressRegion": "CA",
        "postalCode": "12345",
    }
    location_param = LocationParam(location=valid_address_dict)  # type: ignore[arg-type]
    assert location_param.location is not None
    assert location_param.location.streetAddress == "123 Main St"
    assert location_param.location.addressCountry == "US"
    assert location_param.location.addressRegion == "CA"
    assert location_param.location.postalCode == "12345"


def test_valid_location_param_from_json():
    valid_address_json = '{"streetAddress": "456 Elm St", "addressCountry": "US", "addressRegion": "NY", "postalCode": "54321"}'
    location_param = LocationParam(location=valid_address_json)  # type: ignore[arg-type]
    assert location_param.location is not None
    assert location_param.location.streetAddress == "456 Elm St"
    assert location_param.location.addressCountry == "US"
    assert location_param.location.addressRegion == "NY"
    assert location_param.location.postalCode == "54321"


def test_none_location_param():
    location_param = LocationParam(location=None)
    assert location_param.location is None


def test_invalid_json_location_param():
    invalid_address_json = '{"streetAddress": "789 Pine St", "addressCountry": "AnotheraddressCountry", "addressRegion": "FL", "postalCode": "67890"'
    with pytest.raises(ValueError, match=r".* is not a valid JSON object"):
        LocationParam(location=invalid_address_json)  # type: ignore[arg-type]


def test_invalid_type_location_param():
    invalid_type_value = 12345  # Invalid type, should raise ValueError
    with pytest.raises(ValueError, match=r".* type .* is not a supported type"):
        LocationParam(location=invalid_type_value)  # type: ignore[arg-type]


def test_invalid_validation_location_param():
    invalid_address_json = '{"nonExpectedInputField": "67890"}'
    with pytest.raises(ValidationError, match=r"Extra inputs are not permitted .*"):
        LocationParam(location=invalid_address_json)  # type: ignore[arg-type]

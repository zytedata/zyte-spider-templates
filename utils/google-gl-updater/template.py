{% raw %}# ../_geolocations.py counterpart for
# https://developers.google.com/custom-search/docs/json_api_reference#countryCodes
#
# Built automatically with ../../utils/google-gl-updater

from enum import Enum

GOOGLE_GL_OPTIONS = {{% endraw %}{% for country in countries %}
    "{{ country.code }}": "{{ country.name }}",{% endfor %}{% raw %}
}
GOOGLE_GL_OPTIONS_WITH_CODE = {
    code: f"{name} ({code})" for code, name in GOOGLE_GL_OPTIONS.items()
}


class GoogleGl(str, Enum):{% endraw %}{% for country in countries %}
    {{ country.keyword }}: str = "{{ country.code }}"{% endfor %}


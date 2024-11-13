{% raw %}# _google_gl.py counterpart for
# https://developers.google.com/custom-search/docs/json_api_reference#interfaceLanguages
#
# Built automatically with ../../utils/google-hl-updater

from enum import Enum

GOOGLE_HL_OPTIONS = {{% endraw %}{% for language in languages %}
    "{{ language.code }}": "{{ language.name }}",{% endfor %}{% raw %}
}
GOOGLE_HL_OPTIONS_WITH_CODE = {
    code: f"{name} ({code})" for code, name in GOOGLE_HL_OPTIONS.items()
}


class GoogleHl(str, Enum):{% endraw %}{% for language in languages %}
    {{ language.keyword }}: str = "{{ language.code }}"{% endfor %}


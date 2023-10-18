# codes from https://docs.zyte.com/zyte-api/usage/reference.html#operation/extract/request/geolocation
# names from pycountry, initially from the ISO database
from enum import Enum

GEOLOCATION_OPTIONS = {
    "AW": "Aruba",
    "AF": "Afghanistan",
    "AO": "Angola",
    "AI": "Anguilla",
    "AX": "Åland Islands",
    "AL": "Albania",
    "AD": "Andorra",
    "AE": "United Arab Emirates",
    "AR": "Argentina",
    "AM": "Armenia",
    "AS": "American Samoa",
    "AQ": "Antarctica",
    "TF": "French Southern Territories",
    "AG": "Antigua and Barbuda",
    "AU": "Australia",
    "AT": "Austria",
    "AZ": "Azerbaijan",
    "BI": "Burundi",
    "BE": "Belgium",
    "BJ": "Benin",
    "BQ": "Bonaire, Sint Eustatius and Saba",
    "BF": "Burkina Faso",
    "BD": "Bangladesh",
    "BG": "Bulgaria",
    "BH": "Bahrain",
    "BS": "Bahamas",
    "BA": "Bosnia and Herzegovina",
    "BL": "Saint Barthélemy",
    "BY": "Belarus",
    "BZ": "Belize",
    "BM": "Bermuda",
    "BO": "Bolivia, Plurinational State of",
    "BR": "Brazil",
    "BB": "Barbados",
    "BN": "Brunei Darussalam",
    "BT": "Bhutan",
    "BV": "Bouvet Island",
    "BW": "Botswana",
    "CF": "Central African Republic",
    "CA": "Canada",
    "CC": "Cocos (Keeling) Islands",
    "CH": "Switzerland",
    "CL": "Chile",
    "CN": "China",
    "CI": "Côte d'Ivoire",
    "CM": "Cameroon",
    "CD": "Congo, The Democratic Republic of the",
    "CG": "Congo",
    "CK": "Cook Islands",
    "CO": "Colombia",
    "KM": "Comoros",
    "CV": "Cabo Verde",
    "CR": "Costa Rica",
    "CU": "Cuba",
    "CW": "Curaçao",
    "CX": "Christmas Island",
    "KY": "Cayman Islands",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DE": "Germany",
    "DJ": "Djibouti",
    "DM": "Dominica",
    "DK": "Denmark",
    "DO": "Dominican Republic",
    "DZ": "Algeria",
    "EC": "Ecuador",
    "EG": "Egypt",
    "ER": "Eritrea",
    "EH": "Western Sahara",
    "ES": "Spain",
    "EE": "Estonia",
    "ET": "Ethiopia",
    "FI": "Finland",
    "FJ": "Fiji",
    "FK": "Falkland Islands (Malvinas)",
    "FR": "France",
    "FO": "Faroe Islands",
    "FM": "Micronesia, Federated States of",
    "GA": "Gabon",
    "GB": "United Kingdom",
    "GE": "Georgia",
    "GG": "Guernsey",
    "GH": "Ghana",
    "GI": "Gibraltar",
    "GN": "Guinea",
    "GP": "Guadeloupe",
    "GM": "Gambia",
    "GW": "Guinea-Bissau",
    "GQ": "Equatorial Guinea",
    "GR": "Greece",
    "GD": "Grenada",
    "GL": "Greenland",
    "GT": "Guatemala",
    "GF": "French Guiana",
    "GU": "Guam",
    "GY": "Guyana",
    "HK": "Hong Kong",
    "HM": "Heard Island and McDonald Islands",
    "HN": "Honduras",
    "HR": "Croatia",
    "HT": "Haiti",
    "HU": "Hungary",
    "ID": "Indonesia",
    "IM": "Isle of Man",
    "IN": "India",
    "IO": "British Indian Ocean Territory",
    "IE": "Ireland",
    "IR": "Iran, Islamic Republic of",
    "IQ": "Iraq",
    "IS": "Iceland",
    "IL": "Israel",
    "IT": "Italy",
    "JM": "Jamaica",
    "JE": "Jersey",
    "JO": "Jordan",
    "JP": "Japan",
    "KZ": "Kazakhstan",
    "KE": "Kenya",
    "KG": "Kyrgyzstan",
    "KH": "Cambodia",
    "KI": "Kiribati",
    "KN": "Saint Kitts and Nevis",
    "KR": "Korea, Republic of",
    "KW": "Kuwait",
    "LA": "Lao People's Democratic Republic",
    "LB": "Lebanon",
    "LR": "Liberia",
    "LY": "Libya",
    "LC": "Saint Lucia",
    "LI": "Liechtenstein",
    "LK": "Sri Lanka",
    "LS": "Lesotho",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "MO": "Macao",
    "MF": "Saint Martin (French part)",
    "MA": "Morocco",
    "MC": "Monaco",
    "MD": "Moldova, Republic of",
    "MG": "Madagascar",
    "MV": "Maldives",
    "MX": "Mexico",
    "MH": "Marshall Islands",
    "MK": "North Macedonia",
    "ML": "Mali",
    "MT": "Malta",
    "MM": "Myanmar",
    "ME": "Montenegro",
    "MN": "Mongolia",
    "MP": "Northern Mariana Islands",
    "MZ": "Mozambique",
    "MR": "Mauritania",
    "MS": "Montserrat",
    "MQ": "Martinique",
    "MU": "Mauritius",
    "MW": "Malawi",
    "MY": "Malaysia",
    "YT": "Mayotte",
    "NA": "Namibia",
    "NC": "New Caledonia",
    "NE": "Niger",
    "NF": "Norfolk Island",
    "NG": "Nigeria",
    "NI": "Nicaragua",
    "NU": "Niue",
    "NL": "Netherlands",
    "NO": "Norway",
    "NP": "Nepal",
    "NR": "Nauru",
    "NZ": "New Zealand",
    "OM": "Oman",
    "PK": "Pakistan",
    "PA": "Panama",
    "PN": "Pitcairn",
    "PE": "Peru",
    "PH": "Philippines",
    "PW": "Palau",
    "PG": "Papua New Guinea",
    "PL": "Poland",
    "PR": "Puerto Rico",
    "KP": "Korea, Democratic People's Republic of",
    "PT": "Portugal",
    "PY": "Paraguay",
    "PS": "Palestine, State of",
    "PF": "French Polynesia",
    "QA": "Qatar",
    "RE": "Réunion",
    "RO": "Romania",
    "RU": "Russian Federation",
    "RW": "Rwanda",
    "SA": "Saudi Arabia",
    "SD": "Sudan",
    "SN": "Senegal",
    "SG": "Singapore",
    "GS": "South Georgia and the South Sandwich Islands",
    "SH": "Saint Helena, Ascension and Tristan da Cunha",
    "SJ": "Svalbard and Jan Mayen",
    "SB": "Solomon Islands",
    "SL": "Sierra Leone",
    "SV": "El Salvador",
    "SM": "San Marino",
    "SO": "Somalia",
    "PM": "Saint Pierre and Miquelon",
    "RS": "Serbia",
    "SS": "South Sudan",
    "ST": "Sao Tome and Principe",
    "SR": "Suriname",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "SE": "Sweden",
    "SZ": "Eswatini",
    "SX": "Sint Maarten (Dutch part)",
    "SC": "Seychelles",
    "SY": "Syrian Arab Republic",
    "TC": "Turks and Caicos Islands",
    "TD": "Chad",
    "TG": "Togo",
    "TH": "Thailand",
    "TJ": "Tajikistan",
    "TK": "Tokelau",
    "TM": "Turkmenistan",
    "TL": "Timor-Leste",
    "TO": "Tonga",
    "TT": "Trinidad and Tobago",
    "TN": "Tunisia",
    "TR": "Türkiye",
    "TV": "Tuvalu",
    "TW": "Taiwan, Province of China",
    "TZ": "Tanzania, United Republic of",
    "UG": "Uganda",
    "UA": "Ukraine",
    "UM": "United States Minor Outlying Islands",
    "UY": "Uruguay",
    "US": "United States",
    "UZ": "Uzbekistan",
    "VA": "Holy See (Vatican City State)",
    "VC": "Saint Vincent and the Grenadines",
    "VE": "Venezuela, Bolivarian Republic of",
    "VG": "Virgin Islands, British",
    "VI": "Virgin Islands, U.S.",
    "VN": "Viet Nam",
    "VU": "Vanuatu",
    "WF": "Wallis and Futuna",
    "WS": "Samoa",
    "YE": "Yemen",
    "ZA": "South Africa",
    "ZM": "Zambia",
    "ZW": "Zimbabwe",
}


# the functional API doesn't support inheriting from str, StrEnum requires Python 3.11+
class Geolocation(str, Enum):
    AF: str = "AF"
    AL: str = "AL"
    DZ: str = "DZ"
    AS: str = "AS"
    AD: str = "AD"
    AO: str = "AO"
    AI: str = "AI"
    AQ: str = "AQ"
    AG: str = "AG"
    AR: str = "AR"
    AM: str = "AM"
    AW: str = "AW"
    AU: str = "AU"
    AT: str = "AT"
    AZ: str = "AZ"
    BS: str = "BS"
    BH: str = "BH"
    BD: str = "BD"
    BB: str = "BB"
    BY: str = "BY"
    BE: str = "BE"
    BZ: str = "BZ"
    BJ: str = "BJ"
    BM: str = "BM"
    BT: str = "BT"
    BO: str = "BO"
    BQ: str = "BQ"
    BA: str = "BA"
    BW: str = "BW"
    BV: str = "BV"
    BR: str = "BR"
    IO: str = "IO"
    BN: str = "BN"
    BG: str = "BG"
    BF: str = "BF"
    BI: str = "BI"
    CV: str = "CV"
    KH: str = "KH"
    CM: str = "CM"
    CA: str = "CA"
    KY: str = "KY"
    CF: str = "CF"
    TD: str = "TD"
    CL: str = "CL"
    CN: str = "CN"
    CX: str = "CX"
    CC: str = "CC"
    CO: str = "CO"
    KM: str = "KM"
    CG: str = "CG"
    CD: str = "CD"
    CK: str = "CK"
    CR: str = "CR"
    HR: str = "HR"
    CU: str = "CU"
    CW: str = "CW"
    CY: str = "CY"
    CZ: str = "CZ"
    CI: str = "CI"
    DK: str = "DK"
    DJ: str = "DJ"
    DM: str = "DM"
    DO: str = "DO"
    EC: str = "EC"
    EG: str = "EG"
    SV: str = "SV"
    GQ: str = "GQ"
    ER: str = "ER"
    EE: str = "EE"
    SZ: str = "SZ"
    ET: str = "ET"
    FK: str = "FK"
    FO: str = "FO"
    FJ: str = "FJ"
    FI: str = "FI"
    FR: str = "FR"
    GF: str = "GF"
    PF: str = "PF"
    TF: str = "TF"
    GA: str = "GA"
    GM: str = "GM"
    GE: str = "GE"
    DE: str = "DE"
    GH: str = "GH"
    GI: str = "GI"
    GR: str = "GR"
    GL: str = "GL"
    GD: str = "GD"
    GP: str = "GP"
    GU: str = "GU"
    GT: str = "GT"
    GG: str = "GG"
    GN: str = "GN"
    GW: str = "GW"
    GY: str = "GY"
    HT: str = "HT"
    HM: str = "HM"
    VA: str = "VA"
    HN: str = "HN"
    HK: str = "HK"
    HU: str = "HU"
    IS: str = "IS"
    IN: str = "IN"
    ID: str = "ID"
    IR: str = "IR"
    IQ: str = "IQ"
    IE: str = "IE"
    IM: str = "IM"
    IL: str = "IL"
    IT: str = "IT"
    JM: str = "JM"
    JP: str = "JP"
    JE: str = "JE"
    JO: str = "JO"
    KZ: str = "KZ"
    KE: str = "KE"
    KI: str = "KI"
    KP: str = "KP"
    KR: str = "KR"
    KW: str = "KW"
    KG: str = "KG"
    LA: str = "LA"
    LV: str = "LV"
    LB: str = "LB"
    LS: str = "LS"
    LR: str = "LR"
    LY: str = "LY"
    LI: str = "LI"
    LT: str = "LT"
    LU: str = "LU"
    MO: str = "MO"
    MG: str = "MG"
    MW: str = "MW"
    MY: str = "MY"
    MV: str = "MV"
    ML: str = "ML"
    MT: str = "MT"
    MH: str = "MH"
    MQ: str = "MQ"
    MR: str = "MR"
    MU: str = "MU"
    YT: str = "YT"
    MX: str = "MX"
    FM: str = "FM"
    MD: str = "MD"
    MC: str = "MC"
    MN: str = "MN"
    ME: str = "ME"
    MS: str = "MS"
    MA: str = "MA"
    MZ: str = "MZ"
    MM: str = "MM"
    NA: str = "NA"
    NR: str = "NR"
    NP: str = "NP"
    NL: str = "NL"
    NC: str = "NC"
    NZ: str = "NZ"
    NI: str = "NI"
    NE: str = "NE"
    NG: str = "NG"
    NU: str = "NU"
    NF: str = "NF"
    MK: str = "MK"
    MP: str = "MP"
    NO: str = "NO"
    OM: str = "OM"
    PK: str = "PK"
    PW: str = "PW"
    PS: str = "PS"
    PA: str = "PA"
    PG: str = "PG"
    PY: str = "PY"
    PE: str = "PE"
    PH: str = "PH"
    PN: str = "PN"
    PL: str = "PL"
    PT: str = "PT"
    PR: str = "PR"
    QA: str = "QA"
    RO: str = "RO"
    RU: str = "RU"
    RW: str = "RW"
    RE: str = "RE"
    BL: str = "BL"
    SH: str = "SH"
    KN: str = "KN"
    LC: str = "LC"
    MF: str = "MF"
    PM: str = "PM"
    VC: str = "VC"
    WS: str = "WS"
    SM: str = "SM"
    ST: str = "ST"
    SA: str = "SA"
    SN: str = "SN"
    RS: str = "RS"
    SC: str = "SC"
    SL: str = "SL"
    SG: str = "SG"
    SX: str = "SX"
    SK: str = "SK"
    SI: str = "SI"
    SB: str = "SB"
    SO: str = "SO"
    ZA: str = "ZA"
    GS: str = "GS"
    SS: str = "SS"
    ES: str = "ES"
    LK: str = "LK"
    SD: str = "SD"
    SR: str = "SR"
    SJ: str = "SJ"
    SE: str = "SE"
    CH: str = "CH"
    SY: str = "SY"
    TW: str = "TW"
    TJ: str = "TJ"
    TZ: str = "TZ"
    TH: str = "TH"
    TL: str = "TL"
    TG: str = "TG"
    TK: str = "TK"
    TO: str = "TO"
    TT: str = "TT"
    TN: str = "TN"
    TM: str = "TM"
    TC: str = "TC"
    TV: str = "TV"
    TR: str = "TR"
    UG: str = "UG"
    UA: str = "UA"
    AE: str = "AE"
    GB: str = "GB"
    US: str = "US"
    UM: str = "UM"
    UY: str = "UY"
    UZ: str = "UZ"
    VU: str = "VU"
    VE: str = "VE"
    VN: str = "VN"
    VG: str = "VG"
    VI: str = "VI"
    WF: str = "WF"
    EH: str = "EH"
    YE: str = "YE"
    ZM: str = "ZM"
    ZW: str = "ZW"
    AX: str = "AX"


# e.g. {"UY": "Uruguay (UY)"}
GEOLOCATION_OPTIONS_WITH_CODE = {
    code: f"{name} ({code})" for code, name in GEOLOCATION_OPTIONS.items()
}

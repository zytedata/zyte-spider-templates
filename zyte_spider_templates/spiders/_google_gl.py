# ../_geolocations.py counterpart for
# https://developers.google.com/custom-search/docs/json_api_reference#countryCodes
#
# Built automatically with ../../utils/google-gl-updater

from enum import Enum

GOOGLE_GL_OPTIONS = {
    "af": "Afghanistan",
    "al": "Albania",
    "dz": "Algeria",
    "as": "American Samoa",
    "ad": "Andorra",
    "ao": "Angola",
    "ai": "Anguilla",
    "aq": "Antarctica",
    "ag": "Antigua and Barbuda",
    "ar": "Argentina",
    "am": "Armenia",
    "aw": "Aruba",
    "au": "Australia",
    "at": "Austria",
    "az": "Azerbaijan",
    "bs": "Bahamas",
    "bh": "Bahrain",
    "bd": "Bangladesh",
    "bb": "Barbados",
    "by": "Belarus",
    "be": "Belgium",
    "bz": "Belize",
    "bj": "Benin",
    "bm": "Bermuda",
    "bt": "Bhutan",
    "bo": "Bolivia",
    "ba": "Bosnia and Herzegovina",
    "bw": "Botswana",
    "bv": "Bouvet Island",
    "br": "Brazil",
    "io": "British Indian Ocean Territory",
    "bn": "Brunei Darussalam",
    "bg": "Bulgaria",
    "bf": "Burkina Faso",
    "bi": "Burundi",
    "kh": "Cambodia",
    "cm": "Cameroon",
    "ca": "Canada",
    "cv": "Cape Verde",
    "ky": "Cayman Islands",
    "cf": "Central African Republic",
    "td": "Chad",
    "cl": "Chile",
    "cn": "China",
    "cx": "Christmas Island",
    "cc": "Cocos (Keeling) Islands",
    "co": "Colombia",
    "km": "Comoros",
    "cg": "Congo",
    "cd": "Congo, the Democratic Republic of the",
    "ck": "Cook Islands",
    "cr": "Costa Rica",
    "ci": "Cote D'ivoire",
    "hr": "Croatia",
    "cu": "Cuba",
    "cy": "Cyprus",
    "cz": "Czech Republic",
    "dk": "Denmark",
    "dj": "Djibouti",
    "dm": "Dominica",
    "do": "Dominican Republic",
    "ec": "Ecuador",
    "eg": "Egypt",
    "sv": "El Salvador",
    "gq": "Equatorial Guinea",
    "er": "Eritrea",
    "ee": "Estonia",
    "et": "Ethiopia",
    "fk": "Falkland Islands (Malvinas)",
    "fo": "Faroe Islands",
    "fj": "Fiji",
    "fi": "Finland",
    "fr": "France",
    "gf": "French Guiana",
    "pf": "French Polynesia",
    "tf": "French Southern Territories",
    "ga": "Gabon",
    "gm": "Gambia",
    "ge": "Georgia",
    "de": "Germany",
    "gh": "Ghana",
    "gi": "Gibraltar",
    "gr": "Greece",
    "gl": "Greenland",
    "gd": "Grenada",
    "gp": "Guadeloupe",
    "gu": "Guam",
    "gt": "Guatemala",
    "gn": "Guinea",
    "gw": "Guinea-Bissau",
    "gy": "Guyana",
    "ht": "Haiti",
    "hm": "Heard Island and Mcdonald Islands",
    "va": "Holy See (Vatican City State)",
    "hn": "Honduras",
    "hk": "Hong Kong",
    "hu": "Hungary",
    "is": "Iceland",
    "in": "India",
    "id": "Indonesia",
    "ir": "Iran, Islamic Republic of",
    "iq": "Iraq",
    "ie": "Ireland",
    "il": "Israel",
    "it": "Italy",
    "jm": "Jamaica",
    "jp": "Japan",
    "jo": "Jordan",
    "kz": "Kazakhstan",
    "ke": "Kenya",
    "ki": "Kiribati",
    "kp": "Korea, Democratic People's Republic of",
    "kr": "Korea, Republic of",
    "kw": "Kuwait",
    "kg": "Kyrgyzstan",
    "la": "Lao People's Democratic Republic",
    "lv": "Latvia",
    "lb": "Lebanon",
    "ls": "Lesotho",
    "lr": "Liberia",
    "ly": "Libyan Arab Jamahiriya",
    "li": "Liechtenstein",
    "lt": "Lithuania",
    "lu": "Luxembourg",
    "mo": "Macao",
    "mk": "Macedonia, the Former Yugosalv Republic of",
    "mg": "Madagascar",
    "mw": "Malawi",
    "my": "Malaysia",
    "mv": "Maldives",
    "ml": "Mali",
    "mt": "Malta",
    "mh": "Marshall Islands",
    "mq": "Martinique",
    "mr": "Mauritania",
    "mu": "Mauritius",
    "yt": "Mayotte",
    "mx": "Mexico",
    "fm": "Micronesia, Federated States of",
    "md": "Moldova, Republic of",
    "mc": "Monaco",
    "mn": "Mongolia",
    "ms": "Montserrat",
    "ma": "Morocco",
    "mz": "Mozambique",
    "mm": "Myanmar",
    "na": "Namibia",
    "nr": "Nauru",
    "np": "Nepal",
    "nl": "Netherlands",
    "an": "Netherlands Antilles",
    "nc": "New Caledonia",
    "nz": "New Zealand",
    "ni": "Nicaragua",
    "ne": "Niger",
    "ng": "Nigeria",
    "nu": "Niue",
    "nf": "Norfolk Island",
    "mp": "Northern Mariana Islands",
    "no": "Norway",
    "om": "Oman",
    "pk": "Pakistan",
    "pw": "Palau",
    "ps": "Palestinian Territory, Occupied",
    "pa": "Panama",
    "pg": "Papua New Guinea",
    "py": "Paraguay",
    "pe": "Peru",
    "ph": "Philippines",
    "pn": "Pitcairn",
    "pl": "Poland",
    "pt": "Portugal",
    "pr": "Puerto Rico",
    "qa": "Qatar",
    "re": "Reunion",
    "ro": "Romania",
    "ru": "Russian Federation",
    "rw": "Rwanda",
    "sh": "Saint Helena",
    "kn": "Saint Kitts and Nevis",
    "lc": "Saint Lucia",
    "pm": "Saint Pierre and Miquelon",
    "vc": "Saint Vincent and the Grenadines",
    "ws": "Samoa",
    "sm": "San Marino",
    "st": "Sao Tome and Principe",
    "sa": "Saudi Arabia",
    "sn": "Senegal",
    "cs": "Serbia and Montenegro",
    "sc": "Seychelles",
    "sl": "Sierra Leone",
    "sg": "Singapore",
    "sk": "Slovakia",
    "si": "Slovenia",
    "sb": "Solomon Islands",
    "so": "Somalia",
    "za": "South Africa",
    "gs": "South Georgia and the South Sandwich Islands",
    "es": "Spain",
    "lk": "Sri Lanka",
    "sd": "Sudan",
    "sr": "Suriname",
    "sj": "Svalbard and Jan Mayen",
    "sz": "Swaziland",
    "se": "Sweden",
    "ch": "Switzerland",
    "sy": "Syrian Arab Republic",
    "tw": "Taiwan, Province of China",
    "tj": "Tajikistan",
    "tz": "Tanzania, United Republic of",
    "th": "Thailand",
    "tl": "Timor-Leste",
    "tg": "Togo",
    "tk": "Tokelau",
    "to": "Tonga",
    "tt": "Trinidad and Tobago",
    "tn": "Tunisia",
    "tr": "Turkey",
    "tm": "Turkmenistan",
    "tc": "Turks and Caicos Islands",
    "tv": "Tuvalu",
    "ug": "Uganda",
    "ua": "Ukraine",
    "ae": "United Arab Emirates",
    "uk": "United Kingdom",
    "us": "United States",
    "um": "United States Minor Outlying Islands",
    "uy": "Uruguay",
    "uz": "Uzbekistan",
    "vu": "Vanuatu",
    "ve": "Venezuela",
    "vn": "Viet Nam",
    "vg": "Virgin Islands, British",
    "vi": "Virgin Islands, U.S.",
    "wf": "Wallis and Futuna",
    "eh": "Western Sahara",
    "ye": "Yemen",
    "zm": "Zambia",
    "zw": "Zimbabwe",
}
GOOGLE_GL_OPTIONS_WITH_CODE = {
    code: f"{name} ({code})" for code, name in GOOGLE_GL_OPTIONS.items()
}


class GoogleGl(str, Enum):
    af: str = "af"
    al: str = "al"
    dz: str = "dz"
    as_: str = "as"
    ad: str = "ad"
    ao: str = "ao"
    ai: str = "ai"
    aq: str = "aq"
    ag: str = "ag"
    ar: str = "ar"
    am: str = "am"
    aw: str = "aw"
    au: str = "au"
    at: str = "at"
    az: str = "az"
    bs: str = "bs"
    bh: str = "bh"
    bd: str = "bd"
    bb: str = "bb"
    by: str = "by"
    be: str = "be"
    bz: str = "bz"
    bj: str = "bj"
    bm: str = "bm"
    bt: str = "bt"
    bo: str = "bo"
    ba: str = "ba"
    bw: str = "bw"
    bv: str = "bv"
    br: str = "br"
    io: str = "io"
    bn: str = "bn"
    bg: str = "bg"
    bf: str = "bf"
    bi: str = "bi"
    kh: str = "kh"
    cm: str = "cm"
    ca: str = "ca"
    cv: str = "cv"
    ky: str = "ky"
    cf: str = "cf"
    td: str = "td"
    cl: str = "cl"
    cn: str = "cn"
    cx: str = "cx"
    cc: str = "cc"
    co: str = "co"
    km: str = "km"
    cg: str = "cg"
    cd: str = "cd"
    ck: str = "ck"
    cr: str = "cr"
    ci: str = "ci"
    hr: str = "hr"
    cu: str = "cu"
    cy: str = "cy"
    cz: str = "cz"
    dk: str = "dk"
    dj: str = "dj"
    dm: str = "dm"
    do: str = "do"
    ec: str = "ec"
    eg: str = "eg"
    sv: str = "sv"
    gq: str = "gq"
    er: str = "er"
    ee: str = "ee"
    et: str = "et"
    fk: str = "fk"
    fo: str = "fo"
    fj: str = "fj"
    fi: str = "fi"
    fr: str = "fr"
    gf: str = "gf"
    pf: str = "pf"
    tf: str = "tf"
    ga: str = "ga"
    gm: str = "gm"
    ge: str = "ge"
    de: str = "de"
    gh: str = "gh"
    gi: str = "gi"
    gr: str = "gr"
    gl: str = "gl"
    gd: str = "gd"
    gp: str = "gp"
    gu: str = "gu"
    gt: str = "gt"
    gn: str = "gn"
    gw: str = "gw"
    gy: str = "gy"
    ht: str = "ht"
    hm: str = "hm"
    va: str = "va"
    hn: str = "hn"
    hk: str = "hk"
    hu: str = "hu"
    is_: str = "is"
    in_: str = "in"
    id: str = "id"
    ir: str = "ir"
    iq: str = "iq"
    ie: str = "ie"
    il: str = "il"
    it: str = "it"
    jm: str = "jm"
    jp: str = "jp"
    jo: str = "jo"
    kz: str = "kz"
    ke: str = "ke"
    ki: str = "ki"
    kp: str = "kp"
    kr: str = "kr"
    kw: str = "kw"
    kg: str = "kg"
    la: str = "la"
    lv: str = "lv"
    lb: str = "lb"
    ls: str = "ls"
    lr: str = "lr"
    ly: str = "ly"
    li: str = "li"
    lt: str = "lt"
    lu: str = "lu"
    mo: str = "mo"
    mk: str = "mk"
    mg: str = "mg"
    mw: str = "mw"
    my: str = "my"
    mv: str = "mv"
    ml: str = "ml"
    mt: str = "mt"
    mh: str = "mh"
    mq: str = "mq"
    mr: str = "mr"
    mu: str = "mu"
    yt: str = "yt"
    mx: str = "mx"
    fm: str = "fm"
    md: str = "md"
    mc: str = "mc"
    mn: str = "mn"
    ms: str = "ms"
    ma: str = "ma"
    mz: str = "mz"
    mm: str = "mm"
    na: str = "na"
    nr: str = "nr"
    np: str = "np"
    nl: str = "nl"
    an: str = "an"
    nc: str = "nc"
    nz: str = "nz"
    ni: str = "ni"
    ne: str = "ne"
    ng: str = "ng"
    nu: str = "nu"
    nf: str = "nf"
    mp: str = "mp"
    no: str = "no"
    om: str = "om"
    pk: str = "pk"
    pw: str = "pw"
    ps: str = "ps"
    pa: str = "pa"
    pg: str = "pg"
    py: str = "py"
    pe: str = "pe"
    ph: str = "ph"
    pn: str = "pn"
    pl: str = "pl"
    pt: str = "pt"
    pr: str = "pr"
    qa: str = "qa"
    re: str = "re"
    ro: str = "ro"
    ru: str = "ru"
    rw: str = "rw"
    sh: str = "sh"
    kn: str = "kn"
    lc: str = "lc"
    pm: str = "pm"
    vc: str = "vc"
    ws: str = "ws"
    sm: str = "sm"
    st: str = "st"
    sa: str = "sa"
    sn: str = "sn"
    cs: str = "cs"
    sc: str = "sc"
    sl: str = "sl"
    sg: str = "sg"
    sk: str = "sk"
    si: str = "si"
    sb: str = "sb"
    so: str = "so"
    za: str = "za"
    gs: str = "gs"
    es: str = "es"
    lk: str = "lk"
    sd: str = "sd"
    sr: str = "sr"
    sj: str = "sj"
    sz: str = "sz"
    se: str = "se"
    ch: str = "ch"
    sy: str = "sy"
    tw: str = "tw"
    tj: str = "tj"
    tz: str = "tz"
    th: str = "th"
    tl: str = "tl"
    tg: str = "tg"
    tk: str = "tk"
    to: str = "to"
    tt: str = "tt"
    tn: str = "tn"
    tr: str = "tr"
    tm: str = "tm"
    tc: str = "tc"
    tv: str = "tv"
    ug: str = "ug"
    ua: str = "ua"
    ae: str = "ae"
    uk: str = "uk"
    us: str = "us"
    um: str = "um"
    uy: str = "uy"
    uz: str = "uz"
    vu: str = "vu"
    ve: str = "ve"
    vn: str = "vn"
    vg: str = "vg"
    vi: str = "vi"
    wf: str = "wf"
    eh: str = "eh"
    ye: str = "ye"
    zm: str = "zm"
    zw: str = "zw"

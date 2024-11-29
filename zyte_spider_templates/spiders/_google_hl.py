# _google_gl.py counterpart for
# https://developers.google.com/custom-search/docs/json_api_reference#interfaceLanguages
#
# Built automatically with ../../utils/google-hl-updater

from enum import Enum

GOOGLE_HL_OPTIONS = {
    "af": "Afrikaans",
    "sq": "Albanian",
    "sm": "Amharic",
    "ar": "Arabic",
    "az": "Azerbaijani",
    "eu": "Basque",
    "be": "Belarusian",
    "bn": "Bengali",
    "bh": "Bihari",
    "bs": "Bosnian",
    "bg": "Bulgarian",
    "ca": "Catalan",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "hr": "Croatian",
    "cs": "Czech",
    "da": "Danish",
    "nl": "Dutch",
    "en": "English",
    "eo": "Esperanto",
    "et": "Estonian",
    "fo": "Faroese",
    "fi": "Finnish",
    "fr": "French",
    "fy": "Frisian",
    "gl": "Galician",
    "ka": "Georgian",
    "de": "German",
    "el": "Greek",
    "gu": "Gujarati",
    "iw": "Hebrew",
    "hi": "Hindi",
    "hu": "Hungarian",
    "is": "Icelandic",
    "id": "Indonesian",
    "ia": "Interlingua",
    "ga": "Irish",
    "it": "Italian",
    "ja": "Japanese",
    "jw": "Javanese",
    "kn": "Kannada",
    "ko": "Korean",
    "la": "Latin",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "mk": "Macedonian",
    "ms": "Malay",
    "ml": "Malayam",
    "mt": "Maltese",
    "mr": "Marathi",
    "ne": "Nepali",
    "no": "Norwegian",
    "nn": "Norwegian (Nynorsk)",
    "oc": "Occitan",
    "fa": "Persian",
    "pl": "Polish",
    "pt-BR": "Portuguese (Brazil)",
    "pt-PT": "Portuguese (Portugal)",
    "pa": "Punjabi",
    "ro": "Romanian",
    "ru": "Russian",
    "gd": "Scots Gaelic",
    "sr": "Serbian",
    "si": "Sinhalese",
    "sk": "Slovak",
    "sl": "Slovenian",
    "es": "Spanish",
    "su": "Sudanese",
    "sw": "Swahili",
    "sv": "Swedish",
    "tl": "Tagalog",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "ti": "Tigrinya",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "cy": "Welsh",
    "xh": "Xhosa",
    "zu": "Zulu",
}
GOOGLE_HL_OPTIONS_WITH_CODE = {
    code: f"{name} ({code})" for code, name in GOOGLE_HL_OPTIONS.items()
}


class GoogleHl(str, Enum):
    af: str = "af"
    sq: str = "sq"
    sm: str = "sm"
    ar: str = "ar"
    az: str = "az"
    eu: str = "eu"
    be: str = "be"
    bn: str = "bn"
    bh: str = "bh"
    bs: str = "bs"
    bg: str = "bg"
    ca: str = "ca"
    zh_CN: str = "zh-CN"
    zh_TW: str = "zh-TW"
    hr: str = "hr"
    cs: str = "cs"
    da: str = "da"
    nl: str = "nl"
    en: str = "en"
    eo: str = "eo"
    et: str = "et"
    fo: str = "fo"
    fi: str = "fi"
    fr: str = "fr"
    fy: str = "fy"
    gl: str = "gl"
    ka: str = "ka"
    de: str = "de"
    el: str = "el"
    gu: str = "gu"
    iw: str = "iw"
    hi: str = "hi"
    hu: str = "hu"
    is_: str = "is"
    id: str = "id"
    ia: str = "ia"
    ga: str = "ga"
    it: str = "it"
    ja: str = "ja"
    jw: str = "jw"
    kn: str = "kn"
    ko: str = "ko"
    la: str = "la"
    lv: str = "lv"
    lt: str = "lt"
    mk: str = "mk"
    ms: str = "ms"
    ml: str = "ml"
    mt: str = "mt"
    mr: str = "mr"
    ne: str = "ne"
    no: str = "no"
    nn: str = "nn"
    oc: str = "oc"
    fa: str = "fa"
    pl: str = "pl"
    pt_BR: str = "pt-BR"
    pt_PT: str = "pt-PT"
    pa: str = "pa"
    ro: str = "ro"
    ru: str = "ru"
    gd: str = "gd"
    sr: str = "sr"
    si: str = "si"
    sk: str = "sk"
    sl: str = "sl"
    es: str = "es"
    su: str = "su"
    sw: str = "sw"
    sv: str = "sv"
    tl: str = "tl"
    ta: str = "ta"
    te: str = "te"
    th: str = "th"
    ti: str = "ti"
    tr: str = "tr"
    uk: str = "uk"
    ur: str = "ur"
    uz: str = "uz"
    vi: str = "vi"
    cy: str = "cy"
    xh: str = "xh"
    zu: str = "zu"

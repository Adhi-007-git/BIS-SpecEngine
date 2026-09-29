"""
Multilingual Response Generator for BIS SpecEngine (SIH26108).
Provides automatic response language matching in English, Hindi, and Tamil:
- Explanations, summaries, applicability reasoning, warnings, and limitations in the detected language.
- Strict preservation of official BIS standard codes (e.g. IS 1554 (Part 1):1988), ratings, and citations.
- Deterministic fallback when external LLM providers are unavailable or offline.
"""
from typing import Dict, Any, List, Optional
import re
import logging

logger = logging.getLogger("sih26108.multilingual_response")

# Official Title Explanations (Titles remain official English, with bilingual explanations)
TITLE_EXPLANATIONS: Dict[str, Dict[str, str]] = {
    "IS 1554 (Part 1):1988": {
        "hi": "1100 V तक और सहित कार्यशील वोल्टेज के लिए पीवीसी इंसुलेटेड (भारी शुल्क) विद्युत केबल - भाग 1",
        "ta": "1100 V வரை உள்ள வேலை செய்யும் மின்னழுத்தங்களுக்கான பிவிசி இன்சுலேட்டட் (கனரக) மின் கேபிள்கள் - பகுதி 1"
    },
    "IS 694:2010": {
        "hi": "450/750 V तक और सहित कार्यशील वोल्टेज के लिए पीवीसी इंसुलेटेड केबल",
        "ta": "450/750 V வரை உள்ள வேலை செய்யும் மின்னழுத்தங்களுக்கான பிவிசி இன்சுலேட்டட் கேபிள்கள்"
    },
    "IS 7098 (Part 1):1988": {
        "hi": "एक्सएलपीई इंसुलेटेड थर्मोप्लास्टिक शीथेड केबल - भाग 1: 1100 V तक कार्यशील वोल्टेज के लिए",
        "ta": "எக்ஸ்எல்பிஇ இன்சுலேட்டட் தெர்மோபிளாஸ்டிக் உறை கேபிள்கள் - பகுதி 1: 1100 V வரை"
    },
    "IS 7098 (Part 2):2011": {
        "hi": "एक्सएलपीई इंसुलेटेड थर्मोप्लास्टिक शीथेड केबल - भाग 2: 3.3 kV से 33 kV तक कार्यशील वोल्टेज के लिए",
        "ta": "எக்ஸ்எல்பிஇ இன்சுலேட்டட் தெர்மோபிளாஸ்டிக் உறை கேபிள்கள் - பகுதி 2: 3.3 kV முதல் 33 kV வரை"
    },
    "IS 1180 (Part 1):2014": {
        "hi": "आउटडोर / इनडोर वितरण ट्रांसफार्मर 2500 kVA, 33 kV तक - विनिर्देश भाग 1: तेल निमज्जित",
        "ta": "வெளிப்புற / உட்புற விநியோக மின்மாற்றி 2500 kVA, 33 kV வரை - விவரக்குறிப்பு பகுதி 1: எண்ணெய் மூழ்கியது"
    },
    "IS 2026 (Part 1):2011": {
        "hi": "पावर ट्रांसफार्मर - भाग 1: सामान्य विनिर्देश",
        "ta": "பவர் டிரான்ஸ்பார்மர் - பகுதி 1: பொதுவான விவரக்குறிப்பு"
    },
    "IS 1786:2008": {
        "hi": "कंक्रीट सुदृढीकरण के लिए उच्च शक्ति विकृत स्टील की छड़ें और तार (टीएमटी बार्स) - विनिर्देश",
        "ta": "கான்கிரீட் வலுவூட்டலுக்கான உயர் வலிமை சிதைக்கப்பட்ட எஃகு கம்பிகள் மற்றும் கம்பிகள் (டிஎம்டி பார்கள்) - விவரக்குறிப்பு"
    },
    "IS 2062:2011": {
        "hi": "हॉट रोल्ड मध्यम और उच्च तन्यता संरचनात्मक स्टील - विनिर्देश",
        "ta": "ஹாட் ரோல்டு நடுத்தர மற்றும் உயர் இழுவிசை கட்டமைப்பு எஃகு - விவரக்குறிப்பு"
    },
    "IS 456:2000": {
        "hi": "सादा और प्रबलित कंक्रीट - अभ्यास संहिता",
        "ta": "சாதாரண மற்றும் வலுவூட்டப்பட்ட கான்கிரீட் - நடைமுறை குறியீடு"
    },
    "IS 800:2007": {
        "hi": "स्टील में सामान्य निर्माण - अभ्यास संहिता",
        "ta": "எஃகில் பொதுவான கட்டுமானம் - நடைமுறை குறியீடு"
    },
    "IS 383:2016": {
        "hi": "कंक्रीट के लिए मोटे और महीन समुच्चय - विनिर्देश",
        "ta": "கான்கிரீட்டிற்கான கரடுமுரடான மற்றும் நுண்ணிய திரட்டு - விவரக்குறிப்பு"
    },
    "IS 4984:2016": {
        "hi": "पेयजल आपूर्ति के लिए उच्च घनत्व पॉलीथीन पाइप (एचडीपीई) - विनिर्देश",
        "ta": "குடிநீர் விநியோகத்திற்கான உயர் அடர்த்தி பாலிஎதிலீன் குழாய்கள் (எச்டிபிஇ) - விவரக்குறிப்பு"
    },
    "IS 269:2015": {
        "hi": "साधारण पोर्टलैंड सीमेंट (ओपीसी 33, 43, 53 ग्रेड) - विनिर्देश",
        "ta": "சாதாரண போர்ட்லேண்ட் சிமெண்ட் (ஓபிசி 33, 43, 53 கிரேடு) - விவரக்குறிப்பு"
    },
    "IS 1489 (Part 1):2015": {
        "hi": "पोर्टलैंड पोज़ोलाना सीमेंट - विनिर्देश: भाग 1 फ्लाईऐश आधारित",
        "ta": "போர்ட்லேண்ட் போஸோலானா சிமெண்ட் - விவரக்குறிப்பு: பகுதி 1 ஃப்ளைஆஷ் அடிப்படையிலானது"
    },
    "IS 1363 (Part 1):2019": {
        "hi": "हेक्सागोन हेड बोल्ट, स्क्रू और नट - उत्पाद ग्रेड सी",
        "ta": "ஹெக்ஸாகன் ஹெட் போல்ட்கள், திருகுகள் மற்றும் நட்டுகள் - தயாரிப்பு தரம் சி"
    },
    "IS 1367 (Part 1):2014": {
        "hi": "थ्रेडेड स्टील फास्टनरों के लिए तकनीकी आपूर्ति शर्तें",
        "ta": "திரிக்கப்பட்ட எஃகு ஃபாஸ்டென்சர்களுக்கான தொழில்நுட்ப விநியோக நிபந்தனைகள்"
    },
    "IS/IEC 60529:2001": {
        "hi": "बाड़ों द्वारा प्रदान की जाने वाली सुरक्षा की डिग्री (आईपी कोड / जलरोधी)",
        "ta": "அடைப்புகளால் வழங்கப்படும் பாதுகாப்பின் அளவுகள் (ஐபி குறியீடு / நீர்ப்புகா)"
    }
}


def _translate_parameter(text: str, lang: str) -> str:
    """Translates technical parameter substrings into natural Indic terms while preserving values and units."""
    if not text or lang not in ("hi", "ta"):
        return text

    if lang == "hi":
        subs = [
            (r'(?i)\bup\s+to\s+and\s+including\s+(\d+(?:\.\d+)?\s*(?:kv|v|kva|mva|kw|mw|mm|m)?)\b', r'\1 तक और सहित'),
            (r'(?i)\bup\s+to\s+(\d+(?:\.\d+)?\s*(?:kv|v|kva|mva|kw|mw|mm|m)?)\b', r'\1 तक'),
            (r'(?i)\bup\s+to\s+and\s+including\b', 'तक और सहित'),
            (r'(?i)\bup\s+to\b', 'तक'),
            (r'(?i)\bfor\s+working\s+voltages\b', 'कार्यशील वोल्टेज के लिए'),
            (r'(?i)\bworking\s+voltages?\b', 'कार्यशील वोल्टेज'),
            (r'(?i)\boperating\s+voltages?\b', 'ऑपरेटिंग वोल्टेज'),
            (r'(?i)\brated\s+operating\s+voltage\b', 'रेटेड ऑपरेटिंग वोल्टेज'),
            (r'(?i)\bmatches\s+rated\s+scope\b', 'रेटेड कार्यक्षेत्र से मेल खाता है'),
            (r'(?i)\brated\s+scope\b', 'रेटेड कार्यक्षेत्र'),
            (r'(?i)\bheavy\s+duty\b', 'भारी शुल्क'),
            (r'(?i)\barmou?red(?:\s+cable)?\b', 'कवचयुक्त केबल'),
            (r'(?i)\bunarmou?red(?:\s+cable)?\b', 'अकवचयुक्त केबल'),
            (r'(?i)\bunderground(?:\s+cable)?\b', 'भूमिगत केबल'),
            (r'(?i)\belectric\s+cable\b', 'विद्युत केबल'),
            (r'(?i)\bcables?\b', 'केबल'),
            (r'(?i)\binsulation\b', 'इन्सुलेशन'),
            (r'(?i)\bdielectric\s+material\b', 'परावैद्युत (इन्सुलेशन) सामग्री'),
            (r'(?i)\balternative\s+dielectric\s+material\b', 'वैकल्पिक परावैद्युत सामग्री'),
            (r'(?i)\bdielectric\b', 'परावैद्युत'),
            (r'(?i)\bconductors?\b', 'कंडक्टर (चालक)'),
            (r'(?i)\bcopper\b', 'तांबा (Copper)'),
            (r'(?i)\baluminium\b|\baluminum\b', 'एल्यूमीनियम (Aluminium)'),
            (r'(?i)\bdistribution\s+transformer\b', 'वितरण ट्रांसफार्मर'),
            (r'(?i)\bpower\s+transformer\b', 'पावर ट्रांसफार्मर'),
            (r'(?i)\btransformers?\b', 'ट्रांसफार्मर'),
            (r'(?i)\boil[\s\-]cooled\b', 'ऑयल कूल्ड (तेल ठंडा)'),
            (r'(?i)\bair[\s\-]cooled\b', 'एयर कूल्ड (वायु ठंडा)'),
            (r'(?i)\boutdoor\b', 'आउटडोर'),
            (r'(?i)\bindoor\b', 'इनडोर'),
            (r'(?i)\bwaterproof\b', 'जलरोधी'),
            (r'(?i)\bpolyethylene\s+pipe\b', 'पॉलीइथिलीन पाइप'),
            (r'(?i)\bpipes?\b', 'पाइप'),
            (r'(?i)\bstructural\s+steel\b', 'संरचनात्मक स्टील'),
            (r'(?i)\breinforced\s+concrete\b', 'प्रबलित कंक्रीट'),
            (r'(?i)\bconcrete\b', 'कंक्रीट'),
            (r'(?i)\bcement\b', 'सीमेंट'),
            (r'(?i)\baggregate\b', 'समुच्चय'),
            (r'(?i)\bpvc\b', 'पीवीसी (PVC)'),
            (r'(?i)\bxlpe\b', 'एक्सएलपीई (XLPE)'),
            (r'(?i)\bswitchgears?\b', 'स्विचगियर'),
            (r'(?i)\bsteels?\b', 'स्टील'),
            (r'(?i)\bfasteners?\b', 'फास्टनर'),
            (r'(?i)\bbolts?\b', 'बोल्ट'),
            (r'(?i)\bnuts?\b', 'नट'),
            (r'(?i)\bscrews?\b', 'पेंच (स्क्रू)'),
            (r'(?i)\bmatched\s+tokens\b', 'मिलान टोकन'),
            (r'(?i)\btechnical\s+terminology\s+alignment\b', 'तकनीकी शब्दावली संरेखण'),
            (r'(?i)\brelated\s+reference\b', 'संबंधित संदर्भ'),
            (r'(?i)\bdirect\s+match\b', 'प्रत्यक्ष मिलान'),
        ]
    else:  # ta
        subs = [
            (r'(?i)\bup\s+to\s+and\s+including\s+(\d+(?:\.\d+)?\s*(?:kv|v|kva|mva|kw|mw|mm|m)?)\b', r'\1 வரை உள்ள'),
            (r'(?i)\bup\s+to\s+(\d+(?:\.\d+)?\s*(?:kv|v|kva|mva|kw|mw|mm|m)?)\b', r'\1 வரை'),
            (r'(?i)\bup\s+to\s+and\s+including\b', 'வரை உள்ள'),
            (r'(?i)\bup\s+to\b', 'வரை'),
            (r'(?i)\bfor\s+working\s+voltages\b', 'வேலை செய்யும் மின்னழுத்தங்களுக்கு'),
            (r'(?i)\bworking\s+voltages?\b', 'வேலை செய்யும் மின்னழுத்தம்'),
            (r'(?i)\boperating\s+voltages?\b', 'இயக்க மின்னழுத்தம்'),
            (r'(?i)\brated\s+operating\s+voltage\b', 'மதிப்பிடப்பட்ட இயக்க மின்னழுத்தம்'),
            (r'(?i)\bmatches\s+rated\s+scope\b', 'மதிப்பிடப்பட்ட வரம்புடன் பொருந்துகிறது'),
            (r'(?i)\brated\s+scope\b', 'மதிப்பிடப்பட்ட வரம்பு'),
            (r'(?i)\bheavy\s+duty\b', 'கனரக'),
            (r'(?i)\barmou?red(?:\s+cable)?\b', 'கவச கேபிள்'),
            (r'(?i)\bunarmou?red(?:\s+cable)?\b', 'கவசமற்ற கேபிள்'),
            (r'(?i)\bunderground(?:\s+cable)?\b', 'நிலத்தடி கேபிள்'),
            (r'(?i)\belectric\s+cable\b', 'மின்சார கேபிள்'),
            (r'(?i)\bcables?\b', 'கேபிள்'),
            (r'(?i)\binsulation\b', 'காப்பு (Insulation)'),
            (r'(?i)\bdielectric\s+material\b', 'மின்கடத்தா காப்பு பொருள்'),
            (r'(?i)\balternative\s+dielectric\s+material\b', 'மாற்று மின்கடத்தா பொருள்'),
            (r'(?i)\bdielectric\b', 'மின்கடத்தா'),
            (r'(?i)\bconductors?\b', 'கடத்தி (Conductor)'),
            (r'(?i)\bcopper\b', 'தாமிரம் (Copper)'),
            (r'(?i)\baluminium\b|\baluminum\b', 'அலுமினியம் (Aluminium)'),
            (r'(?i)\bdistribution\s+transformer\b', 'விநியோக மின்மாற்றி'),
            (r'(?i)\bpower\s+transformer\b', 'பவர் டிரான்ஸ்பார்மர்'),
            (r'(?i)\btransformers?\b', 'மின்மாற்றி'),
            (r'(?i)\boil[\s\-]cooled\b', 'எண்ணெய் குளிரூட்டப்பட்ட'),
            (r'(?i)\bair[\s\-]cooled\b', 'காற்று குளிரூட்டப்பட்ட'),
            (r'(?i)\boutdoor\b', 'வெளிப்புற'),
            (r'(?i)\bindoor\b', 'உட்புற'),
            (r'(?i)\bwaterproof\b', 'நீர்ப்புகா'),
            (r'(?i)\bpolyethylene\s+pipe\b', 'பாலிஎதிலீன் குழாய்'),
            (r'(?i)\bpipes?\b', 'குழாய்'),
            (r'(?i)\bstructural\s+steel\b', 'கட்டமைப்பு எஃகு'),
            (r'(?i)\breinforced\s+concrete\b', 'வலுவூட்டப்பட்ட கான்கிரீட்'),
            (r'(?i)\bconcrete\b', 'கான்கிரீட்'),
            (r'(?i)\bcement\b', 'சிமெண்ட்'),
            (r'(?i)\baggregate\b', 'திரட்டு'),
            (r'(?i)\bpvc\b', 'பிவிசி (PVC)'),
            (r'(?i)\bxlpe\b', 'எக்ஸ்எல்பிஇ (XLPE)'),
            (r'(?i)\bswitchgears?\b', 'சுவிட்ச்கியர்'),
            (r'(?i)\bsteels?\b', 'எஃகு'),
            (r'(?i)\bfasteners?\b', 'ஃபாஸ்டென்சர்கள்'),
            (r'(?i)\bbolts?\b', 'போல்ட்'),
            (r'(?i)\bnuts?\b', 'நட்'),
            (r'(?i)\bscrews?\b', 'திருகு'),
            (r'(?i)\bmatched\s+tokens\b', 'பொருந்தும் டோக்கன்கள்'),
            (r'(?i)\btechnical\s+terminology\s+alignment\b', 'தொழில்நுட்ப சொற்களஞ்சிய சீரமைப்பு'),
            (r'(?i)\brelated\s+reference\b', 'தொடர்புடைய குறிப்பு'),
            (r'(?i)\bdirect\s+match\b', 'நேரடி பொருத்தம்'),
        ]

    res = text
    for pattern, repl in subs:
        res = re.sub(pattern, repl, res)
    return res


class MultilingualResponseGenerator:
    """Generates natural language compliance explanations and reasoning in the user's language."""

    @staticmethod
    def get_title_explanation(standard_number: str, response_lang: str) -> Optional[str]:
        """Provides non-destructive translated explanation alongside official standard title."""
        if response_lang not in ("hi", "ta"):
            return None
        # Match standard prefix or clean identifier
        for std_key, trans_map in TITLE_EXPLANATIONS.items():
            if standard_number.startswith(std_key.split(":")[0]) or std_key in standard_number:
                return trans_map.get(response_lang)
        return None

    @staticmethod
    def format_reasoning(
        reasons: List[str],
        standard_number: str,
        title: str,
        response_lang: str,
        qco_mandatory: bool = False
    ) -> str:
        """Generates the primary applicability reasoning in the detected language without untranslated phrases."""
        if response_lang == "hi":
            clauses = []
            for r in reasons:
                if "Product category verified" in r:
                    m = re.search(r'\((.*?)\)', r) or re.search(r':\s*(.*)', r)
                    param = f" ({_translate_parameter(m.group(1).strip(), 'hi')})" if m and m.group(1).strip() else ""
                    clauses.append(f"उत्पाद श्रेणी सत्यापित{param}")
                elif "Operating voltage verified" in r:
                    m = re.search(r'\((.*?)\)', r) or re.search(r':\s*(.*)', r)
                    param = f" ({_translate_parameter(m.group(1).strip(), 'hi')})" if m and m.group(1).strip() else ""
                    clauses.append(f"कार्यशील वोल्टेज सत्यापित{param}")
                elif "Specified material verified" in r:
                    m = re.search(r'\((.*?)\)', r) or re.search(r':\s*(.*)', r)
                    param = f" ({_translate_parameter(m.group(1).strip(), 'hi')})" if m and m.group(1).strip() else ""
                    clauses.append(f"विनिर्दिष्ट सामग्री सत्यापित{param}")
                elif "Specified environment verified" in r:
                    m = re.search(r'\((.*?)\)', r) or re.search(r':\s*(.*)', r)
                    param = f" ({_translate_parameter(m.group(1).strip(), 'hi')})" if m and m.group(1).strip() else ""
                    clauses.append(f"विनिर्दिष्ट पर्यावरण स्थिति सत्यापित{param}")
                elif "Capacity rating verified" in r:
                    m = re.search(r'\((.*?)\)', r) or re.search(r':\s*(.*)', r)
                    param = f" ({_translate_parameter(m.group(1).strip(), 'hi')})" if m and m.group(1).strip() else ""
                    clauses.append(f"क्षमता रेटिंग सत्यापित{param}")
                elif "Direct reference to standard code" in r:
                    clauses.append(f"मानक कोड {standard_number} के लिए प्रत्यक्ष संदर्भ सत्यापित")
                elif "Technical terminology alignment" in r:
                    m = re.search(r'\((\d+)\s*matched tokens\)', r, re.IGNORECASE)
                    count_str = f" ({m.group(1)} मिलान टोकन)" if m else ""
                    clauses.append(f"तकनीकी शब्दावली संरेखण{count_str}")
                elif "Related reference:" in r:
                    m_code = re.search(r'(IS(?:\s*[\/\-]\s*IEC)?\s*[0-9]+(?:\s*\([^\)]+\))?(?::[0-9]{4})?)', r)
                    code_str = m_code.group(1) if m_code else standard_number
                    if "conductor" in r.lower():
                        clauses.append(f"संबंधित संदर्भ: {code_str} संपूर्ण केबल असेंबली के बजाय कंडक्टर सामग्री निर्दिष्ट करता है")
                    else:
                        clauses.append(_translate_parameter(r, 'hi'))
                elif "Related reference only:" in r:
                    clauses.append(f"केवल संबंधित संदर्भ: {_translate_parameter(r.split(':', 1)[1].strip(), 'hi')}")
                elif "semantic proximity" in r.lower():
                    clauses.append("खरीद विनिर्देश के साथ अर्थपूर्ण निकटता के आधार पर प्राप्त")
                else:
                    clauses.append(_translate_parameter(r, 'hi'))

            if qco_mandatory:
                clauses.append("गुणवत्ता नियंत्रण आदेश (QCO / Quality Control Order) के तहत अनिवार्य")

            base = "। ".join(clauses)
            if not base:
                base = f"तकनीकी आवश्यकताओं के अनुसार {standard_number} सीधे लागू होता है"
            return f"{standard_number}: {base}।"

        elif response_lang == "ta":
            clauses = []
            for r in reasons:
                if "Product category verified" in r:
                    m = re.search(r'\((.*?)\)', r) or re.search(r':\s*(.*)', r)
                    param = f" ({_translate_parameter(m.group(1).strip(), 'ta')})" if m and m.group(1).strip() else ""
                    clauses.append(f"தயாரிப்பு வகை சரிபார்க்கப்பட்டது{param}")
                elif "Operating voltage verified" in r:
                    m = re.search(r'\((.*?)\)', r) or re.search(r':\s*(.*)', r)
                    param = f" ({_translate_parameter(m.group(1).strip(), 'ta')})" if m and m.group(1).strip() else ""
                    clauses.append(f"இயக்க மின்னழுத்தம் சரிபார்க்கப்பட்டது{param}")
                elif "Specified material verified" in r:
                    m = re.search(r'\((.*?)\)', r) or re.search(r':\s*(.*)', r)
                    param = f" ({_translate_parameter(m.group(1).strip(), 'ta')})" if m and m.group(1).strip() else ""
                    clauses.append(f"குறிப்பிட்ட பொருள் சரிபார்க்கப்பட்டது{param}")
                elif "Specified environment verified" in r:
                    m = re.search(r'\((.*?)\)', r) or re.search(r':\s*(.*)', r)
                    param = f" ({_translate_parameter(m.group(1).strip(), 'ta')})" if m and m.group(1).strip() else ""
                    clauses.append(f"குறிப்பிட்ட சுற்றுச்சூழல் நிலை சரிபார்க்கப்பட்டது{param}")
                elif "Capacity rating verified" in r:
                    m = re.search(r'\((.*?)\)', r) or re.search(r':\s*(.*)', r)
                    param = f" ({_translate_parameter(m.group(1).strip(), 'ta')})" if m and m.group(1).strip() else ""
                    clauses.append(f"திறன் மதிப்பீடு சரிபார்க்கப்பட்டது{param}")
                elif "Direct reference to standard code" in r:
                    clauses.append(f"தரநிலை குறியீடு {standard_number} க்கான நேரடி குறிப்பு சரிபார்க்கப்பட்டது")
                elif "Technical terminology alignment" in r:
                    m = re.search(r'\((\d+)\s*matched tokens\)', r, re.IGNORECASE)
                    count_str = f" ({m.group(1)} பொருந்தும் டோக்கன்கள்)" if m else ""
                    clauses.append(f"தொழில்நுட்ப சொற்களஞ்சிய சீரமைப்பு{count_str}")
                elif "Related reference:" in r:
                    m_code = re.search(r'(IS(?:\s*[\/\-]\s*IEC)?\s*[0-9]+(?:\s*\([^\)]+\))?(?::[0-9]{4})?)', r)
                    code_str = m_code.group(1) if m_code else standard_number
                    if "conductor" in r.lower():
                        clauses.append(f"தொடர்புடைய குறிப்பு: {code_str} முழுமையான கேபிள் அசெம்பிளிக்கு பதிலாக கடத்தி பொருட்களைக் குறிப்பிடுகிறது")
                    else:
                        clauses.append(_translate_parameter(r, 'ta'))
                elif "Related reference only:" in r:
                    clauses.append(f"தொடர்புடைய குறிப்பு மட்டுமே: {_translate_parameter(r.split(':', 1)[1].strip(), 'ta')}")
                elif "semantic proximity" in r.lower():
                    clauses.append("கொள்முதல் விவரக்குறிப்புடன் பொருள்சார் அருகாமையின் அடிப்படையில் பெறப்பட்டது")
                else:
                    clauses.append(_translate_parameter(r, 'ta'))

            if qco_mandatory:
                clauses.append("தரக் கட்டுப்பாட்டு உத்தரவு (QCO / Quality Control Order) கீழ் கட்டாயமானது")

            base = ". ".join(clauses)
            if not base:
                base = f"தொழில்நுட்ப தேவைகளின்படி {standard_number} நேரடியாக பொருந்தும்"
            return f"{standard_number}: {base}."

        else:
            # English
            summary = ". ".join(reasons)
            if qco_mandatory and "Mandatory under QCO" not in summary:
                summary = f"{summary}. Mandatory under statutory Quality Control Order (QCO)"
            return summary or f"Relevant standard matching specifications for {title}"

    @staticmethod
    def format_foreign_warning(fs: str, std_num: str, response_lang: str) -> str:
        """Formats statutory precedence warning for foreign standards."""
        if response_lang == "hi":
            return (
                f"खरीद विनिर्देश विदेशी मानक ({fs}) निर्दिष्ट करता है। "
                f"सार्वजनिक खरीद (मेक इन इंडिया को प्राथमिकता) आदेशों के तहत, "
                f"सत्यापित भारतीय मानक {std_num} को वैधानिक प्राथमिकता प्राप्त है। "
                f"समकक्षता और मेक इन इंडिया अनुपालन सत्यापित करने के लिए अधिकारी समीक्षा आवश्यक है।"
            )
        elif response_lang == "ta":
            return (
                f"கொள்முதல் விவரக்குறிப்பு வெளிநாட்டு தரநிலையைக் ({fs}) குறிப்பிடுகிறது. "
                f"பொதுக் கொள்முதல் (மேக் இன் இந்தியாவுக்கு முன்னுரிமை) உத்தரவுகளின் கீழ், "
                f"சரிபார்க்கப்பட்ட இந்திய தரநிலை {std_num} சட்டபூர்வ முன்னுரிமை பெறுகிறது. "
                f"சமநிலையை சரிபார்க்க அதிகாரி மறுஆய்வு தேவைப்படுகிறது."
            )
        else:
            return (
                f"Procurement specifies foreign standard ({fs}). The verified Indian Standard "
                f"({std_num}) takes statutory precedence under Public Procurement (Preference to Make in India) Orders. "
                f"Officer review is required to verify equivalency."
            )

    @staticmethod
    def format_limitation_message(
        response_lang: str,
        product: Optional[str] = None,
        voltage_val: Optional[float] = None,
        foreign_standards: Optional[List[str]] = None,
        is_cable: bool = False
    ) -> str:
        """Formats limitation message when no verified standard matches."""
        fs_str = ", ".join(foreign_standards) if foreign_standards else ""

        if response_lang == "hi":
            if voltage_val and voltage_val > 1100 and is_cable:
                msg = (
                    f"सक्रिय कैटलॉग में कोई भी सत्यापित भारतीय मानक निर्दिष्ट रेटेड ऑपरेटिंग वोल्टेज "
                    f"({int(voltage_val)} V / {voltage_val/1000:g} kV) से पर्याप्त रूप से मेल नहीं खाता है। "
                    f"सक्रिय कैटलॉग मानक IS 694 (450/750 V तक) और IS 1554 Part 1 (1100 V तक) में वोल्टेज रेटिंग संघर्ष है। "
                    f"मैनुअल अधिकारी समीक्षा आवश्यक है।"
                )
            elif product:
                prod_hi = _translate_parameter(product, 'hi')
                msg = (
                    f"सक्रिय कैटलॉग में कोई भी सत्यापित भारतीय मानक विनिर्दिष्ट उत्पाद श्रेणी ('{prod_hi}') "
                    f"से पर्याप्त रूप से मेल नहीं खाता है। साक्ष्य-प्रथम खरीद नीति के अनुसार, असंबद्ध मानकों को "
                    f"रोक दिया गया है। मैनुअल अधिकारी समीक्षा आवश्यक है।"
                )
            else:
                msg = (
                    "सक्रिय कैटलॉग में कोई भी सत्यापित भारतीय मानक पर्याप्त साक्ष्य के साथ खरीद विनिर्देशों "
                    "से मेल नहीं खाता है। मैनुअल अधिकारी समीक्षा आवश्यक है।"
                )

            if fs_str:
                msg += (
                    f" निविदा में विदेशी मानक ({fs_str}) निर्दिष्ट है। सक्रिय कैटलॉग में कोई सत्यापित "
                    f"समकक्ष भारतीय मानक स्थापित नहीं किया गया। अधिकारी सत्यापन आवश्यक है।"
                )
            return msg

        elif response_lang == "ta":
            if voltage_val and voltage_val > 1100 and is_cable:
                msg = (
                    f"செயலில் உள்ள பட்டியலில் எந்தவொரு சரிபார்க்கப்பட்ட இந்திய தரநிலையும் குறிப்பிட்ட "
                    f"இயக்க மின்னழுத்தத்துடன் ({int(voltage_val)} V / {voltage_val/1000:g} kV) போதுமான அளவு "
                    f"பொருந்தவில்லை. செயலில் உள்ள தரநிலைகளான IS 694 (450/750 V வரை) மற்றும் IS 1554 Part 1 "
                    f"(1100 V வரை) ஆகியவற்றில் மின்னழுத்த முரண்பாடுகள் உள்ளன. கையேடு அதிகாரி மறுஆய்வு தேவைப்படுகிறது."
                )
            elif product:
                prod_ta = _translate_parameter(product, 'ta')
                msg = (
                    f"செயலில் உள்ள பட்டியலில் எந்தவொரு சரிபார்க்கப்பட்ட இந்திய தரநிலையும் குறிப்பிட்ட "
                    f"தயாரிப்பு வகையுடன் ('{prod_ta}') போதுமான அளவு பொருந்தவில்லை. சான்று-முதல் கொள்முதல் "
                    f"கொள்கையின்படி, தொடர்பற்ற தரநிலைகள் நிறுத்தி வைக்கப்பட்டுள்ளன. கையேடு அதிகாரி மறுஆய்வு தேவைப்படுகிறது."
                )
            else:
                msg = (
                    "செயலில் உள்ள பட்டியலில் எந்தவொரு சரிபார்க்கப்பட்ட இந்திய தரநிலையும் போதுமான "
                    "ஆதாரங்களுடன் கொள்முதல் விவரக்குறிப்புகளுடன் பொருந்தவில்லை. கையேடு அதிகாரி மறுஆய்வு தேவைப்படுகிறது."
                )

            if fs_str:
                msg += (
                    f" டெண்டர் வெளிநாட்டு தரநிலையைக் ({fs_str}) குறிப்பிடுகிறது. செயலில் உள்ள பட்டியலில் "
                    f"சமமான இந்திய தரநிலை வரைபடம் நிறுவப்படவில்லை. அதிகாரி சரிபார்ப்பு தேவைப்படுகிறது."
                )
            return msg

        else:
            if voltage_val and voltage_val > 1100 and is_cable:
                msg = (
                    f"No verified Indian Standard in the active catalogue adequately matches the specified "
                    f"rated operating voltage ({int(voltage_val)} V / {voltage_val/1000:g} kV). Active catalogue standards "
                    f"IS 694 (up to 450/750 V) and IS 1554 Part 1 (up to 1100 V) have rated voltage conflicts. "
                    f"Manual officer review is required."
                )
            elif product:
                msg = (
                    f"No verified Indian Standard in the active catalogue adequately matches the specified "
                    f"product category ('{product}'). In accordance with evidence-first procurement policy, "
                    f"unrelated standards have been withheld. Manual officer review is required."
                )
            else:
                msg = (
                    "No verified Indian Standard in the active catalogue adequately matches the procurement "
                    "specifications with sufficient evidence. Manual officer review is required."
                )

            if fs_str:
                msg += (
                    f" Tender specifies foreign standard ({fs_str}). No verified equivalent Indian Standard "
                    f"mapping was established in the active catalogue. Manual officer verification is required."
                )
            return msg

    @staticmethod
    def format_incomplete_normalization_message(response_lang: str) -> str:
        """Formats message when non-English query could not be normalized."""
        if response_lang == "hi":
            return (
                "गैर-अंग्रेजी खरीद शब्दों को विश्वसनीय रूप से सामान्यीकृत करने में असमर्थ। "
                "कृपया क्वेरी को फिर से लिखें या मानक तकनीकी शब्दावली का उपयोग करें।"
            )
        elif response_lang == "ta":
            return (
                "ஆங்கிலம் அல்லாத கொள்முதல் சொற்களை நம்பத்தகுந்த முறையில் இயல்பாக்க முடியவில்லை. "
                "தயவுசெய்து வினவலை மீண்டும் எழுதவும் அல்லது நிலையான தொழில்நுட்ப சொற்களைப் பயன்படுத்தவும்."
            )
        else:
            return (
                "Unable to reliably normalize non-English procurement terms. "
                "Please rephrase the query in English or use standard technical terminology."
            )

    @staticmethod
    def format_advisory_notices(advisories: List[str], response_lang: str) -> List[str]:
        """Translates technical advisory notices to the target response language."""
        if response_lang not in ("hi", "ta") or not advisories:
            return advisories

        translated = []
        for adv in advisories:
            if "Rated operating voltage was not specified" in adv:
                if response_lang == "hi":
                    translated.append(
                        "अधिकारी सत्यापन आवश्यक: क्वेरी में रेटेड ऑपरेटिंग वोल्टेज निर्दिष्ट नहीं किया गया था। "
                        "IS 694 450/750 V तक लागू होता है; IS 1554 (Part 1) 1100 V तक भारी शुल्क प्रतिष्ठानों के लिए लागू होता है।"
                    )
                else:
                    translated.append(
                        "அதிகாரி சரிபார்ப்பு தேவை: வினவலில் மதிப்பிடப்பட்ட இயக்க மின்னழுத்தம் குறிப்பிடப்படவில்லை. "
                        "IS 694 என்பது 450/750 V வரை பொருந்தும்; IS 1554 (Part 1) 1100 V வரையிலான கனரக நிறுவல்களுக்குப் பொருந்தும்."
                    )
            elif "Dielectric insulation material was not specified" in adv:
                if response_lang == "hi":
                    translated.append(
                        "अधिकारी सत्यापन आवश्यक: क्वेरी में ढांकता हुआ इन्सुलेशन सामग्री निर्दिष्ट नहीं की गई थी। "
                        "IS 1554 (Part 1) पीवीसी इन्सुलेशन को कवर करता है; IS 7098 (Part 1) एक्सएलपीई इन्सुलेशन को कवर करता है।"
                    )
                else:
                    translated.append(
                        "அதிகாரி சரிபார்ப்பு தேவை: வினவலில் மின்கடத்தா காப்பு பொருள் குறிப்பிடப்படவில்லை. "
                        "IS 1554 (Part 1) பிவிசி காப்பீட்டை உள்ளடக்கியது; IS 7098 (Part 1) எக்ஸ்எல்பிஇ காப்பீட்டை உள்ளடக்கியது."
                    )
            else:
                translated.append(_translate_parameter(adv, response_lang))
        return translated

    @staticmethod
    def format_summary(
        primary_rec: Dict[str, Any],
        response_lang: str,
        total_count: int
    ) -> str:
        """Builds an executive summary in the detected response language."""
        std_num = primary_rec.get("standard_number", "")
        title = primary_rec.get("title", "")
        status = primary_rec.get("status", "Active")
        qco_flag = primary_rec.get("qco_enforcement_flag", False)

        if response_lang == "hi":
            qco_text = "हाँ (गुणवत्ता नियंत्रण आदेश QCO / Quality Control Order के तहत अनिवार्य)" if qco_flag else "लागू होने के लिए सत्यापन आवश्यक (QCO applicability requires verification)"
            return (
                f"अनुशंसित भारतीय मानक: {std_num} ({title})। "
                f"स्थिति: {status}। गुणवत्ता नियंत्रण आदेश (QCO / Quality Control Order): {qco_text}। "
                f"सत्यापित BIS कैटलॉग के अनुसार कुल {total_count} प्रासंगिक मानक पाए गए।"
            )
        elif response_lang == "ta":
            qco_text = "ஆம் (தரக் கட்டுப்பாட்டு உத்தரவு QCO / Quality Control Order கீழ் கட்டாயமானது)" if qco_flag else "பொருந்துவதற்கு சரிபார்ப்பு தேவை (QCO applicability requires verification)"
            return (
                f"பரிந்துரைக்கப்பட்ட இந்திய தரநிலை: {std_num} ({title}). "
                f"நிலை: {status}. தரக் கட்டுப்பாட்டு உத்தரவு (QCO / Quality Control Order): {qco_text}. "
                f"சரிபார்க்கப்பட்ட BIS பட்டியலின்படி மொத்தம் {total_count} பொருத்தமான தரநிலைகள் கண்டறியப்பட்டன."
            )
        else:
            qco_text = "Mandatory (QCO / ISI Mark)" if qco_flag else "Verification required (no standalone mandatory order confirmed in active registry)"
            return (
                f"Recommended Indian Standard: {std_num} ({title}). "
                f"Lifecycle Status: {status}. QCO Enforcement: {qco_text}. "
                f"Found {total_count} verified applicable standards from official BIS catalogue."
            )

    @staticmethod
    def format_next_steps(primary_rec: Dict[str, Any], response_lang: str) -> str:
        """Generates clear procedural next steps for procurement officers."""
        std_num = primary_rec.get("standard_number", "Indian Standard")
        qco_flag = primary_rec.get("qco_enforcement_flag", False)

        if response_lang == "hi":
            steps = [
                f"1. निविदा तकनीकी विनिर्देशों में {std_num} अनिवार्य मानक के रूप में सम्मिलित करें।"
            ]
            if qco_flag:
                steps.append("2. गुणवत्ता नियंत्रण आदेश (QCO / Quality Control Order) के तहत बोलीदाताओं के लिए वैध BIS लाइसेंस / ISI मार्क अनिवार्य करें।")
            else:
                steps.append("2. BIS अनुरूपता प्रमाण पत्र और परीक्षण रिपोर्ट प्रस्तुत करना अनिवार्य करें; QCO प्रयोज्यता का सत्यापन करें।")
            steps.append("3. अंतिम प्रकाशन से पहले सक्षम तकनीकी प्राधिकारी (कार्यकारी अभियंता) से समीक्षा स्वीकृत कराएं।")
            return " ".join(steps)

        elif response_lang == "ta":
            steps = [
                f"1. டெண்டர் தொழில்நுட்ப விவரக்குறிப்புகளில் {std_num}-ஐ கட்டாய தரநிலையாகச் சேர்க்கவும்."
            ]
            if qco_flag:
                steps.append("2. தரக் கட்டுப்பாட்டு உத்தரவின் (QCO / Quality Control Order) கீழ் ஏலதாரர்களுக்கு சரியான BIS உரிமம் / ISI முத்திரையை கட்டாயமாக்குங்கள்.")
            else:
                steps.append("2. BIS இணக்கச் சான்றிதழ் மற்றும் சோதனை அறிக்கைகளை சமர்ப்பிப்பதை கட்டாயமாக்குங்கள்; QCO பொருந்தும்தன்மையை சரிபார்க்கவும்.")
            steps.append("3. இறுதி வெளியீட்டிற்கு முன் தகுதிவாய்ந்த தொழில்நுட்ப அதிகாரியிடமிருந்து (செயல் பொறியாளர்) மதிப்பாய்வை அங்கீகரிக்கவும்.")
            return " ".join(steps)

        else:
            steps = [
                f"1. Cite {std_num} as the governing technical standard in tender specifications."
            ]
            if qco_flag:
                steps.append("2. Mandate valid BIS Certification / ISI Mark under statutory Quality Control Order.")
            else:
                steps.append("2. Require submission of manufacturer test certificates and compliance reports; verify QCO applicability.")
            steps.append("3. Obtain sign-off from designated procurement technical officer prior to tender publication.")
            return " ".join(steps)

    @staticmethod
    def format_compliance_alerts(compliance_list: List[Dict[str, Any]], response_lang: str) -> List[str]:
        """Translates statutory compliance alerts into the response language."""
        if not compliance_list:
            return []

        alerts = []
        for c in compliance_list:
            status = c.get("status", "")
            mark = c.get("mark", "Mandatory")
            mandate = c.get("mandate", "")

            if status == "Mandatory for Procurement" or status == "Mandatory":
                if response_lang == "hi":
                    mark_hi = "ISI मार्क" if "ISI" in mark else mark
                    alerts.append(f"{mark_hi}: गुणवत्ता नियंत्रण आदेश (QCO / Quality Control Order) के तहत खरीद हेतु अनिवार्य")
                elif response_lang == "ta":
                    mark_ta = "ISI முத்திரை" if "ISI" in mark else mark
                    alerts.append(f"{mark_ta}: தரக் கட்டுப்பாட்டு உத்தரவின் (QCO / Quality Control Order) கீழ் கொள்முதலுக்கு கட்டாயமானது")
                else:
                    alerts.append(f"{mark}: {mandate} (Mandatory for Procurement)".strip())
            elif status == "Verification required":
                if response_lang == "hi":
                    alerts.append("गुणवत्ता नियंत्रण आदेश (QCO): लागू होने के लिए सत्यापन आवश्यक (वर्तमान सक्रिय रजिस्ट्री में कोई अनिवार्य आदेश पुष्ट नहीं)")
                elif response_lang == "ta":
                    alerts.append("தரக் கட்டுப்பாட்டு உத்தரவு (QCO): பொருந்துவதற்கு சரிபார்ப்பு தேவை (செயலில் உள்ள பதிவேட்டில் கட்டாய உத்தரவு உறுதிப்படுத்தப்படவில்லை)")
                else:
                    alerts.append("QCO applicability requires verification: No mandatory order confirmed in active registry.")

        return alerts

    @staticmethod
    def format_exclusion_reason(reason: str, response_lang: str) -> str:
        """Translates exclusion reason into the response language."""
        if not reason:
            return reason
        if response_lang == "hi":
            if "Rated voltage conflict" in reason:
                m_q = re.search(r'Query specifies\s+([^\,]+(?:\([^\)]+\))?)', reason)
                m_std = re.search(r'which exceeds\s+([A-Z0-9\s\(\)\:\/\-]+)\s+verified scope\s*\(([^\)]+)\)', reason)
                q_v = m_q.group(1).strip() if m_q else "विनिर्दिष्ट वोल्टेज"
                std_code = m_std.group(1).strip() if m_std else "मानक"
                std_v = m_std.group(2).strip() if m_std else ""
                v_scope = f" ({_translate_parameter(std_v, 'hi')})" if std_v else ""
                return f"प्रत्यक्ष मिलान के रूप में अपवर्जित: रेटेड वोल्टेज संघर्ष। विनिर्देश में {q_v} निर्दिष्ट है, जो {std_code} के सत्यापित कार्यक्षेत्र{v_scope} से अधिक है।"
            elif "Insulation material conflict" in reason:
                m_q = re.search(r'Query specifies\s+([A-Za-z0-9\s]+?)\s+insulation', reason, re.IGNORECASE)
                m_std = re.search(r'verified scope specifies\s+([A-Za-z0-9\s]+?)\s+insulation', reason, re.IGNORECASE)
                q_mat = _translate_parameter(m_q.group(1).strip(), 'hi') if m_q else "सामग्री"
                std_mat = _translate_parameter(m_std.group(1).strip(), 'hi') if m_std else "सामग्री"
                return f"प्रत्यक्ष मिलान के रूप में अपवर्जित: इन्सुलेशन सामग्री संघर्ष। क्वेरी {q_mat} इन्सुलेशन निर्दिष्ट करती है; मानक सत्यापित कार्यक्षेत्र {std_mat} इन्सुलेशन निर्दिष्ट करता है।"
            elif "Incompatible product category" in reason:
                m_prod = re.search(r"standard does not cover '([^']+)'", reason)
                p_trans = f" ('{_translate_parameter(m_prod.group(1), 'hi')}')" if m_prod else ""
                return f"असंगत उत्पाद श्रेणी: मानक विनिर्दिष्ट उत्पाद{p_trans} को कवर नहीं करता है।"
            elif "specifies conductor materials rather than complete cable assembly" in reason:
                m_code = re.search(r'(IS(?:\s*[\/\-]\s*IEC)?\s*[0-9]+(?:\s*\([^\)]+\))?(?::[0-9]{4})?)', reason)
                c_num = m_code.group(1) if m_code else "मानक"
                return f"संबंधित संदर्भ: {c_num} संपूर्ण केबल असेंबली के बजाय कंडक्टर सामग्री निर्दिष्ट करता है।"
            elif "Alternative dielectric material" in reason:
                return "केवल संबंधित संदर्भ: वैकल्पिक परावैद्युत इन्सुलेशन सामग्री।"
            elif "Scope conflict" in reason:
                return "विनिर्दिष्ट तकनीकी आवश्यकताओं के साथ कार्यक्षेत्र असंगति"
            return _translate_parameter(reason, "hi")

        elif response_lang == "ta":
            if "Rated voltage conflict" in reason:
                m_q = re.search(r'Query specifies\s+([^\,]+(?:\([^\)]+\))?)', reason)
                m_std = re.search(r'which exceeds\s+([A-Z0-9\s\(\)\:\/\-]+)\s+verified scope\s*\(([^\)]+)\)', reason)
                q_v = m_q.group(1).strip() if m_q else "குறிப்பிட்ட மின்னழுத்தம்"
                std_code = m_std.group(1).strip() if m_std else "தரநிலை"
                std_v = m_std.group(2).strip() if m_std else ""
                v_scope = f" ({_translate_parameter(std_v, 'ta')})" if std_v else ""
                return f"நேரடிப் பொருத்தமாக விலக்கப்பட்டது: மதிப்பிடப்பட்ட மின்னழுத்த முரண்பாடு. வினவல் {q_v}-ஐக் குறிப்பிடுகிறது, இது {std_code}-இன் சரிபார்க்கப்பட்ட வரம்பை{v_scope} விட அதிகமாக உள்ளது."
            elif "Insulation material conflict" in reason:
                m_q = re.search(r'Query specifies\s+([A-Za-z0-9\s]+?)\s+insulation', reason, re.IGNORECASE)
                m_std = re.search(r'verified scope specifies\s+([A-Za-z0-9\s]+?)\s+insulation', reason, re.IGNORECASE)
                q_mat = _translate_parameter(m_q.group(1).strip(), 'ta') if m_q else "பொருள்"
                std_mat = _translate_parameter(m_std.group(1).strip(), 'ta') if m_std else "பொருள்"
                return f"நேரடிப் பொருத்தமாக விலக்கப்பட்டது: காப்புப் பொருள் முரண்பாடு. வினவல் {q_mat} காப்பீட்டைக் குறிப்பிடுகிறது; தரநிலை சரிபார்க்கப்பட்ட வரம்பு {std_mat} காப்பீட்டைக் குறிப்பிடுகிறது."
            elif "Incompatible product category" in reason:
                m_prod = re.search(r"standard does not cover '([^']+)'", reason)
                p_trans = f" ('{_translate_parameter(m_prod.group(1), 'ta')}')" if m_prod else ""
                return f"பொருந்தாத தயாரிப்பு வகை: தரநிலை குறிப்பிட்ட தயாரிப்பை{p_trans} உள்ளடக்கவில்லை."
            elif "specifies conductor materials rather than complete cable assembly" in reason:
                m_code = re.search(r'(IS(?:\s*[\/\-]\s*IEC)?\s*[0-9]+(?:\s*\([^\)]+\))?(?::[0-9]{4})?)', reason)
                c_num = m_code.group(1) if m_code else "தரநிலை"
                return f"தொடர்புடைய குறிப்பு: {c_num} முழுமையான கேபிள் அசெம்பிளிக்கு பதிலாக கடத்தி பொருட்களைக் குறிப்பிடுகிறது."
            elif "Alternative dielectric material" in reason:
                return "தொடர்புடைய குறிப்பு மட்டுமே: மாற்று மின்கடத்தா காப்பு பொருள்."
            elif "Scope conflict" in reason:
                return "குறிப்பிட்ட தொழில்நுட்ப தேவைகளுடன் வரம்பு முரண்பாடு"
            return _translate_parameter(reason, "ta")

        return reason

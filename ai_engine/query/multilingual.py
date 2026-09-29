"""
Multilingual Query Understanding & Normalization for SIH26108 (Feature M9).
Provides:
- Dependency-free Unicode script and language detection (Tamil, Hindi/Devanagari, English, Mixed, Unknown).
- Unicode-safe tokenization and cleaning preserving standards, ratings, and voltage values.
- Two-tier normalization:
  1. Configured LLM Provider (if available and responsive).
  2. High-precision deterministic offline bilingual lexicon for Tamil & Hindi procurement terms.
- Transparent normalization status: SUCCESS, UNCHANGED, or INCOMPLETE.
"""
import re
import unicodedata
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("sih26108.multilingual")

# Unicode block definitions
TAMIL_START, TAMIL_END = 0x0B80, 0x0BFF
DEVANAGARI_START, DEVANAGARI_END = 0x0900, 0x097F


TECH_ACRONYMS = {
    "v", "kv", "kva", "mva", "kw", "mw", "hz", "pvc", "xlpe", "is",
    "astm", "iec", "din", "bs", "part", "fe", "tmt", "mm", "kg", "ton", "tons", "sq"
}


def detect_language_and_script(text: str) -> Dict[str, str]:
    """
    Dependency-free script and language detector with dominant-language resolution:
    - Tamil: Unicode range U+0B80–U+0BFF
    - Hindi / Devanagari: Unicode range U+0900–U+097F
    - English: Latin script (a-z, A-Z)
    Returns:
      detected_language: 'ta', 'hi', 'en', 'mixed', or 'unknown'
      detected_script: 'Tamil', 'Devanagari', 'Latin', 'Tamil + Latin', 'Devanagari + Latin', 'Mixed Indic', or 'Unknown'
      response_language: 'en', 'hi', or 'ta'
      response_language_name: 'English', 'Hindi', or 'Tamil'
    """
    if not text or not text.strip():
        return {
            "detected_language": "unknown",
            "detected_script": "Unknown",
            "response_language": "en",
            "response_language_name": "English"
        }

    tamil_count = sum(1 for c in text if TAMIL_START <= ord(c) <= TAMIL_END)
    devanagari_count = sum(1 for c in text if DEVANAGARI_START <= ord(c) <= DEVANAGARI_END)
    latin_count = sum(1 for c in text if ('a' <= c <= 'z') or ('A' <= c <= 'Z'))

    # Extract alphanumeric words and filter out pure technical units/ratings
    words = re.findall(r'[\w]+', text)
    latin_non_tech = []
    devanagari_words = []
    tamil_words = []

    for w in words:
        w_lower = w.lower()
        if w_lower in TECH_ACRONYMS or w.isdigit():
            continue
        has_ta = any(TAMIL_START <= ord(c) <= TAMIL_END for c in w)
        has_hi = any(DEVANAGARI_START <= ord(c) <= DEVANAGARI_END for c in w)
        has_lat = any(('a' <= c <= 'z') or ('A' <= c <= 'Z') for c in w)
        if has_ta:
            tamil_words.append(w)
        elif has_hi:
            devanagari_words.append(w)
        elif has_lat:
            latin_non_tech.append(w)

    # 1. Pure Tamil or Tamil + Latin
    if tamil_count > 0 and devanagari_count == 0:
        if latin_count == 0:
            return {
                "detected_language": "ta",
                "detected_script": "Tamil",
                "response_language": "ta",
                "response_language_name": "Tamil"
            }
        # Mixed Tamil + Latin: evaluate dominant intent
        if len(tamil_words) >= len(latin_non_tech) or tamil_count >= latin_count:
            return {
                "detected_language": "ta",
                "detected_script": "Tamil + Latin",
                "response_language": "ta",
                "response_language_name": "Tamil"
            }
        else:
            return {
                "detected_language": "en",
                "detected_script": "Latin + Tamil",
                "response_language": "en",
                "response_language_name": "English"
            }

    # 2. Pure Hindi or Devanagari + Latin
    if devanagari_count > 0 and tamil_count == 0:
        if latin_count == 0:
            return {
                "detected_language": "hi",
                "detected_script": "Devanagari",
                "response_language": "hi",
                "response_language_name": "Hindi"
            }
        # Mixed Devanagari + Latin: evaluate dominant intent
        if len(devanagari_words) >= len(latin_non_tech) or devanagari_count >= latin_count:
            return {
                "detected_language": "hi",
                "detected_script": "Devanagari + Latin",
                "response_language": "hi",
                "response_language_name": "Hindi"
            }
        else:
            return {
                "detected_language": "en",
                "detected_script": "Latin + Devanagari",
                "response_language": "en",
                "response_language_name": "English"
            }

    # 3. Mixed Indic (Tamil and Devanagari)
    if devanagari_count > 0 and tamil_count > 0:
        dominant = "ta" if tamil_count >= devanagari_count else "hi"
        lang_name = "Tamil" if dominant == "ta" else "Hindi"
        return {
            "detected_language": "mixed",
            "detected_script": "Mixed Indic",
            "response_language": dominant,
            "response_language_name": lang_name
        }

    # 4. Pure Latin (English)
    if latin_count > 0:
        return {
            "detected_language": "en",
            "detected_script": "Latin",
            "response_language": "en",
            "response_language_name": "English"
        }

    return {
        "detected_language": "unknown",
        "detected_script": "Unknown",
        "response_language": "en",
        "response_language_name": "English"
    }


def tokenize_unicode(text: str) -> List[str]:
    """
    Unicode-aware tokenizer preserving:
    - Standard identifiers (e.g. 'IS 1180 (Part 1):2014')
    - Voltage and rating expressions (e.g. '500 kVA', '11 kV/433 V', '1100 V')
    - Unicode words in Devanagari, Tamil, and Latin scripts
    """
    if not text:
        return []

    # Preserve letters (all scripts), non-spacing/combining marks, numbers, and code punctuation
    def is_word_or_mark(c: str) -> bool:
        cat = unicodedata.category(c)
        return cat.startswith(('L', 'M', 'N')) or c in '-_/:().'

    cleaned = "".join(c if is_word_or_mark(c) else " " for c in text)
    tokens = [t.strip() for t in cleaned.split() if t.strip()]
    return tokens


class MultilingualNormalizer:
    """
    Normalizes procurement queries from Tamil or Hindi into English technical requirements.
    Tier 1: Configured LLM provider (when available).
    Tier 2: High-fidelity deterministic offline bilingual procurement lexicon.
    """

    STANDARDS_PATTERN = re.compile(
        r'\b(?:IS(?:\s*[\/\-]\s*IEC)?\s*[0-9]+(?:\s*\([A-Za-z0-9\s]+\))?(?::[0-9]{4})?|'
        r'(?:ASTM\s+[A-Za-z][0-9]+(?:[\-A-Za-z0-9]+)?)|'
        r'(?:IEC\s+[0-9]+(?:\-[0-9]+)?)|(?:DIN\s+[0-9]+)|(?:BS\s+[0-9]+)|'
        r'(?:IEEE\s+[0-9]+)|(?:EN\s+[0-9]+)|(?:ISO\s+[0-9]+))\b',
        re.IGNORECASE
    )

    VOLTAGE_PAIR_PATTERN = re.compile(
        r'\b(\d+(?:\.\d+)?\s*(?:kv|v))\s*(?:\/|to|\-)\s*(\d+(?:\.\d+)?\s*(?:kv|v))\b',
        re.IGNORECASE
    )

    RATINGS_PATTERN = re.compile(
        r'\b(\d+(?:\.\d+)?\s*(?:kva|mva|kw|mw|hp|w|kv|v|sq\.?\s*mm|mm|m|kg|ton|tons|liters|litres|ltr|l))\b',
        re.IGNORECASE
    )

    # Curated, verified offline bilingual domain lexicon for procurement terms
    # Sorted by character length descending during matching for multi-word phrase priority.
    HINDI_LEXICON = {
        # Multi-word compound phrases
        "वितरण ट्रांसफार्मर": "distribution transformer",
        "पावर ट्रांसफार्मर": "power transformer",
        "विद्युत केबल": "electric cable",
        "बिजली केबल": "electric cable",
        "पावर केबल": "power cable",
        "कंट्रोल केबल": "control cable",
        "विद्युत तार": "electric wire",
        "भारी शुल्क": "heavy duty",
        "भारी": "heavy duty",
        "कवचयुक्त केबल": "armored cable",
        "कवचयुक्त": "armored",
        "आर्मर्ड": "armored",
        "भूमिगत केबल": "underground cable",
        "भूमिगत": "underground",
        "साधारण पोर्टलैंड सीमेंट": "ordinary portland cement",
        "पोर्टलैंड पोज़ोलाना सीमेंट": "portland pozzolana cement",
        "पोर्टलैंड सीमेंट": "portland cement",
        "प्रबलित कंक्रीट": "reinforced concrete",
        "कंक्रीट समुच्चय": "concrete aggregate",
        "संरचनात्मक स्टील": "structural steel",
        "संरचनात्मक इस्पात": "structural steel",
        "टीएमटी बार": "TMT bar",
        "पॉलीइथिलीन पाइप": "polyethylene pipe",
        "जल आपूर्ति": "water supply",
        "तेल ठंडा": "oil-cooled",
        "ऑयल कूल्ड": "oil-cooled",
        "वायु ठंडा": "air-cooled",
        "एयर कूल्ड": "air-cooled",
        # Single keywords
        "केबल": "cable",
        "तार": "wire",
        "कंडक्टर": "conductor",
        "चालक": "conductor",
        "पीवीसी": "PVC",
        "एक्सएलपीई": "XLPE",
        "ट्रांसफार्मर": "transformer",
        "परिणामित्र": "transformer",
        "सीमेंट": "cement",
        "कंक्रीट": "concrete",
        "स्टील": "steel",
        "इस्पात": "steel",
        "सरिया": "deformed bar",
        "पाइप": "pipe",
        "बोल्ट": "bolt",
        "नट": "nut",
        "फास्टनर": "fastener",
        "जलरोधी": "waterproof",
        "वाटरप्रूफ": "waterproof",
        "पेयजल": "drinking water",
        "समुच्चय": "aggregate",
        "एग्रीगेट": "aggregate",
        "आउटडोर": "outdoor",
        "बाहरी": "outdoor",
        "इनडोर": "indoor",
        "आंतरिक": "indoor",
        # Procurement & Query Intent Phrases
        "लागू भारतीय मानक बताइए": "applicable Indian Standard",
        "लागू भारतीय मानक बताएं": "applicable Indian Standard",
        "लागू भारतीय मानक": "applicable Indian Standard",
        "भारतीय मानक बताइए": "Indian Standard",
        "भारतीय मानक बताएं": "Indian Standard",
        "भारतीय मानक": "Indian Standard",
        "लागू मानक बताइए": "applicable standard",
        "लागू मानक बताएं": "applicable standard",
        "लागू मानक": "applicable standard",
        "मानक बताइए": "standard",
        "मानक बताएं": "standard",
        "मानक": "standard",
        "लागू": "applicable",
        "के लिए": "for",
        "आवश्यकता": "requirement",
        "विनिर्देश": "specification",
        "बताइए": "",
        "बताएं": "",
        "दीजिए": "",
        "चाहिए": "required",
        "खोजें": "find",
        "ढूंढें": "find",
    }

    TAMIL_LEXICON = {
        # Multi-word compound phrases
        "விநியோக மின்மாற்றி": "distribution transformer",
        "மின்சார கேபிள்": "electric cable",
        "மின் கேபிள்": "electric cable",
        "மின்கேபிள்": "electric cable",
        "கவச கேபிள்": "armored cable",
        "மின் கம்பி": "electric wire",
        "மின் விநியோகம்": "power distribution",
        "நிலத்தடி கேபிள்": "underground cable",
        "வலுவூட்டப்பட்ட கான்கிரீட்": "reinforced concrete",
        "வலுவூட்டல் எஃகு கம்பிகள்": "deformed steel bars",
        "கட்டமைப்பு எஃகு": "structural steel",
        "பாலிஎதிலீன் குழாய்": "polyethylene pipe",
        "எண்ணெய் குளிரூட்டப்பட்ட": "oil-cooled",
        "காற்று குளிரூட்டப்பட்ட": "air-cooled",
        # Procurement & Query Intent Phrases
        "பொருந்தும் இந்திய தரநிலையைச் சொல்லுங்கள்": "applicable Indian Standard",
        "பொருந்தும் இந்திய தரநிலையை சொல்லுங்கள்": "applicable Indian Standard",
        "பொருந்தும் இந்திய தரநிலை": "applicable Indian Standard",
        "இந்திய தரநிலையைச் சொல்லுங்கள்": "Indian Standard",
        "இந்திய தரநிலையை சொல்லுங்கள்": "Indian Standard",
        "இந்திய தரநிலை": "Indian Standard",
        "பொருந்தும் தரநிலையைச் சொல்லுங்கள்": "applicable standard",
        "பொருந்தும் தரநிலை": "applicable standard",
        "தரநிலையைச் சொல்லுங்கள்": "standard",
        "தரநிலையை சொல்லுங்கள்": "standard",
        "தரநிலை": "standard",
        "பொருந்தும்": "applicable",
        "சொல்லுங்கள்": "",
        "கேபிளுக்குப்": "cable",
        "கேபிளுக்கு": "cable",
        "மின்மாற்றிக்கு": "transformer",
        "தேவை": "required",
        "விவரக்குறிப்பு": "specification",
        "கண்டுபிடி": "find",
        # Single keywords
        "மின்மாற்றி": "transformer",
        "கேபிள்": "cable",
        "கம்பி": "wire",
        "கடத்தி": "conductor",
        "பிவிசி": "PVC",
        "பி.வி.சி": "PVC",
        "எக்ஸ்எல்பிஇ": "XLPE",
        "கனரக": "heavy duty",
        "நிலத்தடி": "underground",
        "நீர்ப்புகா": "waterproof",
        "சிமெண்ட்": "cement",
        "சிமென்ட்": "cement",
        "கான்கிரீட்": "concrete",
        "எஃகு": "steel",
        "சரளை": "aggregate",
        "மணல்": "sand",
        "குழாய்": "pipe",
        "திருகாணி": "bolt",
        "நட்டு": "nut",
        "குடிநீர்": "drinking water",
        "வெளிப்புற": "outdoor",
        "உட்புற": "indoor",
    }

    def __init__(self, provider: Optional[Any] = None):
        self.provider = provider

    def normalize(self, query: str) -> Dict[str, Any]:
        """
        Normalizes natural language procurement query into English.
        Returns dict with:
        - detected_language: 'ta', 'hi', 'en', 'mixed', 'unknown'
        - detected_script: 'Tamil', 'Devanagari', 'Latin', etc.
        - response_language: 'en', 'hi', or 'ta'
        - response_language_name: 'English', 'Hindi', or 'Tamil'
        - original_query: original input string
        - normalized_english_query: English technical query string
        - normalization_method: 'UNCHANGED_ENGLISH', 'LLM', 'LOCAL_LEXICON', or 'INCOMPLETE'
        - normalization_status: 'UNCHANGED', 'SUCCESS', or 'INCOMPLETE'
        - normalization_message: human-readable status explanation
        - clean_tokens: Unicode-safe extracted tokens
        """
        if not query or not query.strip():
            return {
                "detected_language": "unknown",
                "detected_script": "Unknown",
                "response_language": "en",
                "response_language_name": "English",
                "original_query": "",
                "normalized_english_query": "",
                "normalization_method": "INCOMPLETE",
                "normalization_status": "INCOMPLETE",
                "normalization_message": "Empty query provided.",
                "clean_tokens": []
            }

        cleaned_query = query.strip()
        lang_info = detect_language_and_script(cleaned_query)
        detected_lang = lang_info["detected_language"]
        detected_script = lang_info["detected_script"]
        response_lang = lang_info.get("response_language", "en")
        response_lang_name = lang_info.get("response_language_name", "English")

        # ── Case 1: English-only query ───────────────────────────────────────
        if detected_lang == "en":
            tokens = tokenize_unicode(cleaned_query)
            return {
                "detected_language": "en",
                "detected_script": detected_script,
                "response_language": "en",
                "response_language_name": "English",
                "original_query": cleaned_query,
                "normalized_english_query": cleaned_query,
                "normalization_method": "UNCHANGED_ENGLISH",
                "normalization_status": "UNCHANGED",
                "normalization_message": "Input query is predominantly Latin script. No translation required.",
                "clean_tokens": tokens
            }

        # ── Case 2: Multilingual (Tamil, Hindi, Mixed) ───────────────────────
        # Tier 1: Try LLM translation if provider is available, valid, and not mock
        if self.provider and hasattr(self.provider, "is_available") and self.provider.is_available():
            provider_name = getattr(self.provider, "__class__", type(self.provider)).__name__
            if provider_name not in ("MockLLMProvider", "NoneType"):
                try:
                    llm_result = self._try_llm_translation(cleaned_query)
                    if llm_result:
                        tokens = tokenize_unicode(llm_result)
                        return {
                            "detected_language": detected_lang,
                            "detected_script": detected_script,
                            "response_language": response_lang,
                            "response_language_name": response_lang_name,
                            "original_query": cleaned_query,
                            "normalized_english_query": llm_result,
                            "normalization_method": "LLM",
                            "normalization_status": "SUCCESS",
                            "normalization_message": f"Query translated from {detected_script} via AI Provider ({provider_name}).",
                            "clean_tokens": tokens
                        }
                except Exception as e:
                    logger.warning(f"LLM translation attempt failed ({type(e).__name__}). Falling back to local lexicon.")

        # Tier 2: Deterministic Local Lexicon Normalization
        lexicon_result = self._normalize_via_lexicon(cleaned_query, detected_lang)
        lexicon_result["response_language"] = response_lang
        lexicon_result["response_language_name"] = response_lang_name
        return lexicon_result

    def _normalize_via_lexicon(self, query: str, detected_lang: str) -> Dict[str, Any]:
        """Performs token-protected deterministic bilingual dictionary translation."""
        lang_info = detect_language_and_script(query)
        detected_script = lang_info["detected_script"]
        response_lang = lang_info.get("response_language", "en")
        response_lang_name = lang_info.get("response_language_name", "English")

        # Step 1: Protect standards identifiers, voltage pairs, and rating tokens
        placeholders: List[str] = []
        working_text = query

        def protect(match: re.Match) -> str:
            token = match.group(0).strip()
            idx = len(placeholders)
            placeholders.append(token)
            return f" __PROTECTED_TOKEN_{idx}__ "

        # Protect standard codes first (e.g. 'IS 1180 (Part 1):2014')
        working_text = self.STANDARDS_PATTERN.sub(protect, working_text)
        # Protect voltage pairs (e.g. '11 kV/433 V')
        working_text = self.VOLTAGE_PAIR_PATTERN.sub(protect, working_text)
        # Protect ratings with units (e.g. '500 kVA', '1100 V')
        working_text = self.RATINGS_PATTERN.sub(protect, working_text)

        # Step 2: Select relevant lexicon dictionary
        lexicon: Dict[str, str] = {}
        if detected_lang in ("hi", "mixed"):
            lexicon.update(self.HINDI_LEXICON)
        if detected_lang in ("ta", "mixed"):
            lexicon.update(self.TAMIL_LEXICON)
        if not lexicon:
            # Combined fallback
            lexicon.update(self.HINDI_LEXICON)
            lexicon.update(self.TAMIL_LEXICON)

        # Sort entries by length descending for greedy longest-match replacement
        sorted_terms = sorted(lexicon.keys(), key=lambda k: len(k), reverse=True)
        translated_count = 0

        for term in sorted_terms:
            if term in working_text:
                replacement = lexicon[term]
                # Replace term with English equivalent, ensuring whitespace boundaries
                working_text = working_text.replace(term, f" {replacement} ")
                translated_count += 1

        # Step 3: Re-inject protected tokens
        for idx, orig_token in enumerate(placeholders):
            placeholder_tag = f"__PROTECTED_TOKEN_{idx}__"
            working_text = working_text.replace(placeholder_tag, orig_token)

        # Normalize redundant spaces and remove punctuation markers like danda
        working_text = working_text.replace("।", " ")
        normalized_str = " ".join(working_text.split()).strip()

        # Step 4: Check if non-English characters remain
        indic_remaining = sum(
            1 for c in normalized_str
            if (TAMIL_START <= ord(c) <= TAMIL_END) or (DEVANAGARI_START <= ord(c) <= DEVANAGARI_END)
        )

        # If we translated terms OR preserved protected standards/ratings and no unhandled text
        has_english_or_protected = bool(placeholders or translated_count > 0)

        if indic_remaining == 0 and has_english_or_protected:
            tokens = tokenize_unicode(normalized_str)
            return {
                "detected_language": detected_lang,
                "detected_script": detected_script,
                "response_language": response_lang,
                "response_language_name": response_lang_name,
                "original_query": query,
                "normalized_english_query": normalized_str,
                "normalization_method": "LOCAL_LEXICON",
                "normalization_status": "SUCCESS",
                "normalization_message": f"Successfully normalized from {detected_script} using deterministic procurement lexicon.",
                "clean_tokens": tokens
            }
        elif translated_count > 0 and indic_remaining > 0:
            # Partially translated: technical terms mapped, but some untranslated words remain
            tokens = tokenize_unicode(normalized_str)
            return {
                "detected_language": detected_lang,
                "detected_script": detected_script,
                "response_language": response_lang,
                "response_language_name": response_lang_name,
                "original_query": query,
                "normalized_english_query": normalized_str,
                "normalization_method": "LOCAL_LEXICON",
                "normalization_status": "SUCCESS",
                "normalization_message": f"Partially normalized from {detected_script} with recognized technical terms.",
                "clean_tokens": tokens
            }
        else:
            # Unsupported vocabulary: no technical procurement terms recognized
            return {
                "detected_language": detected_lang,
                "detected_script": detected_script,
                "response_language": response_lang,
                "response_language_name": response_lang_name,
                "original_query": query,
                "normalized_english_query": None,
                "normalization_method": "INCOMPLETE",
                "normalization_status": "INCOMPLETE",
                "normalization_message": (
                    f"Unable to reliably normalize non-English procurement terms from {detected_script}. "
                    "Please rephrase the query in English or use standard technical terminology."
                ),
                "clean_tokens": tokenize_unicode(query)
            }

    def _try_llm_translation(self, query: str) -> Optional[str]:
        """Prompts LLM to translate procurement specification to English technical keywords."""
        if not self.provider:
            return None

        # Provider must have parse_query or similar API
        parsed_reqs = self.provider.parse_query(query)
        if parsed_reqs and parsed_reqs.product:
            parts = []
            if parsed_reqs.capacity:
                parts.append(parsed_reqs.capacity)
            if parsed_reqs.cooling:
                parts.append(parsed_reqs.cooling)
            if parsed_reqs.product:
                parts.append(parsed_reqs.product)
            if parsed_reqs.primary_voltage:
                parts.append(parsed_reqs.primary_voltage)
            if parsed_reqs.secondary_voltage:
                parts.append(parsed_reqs.secondary_voltage)
            if parsed_reqs.foreign_standards:
                parts.extend(parsed_reqs.foreign_standards)
            return " ".join(parts)
        return None

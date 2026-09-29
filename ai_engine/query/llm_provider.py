"""
LLM Provider Abstraction Layer for SIH26108.
Supports Gemini, OpenAI, Mock, and Local Fallback with:
- Strict JSON structured output validation
- Configurable timeout handling
- Environment-based API key loading
- Zero API key exposure in logs and error responses
"""
import os
import json
import logging
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
except ImportError:
    pass

from ai_engine.query.schema import StructuredRequirements
from ai_engine.query.rule_extractor import RuleExtractor

logger = logging.getLogger("sih26108.llm")

def mask_secret(secret: Optional[str]) -> str:
    """Masks secret keys for safe logging without exposure."""
    if not secret:
        return "<not set>"
    if len(secret) <= 8:
        return "***"
    return f"{secret[:4]}...{secret[-4:]}"

class BaseLLMProvider(ABC):
    """Abstract base class for natural language procurement query understanding providers."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: float = 5.0):
        self.api_key = api_key.strip() if api_key is not None else os.getenv("LLM_API_KEY", "").strip()
        self.model = model
        self.timeout = timeout

    @abstractmethod
    def parse_query(self, query: str) -> Optional[StructuredRequirements]:
        """Converts natural language procurement query into validated StructuredRequirements."""
        pass

    def generate_multilingual_response(
        self,
        query: str,
        context: Dict[str, Any],
        target_language: str
    ) -> Optional[Dict[str, Any]]:
        """Generates structured multilingual explanation and summary in the target language."""
        return None

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is configured and ready to handle requests."""
        pass

    def validate_output(self, raw_data: Any) -> Optional[StructuredRequirements]:
        """Validates and parses raw dictionary or JSON string into StructuredRequirements."""
        try:
            if isinstance(raw_data, str):
                # Clean codeblock markdown markers if present
                clean_str = raw_data.strip()
                if clean_str.startswith("```json"):
                    clean_str = clean_str[7:]
                elif clean_str.startswith("```"):
                    clean_str = clean_str[3:]
                if clean_str.endswith("```"):
                    clean_str = clean_str[:-3]
                parsed = json.loads(clean_str.strip())
            elif isinstance(raw_data, dict):
                parsed = raw_data
            else:
                return None

            return StructuredRequirements(
                product=parsed.get("product"),
                capacity=parsed.get("capacity"),
                cooling=parsed.get("cooling"),
                installation=parsed.get("installation"),
                primary_voltage=parsed.get("primary_voltage"),
                secondary_voltage=parsed.get("secondary_voltage"),
                foreign_standards=parsed.get("foreign_standards", []) or [],
                application=parsed.get("application"),
                additional_parameters=parsed.get("additional_parameters", {}) or {}
            )
        except Exception as e:
            logger.warning(f"Structured output validation failed: {type(e).__name__}")
            return None


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM provider for deterministic offline testing and automated verification.
    Requires no external network or paid API key.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: float = 5.0):
        super().__init__(api_key=api_key or "mock_key", model=model or "mock-model", timeout=timeout)
        self.rule_extractor = RuleExtractor()

    def is_available(self) -> bool:
        return True

    def parse_query(self, query: str) -> Optional[StructuredRequirements]:
        """Uses rule-based extractor to simulate high-fidelity LLM structured extraction."""
        if not query or not query.strip():
            return None
        return self.rule_extractor.extract(query)

    def generate_multilingual_response(
        self,
        query: str,
        context: Dict[str, Any],
        target_language: str
    ) -> Optional[Dict[str, Any]]:
        """Uses deterministic MultilingualResponseGenerator for fast, reliable offline multilingual responses."""
        from ai_engine.recommendation.multilingual_response import MultilingualResponseGenerator
        recs = context.get("recommendations", [])
        if not recs:
            limitation = MultilingualResponseGenerator.format_limitation_message(
                response_lang=target_language,
                product=context.get("product"),
                voltage_val=context.get("voltage"),
                foreign_standards=context.get("foreign_standards"),
                is_cable=context.get("is_cable", False)
            )
            return {
                "summary": limitation,
                "reason": limitation,
                "limitations": limitation,
                "next_steps": "Manual officer review required."
            }

        top_rec = recs[0]
        std_num = top_rec.get("standard_number", "")
        title = top_rec.get("title", "")
        reasons = top_rec.get("ranking_reasons") or [top_rec.get("reason", "")]
        qco = top_rec.get("qco_enforcement_flag", False)

        reason = MultilingualResponseGenerator.format_reasoning(
            reasons=reasons,
            standard_number=std_num,
            title=title,
            response_lang=target_language,
            qco_mandatory=qco
        )
        title_exp = MultilingualResponseGenerator.get_title_explanation(std_num, target_language)
        summary = MultilingualResponseGenerator.format_summary(top_rec, target_language, len(recs))
        next_steps = MultilingualResponseGenerator.format_next_steps(top_rec, target_language)

        return {
            "summary": summary,
            "reason": reason,
            "title_explanation": title_exp,
            "limitations": None,
            "next_steps": next_steps
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider for structured query understanding."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: float = 5.0):
        default_model = os.getenv("LLM_MODEL", "gemini-3.6-flash")
        super().__init__(api_key=api_key, model=model or default_model, timeout=timeout)

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    def parse_query(self, query: str) -> Optional[StructuredRequirements]:
        if not self.is_available() or not query.strip():
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        prompt = (
            "You are a technical procurement requirements parser for Indian engineering standards.\n"
            "Extract structured technical parameters from this procurement query into valid JSON.\n"
            "DO NOT recommend or invent any Indian Standard codes.\n"
            "Schema:\n"
            "{\n"
            '  "product": string or null,\n'
            '  "capacity": string or null,\n'
            '  "cooling": string or null,\n'
            '  "installation": string or null,\n'
            '  "primary_voltage": string or null,\n'
            '  "secondary_voltage": string or null,\n'
            '  "foreign_standards": list of strings,\n'
            '  "application": string or null\n'
            "}\n\n"
            f"Query: {query}\n"
            "Output JSON only:"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json"
            }
        }

        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            raw_text = parts[0].get("text", "")
                            return self.validate_output(raw_text)
            except urllib.error.HTTPError as e:
                if e.code in (500, 502, 503, 504) and attempt == 0:
                    import time
                    time.sleep(1.0)
                    continue
                logger.warning(f"Gemini API request failed (HTTP {e.code}). Falling back to local extractor.")
                break
            except Exception as e:
                # Safe logging: never print API key or URL with key
                exc_name = type(e).__name__
                if attempt == 0 and ("RemoteDisconnected" in exc_name or "timeout" in exc_name.lower()):
                    import time
                    time.sleep(1.0)
                    continue
                logger.warning(f"Gemini API request failed ({exc_name}). Falling back to local extractor.")
                break

        return None

    def generate_multilingual_response(
        self,
        query: str,
        context: Dict[str, Any],
        target_language: str
    ) -> Optional[Dict[str, Any]]:
        """Generates multilingual explanation in target_language using Gemini API."""
        if not self.is_available() or not query.strip():
            return None

        lang_names = {"en": "English", "hi": "Hindi", "ta": "Tamil"}
        target_lang_name = lang_names.get(target_language, "English")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        prompt = (
            f"You are a technical compliance officer for the Bureau of Indian Standards (BIS SpecEngine).\n"
            f"Generate an authoritative procurement recommendation explanation strictly in {target_lang_name} ({target_language}).\n\n"
            f"USER QUERY: {query}\n"
            f"TARGET RESPONSE LANGUAGE: {target_lang_name}\n"
            f"VERIFIED CONTEXT:\n{json.dumps(context, ensure_ascii=False)}\n\n"
            "MANDATORY RULES:\n"
            f"1. Generate reasoning, explanation, summary, and next_steps strictly in {target_lang_name}.\n"
            "2. DO NOT translate official standard numbers or IS codes (e.g. 'IS 1554 (Part 1):1988'), IEC codes, ASTM codes, or QCO identifiers ('Scheme I', 'ISI Mark').\n"
            "3. DO NOT modify ratings (e.g. '1100 V', '500 kVA').\n"
            "4. Keep official titles in English; you may provide a translated explanation in 'title_explanation'.\n"
            f"5. If no verified standard matches, state that limitation clearly in {target_lang_name}.\n"
            "Output JSON with keys: summary, reason, title_explanation, limitations, next_steps."
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        raw_text = parts[0].get("text", "")
                        return json.loads(raw_text.strip())
        except Exception as e:
            logger.warning(f"Gemini multilingual response generation failed ({type(e).__name__}). Falling back to deterministic generator.")
        return None


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider for structured query understanding."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: float = 5.0):
        default_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        super().__init__(api_key=api_key, model=model or default_model, timeout=timeout)

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    def parse_query(self, query: str) -> Optional[StructuredRequirements]:
        if not self.is_available() or not query.strip():
            return None

        url = "https://api.openai.com/v1/chat/completions"
        system_prompt = (
            "You are a technical procurement requirements parser. Extract technical parameters from the "
            "procurement requirement into a JSON object with keys: product, capacity, cooling, installation, "
            "primary_voltage, secondary_voltage, foreign_standards (list), application. DO NOT invent IS codes."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    raw_content = choices[0].get("message", {}).get("content", "")
                    return self.validate_output(raw_content)
        except Exception as e:
            logger.warning(f"OpenAI API request failed ({type(e).__name__}). Falling back to local extractor.")

        return None

    def generate_multilingual_response(
        self,
        query: str,
        context: Dict[str, Any],
        target_language: str
    ) -> Optional[Dict[str, Any]]:
        """Generates multilingual explanation in target_language using OpenAI API."""
        if not self.is_available() or not query.strip():
            return None

        lang_names = {"en": "English", "hi": "Hindi", "ta": "Tamil"}
        target_lang_name = lang_names.get(target_language, "English")

        url = "https://api.openai.com/v1/chat/completions"
        system_prompt = (
            f"You are an expert technical compliance officer for the Bureau of Indian Standards (BIS SpecEngine).\n"
            f"Generate an authoritative procurement recommendation explanation strictly in {target_lang_name} ({target_language}).\n"
            "RULES:\n"
            f"1. Generate reasoning, explanation, summary, and next_steps strictly in {target_lang_name}.\n"
            "2. DO NOT translate official standard numbers or IS codes (e.g. 'IS 1554 (Part 1):1988'), IEC codes, ASTM codes, or QCO identifiers ('Scheme I', 'ISI Mark').\n"
            "3. DO NOT modify ratings (e.g. '1100 V', '500 kVA').\n"
            "4. Keep official titles in English; you may provide a translated explanation in 'title_explanation'.\n"
            f"5. If no verified standard matches, state that limitation clearly in {target_lang_name}.\n"
            "Output JSON with keys: summary, reason, title_explanation, limitations, next_steps."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {query}\nContext: {json.dumps(context, ensure_ascii=False)}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    raw_content = choices[0].get("message", {}).get("content", "")
                    return json.loads(raw_content.strip())
        except Exception as e:
            logger.warning(f"OpenAI multilingual response generation failed ({type(e).__name__}). Falling back to deterministic generator.")

        return None


def get_llm_provider() -> BaseLLMProvider:
    """Factory creating the configured LLM provider according to environment variables."""
    provider_type = os.getenv("LLM_PROVIDER", "").strip().lower()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", None)

    try:
        timeout = float(os.getenv("LLM_TIMEOUT", "5.0"))
    except ValueError:
        timeout = 5.0

    if provider_type == "mock":
        return MockLLMProvider(api_key=api_key or "mock", model=model, timeout=timeout)
    elif provider_type == "openai":
        return OpenAIProvider(api_key=api_key, model=model, timeout=timeout)
    elif provider_type in ("gemini", "google"):
        return GeminiProvider(api_key=api_key, model=model, timeout=timeout)

    # Auto-detection based on API key prefix or default mock fallback
    if api_key:
        if api_key.startswith("AIza") or api_key.startswith("AQ."):
            return GeminiProvider(api_key=api_key, model=model, timeout=timeout)
        elif api_key.startswith("sk-"):
            return OpenAIProvider(api_key=api_key, model=model, timeout=timeout)
        elif "mock" in api_key.lower():
            return MockLLMProvider(api_key=api_key, model=model, timeout=timeout)

    # Default to Mock provider with rule extractor if no external provider specified
    return MockLLMProvider(api_key=api_key, model=model, timeout=timeout)

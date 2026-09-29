"""
Rule-Based Deterministic Extractor for SIH26108.
Extracts structured procurement concepts without relying on external LLM APIs.
Serves as an instant, zero-latency fallback and offline parsing layer.
"""
from typing import Dict, Any, List, Optional
import re
from ai_engine.query.schema import StructuredRequirements

def parse_voltage_to_volts(v_str: Optional[str]) -> Optional[float]:
    """Converts a voltage string (e.g. '1100 V', '1.1 kV', '450/750 V', '750V') to float Volts."""
    if not v_str:
        return None
    # Check slash pairs like 450/750 V -> max is 750 V
    m_pair = re.search(r'(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)\s*(kv|v)?', v_str, re.IGNORECASE)
    if m_pair:
        val = float(m_pair.group(2))
        unit = (m_pair.group(3) or 'v').lower()
        return val * 1000.0 if unit == 'kv' else val
    m = re.search(r'(\d+(?:\.\d+)?)\s*(kv|v)', v_str, re.IGNORECASE)
    if m:
        val = float(m.group(1))
        unit = m.group(2).lower()
        return val * 1000.0 if unit == 'kv' else val
    return None

class RuleExtractor:
    """Extracts technical procurement requirements deterministically using pattern matching."""

    # Regex patterns for electrical & engineering parameters
    CAPACITY_PATTERNS = [
        r'\b(\d+(?:\.\d+)?\s*(?:kva|mva|kw|mw|hp|w|l|ltr|liters|litres|kg|ton|tons))\b',
        r'\b(\d+(?:\.\d+)?\s*sq\.?\s*mm)\b',
        r'\b(\d+(?:\.\d+)?\s*mm)\b'
    ]

    VOLTAGE_PAIR_PATTERNS = [
        r'\b(\d+(?:\.\d+)?\s*(?:kv|v))\s*(?:\/|to|\-)\s*(\d+(?:\.\d+)?\s*(?:kv|v))\b',
        r'\b(\d+(?:\.\d+)?)\s*(?:\/|to|\-)\s*(\d+(?:\.\d+)?\s*(?:kv|v))\b'
    ]

    SINGLE_VOLTAGE_PATTERNS = [
        r'\b(\d+(?:\.\d+)?\s*(?:kv|v))\b'
    ]

    INSULATION_KEYWORDS = {
        "pvc": ["pvc", "polyvinyl chloride", "पीवीसी"],
        "xlpe": ["xlpe", "crosslinked polyethylene", "cross-linked polyethylene", "एक्सएलपीई"]
    }

    DUTY_KEYWORDS = {
        "heavy_duty": ["heavy duty", "heavy-duty", "industrial", "armoured", "armored", "भारी"],
        "light_duty": ["light duty", "light-duty", "domestic", "unsheathed", "flexible cord", "lighting"]
    }

    FOREIGN_STANDARDS_PATTERN = (
        r'(?<!IS\/)(?<!IS\s\/)\b((?:ASTM\s+[A-Za-z][0-9]+(?:[\-A-Za-z0-9]+)?)|'
        r'(?:IEC\s+[0-9]+(?:\-[0-9]+)?)|(?:DIN\s+[0-9]+)|(?:BS\s+[0-9]+)|'
        r'(?:IEEE\s+[0-9]+)|(?:EN\s+[0-9]+)|(?:ISO\s+[0-9]+))\b'
    )

    COOLING_KEYWORDS = {
        "oil-cooled": ["oil-cooled", "oil cooled", "oil immersed", "onan", "onaf"],
        "dry-type": ["dry-type", "dry type", "cast resin", "an"],
        "air-cooled": ["air-cooled", "air cooled"],
        "water-cooled": ["water-cooled", "water cooled"]
    }

    INSTALLATION_KEYWORDS = {
        "outdoor": ["outdoor", "outdoors", "yard", "external", "weatherproof"],
        "indoor": ["indoor", "indoors", "substation", "internal", "panel"],
        "underground": ["underground", "buried", "trench", "direct burial"],
        "submersible": ["submersible", "underwater", "submerged", "immersion"]
    }

    PRODUCT_KEYWORDS = [
        ("distribution transformer", ["distribution transformer", "dist transformer", "step-down transformer"]),
        ("power transformer", ["power transformer"]),
        ("instrument transformer", ["current transformer", "potential transformer", "ct/pt"]),
        ("transformer", ["transformer"]),
        ("pvc insulated cable", ["pvc insulated cable", "pvc electric cable", "pvc wire"]),
        ("xlpe insulated cable", ["xlpe cable", "xlpe insulated cable"]),
        ("power cable", ["power cable", "electric cable", "wiring cable"]),
        ("control cable", ["control cable", "instrumentation cable"]),
        ("cable", ["cable", "wire", "conductor"]),
        ("deformed steel bar", ["tmt bar", "deformed steel bar", "high strength steel bar", "reinforcement steel"]),
        ("structural steel", ["structural steel", "steel section", "steel pipe"]),
        ("steel tubes", ["steel tube", "steel tubes", "tubular", "tubulars", "wrought steel"]),
        ("portland cement", ["ordinary portland cement", "opc", "portland pozzolana cement", "ppc", "cement"]),
        ("concrete aggregate", ["coarse aggregate", "fine aggregate", "aggregate for concrete", "sand"]),
        ("concrete", ["concrete", "rcc"]),
        ("submersible pump", ["submersible pump", "borewell pump"]),
        ("switchgear", ["switchgear", "circuit breaker", "mcb", "mccb"]),
        ("conduit", ["conduit pipe", "pvc conduit", "electrical conduit"]),
        ("enclosure", ["enclosure", "junction box", "distribution board", "ip code"]),
        ("water supply pipe", ["hdpe pipe", "cast iron pipe", "water pipe", "pressure pipe", "polyethylene pipe"]),
        ("fire extinguisher", ["fire extinguisher", "portable fire extinguisher"]),
        ("fire alarm", ["fire alarm", "fire detection"]),
        ("water quality testing", ["drinking water", "water sampling", "water testing", "wastewater"]),
        ("textile machinery", ["textile", "weaving", "loom", "garment machinery", "spinning machine", "weaving loom"]),
        ("machinery", ["machinery", "machine", "mechanical equipment"]),
        ("medical equipment", ["ventilator", "ppe", "surgical", "medical"]),
        ("vehicle", ["automobile", "vehicle", "truck", "tractor", "ev charger"])
    ]

    APPLICATION_KEYWORDS = [
        ("power distribution", ["power distribution", "distribution network", "grid distribution", "substation"]),
        ("building electrical wiring", ["building", "residential", "commercial", "housing", "lighting"]),
        ("structural concrete reinforcement", ["concrete", "structural", "foundation", "rcc", "civil construction"]),
        ("water supply plumbing", ["drinking water", "water supply", "plumbing", "irrigation", "drainage"]),
        ("fire safety protection", ["fire safety", "flame retardant", "fire alarm", "fire detection"])
    ]

    def extract(self, query: str) -> StructuredRequirements:
        """Deterministically extracts structured engineering requirements from natural language query."""
        if not query or not query.strip():
            return StructuredRequirements()

        clean_query = query.strip()
        lower_query = clean_query.lower()

        # 1. Product detection
        detected_product = None
        for prod_name, kw_list in self.PRODUCT_KEYWORDS:
            if any(kw in lower_query for kw in kw_list):
                detected_product = prod_name
                break

        # 2. Capacity detection
        detected_capacity = None
        for pat in self.CAPACITY_PATTERNS:
            match = re.search(pat, clean_query, re.IGNORECASE)
            if match:
                raw_cap = match.group(1).strip()
                normalized_cap = re.sub(r'(?i)\bkva\b', 'kVA', raw_cap)
                normalized_cap = re.sub(r'(?i)\bmva\b', 'MVA', normalized_cap)
                normalized_cap = re.sub(r'(?i)\bkw\b', 'kW', normalized_cap)
                normalized_cap = re.sub(r'(?i)\bmw\b', 'MW', normalized_cap)
                normalized_cap = re.sub(r'(?i)\bhp\b', 'HP', normalized_cap)
                detected_capacity = normalized_cap
                break


        # 3. Cooling detection
        detected_cooling = None
        for cool_type, kw_list in self.COOLING_KEYWORDS.items():
            if any(kw in lower_query for kw in kw_list):
                detected_cooling = cool_type
                break


        # 4. Installation detection
        detected_installation = None
        for inst_type, kw_list in self.INSTALLATION_KEYWORDS.items():
            if any(kw in lower_query for kw in kw_list):
                detected_installation = inst_type
                break

        # 5. Primary and Secondary Voltage detection
        primary_voltage = None
        secondary_voltage = None

        # Check voltage pairs like 11kV/433V or 33kV to 415V or 450/750 V
        for pat in self.VOLTAGE_PAIR_PATTERNS:
            pair_match = re.search(pat, clean_query, re.IGNORECASE)
            if pair_match:
                v1, v2 = pair_match.group(1).strip(), pair_match.group(2).strip()
                # If v1 lacks a unit (e.g. 450 in 450/750 V), inherit unit from v2
                if not re.search(r'[a-zA-Z]', v1):
                    unit_m = re.search(r'[a-zA-Z]+', v2)
                    inherited_unit = unit_m.group(0) if unit_m else 'V'
                    v1 = f"{v1} {inherited_unit}"
                primary_voltage = re.sub(r'([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)', r'\1 \2', v1).upper()
                secondary_voltage = re.sub(r'([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)', r'\1 \2', v2).upper()
                break

        if not primary_voltage:
            # Fall back to single voltage detection
            all_voltages = re.findall(r'\b(\d+(?:\.\d+)?\s*(?:kv|v))\b', clean_query, re.IGNORECASE)
            if len(all_voltages) >= 2:
                primary_voltage = re.sub(r'([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)', r'\1 \2', all_voltages[0]).upper()
                secondary_voltage = re.sub(r'([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)', r'\1 \2', all_voltages[1]).upper()
            elif len(all_voltages) == 1:
                primary_voltage = re.sub(r'([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)', r'\1 \2', all_voltages[0]).upper()

        # 6. Insulation detection (PVC, XLPE)
        detected_insulation = None
        for ins_name, kw_list in self.INSULATION_KEYWORDS.items():
            if any(kw in lower_query for kw in kw_list):
                detected_insulation = ins_name
                break

        # 7. Duty detection (heavy duty, light duty)
        detected_duty = None
        for duty_name, kw_list in self.DUTY_KEYWORDS.items():
            if any(kw in lower_query for kw in kw_list):
                detected_duty = duty_name
                break

        # Numerical voltage parsing in Volts
        rated_volts = None
        if primary_voltage:
            rated_volts = parse_voltage_to_volts(primary_voltage)
            if secondary_voltage:
                sec_v = parse_voltage_to_volts(secondary_voltage)
                if sec_v and ("cable" in (detected_product or "") or "wire" in (detected_product or "")):
                    rated_volts = max(rated_volts or 0.0, sec_v)

        # 8. Foreign Standards detection (IEC, ASTM, BS, DIN, ISO, IEEE)
        foreign_standards = []
        for match in re.finditer(self.FOREIGN_STANDARDS_PATTERN, clean_query, re.IGNORECASE):
            raw_match = match.group(1).strip()
            # Normalize spacing (e.g., IEC 60076, ASTM A36)
            normalized = re.sub(r'\s+', ' ', raw_match).strip().upper()
            if normalized not in foreign_standards:
                foreign_standards.append(normalized)

        # 9. Application detection
        detected_application = None
        for app_name, kw_list in self.APPLICATION_KEYWORDS:
            if any(kw in lower_query for kw in kw_list):
                detected_application = app_name
                break

        # Default fallback application if product is transformer
        if not detected_application and detected_product and "transformer" in detected_product:
            detected_application = "power distribution"

        additional_params = {
            "insulation_material": detected_insulation,
            "duty_type": detected_duty,
            "rated_voltage_volts": rated_volts,
            "voltage_raw": primary_voltage,
            "voltage_secondary_raw": secondary_voltage
        }

        return StructuredRequirements(
            product=detected_product,
            capacity=detected_capacity,
            cooling=detected_cooling,
            installation=detected_installation,
            primary_voltage=primary_voltage,
            secondary_voltage=secondary_voltage,
            foreign_standards=foreign_standards,
            application=detected_application,
            additional_parameters=additional_params
        )

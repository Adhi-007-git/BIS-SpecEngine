"""
Structured Requirements Schema for SIH26108 LLM Query Understanding Layer.
Provides typed validation for procurement technical specifications.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class StructuredRequirements(BaseModel):
    """Structured representation of procurement requirements extracted by the LLM or rule extractor."""
    product: Optional[str] = Field(default=None, description="Identified product or equipment type")
    capacity: Optional[str] = Field(default=None, description="Power, volume, flow or physical capacity rating (e.g., 500 kVA)")
    cooling: Optional[str] = Field(default=None, description="Cooling mechanism (e.g., oil-cooled, dry-type, air-cooled)")
    installation: Optional[str] = Field(default=None, description="Installation environment (e.g., outdoor, indoor, underground)")
    primary_voltage: Optional[str] = Field(default=None, description="Primary or input voltage specification (e.g., 11 kV)")
    secondary_voltage: Optional[str] = Field(default=None, description="Secondary or output voltage specification (e.g., 433 V)")
    foreign_standards: List[str] = Field(default_factory=list, description="Mentioned non-Indian or international standards (e.g., IEC 60076, ASTM A36)")
    application: Optional[str] = Field(default=None, description="Intended procurement application or domain (e.g., power distribution)")
    additional_parameters: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary additional engineering parameters extracted from query")

    def to_dict(self) -> Dict[str, Any]:
        """Backward-compatible dictionary serialization across Pydantic v1 and v2."""
        if hasattr(self, "model_dump"):
            return self.model_dump()
        return self.dict()

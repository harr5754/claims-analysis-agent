from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ClaimType(str, Enum):
    DELAY = "delay"
    VARIATION = "variation"
    DEFECT = "defect"
    PAYMENT = "payment"
    OTHER = "other"

class ClaimStrength(str, Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"
    INSUFFICIENT = "insufficient_information"

class ClaimIssue(BaseModel):
    issue_id: str
    description: str
    claim_type: ClaimType
    our_position: str
    opposing_position: Optional[str] = None
    supporting_evidence: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    strength_score: int = Field(ge=0, le=100)
    notes: Optional[str] = None

class EntitlementAssessment(BaseModel):
    overall_rating: ClaimStrength
    score: int = Field(ge=0, le=100)
    contractual_basis: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    preliminary_conclusion: str

class QuantumAssessment(BaseModel):
    stated_amount: Optional[str] = None
    assessment: str
    confidence: ClaimStrength
    supporting_info_present: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)

class ScheduleImpactAssessment(BaseModel):
    stated_delay: Optional[str] = None
    assessment: str
    confidence: ClaimStrength
    supporting_info_present: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)

class ClaimAnalysis(BaseModel):
    claim_id: str
    project_name: Optional[str] = None
    analysis_date: datetime = Field(default_factory=datetime.now)
    summary: str
    overall_strength: ClaimStrength
    overall_score: int = Field(ge=0, le=100)
    key_issues: List[ClaimIssue] = Field(default_factory=list)
    entitlement: Optional[EntitlementAssessment] = None
    quantum: Optional[QuantumAssessment] = None
    schedule_impact: Optional[ScheduleImpactAssessment] = None
    recommended_actions: List[str] = Field(default_factory=list)
    draft_response: Optional[str] = None
    risk_flags: List[str] = Field(default_factory=list)
    source_documents: List[str] = Field(default_factory=list)
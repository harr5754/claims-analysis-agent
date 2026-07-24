from typing import List, Optional
from pathlib import Path
from datetime import datetime
from groq import Groq

from models.claims import (
    ClaimAnalysis, ClaimIssue, ClaimType, ClaimStrength,
    EntitlementAssessment, QuantumAssessment, ScheduleImpactAssessment
)

class ClaimsAnalysisAgent:
    """
    Claims Analysis Agent with Entitlement, Quantum, and Schedule Impact assessments.
    """

    def __init__(self, groq_api_key: str = None, knowledge_base_path: Optional[str] = None):
        self.client = Groq(api_key=groq_api_key) if groq_api_key else None
        self.knowledge_base_path = knowledge_base_path
        self.history: List[ClaimAnalysis] = []

    def analyze_email_chain(self, email_texts: List[str], claim_id: str = None, context: str = "") -> ClaimAnalysis:
        if not claim_id:
            claim_id = f"CLAIM-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        combined = "\n\n--- EMAIL ---\n\n".join(email_texts)
        return self._analyze(combined, claim_id, context, source="email_chain")

    def analyze_legal_filing(self, text: str, filing_type: str = "unknown", context: str = "") -> ClaimAnalysis:
        if not filing_type or filing_type == "unknown":
            filing_type = "legal_filing"
        claim_id = f"FILING-{filing_type.upper()}-{datetime.now().strftime('%Y%m%d')}"
        return self._analyze(text, claim_id, context, source=filing_type)

    def _analyze(self, text: str, claim_id: str, context: str, source: str) -> ClaimAnalysis:
        key_issues = self._extract_issues(text, context)
        entitlement = self._assess_entitlement(text, context)
        quantum = self._assess_quantum(text, context)
        schedule = self._assess_schedule_impact(text, context)

        overall_score = entitlement.score if entitlement else 50
        overall_strength = entitlement.overall_rating if entitlement else ClaimStrength.MODERATE

        analysis = ClaimAnalysis(
            claim_id=claim_id,
            summary=self._generate_summary(text, context),
            overall_strength=overall_strength,
            overall_score=overall_score,
            key_issues=key_issues,
            entitlement=entitlement,
            quantum=quantum,
            schedule_impact=schedule,
            recommended_actions=self._recommend_actions(key_issues, entitlement, quantum, schedule),
            draft_response=self._draft_response(text, context),
            risk_flags=self._identify_risks(key_issues, entitlement),
            source_documents=[source]
        )

        self.history.append(analysis)
        return analysis

    def _generate_summary(self, text: str, context: str = "") -> str:
        prompt = f"""
You are an experienced construction claims specialist.

Write a clean, factual summary of the claim notification below.

STRICT RULES:
- Only use information explicitly stated in the letter.
- Do not invent facts, amounts, dates, or causes.
- Structure the summary with Date, From, To, Subject, and Key Points when possible.
- Keep the tone professional and neutral.

Project Context:
{context}

Claim Letter:
{text[:14000]}
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a precise construction claims specialist. Never invent facts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=700
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Unable to generate summary. Error: {str(e)}"

    def _assess_entitlement(self, text: str, context: str) -> EntitlementAssessment:
        prompt = f"""
You are an experienced construction claims specialist.

Perform a preliminary Entitlement Assessment.

Project Context:
{context}

STRICT RULES:
- Only use information present in the claim letter and context.
- Do not invent facts or contractual provisions.
- Be conservative.

Provide:
1. Overall Rating: Strong / Moderate / Weak / Insufficient Information
2. Score: 0-100
3. Contractual Basis
4. Strengths (bullet points)
5. Weaknesses (bullet points)
6. Missing Information
7. Preliminary Conclusion

Claim Letter:
{text[:12000]}
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a precise and conservative construction claims specialist. Never invent facts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.15,
                max_tokens=900
            )
            content = response.choices[0].message.content.strip()

            rating = ClaimStrength.MODERATE
            score = 55
            if "Strong" in content:
                rating = ClaimStrength.STRONG
                score = 75
            elif "Weak" in content:
                rating = ClaimStrength.WEAK
                score = 35
            elif "Insufficient" in content:
                rating = ClaimStrength.INSUFFICIENT
                score = 25

            return EntitlementAssessment(
                overall_rating=rating,
                score=score,
                contractual_basis="See detailed analysis",
                strengths=["See detailed analysis"],
                weaknesses=["See detailed analysis"],
                missing_information=["Full contract clauses", "Supporting records"],
                preliminary_conclusion=content
            )
        except Exception:
            return EntitlementAssessment(
                overall_rating=ClaimStrength.INSUFFICIENT,
                score=30,
                contractual_basis="Unable to determine",
                strengths=[],
                weaknesses=["Analysis failed"],
                missing_information=["Full claim letter and contract context required"],
                preliminary_conclusion="Unable to complete entitlement assessment."
            )

    def _assess_quantum(self, text: str, context: str) -> QuantumAssessment:
        prompt = f"""
You are an experienced construction claims specialist focusing on quantum (cost) assessment.

Analyze the claim letter for any stated or implied cost impact.

Project Context:
{context}

STRICT RULES:
- Only use information explicitly stated in the letter.
- Do not invent amounts or cost figures.
- Clearly state when no quantum information is provided.

Provide:
1. Stated Amount (if any)
2. Assessment of the quantum claim
3. Confidence level (Strong / Moderate / Weak / Insufficient Information)
4. Supporting information present
5. Missing information
6. Recommended next steps

Claim Letter:
{text[:12000]}
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a precise construction claims specialist. Never invent cost figures."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.15,
                max_tokens=700
            )
            content = response.choices[0].message.content.strip()

            confidence = ClaimStrength.INSUFFICIENT
            if "Strong" in content:
                confidence = ClaimStrength.STRONG
            elif "Moderate" in content:
                confidence = ClaimStrength.MODERATE
            elif "Weak" in content:
                confidence = ClaimStrength.WEAK

            return QuantumAssessment(
                stated_amount=None,
                assessment=content,
                confidence=confidence,
                supporting_info_present=[],
                missing_information=["Detailed cost breakdown", "Supporting invoices / timesheets"],
                recommended_next_steps=["Request detailed cost records from claimant"]
            )
        except Exception:
            return QuantumAssessment(
                stated_amount=None,
                assessment="Unable to assess quantum.",
                confidence=ClaimStrength.INSUFFICIENT,
                supporting_info_present=[],
                missing_information=["Full claim letter and cost data required"],
                recommended_next_steps=["Obtain supporting cost documentation"]
            )

    def _assess_schedule_impact(self, text: str, context: str) -> ScheduleImpactAssessment:
        prompt = f"""
You are an experienced construction claims specialist focusing on schedule impact.

Analyze the claim letter for any stated or implied delay / schedule impact.

Project Context:
{context}

STRICT RULES:
- Only use information explicitly stated in the letter.
- Do not invent delay periods or critical path analysis.
- Clearly state when no schedule information is provided.

Provide:
1. Stated Delay (if any)
2. Assessment of the schedule impact
3. Confidence level (Strong / Moderate / Weak / Insufficient Information)
4. Supporting information present
5. Missing information
6. Recommended next steps

Claim Letter:
{text[:12000]}
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a precise construction claims specialist. Never invent schedule data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.15,
                max_tokens=700
            )
            content = response.choices[0].message.content.strip()

            confidence = ClaimStrength.INSUFFICIENT
            if "Strong" in content:
                confidence = ClaimStrength.STRONG
            elif "Moderate" in content:
                confidence = ClaimStrength.MODERATE
            elif "Weak" in content:
                confidence = ClaimStrength.WEAK

            return ScheduleImpactAssessment(
                stated_delay=None,
                assessment=content,
                confidence=confidence,
                supporting_info_present=[],
                missing_information=["Updated baseline schedule", "Impacted activity analysis"],
                recommended_next_steps=["Request schedule impact analysis from claimant"]
            )
        except Exception:
            return ScheduleImpactAssessment(
                stated_delay=None,
                assessment="Unable to assess schedule impact.",
                confidence=ClaimStrength.INSUFFICIENT,
                supporting_info_present=[],
                missing_information=["Full claim letter and schedule data required"],
                recommended_next_steps=["Obtain supporting schedule documentation"]
            )

    def _extract_issues(self, text: str, context: str = "") -> List[ClaimIssue]:
        text_lower = text.lower()
        issues = []

        if any(word in text_lower for word in ["strike", "customs", "work slow"]):
            issues.append(ClaimIssue(
                issue_id="ISSUE-1",
                description="Delays caused by customs officials strikes / work slow-downs",
                claim_type=ClaimType.DELAY,
                our_position="Potential excusable delay – further assessment required",
                strength_score=65,
                notes="Keyword detection – verify against full letter"
            ))
        elif "delay" in text_lower:
            issues.append(ClaimIssue(
                issue_id="ISSUE-1",
                description="Delay-related claim",
                claim_type=ClaimType.DELAY,
                our_position="Requires further contractual review",
                strength_score=50
            ))
        else:
            issues.append(ClaimIssue(
                issue_id="ISSUE-1",
                description="General claim review required",
                claim_type=ClaimType.OTHER,
                our_position="Further review needed",
                strength_score=40
            ))
        return issues

    def _draft_response(self, text: str, context: str = "") -> str:
        prompt = f"""
You are an experienced construction contracts manager.

Write a professional draft response to the claim letter below.

STRICT RULES:
- Base the response only on the information in the claim letter.
- Do not invent facts.
- Acknowledge receipt.
- Request supporting documentation where appropriate.
- Keep the tone professional and firm.

Project Context:
{context}

Claim Letter:
{text[:12000]}
"""
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a precise construction contracts specialist. Never invent facts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Unable to generate a reliable draft response."

    def _recommend_actions(self, issues, entitlement, quantum, schedule) -> List[str]:
        actions = [
            "Review all supporting evidence carefully",
            "Confirm the applicable contract clause(s)",
            "Assess schedule and cost impact"
        ]
        if entitlement and entitlement.overall_rating in [ClaimStrength.WEAK, ClaimStrength.INSUFFICIENT]:
            actions.append("Request additional documentation from the claimant")
        if quantum and quantum.confidence == ClaimStrength.INSUFFICIENT:
            actions.append("Request detailed cost breakdown and supporting records")
        if schedule and schedule.confidence == ClaimStrength.INSUFFICIENT:
            actions.append("Request schedule impact analysis and supporting programme")
        return actions

    def _identify_risks(self, issues, entitlement) -> List[str]:
        risks = []
        if entitlement and entitlement.score < 50:
            risks.append("Low preliminary entitlement score – further investigation required")
        for issue in issues:
            if issue.strength_score < 50:
                risks.append(f"Low confidence on: {issue.description}")
        return risks

    def save_analysis(self, analysis: ClaimAnalysis, output_path: str):
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(analysis.model_dump_json(indent=2))
        print(f"Analysis saved to {path}")
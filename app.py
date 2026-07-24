import streamlit as st
import os
from datetime import datetime
from pathlib import Path

from agents.claims_agent import ClaimsAnalysisAgent
from models.claims import ClaimAnalysis

st.set_page_config(
    page_title="Claims Analysis Agent",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Claims Analysis Agent")
st.caption("Construction Claims – Summary • Entitlement • Quantum • Schedule Impact")

# Sidebar
with st.sidebar:
    st.header("Settings")
    
    # Try to load the key from Streamlit Secrets
    secret_key = None
    try:
        secret_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        secret_key = None
    
    if secret_key:
        # Secret exists – use it and hide the input box
        groq_key = secret_key
        st.success("API key loaded from Secrets")
    else:
        # No secret found – show the input box
        groq_key = st.text_input(
            "Groq API Key",
            type="password",
            help="Enter your Groq API key"
        )

# Project Context
st.subheader("1. Project Context")
col1, col2 = st.columns(2)

with col1:
    project_type = st.text_input("Project Type", placeholder="EPC, renovation, fabrication, etc.")
    location = st.text_input("Location", placeholder="São Paulo, Brazil")
    your_role = st.selectbox("Your Role", ["Claimant", "Respondent", "Neutral"])

with col2:
    dispute_stage = st.selectbox("Dispute Stage", ["Pre-claim", "Negotiation", "Arbitration", "Litigation"])
    contract_type = st.text_input("Contract Type", placeholder="FAR, FIDIC, custom, etc.")
    contract_clause = st.text_input("Known Contract Clause(s)", placeholder="e.g. Clause F.7 / FAR 52.249-10")

additional_context = st.text_area(
    "Additional Context",
    height=80,
    placeholder="Any other relevant background..."
)

# Document Input
st.markdown("---")
st.subheader("2. Claim Document")

tab1, tab2 = st.tabs(["📧 Email / Text", "📄 Upload Document"])

email_text = ""
filing_text = ""

with tab1:
    email_text = st.text_area(
        "Paste the claim letter or email chain here:",
        height=280,
        placeholder="Paste the full text of the claim notification..."
    )

with tab2:
    uploaded_file = st.file_uploader(
        "Upload Word (.docx) or Text file",
        type=["docx", "txt"]
    )
    filing_text = st.text_area(
        "Or paste the document content:",
        height=200
    )

# Analyze Button
if st.button("🔍 Analyze Claim", type="primary", use_container_width=True):
    if not groq_key:
        st.error("Please enter your Groq API key in the sidebar.")
        st.stop()

    # Build context
    context = f"""
Project Type: {project_type}
Location: {location}
Your Role: {your_role}
Dispute Stage: {dispute_stage}
Contract Type: {contract_type}
Applicable Clause: {contract_clause}
Additional Context: {additional_context}
"""

    # Collect text
    texts = []
    if email_text.strip():
        texts.append(email_text.strip())
    if filing_text.strip():
        texts.append(filing_text.strip())

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".docx"):
                from docx import Document
                doc = Document(uploaded_file)
                content = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                texts.append(content)
            else:
                content = uploaded_file.read().decode("utf-8", errors="ignore")
                texts.append(content)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

    if not texts:
        st.warning("Please provide a claim letter or upload a document.")
        st.stop()

    combined = "\n\n--- DOCUMENT ---\n\n".join(texts)

    with st.spinner("Analyzing claim... this may take 20–40 seconds"):
        try:
            agent = ClaimsAnalysisAgent(groq_api_key=groq_key)

            if email_text.strip() and not uploaded_file:
                analysis = agent.analyze_email_chain(texts, context=context)
            else:
                analysis = agent.analyze_legal_filing(combined, context=context)

            # ==================== RESULTS ====================
            st.success("Analysis complete")

            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Score", f"{analysis.overall_score}/100")
            with col2:
                st.metric("Strength", analysis.overall_strength.value.upper().replace("_", " "))
            with col3:
                st.metric("Key Issues", len(analysis.key_issues))

            # Summary
            st.markdown("### Summary")
            st.write(analysis.summary)

            # Entitlement Assessment
            if analysis.entitlement:
                st.markdown("### Entitlement Assessment")
                ent = analysis.entitlement
                st.write(f"**Rating:** {ent.overall_rating.value.upper().replace('_', ' ')} ({ent.score}/100)")
                st.write(f"**Contractual Basis:** {ent.contractual_basis}")

                if ent.strengths:
                    st.markdown("**Strengths**")
                    for s in ent.strengths:
                        st.write(f"- {s}")

                if ent.weaknesses:
                    st.markdown("**Weaknesses**")
                    for w in ent.weaknesses:
                        st.write(f"- {w}")

                if ent.missing_information:
                    st.markdown("**Missing Information**")
                    for m in ent.missing_information:
                        st.write(f"- {m}")

                st.markdown("**Preliminary Conclusion**")
                st.info(ent.preliminary_conclusion)

            # Quantum Assessment
            if analysis.quantum:
                st.markdown("### Quantum Assessment")
                q = analysis.quantum
                st.write(f"**Confidence:** {q.confidence.value.upper().replace('_', ' ')}")
                if q.stated_amount:
                    st.write(f"**Stated Amount:** {q.stated_amount}")
                st.write(q.assessment)

                if q.missing_information:
                    st.markdown("**Missing Information**")
                    for m in q.missing_information:
                        st.write(f"- {m}")

                if q.recommended_next_steps:
                    st.markdown("**Recommended Next Steps**")
                    for step in q.recommended_next_steps:
                        st.write(f"- {step}")

            # Schedule Impact Assessment
            if analysis.schedule_impact:
                st.markdown("### Schedule Impact Assessment")
                s = analysis.schedule_impact
                st.write(f"**Confidence:** {s.confidence.value.upper().replace('_', ' ')}")
                if s.stated_delay:
                    st.write(f"**Stated Delay:** {s.stated_delay}")
                st.write(s.assessment)

                if s.missing_information:
                    st.markdown("**Missing Information**")
                    for m in s.missing_information:
                        st.write(f"- {m}")

                if s.recommended_next_steps:
                    st.markdown("**Recommended Next Steps**")
                    for step in s.recommended_next_steps:
                        st.write(f"- {step}")

            # Key Issues
            st.markdown("### Key Issues")
            for issue in analysis.key_issues:
                with st.expander(f"{issue.issue_id}: {issue.description} (Score: {issue.strength_score})"):
                    st.write(f"**Type:** {issue.claim_type.value}")
                    st.write(f"**Position:** {issue.our_position}")
                    if issue.notes:
                        st.write(f"**Notes:** {issue.notes}")

            # Recommended Actions
            st.markdown("### Recommended Actions")
            for action in analysis.recommended_actions:
                st.write(f"- {action}")

            # Risk Flags
            if analysis.risk_flags:
                st.markdown("### Risk Flags")
                for risk in analysis.risk_flags:
                    st.warning(risk)

            # Draft Response
            st.markdown("### Draft Response")
            st.text_area("Draft Response", analysis.draft_response or "No draft generated", height=280)

            # Save
            if st.button("💾 Save Analysis as JSON"):
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                output_path = output_dir / f"analysis_{analysis.claim_id}.json"
                agent.save_analysis(analysis, str(output_path))
                st.success(f"Saved to {output_path}")

        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            st.exception(e)

st.markdown("---")
st.caption("Claims Analysis Agent – Construction Claims MVP")
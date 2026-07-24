from agents.claims_agent import ClaimsAnalysisAgent

# Initialize the agent
agent = ClaimsAnalysisAgent()

# Example email chain (you can replace with real emails)
emails = [
    "Subject: Moisture Content Issue\n\nWe are experiencing significantly lower production due to the moisture content being higher than the 5% specified in the design criteria.",
    "Subject: Re: Moisture Content Issue\n\nPlease review the original design criteria and any change notices. This is causing major delays and cost overruns."
]

# Analyze the claim
analysis = agent.analyze_email_chain(emails, claim_id="TEST-001")

print("\n=== CLAIM ANALYSIS RESULT ===")
print(analysis.model_dump_json(indent=2))

# Save to file
agent.save_analysis(analysis, "output/test_analysis.json")
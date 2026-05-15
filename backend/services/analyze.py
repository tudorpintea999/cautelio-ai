import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

_SYSTEM_PROMPT = """You are a contract compliance analyst specializing in freelance and SMB agreements. Identify clauses that are dangerous, one-sided, or that a non-lawyer would miss.

Flag these clause types:
- ip_assignment: IP transfer, work-for-hire, assignment of inventions
- non_compete: non-compete, non-solicitation, exclusivity
- auto_renew: automatic renewal with short or unclear cancellation windows
- arbitration: mandatory arbitration, class action waivers
- liability: one-sided liability caps, consequential damages exclusions
- indemnity: broad indemnification obligations
- termination: one-sided termination rights, clawback provisions
- payment: late payment penalties, clawback, offset rights
- modification: unilateral right to change terms
- other: any other high-risk clause

Return ONLY a valid JSON object with this exact structure — no markdown, no explanation:
{
  "overall_risk": "high|medium|low",
  "summary": "2-3 sentences on the contract's risk profile in plain English",
  "clauses": [
    {
      "text": "exact or near-exact quote from the contract, max 150 characters",
      "type": "one of the types listed above",
      "risk_level": "high|medium|low",
      "explanation": "one sentence plain English explanation of the risk",
      "negotiable": true or false,
      "negotiation_tip": "specific language to request instead, or null if not negotiable"
    }
  ],
  "freelancer_flags": [
    {
      "issue": "brief description of the freelancer-specific concern",
      "clause_text": "relevant quote from the contract"
    }
  ]
}"""


async def analyze_contract(text: str, freelancer_mode: bool) -> dict:
    prefix = (
        "FREELANCER MODE ACTIVE: Prioritize and flag all IP assignment, work-for-hire, "
        "portfolio rights, and ownership clauses prominently in freelancer_flags.\n\n"
        if freelancer_mode
        else ""
    )

    message = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"{prefix}Contract text:\n\n{text[:40000]}",
            }
        ],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if Claude wraps the JSON
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return json.loads(raw)

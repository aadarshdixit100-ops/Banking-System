"""GenAI-powered transaction analysis.

This complements the deterministic rule-based fraud checks in
fraud_detection.py: rather than fixed thresholds, it asks Claude to read a
customer's recent transaction pattern and produce a short plain-English risk
narrative plus a risk rating. It's meant as an analyst's second opinion, not
a replacement for the rule engine.
"""

import json

from anthropic import AsyncAnthropic

from app.core.config import settings

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


SYSTEM_PROMPT = (
    "You are a banking fraud analyst assistant. You will be given a JSON list of "
    "recent transactions for a single account. Assess whether the pattern looks "
    "risky (structuring, rapid drain, unusual amounts, odd timing, round-tripping "
    "between accounts, etc). Respond ONLY with compact JSON, no prose outside it: "
    '{"risk_level": "low|medium|high", "summary": "2-3 sentence explanation", '
    '"signals": ["short phrase", ...]}'
)


async def analyze_account_activity(account_no: int, transactions: list[dict]) -> dict:
    if not settings.anthropic_api_key:
        return {
            "risk_level": "unknown",
            "summary": "GenAI analysis is not configured. Set ANTHROPIC_API_KEY to enable it.",
            "signals": [],
        }

    payload = [
        {
            "type": t["type"],
            "amount": t["amount"],
            "balance_after": t["balance_after"],
            "counterparty_account_no": t.get("counterparty_account_no"),
            "created_at": str(t["created_at"]),
        }
        for t in transactions
    ]

    client = _get_client()
    response = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Account {account_no} recent transactions:\n{json.dumps(payload, default=str)}",
            }
        ],
    )

    text = "".join(block.text for block in response.content if block.type == "text").strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"risk_level": "unknown", "summary": text, "signals": []}

    return parsed

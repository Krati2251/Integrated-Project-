"""
Ticket analysis using LangChain + Groq (Llama 3.1 70B).

OPTIMISATION:  Analysis + draft reply are produced in a **single** LLM call
so each email costs only 1 API request (Groq free tier = 30 req/min).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root BEFORE any other imports
_project_root = Path(__file__).parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)

import hashlib
import re
from functools import lru_cache

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from schemas import TicketAnalysis, TicketAnalysisWithDraft

# ────────────────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

_LLM_AVAILABLE = bool(GROQ_API_KEY)

# ────────────────────── LLM Setup ──────────────────────

if _LLM_AVAILABLE:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=GROQ_API_KEY,
        temperature=0,            # deterministic for classification
        max_tokens=2048,          # enough for analysis + full draft
        request_timeout=60,
    )
    # Structured output — forces the LLM to return valid JSON matching
    # our Pydantic schema (analysis + draft combined).
    structured_llm = llm.with_structured_output(TicketAnalysisWithDraft)
    # Also keep an analysis-only structured LLM for the /analyze endpoint.
    structured_llm_analysis_only = llm.with_structured_output(TicketAnalysis)
else:
    llm = None
    structured_llm = None
    structured_llm_analysis_only = None

# ────────────────────── Combined Prompt ──────────────────────
# One prompt that asks for BOTH analysis AND draft reply in a single call.

COMBINED_SYSTEM_PROMPT = """\
You are a senior financial support triage agent AND a professional customer \
support writer. You will analyse an incoming customer email and produce:

A) STRUCTURED TRIAGE ANALYSIS
B) A PERSONALISED DRAFT REPLY

═══ PART A — ANALYSIS RULES ═══

SENTIMENT — Exactly one of: Positive, Negative, Neutral, Urgent
  • Positive — satisfied or sending thanks
  • Negative — frustrated, angry, or dissatisfied
  • Neutral  — informational or routine enquiry
  • Urgent   — immediate danger, fraud, or threats

INTENT — Short phrase (5-10 words) describing what the customer wants.

ENTITIES — Extract (set null if not found):
  • customer_name  — sender's full name
  • transaction_id — any transaction/reference ID (e.g. TXN-12345)
  • amount         — monetary amount (e.g. "$500.00")

PRIORITY (CRITICAL — follow these rules exactly):
  • High   — ANY of these: fraud, theft, unauthorised transactions, account
              compromise, security breach, stolen card, payment failed but money
              deducted, large failed transfers, salary/rent payment failures,
              refund not received/credited, account lockout with urgent need,
              billing error (charged after cancellation), critical transaction
              failures. If money is lost, stuck, or at risk → ALWAYS High.
  • Medium — disputes without money loss, app/feature malfunctions, KYC/document
              issues, non-critical payment questions, chargeback requests where
              money is safe.
  • Low    — general enquiries, information requests, feedback, feature requests,
              status checks, statement requests, thank-you notes.

CATEGORY:
  • Fraud         — fraud, theft, unauthorised access, suspicious activity,
                     security breach, stolen card, identity theft
  • Payment Issue — billing errors, refund requests, payment failures, disputes,
                     failed transfers, subscription charges, account lockout
  • General       — all other enquiries

SUMMARY — Concise 1-2 sentence summary for the support agent.

═══ PART B — DRAFT REPLY RULES ═══

Write a professional, empathetic plain-text email reply (80-150 words).

1. GREETING — "Dear <customer_name>," (or "Dear Valued Customer," if unknown).

2. TONE BY CATEGORY:
   • Fraud:
     – Express urgent concern and empathy
     – Assure account security is top priority
     – State fraud/security team is investigating
     – Advise "We have temporarily secured your account"
     – Provide hotline: 1-800-FRAUD-HELP
   • Payment Issue:
     – Acknowledge inconvenience with empathy
     – Payment/billing team is reviewing
     – Reference number: [REF-XXXXXX]
     – Resolution: 2-3 business days
   • General:
     – Polite, warm, professional
     – Helpful and informative
     – Offer further assistance

3. CLOSING — End with:
   "Best regards,
   Finance Support Team
   finance-support@company.com"

4. Do NOT use markdown. Plain text only.

Return ALL fields in a single JSON response.
"""

combined_prompt = ChatPromptTemplate.from_messages([
    ("system", COMBINED_SYSTEM_PROMPT),
    ("human", "Analyse and draft a reply for the following customer email:\n\n{email_body}"),
])

# Analysis-only prompt (for the /analyze endpoint that doesn't need a draft)
ANALYSIS_ONLY_SYSTEM_PROMPT = """\
You are a senior financial support triage agent. Analyse the incoming \
customer email and return a structured JSON report.

SENTIMENT — Exactly one of: Positive, Negative, Neutral, Urgent
INTENT — Short phrase (5-10 words) describing what the customer wants.
ENTITIES — Extract customer_name, transaction_id, amount (null if not found).
PRIORITY (follow strictly):
  High — fraud, security breach, payment failed + money deducted, refund not
         received, account lockout, billing error, any situation where money
         is lost/stuck/at risk.
  Medium — disputes (money safe), app bugs, KYC issues.
  Low — general questions, feedback, status checks, statements.
CATEGORY — Fraud, Payment Issue, or General.
SUMMARY — 1-2 sentence summary.
"""

analysis_only_prompt = ChatPromptTemplate.from_messages([
    ("system", ANALYSIS_ONLY_SYSTEM_PROMPT),
    ("human", "Analyse the following customer email:\n\n{email_body}"),
])

# ────────────────────── Chains ──────────────────────

combined_chain = (combined_prompt | structured_llm) if structured_llm is not None else None
analysis_only_chain = (analysis_only_prompt | structured_llm_analysis_only) if structured_llm_analysis_only is not None else None

# ────────────────────── In-memory cache ──────────────────────
# Prevents re-analysing the exact same email body within one server session.
_cache: dict[str, TicketAnalysisWithDraft] = {}


def _cache_key(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _local_analysis(email_body: str) -> TicketAnalysis:
    """Heuristic analysis fallback when LLM credentials are unavailable."""
    txt = email_body.strip()
    lower = txt.lower()

    fraud_words = [
        "fraud", "unauthorized", "unauthorised", "stolen", "hacked",
        "suspicious", "compromise", "scam", "identity theft",
    ]
    payment_words = [
        "payment", "charged", "charge", "refund", "transfer", "billing",
        "invoice", "card", "debit", "credit", "failed transaction",
    ]
    urgent_words = [
        "urgent", "immediately", "asap", "right now", "freeze", "blocked",
    ]
    negative_words = [
        "angry", "frustrated", "upset", "disappointed", "worried", "problem",
    ]

    def _has_any(words: list[str]) -> bool:
        return any(w in lower for w in words)

    is_fraud = _has_any(fraud_words)
    is_payment = _has_any(payment_words)
    is_urgent = _has_any(urgent_words)
    is_negative = _has_any(negative_words)

    if is_fraud:
        category = "Fraud"
        priority = "High"
        intent = "Report suspected unauthorized activity"
    elif is_payment:
        category = "Payment Issue"
        priority = "Medium"
        intent = "Resolve payment or billing problem"
    else:
        category = "General"
        priority = "Low"
        intent = "General support request"

    if is_urgent or is_fraud:
        sentiment = "Urgent"
    elif is_negative:
        sentiment = "Negative"
    elif any(w in lower for w in ["thanks", "thank you", "great", "appreciate"]):
        sentiment = "Positive"
    else:
        sentiment = "Neutral"

    name_match = re.search(r"(?:my name is|i am|this is)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})", txt)
    txn_match = re.search(r"\b(?:txn|tx|ref|reference)[-\s:]*([A-Za-z0-9-]{4,})\b", txt, flags=re.IGNORECASE)
    amt_match = re.search(r"(?:\$|USD\s?)\s?([\d,]+(?:\.\d{1,2})?)", txt, flags=re.IGNORECASE)

    customer_name = name_match.group(1).strip() if name_match else None
    transaction_id = txn_match.group(1).strip() if txn_match else None
    amount = f"${amt_match.group(1)}" if amt_match else None

    summary = f"{category} email classified with {priority} priority via local fallback analyzer."

    return TicketAnalysis(
        sentiment=sentiment,
        intent=intent,
        entities={
            "customer_name": customer_name,
            "transaction_id": transaction_id,
            "amount": amount,
        },
        priority=priority,
        category=category,
        summary=summary,
    )


# ────────────────────── Public API ──────────────────────

def analyze_and_draft(email_body: str) -> TicketAnalysisWithDraft:
    """
    Analyse a customer email AND generate a draft reply in **one** LLM call.

    Returns:
        TicketAnalysisWithDraft — contains all analysis fields + draft_response.
    """
    if not email_body or not email_body.strip():
        raise ValueError("email_body cannot be empty.")

    clean = email_body.strip()
    key = _cache_key(clean)

    if key in _cache:
        return _cache[key]

    if combined_chain is not None:
        result: TicketAnalysisWithDraft = combined_chain.invoke({"email_body": clean})
    else:
        analysis = _local_analysis(clean)
        result = TicketAnalysisWithDraft(
            sentiment=analysis.sentiment,
            intent=analysis.intent,
            entities=analysis.entities,
            priority=analysis.priority,
            category=analysis.category,
            summary=analysis.summary,
            draft_response=generate_draft_response(analysis),
        )
    _cache[key] = result
    return result


def analyze_ticket(email_body: str) -> TicketAnalysis:
    """
    Analyse-only (no draft). Used by the /analyze endpoint.

    For endpoints that also need a draft, prefer analyze_and_draft() to
    save an API call.
    """
    if not email_body or not email_body.strip():
        raise ValueError("email_body cannot be empty.")

    clean = email_body.strip()
    key = _cache_key(clean)

    # If we already have a combined result cached, reuse the analysis part
    if key in _cache:
        cached = _cache[key]
        return TicketAnalysis(
            sentiment=cached.sentiment,
            intent=cached.intent,
            entities=cached.entities,
            priority=cached.priority,
            category=cached.category,
            summary=cached.summary,
        )

    if analysis_only_chain is not None:
        return analysis_only_chain.invoke({"email_body": clean})

    return _local_analysis(clean)


def generate_draft_response(analysis: TicketAnalysis) -> str:
    """
    Backward-compatible wrapper. If the analysis came from analyze_and_draft(),
    return its draft. Otherwise fall back to a simple template (no extra API call).
    """
    if isinstance(analysis, TicketAnalysisWithDraft):
        return analysis.draft_response

    # Fallback: generate a template-based draft without an API call
    customer = analysis.entities.customer_name or "Valued Customer"
    cat = analysis.category.value

    if cat == "Fraud":
        body = (
            f"Dear {customer},\n\n"
            "Thank you for alerting us to this matter. We take the security of your "
            "account very seriously. Our fraud investigation team has been immediately "
            "notified and is actively reviewing the suspicious activity you reported.\n\n"
            "As a precaution, we have temporarily secured your account to prevent any "
            "further unauthorized transactions. Please do not hesitate to contact our "
            "dedicated fraud hotline at 1-800-FRAUD-HELP for immediate assistance.\n\n"
            "We will keep you updated on the progress of our investigation.\n\n"
            "Best regards,\nFinance Support Team\nfinance-support@company.com"
        )
    elif cat == "Payment Issue":
        body = (
            f"Dear {customer},\n\n"
            "Thank you for reaching out regarding your payment concern. We sincerely "
            "apologize for the inconvenience this has caused.\n\n"
            "Our payment and billing team is currently reviewing your case. Your "
            "reference number is [REF-XXXXXX]. You can expect a resolution within "
            "2-3 business days.\n\n"
            "If you have any further questions, please don't hesitate to reach out.\n\n"
            "Best regards,\nFinance Support Team\nfinance-support@company.com"
        )
    else:
        body = (
            f"Dear {customer},\n\n"
            "Thank you for contacting us. We have received your enquiry and our team "
            "is looking into it.\n\n"
            "We will get back to you shortly with a detailed response. If you need "
            "immediate assistance, please feel free to reach out again.\n\n"
            "Best regards,\nFinance Support Team\nfinance-support@company.com"
        )
    return body


# ────────────────────── Quick test ──────────────────────

if __name__ == "__main__":
    sample_email = (
        "Hi, my name is Rajesh Kumar. I noticed an unauthorized "
        "transaction of $500 on my account. The transaction ID is TXN-98432. "
        "I did not make this purchase and I'm very worried someone has access "
        "to my account. Please investigate this immediately and freeze my card."
    )

    print("🔍 Analysing sample email (single combined call)...\n")
    result = analyze_and_draft(sample_email)

    print("=" * 60)
    print("          TICKET ANALYSIS + DRAFT RESULT")
    print("=" * 60)
    print(f"  Sentiment   : {result.sentiment.value}")
    print(f"  Intent      : {result.intent}")
    print(f"  Priority    : {result.priority.value}")
    print(f"  Category    : {result.category.value}")
    print(f"  Summary     : {result.summary}")
    print()
    print("  Entities:")
    print(f"    Name      : {result.entities.customer_name or 'N/A'}")
    print(f"    Txn ID    : {result.entities.transaction_id or 'N/A'}")
    print(f"    Amount    : {result.entities.amount or 'N/A'}")
    print()
    print("  Draft Response:")
    print(f"    {result.draft_response[:200]}...")
    print("=" * 60)

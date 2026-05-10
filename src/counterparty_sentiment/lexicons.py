"""Auditable financial NLP lexicons and source reliability configuration."""

from __future__ import annotations

RISK_LEXICON: dict[str, dict[str, float]] = {
    "credit_risk": {
        "default": 1.0,
        "default warning": 0.95,
        "missed payment": 0.95,
        "restructuring": 0.75,
        "downgrade": 0.6,
        "negative outlook": 0.55,
        "distress": 0.7,
        "covenant breach": 0.8,
        "breach of covenant": 0.8,
    },
    "conduct_risk": {
        "fraud": 1.0,
        "bribery": 0.9,
        "misconduct": 0.8,
        "probe": 0.6,
        "investigation": 0.55,
        "lawsuit": 0.55,
        "allegations": 0.45,
    },
    "liquidity_risk": {
        "liquidity shortage": 1.0,
        "liquidity squeeze": 0.95,
        "cash burn": 0.8,
        "refinancing pressure": 0.7,
        "funding pressure": 0.75,
        "withdrawal": 0.55,
        "illiquid": 0.85,
    },
    "systemic_risk": {
        "systemic financial risks": 1.0,
        "systemic risk": 0.95,
        "amplify systemic financial risks": 1.0,
        "contagion": 0.85,
        "growing links": 0.65,
        "banks and private credit": 0.8,
        "private credit": 0.45,
        "interconnected": 0.65,
        "financial stability board": 0.5,
    },
    "sanctions_risk": {
        "sanction": 1.0,
        "sanctions exposure": 1.0,
        "export control": 0.8,
        "money laundering": 0.85,
        "aml breach": 0.8,
    },
    "market_risk": {
        "volatile": 0.6,
        "selloff": 0.75,
        "spread widening": 0.8,
        "drawdown": 0.65,
        "margin call": 0.85,
    },
    "resilience": {
        "well capitalized": -0.9,
        "investment grade": -0.75,
        "liquidity buffer": -0.7,
        "stable": -0.45,
        "upgrade": -0.65,
        "upgraded": -0.65,
        "resolved": -0.55,
        "dismissed": -0.5,
        "no evidence": -0.45,
        "compliant": -0.4,
    },
}

POSITIVE_TERMS = frozenset(
    term for terms in RISK_LEXICON.values() for term, weight in terms.items() if weight < 0
) | frozenset({"approved", "beat", "capital raise", "deleveraging", "profitable", "recovered"})

NEGATIVE_TERMS = frozenset(
    term for category, terms in RISK_LEXICON.items() if category != "resilience" for term, weight in terms.items() if weight > 0
) | frozenset({"amplify", "risk", "risks", "stress", "warned"})

SOURCE_RELIABILITY = {
    "sec filing": 1.0,
    "sec": 1.0,
    "10-k": 1.0,
    "10-q": 1.0,
    "reuters": 0.95,
    "bloomberg": 0.95,
    "ft": 0.9,
    "financial times": 0.9,
    "analyst-note": 0.85,
    "analyst note": 0.85,
    "news": 0.8,
    "press release": 0.75,
    "twitter": 0.4,
    "x": 0.4,
    "social": 0.35,
    "unknown": 0.65,
}

UNCERTAINTY_TERMS = frozenset({"could", "may", "might", "alleged", "reportedly", "possible", "potential"})
INTENSIFIERS = frozenset({"amplify", "growing", "material", "significant", "severe", "sharp", "elevated", "warned"})
NEGATORS = frozenset({"not", "no", "never", "without", "denied", "dismissed", "cleared"})
SUPPRESSION_PATTERNS = {
    "conduct_risk": (
        "denied fraud",
        "denied fraud allegations",
        "no evidence of misconduct",
        "fraud investigation dismissed",
        "misconduct allegations dismissed",
        "cleared of fraud",
    ),
    "credit_risk": (
        "not in default",
        "no default",
        "default risk resolved",
    ),
    "sanctions_risk": (
        "sanctions lifted",
        "no sanctions exposure",
    ),
}

EVENT_TYPE_PATTERNS = {
    "downgrade": ("downgrade", "downgraded", "negative outlook"),
    "upgrade": ("upgrade", "upgraded"),
    "restructuring": ("restructuring", "debt exchange"),
    "sanctions_exposure": ("sanction", "sanctions exposure", "export control"),
    "covenant_breach": ("covenant breach", "breach of covenant"),
    "liquidity_stress": ("liquidity shortage", "liquidity squeeze", "cash burn", "refinancing pressure"),
    "default_warning": ("default warning", "missed payment", "default risk", "default"),
    "fraud_loss_exposure": ("fraud", "bribery", "misconduct"),
    "systemic_risk_warning": ("systemic financial risks", "systemic risk", "contagion"),
}


TERM_RISK_FLAGS = {
    "default": "credit_default",
    "default warning": "default_warning",
    "missed payment": "payment_stress",
    "restructuring": "restructuring_risk",
    "covenant breach": "covenant_breach",
    "breach of covenant": "covenant_breach",
    "fraud": "conduct_risk",
    "bribery": "conduct_risk",
    "misconduct": "conduct_risk",
    "liquidity shortage": "liquidity_stress",
    "liquidity squeeze": "liquidity_stress",
    "refinancing pressure": "refinancing_pressure",
    "systemic financial risks": "systemic_risk",
    "systemic risk": "systemic_risk",
    "amplify systemic financial risks": "systemic_risk_amplification",
    "growing links": "interconnectedness_risk",
    "private credit": "private_credit_exposure",
    "banks and private credit": "bank_private_credit_linkage",
    "sanction": "sanctions_exposure",
    "sanctions exposure": "sanctions_exposure",
}

CATEGORY_ALIASES = {
    "credit_risk": "credit",
    "liquidity_risk": "liquidity",
    "systemic_risk": "systemic",
    "conduct_risk": "legal_conduct",
    "sanctions_risk": "sanctions",
    "market_risk": "market",
    "resilience": "resilience",
}

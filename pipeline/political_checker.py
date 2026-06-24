"""
Political sensitivity checker for IRIS.

This does not decide whether a claim is true or false. It only adds a warning
flag when the topic involves politics, public officials, elections, or
government agencies.
"""

from __future__ import annotations

import re
from typing import Dict, List


POLITICAL_KEYWORDS = [
    "president",
    "vice president",
    "senator",
    "congressman",
    "congresswoman",
    "mayor",
    "governor",
    "barangay",
    "election",
    "campaign",
    "vote",
    "voter",
    "comelec",
    "senado",
    "kongreso",
    "pangulo",
    "bise presidente",
    "gobyerno",
    "halalan",
    "botante",
    "boto",
    "philippines government",
    "department of",
]

PUBLIC_AGENCIES = [
    "doh",
    "deped",
    "dilg",
    "dost",
    "dswd",
    "dti",
    "dnd",
    "pnp",
    "afp",
    "bir",
    "doj",
    "coa",
    "nbi",
    "lto",
    "ltfrb",
    "philhealth",
    "sss",
    "gsis",
]


def _normalize(text: str) -> str:
    """Lowercase text and make spacing predictable for keyword matching."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def flag_political(text: str) -> Dict[str, object]:
    """
    Checks whether text should receive the Politically Sensitive overlay.

    The returned flag can attach to any final verdict later, such as Verified or
    Not Found.
    """
    normalized = _normalize(text)

    matched_keywords: List[str] = [
        keyword for keyword in POLITICAL_KEYWORDS if keyword in normalized
    ]

    matched_agencies: List[str] = [
        agency
        for agency in PUBLIC_AGENCIES
        if re.search(rf"\b{re.escape(agency)}\b", normalized)
    ]

    return {
        "politically_sensitive": bool(matched_keywords or matched_agencies),
        "matched_keywords": matched_keywords,
        "matched_agencies": matched_agencies,
    }

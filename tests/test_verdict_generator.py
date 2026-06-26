"""
Simple Week 3 verdict helper checks.

Run from the iris-backend folder:
    python tests/test_verdict_generator.py

This test loads the sentence-transformers model, so the first run may take time.
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.verdict_generator import generate_verdict


def run_checks() -> None:
    claim = "The Department of Health reported new dengue cases."
    articles = [
        {
            "source": "GMA News",
            "title": "DOH reports dengue cases",
            "url": "https://example.com/dengue",
            "status": "extracted",
            "word_count": 120,
            "text": (
                "The Department of Health reported new dengue cases in the "
                "Philippines and reminded the public to remove mosquito "
                "breeding sites."
            ),
        },
        {
            "source": "Philippine Star",
            "title": "Sports update",
            "url": "https://example.com/sports",
            "status": "extracted",
            "word_count": 120,
            "text": (
                "A basketball team won the championship after a close final "
                "game in Manila."
            ),
        },
    ]

    result = generate_verdict(claim, articles)

    assert result["verdict"] in ["Verified", "Partially Verified", "Not Found"]
    assert result["primary_evidence"] is not None
    assert "similarity_score" in result["primary_evidence"]
    assert result["corroboration_count"] >= 0

    print("All Week 3 verdict checks passed.")
    print(f"Verdict: {result['verdict']}")
    print(f"Top score: {result['primary_evidence']['similarity_score']}")


if __name__ == "__main__":
    run_checks()

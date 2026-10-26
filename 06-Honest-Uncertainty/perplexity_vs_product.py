"""
perplexity_vs_product.py: perplexity is not product quality.

Run:  python perplexity_vs_product.py

Cross-entropy and perplexity say how well a model predicts the next tokens of a known
text. They matter in training. They do not say whether the chatbot followed the policy,
cited fresh sources, or escalated a medical question.

Here, model B predicts the reference text better (lower perplexity) and is worse for
the product. Treat perplexity as a background signal; decide on product metrics.
"""

from __future__ import annotations

import math
import sys
from typing import Dict, List

# Probability each model gave to the actual next token of a reference support transcript.
TOKEN_PROBABILITIES: Dict[str, List[float]] = {
    "model_a": [0.42, 0.31, 0.55, 0.20, 0.38, 0.47, 0.29, 0.51, 0.33, 0.40, 0.26, 0.44],
    "model_b": [0.58, 0.49, 0.66, 0.37, 0.52, 0.61, 0.45, 0.63, 0.50, 0.57, 0.41, 0.60],
}
# Product metrics on the same 200 support questions (passes out of 200).
PRODUCT = {
    "model_a": {"follows return policy": 188, "cites a current source": 176, "escalates medical questions": 39},
    "model_b": {"follows return policy": 171, "cites a current source": 150, "escalates medical questions": 31},
}
MEDICAL_QUESTIONS = 40


def cross_entropy(probs: List[float]) -> float:
    """Average negative log-probability of the true tokens, in nats."""
    return -sum(math.log(p) for p in probs) / len(probs)


def main() -> None:
    print(f"{'':28} {'model A':>10} {'model B':>10}")
    ce = {m: cross_entropy(p) for m, p in TOKEN_PROBABILITIES.items()}
    print(f"{'cross-entropy (lower=better)':28} {ce['model_a']:>10.2f} {ce['model_b']:>10.2f}")
    print(f"{'perplexity (lower=better)':28} {math.exp(ce['model_a']):>10.2f} {math.exp(ce['model_b']):>10.2f}")
    print("─" * 50)
    for metric in PRODUCT["model_a"]:
        n = MEDICAL_QUESTIONS if "medical" in metric else 200
        a, b = PRODUCT["model_a"][metric], PRODUCT["model_b"][metric]
        print(f"{metric:28} {a / n:>10.0%} {b / n:>10.0%}")
    print("\nModel B wins on perplexity and loses on every product metric.")
    print("Perplexity is a background signal. Base the decision on product metrics.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()

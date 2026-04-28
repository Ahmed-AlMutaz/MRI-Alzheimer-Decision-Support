def build_explanation(label: str, confidence: float) -> str:
    pct = round(confidence * 100, 2)

    if label == "Normal":
        return (
            f"The scan pattern appears closer to the normal class with {pct}% confidence. "
            "This suggests no strong imaging pattern of Alzheimer's in this automated check."
        )

    if label == "Early-stage Alzheimer's":
        return (
            f"The scan pattern is more consistent with early-stage Alzheimer's at {pct}% confidence. "
            "This may indicate subtle changes and should be correlated with clinical evaluation."
        )

    return (
        f"The scan pattern is more consistent with advanced Alzheimer's at {pct}% confidence. "
        "This indicates a stronger pattern in this automated check and needs specialist review."
    )

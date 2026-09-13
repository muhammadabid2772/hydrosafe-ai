def analyze_trends(readings):
    """
    Analyze a sequence of numeric readings and return
    a unified trend intelligence result.
    """

    if not readings or len(readings) < 2:
        return {
            "trend": "insufficient_data",
            "percentage_change": 0,
            "rate_of_change": 0,
            "sustained": False,
            "sudden_acceleration": False,
            "time_window": 0,
            "score": 0,
            "confidence": 0,
            "evidence": "Not enough observations to determine a trend."
        }

    values = [float(reading["value"]) for reading in readings]

    first_value = values[0]
    last_value = values[-1]

    change = last_value - first_value

    if first_value != 0:
        percentage_change = (change / abs(first_value)) * 100
    else:
        percentage_change = 0

    rate_of_change = change / (len(values) - 1)

    if change > 0:
        trend = "increasing"
    elif change < 0:
        trend = "decreasing"
    else:
        trend = "stable"

    increasing_steps = sum(
        1 for i in range(1, len(values))
        if values[i] > values[i - 1]
    )

    decreasing_steps = sum(
        1 for i in range(1, len(values))
        if values[i] < values[i - 1]
    )

    total_steps = len(values) - 1
    required_steps = max(1, int(total_steps * 0.7))

    sustained = (
        increasing_steps >= required_steps
        or decreasing_steps >= required_steps
    )

    changes = [
        values[i] - values[i - 1]
        for i in range(1, len(values))
    ]

    sudden_acceleration = False

    if len(changes) >= 2:
        recent_change = abs(changes[-1])
        previous_change = abs(changes[-2])

        if previous_change > 0 and recent_change >= previous_change * 2:
            sudden_acceleration = True

    score = min(100, abs(percentage_change) * 10)

    if sudden_acceleration:
        score = min(100, score + 20)

    consistency = max(
        increasing_steps,
        decreasing_steps
    ) / total_steps

    confidence = min(
        1.0,
        0.5 + (consistency * 0.4)
    )

    evidence = (
        f"The {trend} trend changed by "
        f"{percentage_change:.2f}% over the previous "
        f"{len(values)} observations."
    )

    if sustained:
        evidence += " The movement is sustained."

    if sudden_acceleration:
        evidence += " A sudden acceleration was detected."

    return {
        "trend": trend,
        "percentage_change": round(percentage_change, 2),
        "rate_of_change": round(rate_of_change, 4),
        "sustained": sustained,
        "sudden_acceleration": sudden_acceleration,
        "time_window": len(values),
        "score": round(score, 2),
        "confidence": round(confidence, 2),
        "evidence": evidence
    }
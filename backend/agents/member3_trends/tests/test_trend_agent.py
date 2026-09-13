from backend.agents.member3_trends import analyze_trends


def test_timestamped_rate_is_per_day_and_order_is_normalized():
    result = analyze_trends([
        {"value": 12, "timestamp": "2026-01-03T00:00:00Z"},
        {"value": 10, "timestamp": "2026-01-01T00:00:00Z"},
    ])
    assert result["available"] is True
    assert result["rate_of_change"] == 1
    assert result["rate_unit"] == "per_day"
    assert result["trend"] == "increasing"


def test_flat_zero_series_is_available_with_valid_zero_score():
    result = analyze_trends([
        {"value": 0, "timestamp": "2026-01-01T00:00:00Z"},
        {"value": 0, "timestamp": "2026-01-02T00:00:00Z"},
    ])
    assert result["available"] is True
    assert result["trend"] == "stable"
    assert result["score"] == 0


def test_one_point_is_explicitly_insufficient():
    result = analyze_trends([{"value": 2, "timestamp": "2026-01-01T00:00:00Z"}])
    assert result["available"] is False
    assert result["status"] == "INSUFFICIENT_DATA"


def test_naive_and_utc_timestamps_can_be_sorted_together():
    result = analyze_trends([
        {"value": 2, "timestamp": "2026-01-02T00:00:00Z"},
        {"value": 1, "timestamp": "2026-01-01T00:00:00"},
    ])
    assert result["available"] is True
    assert result["rate_of_change"] == 1

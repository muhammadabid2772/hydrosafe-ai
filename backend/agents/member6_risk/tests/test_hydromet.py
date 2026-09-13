from backend.agents.member6_risk.hydromet import HydrometObservation, build_hydromet_calibration


def test_calibration_reports_gaps_completeness_and_latest_rolling_values():
    rows = [
        HydrometObservation(
            observed_at=f"2025-01-{day:02d}", reservoir_level_m=460 + day / 10,
            tailwater_level_m=390.0, inflow_m3_s=100 + day, outflow_m3_s=None,
            mean_temperature_c=10.0, daily_rainfall_mm=float(day % 2),
        )
        for day in range(1, 16) if day != 8
    ]
    model = build_hydromet_calibration(rows)
    assert model["row_count"] == 14
    assert model["missing_dates"] == ["2025-01-08"]
    assert model["field_completeness"]["outflow_m3_s"] == 0
    assert model["latest_context"]["rainfall_7d_mm"] == 4
    assert "01|reservoir_level_m" in model["monthly_profiles"]

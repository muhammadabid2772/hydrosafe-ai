from datetime import datetime

from backend.agents.member6_risk.normalizer import _find_header, _timestamp


def test_observation_header_wins_over_installation_metadata():
    rows = [
        ["Installation date", datetime(2020, 1, 1), "埋设时间"],
        ["Observation Date", "Time", "Applied pressure (MPa)"],
    ]
    assert _find_header(rows) == (1, 0)


def test_timestamp_combines_excel_date_and_time():
    result = _timestamp(datetime(2025, 10, 20), datetime(1900, 1, 1, 9, 15).time())
    assert result == datetime(2025, 10, 20, 9, 15)

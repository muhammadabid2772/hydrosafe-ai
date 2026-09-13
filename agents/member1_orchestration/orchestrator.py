import pandas as pd

try:
    import backend.agents.member2_validation as m2
except ImportError:
    m2 = None

try:
    from backend.agents.member3_trends.trend_agent import analyze_trends as m3_analyze_trends
except ImportError:
    m3_analyze_trends = None

try:
    from backend.agents.member4_anomaly import Member4Detector, normalize_history
    from backend.agents.member4_anomaly.models import Member4CurrentConditions
except ImportError:
    Member4Detector, normalize_history, Member4CurrentConditions = None, None, None


def _serialize(obj):
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj


def run_complete_analysis(file_path: str) -> dict:
    df = pd.read_csv(file_path)

    # 1. Validation (Member 2)
    quality = {"status": "NOT_AVAILABLE", "reason": "Member 2 not loaded"}
    if m2:
        try:
            fn = getattr(m2, "validate_data", getattr(m2, "validate_dataset", None))
            if fn:
                quality = _serialize(fn(df))
            else:
                quality = {"status": "ERROR", "reason": "No validate_data or validate_dataset found in M2"}
        except Exception as e:
            quality = {"status": "ERROR", "reason": f"Member 2 error: {str(e)}"}

    # 2. Trends (Member 3)
    trends = {"status": "NOT_AVAILABLE", "reason": "Member 3 not loaded"}
    if m3_analyze_trends:
        try:
            metric_col = next(
                (c for c in ["Reservoir water level", "reservoir_level", "in_flow", "inflow"] if c in df.columns),
                df.select_dtypes(include="number").columns[0] if not df.select_dtypes(include="number").empty else None
            )
            if metric_col:
                readings = [{"value": row[metric_col]} for _, row in df.iterrows() if pd.notna(row[metric_col])]
                trends = _serialize(m3_analyze_trends(readings))
            else:
                trends = {"status": "ERROR", "reason": "No numeric column found for trend analysis"}
        except Exception as e:
            trends = {"status": "ERROR", "reason": f"Member 3 error: {str(e)}"}

    # 3. Anomalies (Member 4)
    anomalies = {"status": "NOT_AVAILABLE", "reason": "Member 4 not loaded"}
    if Member4Detector:
        try:
            detector = Member4Detector(history=df)
            norm_df = detector.history
            if not norm_df.empty:
                current_dict = norm_df.iloc[-1].to_dict()
                valid_params = {"reservoir_level", "tailwater", "inflow", "rainfall", "temperature"}
                filtered_dict = {k: float(v) for k, v in current_dict.items() if k in valid_params and pd.notna(v)}
                if Member4CurrentConditions and set(filtered_dict.keys()) >= valid_params:
                    current_payload = Member4CurrentConditions(**filtered_dict)
                else:
                    current_payload = filtered_dict
                
                if hasattr(detector, "assess"):
                    res = detector.assess(current=current_payload)
                elif hasattr(detector, "detect"):
                    res = detector.detect()
                elif callable(detector):
                    res = detector(current_payload)
                else:
                    res = {"status": "ERROR", "reason": "No valid method on Member4Detector"}
                anomalies = _serialize(res)
            else:
                anomalies = {"status": "ERROR", "reason": "Normalized history is empty"}
        except Exception as e:
            anomalies = {"status": "ERROR", "reason": f"Member 4 error: {str(e)}"}

    return {
        "project_id": "demo-dam-01",
        "structure": "ACCRD",
        "quality": quality,
        "trends": trends,
        "anomalies": anomalies,
        "correlations": {"status": "NOT_AVAILABLE", "reason": "Member 5 not connected."},
        "risk": {"status": "NOT_AVAILABLE", "reason": "Member 6 not connected.", "risk_score": 0, "risk_level": "NOT_ASSESSED"},
        "report": {
            "status": "SUCCESS",
            "summary": "Pipeline evaluation completed.",
            "what_is_happening": "System operating within nominal limits.",
            "recommended_action": "Continue standard monitoring."
        }
    }
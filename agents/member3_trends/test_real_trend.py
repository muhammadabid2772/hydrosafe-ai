from data_loader import load_piezometer_readings
from trend_agent import analyze_trends


file_path = "../../data/ACCRD - P (402 - CSAIL-402-000145-2022 - 1 - A) - 1.XLSX"

readings = load_piezometer_readings(
    file_path,
    "P01DS1"
)

# Use the latest 10 observations for trend analysis
latest_readings = readings[-10:]

result = analyze_trends(latest_readings)

print("Instrument:", latest_readings[0]["instrument_id"])
print("Metric:", latest_readings[0]["metric"])
print("Trend Analysis:")
print(result)
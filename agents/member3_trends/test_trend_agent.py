from trend_agent import analyze_trends


readings = [
    {"value": 10},
    {"value": 10.5},
    {"value": 11},
    {"value": 11.8},
    {"value": 12.5},
    {"value": 13},
    {"value": 14}
]


result = analyze_trends(readings)

print(result)
from data_loader import load_piezometer_readings


file_path = "../../data/ACCRD - P (402 - CSAIL-402-000145-2022 - 1 - A) - 1.XLSX"

readings = load_piezometer_readings(
    file_path,
    "P01DS1"
)

print("Total readings:", len(readings))
print("First reading:", readings[0])
print("Last reading:", readings[-1])
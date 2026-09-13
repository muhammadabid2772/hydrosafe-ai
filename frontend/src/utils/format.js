export function formatUtcTimestamp(value) {
  if (!value) return "Pending";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Pending";
  return `${date.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

export function formatUnit(unit) {
  if (unit === "m3/s") return "m³/s";
  if (unit === "C") return "°C";
  return unit;
}

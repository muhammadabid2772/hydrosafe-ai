export const DEFAULT_CONDITIONS = Object.freeze({
  reservoir_level: "459.04",
  tailwater: "391.69",
  inflow: "490",
  rainfall: "49",
  temperature: "24.8",
});

export const CONDITION_FIELDS = Object.freeze([
  { key: "reservoir_level", label: "Reservoir level", unit: "m", step: "0.01" },
  { key: "tailwater", label: "Tailwater level", unit: "m", step: "0.01" },
  { key: "inflow", label: "Inflow", unit: "m³/s", step: "0.01", min: "0" },
  { key: "rainfall", label: "Daily rainfall", unit: "mm", step: "0.01", min: "0" },
  { key: "temperature", label: "Mean temperature", unit: "°C", step: "0.1" },
]);

export function validateConditions(values) {
  const errors = {};
  for (const field of CONDITION_FIELDS) {
    const value = Number(values[field.key]);
    if (values[field.key] === "" || !Number.isFinite(value)) errors[field.key] = "Enter a valid number.";
    if ((field.key === "inflow" || field.key === "rainfall") && value < 0) {
      errors[field.key] = `${field.label} cannot be negative.`;
    }
  }
  return errors;
}

export function buildAnomalyRequest({ values, observedAt, structure }) {
  return {
    risk: {
      project_id: "demo-dam-01",
      structure,
    },
    current_hydromet: Object.fromEntries(
      CONDITION_FIELDS.map((field) => [field.key, Number(values[field.key])]),
    ),
    observed_at: new Date(observedAt).toISOString(),
    source: "HydroSafe operator entry screened against the shared hydrometeorological baseline",
  };
}

export function severityTone(severity) {
  if (severity === "High") return "critical";
  if (severity === "Moderate") return "warning";
  return "normal";
}

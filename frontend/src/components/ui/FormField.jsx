export default function FormField({ label, id, error, hint, ...inputProps }) {
  const describedBy = [error ? `${id}-error` : "", hint ? `${id}-hint` : ""].filter(Boolean).join(" ");
  return (
    <label className="form-field" htmlFor={id}>
      <span>{label}</span>
      <input id={id} aria-invalid={Boolean(error)} aria-describedby={describedBy || undefined} {...inputProps} />
      {hint && <small id={`${id}-hint`}>{hint}</small>}
      {error && <small className="field-error" id={`${id}-error`}>{error}</small>}
    </label>
  );
}

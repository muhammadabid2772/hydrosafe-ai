import { useState } from "react";

export default function PasswordField({ label, id, hint, ...props }) {
  const [visible, setVisible] = useState(false);
  return (
    <label className="form-field" htmlFor={id}>
      <span>{label}</span>
      <span className="password-wrap">
        <input id={id} type={visible ? "text" : "password"} aria-describedby={hint ? `${id}-hint` : undefined} {...props} />
        <button type="button" onClick={() => setVisible((value) => !value)} aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" /><circle cx="12" cy="12" r="2.5" />{visible && <path d="m4 4 16 16" />}</svg>
        </button>
      </span>
      {hint && <small id={`${id}-hint`}>{hint}</small>}
    </label>
  );
}

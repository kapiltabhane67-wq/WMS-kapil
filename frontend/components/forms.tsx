import type { FormEvent, ReactNode } from "react";

export function FormPanel({
  title,
  icon,
  onSubmit,
  children,
}: {
  title: string;
  icon: ReactNode;
  onSubmit: (event: FormEvent) => void;
  children: ReactNode;
}) {
  return (
    <form className="panel" onSubmit={onSubmit}>
      <div className="panel-head">
        <h2>{title}</h2>
        {icon}
      </div>
      <div className="panel-body form-grid">{children}</div>
    </form>
  );
}

export function Input({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="form-grid">
      <span>{label}</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

export function NumberInput({
  label,
  value,
  onChange,
  min = 0,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
}) {
  return (
    <label className="form-grid">
      <span>{label}</span>
      <input type="number" min={min} value={value} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}

export function Select({
  label,
  value,
  onChange,
  options,
  placeholder = "Select",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
  placeholder?: string;
}) {
  return (
    <label className="form-grid">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} disabled={options.length === 0}>
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

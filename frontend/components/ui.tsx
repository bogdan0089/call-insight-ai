import {
  cloneElement,
  useId,
  type ButtonHTMLAttributes,
  type CSSProperties,
  type ReactElement,
  type ReactNode,
} from "react";
import { color, radius, type } from "@/lib/theme";

type Tone = "neutral" | "pass" | "fail" | "warn" | "info" | "accent";

const TONES: Record<Tone, { fg: string; bg: string; border: string }> = {
  neutral: { fg: color.textMuted, bg: "transparent", border: color.border },
  pass: { fg: color.pass, bg: color.passBg, border: color.passBorder },
  fail: { fg: color.fail, bg: color.failBg, border: color.failBorder },
  warn: { fg: color.warn, bg: color.warnBg, border: color.warnBorder },
  info: { fg: color.info, bg: color.infoBg, border: color.infoBorder },
  accent: { fg: color.accent, bg: color.accentSoft, border: color.accentBorder },
};

export function Card({
  children,
  style,
  padded = true,
}: {
  children: ReactNode;
  style?: CSSProperties;
  padded?: boolean;
}) {
  return (
    <section
      style={{
        background: color.surface,
        border: `1px solid ${color.border}`,
        borderRadius: radius.lg,
        padding: padded ? "18px 20px" : 0,
        overflow: "hidden",
        ...style,
      }}
    >
      {children}
    </section>
  );
}

export function CardTitle({ children, aside }: { children: ReactNode; aside?: ReactNode }) {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
        padding: "16px 20px",
        borderBottom: `1px solid ${color.border}`,
      }}
    >
      <h2 style={{ margin: 0, fontSize: 13, fontWeight: 700, letterSpacing: "-0.1px" }}>
        {children}
      </h2>
      {aside}
    </header>
  );
}

export function Label({ children }: { children: ReactNode }) {
  return <span style={{ ...type.label, color: color.textDim }}>{children}</span>;
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: Tone }) {
  const t = TONES[tone];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        padding: "3px 9px",
        borderRadius: radius.pill,
        border: `1px solid ${t.border}`,
        background: t.bg,
        color: t.fg,
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: "0.8px",
        textTransform: "uppercase",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </span>
  );
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  tone?: Tone;
  children: ReactNode;
}

export function Button({ tone = "neutral", children, style, ...rest }: ButtonProps) {
  const t = TONES[tone];
  return (
    <button
      className="btn"
      style={{
        padding: "7px 14px",
        borderRadius: radius.sm,
        border: `1px solid ${t.border}`,
        background: t.bg,
        color: rest.disabled ? color.textFaint : t.fg,
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: "0.6px",
        textTransform: "uppercase",
        cursor: rest.disabled ? "not-allowed" : "pointer",
        ...style,
      }}
      {...rest}
    >
      {children}
    </button>
  );
}

export function Stat({
  label,
  value,
  hint,
  tone = "neutral",
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: Tone;
}) {
  return (
    <Card style={{ padding: "16px 18px" }}>
      <Label>{label}</Label>
      <div
        className="num"
        style={{
          marginTop: 8,
          fontSize: 26,
          fontWeight: 700,
          lineHeight: 1.1,
          color: TONES[tone].fg === color.textMuted ? color.text : TONES[tone].fg,
        }}
      >
        {value}
      </div>
      {hint ? (
        <div style={{ marginTop: 6, fontSize: 12, color: color.textDim }}>{hint}</div>
      ) : null}
    </Card>
  );
}

export function Meter({ value, tone }: { value: number | null; tone: Tone }) {
  return (
    <div className="meter" title={value === null ? "немає оцінки" : `${value}`}>
      <span
        style={{
          width: `${Math.max(0, Math.min(100, value ?? 0))}%`,
          background: TONES[tone].fg,
          opacity: value === null ? 0.15 : 1,
        }}
      />
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        padding: "40px 20px",
        textAlign: "center",
        color: color.textDim,
        fontSize: 13,
      }}
    >
      {children}
    </div>
  );
}

export function Notice({ tone = "fail", children }: { tone?: Tone; children: ReactNode }) {
  const t = TONES[tone];
  return (
    <div
      style={{
        padding: "12px 16px",
        borderRadius: radius.md,
        border: `1px solid ${t.border}`,
        background: t.bg,
        color: t.fg,
        fontSize: 13,
      }}
    >
      {children}
    </div>
  );
}

export function SortHeader<Field extends string>({
  field,
  label,
  sortBy,
  order,
  onSort,
  align = "left",
}: {
  field: Field;
  label: string;
  sortBy: Field;
  order: "asc" | "desc";
  onSort: (field: Field) => void;
  align?: "left" | "right";
}) {
  const active = sortBy === field;
  const arrow = active ? (order === "asc" ? "↑" : "↓") : "↕";
  return (
    <th style={{ textAlign: align }} aria-sort={active ? (order === "asc" ? "ascending" : "descending") : "none"}>
      <button type="button" className="sort-head" data-active={active} onClick={() => onSort(field)}>
        {label}
        <span aria-hidden className="sort-arrow">
          {arrow}
        </span>
      </button>
    </th>
  );
}

interface Control {
  id?: string;
  "aria-describedby"?: string;
  "aria-invalid"?: boolean;
}

export function Field({
  label,
  error,
  hint,
  children,
}: {
  label: string;
  error?: string | null;
  hint?: ReactNode;
  children: ReactElement<Control>;
}) {
  const id = useId();
  const noteId = `${id}-note`;
  const note = error || hint;

  const control = cloneElement(children, {
    id,
    "aria-describedby": note ? noteId : undefined,
    "aria-invalid": error ? true : undefined,
  });

  return (
    <div className="form-field">
      <label htmlFor={id} style={{ ...type.label, color: color.textDim }}>
        {label}
      </label>
      {control}
      {note ? (
        <span
          id={noteId}
          role={error ? "alert" : undefined}
          style={{ fontSize: 12, color: error ? color.fail : color.textDim }}
        >
          {note}
        </span>
      ) : null}
    </div>
  );
}

export function AuthCard({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="auth-wrap">
      <Card style={{ padding: "28px 28px 24px" }}>
        <h1 className="page-title" style={{ fontSize: 20 }}>
          {title}
        </h1>
        {subtitle ? <p className="page-sub">{subtitle}</p> : null}
        <div style={{ marginTop: 22 }}>{children}</div>
      </Card>
      {footer ? <div className="auth-footer">{footer}</div> : null}
    </div>
  );
}

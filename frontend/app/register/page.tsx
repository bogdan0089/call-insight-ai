"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";
import { AuthCard, Button, Field, Notice } from "@/components/ui";
import { api } from "@/lib/api";
import { NAME_MAX, ORG_NAME_MAX, ORG_NAME_MIN, PASSWORD_MAX, passwordProblem } from "@/lib/limits";

interface Form {
  organization_name: string;
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}

const EMPTY: Form = {
  organization_name: "",
  first_name: "",
  last_name: "",
  email: "",
  password: "",
};

function problems(form: Form): Partial<Record<keyof Form, string>> {
  const found: Partial<Record<keyof Form, string>> = {};
  if (form.organization_name.trim().length < ORG_NAME_MIN) {
    found.organization_name = `Щонайменше ${ORG_NAME_MIN} символи`;
  }
  if (!form.first_name.trim()) found.first_name = "Вкажіть імʼя";
  if (!form.last_name.trim()) found.last_name = "Вкажіть прізвище";
  if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) found.email = "Схоже, пошта з помилкою";
  const password = passwordProblem(form.password);
  if (password) found.password = password;
  return found;
}

function CheckInbox({ email }: { email: string }) {
  const [state, setState] = useState<"idle" | "busy" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);

  async function resend() {
    setState("busy");
    setError(null);
    try {
      await api.resend(email);
      setState("sent");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не вдалося надіслати");
      setState("idle");
    }
  }

  return (
    <AuthCard
      title="Перевірте пошту"
      subtitle={
        <>
          Надіслали посилання на <b>{email}</b>. Відкрийте його, щоб підтвердити адресу.
        </>
      }
      footer={<Link href="/login">Повернутись до входу</Link>}
    >
      <div className="form">
        {error ? <Notice>{error}</Notice> : null}
        {state === "sent" ? <Notice tone="pass">Лист надіслано ще раз</Notice> : null}
        <Button type="button" onClick={resend} disabled={state !== "idle"}>
          {state === "busy" ? "Надсилаємо…" : "Надіслати ще раз"}
        </Button>
      </div>
    </AuthCard>
  );
}

function RegisterForm() {
  const params = useSearchParams();

  const [form, setForm] = useState<Form>(EMPTY);
  const [touched, setTouched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [sentTo, setSentTo] = useState<string | null>(params.get("resend"));

  const found = problems(form);
  const show = (field: keyof Form) => (touched ? found[field] : null);

  function change(field: keyof Form, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setTouched(true);
    if (Object.keys(found).length > 0) return;

    setBusy(true);
    setError(null);
    try {
      const email = form.email.trim();
      await api.register({
        email,
        password: form.password,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        organization_name: form.organization_name.trim(),
      });
      setSentTo(email);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не вдалося зареєструватись");
    } finally {
      setBusy(false);
    }
  }

  if (sentTo) return <CheckInbox email={sentTo} />;

  return (
    <AuthCard
      title="Реєстрація компанії"
      subtitle="Ви станете власником і зможете запросити команду"
      footer={
        <>
          Уже є акаунт? <Link href="/login">Увійти</Link>
        </>
      }
    >
      <form className="form" onSubmit={submit} noValidate>
        {error ? <Notice>{error}</Notice> : null}

        <Field label="Назва компанії" error={show("organization_name")}>
          <input
            className="field"
            maxLength={ORG_NAME_MAX}
            autoComplete="organization"
            value={form.organization_name}
            onChange={(event) => change("organization_name", event.target.value)}
          />
        </Field>

        <div className="form-row">
          <Field label="Імʼя" error={show("first_name")}>
            <input
              className="field"
              maxLength={NAME_MAX}
              autoComplete="given-name"
              value={form.first_name}
              onChange={(event) => change("first_name", event.target.value)}
            />
          </Field>
          <Field label="Прізвище" error={show("last_name")}>
            <input
              className="field"
              maxLength={NAME_MAX}
              autoComplete="family-name"
              value={form.last_name}
              onChange={(event) => change("last_name", event.target.value)}
            />
          </Field>
        </div>

        <Field label="Пошта" error={show("email")}>
          <input
            className="field"
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={(event) => change("email", event.target.value)}
          />
        </Field>

        <Field label="Пароль" error={show("password")} hint="Від 8 символів, літера і цифра">
          <input
            className="field"
            type="password"
            autoComplete="new-password"
            maxLength={PASSWORD_MAX}
            value={form.password}
            onChange={(event) => change("password", event.target.value)}
          />
        </Field>

        <Button tone="accent" type="submit" disabled={busy} style={{ padding: "10px 14px" }}>
          {busy ? "Створюємо…" : "Зареєструвати"}
        </Button>
      </form>
    </AuthCard>
  );
}

export default function RegisterPage() {
  return (
    <Suspense>
      <RegisterForm />
    </Suspense>
  );
}

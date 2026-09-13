"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";
import { useAuth } from "@/components/auth-provider";
import { AuthCard, Button, Field, Notice } from "@/components/ui";
import { ApiError, api } from "@/lib/api";
import { PASSWORD_MAX } from "@/lib/limits";
import { safeNext } from "@/lib/redirect";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { signIn } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [unverified, setUnverified] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setUnverified(false);

    try {
      const { access_token } = await api.login(email.trim(), password);
      await signIn(access_token);
      router.replace(safeNext(params.get("next")));
    } catch (err) {
      if (err instanceof ApiError && err.code === "EmailNotVerified") {
        setUnverified(true);
      } else if (err instanceof ApiError && err.code === "InvalidCredentials") {
        setError("Невірна пошта або пароль");
      } else if (err instanceof ApiError && err.code === "AccountDisabled") {
        setError("Доступ вимкнено. Зверніться до власника компанії");
      } else {
        setError(err instanceof Error ? err.message : "Не вдалося увійти");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard
      title="Вхід"
      subtitle="Контроль якості дзвінків вашої команди"
      footer={
        <>
          Немає акаунта? <Link href="/register">Зареєструвати компанію</Link>
        </>
      }
    >
      <form className="form" onSubmit={submit} noValidate>
        {error ? <Notice>{error}</Notice> : null}
        {unverified ? (
          <Notice tone="warn">
            Пошту ще не підтверджено. Перевірте скриньку або{" "}
            <Link className="link" href={`/register?resend=${encodeURIComponent(email.trim())}`}>
              надішліть лист ще раз
            </Link>
            .
          </Notice>
        ) : null}

        <Field label="Пошта">
          <input
            className="field"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </Field>

        <Field label="Пароль">
          <input
            className="field"
            type="password"
            autoComplete="current-password"
            required
            maxLength={PASSWORD_MAX}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </Field>

        <Button
          tone="accent"
          type="submit"
          disabled={busy || !email.trim() || !password}
          style={{ padding: "10px 14px" }}
        >
          {busy ? "Входимо…" : "Увійти"}
        </Button>

      </form>
    </AuthCard>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}

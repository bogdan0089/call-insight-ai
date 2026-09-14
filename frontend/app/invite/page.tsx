"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";
import { useAuth } from "@/components/auth-provider";
import { AuthCard, Button, Field, Notice } from "@/components/ui";
import { api } from "@/lib/api";
import { PASSWORD_MAX, passwordProblem } from "@/lib/limits";

function AcceptInvite() {
  const router = useRouter();
  const params = useSearchParams();
  const { signIn } = useAuth();
  const token = params.get("token");

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [touched, setTouched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const problem = passwordProblem(password);
  const mismatch = confirm && confirm !== password ? "Паролі не збігаються" : null;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setTouched(true);
    if (!token || problem || mismatch || !confirm) return;

    setBusy(true);
    setError(null);
    try {
      const user = await api.acceptInvite(token, password);
      const { access_token } = await api.login(user.email, password);
      await signIn(access_token);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не вдалося прийняти запрошення");
    } finally {
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <AuthCard title="Запрошення">
        <Notice>У посиланні немає токена. Попросіть надіслати запрошення ще раз.</Notice>
      </AuthCard>
    );
  }

  return (
    <AuthCard title="Вас запросили в команду" subtitle="Задайте пароль, щоб увійти">
      <form className="form" onSubmit={submit} noValidate>
        {error ? <Notice>{error}</Notice> : null}

        <Field label="Пароль" error={touched ? problem : null} hint="Від 8 символів, літера і цифра">
          <input
            className="field"
            type="password"
            autoComplete="new-password"
            maxLength={PASSWORD_MAX}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </Field>

        <Field label="Ще раз" error={touched ? mismatch : null}>
          <input
            className="field"
            type="password"
            autoComplete="new-password"
            maxLength={PASSWORD_MAX}
            value={confirm}
            onChange={(event) => setConfirm(event.target.value)}
          />
        </Field>

        <Button tone="accent" type="submit" disabled={busy} style={{ padding: "10px 14px" }}>
          {busy ? "Зберігаємо…" : "Задати пароль і увійти"}
        </Button>
      </form>
    </AuthCard>
  );
}

export default function InvitePage() {
  return (
    <Suspense>
      <AcceptInvite />
    </Suspense>
  );
}

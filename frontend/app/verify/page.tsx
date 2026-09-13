"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import { AuthCard, Empty, Notice } from "@/components/ui";
import { api } from "@/lib/api";

type State =
  | { kind: "working" }
  | { kind: "done"; email: string }
  | { kind: "failed"; message: string };

function Verify() {
  const params = useSearchParams();
  const token = params.get("token");
  const [state, setState] = useState<State>(
    token ? { kind: "working" } : { kind: "failed", message: "У посиланні немає токена" },
  );

  const started = useRef(false);

  useEffect(() => {
    if (!token || started.current) return;
    started.current = true;

    api
      .verify(token)
      .then((user) => setState({ kind: "done", email: user.email }))
      .catch((err: unknown) =>
        setState({
          kind: "failed",
          message: err instanceof Error ? err.message : "Не вдалося підтвердити",
        }),
      );
  }, [token]);

  if (state.kind === "working") {
    return (
      <AuthCard title="Підтвердження пошти">
        <Empty>Перевіряємо посилання…</Empty>
      </AuthCard>
    );
  }

  if (state.kind === "done") {
    return (
      <AuthCard title="Пошту підтверджено" subtitle={state.email}>
        <Notice tone="pass">
          Готово. Тепер можна{" "}
          <Link className="link" href="/login">
            увійти
          </Link>
          .
        </Notice>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title="Посилання не спрацювало"
      footer={
        <>
          <Link href="/register">Надіслати новий лист</Link> · <Link href="/login">Вхід</Link>
        </>
      }
    >
      <Notice>{state.message}. Можливо, його вже використали або минув термін дії.</Notice>
    </AuthCard>
  );
}

export default function VerifyPage() {
  return (
    <Suspense>
      <Verify />
    </Suspense>
  );
}

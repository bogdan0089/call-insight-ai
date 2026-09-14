"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRole } from "@/components/auth-provider";
import {
  Badge,
  Button,
  Card,
  CardTitle,
  Empty,
  Field,
  Label,
  Notice,
} from "@/components/ui";
import { api, type ApiKey, type ApiKeyCreated } from "@/lib/api";
import { dateTime } from "@/lib/format";
import { API_KEY_NAME_MAX } from "@/lib/limits";
import { canManageApiKeys } from "@/lib/permissions";
import { color } from "@/lib/theme";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8090";

function SecretOnce({ created, onClose }: { created: ApiKeyCreated; onClose: () => void }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(created.secret);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <Card style={{ borderColor: color.accentBorder, marginBottom: 14 }}>
      <div style={{ display: "grid", gap: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontWeight: 700 }}>Ключ «{created.key.name}» створено</div>
            <div style={{ fontSize: 13, color: color.warn, marginTop: 2 }}>
              Скопіюйте його зараз — більше його ніде не побачити, навіть у базі.
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <Button type="button" tone="accent" onClick={copy}>
              {copied ? "Скопійовано" : "Скопіювати"}
            </Button>
            <Button type="button" onClick={onClose}>
              Я зберіг
            </Button>
          </div>
        </div>
        <div className="secret">{created.secret}</div>
        <div style={{ fontSize: 12, color: color.textDim }}>
          Використання:{" "}
          <span className="num">
            curl -H &quot;X-API-Key: {created.secret}&quot; {API_URL}/calls
          </span>
        </div>
      </div>
    </Card>
  );
}

export default function KeysPage() {
  const role = useRole();
  const allowed = canManageApiKeys(role);

  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [name, setName] = useState("");
  const [created, setCreated] = useState<ApiKeyCreated | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState<number | null>(null);

  useEffect(() => {
    if (!allowed) return;
    let alive = true;
    api
      .listApiKeys()
      .then((list) => alive && setKeys(list))
      .catch((err: unknown) => alive && setError(err instanceof Error ? err.message : "Ключі не завантажились"))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [allowed]);

  async function create(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await api.createApiKey(name.trim());
      setCreated(result);
      setKeys((prev) => [result.key, ...prev]);
      setName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не вдалося створити ключ");
    } finally {
      setBusy(false);
    }
  }

  async function revoke(key: ApiKey) {
    setBusy(true);
    setError(null);
    try {
      const updated = await api.revokeApiKey(key.id);
      setKeys((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не вдалося відкликати");
    } finally {
      setBusy(false);
      setConfirming(null);
    }
  }

  if (!allowed) {
    return (
      <div style={{ marginTop: 32 }}>
        <Notice tone="warn">Ключі API видає тільки власник компанії.</Notice>
      </div>
    );
  }

  return (
    <>
      <header className="page-head">
        <div>
          <h1 className="page-title">Ключі API</h1>
          <p className="page-sub">
            Для підключення CRM, телефонії чи власних скриптів. Ключ бачить усі дзвінки компанії.
          </p>
        </div>
      </header>

      {error ? (
        <div style={{ marginBottom: 14 }}>
          <Notice>{error}</Notice>
        </div>
      ) : null}
      {created ? <SecretOnce created={created} onClose={() => setCreated(null)} /> : null}

      <div className="grid grid-split">
        <Card padded={false}>
          <CardTitle aside={<Label>{keys.filter((key) => key.is_active).length} активних</Label>}>
            Видані ключі
          </CardTitle>
          {keys.length === 0 ? (
            <Empty>{loading ? "Читаємо ключі…" : "Ключів ще немає"}</Empty>
          ) : (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>Назва</th>
                    <th>Префікс</th>
                    <th>Останнє використання</th>
                    <th>Стан</th>
                  </tr>
                </thead>
                <tbody>
                  {keys.map((key) => (
                    <tr key={key.id} style={{ opacity: key.is_active ? 1 : 0.55 }}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{key.name}</div>
                        <div style={{ fontSize: 12, color: color.textDim }}>
                          створено {dateTime(key.created_at)}
                        </div>
                      </td>
                      <td className="num" style={{ color: color.textMuted }}>
                        ci_{key.prefix}_…
                      </td>
                      <td className="num" style={{ color: color.textMuted, whiteSpace: "nowrap" }}>
                        {key.last_used_at ? dateTime(key.last_used_at) : "ще не використовувався"}
                      </td>
                      <td>
                        {!key.is_active ? (
                          <Badge tone="fail">відкликано</Badge>
                        ) : confirming === key.id ? (
                          <div style={{ display: "flex", gap: 6 }}>
                            <Button type="button" tone="fail" disabled={busy} onClick={() => void revoke(key)}>
                              Так, відкликати
                            </Button>
                            <Button type="button" disabled={busy} onClick={() => setConfirming(null)}>
                              Ні
                            </Button>
                          </div>
                        ) : (
                          <Button type="button" disabled={busy} onClick={() => setConfirming(key.id)}>
                            Відкликати
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card padded={false}>
          <CardTitle>Новий ключ</CardTitle>
          <form className="form" style={{ padding: "16px 20px 20px" }} onSubmit={create} noValidate>
            <Field label="Для чого" hint="Наприклад: «CRM» або «Binotel». Назва лише для вас.">
              <input
                className="field"
                maxLength={API_KEY_NAME_MAX}
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </Field>
            <Button tone="accent" type="submit" disabled={busy || !name.trim()}>
              {busy ? "Створюємо…" : "Створити ключ"}
            </Button>
            <div style={{ fontSize: 12, color: color.textDim, lineHeight: 1.6 }}>
              Відкликання діє одразу: наступний запит із цим ключем отримає 401.
            </div>
          </form>
        </Card>
      </div>
    </>
  );
}

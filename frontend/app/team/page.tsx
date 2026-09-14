"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { useProfile } from "@/components/auth-provider";
import {
  Badge,
  Button,
  Card,
  CardTitle,
  Empty,
  Field,
  Notice,
  SortHeader,
} from "@/components/ui";
import {
  api,
  type PeoplePage,
  type PeopleSortField,
  type Person,
  type Role,
} from "@/lib/api";
import { fullDate } from "@/lib/format";
import { EMAIL_MAX, NAME_MAX, PAGE_SIZE } from "@/lib/limits";
import {
  INVITABLE_ROLES,
  ROLE_LABEL,
  canChangeRoles,
  canManagePeople,
} from "@/lib/permissions";
import { color } from "@/lib/theme";
import { useSort } from "@/lib/use-sort";

const DESC_FIRST: readonly PeopleSortField[] = ["created_at"];

interface InviteForm {
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  manager_id: string;
}

const EMPTY_INVITE: InviteForm = {
  email: "",
  first_name: "",
  last_name: "",
  role: "operator",
  manager_id: "",
};

function InvitePanel({
  actorRole,
  managers,
  onDone,
}: {
  actorRole: Role;
  managers: Person[];
  onDone: (person: Person) => void;
}) {
  const [form, setForm] = useState<InviteForm>(EMPTY_INVITE);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const wholeOrg = canChangeRoles(actorRole);
  const roles = wholeOrg ? INVITABLE_ROLES : (["operator"] as Role[]);

  function change<K extends keyof InviteForm>(key: K, value: InviteForm[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const person = await api.invitePerson({
        email: form.email.trim(),
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        role: form.role,
        manager_id: wholeOrg && form.manager_id ? Number(form.manager_id) : null,
      });
      setForm(EMPTY_INVITE);
      onDone(person);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не вдалося запросити");
    } finally {
      setBusy(false);
    }
  }

  const ready = form.email.trim() && form.first_name.trim() && form.last_name.trim();

  return (
    <Card padded={false}>
      <CardTitle>Запросити людину</CardTitle>
      <form className="form" style={{ padding: "16px 20px 20px" }} onSubmit={submit} noValidate>
        {error ? <Notice>{error}</Notice> : null}

        <div className="form-row">
          <Field label="Імʼя">
            <input
              className="field"
              maxLength={NAME_MAX}
              value={form.first_name}
              onChange={(event) => change("first_name", event.target.value)}
            />
          </Field>
          <Field label="Прізвище">
            <input
              className="field"
              maxLength={NAME_MAX}
              value={form.last_name}
              onChange={(event) => change("last_name", event.target.value)}
            />
          </Field>
        </div>

        <Field label="Пошта" hint="Сюди прийде лист із посиланням, щоб задати пароль">
          <input
            className="field"
            type="email"
            maxLength={EMAIL_MAX}
            value={form.email}
            onChange={(event) => change("email", event.target.value)}
          />
        </Field>

        <div className="form-row">
          <Field label="Роль">
            <select
              className="field"
              value={form.role}
              disabled={roles.length === 1}
              onChange={(event) => change("role", event.target.value as Role)}
            >
              {roles.map((role) => (
                <option key={role} value={role}>
                  {ROLE_LABEL[role]}
                </option>
              ))}
            </select>
          </Field>

          {wholeOrg && form.role === "operator" ? (
            <Field label="Керівник">
              <select
                className="field"
                value={form.manager_id}
                onChange={(event) => change("manager_id", event.target.value)}
              >
                <option value="">без керівника</option>
                {managers.map((manager) => (
                  <option key={manager.id} value={manager.id}>
                    {manager.full_name}
                  </option>
                ))}
              </select>
            </Field>
          ) : (
            <Field label="Керівник">
              <input
                className="field"
                disabled
                value={wholeOrg ? "не потрібен для цієї ролі" : "ви"}
              />
            </Field>
          )}
        </div>

        <Button tone="accent" type="submit" disabled={busy || !ready}>
          {busy ? "Надсилаємо…" : "Надіслати запрошення"}
        </Button>
      </form>
    </Card>
  );
}

export default function TeamPage() {
  const { user } = useProfile();
  const [offset, setOffset] = useState(0);
  const resetPage = useCallback(() => setOffset(0), []);
  const sort = useSort<PeopleSortField>("name", "asc", DESC_FIRST, resetPage);

  const [roleFilter, setRoleFilter] = useState<Role | "">("");
  const [activeFilter, setActiveFilter] = useState<"" | "true" | "false">("");
  const [page, setPage] = useState<PeoplePage | null>(null);
  const [managers, setManagers] = useState<Person[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<number | null>(null);
  const [version, setVersion] = useState(0);

  const allowed = canManagePeople(user.role);
  const wholeOrg = canChangeRoles(user.role);

  useEffect(() => {
    if (!allowed) return;
    let alive = true;

    async function run() {
      setLoading(true);
      try {
        const [people, managerList] = await Promise.all([
          api.listPeople({
            role: roleFilter || null,
            is_active: activeFilter === "" ? null : activeFilter === "true",
            sort_by: sort.sortBy,
            order: sort.order,
            limit: PAGE_SIZE,
            offset,
          }),
          wholeOrg
            ? api.listPeople({ role: "manager", is_active: true, limit: 100 })
            : Promise.resolve(null),
        ]);
        if (!alive) return;
        setPage(people);
        if (managerList) setManagers(managerList.items);
        setError(null);
      } catch (err) {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "Команда не завантажилась");
      } finally {
        if (alive) setLoading(false);
      }
    }

    void run();
    return () => {
      alive = false;
    };
  }, [allowed, wholeOrg, roleFilter, activeFilter, sort.sortBy, sort.order, offset, version]);

  const shown = useMemo(() => {
    if (!page || page.total === 0) return "0";
    return `${page.offset + 1}–${page.offset + page.items.length} з ${page.total}`;
  }, [page]);

  async function update(person: Person, patch: Parameters<typeof api.updatePerson>[1]) {
    setPending(person.id);
    setError(null);
    try {
      const updated = await api.updatePerson(person.id, patch);
      setPage((prev) =>
        prev
          ? { ...prev, items: prev.items.map((item) => (item.id === updated.id ? updated : item)) }
          : prev,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не вдалося змінити");
    } finally {
      setPending(null);
    }
  }

  if (!allowed) {
    return (
      <div style={{ marginTop: 32 }}>
        <Notice tone="warn">Керувати командою можуть власник, адміністратор і керівник.</Notice>
      </div>
    );
  }

  return (
    <>
      <header className="page-head">
        <div>
          <h1 className="page-title">Команда</h1>
          <p className="page-sub">
            {wholeOrg ? "Усі люди компанії" : "Ви і ваші оператори"} · {shown}
          </p>
        </div>
      </header>

      {error ? <Notice>{error}</Notice> : null}
      {notice ? (
        <div style={{ marginBottom: 14 }}>
          <Notice tone="pass">{notice}</Notice>
        </div>
      ) : null}

      <div className="grid grid-wide">
        <Card padded={false}>
          <CardTitle
            aside={
              <div style={{ display: "flex", gap: 8 }}>
                <select
                  className="field"
                  style={{ width: "auto" }}
                  value={roleFilter}
                  aria-label="Фільтр за роллю"
                  onChange={(event) => {
                    setOffset(0);
                    setRoleFilter(event.target.value as Role | "");
                  }}
                >
                  <option value="">усі ролі</option>
                  {(["owner", ...INVITABLE_ROLES] as Role[]).map((role) => (
                    <option key={role} value={role}>
                      {ROLE_LABEL[role]}
                    </option>
                  ))}
                </select>
                <select
                  className="field"
                  style={{ width: "auto" }}
                  value={activeFilter}
                  aria-label="Фільтр за доступом"
                  onChange={(event) => {
                    setOffset(0);
                    setActiveFilter(event.target.value as "" | "true" | "false");
                  }}
                >
                  <option value="">будь-який доступ</option>
                  <option value="true">активні</option>
                  <option value="false">вимкнені</option>
                </select>
              </div>
            }
          >
            Люди
          </CardTitle>

          {!page || page.items.length === 0 ? (
            <Empty>{loading ? "Читаємо команду…" : "Нікого не знайдено"}</Empty>
          ) : (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <SortHeader field="name" label="Людина" {...sort.header} />
                    <SortHeader field="role" label="Роль" {...sort.header} />
                    <th>Керівник</th>
                    <SortHeader field="created_at" label="Додано" {...sort.header} />
                    <th>Доступ</th>
                  </tr>
                </thead>
                <tbody>
                  {page.items.map((person) => {
                    const self = person.id === user.id;
                    const busy = pending === person.id;
                    const editableRole = wholeOrg && !self && person.role !== "owner";
                    return (
                      <tr key={person.id} style={{ opacity: person.is_active ? 1 : 0.55 }}>
                        <td>
                          <div style={{ fontWeight: 600 }}>
                            {person.full_name}
                            {self ? (
                              <span style={{ color: color.textDim, fontWeight: 400 }}> · ви</span>
                            ) : null}
                          </div>
                          <div style={{ fontSize: 12, color: color.textDim }}>{person.email}</div>
                        </td>
                        <td>
                          {editableRole ? (
                            <select
                              className="field"
                              style={{ width: "auto" }}
                              value={person.role}
                              disabled={busy}
                              aria-label={`Роль: ${person.full_name}`}
                              onChange={(event) =>
                                void update(person, { role: event.target.value as Role })
                              }
                            >
                              {INVITABLE_ROLES.map((role) => (
                                <option key={role} value={role}>
                                  {ROLE_LABEL[role]}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <Badge tone={person.role === "owner" ? "accent" : "neutral"}>
                              {ROLE_LABEL[person.role]}
                            </Badge>
                          )}
                        </td>
                        <td style={{ color: person.manager_name ? color.text : color.textDim }}>
                          {person.manager_name ?? "—"}
                        </td>
                        <td className="num" style={{ color: color.textMuted, whiteSpace: "nowrap" }}>
                          {fullDate(person.created_at)}
                        </td>
                        <td>
                          {!person.is_verified ? (
                            <Badge tone="warn">запрошено</Badge>
                          ) : self ? (
                            <Badge tone="pass">активний</Badge>
                          ) : (
                            <Button
                              type="button"
                              tone={person.is_active ? "neutral" : "pass"}
                              disabled={busy}
                              onClick={() => void update(person, { is_active: !person.is_active })}
                            >
                              {person.is_active ? "Вимкнути" : "Увімкнути"}
                            </Button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {page && page.total > PAGE_SIZE ? (
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: 8,
                padding: "12px 20px",
                borderTop: `1px solid ${color.border}`,
              }}
            >
              <Button
                type="button"
                disabled={offset === 0 || loading}
                onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
              >
                Назад
              </Button>
              <Button
                type="button"
                disabled={offset + PAGE_SIZE >= page.total || loading}
                onClick={() => setOffset((value) => value + PAGE_SIZE)}
              >
                Далі
              </Button>
            </div>
          ) : null}
        </Card>

        <InvitePanel
          actorRole={user.role}
          managers={managers}
          onDone={(person) => {
            setNotice(`Запрошення надіслано на ${person.email}`);
            setVersion((value) => value + 1);
          }}
        />
      </div>
    </>
  );
}

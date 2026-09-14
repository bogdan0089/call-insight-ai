"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRole } from "@/components/auth-provider";
import { STATUS_META, StatusBadge } from "@/components/status-badge";
import { Button, Card, CardTitle, Empty, Label, Meter, Notice, SortHeader } from "@/components/ui";
import {
  CALL_STATUSES,
  api,
  type CallFilters,
  type CallPage,
  type CallSortField,
  type Person,
} from "@/lib/api";
import { dateTime, duration, num, score } from "@/lib/format";
import { PAGE_SIZE } from "@/lib/limits";
import { canManagePeople } from "@/lib/permissions";
import { color, scoreTone } from "@/lib/theme";
import { useSort } from "@/lib/use-sort";

const DESC_FIRST: readonly CallSortField[] = ["created_at", "total_score", "duration_sec"];


const EMPTY: CallFilters = {
  operator_id: null,
  status: null,
  created_from: null,
  created_to: null,
  score_min: null,
  score_max: null,
};

function endOfDay(value: string | null | undefined): string | null {
  if (!value) return null;
  return value.length === 10 ? `${value}T23:59:59` : value;
}

function CallsView() {
  const params = useSearchParams();
  const fromLink: CallFilters = {
    ...EMPTY,
    created_from: params.get("created_from"),
    created_to: params.get("created_to"),
  };

  const [filters, setFilters] = useState<CallFilters>(fromLink);
  const [applied, setApplied] = useState<CallFilters>(fromLink);
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<CallPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [operators, setOperators] = useState<Person[]>([]);

  const role = useRole();
  const pickOperator = canManagePeople(role);

  const resetPage = useCallback(() => setOffset(0), []);
  const sort = useSort<CallSortField>("created_at", "desc", DESC_FIRST, resetPage);

  const requestKey = JSON.stringify({ applied, offset, by: sort.sortBy, order: sort.order });
  const [loadedFor, setLoadedFor] = useState<string | null>(null);
  const loading = loadedFor !== requestKey;

  useEffect(() => {
    if (!pickOperator) return;
    let alive = true;
    api
      .listPeople({ role: "operator", limit: 100, sort_by: "name", order: "asc" })
      .then((result) => {
        if (alive) setOperators(result.items);
      })
      .catch(() => {
      });
    return () => {
      alive = false;
    };
  }, [pickOperator]);

  useEffect(() => {
    let alive = true;

    async function run() {
      try {
        const result = await api.listCalls({
          ...applied,
          created_to: endOfDay(applied.created_to),
          limit: PAGE_SIZE,
          offset,
          sort_by: sort.sortBy,
          order: sort.order,
        });
        if (!alive) return;
        setPage(result);
        setError(null);
      } catch (err) {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "Список не завантажився");
        setPage(null);
      } finally {
        if (alive) setLoadedFor(requestKey);
      }
    }

    void run();
    return () => {
      alive = false;
    };
  }, [applied, offset, sort.sortBy, sort.order, requestKey]);

  const shown = useMemo(() => {
    if (!page || page.total === 0) return "0";
    return `${page.offset + 1}–${page.offset + page.items.length} з ${page.total}`;
  }, [page]);

  function change<K extends keyof CallFilters>(key: K, value: CallFilters[K]) {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }

  function apply() {
    setOffset(0);
    setApplied(filters);
  }

  function reset() {
    setFilters(EMPTY);
    setApplied(EMPTY);
    setOffset(0);
  }

  return (
    <>
      <header className="page-head">
        <div>
          <h1 className="page-title">Дзвінки</h1>
          <p className="page-sub">Фільтри рахує база — на клієнт їде тільки сторінка</p>
        </div>
        <Label>{loading ? "завантаження…" : shown}</Label>
      </header>

      <Card style={{ marginBottom: 14 }}>
        <div
          className="grid"
          style={{ gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}
        >
          {pickOperator ? (
            <FilterField label="Оператор">
              <select
                className="field"
                value={filters.operator_id ?? ""}
                onChange={(e) =>
                  change("operator_id", e.target.value ? Number(e.target.value) : null)
                }
              >
                <option value="">усі</option>
                {operators.map((operator) => (
                  <option key={operator.id} value={operator.id}>
                    {operator.full_name}
                  </option>
                ))}
              </select>
            </FilterField>
          ) : null}

          <FilterField label="Статус">
            <select
              className="field"
              value={filters.status ?? ""}
              onChange={(e) =>
                change("status", e.target.value ? (e.target.value as CallFilters["status"]) : null)
              }
            >
              <option value="">усі</option>
              {CALL_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {STATUS_META[status].text}
                </option>
              ))}
            </select>
          </FilterField>

          <FilterField label="Дата від">
            <input
              className="field"
              type="date"
              value={filters.created_from ?? ""}
              onChange={(e) => change("created_from", e.target.value || null)}
            />
          </FilterField>

          <FilterField label="Дата до">
            <input
              className="field"
              type="date"
              value={filters.created_to ?? ""}
              onChange={(e) => change("created_to", e.target.value || null)}
            />
          </FilterField>

          <FilterField label="Бал від">
            <input
              className="field"
              type="number"
              min={0}
              max={100}
              value={filters.score_min ?? ""}
              onChange={(e) => change("score_min", e.target.value ? Number(e.target.value) : null)}
              placeholder="0"
            />
          </FilterField>

          <FilterField label="Бал до">
            <input
              className="field"
              type="number"
              min={0}
              max={100}
              value={filters.score_max ?? ""}
              onChange={(e) => change("score_max", e.target.value ? Number(e.target.value) : null)}
              placeholder="100"
            />
          </FilterField>
        </div>

        <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
          <Button tone="accent" onClick={apply}>
            Застосувати
          </Button>
          <Button onClick={reset}>Скинути</Button>
          {filters.score_min !== null || filters.score_max !== null ? (
            <span style={{ alignSelf: "center", fontSize: 12, color: color.warn }}>
              фільтр за балом ховає ще не оцінені дзвінки
            </span>
          ) : null}
        </div>
      </Card>

      {error ? <Notice>{error}</Notice> : null}

      <Card padded={false}>
        <CardTitle aside={<Label>{shown}</Label>}>Результат</CardTitle>

        {!page || page.items.length === 0 ? (
          <Empty>{loading ? "Читаємо базу…" : "Нічого не знайшлось за цими фільтрами"}</Empty>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>#</th>
                  <SortHeader field="created_at" label="Створено" {...sort.header} />
                  <SortHeader field="operator" label="Оператор" {...sort.header} />
                  <SortHeader field="status" label="Статус" {...sort.header} />
                  <SortHeader field="duration_sec" label="Тривалість" {...sort.header} />
                  <SortHeader field="total_score" label="Бал" {...sort.header} />
                  <th />
                </tr>
              </thead>
              <tbody>
                {page.items.map((call) => {
                  const value = num(call.total_score);
                  return (
                    <tr key={call.id}>
                      <td className="num" style={{ color: color.textDim }}>
                        {call.id}
                      </td>
                      <td className="num">{dateTime(call.created_at)}</td>
                      <td>{call.operator_name ?? <span style={{ color: color.textFaint }}>—</span>}</td>
                      <td>
                        <StatusBadge status={call.status} />
                      </td>
                      <td className="num">{duration(call.duration_sec)}</td>
                      <td style={{ minWidth: 130 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <span className="num" style={{ width: 46 }}>
                            {score(call.total_score)}
                          </span>
                          <Meter value={value} tone={scoreTone(value)} />
                        </div>
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <Link href={`/calls/${call.id}`} className="btn link-button">
                          Розбір
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <footer
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: 10,
            padding: "14px 20px",
            borderTop: `1px solid ${color.border}`,
          }}
        >
          <Button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
            Назад
          </Button>
          <Button disabled={!page?.has_more} onClick={() => setOffset(offset + PAGE_SIZE)}>
            Далі
          </Button>
        </footer>
      </Card>
    </>
  );
}

export default function CallsPage() {
  return (
    <Suspense>
      <CallsView />
    </Suspense>
  );
}

function FilterField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <Label>{label}</Label>
      {children}
    </label>
  );
}

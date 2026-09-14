"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { DailyChart, type DayPoint } from "@/components/daily-chart";
import { Card, CardTitle, Empty, Label, Meter, Notice, SortHeader, Stat } from "@/components/ui";
import {
  api,
  type SortOrder,
  type ChecklistSortField,
  type ChecklistStats,
  type DailyStats,
  type OperatorSortField,
  type OperatorStats,
} from "@/lib/api";
import { isoDay, num, percent, score } from "@/lib/format";
import { color, scoreTone } from "@/lib/theme";
import { useSort } from "@/lib/use-sort";

const OPERATOR_DESC_FIRST: readonly OperatorSortField[] = [
  "calls_total",
  "calls_scored",
  "avg_score",
  "min_score",
  "max_score",
  "failed_required",
  "failed_required_rate",
];
const CHECKLIST_DESC_FIRST: readonly ChecklistSortField[] = ["weight", "scored", "passed"];
const CHART_DAYS = 14;

function sortRows<T>(rows: T[], value: (row: T) => number | string | null, order: SortOrder): T[] {
  const sign = order === "asc" ? 1 : -1;
  return [...rows].sort((left, right) => {
    const a = value(left);
    const b = value(right);
    if (a === null && b === null) return 0;
    if (a === null) return 1;
    if (b === null) return -1;
    if (typeof a === "string" || typeof b === "string") {
      return String(a).localeCompare(String(b), "uk") * sign;
    }
    return (a - b) * sign;
  });
}

const OPERATOR_VALUE: Record<OperatorSortField, (row: OperatorStats) => number | string | null> = {
  operator_name: (row) => {
    const parts = row.operator_name.trim().split(/\s+/);
    return [...parts.slice(1), parts[0]].join(" ").toLocaleLowerCase("uk");
  },
  calls_total: (row) => row.calls_total,
  calls_scored: (row) => row.calls_scored,
  avg_score: (row) => num(row.avg_score),
  min_score: (row) => num(row.min_score),
  max_score: (row) => num(row.max_score),
  failed_required: (row) => row.failed_required,
  failed_required_rate: (row) => row.failed_required_rate,
};

const CHECKLIST_VALUE: Record<ChecklistSortField, (row: ChecklistStats) => number | string | null> = {
  code: (row) => row.code,
  title: (row) => row.title.toLocaleLowerCase("uk"),
  weight: (row) => num(row.weight),
  scored: (row) => row.scored,
  passed: (row) => row.passed,
  pass_rate: (row) => row.pass_rate,
};

function defaultRange(): { from: string; to: string } {
  const to = new Date();
  const from = new Date();
  from.setDate(to.getDate() - (CHART_DAYS - 1));
  return { from: isoDay(from), to: isoDay(to) };
}

export default function OverviewPage() {
  const [operators, setOperators] = useState<OperatorStats[]>([]);
  const [checklist, setChecklist] = useState<ChecklistStats[]>([]);
  const [daily, setDaily] = useState<DailyStats[]>([]);
  const [day, setDay] = useState<DayPoint | null>(null);
  const [range, setRange] = useState(defaultRange);

  const rangeKey = `${range.from}:${range.to}`;
  const [dailyFor, setDailyFor] = useState<string | null>(null);
  const dailyLoading = dailyFor !== rangeKey;
  const selectedDay = day && day.day >= range.from && day.day <= range.to ? day : null;
  const [error, setError] = useState<string | null>(null);
  const operatorSort = useSort<OperatorSortField>("avg_score", "desc", OPERATOR_DESC_FIRST);
  const checklistSort = useSort<ChecklistSortField>("pass_rate", "asc", CHECKLIST_DESC_FIRST);

  const [operatorsLoaded, setOperatorsLoaded] = useState(false);
  const [checklistLoaded, setChecklistLoaded] = useState(false);
  const loadingOperators = !operatorsLoaded;
  const loadingChecklist = !checklistLoaded;
  const loading = loadingOperators || loadingChecklist;

  useEffect(() => {
    let alive = true;

    api
      .dailyStats({
        created_from: `${range.from}T00:00:00`,
        created_to: `${range.to}T23:59:59`,
      })
      .then((rows) => {
        if (alive) setDaily(rows);
      })
      .catch(() => {
      })
      .finally(() => {
        if (alive) setDailyFor(rangeKey);
      });
    return () => {
      alive = false;
    };
  }, [range, rangeKey]);

  useEffect(() => {
    let alive = true;
    api
      .operatorStats()
      .then((rows) => {
        if (!alive) return;
        setOperators(rows);
        setError(null);
      })
      .catch((err: unknown) => {
        if (alive) setError(err instanceof Error ? err.message : "Статистика не завантажилась");
      })
      .finally(() => {
        if (alive) setOperatorsLoaded(true);
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    let alive = true;
    api
      .checklistStats()
      .then((rows) => {
        if (alive) setChecklist(rows);
      })
      .catch((err: unknown) => {
        if (alive) setError(err instanceof Error ? err.message : "Статистика не завантажилась");
      })
      .finally(() => {
        if (alive) setChecklistLoaded(true);
      });
    return () => {
      alive = false;
    };
  }, []);

  const shownOperators = useMemo(
    () => sortRows(operators, OPERATOR_VALUE[operatorSort.sortBy], operatorSort.order),
    [operators, operatorSort.sortBy, operatorSort.order],
  );
  const shownChecklist = useMemo(
    () => sortRows(checklist, CHECKLIST_VALUE[checklistSort.sortBy], checklistSort.order),
    [checklist, checklistSort.sortBy, checklistSort.order],
  );

  const callsTotal = operators.reduce((acc, row) => acc + row.calls_total, 0);
  const scoredTotal = operators.reduce((acc, row) => acc + row.calls_scored, 0);
  const failedTotal = operators.reduce((acc, row) => acc + row.failed_required, 0);
  const weightedAvg =
    scoredTotal === 0
      ? null
      : operators.reduce((acc, row) => acc + (num(row.avg_score) ?? 0) * row.calls_scored, 0) /
        scoredTotal;

  return (
    <>
      <header className="page-head">
        <div>
          <h1 className="page-title">Огляд якості</h1>
          <p className="page-sub">Зведення по операторах і пунктах чекліста</p>
        </div>
      </header>

      {error ? <Notice>{error}</Notice> : null}

      <div className="grid grid-stats" style={{ marginBottom: 14 }}>
        <Stat
          label="Дзвінків"
          value={loadingOperators ? "—" : callsTotal}
          hint={loadingOperators ? "завантаження" : scoredTotal + " з оцінкою"}
        />
        <Stat
          label="Середній бал"
          value={loadingOperators || weightedAvg === null ? "—" : weightedAvg.toFixed(2)}
          hint="зважено за кількістю оцінених"
          tone={loadingOperators ? "neutral" : scoreTone(weightedAvg)}
        />
        <Stat
          label="Провалено важливих"
          value={loadingOperators ? "—" : failedTotal}
          hint={!loadingOperators && callsTotal ? percent(failedTotal / callsTotal) : "—"}
          tone={loadingOperators ? "neutral" : failedTotal > 0 ? "fail" : "pass"}
        />
        <Stat
          label="Операторів"
          value={loadingOperators ? "—" : operators.length}
          hint="із дзвінками за період"
        />
      </div>

      <Card padded={false} style={{ marginBottom: 14 }}>
        <CardTitle
          aside={
            <div className="range-picker">
              <input
                className="field"
                type="date"
                aria-label="Період від"
                value={range.from}
                max={range.to}
                onChange={(event) =>
                  setRange((current) => ({ ...current, from: event.target.value || current.from }))
                }
              />
              <span>—</span>
              <input
                className="field"
                type="date"
                aria-label="Період до"
                value={range.to}
                min={range.from}
                onChange={(event) =>
                  setRange((current) => ({ ...current, to: event.target.value || current.to }))
                }
              />
              <button type="button" className="btn nav-exit" onClick={() => setRange(defaultRange())}>
                {CHART_DAYS} днів
              </button>
            </div>
          }
        >
          Динаміка по днях
        </CardTitle>
        {dailyLoading ? (
          <Empty>Читаємо статистику…</Empty>
        ) : (
          <DailyChart
            rows={daily}
            from={range.from}
            to={range.to}
            selected={selectedDay?.day ?? null}
            onSelect={(point) => setDay((current) => (current?.day === point.day ? null : point))}
          />
        )}
        {selectedDay ? (
          <div className="day-panel">
            <div className="day-panel-numbers">
              <span>
                <b>{selectedDay.label}</b>
              </span>
              <span>
                дзвінків <b className="num">{selectedDay.calls}</b>
              </span>
              <span>
                з оцінкою <b className="num">{selectedDay.scored}</b>
              </span>
              <span>
                середній{" "}
                <b className="num" style={{ color: color.text }}>
                  {selectedDay.score === null ? "—" : selectedDay.score.toFixed(2)}
                </b>
              </span>
              <span>
                провалено важливих{" "}
                <b className="num" style={{ color: selectedDay.failed ? color.fail : color.textDim }}>
                  {selectedDay.failed}
                </b>
              </span>
            </div>
            {selectedDay.calls > 0 ? (
              <Link
                className="btn link-button"
                href={`/calls?created_from=${selectedDay.day}&created_to=${selectedDay.day}`}
              >
                Показати дзвінки
              </Link>
            ) : null}
          </div>
        ) : null}
      </Card>

      <div className="grid grid-split">
        <Card padded={false}>
          <CardTitle
            aside={<Label>{loadingOperators ? "завантаження" : operators.length + " рядків"}</Label>}
          >
            Оператори
          </CardTitle>
          {operators.length === 0 ? (
            <Empty>{loading ? "Читаємо статистику…" : "Дзвінків із операторами ще немає"}</Empty>
          ) : (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <SortHeader field="operator_name" label="Оператор" {...operatorSort.header} />
                    <SortHeader field="calls_total" label="Дзвінків" {...operatorSort.header} />
                    <SortHeader field="avg_score" label="Середній" {...operatorSort.header} />
                    <SortHeader field="min_score" label="Діапазон" {...operatorSort.header} />
                    <SortHeader
                      field="failed_required_rate"
                      label="Провали"
                      {...operatorSort.header}
                    />
                  </tr>
                </thead>
                <tbody>
                  {shownOperators.map((row) => {
                    const avg = num(row.avg_score);
                    return (
                      <tr key={row.operator_id}>
                        <td style={{ fontWeight: 600, whiteSpace: "nowrap" }}>
                          {row.operator_name}
                        </td>
                        <td className="num">
                          {row.calls_total}
                          <span style={{ color: color.textFaint }}> / {row.calls_scored}</span>
                        </td>
                        <td style={{ minWidth: 130 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <span className="num" style={{ width: 46 }}>
                              {score(row.avg_score)}
                            </span>
                            <Meter value={avg} tone={scoreTone(avg)} />
                          </div>
                        </td>
                        <td
                          className="num"
                          style={{ color: color.textMuted, whiteSpace: "nowrap" }}
                        >
                          {score(row.min_score)}–{score(row.max_score)}
                        </td>
                        <td
                          className="num"
                          style={{
                            color: row.failed_required ? color.fail : color.textDim,
                            whiteSpace: "nowrap",
                          }}
                        >
                          {row.failed_required} · {percent(row.failed_required_rate)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <Card padded={false}>
          <CardTitle aside={<Label>{loadingChecklist ? "завантаження" : checklist.length + " пунктів"}</Label>}>
            Пункти чекліста
          </CardTitle>
          {checklist.length === 0 ? (
            <Empty>{loading ? "Читаємо статистику…" : "Оцінок ще немає"}</Empty>
          ) : (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <SortHeader field="title" label="Пункт" {...checklistSort.header} />
                    <SortHeader field="weight" label="Вага" {...checklistSort.header} />
                    <SortHeader field="pass_rate" label="Пройдено" {...checklistSort.header} />
                  </tr>
                </thead>
                <tbody>
                  {shownChecklist.map((item) => {
                    const rate = item.pass_rate === null ? null : item.pass_rate * 100;
                    return (
                      <tr key={item.checklist_item_id}>
                        <td>
                          <div style={{ fontWeight: 600 }}>{item.title}</div>
                          <div
                            style={{
                              fontSize: 11,
                              color: color.textFaint,
                              fontFamily: "var(--mono)",
                            }}
                          >
                            {item.code}
                            {item.is_required ? " · важливий" : ""}
                          </div>
                        </td>
                        <td className="num">{num(item.weight)}</td>
                        <td style={{ minWidth: 140 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <span className="num" style={{ width: 64 }}>
                              {item.passed}/{item.scored}
                            </span>
                            <Meter value={rate} tone={scoreTone(rate)} />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </>
  );
}

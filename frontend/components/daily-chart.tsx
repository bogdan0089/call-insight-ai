"use client";

import { useMemo } from "react";
import { Empty } from "@/components/ui";
import type { DailyStats } from "@/lib/api";
import { num } from "@/lib/format";
import { color } from "@/lib/theme";

export interface DayPoint {
  day: string;
  label: string;
  calls: number;
  scored: number;
  score: number | null;
  failed: number;
}

function dayKey(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(
    date.getDate(),
  ).padStart(2, "0")}`;
}

function buildDays(rows: DailyStats[], from: string, to: string): DayPoint[] {
  const byDay = new Map(rows.map((row) => [row.day, row]));
  const start = new Date(`${from}T00:00:00`);
  const end = new Date(`${to}T00:00:00`);
  const points: DayPoint[] = [];

  for (let date = start; date <= end; date.setDate(date.getDate() + 1)) {
    const key = dayKey(date);
    const row = byDay.get(key);
    points.push({
      day: key,
      label: `${key.slice(8, 10)}.${key.slice(5, 7)}`,
      calls: row?.calls_total ?? 0,
      scored: row?.calls_scored ?? 0,
      score: row ? num(row.avg_score) : null,
      failed: row?.failed_required ?? 0,
    });
  }

  return points;
}

export function DailyChart({
  rows,
  from,
  to,
  selected,
  onSelect,
}: {
  rows: DailyStats[];
  from: string;
  to: string;
  selected?: string | null;
  onSelect?: (point: DayPoint) => void;
}) {
  const points = useMemo(() => buildDays(rows, from, to), [rows, from, to]);
  const maxCalls = Math.max(...points.map((point) => point.calls), 1);

  if (points.every((point) => point.calls === 0)) {
    return <Empty>За цей період дзвінків не було</Empty>;
  }

  const scored = points
    .map((point, index) => ({ point, index }))
    .filter((item) => item.point.score !== null);

  const line = scored
    .map(
      ({ point, index }) =>
        `${((index + 0.5) / points.length) * 100},${100 - (point.score ?? 0)}`,
    )
    .join(" ");

  return (
    <div className="chart">
      <div className="chart-legend">
        <span>
          <i style={{ background: color.accentSoft, borderColor: color.accentBorder }} />
          стовпчики — скільки дзвінків за день
        </span>
        <span>
          <i className="line" style={{ background: color.pass }} />
          лінія — середній бал за день
        </span>
      </div>

      <div className="chart-body">
        <div className="chart-grid" aria-hidden>
          {[100, 75, 50, 25, 0].map((value) => (
            <div key={value}>
              <span>{Math.round((maxCalls * value) / 100)}</span>
              <span className="right">{value}</span>
            </div>
          ))}
        </div>

        <div className="chart-bars">
          {points.map((point) => (
            <button
              type="button"
              key={point.day}
              className="chart-col"
              data-selected={selected === point.day}
              aria-label={`${point.label}: ${point.calls} дзвінків`}
              onClick={() => onSelect?.(point)}
            >
              <span
                className="chart-bar"
                style={{ height: `${(point.calls / maxCalls) * 100}%` }}
              />
            </button>
          ))}
        </div>

        <svg
          className="chart-line"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          aria-hidden
        >
          {scored.length > 1 ? (
            <polyline
              points={line}
              fill="none"
              stroke={color.pass}
              strokeWidth="2"
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
        </svg>

        <div className="chart-dots" aria-hidden>
          {scored.map(({ point, index }) => (
            <span
              key={point.day}
              style={{
                left: `${((index + 0.5) / points.length) * 100}%`,
                top: `${100 - (point.score ?? 0)}%`,
              }}
            />
          ))}
        </div>
      </div>

      <div className="chart-axes" aria-hidden>
        <span>дзвінків</span>
        <span className="right">бал</span>
      </div>

      <div className="chart-days">
        {points.map((point, index) => {
          const step = Math.ceil(points.length / 16);
          const visible = index % step === 0 || index === points.length - 1;
          return (
            <span key={point.day} data-selected={selected === point.day}>
              {visible ? point.label : ""}
            </span>
          );
        })}
      </div>
    </div>
  );
}

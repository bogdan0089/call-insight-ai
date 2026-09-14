"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useRole } from "@/components/auth-provider";
import { StatusBadge } from "@/components/status-badge";
import { Badge, Button, Card, CardTitle, Empty, Label, Meter, Notice, Stat } from "@/components/ui";
import { api, type CallReport, type Score, type Segment } from "@/lib/api";
import { dateTime, duration, num, score, timecode } from "@/lib/format";
import { canVerifyScores } from "@/lib/permissions";
import { color, scoreTone } from "@/lib/theme";

export default function CallReportPage() {
  const params = useParams<{ id: string }>();
  const callId = Number(params.id);
  const canVerify = canVerifyScores(useRole());

  const [report, setReport] = useState<CallReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<number | null>(null);
  const [highlight, setHighlight] = useState<string | null>(null);

  useEffect(() => {
    if (!Number.isFinite(callId)) return;
    let alive = true;

    async function run() {
      try {
        const data = await api.getReport(callId);
        if (!alive) return;
        setReport(data);
        setError(null);
      } catch (err) {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "Дзвінок не завантажився");
        setReport(null);
      } finally {
        if (alive) setLoading(false);
      }
    }

    void run();
    return () => {
      alive = false;
    };
  }, [callId]);

  async function toggleVerified(item: Score) {
    setPending(item.id);
    try {
      const updated = await api.verifyScore(callId, item.id, !item.is_verified);
      setReport((prev) =>
        prev
          ? {
              ...prev,
              verified_count: prev.verified_count + (updated.is_verified ? 1 : -1),
              scores: prev.scores.map((s) => (s.id === updated.id ? updated : s)),
            }
          : prev,
      );
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не вдалось зберегти підтвердження");
    } finally {
      setPending(null);
    }
  }

  if (loading) {
    return <Empty>Читаємо розбір…</Empty>;
  }

  if (error && !report) {
    return (
      <>
        <header className="page-head">
          <h1 className="page-title">Дзвінок {callId}</h1>
          <Link href="/calls" className="btn link-button link-button-neutral">
            До списку
          </Link>
        </header>
        <Notice>{error}</Notice>
      </>
    );
  }

  if (!report) return null;

  const total = num(report.total_score);
  const passed = report.scores.filter((s) => s.passed).length;

  return (
    <>
      <header className="page-head">
        <div>
          <h1 className="page-title">
            Дзвінок {report.id}
            {report.operator_name ? (
              <span style={{ color: color.textMuted, fontWeight: 500 }}> · {report.operator_name}</span>
            ) : null}
          </h1>
          <p className="page-sub">
            {dateTime(report.created_at)} · {duration(report.duration_sec)}
            {report.external_id ? ` · ${report.external_id}` : ""}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <StatusBadge status={report.status} />
          <Link href="/calls" className="btn link-button link-button-neutral">
            До списку
          </Link>
        </div>
      </header>

      {error ? <Notice>{error}</Notice> : null}
      {report.error ? <Notice tone="warn">Помилка обробки: {report.error}</Notice> : null}

      <div className="grid grid-stats" style={{ marginBottom: 14 }}>
        <Stat label="Бал" value={score(report.total_score)} tone={scoreTone(total)} hint="зі 100" />
        <Stat
          label="Пунктів пройдено"
          value={`${passed}/${report.scores.length}`}
          hint="за чеклістом"
        />
        <Stat
          label="Важливі пункти"
          value={report.failed_required ? "провал" : "ок"}
          tone={report.failed_required ? "fail" : "pass"}
          hint="обовʼязкові до виконання"
        />
        <Stat
          label="Підтверджено людиною"
          value={report.verified_count}
          tone={report.verified_count > 0 ? "accent" : "neutral"}
          hint="тільки ці йдуть у приклади для LLM"
        />
      </div>

      <div className="grid grid-split">
        <Card padded={false}>
          <CardTitle aside={<Label>{report.scores.length} пунктів</Label>}>Чекліст</CardTitle>
          {report.scores.length === 0 ? (
            <Empty>Дзвінок ще не оцінено</Empty>
          ) : (
            <div style={{ padding: "6px 20px 16px" }}>
              {report.scores.map((item) => (
                <ScoreRow
                  key={item.id}
                  item={item}
                  busy={pending === item.id}
                  canVerify={canVerify}
                  onToggle={() => toggleVerified(item)}
                  onHover={setHighlight}
                />
              ))}
            </div>
          )}
        </Card>

        <Card padded={false}>
          <CardTitle aside={<Label>{report.segments.length} реплік</Label>}>Стенограма</CardTitle>
          {report.segments.length === 0 ? (
            <Empty>
              {report.transcript_text ? "Розшифровка без поділу на репліки" : "Розшифровки ще немає"}
            </Empty>
          ) : (
            <div style={{ padding: "6px 20px 16px" }}>
              {report.segments.map((segment) => (
                <SegmentRow key={segment.idx} segment={segment} highlight={highlight} />
              ))}
            </div>
          )}
        </Card>
      </div>
    </>
  );
}

function ScoreRow({
  item,
  busy,
  canVerify,
  onToggle,
  onHover,
}: {
  item: Score;
  busy: boolean;
  canVerify: boolean;
  onToggle: () => void;
  onHover: (quote: string | null) => void;
}) {
  const confidence = num(item.confidence);

  return (
    <div
      onMouseEnter={() => onHover(item.quote)}
      onMouseLeave={() => onHover(null)}
      style={{
        padding: "14px 0",
        borderBottom: `1px solid ${color.borderSoft}`,
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
        <Badge tone={item.passed ? "pass" : "fail"}>{item.passed ? "так" : "ні"}</Badge>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600 }}>{item.title}</div>
          <div style={{ fontSize: 11, color: color.textFaint, fontFamily: "var(--mono)" }}>
            {item.code} · вага {num(item.weight)}
            {item.is_required ? " · важливий" : ""}
            {confidence !== null ? ` · впевненість ${confidence.toFixed(2)}` : ""}
          </div>
        </div>
        {canVerify ? (
          <Button
            tone={item.is_verified ? "accent" : "neutral"}
            disabled={busy}
            onClick={onToggle}
            title="Підтверджена людиною оцінка потрапляє у приклади для наступних розборів"
          >
            {item.is_verified ? "підтверджено" : "підтвердити"}
          </Button>
        ) : item.is_verified ? (
          <Badge tone="accent">перевірено</Badge>
        ) : null}
      </div>

      {item.quote ? (
        <p className="quote">
          «{item.quote}»
          {item.quote_start_ms !== null ? (
            <span className="num" style={{ color: color.textFaint, fontStyle: "normal" }}>
              {" "}
              {timecode(item.quote_start_ms)}
            </span>
          ) : null}
        </p>
      ) : (
        <p className="quote" style={{ color: color.textFaint }}>
          цитати немає — модель не навела доказу
        </p>
      )}

      {confidence !== null && confidence < 0.6 ? (
        <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 8 }}>
          <Meter value={confidence * 100} tone="warn" />
          <span style={{ fontSize: 11, color: color.warn }}>низька впевненість</span>
        </div>
      ) : null}
    </div>
  );
}

function SegmentRow({ segment, highlight }: { segment: Segment; highlight: string | null }) {
  const speaker = segment.speaker === "operator" ? "оператор" : segment.speaker === "client" ? "клієнт" : "?";

  return (
    <div className={`segment ${segment.speaker}`}>
      <div>
        <div className="num" style={{ fontSize: 11, color: color.textFaint }}>
          {timecode(segment.start_ms)}
        </div>
        <div style={{ fontSize: 10, color: color.textDim, textTransform: "uppercase" }}>
          {speaker}
        </div>
      </div>
      <div className="segment-text">{markQuote(segment.text, highlight)}</div>
    </div>
  );
}

function markQuote(text: string, quote: string | null) {
  if (!quote) return text;

  const needle = quote.trim();
  if (needle.length < 4) return text;

  const at = text.toLowerCase().indexOf(needle.toLowerCase());
  if (at === -1) return text;

  return (
    <>
      {text.slice(0, at)}
      <mark>{text.slice(at, at + needle.length)}</mark>
      {text.slice(at + needle.length)}
    </>
  );
}

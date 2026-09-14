import { Badge } from "@/components/ui";
import type { CallStatus } from "@/lib/api";

export const STATUS_META: Record<
  CallStatus,
  { text: string; tone: "neutral" | "info" | "pass" | "fail" }
> = {
  queued: { text: "у черзі", tone: "neutral" },
  transcribing: { text: "розшифровка", tone: "info" },
  analyzing: { text: "аналіз", tone: "info" },
  done: { text: "готово", tone: "pass" },
  failed: { text: "помилка", tone: "fail" },
};

export function StatusBadge({ status }: { status: CallStatus }) {
  const meta = STATUS_META[status];
  return <Badge tone={meta.tone}>{meta.text}</Badge>;
}

"use client";

import type { ReactNode } from "react";
import { useAuth, useProfile } from "@/components/auth-provider";
import { Badge, Button, Card, CardTitle, Label } from "@/components/ui";
import { fullDate } from "@/lib/format";
import {
  ROLE_LABEL,
  canManageApiKeys,
  canManagePeople,
  canVerifyScores,
} from "@/lib/permissions";
import { color } from "@/lib/theme";

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "160px 1fr",
        gap: 12,
        padding: "12px 20px",
        borderBottom: `1px solid ${color.borderSoft}`,
        alignItems: "center",
      }}
    >
      <Label>{label}</Label>
      <div style={{ fontSize: 14 }}>{children}</div>
    </div>
  );
}

export default function CabinetPage() {
  const { user, organization } = useProfile();
  const { signOut } = useAuth();

  const abilities = [
    { allowed: true, text: "Бачити дзвінки й статистику" + (user.role === "operator" ? " — свої" : "") },
    { allowed: canVerifyScores(user.role), text: "Підтверджувати оцінки" },
    { allowed: canManagePeople(user.role), text: "Запрошувати людей у команду" },
    { allowed: canManageApiKeys(user.role), text: "Видавати ключі API" },
  ];

  return (
    <>
      <header className="page-head">
        <div>
          <h1 className="page-title">Кабінет</h1>
          <p className="page-sub">Ваш профіль і доступ у компанії</p>
        </div>
        <Button type="button" className="btn only-narrow" onClick={signOut}>
          Вийти
        </Button>
      </header>

      <div className="grid grid-split">
        <Card padded={false}>
          <CardTitle>Профіль</CardTitle>
          <Row label="Імʼя">{user.full_name}</Row>
          <Row label="Пошта">{user.email}</Row>
          <Row label="Роль">
            <Badge tone="accent">{ROLE_LABEL[user.role]}</Badge>
          </Row>
          <Row label="Пошта підтверджена">
            {user.is_verified ? <Badge tone="pass">так</Badge> : <Badge tone="warn">ні</Badge>}
          </Row>
          <Row label="З нами з">{fullDate(user.created_at)}</Row>
        </Card>

        <div className="grid">
          <Card padded={false}>
            <CardTitle>Компанія</CardTitle>
            {organization ? (
              <>
                <Row label="Назва">{organization.name}</Row>
                <Row label="Ідентифікатор">
                  <span className="num" style={{ color: color.textMuted }}>
                    {organization.slug}
                  </span>
                </Row>
              </>
            ) : (
              <Row label="Назва">
                <span style={{ color: color.textDim }}>не привʼязано</span>
              </Row>
            )}
          </Card>

          <Card padded={false}>
            <CardTitle>Що вам доступно</CardTitle>
            <ul style={{ listStyle: "none", margin: 0, padding: "8px 20px 16px" }}>
              {abilities.map((ability) => (
                <li
                  key={ability.text}
                  style={{
                    display: "flex",
                    gap: 10,
                    padding: "6px 0",
                    color: ability.allowed ? color.text : color.textDim,
                  }}
                >
                  <span style={{ color: ability.allowed ? color.pass : color.textFaint }}>
                    {ability.allowed ? "✓" : "—"}
                  </span>
                  {ability.text}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </>
  );
}

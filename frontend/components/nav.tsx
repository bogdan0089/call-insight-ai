"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import type { Role } from "@/lib/api";
import { ROLE_LABEL, canManageApiKeys, canManagePeople } from "@/lib/permissions";
import { color } from "@/lib/theme";

interface NavLink {
  href: string;
  label: string;
  visible: (role: Role) => boolean;
}

const LINKS: NavLink[] = [
  { href: "/", label: "Огляд", visible: () => true },
  { href: "/calls", label: "Дзвінки", visible: () => true },
  { href: "/team", label: "Команда", visible: canManagePeople },
  { href: "/keys", label: "Ключі API", visible: canManageApiKeys },
];

function initials(first: string, last: string) {
  return `${first.charAt(0)}${last.charAt(0)}`.toUpperCase();
}

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

export function Nav() {
  const pathname = usePathname();
  const { status, profile, signOut } = useAuth();
  const role = profile?.user.role;

  return (
    <nav
      style={{
        borderBottom: `1px solid ${color.border}`,
        background: `${color.surface}cc`,
        backdropFilter: "blur(8px)",
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}
    >
      <div className="shell nav-inner">
        <Link href="/" className="nav-brand">
          <span
            style={{
              width: 9,
              height: 9,
              borderRadius: 3,
              background: color.accent,
              boxShadow: `0 0 12px ${color.accent}`,
            }}
          />
          <span style={{ fontWeight: 700, letterSpacing: "-0.2px" }}>call&#8202;insight</span>
        </Link>

        {role ? (
          <div className="nav-links">
            {LINKS.filter((link) => link.visible(role)).map((link) => {
              const active = isActive(pathname, link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  style={{
                    padding: "6px 12px",
                    borderRadius: 6,
                    fontSize: 13,
                    fontWeight: 600,
                    color: active ? color.text : color.textMuted,
                    background: active ? color.surfaceRaised : "transparent",
                  }}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        ) : null}

        <div className="nav-user">
          {status === "authenticated" && profile ? (
            <>
              <Link
                href="/cabinet"
                className="nav-profile"
                aria-label={`Кабінет: ${profile.user.full_name}`}
                style={{
                  background: isActive(pathname, "/cabinet") ? color.surfaceRaised : "transparent",
                }}
              >
                <span className="nav-profile-text">
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{profile.user.full_name}</span>
                  <span style={{ fontSize: 11, color: color.textDim }}>
                    {ROLE_LABEL[profile.user.role]}
                    {profile.organization ? ` · ${profile.organization.name}` : ""}
                  </span>
                </span>
                <span className="nav-avatar" aria-hidden>
                  {initials(profile.user.first_name, profile.user.last_name)}
                </span>
              </Link>
              <button type="button" className="btn nav-exit" onClick={signOut}>
                Вийти
              </button>
            </>
          ) : status === "anonymous" ? (
            <>
              <Link href="/login" className="link" style={{ fontSize: 13, fontWeight: 600 }}>
                Увійти
              </Link>
              <Link href="/register" className="link" style={{ fontSize: 13, fontWeight: 600 }}>
                Реєстрація
              </Link>
            </>
          ) : null}
        </div>
      </div>
    </nav>
  );
}

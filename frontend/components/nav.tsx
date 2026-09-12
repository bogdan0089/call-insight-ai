"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { color } from "@/lib/theme";

const LINKS = [{ href: "/", label: "Огляд" }];

export function Nav() {
  const pathname = usePathname();

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
      <div
        className="shell"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 28,
          height: 56,
          paddingBottom: 0,
        }}
      >
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: 9 }}>
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

        <div style={{ display: "flex", gap: 4 }}>
          {LINKS.map((link) => {
            const active =
              link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
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
      </div>
    </nav>
  );
}

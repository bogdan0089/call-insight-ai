import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AuthGate, AuthProvider } from "@/components/auth-provider";
import { Nav } from "@/components/nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "call insight — контроль якості дзвінків",
  description: "Оцінка розмов операторів за чеклістом",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="uk">
      <body>
        <AuthProvider>
          <Nav />
          <main className="shell">
            <AuthGate>{children}</AuthGate>
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}

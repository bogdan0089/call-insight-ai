"use client";

import { usePathname, useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { Empty } from "@/components/ui";
import { api, type Profile, type Role } from "@/lib/api";
import { clearToken, getToken, onTokenChange, setToken } from "@/lib/auth";
import { safeNext } from "@/lib/redirect";

const PUBLIC_ROUTES = ["/login", "/register", "/verify", "/invite"];
const GUEST_ONLY_ROUTES = ["/login", "/register"];

type Status = "loading" | "anonymous" | "authenticated";

interface Loaded {
  token: string;
  profile: Profile | null;
}

interface AuthContextValue {
  status: Status;
  profile: Profile | null;
  signIn: (token: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function isPublic(pathname: string) {
  return PUBLIC_ROUTES.some((route) => pathname === route || pathname.startsWith(`${route}/`));
}

const serverToken = () => null;

const noopSubscribe = () => () => {};

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  const token = useSyncExternalStore(onTokenChange, getToken, serverToken);
  const [loaded, setLoaded] = useState<Loaded | null>(null);

  const hydrated = useSyncExternalStore(noopSubscribe, () => true, () => false);

  const current = token !== null && loaded?.token === token ? loaded : null;
  const profile = current?.profile ?? null;
  const status: Status = !hydrated
    ? "loading"
    : token === null
      ? "anonymous"
      : current === null
        ? "loading"
        : profile
          ? "authenticated"
          : "anonymous";

  useEffect(() => {
    if (token === null) return;
    let alive = true;
    api
      .me()
      .then((result) => {
        if (alive) setLoaded({ token, profile: result });
      })
      .catch(() => {
        if (!alive) return;
        setLoaded({ token, profile: null });
        clearToken();
      });
    return () => {
      alive = false;
    };
  }, [token]);

  useEffect(() => {
    if (status === "anonymous" && !isPublic(pathname)) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
    if (status === "authenticated" && GUEST_ONLY_ROUTES.includes(pathname)) {
      const next = new URLSearchParams(window.location.search).get("next");
      router.replace(safeNext(next));
    }
  }, [status, pathname, router]);

  const signIn = useCallback(async (next: string) => {
    setToken(next);
    const result = await api.me();
    setLoaded({ token: next, profile: result });
  }, []);

  const signOut = useCallback(() => {
    clearToken();
    router.replace("/login");
  }, [router]);

  const value = useMemo<AuthContextValue>(
    () => ({ status, profile, signIn, signOut }),
    [status, profile, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function AuthGate({ children }: { children: ReactNode }) {
  const { status, profile } = useAuth();
  const pathname = usePathname();

  if (!isPublic(pathname) && status !== "authenticated") {
    return <Empty>Перевіряємо доступ…</Empty>;
  }
  return (
    <>
      {profile?.is_demo && !isPublic(pathname) ? (
        <div className="demo-banner">
          Демо-режим: можна все переглядати, але зміни вимкнені.
        </div>
      ) : null}
      {children}
    </>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

export function useProfile(): Profile {
  const { profile } = useAuth();
  if (!profile) throw new Error("useProfile is only available on authenticated pages");
  return profile;
}

export function useRole(): Role {
  return useProfile().user.role;
}

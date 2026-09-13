import { clearToken, getToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8090";

export type Role = "super_admin" | "owner" | "admin" | "manager" | "operator";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
}

export interface Profile {
  user: User;
  organization: Organization | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export class ApiError extends Error {
  status: number;
  code: string | null;
  retryAfter: number | null;

  constructor(
    status: number,
    message: string,
    code: string | null = null,
    retryAfter: number | null = null,
  ) {
    super(message);
    this.status = status;
    this.code = code;
    this.retryAfter = retryAfter;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init?.headers as Record<string, string>) ?? {}),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers, cache: "no-store" });
  } catch {
    throw new ApiError(0, "API недоступний — перевір, чи піднятий бекенд", "NetworkError");
  }

  if (response.status === 401 && token) {
    clearToken();
  }

  if (!response.ok) {
    throw await toError(response);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

async function toError(response: Response): Promise<ApiError> {
  const retryHeader = response.headers.get("Retry-After");
  const retryAfter = retryHeader ? Number(retryHeader) : null;

  let body: { detail?: unknown; code?: unknown } | null = null;
  try {
    body = await response.json();
  } catch {
  }
  const code = typeof body?.code === "string" ? body.code : null;

  if (response.status === 429) {
    const wait = retryAfter ? ` Спробуйте через ${retryAfter} с.` : "";
    return new ApiError(429, `Забагато спроб.${wait}`, code, retryAfter);
  }

  const detail = body?.detail;
  if (typeof detail === "string") return new ApiError(response.status, detail, code, retryAfter);
  if (Array.isArray(detail) && detail[0]?.msg) {
    return new ApiError(response.status, String(detail[0].msg), code, retryAfter);
  }
  return new ApiError(response.status, `Помилка ${response.status}`, code, retryAfter);
}

const post = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });

export const api = {
  register: (payload: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    organization_name: string;
  }) => request<{ detail: string }>("/auth/register", post(payload)),

  resend: (email: string) => request<{ detail: string }>("/auth/resend", post({ email })),

  verify: (token: string) => request<User>("/auth/verify", post({ token })),

  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", post({ email, password })),

  me: () => request<Profile>("/auth/me"),
};

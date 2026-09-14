import { clearToken, getToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8090";

export type CallStatus = "queued" | "transcribing" | "analyzing" | "done" | "failed";
export type Role = "super_admin" | "owner" | "admin" | "manager" | "operator";
export type SortOrder = "asc" | "desc";

export const CALL_STATUSES: CallStatus[] = [
  "queued",
  "transcribing",
  "analyzing",
  "done",
  "failed",
];


export type CallSortField =
  | "created_at"
  | "operator"
  | "total_score"
  | "duration_sec"
  | "status";

export interface CallListItem {
  id: number;
  external_id: string | null;
  operator_id: number | null;
  operator_name: string | null;
  status: CallStatus;
  duration_sec: number | null;
  total_score: string | null;
  created_at: string;
}

export interface CallPage {
  items: CallListItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface Segment {
  idx: number;
  speaker: "operator" | "client" | "unknown";
  start_ms: number;
  end_ms: number;
  text: string;
}

export interface Score {
  id: number;
  checklist_item_id: number;
  code: string;
  title: string;
  weight: string;
  is_required: boolean;
  passed: boolean;
  quote: string | null;
  quote_start_ms: number | null;
  confidence: string | null;
  is_verified: boolean;
}

export interface CallReport {
  id: number;
  external_id: string | null;
  operator_id: number | null;
  operator_name: string | null;
  status: CallStatus;
  duration_sec: number | null;
  total_score: string | null;
  error: string | null;
  created_at: string;
  failed_required: boolean;
  verified_count: number;
  transcript_text: string | null;
  segments: Segment[];
  scores: Score[];
}

export interface CallFilters {
  operator_id?: number | null;
  status?: CallStatus | null;
  created_from?: string | null;
  created_to?: string | null;
  score_min?: number | null;
  score_max?: number | null;
  limit?: number;
  offset?: number;
  sort_by?: CallSortField;
  order?: SortOrder;
}


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

export type PeopleSortField = "name" | "email" | "role" | "created_at";

export interface Person {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: Role;
  manager_id: number | null;
  manager_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface PeoplePage {
  items: Person[];
  total: number;
  limit: number;
  offset: number;
}

export interface PeopleParams {
  role?: Role | null;
  manager_id?: number | null;
  is_active?: boolean | null;
  limit?: number;
  offset?: number;
  sort_by?: PeopleSortField;
  order?: SortOrder;
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

function query(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  const encoded = search.toString();
  return encoded ? `?${encoded}` : "";
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

  listCalls: (filters: CallFilters = {}) => request<CallPage>(`/calls${query(filters)}`),

  getReport: (callId: number) => request<CallReport>(`/calls/${callId}/report`),

  verifyScore: (callId: number, scoreId: number, isVerified: boolean) =>
    request<Score>(`/calls/${callId}/scores/${scoreId}`, {
      method: "PATCH",
      body: JSON.stringify({ is_verified: isVerified }),
    }),

  listPeople: (params: PeopleParams = {}) => request<PeoplePage>(`/people${query(params)}`),
};

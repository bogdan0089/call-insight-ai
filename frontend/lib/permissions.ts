import type { Role } from "@/lib/api";

const MANAGE_PEOPLE: Role[] = ["owner", "admin", "manager"];
const MANAGE_API_KEYS: Role[] = ["owner"];
const VERIFY_SCORES: Role[] = ["owner", "admin", "manager"];

export const canManagePeople = (role: Role) => MANAGE_PEOPLE.includes(role);
export const canManageApiKeys = (role: Role) => MANAGE_API_KEYS.includes(role);
export const canVerifyScores = (role: Role) => VERIFY_SCORES.includes(role);

export const ROLE_LABEL: Record<Role, string> = {
  super_admin: "Платформа",
  owner: "Власник",
  admin: "Адміністратор",
  manager: "Керівник",
  operator: "Оператор",
};

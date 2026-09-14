export const NAME_MAX = 64;
export const ORG_NAME_MIN = 2;
export const ORG_NAME_MAX = 128;
export const PASSWORD_MIN = 8;
export const PASSWORD_MAX = 72;
export const PAGE_SIZE = 20;

export const PASSWORD_RULE = /^(?=.*[A-Za-z])(?=.*\d).+$/;

export function passwordProblem(password: string): string | null {
  if (password.length < PASSWORD_MIN) return `Щонайменше ${PASSWORD_MIN} символів`;
  if (password.length > PASSWORD_MAX) return `Не довше ${PASSWORD_MAX} символів`;
  if (!PASSWORD_RULE.test(password)) return "Потрібні і літера, і цифра";
  return null;
}

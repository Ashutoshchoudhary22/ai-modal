export function hashPassword(value: string): string {
  return `hash:${value}`;
}

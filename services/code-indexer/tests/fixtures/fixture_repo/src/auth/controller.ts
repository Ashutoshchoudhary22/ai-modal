import { AuthService } from "./service";

export function login(username: string, password: string): boolean {
  const service = new AuthService();
  return service.login(username, password);
}

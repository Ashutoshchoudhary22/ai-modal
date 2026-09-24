import { User } from "../models/User";
import { hashPassword } from "../utils/hash";

export class AuthService {
  login(username: string, password: string): boolean {
    const user = new User(username);
    return hashPassword(password) === user.passwordHash;
  }
}

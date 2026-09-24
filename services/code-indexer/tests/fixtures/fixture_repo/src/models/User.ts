export class User {
  constructor(public username: string) {
    this.passwordHash = "";
  }
  passwordHash: string;
}

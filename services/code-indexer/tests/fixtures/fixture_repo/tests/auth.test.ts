import { login } from "../src/auth/controller";

test("login", () => {
  expect(login("user", "pass")).toBeDefined();
});

import { newBinding } from "./binding";

describe("newBinding", () => {
  it("returns 64 lower-case hex characters, the shape the server accepts", () => {
    expect(newBinding()).toMatch(/^[0-9a-f]{64}$/);
  });

  it("returns a new secret each call", () => {
    expect(newBinding()).not.toBe(newBinding());
  });
});

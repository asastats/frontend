import { install } from "./main";

describe("app main", () => {
  beforeEach(() => {
    delete window.ASAStatsApp;
  });

  it("publishes window.ASAStatsApp with isApp", () => {
    expect(install()).toEqual({ isApp: true });
    expect(window.ASAStatsApp?.isApp).toBe(true);
  });

  it("keeps an API that is already there", () => {
    const existing = { isApp: true as const };
    window.ASAStatsApp = existing;
    expect(install()).toBe(existing);
  });
});

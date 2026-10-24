import { App } from "@capacitor/app";

import { handleAppUrl, installDeepLinks } from "./deepLinks";

jest.mock("@capacitor/app", () => ({
  App: { addListener: jest.fn().mockResolvedValue({ remove: jest.fn() }) },
}));

const ORIGIN = "https://www.asastats.com";

describe("handleAppUrl", () => {
  const navigate = jest.fn();

  it("follows a link to this site", () => {
    expect(handleAppUrl({ url: `${ORIGIN}/ABC/` }, ORIGIN, navigate)).toBe(true);
    expect(navigate).toHaveBeenCalledWith(`${ORIGIN}/ABC/`);
  });

  it.each(["https://evil.example/", "com.asastats.app:/auth?ticket=x"])(
    "ignores %s",
    (url) => {
      expect(handleAppUrl({ url }, ORIGIN, navigate)).toBe(false);
      expect(navigate).not.toHaveBeenCalled();
    }
  );

  it("ignores an unparseable URL", () => {
    expect(handleAppUrl({ url: "::" }, ORIGIN, navigate)).toBe(false);
  });
});

describe("installDeepLinks", () => {
  it("listens for appUrlOpen and navigates with location.assign", () => {
    Object.assign(window.location, { origin: ORIGIN, assign: jest.fn() });
    installDeepLinks();
    expect(App.addListener).toHaveBeenCalledWith("appUrlOpen", expect.any(Function));
    (App.addListener as jest.Mock).mock.calls[0][1]({ url: `${ORIGIN}/faq/` });
    expect(window.location.assign).toHaveBeenCalledWith(`${ORIGIN}/faq/`);
  });
});

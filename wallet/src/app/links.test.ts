import { Browser } from "@capacitor/browser";

import { classifyLink, handleLinkClick, installLinks } from "./links";

jest.mock("@capacitor/browser", () => ({
  Browser: { open: jest.fn().mockResolvedValue(undefined) },
}));

const ORIGIN = "https://www.asastats.com";

function link(href: string, attrs: Record<string, string> = {}): HTMLAnchorElement {
  const a = document.createElement("a");
  a.setAttribute("href", href);
  Object.entries(attrs).forEach(([k, v]) => a.setAttribute(k, v));
  document.body.appendChild(a);
  return a;
}

function click(target: Element, init: MouseEventInit = {}): MouseEvent {
  return new MouseEvent("click", { bubbles: true, cancelable: true, button: 0, ...init });
}

describe("classifyLink", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("sends another site to the browser sheet", () => {
    expect(classifyLink(link("https://explorer.perawallet.app/x"), ORIGIN)).toBe("browser");
  });

  it("opens a same-site new-tab link in place", () => {
    expect(classifyLink(link(`${ORIGIN}/faq/`, { target: "_blank" }), ORIGIN)).toBe(
      "in-place"
    );
  });

  it("leaves a plain same-site link alone", () => {
    expect(classifyLink(link(`${ORIGIN}/faq/`), ORIGIN)).toBe("default");
  });

  it.each(["mailto:info@asastats.com", "tel:123", "perawallet-wc://x"])(
    "leaves %s to the OS",
    (href) => {
      expect(classifyLink(link(href), ORIGIN)).toBe("default");
    }
  );

  it("leaves an unparseable href alone", () => {
    const a = link("x");
    Object.defineProperty(a, "href", { value: "http://[bad" });
    expect(classifyLink(a, ORIGIN)).toBe("default");
  });
});

describe("handleLinkClick", () => {
  const navigate = jest.fn();

  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("takes over an external tap", () => {
    const a = link("https://x.com/asastatscom");
    const event = click(a);
    Object.defineProperty(event, "target", { value: a });
    expect(handleLinkClick(event, ORIGIN, navigate)).toBe(true);
    expect(event.defaultPrevented).toBe(true);
    expect(Browser.open).toHaveBeenCalledWith({ url: "https://x.com/asastatscom" });
  });

  it("navigates a same-site new-tab link in place", () => {
    const a = link(`${ORIGIN}/historic/x`, { target: "_blank" });
    const event = click(a);
    Object.defineProperty(event, "target", { value: a.appendChild(document.createElement("span")) });
    expect(handleLinkClick(event, ORIGIN, navigate)).toBe(true);
    expect(navigate).toHaveBeenCalledWith(`${ORIGIN}/historic/x`);
    expect(Browser.open).not.toHaveBeenCalled();
  });

  it.each([
    ["a modifier key", { ctrlKey: true }],
    ["a meta key", { metaKey: true }],
    ["shift", { shiftKey: true }],
    ["alt", { altKey: true }],
    ["another button", { button: 1 }],
  ])("ignores a click with %s", (_name, init) => {
    const a = link("https://x.com/");
    const event = click(a, init as MouseEventInit);
    Object.defineProperty(event, "target", { value: a });
    expect(handleLinkClick(event, ORIGIN, navigate)).toBe(false);
  });

  it("ignores a click a page script already handled", () => {
    const a = link("https://x.com/");
    const event = click(a);
    event.preventDefault();
    Object.defineProperty(event, "target", { value: a });
    expect(handleLinkClick(event, ORIGIN, navigate)).toBe(false);
  });

  it.each([{ "data-app-download": "" }, { download: "" }])(
    "leaves download links to the downloads module",
    (attrs) => {
      const a = link(`${ORIGIN}/x.csv`, { target: "_blank", ...attrs });
      const event = click(a);
      Object.defineProperty(event, "target", { value: a });
      expect(handleLinkClick(event, ORIGIN, navigate)).toBe(false);
    }
  );

  it("ignores clicks outside links", () => {
    const div = document.createElement("div");
    const event = click(div);
    Object.defineProperty(event, "target", { value: div });
    expect(handleLinkClick(event, ORIGIN, navigate)).toBe(false);
  });

  it("ignores a click without a target", () => {
    const event = click(document.body);
    Object.defineProperty(event, "target", { value: null });
    expect(handleLinkClick(event, ORIGIN, navigate)).toBe(false);
  });

  it("leaves a plain same-site link alone", () => {
    const a = link(`${ORIGIN}/faq/`);
    const event = click(a);
    Object.defineProperty(event, "target", { value: a });
    expect(handleLinkClick(event, ORIGIN, navigate)).toBe(false);
    expect(event.defaultPrevented).toBe(false);
  });
});

describe("installLinks", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    Object.assign(window.location, { origin: ORIGIN, assign: jest.fn() });
  });

  it("handles taps on the document", () => {
    installLinks(document, jest.fn());
    const a = link("https://x.com/");
    a.dispatchEvent(click(a));
    expect(Browser.open).toHaveBeenCalledWith({ url: "https://x.com/" });
  });

  it("navigates with location.assign by default", () => {
    const doc = document.implementation.createHTMLDocument("x");
    installLinks(doc);
    const a = doc.createElement("a");
    a.setAttribute("href", `${ORIGIN}/faq/`);
    a.setAttribute("target", "_blank");
    doc.body.appendChild(a);
    a.dispatchEvent(click(a));
    expect(window.location.assign).toHaveBeenCalledWith(`${ORIGIN}/faq/`);
  });

  it("listens on the global document by default", () => {
    installLinks();
    const a = link("https://x.com/default");
    a.dispatchEvent(click(a));
    expect(Browser.open).toHaveBeenCalledWith({ url: "https://x.com/default" });
  });
});

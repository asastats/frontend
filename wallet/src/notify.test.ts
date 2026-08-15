import { notify, NOTIFY_EVENT, NOTICE_TIMEOUT_MS, NotifyDetail } from "./notify";

/** Listen for notifications, optionally claiming them the way a host would. */
function listen(claim: boolean): { seen: NotifyDetail[]; stop: () => void } {
  const seen: NotifyDetail[] = [];
  const handler = (event: Event) => {
    seen.push((event as CustomEvent<NotifyDetail>).detail);
    if (claim) event.preventDefault();
  };
  document.addEventListener(NOTIFY_EVENT, handler);
  return { seen, stop: () => document.removeEventListener(NOTIFY_EVENT, handler) };
}

describe("notify", () => {
  let host: HTMLElement;

  beforeEach(() => {
    document.body.innerHTML = "";
    host = document.createElement("div");
    document.body.appendChild(host);
  });

  it("reaches a host listener through the component's subtree", () => {
    const l = listen(true);
    expect(notify(host, "wallet said no")).toBe(true);
    expect(l.seen).toEqual([{ message: "wallet said no", level: "error" }]);
    l.stop();
  });

  it("leaves rendering to a host that claims the message", () => {
    const l = listen(true);
    notify(host, "claimed");
    expect(host.querySelector("[data-notice]")).toBeNull();
    l.stop();
  });

  it("falls back to a plain notice when nothing claims it", () => {
    jest.useFakeTimers();
    expect(notify(host, "boom")).toBe(false);
    const notice = host.querySelector("[data-notice]")!;
    expect(notice.getAttribute("data-notice")).toBe("error");
    expect(notice.getAttribute("role")).toBe("alert");
    expect(notice.textContent).toBe("boom");
    // No framework classes on the fallback -- only the data hook.
    expect(notice.className).toBe("");
    jest.advanceTimersByTime(NOTICE_TIMEOUT_MS);
    expect(host.querySelector("[data-notice]")).toBeNull();
    jest.useRealTimers();
  });

  it("announces info without interrupting", () => {
    notify(host, "connected", "info");
    const notice = host.querySelector("[data-notice]")!;
    expect(notice.getAttribute("data-notice")).toBe("info");
    expect(notice.getAttribute("role")).toBe("status");
  });

  it("renders wallet-derived markup as text, never as HTML", () => {
    notify(host, "<img src=x onerror=alert(1)>");
    const notice = host.querySelector("[data-notice]")!;
    expect(notice.querySelector("img")).toBeNull();
    expect(notice.textContent).toBe("<img src=x onerror=alert(1)>");
  });

  it("still reaches the document when the caller has no container", () => {
    const l = listen(true);
    expect(notify(null, "no host")).toBe(true);
    expect(l.seen).toEqual([{ message: "no host", level: "error" }]);
    l.stop();
  });

  it("drops an unclaimed message rather than appending to the page body", () => {
    // Matches the old behaviour on a page without the framework global: a
    // caller with nowhere to put a notice stays silent instead of guessing.
    expect(notify(null, "nowhere to go")).toBe(false);
    expect(document.querySelectorAll("[data-notice]")).toHaveLength(0);
  });
});

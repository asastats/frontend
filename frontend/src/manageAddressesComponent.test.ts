/**
 * @jest-environment jsdom
 */

import {
  ManageAddressesComponent,
  type ManageDeps,
} from "./manageAddressesComponent";

const ROWS = [
  { id: 1, address: "0xprimary", chain: "evm", is_primary: true, login_enabled: true, label: "" },
  { id: 2, address: "ALGOSEC", chain: "algorand", is_primary: false, login_enabled: false, label: "" },
];

const flush = () => new Promise((r) => setTimeout(r, 0));

function setupDOM(): HTMLElement {
  document.body.innerHTML = `
    <div id="connected-addresses" data-api-base="/api/v2/wallet">
      <input type="hidden" name="csrfmiddlewaretoken" value="tok">
      <div id="connected-addresses-list"></div>
      <button class="manage-action manage-add" data-action="add">Add address</button>
    </div>`;
  return document.getElementById("connected-addresses")!;
}

function jsonResponse(payload: unknown): Response {
  return { json: async () => payload } as Response;
}

function makeFetch(opts: { rows?: unknown[]; nonce?: unknown; manage?: unknown } = {}) {
  const rows = opts.rows ?? ROWS;
  return jest.fn(async (url: string, _init?: RequestInit) => {
    if (url.endsWith("/manage/addresses/")) return jsonResponse({ addresses: rows });
    if (url.endsWith("/manage/nonce/"))
      return jsonResponse(
        opts.nonce ?? { nonce: "N1", prefix: "asastats-auth:", address: "0xprimary", chain: "evm" }
      );
    if (url.endsWith("/manage/")) return jsonResponse(opts.manage ?? { success: true });
    return jsonResponse({});
  });
}

function deps(over: Partial<ManageDeps> = {}): ManageDeps {
  return {
    fetchFn: makeFetch(),
    stepUpSign: jest.fn(async () => ({ signature: "0xsig" })),
    addAddress: jest.fn(async () => {}),
    ...over,
  };
}

function postCalls(fetchFn: jest.Mock, suffix: string) {
  return fetchFn.mock.calls.filter(
    ([url, init]) => url.endsWith(suffix) && init?.method === "POST"
  );
}

beforeEach(() => {
  (window as any).M = { toast: jest.fn() };
});

describe("ManageAddressesComponent.load/render", () => {
  it("renders a row per address; primary has no action buttons", async () => {
    const root = setupDOM();
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps());
    await c.bind();
    const rows = root.querySelectorAll(".connected-address-row");
    expect(rows).toHaveLength(2);
    // primary row (id 1): no action buttons
    expect(rows[0].querySelectorAll(".manage-action")).toHaveLength(0);
    // secondary row (id 2): make-primary, enable-login, remove
    expect(rows[1].querySelector(".manage-set_primary")).not.toBeNull();
    expect(rows[1].querySelector(".manage-enable_login")).not.toBeNull();
    expect(rows[1].querySelector(".manage-remove")).not.toBeNull();
  });

  it("groups each address in a Materialize collapsible item", async () => {
    const root = setupDOM();
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps());
    await c.bind();
    const ul = root.querySelector("ul.collapsible");
    expect(ul).not.toBeNull();
    const items = ul!.querySelectorAll("li.connected-address-row");
    expect(items).toHaveLength(2);
    // header carries the address; body carries that address's actions
    expect(items[1].querySelector(".collapsible-header .address-text")).not.toBeNull();
    const body = items[1].querySelector(".collapsible-body");
    expect(body!.querySelector(".manage-set_primary")).not.toBeNull();
    // primary's body shows a note, not actions
    expect(items[0].querySelector(".collapsible-body .address-note")).not.toBeNull();
  });

  it("shows Disable for an already login-enabled secondary", async () => {
    const root = setupDOM();
    const rows = [
      ROWS[0],
      { ...ROWS[1], login_enabled: true },
    ];
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn: makeFetch({ rows }) }));
    await c.bind();
    expect(root.querySelector(".manage-disable_login")).not.toBeNull();
    expect(root.querySelector(".manage-enable_login")).toBeNull();
  });

  it("toasts when loading fails", async () => {
    const root = setupDOM();
    const fetchFn = jest.fn(async () => {
      throw new Error("network down");
    });
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ html: "network down" })
    );
  });
});

describe("ManageAddressesComponent non-step-up actions", () => {
  it("removes a secondary and reloads", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch();
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    root.querySelector<HTMLElement>(".manage-remove")!.click();
    await flush();
    const calls = postCalls(fetchFn, "/manage/");
    expect(JSON.parse(calls[0][1].body)).toEqual({ operation: "remove", target_id: 2 });
    expect(calls[0][1].headers["X-CSRFToken"]).toBe("tok");
    // reloaded the list after the action
    expect(fetchFn.mock.calls.filter(([u]) => u.endsWith("/manage/addresses/"))).toHaveLength(2);
  });

  it("disables login without a step-up signature", async () => {
    const root = setupDOM();
    const rows = [ROWS[0], { ...ROWS[1], login_enabled: true }];
    const stepUpSign = jest.fn();
    const fetchFn = makeFetch({ rows });
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn, stepUpSign }));
    await c.bind();
    root.querySelector<HTMLElement>(".manage-disable_login")!.click();
    await flush();
    expect(stepUpSign).not.toHaveBeenCalled();
    expect(postCalls(fetchFn, "/manage/nonce/")).toHaveLength(0);
    expect(JSON.parse(postCalls(fetchFn, "/manage/")[0][1].body)).toEqual({
      operation: "set_login",
      target_id: 2,
      enabled: false,
    });
  });
});

describe("ManageAddressesComponent step-up actions", () => {
  it("enables login via a primary-signed step-up", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch();
    const stepUpSign = jest.fn(async () => ({ signature: "0xdead" }));
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn, stepUpSign }));
    await c.bind();
    root.querySelector<HTMLElement>(".manage-enable_login")!.click();
    await flush();
    expect(stepUpSign).toHaveBeenCalledWith("0xprimary", "evm", "asastats-auth:N1");
    const body = JSON.parse(postCalls(fetchFn, "/manage/")[0][1].body);
    expect(body).toEqual({
      operation: "set_login",
      target_id: 2,
      enabled: true,
      nonce: "N1",
      chain: "evm",
      signature: "0xdead",
    });
  });

  it("makes an address primary via step-up", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch();
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    root.querySelector<HTMLElement>(".manage-set_primary")!.click();
    await flush();
    const body = JSON.parse(postCalls(fetchFn, "/manage/")[0][1].body);
    expect(body.operation).toBe("set_primary");
    expect(body.target_id).toBe(2);
    expect(body.signature).toBe("0xsig");
  });

  it("aborts step-up when the signer rejects (wrong account)", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch();
    const stepUpSign = jest.fn(async () => {
      throw new Error("connected wallet is not your primary");
    });
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn, stepUpSign }));
    await c.bind();
    root.querySelector<HTMLElement>(".manage-set_primary")!.click();
    await flush();
    expect(postCalls(fetchFn, "/manage/")).toHaveLength(0); // never posted the op
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ html: "connected wallet is not your primary" })
    );
  });

  it("surfaces a step-up nonce error", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch({ nonce: { error: "No primary address" } });
    const stepUpSign = jest.fn();
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn, stepUpSign }));
    await c.bind();
    root.querySelector<HTMLElement>(".manage-set_primary")!.click();
    await flush();
    expect(stepUpSign).not.toHaveBeenCalled();
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ html: "No primary address" })
    );
  });

  it("surfaces a failed operation result", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch({ manage: { success: false, error: "Set another address as primary" } });
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    root.querySelector<HTMLElement>(".manage-remove")!.click();
    await flush();
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ html: "Set another address as primary" })
    );
  });
});

describe("ManageAddressesComponent add + misc", () => {
  it("runs the add-address flow then reloads", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch();
    const addAddress = jest.fn(async () => {});
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn, addAddress }));
    await c.bind();
    root.querySelector<HTMLElement>(".manage-add")!.click();
    await flush();
    expect(addAddress).toHaveBeenCalledWith("/api/v2/wallet");
    expect(fetchFn.mock.calls.filter(([u]) => u.endsWith("/manage/addresses/"))).toHaveLength(2);
  });

  it("ignores clicks that are not action buttons", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch();
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    const before = fetchFn.mock.calls.length;
    root.querySelector<HTMLElement>("#connected-addresses-list")!.click();
    await flush();
    expect(fetchFn.mock.calls.length).toBe(before);
  });

  it("falls back to a card panel when Materialize is absent", async () => {
    const root = setupDOM();
    delete (window as any).M;
    const fetchFn = jest.fn(async () => {
      throw new Error("boom");
    });
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    expect(root.querySelector(".card-panel")?.textContent).toBe("boom");
  });

  it("escapes error text before toasting", async () => {
    const root = setupDOM();
    const fetchFn = jest.fn(async () => {
      throw new Error("<img src=x>");
    });
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ html: "&lt;img src=x&gt;" })
    );
  });

  it("stringifies non-Error throwables from add-address", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch();
    const addAddress = jest.fn(async () => {
      // eslint-disable-next-line no-throw-literal
      throw "string failure";
    });
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn, addAddress }));
    await c.bind();
    root.querySelector<HTMLElement>(".manage-add")!.click();
    await flush();
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ html: "string failure" })
    );
  });

  it("uses the csrftoken cookie when present", async () => {
    const root = setupDOM();
    document.cookie = "csrftoken=ck";
    const fetchFn = makeFetch();
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    root.querySelector<HTMLElement>(".manage-remove")!.click();
    await flush();
    expect(postCalls(fetchFn, "/manage/")[0][1].headers["X-CSRFToken"]).toBe("ck");
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  });

  it("renders nothing when the list response omits addresses", async () => {
    const root = setupDOM();
    const fetchFn = jest.fn(async () => jsonResponse({}));
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    expect(root.querySelectorAll(".connected-address-row")).toHaveLength(0);
  });

  it("ignores an unrecognized action attribute", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch();
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    const bogus = document.createElement("button");
    bogus.className = "manage-action";
    bogus.dataset.action = "bogus";
    root.appendChild(bogus);
    const before = fetchFn.mock.calls.length;
    bogus.click();
    await flush();
    expect(fetchFn.mock.calls.length).toBe(before);
  });

  it("ignores a manage-action button with no action attribute", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch();
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    const b = document.createElement("button");
    b.className = "manage-action";
    root.appendChild(b);
    const before = fetchFn.mock.calls.length;
    b.click();
    await flush();
    expect(fetchFn.mock.calls.length).toBe(before);
  });

  it("uses the default api base when none is supplied", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch();
    const c = new ManageAddressesComponent(root, undefined, deps({ fetchFn }));
    await c.bind();
    expect(
      fetchFn.mock.calls.some(([u]) => u === "/api/v2/wallet/manage/addresses/")
    ).toBe(true);
  });

  it("renders into the container when no list element exists", async () => {
    document.body.innerHTML = `<div id="connected-addresses"></div>`;
    const root = document.getElementById("connected-addresses")!;
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps());
    await c.bind();
    expect(root.querySelectorAll(".connected-address-row")).toHaveLength(2);
  });

  it("sends an empty CSRF token when neither cookie nor input is present", async () => {
    document.body.innerHTML = `<div id="connected-addresses"><div id="connected-addresses-list"></div></div>`;
    const root = document.getElementById("connected-addresses")!;
    const fetchFn = makeFetch();
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    root.querySelector<HTMLElement>(".manage-remove")!.click();
    await flush();
    expect(postCalls(fetchFn, "/manage/")[0][1].headers["X-CSRFToken"]).toBe("");
  });

  it("defaults the failure message when the result omits one", async () => {
    const root = setupDOM();
    const fetchFn = makeFetch({ manage: { success: false } });
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    root.querySelector<HTMLElement>(".manage-remove")!.click();
    await flush();
    expect((window as any).M.toast).toHaveBeenCalledWith(
      expect.objectContaining({ html: "Operation failed" })
    );
  });

  it("auto-dismisses the card panel fallback", async () => {
    jest.useFakeTimers();
    const root = setupDOM();
    delete (window as any).M;
    const fetchFn = jest.fn(async () => {
      throw new Error("x");
    });
    const c = new ManageAddressesComponent(root, "/api/v2/wallet", deps({ fetchFn }));
    await c.bind();
    expect(root.querySelector(".card-panel")).not.toBeNull();
    jest.advanceTimersByTime(5000);
    expect(root.querySelector(".card-panel")).toBeNull();
    jest.useRealTimers();
  });
});

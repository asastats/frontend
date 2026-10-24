import { Directory, Filesystem } from "@capacitor/filesystem";
import { Share } from "@capacitor/share";

import { notify } from "../notify";
import {
  attachmentName,
  blobToBase64,
  DEFAULT_FILENAME,
  download,
  DOWNLOAD_ERROR,
  fetchFile,
  installDownloads,
  shareFile,
} from "./downloads";

jest.mock("@capacitor/filesystem", () => ({
  Directory: { Cache: "CACHE" },
  Filesystem: { writeFile: jest.fn() },
}));
jest.mock("@capacitor/share", () => ({ Share: { share: jest.fn() } }));
jest.mock("../notify", () => ({ notify: jest.fn() }));

const fetchMock = global.fetch as jest.Mock;

function response(
  body: string,
  headers: Record<string, string> = {},
  init: { ok?: boolean; status?: number; url?: string } = {}
) {
  return {
    ok: init.ok ?? true,
    status: init.status ?? 200,
    url: init.url ?? "",
    headers: { get: (name: string) => headers[name] ?? null },
    blob: () => Promise.resolve(new Blob([body])),
  };
}

const ATTACHMENT = { "Content-Disposition": 'attachment; filename="report_1_ABC.zip"' };

beforeEach(() => {
  (Filesystem.writeFile as jest.Mock).mockResolvedValue({ uri: "file:///cache/x" });
  (Share.share as jest.Mock).mockResolvedValue({});
});

describe("attachmentName", () => {
  it.each([
    [null, null],
    ["", null],
    ['inline; filename="a.pdf"', null],
    ['attachment; filename="pnl-abc.csv"', "pnl-abc.csv"],
    ["attachment; filename=plain.csv", "plain.csv"],
    ["attachment; filename*=UTF-8''r%C3%A9sum%C3%A9.pdf", "r_sum_.pdf"],
    ["attachment; filename*=UTF-8''%E0%A4%A.pdf; filename=\"fallback.pdf\"", "fallback.pdf"],
    ['attachment; filename="../../etc/passwd"', "passwd"],
    ['attachment; filename="a\\\\b.zip"', "b.zip"],
    ['attachment; filename=".."', DEFAULT_FILENAME],
    ["attachment", DEFAULT_FILENAME],
  ])("%s -> %s", (header, name) => {
    expect(attachmentName(header)).toBe(name);
  });
});

describe("fetchFile", () => {
  it("returns the file with its name", async () => {
    fetchMock.mockResolvedValue(response("zip", ATTACHMENT, { url: "/export/download/" }));
    const { file, responseUrl } = await fetchFile("/x/", { method: "POST" });
    expect(fetchMock).toHaveBeenCalledWith("/x/", {
      credentials: "same-origin",
      method: "POST",
    });
    expect(file!.filename).toBe("report_1_ABC.zip");
    expect(responseUrl).toBe("/export/download/");
  });

  it("returns no file for a page, with where it ended up", async () => {
    fetchMock.mockResolvedValue(response("<html>", {}, { url: "/export/ABC/" }));
    expect(await fetchFile("/x/")).toEqual({ file: null, responseUrl: "/export/ABC/" });
  });

  it("falls back to the requested URL when the response has none", async () => {
    fetchMock.mockResolvedValue(response("<html>"));
    expect((await fetchFile("/x/")).responseUrl).toBe("/x/");
  });

  it("throws on an HTTP error", async () => {
    fetchMock.mockResolvedValue(response("", {}, { ok: false, status: 500 }));
    await expect(fetchFile("/x/")).rejects.toThrow("HTTP 500");
  });
});

describe("blobToBase64", () => {
  it("returns plain base64", async () => {
    expect(await blobToBase64(new Blob(["hello"]))).toBe(btoa("hello"));
  });

  it("rejects when the blob cannot be read", async () => {
    const original = FileReader.prototype.readAsDataURL;
    FileReader.prototype.readAsDataURL = function () {
      this.onerror!(new ProgressEvent("error") as ProgressEvent<FileReader>);
    };
    await expect(blobToBase64(new Blob(["x"]))).rejects.toBeNull();
    FileReader.prototype.readAsDataURL = original;
  });
});

describe("shareFile", () => {
  const file = { filename: "a.csv", blob: new Blob(["a,b"]) };

  it("writes to the cache and shares the file", async () => {
    await shareFile(file);
    expect(Filesystem.writeFile).toHaveBeenCalledWith({
      path: "a.csv",
      data: btoa("a,b"),
      directory: Directory.Cache,
    });
    expect(Share.share).toHaveBeenCalledWith({ title: "a.csv", files: ["file:///cache/x"] });
  });

  it.each([new Error("Share canceled"), "User cancelled"])(
    "treats closing the sheet as fine (%s)",
    async (error) => {
      (Share.share as jest.Mock).mockRejectedValue(error);
      await expect(shareFile(file)).resolves.toBeUndefined();
    }
  );

  it("passes on other share errors", async () => {
    (Share.share as jest.Mock).mockRejectedValue(new Error("no app"));
    await expect(shareFile(file)).rejects.toThrow("no app");
  });

  it("passes on a rejection without a message", async () => {
    (Share.share as jest.Mock).mockRejectedValue(undefined);
    await expect(shareFile(file)).rejects.toBeUndefined();
  });
});

describe("download", () => {
  it("shares a file", async () => {
    fetchMock.mockResolvedValue(response("zip", ATTACHMENT));
    expect(await download("/x/")).toBe(true);
    expect(Share.share).toHaveBeenCalled();
  });

  it("shows a page that is not a file", async () => {
    fetchMock.mockResolvedValue(response("<html>", {}, { url: "/export/ABC/" }));
    const fallback = jest.fn();
    expect(await download("/x/", {}, fallback)).toBe(false);
    expect(fallback).toHaveBeenCalledWith("/export/ABC/");
  });

  it("shows the page with location.assign by default", async () => {
    Object.assign(window.location, { assign: jest.fn() });
    fetchMock.mockResolvedValue(response("<html>", {}, { url: "/export/ABC/" }));
    await download("/x/");
    expect(window.location.assign).toHaveBeenCalledWith("/export/ABC/");
  });

  it("tells the user when it fails", async () => {
    fetchMock.mockRejectedValue(new Error("offline"));
    const host = document.createElement("div");
    expect(await download("/x/", {}, jest.fn(), host)).toBe(false);
    expect(notify).toHaveBeenCalledWith(host, DOWNLOAD_ERROR);
  });
});

describe("installDownloads", () => {
  const flush = () => new Promise((resolve) => setTimeout(resolve, 0));

  beforeAll(() => installDownloads());

  beforeEach(() => {
    document.body.innerHTML = "";
    fetchMock.mockResolvedValue(response("zip", ATTACHMENT));
  });

  it("downloads a marked link", async () => {
    document.body.innerHTML =
      '<p><a data-app-download href="https://www.asastats.com/r.pdf"><b>PDF</b></a></p>';
    const inner = document.querySelector("b")!;
    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    inner.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
    await flush();
    expect(fetchMock).toHaveBeenCalledWith("https://www.asastats.com/r.pdf", {
      credentials: "same-origin",
    });
  });

  it.each([
    ["an unmarked link", '<a href="#r">x</a>', {}],
    ["another button", '<a data-app-download href="#r">x</a>', { button: 1 }],
  ])("leaves %s alone", (_name, html, init) => {
    document.body.innerHTML = html;
    const event = new MouseEvent("click", { bubbles: true, cancelable: true, ...init });
    document.querySelector("a")!.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("leaves a click a page script already handled", () => {
    document.body.innerHTML = '<a data-app-download href="/r.pdf">x</a>';
    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    event.preventDefault();
    document.querySelector("a")!.dispatchEvent(event);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("ignores a click on the document itself", () => {
    document.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(fetchMock).not.toHaveBeenCalled();
  });

  function form(html: string): HTMLFormElement {
    document.body.innerHTML = html;
    return document.querySelector("form")!;
  }

  function submit(target: HTMLFormElement, submitter?: HTMLElement | null) {
    const event = new Event("submit", { bubbles: true, cancelable: true });
    Object.defineProperty(event, "submitter", { value: submitter ?? null });
    target.dispatchEvent(event);
    return event;
  }

  it("posts a marked form with its submit button and shares the file", async () => {
    const f = form(
      '<form data-app-download method="post" action="https://www.asastats.com/export/ABC/">' +
        '<input name="agree" value="on"><button name="download" value="1">Go</button></form>'
    );
    const event = submit(f, f.querySelector("button"));
    expect(event.defaultPrevented).toBe(true);
    await flush();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("https://www.asastats.com/export/ABC/");
    expect(init.method).toBe("POST");
    expect((init.body as FormData).get("agree")).toBe("on");
    expect((init.body as FormData).get("download")).toBe("1");
    await flush();
    expect(Share.share).toHaveBeenCalled();
  });

  it("takes over a submit through a marked button only", async () => {
    const f = form(
      '<form method="post" action="https://www.asastats.com/export/ABC/">' +
        '<button id="dl" name="download" value="1" data-app-download>Download</button>' +
        '<button id="rf" name="refresh" value="1">Refresh</button></form>'
    );
    expect(submit(f, document.getElementById("rf")).defaultPrevented).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(submit(f, document.getElementById("dl")).defaultPrevented).toBe(true);
    await flush();
    expect((fetchMock.mock.calls[0][1].body as FormData).get("download")).toBe("1");
  });

  it("unmarks the button before submitting natively", async () => {
    fetchMock.mockResolvedValue(response("<html>"));
    const f = form(
      '<form method="post" action="/x/"><button data-app-download name="download">Go</button></form>'
    );
    f.requestSubmit = jest.fn();
    const button = f.querySelector("button")!;
    submit(f, button);
    await flush();
    expect(button.hasAttribute("data-app-download")).toBe(false);
    expect(f.requestSubmit).toHaveBeenCalledWith(button);
  });

  it("sends a GET form as a query string", async () => {
    const f = form(
      '<form data-app-download action="https://www.asastats.com/r"><input name="a" value="1"></form>'
    );
    submit(f);
    await flush();
    expect(fetchMock).toHaveBeenCalledWith("https://www.asastats.com/r?a=1", {
      credentials: "same-origin",
    });
  });

  it("appends to an action that already has a query", async () => {
    const f = form(
      '<form data-app-download method="get" action="https://www.asastats.com/r?k=2">' +
        '<input name="a" value="1"></form>'
    );
    submit(f, document.createElement("button"));
    await flush();
    expect(fetchMock.mock.calls[0][0]).toBe("https://www.asastats.com/r?k=2&a=1");
  });

  it("submits natively when the answer is a page", async () => {
    fetchMock.mockResolvedValue(response("<html>", {}, { url: "/export/ABC/" }));
    const f = form(
      '<form data-app-download method="post" action="/export/ABC/"><button>Go</button></form>'
    );
    f.requestSubmit = jest.fn();
    const button = f.querySelector("button")!;
    submit(f, button);
    await flush();
    expect(f.hasAttribute("data-app-download")).toBe(false);
    expect(f.requestSubmit).toHaveBeenCalledWith(button);
  });

  it("submits natively without a submitter", async () => {
    fetchMock.mockResolvedValue(response("<html>"));
    const f = form('<form data-app-download method="post" action="/x/"></form>');
    f.requestSubmit = jest.fn();
    submit(f);
    await flush();
    expect(f.requestSubmit).toHaveBeenCalledWith(undefined);
  });

  it.each([
    ["an unmarked form", '<form method="post" action="/x/"></form>'],
  ])("leaves %s alone", (_name, html) => {
    const event = submit(form(html));
    expect(event.defaultPrevented).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("leaves a submit a page script already handled", () => {
    const f = form('<form data-app-download method="post" action="/x/"></form>');
    f.addEventListener("submit", (e) => e.preventDefault(), { capture: true });
    submit(f);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("ignores submit events from non-forms", () => {
    const div = document.createElement("div");
    document.body.appendChild(div);
    div.dispatchEvent(new Event("submit", { bubbles: true }));
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

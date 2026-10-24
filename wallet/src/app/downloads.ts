/**
 * @file Exports and reports as files the user can save or send.
 *
 * The WebView ignores `Content-Disposition: attachment` on both platforms, so
 * tapping an export would do nothing. Links and forms marked
 * `data-app-download` are fetched here instead, written to the app's cache
 * and handed to the share sheet. A response that is not a file (an error page,
 * a "still processing" redirect) is shown the ordinary way.
 */

import { Directory, Filesystem } from "@capacitor/filesystem";
import { Share } from "@capacitor/share";

import { notify } from "../notify";

/** Shown when the file could not be fetched or saved. */
export const DOWNLOAD_ERROR = "The download failed. Please try again.";

/** Used when the response names no file. */
export const DEFAULT_FILENAME = "asastats-download";

/** A response that carries a file, with the name the server gave it. */
export interface DownloadedFile {
  filename: string;
  blob: Blob;
}

/**
 * Return the file name from a `Content-Disposition` header, or null when the
 * response is not an attachment.
 *
 * @param header - the header value, possibly null.
 * @returns a safe base name, or null.
 */
export function attachmentName(header: string | null): string | null {
  if (!header || !/^\s*attachment\b/i.test(header)) return null;
  const encoded = /filename\*\s*=\s*UTF-8''([^;]+)/i.exec(header);
  const quoted = /filename\s*=\s*"([^"]*)"/i.exec(header);
  const bare = /filename\s*=\s*([^;"\s]+)/i.exec(header);
  let name = "";
  if (encoded) {
    try {
      name = decodeURIComponent(encoded[1]);
    } catch {
      name = "";
    }
  }
  name = name || quoted?.[1] || bare?.[1] || "";
  // A base name only: never let the server pick a path inside the cache.
  name = name.replace(/^.*[\\/]/, "").replace(/[^\w.\- ]/g, "_").trim();
  return name && !/^\.+$/.test(name) ? name : DEFAULT_FILENAME;
}

/**
 * Fetch `url` and return the file it answers with, or null if it is not one.
 *
 * @param url - same-site URL.
 * @param init - fetch options (method, body).
 * @returns the file, or null with the response URL to show instead.
 */
export async function fetchFile(
  url: string,
  init: RequestInit = {}
): Promise<{ file: DownloadedFile | null; responseUrl: string }> {
  const response = await fetch(url, { credentials: "same-origin", ...init });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const filename = attachmentName(response.headers.get("Content-Disposition"));
  if (filename === null) return { file: null, responseUrl: response.url || url };
  return { file: { filename, blob: await response.blob() }, responseUrl: response.url };
}

/**
 * Return `blob` as base64, the form `Filesystem.writeFile` takes.
 *
 * @param blob - file contents.
 * @returns base64 without a data-URL prefix.
 */
export function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).replace(/^data:[^,]*,/, ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

/**
 * Write `file` to the cache directory and open the share sheet for it.
 *
 * @param file - the downloaded file.
 */
export async function shareFile(file: DownloadedFile): Promise<void> {
  const { uri } = await Filesystem.writeFile({
    path: file.filename,
    data: await blobToBase64(file.blob),
    directory: Directory.Cache,
  });
  try {
    await Share.share({ title: file.filename, files: [uri] });
  } catch (error) {
    // Closing the sheet rejects; that is the user's choice, not a failure.
    if (!/cancel/i.test(String((error as Error)?.message ?? error))) throw error;
  }
}

/**
 * Download `url` and share it; show the page instead if it is not a file.
 *
 * @param url - same-site URL.
 * @param init - fetch options.
 * @param fallback - shows a non-file response the ordinary way.
 * @param host - where an error notice goes.
 * @returns whether a file was shared.
 */
export async function download(
  url: string,
  init: RequestInit = {},
  fallback: (responseUrl: string) => void = (target) => window.location.assign(target),
  host: HTMLElement | null = null
): Promise<boolean> {
  try {
    const { file, responseUrl } = await fetchFile(url, init);
    if (file === null) {
      fallback(responseUrl);
      return false;
    }
    await shareFile(file);
    return true;
  } catch {
    notify(host, DOWNLOAD_ERROR);
    return false;
  }
}

/**
 * Take over taps on `a[data-app-download]`, and submits of a
 * `form[data-app-download]` or through a submit button carrying it.
 *
 * A form whose response is not a file is submitted again natively, so the
 * server's own page (validation errors, messages) shows as it would in a
 * browser.
 *
 * @param doc - the document to listen on.
 */
export function installDownloads(doc: Document = document): void {
  doc.addEventListener("click", (event) => {
    if (event.defaultPrevented || event.button !== 0) return;
    const anchor = (event.target as Element | null)?.closest?.("a[data-app-download]");
    if (!(anchor instanceof HTMLAnchorElement)) return;
    event.preventDefault();
    void download(anchor.href, {}, undefined, anchor.parentElement);
  });

  doc.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || event.defaultPrevented) return;
    const submitter = (event as SubmitEvent).submitter as HTMLButtonElement | null;
    if (!form.hasAttribute("data-app-download") && !submitter?.hasAttribute("data-app-download")) {
      return;
    }
    event.preventDefault();
    const body = new FormData(form);
    if (submitter?.name) body.append(submitter.name, submitter.value);
    const method = (form.getAttribute("method") || "GET").toUpperCase();
    const action = form.action;
    const url =
      method === "GET"
        ? `${action}${action.includes("?") ? "&" : "?"}${new URLSearchParams(
            body as unknown as Record<string, string>
          )}`
        : action;
    void download(
      url,
      method === "GET" ? {} : { method, body },
      () => {
        form.removeAttribute("data-app-download");
        submitter?.removeAttribute("data-app-download");
        form.requestSubmit(submitter ?? undefined);
      },
      form
    );
  });
}

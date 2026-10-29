/**
 * @file Social sign-in in the app. Apple (iOS) and Google use the platform's own
 * sheet (O3): its ID token is posted from this page, so this session signs in.
 * The rest, and any phone without the sheet, go through the system browser
 * (F4): the WebAuth sheet returns a one-time ticket, traded here for a session.
 *
 * Server side: `core/views_appnative.py`, `core/views_appauth.py`. Native side:
 * mobile/ `NativeSignIn` and `WebAuth` plugins.
 */

import { registerPlugin } from "@capacitor/core";

import { csrfToken } from "./push";

/** The local plugin in mobile/; it builds the start URL itself. */
export interface WebAuthPlugin {
  start(options: { provider: string; challenge: string; next?: string }): Promise<{ url: string }>;
}

export const WebAuth = registerPlugin<WebAuthPlugin>("WebAuth");

/** What a native sheet returns; Apple adds the code and, the first time, the name. */
export interface NativeSignInResult {
  idToken: string;
  authorizationCode?: string;
  givenName?: string;
  familyName?: string;
}

/** The local plugin in mobile/ (O3); app versions without it reject every call. */
export interface NativeSignInPlugin {
  isAvailable(options: { provider: string }): Promise<{ available: boolean }>;
  signIn(options: {
    provider: string;
    nonce: string;
    serverClientId?: string;
  }): Promise<NativeSignInResult>;
}

export const NativeSignIn = registerPlugin<NativeSignInPlugin>("NativeSignIn");

/** Must match frontend `NATIVE_PROVIDERS` and the native-sign-in URLs. */
export const NATIVE_PROVIDERS = ["apple", "google"];
export const NATIVE_NONCE_PATH = "/app/auth/native/nonce/";
export const NATIVE_PATH = "/app/auth/native/";

/** Must match `app_auth_return` and the plugin's callback path. */
export const RETURN_PATH = "/app/auth/return/";
export const REDEEM_PATH = "/app/auth/redeem/";

export const MESSAGES = {
  unsupported:
    "Social sign-in in the app needs iOS 17.4 or later, or Chrome 137 or later on Android. " +
    "Sign in with email or a wallet, or link this sign-in on the website.",
  failed: "Sign-in did not finish. Try again.",
  connectOnWebsite: "Add a Google account to this phone first, or connect Google on the website.",
};

/**
 * Encode bytes as base64url without padding.
 *
 * @param bytes - the bytes.
 * @returns the text.
 */
export function base64url(bytes: Uint8Array): string {
  let binary = "";
  bytes.forEach((byte) => (binary += String.fromCharCode(byte)));
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/**
 * Make a fresh secret: 32 random bytes, 43 characters.
 *
 * @returns the verifier.
 */
export function makeVerifier(): string {
  return base64url(crypto.getRandomValues(new Uint8Array(32)));
}

/**
 * The server's `challenge_for`: base64url SHA-256 of the verifier.
 *
 * @param verifier - the secret.
 * @returns the challenge.
 */
export async function challengeFor(verifier: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
  return base64url(new Uint8Array(digest));
}

/**
 * The page to land on after sign-in: the `next` parameter, else this page,
 * except the sign-in pages themselves (the server then uses its default).
 *
 * @param location - where the reader is.
 * @returns a path, or undefined.
 */
export function nextFor(location: Location): string | undefined {
  const next = new URLSearchParams(location.search).get("next");
  if (next) return next;
  if (location.pathname.startsWith("/accounts/")) return undefined;
  return location.pathname + location.search;
}

/**
 * Return the ticket from the sheet's callback URL, if it is ours.
 *
 * @param url - what the plugin returned.
 * @param origin - this site's origin.
 * @returns the ticket, or null.
 */
export function ticketFrom(url: string, origin: string): string | null {
  try {
    const parsed = new URL(url);
    if (parsed.origin !== origin || parsed.pathname !== RETURN_PATH) return null;
    return parsed.searchParams.get("ticket") || null;
  } catch {
    return null;
  }
}

/**
 * POST `fields` and the CSRF token as a hidden form, so nothing lands in
 * history and the server's answer (a redirect, a signup form) is the next page.
 *
 * @param action - same-site path.
 * @param fields - the values to send.
 * @param doc - the document to submit from.
 */
export function postForm(action: string, fields: Record<string, string>, doc: Document = document): void {
  const form = doc.createElement("form");
  form.method = "POST";
  form.action = action;
  form.hidden = true;
  for (const [name, value] of Object.entries({ ...fields, csrfmiddlewaretoken: csrfToken() })) {
    const input = doc.createElement("input");
    input.type = "hidden";
    input.name = name;
    input.value = value;
    form.appendChild(input);
  }
  doc.body.appendChild(form);
  form.submit();
}

/**
 * POST the ticket and verifier, so neither lands in history.
 *
 * @param ticket - from the callback.
 * @param verifier - the secret.
 * @param doc - the document to submit from.
 */
export function redeem(ticket: string, verifier: string, doc: Document = document): void {
  postForm(REDEEM_PATH, { ticket, verifier }, doc);
}

/**
 * Whether this phone has a native sheet for `provider`.
 *
 * @param provider - an allauth provider id.
 * @returns false for other providers and for app versions without the plugin.
 */
export async function nativeAvailable(provider: string): Promise<boolean> {
  if (!NATIVE_PROVIDERS.includes(provider)) return false;
  try {
    return (await NativeSignIn.isAvailable({ provider })).available === true;
  } catch {
    return false;
  }
}

/**
 * Ask the server for this session's single-use nonce.
 *
 * @returns the nonce and the website's Google client id.
 */
export async function fetchNonce(): Promise<{ nonce: string; google_client_id: string }> {
  const response = await fetch(NATIVE_NONCE_PATH, {
    method: "POST",
    credentials: "same-origin",
    headers: { "X-CSRFToken": csrfToken() },
  });
  if (!response.ok) throw new Error("failed");
  return response.json();
}

/**
 * Sign in or connect with a native sheet.
 *
 * @param provider - `apple` or `google`.
 * @param process - `login`, or `connect` on the Connections page.
 * @param next - where a login lands.
 * @param say - shows a message to the reader.
 * @returns `sent` when the token form was posted, `fallback` when the phone has
 *   no account for the sheet, `stopped` otherwise.
 */
export async function nativeSignIn(
  provider: string,
  process: "login" | "connect",
  next: string | undefined,
  say: (message: string) => void
): Promise<"sent" | "fallback" | "stopped"> {
  let result: NativeSignInResult;
  try {
    const { nonce, google_client_id: serverClientId } = await fetchNonce();
    result = await NativeSignIn.signIn({ provider, nonce, serverClientId });
  } catch (error) {
    const reason = (error as Error)?.message;
    if (reason === "unavailable") return "fallback";
    if (reason !== "cancelled" && reason !== "busy") say(MESSAGES.failed);
    return "stopped";
  }
  const fields: Record<string, string> = { provider, process, id_token: result.idToken };
  if (result.authorizationCode) fields.code = result.authorizationCode;
  if (result.givenName) fields.first_name = result.givenName;
  if (result.familyName) fields.last_name = result.familyName;
  if (next && process === "login") fields.next = next;
  postForm(NATIVE_PATH, fields);
  return "sent";
}

/**
 * Sign in with `provider`: its native sheet where the phone has one, else the
 * system browser.
 *
 * @param provider - an allauth provider id, as `data-app-signin` names it.
 * @param next - where to land; see `nextFor`.
 * @param say - shows a message to the reader.
 * @returns whether the redeem form was sent.
 */
export async function signIn(
  provider: string,
  next: string | undefined = nextFor(window.location),
  say: (message: string) => void = (message) => window.alert(message)
): Promise<boolean> {
  if (await nativeAvailable(provider)) {
    const outcome = await nativeSignIn(provider, "login", next, say);
    if (outcome !== "fallback") return outcome === "sent";
  }
  let url: string;
  const verifier = makeVerifier();
  try {
    const challenge = await challengeFor(verifier);
    ({ url } = await WebAuth.start({ provider, challenge, next }));
  } catch (error) {
    const reason = (error as Error)?.message;
    if (reason === "cancelled" || reason === "busy") return false;
    say(reason === "unsupported" ? MESSAGES.unsupported : MESSAGES.failed);
    return false;
  }
  const ticket = ticketFrom(url, window.location.origin);
  if (!ticket) {
    say(MESSAGES.failed);
    return false;
  }
  redeem(ticket, verifier);
  return true;
}

/**
 * Connect `provider` to the signed-in account with its native sheet.
 *
 * @param provider - `apple` or `google`.
 * @param say - shows a message to the reader.
 * @returns whether the token form was sent.
 */
export async function connect(
  provider: string,
  say: (message: string) => void = (message) => window.alert(message)
): Promise<boolean> {
  const outcome = await nativeSignIn(provider, "connect", undefined, say);
  if (outcome === "fallback") say(MESSAGES.connectOnWebsite);
  return outcome === "sent";
}

/**
 * Arm the Connections page's `data-app-connect` buttons this phone has a sheet
 * for: show them (`hidden` in the template) and hide their website-only note.
 *
 * @param doc - the page.
 */
export async function armConnect(doc: Document = document): Promise<void> {
  for (const button of Array.from(doc.querySelectorAll<HTMLElement>("[data-app-connect]"))) {
    const provider = button.dataset.appConnect as string;
    if (!(await nativeAvailable(provider))) continue;
    button.dataset.appConnectReady = "";
    button.hidden = false;
    doc.querySelectorAll<HTMLElement>(`[data-app-connect-fallback="${provider}"]`).forEach((note) => {
      note.hidden = true;
    });
  }
}

/**
 * Send clicks on `data-app-signin` buttons to `signIn`, and on armed
 * `data-app-connect` buttons to `connect`, instead of their href.
 *
 * @param doc - the document to listen on.
 */
export function installSignIn(doc: Document = document): void {
  doc.addEventListener("click", (event) => {
    if (event.defaultPrevented || event.button !== 0) return;
    const target = event.target as Element | null;
    const connectButton = target?.closest?.("[data-app-connect-ready]");
    if (connectButton instanceof HTMLElement) {
      event.preventDefault();
      void connect(connectButton.dataset.appConnect as string);
      return;
    }
    const button = target?.closest?.("[data-app-signin]");
    if (!(button instanceof HTMLElement)) return;
    event.preventDefault();
    void signIn(button.dataset.appSignin as string);
  });
  void armConnect(doc);
}

/**
 * @file Social sign-in through the system browser (F4): the native WebAuth sheet
 * returns a one-time ticket, which this page trades for a session.
 *
 * Server side: `core/views_appauth.py`. Native side: mobile/ `WebAuth` plugin.
 */

import { registerPlugin } from "@capacitor/core";

import { csrfToken } from "./push";

/** The local plugin in mobile/; it builds the start URL itself. */
export interface WebAuthPlugin {
  start(options: { provider: string; challenge: string; next?: string }): Promise<{ url: string }>;
}

export const WebAuth = registerPlugin<WebAuthPlugin>("WebAuth");

/** Must match `app_auth_return` and the plugin's callback path. */
export const RETURN_PATH = "/app/auth/return/";
export const REDEEM_PATH = "/app/auth/redeem/";

export const MESSAGES = {
  unsupported:
    "Social sign-in in the app needs iOS 17.4 or later, or Chrome 137 or later on Android. " +
    "Sign in with email or a wallet, or link this sign-in on the website.",
  failed: "Sign-in did not finish. Try again.",
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
 * POST the ticket and verifier as a form, so neither lands in history.
 *
 * @param ticket - from the callback.
 * @param verifier - the secret.
 * @param doc - the document to submit from.
 */
export function redeem(ticket: string, verifier: string, doc: Document = document): void {
  const form = doc.createElement("form");
  form.method = "POST";
  form.action = REDEEM_PATH;
  form.hidden = true;
  const fields: Record<string, string> = {
    ticket,
    verifier,
    csrfmiddlewaretoken: csrfToken(),
  };
  for (const [name, value] of Object.entries(fields)) {
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
 * Sign in with `provider` through the system browser.
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
 * Send clicks on `data-app-signin` buttons to `signIn` instead of their href.
 *
 * @param doc - the document to listen on.
 */
export function installSignIn(doc: Document = document): void {
  doc.addEventListener("click", (event) => {
    if (event.defaultPrevented || event.button !== 0) return;
    const button = (event.target as Element | null)?.closest?.("[data-app-signin]");
    if (!(button instanceof HTMLElement)) return;
    event.preventDefault();
    void signIn(button.dataset.appSignin as string);
  });
}

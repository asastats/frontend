import { TextEncoder, TextDecoder } from "util";

// Provide Node globals the browser-targeted code expects under jsdom.
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as any;

// Default fetch mock; individual tests override the implementation.
global.fetch = jest.fn();

// Writable window.location so auth() redirects can be asserted.
Object.defineProperty(window, "location", {
  value: { href: "" },
  writable: true,
});

// btoa shim for base64 encoding of signed transaction bytes.
global.btoa = (str: string) => Buffer.from(str, "binary").toString("base64");

afterEach(() => {
  jest.clearAllMocks();
});

import { Capacitor } from "@capacitor/core";

import {
  FlutterData,
  RECENT_KEY,
  SEEDED_KEY,
  installFlutterAddresses,
  mergeEntries,
  seedFlutterAddresses,
  validEntries,
} from "./flutterAddresses";

jest.mock("@capacitor/core", () => ({
  Capacitor: { isPluginAvailable: jest.fn() },
  registerPlugin: jest.fn(() => ({ readAddresses: jest.fn() })),
}));

const available = Capacitor.isPluginAvailable as jest.Mock;
const read = FlutterData.readAddresses as jest.Mock;
const A = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU";
const B = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU";
const stored = () => JSON.parse(localStorage.getItem(RECENT_KEY) ?? "null");

describe("validEntries", () => {
  it("splits multi-address strings and keeps addresses and .algo names", () => {
    expect(validEntries([`${A},${B}`, "x.algo/nfd", 7, "bad", A.toLowerCase(), `${A} y.algo`])).toEqual([
      A,
      B,
      "x.algo/nfd",
      A,
      "y.algo",
    ]);
  });
});

describe("mergeEntries", () => {
  it("puts the app's own first, drops repeats and caps at twenty", () => {
    expect(mergeEntries(["a.algo", A], [A, "b.algo"])).toEqual(["a.algo", A, "b.algo"]);
    const many = Array.from({ length: 25 }, (_, i) => `n${i}.algo`);
    expect(mergeEntries([A], many)).toHaveLength(20);
  });
});

describe("seedFlutterAddresses", () => {
  beforeEach(() => {
    localStorage.clear();
    available.mockReset().mockReturnValue(true);
    read.mockReset().mockResolvedValue({ addresses: [`${A},${B}`, "old.algo"] });
  });

  it("merges Flutter's entries after the app's own and sets the flag", async () => {
    localStorage.setItem(RECENT_KEY, JSON.stringify(["new.algo", B]));

    await expect(seedFlutterAddresses()).resolves.toBe(true);
    expect(stored()).toEqual(["new.algo", B, A, "old.algo"]);
    expect(localStorage.getItem(SEEDED_KEY)).toBe("1");
  });

  it("seeds an empty list", async () => {
    await seedFlutterAddresses();
    expect(stored()).toEqual([A, B, "old.algo"]);
  });

  it("runs only once", async () => {
    await seedFlutterAddresses();
    localStorage.setItem(RECENT_KEY, "[]");

    await expect(seedFlutterAddresses()).resolves.toBe(false);
    expect(read).toHaveBeenCalledTimes(1);
    expect(stored()).toEqual([]);
  });

  it("waits for a shell with the plugin, without setting the flag", async () => {
    available.mockReturnValue(false);

    await expect(seedFlutterAddresses()).resolves.toBe(false);
    expect(read).not.toHaveBeenCalled();
    expect(localStorage.getItem(SEEDED_KEY)).toBeNull();
  });

  it("leaves the flag unset when the read fails", async () => {
    read.mockRejectedValue(new Error("native"));

    await expect(seedFlutterAddresses()).resolves.toBe(false);
    expect(localStorage.getItem(SEEDED_KEY)).toBeNull();
  });

  it("sets the flag without touching the list when Flutter saved nothing usable", async () => {
    localStorage.setItem(RECENT_KEY, JSON.stringify([B]));
    read.mockResolvedValue({ addresses: ["junk"] });

    await expect(seedFlutterAddresses()).resolves.toBe(true);
    expect(stored()).toEqual([B]);
    expect(localStorage.getItem(SEEDED_KEY)).toBe("1");
  });

  it("treats a missing addresses array as nothing saved", async () => {
    read.mockResolvedValue({});

    await expect(seedFlutterAddresses()).resolves.toBe(true);
    expect(localStorage.getItem(RECENT_KEY)).toBeNull();
  });

  it("replaces a stored list it cannot read", async () => {
    localStorage.setItem(RECENT_KEY, "{");
    await seedFlutterAddresses();
    expect(stored()).toEqual([A, B, "old.algo"]);

    localStorage.clear();
    localStorage.setItem(RECENT_KEY, JSON.stringify({ a: 1 }));
    await seedFlutterAddresses();
    expect(stored()).toEqual([A, B, "old.algo"]);
  });

  it("returns false when storage is unavailable", async () => {
    const broken = {
      getItem: () => {
        throw new Error("blocked");
      },
    } as unknown as Storage;

    await expect(seedFlutterAddresses(broken)).resolves.toBe(false);
  });
});

describe("installFlutterAddresses", () => {
  it("starts the seeding", async () => {
    localStorage.clear();
    available.mockReturnValue(true);
    read.mockResolvedValue({ addresses: ["start.algo"] });

    installFlutterAddresses();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(stored()).toEqual(["start.algo"]);
  });
});

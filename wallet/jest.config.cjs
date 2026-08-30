module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  transform: {
    "^.+\\.(ts|tsx)$": ["ts-jest", { tsconfig: "tsconfig.test.json" }],
  },
  transformIgnorePatterns: [
    "node_modules/(?!(@txnlab/use-wallet|@perawallet/connect|@blockshake/defly-connect|lute-connect|viem|@walletconnect)/)",
  ],
  testMatch: ["**/?(*.)+(spec|test).ts"],

  // Every source module, and the exclusions are spelled out rather than left
  // to be discovered. This used to name five modules to skip while four more
  // carried `/* istanbul ignore file */` in their own first line, so the
  // reported "100%" was over seven files of twelve and nothing said so. The
  // one that mattered was `swapBootstrap.ts`, which publishes the whole
  // `window.asastatsSwap` surface: anything added there landed outside the
  // number by default.
  //
  // Only two files are left out now, both because they cannot be covered
  // rather than because covering them is awkward:
  //
  //   *.d.ts        - type declarations, no runtime statements to execute.
  //   setupTests.ts - a `setupFilesAfterEnv` file. Jest loads it before
  //                   instrumentation, so it is never reported even though
  //                   every one of the tests below runs it. Listed explicitly
  //                   because it *is* instrumentable if it stops being a setup
  //                   file, and a silent absence is what this comment exists
  //                   to prevent.
  collectCoverageFrom: [
    "src/**/*.ts",
    "!src/**/*.d.ts",
    "!src/**/*.test.ts",
    "!src/setupTests.ts",
  ],

  // The number is now load-bearing, so it is enforced rather than reported.
  // Without this, a new module arrives uncovered and the summary quietly
  // drops a few points that nobody reads.
  coverageThreshold: {
    global: { statements: 100, branches: 100, functions: 100, lines: 100 },
  },

  setupFilesAfterEnv: ["<rootDir>/src/setupTests.ts"],
  coverageDirectory: "coverage",
  coverageReporters: ["text", "lcov", "html"],
};

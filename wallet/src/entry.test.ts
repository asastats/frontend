const loaded = jest.fn();

jest.mock("./main", () => {
  loaded();
  return {};
});

it("loads main.ts", async () => {
  await import("./entry");
  await new Promise((resolve) => setTimeout(resolve, 0));
  expect(loaded).toHaveBeenCalledTimes(1);
});

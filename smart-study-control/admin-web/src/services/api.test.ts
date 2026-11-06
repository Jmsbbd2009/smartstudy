import { describe, it, expect, afterEach, vi } from "vitest";
import { UserSchema, setSession, getSession, api, uploadPdf } from "./api";
describe("authentication boundary", () => {
  it("rejects unknown privileged roles", () => {
    expect(() =>
      UserSchema.parse({ id: "1", name: "Ali", email: "x@y.z", role: "ROOT" }),
    ).toThrow();
  });
  it("requires both rotating credentials and validated user", () => {
    expect(() => setSession({ access_token: "x" })).toThrow();
  });
  it("clears authenticated state on sign out", () => {
    setSession({
      access_token: "a",
      refresh_token: "r",
      user: { id: "1", name: "Ali", email: "x@y.z", role: "PARENT" },
    });
    expect(getSession()?.user.role).toBe("PARENT");
    setSession(null);
    expect(getSession()).toBeNull();
  });
});

describe("credential expiry during critical writes", () => {
  const session = {
    access_token: "old",
    refresh_token: "rotation-1",
    user: { id: "1", name: "Ali", email: "x@y.z", role: "PARENT" },
  };
  afterEach(() => {
    setSession(null);
    vi.unstubAllGlobals();
  });
  it("preserves the idempotency key after token rotation", async () => {
    setSession(session);
    const transport = vi
      .fn()
      .mockResolvedValueOnce(new Response("{}", { status: 401 }))
      .mockResolvedValueOnce(
        Response.json({
          ...session,
          access_token: "new",
          refresh_token: "rotation-2",
        }),
      )
      .mockResolvedValueOnce(Response.json({ id: "same-attempt" }));
    vi.stubGlobal("fetch", transport);
    await api("reading/plans/p/lessons/l/attempts", "POST", {});
    const first = transport.mock.calls[0][1];
    const retry = transport.mock.calls[2][1];
    expect(first.headers["Idempotency-Key"]).toBe(
      retry.headers["Idempotency-Key"],
    );
    expect(retry.headers.Authorization).toBe("Bearer new");
  });
  it("retries the actual PDF body with a refreshed credential", async () => {
    setSession(session);
    const transport = vi
      .fn()
      .mockResolvedValueOnce(new Response("{}", { status: 401 }))
      .mockResolvedValueOnce(
        Response.json({
          ...session,
          access_token: "new",
          refresh_token: "rotation-2",
        }),
      )
      .mockResolvedValueOnce(Response.json({ id: "book" }));
    vi.stubGlobal("fetch", transport);
    await uploadPdf(
      "books",
      "Science",
      new File(["%PDF-1.4"], "book.pdf", { type: "application/pdf" }),
    );
    expect(transport.mock.calls[2][1].body).toBe(
      transport.mock.calls[0][1].body,
    );
    expect(transport.mock.calls[2][1].headers.get("Authorization")).toBe(
      "Bearer new",
    );
    expect(getSession()?.refresh_token).toBe("rotation-2");
  });
});

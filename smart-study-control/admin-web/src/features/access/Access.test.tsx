// @vitest-environment jsdom
import { afterEach, describe, it, expect, vi } from "vitest";
import { startTelegram } from "./Access";
import { setSession } from "../../services/api";
afterEach(() => {
  setSession(null);
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
describe("Telegram redirect boundary", () => {
  it("opens the real bot directly after a validated challenge", async () => {
    const popup = {
      opener: {},
      location: { replace: vi.fn() },
      close: vi.fn(),
    };
    vi.spyOn(window, "open").mockReturnValue(popup as any);
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        Response.json({
          deep_link: "https://t.me/TestBot?start=login_example",
          challenge_id: "c",
          verifier: "v",
        }),
      ),
    );
    const ready = vi.fn();
    await startTelegram("auth/telegram/login/start", { login: "staff" }, ready);
    expect(popup.opener).toBeNull();
    expect(popup.location.replace).toHaveBeenCalledWith(
      "https://t.me/TestBot?start=login_example",
    );
    expect(ready).toHaveBeenCalled();
  });
  it("rejects an untrusted redirect before opening it", async () => {
    const popup = {
      opener: {},
      location: { replace: vi.fn() },
      close: vi.fn(),
    };
    vi.spyOn(window, "open").mockReturnValue(popup as any);
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        Response.json({ deep_link: "https://evil.example/steal" }),
      ),
    );
    await expect(
      startTelegram("auth/telegram/login/start", {}, vi.fn()),
    ).rejects.toThrow();
    expect(popup.location.replace).not.toHaveBeenCalled();
    expect(popup.close).toHaveBeenCalled();
  });
  it("keeps the challenge available when the browser blocks popups", async () => {
    vi.spyOn(window, "open").mockReturnValue(null);
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        Response.json({ deep_link: "https://t.me/TestBot?start=login_x" }),
      ),
    );
    const ready = vi.fn();
    await startTelegram("auth/telegram/login/start", {}, ready);
    expect(ready).toHaveBeenCalled();
  });
});

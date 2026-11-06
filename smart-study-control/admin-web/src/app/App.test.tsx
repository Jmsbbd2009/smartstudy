// @vitest-environment jsdom
import { afterEach, describe, it, expect, vi } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App } from "./App";
import { setSession } from "../services/api";
function renderApp() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  );
}
afterEach(() => {
  cleanup();
  setSession(null);
  vi.unstubAllGlobals();
});
describe("role and authentication UI", () => {
  it("keeps failed credentials outside the authenticated dashboard", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({ error: { message: "Invalid credentials" } }),
            { status: 401, headers: { "Content-Type": "application/json" } },
          ),
      ),
    );
    renderApp();
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "wrong@example.test" },
    });
    fireEvent.change(screen.getByLabelText("Parol"), {
      target: { value: "wrong-password-123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Kirish" }));
    await waitFor(() =>
      expect(screen.getByRole("alert").textContent).toContain(
        "Invalid credentials",
      ),
    );
    expect(screen.queryByRole("navigation")).toBeNull();
  });
  it("offers teachers academic navigation without household device access", async () => {
    setSession({
      access_token: "test-access",
      refresh_token: "test-refresh",
      user: {
        id: "teacher",
        name: "Test Teacher",
        email: "teacher@example.test",
        role: "TEACHER",
      },
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response("[]", {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
      ),
    );
    renderApp();
    expect(screen.getByRole("button", { name: "Sinflar" })).toBeDefined();
    expect(screen.queryByRole("button", { name: "Qurilmalar" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Sinflar" }));
    await waitFor(() =>
      expect(screen.getByLabelText("Sinf nomi")).toBeDefined(),
    );
  });
  it("offers guardians the authorized household device workflow", async () => {
    setSession({
      access_token: "test-access",
      refresh_token: "test-refresh",
      user: {
        id: "parent",
        name: "Test Parent",
        email: "parent@example.test",
        role: "PARENT",
      },
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response("[]", {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
      ),
    );
    renderApp();
    fireEvent.click(screen.getByRole("button", { name: "Qurilmalar" }));
    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: "Qurilma va ekran vaqti" }),
      ).toBeDefined(),
    );
    expect(screen.getByLabelText("Farzand")).toBeDefined();
  });
});

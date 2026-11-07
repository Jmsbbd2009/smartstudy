// @vitest-environment jsdom
import { afterEach, describe, it, expect, vi } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
  within,
  configure,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { File as NativeFile, Blob as NativeBlob } from "node:buffer";
import fs from "node:fs";
import { App } from "./App";
import { setSession } from "../services/api";
configure({ asyncUtilTimeout: 8000 });
afterEach(() => {
  cleanup();
  setSession(null);
  vi.unstubAllGlobals();
});
describe.skipIf(process.env.LIVE_E2E !== "1")(
  "real HTTP staff management",
  () => {
    it("provisions staff, renews credentials, delivers and acknowledges actual notifications", async () => {
      vi.stubGlobal("Blob", NativeBlob);
      vi.stubGlobal("File", NativeFile);
      const { fetch: transport, FormData: NativeFormData } =
        await import("undici");
      vi.stubGlobal("fetch", transport);
      vi.stubGlobal("FormData", NativeFormData);
      const checks: string[] = [];
      const password = process.env.TEST_ACCOUNT_PASSWORD!;
      const client = new QueryClient({
        defaultOptions: {
          queries: { retry: false },
          mutations: { retry: false },
        },
      });
      render(
        <QueryClientProvider client={client}>
          <App />
        </QueryClientProvider>,
      );
      async function login(name: string, pass: string) {
        fireEvent.change(screen.getByLabelText("Email", { exact: true }), {
          target: { value: name },
        });
        fireEvent.change(screen.getByLabelText("Parol", { exact: true }), {
          target: { value: pass },
        });
        fireEvent.click(screen.getByRole("button", { name: "Kirish" }));
      }
      async function logout() {
        fireEvent.click(screen.getByRole("button", { name: "Chiqish" }));
        await screen.findByRole("heading", { name: "Xush kelibsiz" });
      }
      await login("555 1234567", password);
      await screen.findByRole("navigation");
      checks.push("Normalized numeric super admin login");
      fireEvent.click(screen.getByRole("button", { name: "Xodimlar" }));
      await screen.findByRole("heading", { name: "Xodimlar boshqaruvi" });
      function fill(label: string, value: string) {
        fireEvent.change(screen.getByLabelText(label, { exact: true }), {
          target: { value },
        });
      }
      fill("Ism", "HTTP School Admin");
      fill("Email", "http.admin@example.test");
      fill("Login", "http.admin");
      fill("Vaqtinchalik parol", "Temporary-Password-456");
      fill("Yangi maktab nomi", "HTTP school");
      fireEvent.click(screen.getByRole("button", { name: "Xodim yaratish" }));
      await screen.findByText("HTTP School Admin", { exact: true });
      checks.push("Super admin creates real school administrator");
      fireEvent.change(screen.getByLabelText("Rol", { exact: true }), {
        target: { value: "TEACHER" },
      });
      await screen.findByRole("option", { name: "HTTP school" });
      fill("Ism", "HTTP Teacher");
      fill("Email", "http.teacher@example.test");
      fill("Login", "http.teacher");
      fill("Vaqtinchalik parol", "Temporary-Password-456");
      fireEvent.change(screen.getByLabelText("Maktab", { exact: true }), {
        target: {
          value: (
            screen.getByRole("option", {
              name: "HTTP school",
            }) as HTMLOptionElement
          ).value,
        },
      });
      fireEvent.click(screen.getByRole("button", { name: "Xodim yaratish" }));
      await screen.findByText("HTTP Teacher", { exact: true });
      checks.push("Super admin assigns real teacher to selected school");
      const teacher = screen
        .getByText("HTTP Teacher", { exact: true })
        .closest("article")!;
      fireEvent.click(within(teacher).getByRole("checkbox"));
      fill("Sarlavha", "Darsga tayyorlanish");
      fill("Xabar", "Ertaga yangi mavzuni muhokama qilamiz.");
      fireEvent.click(
        screen.getByRole("button", { name: "Tanlangan xodimlarga yuborish" }),
      );
      await waitFor(() =>
        expect(
          (screen.getByLabelText("Sarlavha", {}) as HTMLInputElement).value,
        ).toBe(""),
      );
      checks.push("Staff announcement persisted on real backend");
      await logout();
      await login("http.teacher", "Temporary-Password-456");
      await screen.findByRole("heading", { name: "Parolni yangilang" });
      expect(screen.queryByRole("navigation")).toBeNull();
      checks.push("Temporary credential cannot enter teacher dashboard");
      fill("Hozirgi parol", "Temporary-Password-456");
      fill("Yangi parol", "Fresh-Teacher-Password-987");
      fireEvent.click(
        screen.getByRole("button", { name: "Yangi parolni saqlash" }),
      );
      await screen.findByRole("navigation");
      expect(screen.queryByRole("button", { name: "Xodimlar" })).toBeNull();
      expect(screen.queryByRole("button", { name: "Qurilmalar" })).toBeNull();
      checks.push(
        "Teacher renews password and receives least-privilege navigation",
      );
      fireEvent.click(screen.getByRole("button", { name: "Bildirishnomalar" }));
      await screen.findByText("Darsga tayyorlanish", { exact: true });
      const note = screen
        .getByText("Darsga tayyorlanish", { exact: true })
        .closest("article")!;
      fireEvent.click(within(note).getByRole("button", { name: "O‘qildi" }));
      await waitFor(() =>
        expect(
          within(note).queryByRole("button", { name: "O‘qildi" }),
        ).toBeNull(),
      );
      checks.push("Teacher receives and acknowledges persisted announcement");
      fs.writeFileSync(
        process.env.TEST_ACCESS_RESULTS_JSON!,
        JSON.stringify(
          {
            passed: checks.length,
            checks,
            transport:
              "Real React DOM + actual HTTP to disposable FastAPI/SQLite; no mocked responses",
            native_biometrics:
              "not exercised; cryptographic signature validation tested separately",
          },
          null,
          2,
        ),
      );
    }, 100000);
  },
);

// @vitest-environment jsdom
import { afterEach, describe, it, expect, vi } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
  cleanup,
  configure,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { File as NativeFile, Blob as NativeBlob } from "node:buffer";
import fs from "node:fs";
import { App } from "./App";
import { setSession } from "../services/api";
const enabled = process.env.LIVE_E2E === "1";
configure({ asyncUtilTimeout: 8000 });
afterEach(() => {
  cleanup();
  setSession(null);
  vi.unstubAllGlobals();
});
describe.skipIf(!enabled)("live admin PDF to reward workflow", () => {
  it("uploads, validates, assigns, grades and rewards through actual HTTP", async () => {
    vi.stubGlobal("Blob", NativeBlob);
    vi.stubGlobal("File", NativeFile);
    const { fetch: nativeFetch, FormData: NativeFormData } =
      await import("undici");
    vi.stubGlobal("fetch", nativeFetch);
    vi.stubGlobal("FormData", NativeFormData);
    const api = process.env.TEST_API_URL!;
    const password = process.env.TEST_ACCOUNT_PASSWORD!;
    const checks: string[] = [];
    const account = async (email: string) => {
      const response = await nativeFetch(api + "/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      expect(response.status).toBe(200);
      return (await response.json()) as any;
    };
    const parent = await account("parent.e2e@example.test");
    const child = (
      (await nativeFetch(api + "/families/children", {
        headers: { Authorization: `Bearer ${parent.access_token}` },
      }).then((r) => r.json())) as any[]
    )[0];
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
    async function login(email: string) {
      fireEvent.change(screen.getByLabelText("Email", { exact: true }), {
        target: { value: email },
      });
      fireEvent.change(screen.getByLabelText("Parol", { exact: true }), {
        target: { value: password },
      });
      fireEvent.click(screen.getByRole("button", { name: "Kirish" }));
      await screen.findByRole("navigation");
    }
    async function logout() {
      fireEvent.click(screen.getByRole("button", { name: "Chiqish" }));
      await screen.findByRole("heading", { name: "Xush kelibsiz" });
    }
    await login("parent.e2e@example.test");
    checks.push("Real parent login");
    fireEvent.click(screen.getByRole("button", { name: "AI boshqaruv" }));
    await screen.findByRole("option", { name: child.name });
    fireEvent.change(await screen.findByLabelText("Farzand", { exact: true }), {
      target: { value: child.id },
    });
    const toggle = await screen.findByLabelText(
      "Avtopilotga ruxsat berish",
      {},
    );
    fireEvent.click(toggle);
    fireEvent.click(
      screen.getByRole("button", { name: "Avtopilot sozlamalarini saqlash" }),
    );
    await waitFor(async () => {
      const c = (await nativeFetch(api + `/automation/children/${child.id}`, {
        headers: { Authorization: `Bearer ${parent.access_token}` },
      }).then((r) => r.json())) as any;
      expect(c.enabled).toBe(true);
    });
    checks.push("Guardian config saved on real backend");
    fireEvent.click(
      screen.getByRole("button", { name: "Kitoblar va AI test" }),
    );
    fireEvent.change(screen.getByLabelText("Kitob nomi", { exact: true }), {
      target: { value: "DOM test kitobi" },
    });
    const bytes = fs.readFileSync(process.env.TEST_BOOK_PDF!);
    const file = new NativeFile([bytes], "source.pdf", {
      type: "application/pdf",
    });
    fireEvent.change(screen.getByLabelText("PDF kitob", { exact: true }), {
      target: { files: [file] },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: "Kitobni yuklash" }).closest("form")!,
    );
    await screen.findByRole(
      "heading",
      { name: "DOM test kitobi" },
      { timeout: 15000 },
    );
    const facts = [
      "Water freezes at zero degrees Celsius.",
      "Plants use sunlight to make food.",
      "Earth travels around the Sun once each year.",
    ];
    await screen.findByText(facts[0], { exact: true });
    checks.push("Real PDF upload, extraction and source-page UI");
    fireEvent.click(
      screen.getByRole("button", { name: "AI dars va test yaratish" }),
    );
    await screen.findByText(/AI is not configured/);
    checks.push("Missing live AI credentials produce a visible error");
    fireEvent.click(screen.getByRole("button", { name: "Qo‘lda dars tuzish" }));
    fireEvent.change(screen.getByLabelText("Dars nomi", { exact: true }), {
      target: { value: "Tabiatning uch qoidasi" },
    });
    fireEvent.change(
      screen.getByLabelText("Qisqa tushuntirish", { exact: true }),
      { target: { value: "Suv, o‘simliklar va Yer haqidagi manbali dars." } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Tushuncha qo‘shish" }));
    fireEvent.click(screen.getByRole("button", { name: "Tushuncha qo‘shish" }));
    for (let i = 0; i < 3; i++) {
      const section = within(
        document.querySelectorAll(".editor-section")[i] as HTMLElement,
      );
      fireEvent.change(
        section.getByLabelText(`Tushuncha ${i + 1}`, { exact: true }),
        { target: { value: ["Suv", "O‘simliklar", "Yer"][i] } },
      );
      fireEvent.change(
        section.getByLabelText("Tushuntirish", { exact: true }),
        { target: { value: facts[i] } },
      );
      fireEvent.change(
        section.getByLabelText("Manba sahifasi", { exact: true }),
        { target: { value: String(i + 1) } },
      );
      fireEvent.change(
        section.getByLabelText("Kitobdan aynan olingan iqtibos", {}),
        { target: { value: facts[i] } },
      );
    }
    const prompts = [
      "Water freezes at?",
      "Plants use what to make food?",
      "Earth travels around?",
    ];
    const options = [
      ["Zero degrees Celsius", "One hundred degrees Celsius"],
      ["Sunlight", "Moonlight"],
      ["The Sun", "Mars"],
    ];
    for (let i = 0; i < 3; i++) {
      const section = within(
        document.querySelectorAll(".editor-section")[i + 3] as HTMLElement,
      );
      for (const [label, value] of [
        [`Savol ${i + 1}`, prompts[i]],
        ["Variantlar — har qatorda bittadan", options[i].join("\n")],
        ["Javob tushuntirishi", facts[i]],
        ["Savol manba sahifasi", String(i + 1)],
        ["Savolning aniq manba iqtibosi", facts[i]],
      ])
        fireEvent.change(section.getByLabelText(label, { exact: true }), {
          target: { value },
        });
    }
    fireEvent.click(
      screen.getByRole("button", { name: "Dars qoralamasini saqlash" }),
    );
    await screen.findByRole("img", { name: "Kitobning tushunchalar xaritasi" });
    checks.push("Source-grounded editor and real SVG concept map");
    fireEvent.click(
      screen.getByLabelText(
        "Manbalar va barcha javob kalitlarini tekshirdim, tasdiqlayman.",
        { exact: true },
      ),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Darsni e’lon qilish" }),
    );
    await waitFor(() =>
      expect(
        screen.queryByRole("button", {
          name: "Darsni e’lon qilish",
        }),
      ).toBeNull(),
    );
    checks.push("Validated answer-key publication");
    fireEvent.change(screen.getByLabelText("O‘quvchi", { exact: true }), {
      target: { value: child.id },
    });
    fireEvent.click(
      screen.getByLabelText("Tasdiqlangan testdan keyin avtomatik mukofot", {}),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Sahifalarni biriktirish" }),
    );
    await screen.findByRole("heading", { name: "O‘qish va test natijalari" });
    checks.push("Guardian assigns reading with bounded automatic reward");
    await logout();
    await login("student.e2e@example.test");
    expect(screen.queryByRole("button", { name: "AI boshqaruv" })).toBeNull();
    fireEvent.click(
      screen.getByRole("button", { name: "Kitoblar va AI test" }),
    );
    expect(
      screen.queryByRole("button", { name: "Kitobni yuklash" }),
    ).toBeNull();
    await waitFor(() =>
      expect(document.querySelectorAll(".book-card").length).toBe(1),
    );
    fireEvent.click(document.querySelector(".book-card")!);
    await screen.findByRole("button", { name: "Sahifani belgilash" });
    checks.push("Student role and private reading assignment");
    fireEvent.click(screen.getByRole("button", { name: "Sahifani belgilash" }));
    await screen.findByText("33.33%", { exact: true });
    expect(screen.getByText("0%", { exact: true })).toBeDefined();
    checks.push("Self-reported reading separated from checked understanding");
    await waitFor(() =>
      expect(document.querySelector(".lesson-list button")).not.toBeNull(),
    );
    fireEvent.click(document.querySelector(".lesson-list button")!);
    fireEvent.click(
      await screen.findByRole("button", { name: "Tushunish testini boshlash" }),
    );
    for (const answer of ["Zero degrees Celsius", "Sunlight", "The Sun"])
      fireEvent.click(await screen.findByRole("radio", { name: answer }));
    await waitFor(() =>
      expect(
        screen
          .getByRole("button", { name: "Testni yakunlash" })
          .hasAttribute("disabled"),
      ).toBe(false),
    );
    fireEvent.click(screen.getByRole("button", { name: "Testni yakunlash" }));
    await screen.findByText("Mukofot berildi · 15 daqiqa", { exact: true });
    checks.push("Shuffled objective test graded and 15 minutes granted");
    const student = await account("student.e2e@example.test");
    const wallet = (await nativeFetch(api + "/rewards/wallet", {
      headers: { Authorization: `Bearer ${student.access_token}` },
    }).then((r) => r.json())) as any;
    expect(wallet.available).toBe(15);
    const plans = (await nativeFetch(api + "/reading/plans", {
      headers: { Authorization: `Bearer ${student.access_token}` },
    }).then((r) => r.json())) as any[];
    const detail = (await nativeFetch(api + `/reading/plans/${plans[0].id}`, {
      headers: { Authorization: `Bearer ${student.access_token}` },
    }).then((r) => r.json())) as any;
    expect(detail.progress.checked_percent).toBe(100);
    expect(detail.progress.self_reported_percent).toBe(33.33);
    checks.push("Server wallet and reading coverage verified");
    await logout();
    await login("parent.e2e@example.test");
    fireEvent.click(
      screen.getByRole("button", { name: "Kitoblar va AI test" }),
    );
    const assignedCard = () =>
      Array.from(document.querySelectorAll(".book-card")).find((card) =>
        card.textContent?.includes(child.name),
      );
    await waitFor(() => expect(assignedCard()).toBeDefined());
    fireEvent.click(assignedCard()!);
    await screen.findByText("Mukofot berildi · 15 daqiqa", { exact: true });
    checks.push("Guardian receives real test history");
    await logout();
    await login("teacher.e2e@example.test");
    expect(screen.queryByRole("button", { name: "Qurilmalar" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Sinflar" }));
    fireEvent.change(
      await screen.findByLabelText("Sinf nomi", { exact: true }),
      { target: { value: "DOM 8-A" } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Sinf yaratish" }));
    await screen.findByRole("button", { name: "DOM 8-A" });
    checks.push("Teacher classroom and household isolation");
    fs.writeFileSync(
      process.env.TEST_RESULTS_JSON!,
      JSON.stringify(
        {
          passed: checks.length,
          checks,
          transport:
            "jsdom rendered UI + actual HTTP to FastAPI/SQLite; no mocked responses",
          browser_execution: false,
          live_ai: "not configured; unavailable-state tested",
        },
        null,
        2,
      ),
    );
  }, 100000);
});

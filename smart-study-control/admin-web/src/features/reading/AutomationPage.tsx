import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { BrainCircuit, Shield, Clock } from "lucide-react";
import { api, type Row } from "../../services/api";
import { Button } from "../../components/ui/button";
export function AutomationPage({ children }: { children: Row[] }) {
  const client = useQueryClient();
  const [child, setChild] = useState("");
  const [enabled, setEnabled] = useState(false);
  const [practice, setPractice] = useState(false);
  const [limit, setLimit] = useState(60);
  const [maximum, setMaximum] = useState(2);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(
    "Bugungi o‘qish natijalariga mos qisqa takrorlash rejasini tuz. Tanaffuslarni ham hisobga ol.",
  );
  const config = useQuery({
    queryKey: ["automation", child],
    queryFn: () => api(`automation/children/${child}`),
    enabled: !!child,
  });
  const runs = useQuery({
    queryKey: ["automation-runs", child],
    queryFn: () => api<Row[]>(`automation/children/${child}/runs`),
    enabled: !!child,
  });
  useEffect(() => {
    if (config.data) {
      setEnabled(config.data.enabled);
      setPractice(config.data.auto_practice);
      setLimit(config.data.daily_reward_limit);
      setMaximum(config.data.max_tasks_per_day);
    }
  }, [config.data]);
  async function perform(fn: () => Promise<unknown>) {
    setError("");
    setBusy(true);
    try {
      await fn();
      await client.invalidateQueries();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="automation-page">
      <div className="page-title">
        <div>
          <span className="eyebrow">OTA-ONA VAKOLATI BILAN</span>
          <h1>
            AI boshqaruv markazi<span className="title-dot">.</span>
          </h1>
          <p>
            Kundalik ta’limni avtomatlashtiring, chegaralarni o‘zingiz
            belgilang.
          </p>
        </div>
        <BrainCircuit size={38} />
      </div>
      {error && (
        <div role="alert" className="error">
          {error}
        </div>
      )}
      <section className="card">
        <label className="field">
          <span>Farzand</span>
          <select value={child} onChange={(e) => setChild(e.target.value)}>
            <option value="">Tanlang</option>
            {children.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <p className="reading-note">
          <Shield size={16} /> AI ruxsat etilgan akademik vazifalarni tuzadi va
          tasdiqlangan kitob testlari uchun cheklangan mukofotni boshqaradi.
          Device Owner yoqish, himoyani o‘chirish va oilaviy siyosatni
          o‘zgartirish kattalar nazoratida qoladi.
        </p>
      </section>
      {child && config.data && (
        <>
          <section className="card">
            <h3>Avtopilot qoidalari</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                perform(() =>
                  api(`automation/children/${child}`, "PUT", {
                    enabled,
                    auto_practice: practice,
                    daily_reward_limit: limit,
                    max_tasks_per_day: maximum,
                  }),
                );
              }}
            >
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={enabled}
                  onChange={(e) => setEnabled(e.target.checked)}
                />
                Avtopilotga ruxsat berish
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={practice}
                  onChange={(e) => setPractice(e.target.checked)}
                />
                Kuniga qisqa mashq vazifalarini avtomatik tuzish
              </label>
              <div className="form-grid">
                <label className="field">
                  <span>Kunlik kitob mukofoti chegarasi (daqiqa)</span>
                  <input
                    type="number"
                    min="0"
                    max="120"
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                  />
                </label>
                <label className="field">
                  <span>Kunlik yangi mashq vazifalari (0–3)</span>
                  <input
                    type="number"
                    min="0"
                    max="3"
                    value={maximum}
                    onChange={(e) => setMaximum(Number(e.target.value))}
                  />
                </label>
              </div>
              <Button type="submit" disabled={busy}>
                Avtopilot sozlamalarini saqlash
              </Button>
            </form>
            <p className="reading-note">
              Mashq vazifalari avtomatik ekran vaqti bermaydi. O‘qish mukofoti
              faqat kattalar javob kalitini tasdiqlagan dars va tegishli rejada
              avtomatik mukofot yoqilganda beriladi.
            </p>
          </section>
          <section className="card">
            <h3>Bugungi rejani tuzish</h3>
            <label className="field">
              <span>AI uchun ta’lim maqsadi</span>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                maxLength={2000}
              />
            </label>
            <Button
              disabled={
                busy ||
                !config.data.enabled ||
                !config.data.auto_practice ||
                !message.trim()
              }
              onClick={() =>
                perform(() =>
                  api(`automation/children/${child}/run`, "POST", { message }),
                )
              }
            >
              <BrainCircuit size={17} />
              {busy ? "AI ishlamoqda…" : "Bugungi AI rejasini yaratish"}
            </Button>
            <p className="reading-note">
              Bir kunda bir marta reja yaratiladi. AI ulanmagan bo‘lsa vazifa
              yaratilmaydi va xato ochiq ko‘rsatiladi. Kundalik ish uchun
              serverdagi avtopilot worker yoqilgan bo‘lishi kerak.
            </p>
          </section>
          <section className="card">
            <h3>
              <Clock size={17} /> Avtopilot tarixi
            </h3>
            {runs.data?.length === 0 && <p>Hali reja yaratilmagan.</p>}
            {runs.data?.map((run) => (
              <article className="submission" key={run.id}>
                <strong>
                  {run.day} ·{" "}
                  {run.status === "COMPLETED"
                    ? "Yakunlangan"
                    : run.status === "FAILED"
                      ? "AI bajarilmadi"
                      : "Jarayonda"}
                </strong>
                {run.result.summary && <p>{run.result.summary}</p>}
                {run.result.assignment_ids && (
                  <p>
                    {run.result.assignment_ids.length} ta mashq vazifasi
                    yaratildi.
                  </p>
                )}
                {run.status === "FAILED" && (
                  <p>
                    AI xizmati tayyor emas yoki javob tekshiruvidan o‘tmadi.
                    Yangi vazifa yaratilmagan.
                  </p>
                )}
              </article>
            ))}
          </section>
        </>
      )}
      {config.error && <p role="alert">{config.error.message}</p>}
    </div>
  );
}

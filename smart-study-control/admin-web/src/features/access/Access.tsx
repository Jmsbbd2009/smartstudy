import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, setSession, type Row, type User } from "../../services/api";
import { Button } from "../../components/ui/button";
const decode = (value: string) =>
  Uint8Array.from(atob(value.replace(/-/g, "+").replace(/_/g, "/")), (c) =>
    c.charCodeAt(0),
  );
const encode = (value: ArrayBuffer) =>
  btoa(String.fromCharCode(...new Uint8Array(value)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
function serialize(credential: PublicKeyCredential) {
  const response = credential.response as AuthenticatorAttestationResponse &
    AuthenticatorAssertionResponse;
  return {
    id: credential.id,
    rawId: encode(credential.rawId),
    type: credential.type,
    clientExtensionResults: credential.getClientExtensionResults(),
    response: {
      clientDataJSON: encode(response.clientDataJSON),
      ...(response.attestationObject
        ? {
            attestationObject: encode(response.attestationObject),
            transports: response.getTransports?.() || [],
          }
        : {
            authenticatorData: encode(response.authenticatorData),
            signature: encode(response.signature),
            userHandle: response.userHandle
              ? encode(response.userHandle)
              : null,
          }),
    },
  };
}
export async function startTelegram(
  path: string,
  body: unknown,
  ready: (row: Row) => void,
) {
  const popup = window.open("about:blank", "_blank");
  if (popup) popup.opener = null;
  try {
    const row = await api(path, "POST", body);
    const target = new URL(row.deep_link);
    if (target.protocol !== "https:" || target.hostname !== "t.me")
      throw new Error("Telegram havolasi tasdiqlanmadi");
    ready(row);
    popup?.location.replace(target.href);
  } catch (error) {
    popup?.close();
    throw error;
  }
}

export async function passkeyLogin(login: string) {
  if (!window.isSecureContext || !window.PublicKeyCredential)
    throw new Error("Passkey uchun HTTPS yoki localhost va mos qurilma kerak.");
  const challenge = await api("auth/passkeys/login/options", "POST", { login });
  const options = {
    ...challenge.options,
    challenge: decode(challenge.options.challenge),
    allowCredentials: challenge.options.allowCredentials?.map((c: Row) => ({
      ...c,
      id: decode(c.id),
    })),
  };
  const credential = (await navigator.credentials.get({
    publicKey: options,
  })) as PublicKeyCredential | null;
  if (!credential) throw new Error("Qurilma tasdig‘i bekor qilindi");
  setSession(
    await api("auth/passkeys/login/verify", "POST", {
      challenge_id: challenge.challenge_id,
      verifier: challenge.verifier,
      credential: serialize(credential),
    }),
  );
}
async function registerPasskey(password: string) {
  if (!window.isSecureContext || !window.PublicKeyCredential)
    throw new Error("Passkey uchun HTTPS yoki localhost va mos qurilma kerak.");
  const challenge = await api("auth/passkeys/register/options", "POST", {
    password,
  });
  const options = {
    ...challenge.options,
    challenge: decode(challenge.options.challenge),
    user: { ...challenge.options.user, id: decode(challenge.options.user.id) },
    excludeCredentials: challenge.options.excludeCredentials?.map((c: Row) => ({
      ...c,
      id: decode(c.id),
    })),
  };
  const credential = (await navigator.credentials.create({
    publicKey: options,
  })) as PublicKeyCredential | null;
  if (!credential) throw new Error("Qurilma tasdig‘i bekor qilindi");
  await api("auth/passkeys/register/verify", "POST", {
    challenge_id: challenge.challenge_id,
    verifier: challenge.verifier,
    credential: serialize(credential),
    label: navigator.platform || "Qurilma",
  });
}
export function TelegramLogin({
  login,
  onError,
}: {
  login: string;
  onError: (s: string) => void;
}) {
  const [challenge, setChallenge] = useState<Row | null>(null),
    [code, setCode] = useState(""),
    [busy, setBusy] = useState(false);
  async function run(fn: () => Promise<void>) {
    setBusy(true);
    onError("");
    try {
      await fn();
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="access-options">
      <p>Telefon yoki loginni kiriting, Telegram botidan bir martalik kod oling.</p>
      <div className="action-row">
        <Button
          type="button"
          variant="outline"
          disabled={busy || !login}
          onClick={() =>
            run(() =>
              startTelegram(
                "auth/telegram/login/start",
                { login },
                setChallenge,
              ),
            )
          }
        >
          Telegram orqali kirish
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={busy || !login}
          onClick={() => run(() => passkeyLogin(login))}
        >
          Yuz / qurilma kaliti bilan kirish
        </Button>
      </div>
      {challenge && (
        <div className="access-step">
          <a
            href={challenge.deep_link}
            target="_blank"
            rel="noopener noreferrer"
            className="access-link"
          >
            Telegram botiga o‘tish →
          </a>
          <p>
            Botda Start bosing. Kod faqat shu hisobga bog‘langan Telegramga
            yuboriladi. 5 daqiqa amal qiladi.
          </p>
          <label className="field">
            Telegram kodi
            <input
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
          </label>
          <Button
            type="button"
            disabled={busy || !/^\d{6}$/.test(code)}
            onClick={() =>
              run(async () =>
                setSession(
                  await api("auth/telegram/login/finish", "POST", {
                    challenge_id: challenge.challenge_id,
                    verifier: challenge.verifier,
                    code,
                  }),
                ),
              )
            }
          >
            Kodni tasdiqlash
          </Button>
        </div>
      )}
    </section>
  );
}
export function PasswordRenewal() {
  const [old, setOld] = useState(""),
    [fresh, setFresh] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  return (
    <main className="login-page">
      <section className="login-card">
        <h1>Parolni yangilang</h1>
        <p>
          Vaqtinchalik parol bilan boshqaruv ochilmaydi. Kamida 12 belgili yangi
          parol tanlang.
        </p>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            try {
              setSession(
                await api("auth/password", "POST", {
                  current_password: old,
                  new_password: fresh,
                }),
              );
            } catch (err) {
              setError((err as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <label className="field">
            Hozirgi parol
            <input
              type="password"
              autoComplete="current-password"
              value={old}
              onChange={(e) => setOld(e.target.value)}
              required
            />
          </label>
          <label className="field">
            Yangi parol
            <input
              type="password"
              autoComplete="new-password"
              minLength={12}
              value={fresh}
              onChange={(e) => setFresh(e.target.value)}
              required
            />
          </label>
          <Button disabled={busy} type="submit">
            Yangi parolni saqlash
          </Button>
        </form>
      </section>
    </main>
  );
}
export function SecurityAccess({ user }: { user: User }) {
  const [password, setPassword] = useState(""),
    [challenge, setChallenge] = useState<Row | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const client = useQueryClient();
  const tg = useQuery({
    queryKey: ["tg-me"],
    queryFn: () => api("auth/telegram/me"),
  });
  const keys = useQuery({
    queryKey: ["passkeys"],
    queryFn: () => api<Row[]>("auth/passkeys"),
  });
  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
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
    <section className="card access-settings">
      <h2>Telegram va qurilma kaliti</h2>
      <p>
        Bu serverdagi yuzni tanish emas. Passkey tasdig‘ini qurilmaning o‘zi
        bajaradi; u biometrika yoki qurilma PIN-kodini so‘rashi mumkin. Yuz
        rasmi serverga yuborilmaydi.
      </p>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <label className="field">
        Hisob paroli
        <input
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>
      <div className="action-row">
        <Button
          disabled={busy || !password}
          onClick={() =>
            run(() =>
              startTelegram(
                "auth/telegram/link/start",
                { password },
                setChallenge,
              ),
            )
          }
        >
          Telegramni bog‘lash
        </Button>
        <Button
          variant="outline"
          disabled={busy || !password}
          onClick={() => run(() => registerPasskey(password))}
        >
          Qurilma kalitini qo‘shish
        </Button>
      </div>
      {challenge && (
        <div className="access-step">
          <a
            href={challenge.deep_link}
            target="_blank"
            rel="noopener noreferrer"
            className="access-link"
          >
            Botga o‘tish →
          </a>
          <p>Start bosgach shu oynaga qaytib tasdiqlang.</p>
          <Button
            disabled={busy}
            onClick={() =>
              run(async () => {
                await api("auth/telegram/link/finish", "POST", {
                  challenge_id: challenge.challenge_id,
                  verifier: challenge.verifier,
                  password,
                });
                setChallenge(null);
              })
            }
          >
            Telegram bog‘lanishini tasdiqlash
          </Button>
        </div>
      )}
      <p>
        {tg.data?.linked ? "Telegram bog‘langan" : "Telegram hali bog‘lanmagan"}
      </p>
      {tg.data?.linked && (
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={!!tg.data.notifications_enabled}
            onChange={(e) =>
              run(async () => {
                await api("auth/telegram/notifications", "PUT", {
                  enabled: e.target.checked,
                });
              })
            }
          />
          Bildirishnomalarni Telegramga ham yuborish
        </label>
      )}
      <ul>
        {keys.data?.map((k) => (
          <li key={k.id}>
            {k.label}{" "}
            <button
              disabled={busy || !password}
              onClick={() =>
                run(async () => {
                  await api(`auth/passkeys/${k.id}`, "DELETE", { password });
                })
              }
            >
              Kalitni olib tashlash
            </button>
          </li>
        ))}
      </ul>
      <small>Hisob: {user.login || user.email}</small>
    </section>
  );
}
export function StaffPage({ user }: { user: User }) {
  const client = useQueryClient();
  const rows = useQuery({
    queryKey: ["staff"],
    queryFn: () => api<Row[]>("staff"),
  });
  const schools = useQuery({
    queryKey: ["staff-schools"],
    queryFn: () => api<Row[]>("staff/schools"),
  });
  const [form, setForm] = useState({
      name: "",
      email: "",
      login: "",
      password: "",
      role: "TEACHER",
      school_name: "",
      school_id: "",
    }),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [recipients, setRecipients] = useState<string[]>([]),
    [title, setTitle] = useState(""),
    [message, setMessage] = useState("");
  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await fn();
      await client.invalidateQueries();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const change = (key: keyof typeof form, value: string) =>
    setForm((v) => ({ ...v, [key]: value }));
  return (
    <div className="access-settings">
      <h1>Xodimlar boshqaruvi</h1>
      <p>
        Admin va o‘qituvchi hisoblarini faqat super admin yaratadi. Maktab
        admini o‘z maktabidagi xodimlarni ko‘radi.
      </p>
      {(error || rows.error) && (
        <p role="alert" className="error">
          {error || rows.error?.message}
        </p>
      )}
      {user.role === "SUPER_ADMIN" && (
        <section className="card">
          <h2>Yangi xodim</h2>
          <form
            className="form-grid"
            onSubmit={(e) => {
              e.preventDefault();
              run(async () => {
                await api("staff", "POST", {
                  ...form,
                  email: form.email || null,
                  school_id: form.role === "TEACHER" ? form.school_id : null,
                  school_name:
                    form.role === "SCHOOL_ADMIN" ? form.school_name : null,
                });
                setForm((v) => ({
                  ...v,
                  name: "",
                  email: "",
                  login: "",
                  password: "",
                }));
              });
            }}
          >
            {(["name", "login", "password"] as const).map((key, i) => (
              <label className="field" key={key}>
                {["Ism", "Telefon yoki login", "Vaqtinchalik parol"][i]}
                <input
                  type={
                    key === "password"
                      ? "password"
                      : "text"
                  }
                  minLength={key === "password" ? 12 : 1}
                  autoComplete={key === "password" ? "new-password" : "off"}
                  value={form[key]}
                  required
                  onChange={(e) => change(key, e.target.value)}
                />
              </label>
            ))}
            <label className="field">
              Rol
              <select
                value={form.role}
                onChange={(e) => change("role", e.target.value)}
              >
                <option value="TEACHER">O‘qituvchi</option>
              </select>
            </label>
            {form.role === "SCHOOL_ADMIN" ? (
              <label className="field">
                Yangi maktab nomi
                <input
                  value={form.school_name}
                  onChange={(e) => change("school_name", e.target.value)}
                  required
                />
              </label>
            ) : (
              <label className="field">
                Maktab
                <select
                  value={form.school_id}
                  onChange={(e) => change("school_id", e.target.value)}
                  required
                >
                  <option value="">Tanlang</option>
                  {schools.data?.map((s) => (
                    <option value={s.id} key={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <Button disabled={busy} type="submit">
              Xodim yaratish
            </Button>
          </form>
        </section>
      )}
      <section className="card">
        <h2>Xodimlar ro‘yxati</h2>
        {rows.isLoading && <p>Yuklanmoqda…</p>}
        {rows.data?.length === 0 && <p>Hali xodim yo‘q.</p>}
        {rows.data?.map((row) => (
          <article className="submission" key={row.id}>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={recipients.includes(row.id)}
                onChange={(e) =>
                  setRecipients((v) =>
                    e.target.checked
                      ? [...v, row.id]
                      : v.filter((x) => x !== row.id),
                  )
                }
              />
              <strong>{row.name}</strong> · {row.login} · {row.role}
            </label>
            <p>
              {row.active ? "Faol" : "O‘chirilgan"}
              {row.must_change_password ? " · yangi parol kerak" : ""}
            </p>
            {user.role === "SUPER_ADMIN" && (
              <Button
                variant="outline"
                disabled={busy}
                onClick={() =>
                  run(async () => {
                    await api(`staff/${row.id}/state`, "PUT", {
                      active: !row.active,
                    });
                  })
                }
              >
                {row.active ? "Hisobni to‘xtatish" : "Hisobni yoqish"}
              </Button>
            )}
          </article>
        ))}
      </section>
      <section className="card">
        <h2>Xodimlarga bildirishnoma</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            run(async () => {
              await api("staff/announcements", "POST", {
                title,
                body: message,
                recipient_ids: recipients,
              });
              setTitle("");
              setMessage("");
            });
          }}
        >
          <label className="field">
            Sarlavha
            <input
              value={title}
              required
              onChange={(e) => setTitle(e.target.value)}
            />
          </label>
          <label className="field">
            Xabar
            <textarea
              value={message}
              required
              onChange={(e) => setMessage(e.target.value)}
            />
          </label>
          <Button disabled={busy || recipients.length === 0} type="submit">
            Tanlangan xodimlarga yuborish
          </Button>
        </form>
      </section>
    </div>
  );
}
export function NotificationCenter() {
  const client = useQueryClient();
  const rows = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api<Row[]>("notifications"),
    refetchInterval: 15000,
  });
  return (
    <section className="card">
      <h1>Bildirishnomalar</h1>
      {rows.error && <p role="alert">{rows.error.message}</p>}
      {rows.isLoading && <p>Yuklanmoqda…</p>}
      {rows.data?.length === 0 && <p>Hozircha bildirishnoma yo‘q.</p>}
      {rows.data?.map((n) => (
        <article className="submission" key={n.id}>
          <strong>{n.title}</strong>
          <p>{n.body}</p>
          <small>{new Date(n.created_at).toLocaleString()}</small>
          {!n.read && (
            <Button
              variant="outline"
              onClick={async () => {
                await api(`notifications/${n.id}/read`, "POST");
                client.invalidateQueries({ queryKey: ["notifications"] });
              }}
            >
              O‘qildi
            </Button>
          )}
        </article>
      ))}
    </section>
  );
}
export function TeacherLocation() {
  const [classId, setClassId] = useState(""),
    [child, setChild] = useState(""),
    [error, setError] = useState("");
  const client = useQueryClient();
  const classes = useQuery({
    queryKey: ["classrooms"],
    queryFn: () => api<Row[]>("classrooms"),
  });
  const roster = useQuery({
    queryKey: ["location-roster", classId],
    queryFn: () => api<Row[]>(`classrooms/${classId}/students`),
    enabled: !!classId,
  });
  const policy = useQuery({
    queryKey: ["location-policy", child],
    queryFn: () => api(`location/children/${child}/consent`),
    enabled: !!child,
  });
  const location = useQuery({
    queryKey: ["teacher-location", child],
    queryFn: () => api(`location/children/${child}/latest`),
    enabled: !!child,
    refetchInterval: 5000,
  });
  return (
    <section className="card">
      <h1>O‘quvchi joylashuvi</h1>
      <p>Faqat o‘zingizning sinfingizdagi o‘quvchilar. O‘quvchi ulashishni ilovada o‘zi boshlaydi va istalgan payt to‘xtatadi. Ulanish vaqt bilan cheklangan; kuzatuv fonda yashirin ishlamaydi.</p>
      <label className="field">
        Sinf
        <select value={classId} onChange={e => { setClassId(e.target.value); setChild(""); }}>
          <option value="">Sinfni tanlang</option>
          {classes.data?.map(c => <option value={c.id} key={c.id}>{c.name}</option>)}
        </select>
      </label>
      <label className="field">
        O‘quvchi
        <select value={child} onChange={e => setChild(e.target.value)} disabled={!classId}>
          <option value="">O‘quvchini tanlang</option>
          {roster.data?.map(s => <option value={s.id} key={s.id}>{s.name}</option>)}
        </select>
      </label>
      {error && <p role="alert" className="error">{error}</p>}
      {child && <>
        <p>{policy.data?.enabled ? "Sinf doirasidagi ruxsat yoqilgan" : "Sinf doirasidagi ruxsat o‘chiq"}</p>
        <Button onClick={async () => { setError(""); try { await api(`location/children/${child}/consent`, "PUT", { enabled: !policy.data?.enabled, max_minutes: 60 }); await client.invalidateQueries(); } catch (e) { setError((e as Error).message); } }}>
          {policy.data?.enabled ? "Ulashish ruxsatini o‘chirish" : "Sessiya uchun ruxsat berish"}
        </Button>
        <p>{location.data?.active ? (location.data.stale ? "O‘quvchi ulashishni yoqqan, signal eskirgan" : "O‘quvchi ulashishni yoqqan") : "Faol ulashish yo‘q"}</p>
        {location.data?.active && location.data.latitude != null && !location.data.stale && <><p>{location.data.latitude}, {location.data.longitude} · ±{Math.round(location.data.accuracy_m)} m</p><p>Yangilandi: {new Date(location.data.received_at).toLocaleTimeString()}</p><a target="_blank" rel="noopener noreferrer" href={`https://www.openstreetmap.org/?mlat=${location.data.latitude}&mlon=${location.data.longitude}#map=16/${location.data.latitude}/${location.data.longitude}`}>Xaritada ochish →</a></>}
      </>}
    </section>
  );
}

export function FamilyLocation({ children }: { children: Row[] }) {
  const [child, setChild] = useState(""),
    [error, setError] = useState(""),
    [minutes, setMinutes] = useState(60);
  const client = useQueryClient();
  const policy = useQuery({
    queryKey: ["location-policy", child],
    queryFn: () => api(`location/children/${child}/consent`),
    enabled: !!child,
  });
  const location = useQuery({
    queryKey: ["family-location", child],
    queryFn: () => api(`location/children/${child}/latest`),
    enabled: !!child,
    refetchInterval: 5000,
  });
  return (
    <section className="card">
      <h1>Oilaviy joylashuv</h1>
      <p>
        Farzand ilovada ulashishni o‘zi boshlaydi. Doimiy ko‘rinadigan
        bildirishnoma va to‘xtatish tugmasi bor. Koordinatalarni faqat bog‘langan
        vasiy va o‘quvchining amaldagi sinf o‘qituvchisi ko‘ra oladi.
      </p>
      <label className="field">
        Farzand
        <select value={child} onChange={(e) => setChild(e.target.value)}>
          <option value="">Tanlang</option>
          {children.map((c) => (
            <option value={c.id} key={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </label>
      {error && <p role="alert">{error}</p>}
      {child && (
        <>
          <label className="field">
            Maksimal muddat (daqiqa)
            <input
              type="number"
              min={1}
              max={240}
              value={minutes}
              onChange={(e) => setMinutes(Number(e.target.value))}
            />
          </label>
          <Button
            onClick={async () => {
              setError("");
              try {
                await api(`location/children/${child}/consent`, "PUT", {
                  enabled: !policy.data?.enabled,
                  guardian_consent: true,
                  max_minutes: minutes,
                });
                await client.invalidateQueries();
              } catch (e) {
                setError((e as Error).message);
              }
            }}
          >
            {policy.data?.enabled
              ? "Rozilikni bekor qilish"
              : "Joylashuv ulashishga rozilik berish"}
          </Button>
          <p>
            {location.data?.active
              ? "Farzand ulashishni yoqqan"
              : "Hozir ulashish yo‘q"}
          </p>
          {location.data?.active && (
            <>
              <p>
                {location.data.stale
                  ? "Signal eskirgan yoki uzilgan"
                  : "Yaqinda yangilangan"}
              </p>
              {location.data.received_at && (
                <p>
                  Oxirgi yangilanish:{" "}
                  {new Date(location.data.received_at).toLocaleTimeString()}
                </p>
              )}
              {location.data.latitude != null && !location.data.stale && (
                <>
                  <p>
                    {location.data.latitude}, {location.data.longitude} · ±
                    {Math.round(location.data.accuracy_m)} m
                  </p>
                  <a
                    target="_blank"
                    rel="noopener noreferrer"
                    href={`https://www.openstreetmap.org/?mlat=${location.data.latitude}&mlon=${location.data.longitude}#map=16/${location.data.latitude}/${location.data.longitude}`}
                  >
                    Tashqi xaritada ochish →
                  </a>
                </>
              )}
              <p>GPS va tarmoq holatiga bog‘liq. Telefonning o‘z hisoboti.</p>
            </>
          )}
        </>
      )}
    </section>
  );
}

export function Integrations() {
  const config = useQuery({
    queryKey: ["integrations"],
    queryFn: () => api("operations/integrations"),
  });
  const [checks, setChecks] = useState<Row | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  return (
    <section className="card">
      <h2>AI va Telegram ulanishlari</h2>
      <p>Faol provayder: {config.data?.ai_provider || "Yuklanmoqda…"}</p>
      <p>
        Groq: {config.data?.groq_configured ? "Kalit sozlangan" : "Sozlanmagan"}{" "}
        · {config.data?.groq_model}
      </p>
      <p>
        DeepSeek:{" "}
        {config.data?.deepseek_configured ? "Kalit sozlangan" : "Sozlanmagan"} ·{" "}
        {config.data?.deepseek_model}
      </p>
      <p>
        Hugging Face:{" "}
        {config.data?.huggingface_configured
          ? "Kalit sozlangan"
          : "Sozlanmagan"}{" "}
        · {config.data?.hf_model}
      </p>
      <p>
        Telegram:{" "}
        {config.data?.telegram_configured ? "Sozlangan" : "Sozlanmagan"} · @
        {config.data?.telegram_username}
      </p>
      <p>
        Tekshiruv kalit qabul qilinishini ko‘rsatadi; model krediti va javob
        sifati alohida tekshiriladi.
      </p>
      {error && <p role="alert">{error}</p>}
      <Button
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          setError("");
          try {
            setChecks(await api("operations/integrations/check", "POST", {}));
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        Ulanishlarni tekshirish
      </Button>
      {checks &&
        Object.entries(checks).map(([name, result]) => (
          <p key={name}>
            {name}:{" "}
            {!result.configured
              ? "sozlanmagan"
              : result.accepted
                ? "kalit qabul qilindi"
                : `ishlamadi · ${result.http_status || result.error}`}
          </p>
        ))}
    </section>
  );
}

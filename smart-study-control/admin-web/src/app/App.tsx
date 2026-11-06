import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  AreaChart,
  Area,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  CartesianGrid,
} from "recharts";
import {
  BookOpen,
  LayoutDashboard,
  Users,
  Monitor,
  ChartNoAxesCombined,
  Shield,
  Settings,
  LogOut,
  ArrowUpRight,
  Check,
  Plus,
  Sun,
  GraduationCap,
  Clock,
  ArrowLeft,
} from "lucide-react";
import { Button } from "../components/ui/button";
import {
  api,
  getSession,
  setSession,
  subscribe,
  logout,
  downloadAttachment,
  type Row,
  type Session,
} from "../services/api";
import { translations, type Lang } from "../i18n";
import { BooksPage } from "../features/reading/BooksPage";
import { AutomationPage } from "../features/reading/AutomationPage";
import {
  TelegramLogin,
  PasswordRenewal,
  SecurityAccess,
  StaffPage,
  NotificationCenter,
  FamilyLocation,
  Integrations,
} from "../features/access/Access";

const schema = z.object({
  email: z.string().min(1).max(254),
  password: z.string().min(1).max(128),
});
function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}
function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={`card ${className}`}>{children}</section>;
}
function Empty() {
  return (
    <p className="empty">
      Hozircha ma’lumot yo‘q. Yangi ma’lumot qo‘shilganda shu yerda ko‘rinadi.
    </p>
  );
}
const statusNames: Record<string, string> = {
  ASSIGNED: "Berilgan",
  SUBMITTED: "Topshirilgan",
  APPROVED: "Tasdiqlangan",
  REVISION_REQUESTED: "Qayta ishlash",
  NEEDS_HUMAN_REVIEW: "Tekshiruv kerak",
  REJECTED: "Rad etilgan",
};
function Badge({ value }: { value: string }) {
  return (
    <span className={`badge ${value === "APPROVED" ? "positive" : ""}`}>
      {statusNames[value] || value}
    </span>
  );
}
export function App() {
  const [session, update] = useState<Session | null>(getSession);
  const [page, setPage] = useState("overview");
  const [lang, setLang] = useState<Lang>("uz");
  const [error, setError] = useState("");
  const queryClient = useQueryClient();
  const t = translations[lang];
  useEffect(
    () =>
      subscribe((s) => {
        update(s);
        queryClient.clear();
      }),
    [queryClient],
  );
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  const tasks = useQuery({
    queryKey: ["assignments"],
    queryFn: () => api<Row[]>("assignments"),
    enabled: !!session && !session.user.must_change_password,
  });
  const children = useQuery({
    queryKey: ["children"],
    queryFn: () => api<Row[]>("families/children"),
    enabled: session?.user.role === "PARENT",
  });
  async function act(fn: () => Promise<unknown>) {
    setError("");
    try {
      await fn();
      await queryClient.invalidateQueries();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => setPage("overview"), [session?.user.id]);
  if (!session) return <Login onError={setError} error={error} />;
  if (session.user.must_change_password) return <PasswordRenewal />;
  const parent = session.user.role === "PARENT",
    teacher = session.user.role === "TEACHER",
    student = session.user.role === "STUDENT",
    operator = !parent && !teacher && !student;
  const nav = [
    ["overview", t.overview, LayoutDashboard],
    ...(!operator
      ? [
          ["assignments", t.assignments, BookOpen],
          ["books", "Kitoblar va AI test", BookOpen],
        ]
      : []),
    ...(parent ? [["automation", "AI boshqaruv", Shield]] : []),
    ...(parent
      ? [
          ["family", t.family, Users],
          ["devices", t.devices, Monitor],
        ]
      : []),
    ...(teacher ? [["classes", t.classes, GraduationCap]] : []),
    ...(!operator ? [["reports", t.reports, ChartNoAxesCombined]] : []),
    ...(operator ? [["staff", "Xodimlar", Users]] : []),
    ...(parent ? [["location", "Oilaviy joylashuv", Monitor]] : []),
    ["notifications", "Bildirishnomalar", Clock],
    ["audit", t.audit, Shield],
    ["settings", t.settings, Settings],
  ] as const;
  return (
    <div className="shell">
      <aside>
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setPage("overview");
          }}
        >
          <span className="brand-icon">
            <BookOpen size={24} />
          </span>
          <span>
            smart study<small>CONTROL CENTER</small>
          </span>
        </a>
        <div className="workspace">
          O‘QUV MUHITI <span>01</span>
        </div>
        <nav aria-label="Asosiy navigatsiya">
          {nav.map(([key, label, Icon]) => (
            <button
              key={key as string}
              className={page === key ? "active" : ""}
              onClick={() => {
                setPage(key as string);
                setError("");
              }}
            >
              <Icon size={19} />
              {label as string}
              {page === key && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="privacy-note">
            <Shield size={20} />
            <p>
              Xavfsiz o‘quv muhiti
              <small>Vakolatlar va maxfiylik nazorat ostida.</small>
            </p>
          </div>
          <button onClick={() => act(() => logout())}>
            <LogOut size={18} />
            {t.signOut}
          </button>
        </div>
      </aside>
      <main>
        <header>
          <div>
            <span className="eyebrow">SMART STUDY CONTROL</span>
            <p>{t.today}</p>
          </div>
          <div className="account">
            <select
              aria-label="Til"
              value={lang}
              onChange={(e) => setLang(e.target.value as Lang)}
            >
              <option value="uz">UZ</option>
              <option value="en">EN</option>
              <option value="ru">RU</option>
            </select>
            <div className="avatar">{session.user.name[0]?.toUpperCase()}</div>
            <div>
              <strong>{session.user.name}</strong>
              <small>{session.user.role}</small>
            </div>
          </div>
        </header>
        <div className="content">
          {error && (
            <div role="alert" className="error">
              {error}
              <button aria-label="Yopish" onClick={() => setError("")}>
                ×
              </button>
            </div>
          )}
          {tasks.error && (
            <div role="alert" className="error">
              {tasks.error.message}
            </div>
          )}
          {page === "overview" && (
            <>
              <div className="page-title">
                <div>
                  <p className="eyebrow">KUNLIK NAZORAT</p>
                  <h1>
                    {t.overview}
                    <span className="title-dot">.</span>
                  </h1>
                  <p>{t.welcome}</p>
                </div>
                <Button
                  variant="outline"
                  onClick={() => queryClient.invalidateQueries()}
                >
                  <Clock size={16} />
                  {t.refresh}
                </Button>
              </div>
              <section className="hero">
                <div>
                  <span className="hero-label">
                    <span /> BIRGALIKDA O‘SAMIZ
                  </span>
                  <h2>
                    Bilimga vaqt ajrating.
                    <br />
                    Natijalar ortidan keladi.
                  </h2>
                  <p>
                    {parent
                      ? "Farzandingizning o‘qish odatlari va kichik yutuqlarini bir joyda kuzating."
                      : teacher
                        ? "Vazifalar, o‘quvchilar va foydali fikr-mulohazalar — bir joyda."
                        : "O‘quv muhitingizning holatini shu yerdan kuzating."}
                  </p>
                  {!operator && (
                    <Button onClick={() => setPage("assignments")}>
                      {t.assignments}
                      <ArrowUpRight size={17} />
                    </Button>
                  )}
                </div>
                <div className="learning-art" aria-hidden="true">
                  <div className="orbit orbit-one" />
                  <div className="orbit orbit-two" />
                  <div className="art-book">
                    <BookOpen size={90} strokeWidth={1.2} />
                  </div>
                  <div className="floating-check">
                    <Check size={28} />
                  </div>
                  <span className="floating-star">✦</span>
                </div>
              </section>
              <div className="stats-grid">
                <Stat
                  label="Jami vazifalar"
                  value={tasks.data?.length || 0}
                  icon={<BookOpen size={20} />}
                />
                <Stat
                  label={t.approved}
                  value={
                    tasks.data?.filter((a) => a.status === "APPROVED").length ||
                    0
                  }
                  icon={<Check size={20} />}
                />
                <Stat
                  label={t.pending}
                  value={
                    tasks.data?.filter((a) => a.status !== "APPROVED").length ||
                    0
                  }
                  icon={<Clock size={20} />}
                />
                <Stat
                  label={parent ? "Bog‘langan farzandlar" : "Sizning rolingiz"}
                  value={
                    parent ? children.data?.length || 0 : session.user.role
                  }
                  icon={<Users size={20} />}
                />
              </div>
              {!operator && (
                <div className="overview-grid">
                  <Card>
                    <div className="section-heading">
                      <h3>So‘nggi vazifalar</h3>
                      <button onClick={() => setPage("assignments")}>
                        Barchasi <ArrowUpRight size={15} />
                      </button>
                    </div>
                    <TaskTable
                      tasks={tasks.data?.slice(0, 5) || []}
                      onOpen={(id) => {
                        setPage("assignments");
                        sessionStorage.setItem("selectedAssignment", id);
                      }}
                    />
                  </Card>
                  <Card>
                    <span className="eyebrow">MUVOZANAT MUHIM</span>
                    <h3>
                      Bilim. Dam olish.
                      <br />
                      Sog‘lom odatlar.
                    </h3>
                    <div className="wellbeing-icon">
                      <Sun size={48} />
                    </div>
                    <p>
                      O‘qishdagi qiyinchilik dam olishni butunlay bekor
                      qilmasligi kerak. Tanaffus va zarur aloqa doim muhim.
                    </p>
                  </Card>
                </div>
              )}
              {operator && <Operational />}
            </>
          )}
          {page === "staff" && operator && <StaffPage user={session.user} />}
          {page === "notifications" && <NotificationCenter />}
          {page === "location" && parent && (
            <FamilyLocation children={children.data || []} />
          )}
          {page === "books" && (
            <BooksPage user={session.user} children={children.data || []} />
          )}
          {page === "automation" && parent && (
            <AutomationPage children={children.data || []} />
          )}
          {page === "assignments" && (
            <Assignments
              tasks={tasks.data || []}
              parent={parent}
              teacher={teacher}
              children={children.data || []}
              act={act}
            />
          )}
          {page === "family" && (
            <Family children={children.data || []} act={act} />
          )}
          {page === "classes" && <Classes act={act} />}
          {page === "devices" && (
            <Devices children={children.data || []} act={act} />
          )}
          {page === "reports" && (
            <Reports children={children.data || []} teacher={teacher} />
          )}
          {page === "audit" && <Audit />}
          {page === "settings" && session.user.role === "SUPER_ADMIN" && (
            <Integrations />
          )}
          {page === "settings" &&
            ["TEACHER", "SCHOOL_ADMIN", "SUPER_ADMIN"].includes(
              session.user.role,
            ) && <SecurityAccess user={session.user} />}
          {page === "settings" && (
            <Card>
              <h2>Maxfiylik va hisob</h2>
              <p>
                O‘qituvchilar faqat o‘z sinfidagi akademik ma’lumotlarni
                ko‘radi. Qurilma siyosatini faqat bog‘langan vakolatli ota-ona
                boshqaradi. Yashirin kuzatuv yo‘q.
              </p>
              <p>
                Kirish ma’lumotlari faqat joriy oynaning xotirasida turadi. Oyna
                yangilanganda qayta kirish kerak.
              </p>
              <Button
                variant="danger"
                onClick={() =>
                  act(() => api("privacy/deletion-request", "POST", {}))
                }
              >
                Ma’lumotlarni o‘chirishni so‘rash
              </Button>
              <p>
                So‘rov vakolatli administrator tomonidan tekshirib bajariladi.
              </p>
            </Card>
          )}
          <footer>
            SMART STUDY CONTROL <span>{t.subtitle}</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
function Login({
  error,
  onError,
}: {
  error: string;
  onError: (s: string) => void;
}) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) });
  return (
    <div className="login-shell">
      <div className="login-story">
        <span className="hero-label">SMART STUDY CONTROL</span>
        <h1>
          Yaxshi odatlar.
          <br />
          Katta imkoniyatlar.
        </h1>
        <p>Ta’lim, sog‘lom ekran vaqti va hamkorlik.</p>
        <BookOpen size={180} strokeWidth={0.7} />
        <small>Learn. Achieve. Unlock.</small>
      </div>
      <form
        className="login-form"
        onSubmit={handleSubmit(async (values) => {
          onError("");
          try {
            setSession(await api("auth/login", "POST", values));
          } catch (e) {
            onError((e as Error).message);
          }
        })}
      >
        <span className="eyebrow">BOSHQARUV MARKAZI</span>
        <h2>Xush kelibsiz</h2>
        <p>Ota-ona yoki o‘qituvchi hisobingiz bilan kiring.</p>
        <Field label="Email">
          <input
            autoComplete="username"
            type="text"
            placeholder="Email yoki login"
            {...register("email")}
          />
          {errors.email && <small>Email yoki login kiriting</small>}
        </Field>
        <Field label="Parol">
          <input
            autoComplete="current-password"
            type="password"
            {...register("password")}
          />
          {errors.password && <small>Parolni kiriting</small>}
        </Field>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <Button disabled={isSubmitting} type="submit">
          {isSubmitting ? "Kutilmoqda…" : "Kirish"}
          <ArrowUpRight size={18} />
        </Button>
        <TelegramLogin login={watch("email") || ""} onError={onError} />
        <p className="muted">
          Ota-ona va o‘quvchi hisobini Android ilovasida yarating. O‘qituvchi
          hisobini administrator beradi.
        </p>
      </form>
    </div>
  );
}
function Stat({
  label,
  value,
  icon,
}: {
  label: string;
  value: string | number;
  icon: ReactNode;
}) {
  return (
    <Card>
      <div className="stat-icon">{icon}</div>
      <p className="stat-label">{label}</p>
      <strong className="stat-value">{value}</strong>
    </Card>
  );
}
function TaskTable({
  tasks,
  onOpen,
}: {
  tasks: Row[];
  onOpen: (id: string) => void;
}) {
  if (!tasks.length) return <Empty />;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Vazifa</th>
            <th>Fan</th>
            <th>Holat</th>
            <th>
              <span className="sr-only">Ochish</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((a) => (
            <tr key={a.id}>
              <td>
                <strong>{a.title}</strong>
                <small>
                  {a.due_at
                    ? new Date(a.due_at).toLocaleDateString("uz-UZ")
                    : "Muddat belgilanmagan"}
                </small>
              </td>
              <td>{a.subject}</td>
              <td>
                <Badge value={a.status} />
              </td>
              <td>
                <button
                  className="icon-button"
                  aria-label={`${a.title} ni ochish`}
                  onClick={() => onOpen(a.id)}
                >
                  <ArrowUpRight size={19} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
type Act = (fn: () => Promise<unknown>) => Promise<void>;
function Assignments({
  tasks,
  parent,
  teacher,
  children,
  act,
}: {
  tasks: Row[];
  parent: boolean;
  teacher: boolean;
  children: Row[];
  act: Act;
}) {
  const [selected, select] = useState<string | null>(() => {
    const id = sessionStorage.getItem("selectedAssignment");
    sessionStorage.removeItem("selectedAssignment");
    return id;
  });
  const [creating, create] = useState(false);
  const detail = useQuery({
    queryKey: ["assignment", selected],
    queryFn: () => api(`assignments/${selected}`),
    enabled: !!selected,
  });
  if (selected)
    return (
      <>
        <Button variant="ghost" onClick={() => select(null)}>
          <ArrowLeft size={16} />
          Vazifalarga qaytish
        </Button>
        {detail.isLoading ? (
          <p>Yuklanmoqda…</p>
        ) : detail.error ? (
          <p role="alert">{detail.error.message}</p>
        ) : (
          detail.data && (
            <Card>
              <Badge value={detail.data.status} />
              <h1>{detail.data.title}</h1>
              <p>{detail.data.description}</p>
              <h3>Fayllar</h3>
              {detail.data.attachments.map((a: Row) => (
                <Button
                  key={a.id}
                  variant="outline"
                  onClick={() =>
                    act(() => downloadAttachment(a.id, a.filename))
                  }
                >
                  {a.filename}
                </Button>
              ))}
              <h3>Topshirish tarixi</h3>
              {detail.data.submissions.length === 0 ? (
                <Empty />
              ) : (
                [...detail.data.submissions]
                  .reverse()
                  .map((s: Row, index: number) => (
                    <Submission
                      key={s.id}
                      sub={s}
                      newest={index === 0}
                      canReview={parent || teacher}
                      act={act}
                    />
                  ))
              )}
              {(parent || teacher) && (
                <QuizBuilder assignment={detail.data} act={act} />
              )}
            </Card>
          )
        )}
      </>
    );
  return (
    <>
      <div className="page-title">
        <div>
          <h1>
            Vazifalar<span className="title-dot">.</span>
          </h1>
          <p>Vazifa bering, natijani ko‘ring va fikr bildiring.</p>
        </div>
        {(parent || teacher) && (
          <Button onClick={() => create(!creating)}>
            <Plus size={18} />
            Yangi vazifa
          </Button>
        )}
      </div>
      {creating && (
        <AssignmentForm
          parent={parent}
          children={children}
          act={act}
          done={() => create(false)}
        />
      )}
      <Card>
        <TaskTable tasks={tasks} onOpen={select} />
      </Card>
    </>
  );
}
function AssignmentForm({
  parent,
  children,
  act,
  done,
}: {
  parent: boolean;
  children: Row[];
  act: Act;
  done: () => void;
}) {
  const [classId, setClass] = useState("");
  const classes = useQuery({
    queryKey: ["classrooms"],
    queryFn: () => api<Row[]>("classrooms"),
    enabled: !parent,
  });
  const roster = useQuery({
    queryKey: ["roster", classId],
    queryFn: () => api<Row[]>(`classrooms/${classId}/students`),
    enabled: !!classId,
  });
  const assignmentSchema = z.object({
    title: z.string().min(1).max(150),
    subject: z.string().min(1),
    description: z.string(),
    student_id: z.string().uuid(),
    reward_minutes: z.number().int().min(0).max(120),
  });
  const form = useForm<z.infer<typeof assignmentSchema>>({
    resolver: zodResolver(assignmentSchema),
    defaultValues: { reward_minutes: parent ? 15 : 0 },
  });
  return (
    <Card>
      <form
        className="form-grid"
        onSubmit={form.handleSubmit((values) =>
          act(async () => {
            await api("assignments", "POST", {
              ...values,
              ...(!parent ? { classroom_id: classId } : {}),
            });
            done();
          }),
        )}
      >
        {!parent && (
          <Field label="Sinf">
            <select
              required
              value={classId}
              onChange={(e) => setClass(e.target.value)}
            >
              <option value="">Tanlang</option>
              {classes.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </Field>
        )}
        <Field label="O‘quvchi">
          <select {...form.register("student_id")}>
            <option value="">Tanlang</option>
            {(parent ? children : roster.data || []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Sarlavha">
          <input {...form.register("title")} />
        </Field>
        <Field label="Fan">
          <input {...form.register("subject")} />
        </Field>
        <Field label="Tavsif">
          <textarea {...form.register("description")} />
        </Field>
        {parent && (
          <Field label="Mukofot daqiqalari">
            <input
              type="number"
              {...form.register("reward_minutes", { valueAsNumber: true })}
            />
          </Field>
        )}
        <div>
          {Object.keys(form.formState.errors).length > 0 && (
            <p role="alert">Barcha maydonlarni tekshiring.</p>
          )}
          <Button type="submit" disabled={form.formState.isSubmitting}>
            Vazifani berish
          </Button>
        </div>
      </form>
    </Card>
  );
}
function Submission({
  sub,
  newest,
  canReview,
  act,
}: {
  sub: Row;
  newest: boolean;
  canReview: boolean;
  act: Act;
}) {
  const [feedback, setFeedback] = useState("");
  const [evaluation, setEvaluation] = useState<Row | null>(null);
  return (
    <article className="submission">
      <Badge value={sub.status} />
      <p className="answer-text">{sub.text}</p>
      <small>{sub.created_at}</small>
      {canReview && newest && (
        <>
          <Field label="Izoh">
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
            />
          </Field>
          <div className="actions">
            <Button
              variant="outline"
              onClick={() =>
                act(async () =>
                  setEvaluation(
                    await api(
                      `ai/evaluate-homework?submission_id=${sub.id}`,
                      "POST",
                      {},
                    ),
                  ),
                )
              }
            >
              AI yordamida tekshirish
            </Button>
            <Button
              onClick={() =>
                act(() =>
                  api(`submissions/${sub.id}/review`, "POST", {
                    decision: "APPROVED",
                    feedback,
                  }),
                )
              }
            >
              <Check size={17} />
              Tasdiqlash
            </Button>
            <Button
              variant="outline"
              onClick={() =>
                act(() =>
                  api(`submissions/${sub.id}/review`, "POST", {
                    decision: "REVISION_REQUESTED",
                    feedback,
                  }),
                )
              }
            >
              Qayta ishlash
            </Button>
            <Button
              variant="danger"
              onClick={() =>
                act(() =>
                  api(`submissions/${sub.id}/review`, "POST", {
                    decision: "REJECTED",
                    feedback,
                  }),
                )
              }
            >
              Rad etish
            </Button>
          </div>
        </>
      )}
      {evaluation && (
        <div className="review-result">
          <strong>
            {evaluation.correct} / {evaluation.total}
          </strong>
          <p>{evaluation.feedback}</p>
          <p>
            Ishonch: {Math.round(evaluation.confidence * 100)}%. Yakuniy
            tasdiqni vakolatli katta yoshli beradi.
          </p>
        </div>
      )}
    </article>
  );
}
function Family({ children, act }: { children: Row[]; act: Act }) {
  const [code, setCode] = useState("");
  const [consent, setConsent] = useState(false);
  return (
    <>
      <div className="page-title">
        <div>
          <h1>
            Farzandlar<span className="title-dot">.</span>
          </h1>
          <p>Oila nazorati ochiq rozilikdan boshlanadi.</p>
        </div>
      </div>
      <Card>
        <h3>Yangi farzandni bog‘lash</h3>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            act(async () => {
              await api("families/link-child", "POST", {
                code,
                guardian_consent: consent,
              });
              setCode("");
            });
          }}
        >
          <Field label="Farzand ilovasidagi taklif kodi">
            <input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
          </Field>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            Vakolatli ota-ona/vasiy ekanimni va nazoratga roziligimni
            tasdiqlayman.
          </label>
          <Button type="submit" disabled={!consent}>
            Bog‘lash
          </Button>
        </form>
      </Card>
      <div className="stats-grid">
        {children.map((c) => (
          <Card key={c.id}>
            <div className="avatar">{c.name[0]}</div>
            <h3>{c.name}</h3>
            <p>{c.email}</p>
            <Button
              variant="danger"
              onClick={() =>
                act(() => api(`families/children/${c.id}`, "DELETE"))
              }
            >
              Rozilikni bekor qilish
            </Button>
          </Card>
        ))}
      </div>
    </>
  );
}
function Classes({ act }: { act: Act }) {
  const classes = useQuery({
    queryKey: ["classrooms"],
    queryFn: () => api<Row[]>("classrooms"),
  });
  const [name, setName] = useState("");
  const [selected, select] = useState("");
  const [code, setCode] = useState("");
  const roster = useQuery({
    queryKey: ["roster", selected],
    queryFn: () => api<Row[]>(`classrooms/${selected}/students`),
    enabled: !!selected,
  });
  return (
    <>
      <h1>Sinflar</h1>
      <Card>
        <form
          className="inline-form"
          onSubmit={(e) => {
            e.preventDefault();
            act(async () => {
              await api("classrooms", "POST", { name });
              setName("");
            });
          }}
        >
          <Field label="Sinf nomi">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </Field>
          <Button type="submit">Sinf yaratish</Button>
        </form>
        <div className="actions">
          {classes.data?.map((c) => (
            <Button
              key={c.id}
              variant="outline"
              onClick={() => {
                select(c.id);
                setCode("");
              }}
            >
              {c.name}
            </Button>
          ))}
        </div>
        {selected && (
          <>
            <Button
              onClick={() =>
                act(async () =>
                  setCode(
                    (await api(`classrooms/${selected}/invite`, "POST", {}))
                      .code,
                  ),
                )
              }
            >
              Taklif kodi
            </Button>
            {code && <p className="code">{code}</p>}
            <h3>O‘quvchilar</h3>
            {roster.data?.map((s) => (
              <p key={s.id}>{s.name}</p>
            ))}
          </>
        )}
      </Card>
    </>
  );
}
function Devices({ children, act }: { children: Row[]; act: Act }) {
  const [child, setChild] = useState("");
  const [id, setId] = useState("");
  const devices = useQuery({
    queryKey: ["devices", child],
    queryFn: () => api<Row[]>(`devices?child_id=${child}`),
    enabled: !!child,
  });
  return (
    <>
      <h1>Qurilma va ekran vaqti</h1>
      <p>
        Oddiy APK tizim darajasida ilovalarni cheklay olmaydi. Kuchli nazorat
        uchun mos qurilmada Device Owner kerak.
      </p>
      <Card>
        <Field label="Farzand">
          <select
            value={child}
            onChange={(e) => {
              setChild(e.target.value);
              setId("");
            }}
          >
            <option value="">Tanlang</option>
            {children.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        <div className="actions">
          {devices.data?.map((d) => (
            <Button variant="outline" key={d.id} onClick={() => setId(d.id)}>
              <Monitor size={17} />
              {d.name} · {d.mode}
            </Button>
          ))}
        </div>
        {devices.data?.length === 0 && <Empty />}
      </Card>
      {id && (
        <Card>
          <h3>Qurilmadan kelgan himoya holati</h3>
          <p>
            {devices.data?.find((d) => d.id === id)?.compliance
              ?.device_owner_reported
              ? devices.data?.find((d) => d.id === id)?.compliance
                  ?.uninstall_blocked
                ? "Qurilma ilovani o‘chirish bloki faol deb xabar berdi."
                : "Device Owner mavjud, lekin o‘chirish blokining tasdig‘i hali kelmagan."
              : "Oddiy Android rejimi: ilovani o‘chirishdan kuchli himoya mavjud emas."}
          </p>
          <p>Bu qurilma xabari; mustaqil apparat attestatsiyasi emas.</p>
        </Card>
      )}
      {id && (
        <PolicyEditor
          key={id}
          id={id}
          child={child}
          act={act}
          inventory={
            devices.data?.find((d) => d.id === id)?.compliance?.eligible_apps ||
            []
          }
        />
      )}
    </>
  );
}
function PolicyEditor({
  id,
  child,
  act,
  inventory,
}: {
  id: string;
  child: string;
  act: Act;
  inventory: Row[];
}) {
  const policy = useQuery({
    queryKey: ["policy", id],
    queryFn: () => api(`devices/${id}/policies`),
  });
  const [packages, setPackages] = useState("");
  const [defaultBlocked, setDefault] = useState(true);
  const [studyStart, setStudyStart] = useState("16:00");
  const [studyEnd, setStudyEnd] = useState("18:00");
  const [sleepStart, setSleepStart] = useState("22:00");
  const [sleepEnd, setSleepEnd] = useState("07:00");
  const [protection, setProtection] = useState(false);
  const [study, setStudy] = useState(false);
  const [sleep, setSleep] = useState(false);
  const [daily, setDaily] = useState(60);
  const [weekly, setWeekly] = useState(300);
  useEffect(() => {
    if (policy.data) {
      const p = policy.data.document;
      setPackages((p.blocked_packages || []).join("\n"));
      setDefault(p.default_blocked ?? true);
      setProtection(p.uninstall_protection ?? false);
      setStudy((p.study || []).length > 0);
      setSleep((p.sleep || []).length > 0);
      const time = (m: number) =>
        `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
      if (p.study?.[0]) {
        setStudyStart(time(p.study[0].start_minute));
        setStudyEnd(time(p.study[0].end_minute));
      }
      if (p.sleep?.[0]) {
        setSleepStart(time(p.sleep[0].start_minute));
        setSleepEnd(time(p.sleep[0].end_minute));
      }
    }
  }, [policy.data]);
  const minute = (s: string) =>
    Number(s.split(":")[0]) * 60 + Number(s.split(":")[1]);
  function document() {
    return {
      ...policy.data?.document,
      blocked_packages: packages.split(/\s+/).filter(Boolean),
      default_blocked: defaultBlocked,
      uninstall_protection: protection,
      study: study
        ? [
            {
              days: [1, 2, 3, 4, 5, 6, 7],
              start_minute: minute(studyStart),
              end_minute: minute(studyEnd),
            },
          ]
        : [],
      sleep: sleep
        ? [
            {
              days: [1, 2, 3, 4, 5, 6, 7],
              start_minute: minute(sleepStart),
              end_minute: minute(sleepEnd),
            },
          ]
        : [],
      timezone: "Asia/Tashkent",
      expected_version: policy.data?.version || 0,
    };
  }
  return (
    <>
      <Card>
        <h3>Ochiq ruxsat va himoya</h3>
        <p>
          Zarur aloqa, klaviatura va tizim ilovalari himoyalangan. Avval qurilma
          nazoratiga rozilik bering.
        </p>
        <Button
          variant="outline"
          onClick={() => act(() => api(`devices/${id}/authorize`, "POST", {}))}
        >
          Qurilma boshqaruviga roziman
        </Button>
      </Card>
      <Card>
        <h3>Cheklovlar</h3>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            act(() => api(`devices/${id}/policies`, "PUT", document()));
          }}
        >
          <div className="field">
            <span>Cheklanadigan ilovalar</span>
            {inventory.length === 0 && (
              <p className="muted">
                Qurilma boshqaruviga rozilik bering, so‘ng farzand ilovasidagi
                “Qurilma holati” sahifasida yangilang. Ilovalar nomlari shu
                yerda ko‘rinadi.
              </p>
            )}
            {inventory.map((app) => (
              <label className="checkbox-label" key={app.package}>
                <input
                  type="checkbox"
                  checked={packages.split(/\s+/).includes(app.package)}
                  onChange={(e) => {
                    const selected = new Set(
                      packages.split(/\s+/).filter(Boolean),
                    );
                    if (e.target.checked) selected.add(app.package);
                    else selected.delete(app.package);
                    setPackages([...selected].join("\n"));
                  }}
                />
                {app.label}
              </label>
            ))}
            <details>
              <summary>Qo‘shimcha texnik sozlama</summary>
              <Field label="Ilova paketlari">
                <textarea
                  value={packages}
                  onChange={(e) => setPackages(e.target.value)}
                />
              </Field>
            </details>
          </div>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={defaultBlocked}
              onChange={(e) => setDefault(e.target.checked)}
            />
            Mukofot bo‘lmaganda tanlangan ilovalarni cheklash
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={protection}
              onChange={(e) => setProtection(e.target.checked)}
            />
            Ruxsatli qurilmada boshqaruv ilovasini o‘chirishdan himoyalash
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={study}
              onChange={(e) => setStudy(e.target.checked)}
            />
            O‘qish jadvali
          </label>
          {study && (
            <div className="form-grid">
              <Field label="Boshlanish">
                <input
                  type="time"
                  value={studyStart}
                  onChange={(e) => setStudyStart(e.target.value)}
                  required
                />
              </Field>
              <Field label="Tugash">
                <input
                  type="time"
                  value={studyEnd}
                  onChange={(e) => setStudyEnd(e.target.value)}
                  required
                />
              </Field>
            </div>
          )}
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={sleep}
              onChange={(e) => setSleep(e.target.checked)}
            />
            Uyqu jadvali
          </label>
          {sleep && (
            <div className="form-grid">
              <Field label="Uyqu vaqti">
                <input
                  type="time"
                  value={sleepStart}
                  onChange={(e) => setSleepStart(e.target.value)}
                  required
                />
              </Field>
              <Field label="Ertalab">
                <input
                  type="time"
                  value={sleepEnd}
                  onChange={(e) => setSleepEnd(e.target.value)}
                  required
                />
              </Field>
            </div>
          )}
          <Button type="submit" disabled={!policy.data}>
            Siyosatni saqlash
          </Button>
        </form>
      </Card>
      <Card>
        <h3>Ekran vaqti budjeti</h3>
        <form
          className="form-grid"
          onSubmit={(e) => {
            e.preventDefault();
            act(() =>
              api(`rewards/budget/${child}`, "PUT", {
                daily_max: daily,
                weekly_max: weekly,
              }),
            );
          }}
        >
          <Field label="Kunlik maksimum (daqiqa)">
            <input
              type="number"
              min="0"
              max="240"
              value={daily}
              onChange={(e) => setDaily(Number(e.target.value))}
            />
          </Field>
          <Field label="Haftalik maksimum">
            <input
              type="number"
              min="0"
              max="1680"
              value={weekly}
              onChange={(e) => setWeekly(Number(e.target.value))}
            />
          </Field>
          <Button type="submit">Budjetni saqlash</Button>
        </form>
      </Card>
      <Card>
        <h3>Vaqtincha ochish va xavfsiz chiqarish</h3>
        <div className="actions">
          <Button
            onClick={() =>
              act(() =>
                api(`devices/${id}/policies`, "PUT", {
                  ...document(),
                  override_until: new Date(
                    Date.now() + 30 * 60000,
                  ).toISOString(),
                }),
              )
            }
          >
            30 daqiqa ota-ona ruxsati
          </Button>
          <Button
            variant="outline"
            onClick={() =>
              act(() =>
                api(`devices/${id}/policies`, "PUT", {
                  ...document(),
                  override_until: null,
                }),
              )
            }
          >
            Vaqtincha ruxsatni bekor qilish
          </Button>
          <Button
            variant="danger"
            onClick={() =>
              act(() => api(`devices/${id}/deprovision`, "POST", {}))
            }
          >
            Qurilmani nazoratdan chiqarish
          </Button>
        </div>
        <p>
          Cheklovlar qurilma bilan sinxronlashgach olib tashlanadi. Device Owner
          maqomini olib tashlash alohida administrator jarayoni.
        </p>
      </Card>
    </>
  );
}
function Reports({ children, teacher }: { children: Row[]; teacher: boolean }) {
  const [child, setChild] = useState("");
  const report = useQuery({
    queryKey: ["report", child],
    queryFn: () => api(`reports/weekly${child ? "?child_id=" + child : ""}`),
    enabled: !teacher || !!child,
  });
  const classes = useQuery({
    queryKey: ["classrooms"],
    queryFn: () => api<Row[]>("classrooms"),
    enabled: teacher,
  });
  const [classId, setClass] = useState("");
  const roster = useQuery({
    queryKey: ["roster", classId],
    queryFn: () => api<Row[]>(`classrooms/${classId}/students`),
    enabled: !!classId,
  });
  const data = report.data
    ? [
        { name: "Berilgan", count: report.data.assigned },
        { name: "Tasdiqlangan", count: report.data.approved },
      ]
    : [];
  return (
    <>
      <h1>O‘quv natijalari</h1>
      <Card>
        {teacher && (
          <Field label="Sinf">
            <select
              value={classId}
              onChange={(e) => {
                setClass(e.target.value);
                setChild("");
              }}
            >
              <option value="">Tanlang</option>
              {classes.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </Field>
        )}
        <Field label="O‘quvchi">
          <select value={child} onChange={(e) => setChild(e.target.value)}>
            <option value="">Tanlang</option>
            {(teacher ? roster.data || [] : children).map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        {report.error && <p role="alert">{report.error.message}</p>}
        {report.data && (
          <>
            <div className="chart">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#477BFF" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p>Bajarilish: {Math.round(report.data.completion_rate * 100)}%</p>
            {!teacher && (
              <p>
                Fokus: {report.data.focus_seconds || 0} soniya. Berilgan
                mukofot: {report.data.reward_minutes_earned || 0} daqiqa. Band
                qilingan ko‘ngilochar vaqt:{" "}
                {report.data.access_minutes_reserved || 0} daqiqa.
              </p>
            )}
          </>
        )}
      </Card>
    </>
  );
}
function Audit() {
  const q = useQuery({
    queryKey: ["audit"],
    queryFn: () => api<Row[]>("audit"),
  });
  return (
    <Card>
      <h1>Faoliyat tarixi</h1>
      <p>O‘z hisobingiz orqali bajarilgan amallar.</p>
      {q.data?.length === 0 && <Empty />}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Amal</th>
              <th>Resurs</th>
              <th>Vaqt</th>
            </tr>
          </thead>
          <tbody>
            {q.data?.map((a) => (
              <tr key={a.id}>
                <td>{a.action}</td>
                <td>{a.resource_id}</td>
                <td>{a.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
function QuizBuilder({ assignment, act }: { assignment: Row; act: Act }) {
  const [open, setOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [options, setOptions] = useState("");
  const [answer, setAnswer] = useState("");
  const [explanation, setExplanation] = useState("");
  const [validated, setValidated] = useState(false);
  return (
    <>
      <Button variant="outline" onClick={() => setOpen(!open)}>
        Test yaratish
      </Button>
      {open && (
        <form
          className="submission"
          onSubmit={(e) => {
            e.preventDefault();
            act(async () => {
              await api("quizzes", "POST", {
                assignment_id: assignment.id,
                title: assignment.title,
                time_limit_seconds: 600,
                validated,
                questions: [
                  {
                    prompt,
                    options: options.split("\n").filter(Boolean),
                    answer,
                    explanation,
                  },
                ],
              });
              setOpen(false);
            });
          }}
        >
          <Field label="Savol">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              required
            />
          </Field>
          <Field label="Variantlar (har qatorda bittadan)">
            <textarea
              value={options}
              onChange={(e) => setOptions(e.target.value)}
              required
            />
          </Field>
          <Field label="To‘g‘ri variant">
            <input
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              required
            />
          </Field>
          <Field label="Tushuntirish">
            <textarea
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              required
            />
          </Field>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={validated}
              onChange={(e) => setValidated(e.target.checked)}
            />
            Javob kalitini tekshirib tasdiqladim.
          </label>
          <Button type="submit" disabled={!validated}>
            Testni saqlash
          </Button>
        </form>
      )}
    </>
  );
}
function Operational() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const base = (
        import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"
      ).replace(/\/api\/v1\/?$/, "");
      const r = await fetch(base + "/health/ready");
      return { ready: r.ok };
    },
  });
  return (
    <Card>
      <h3>Xizmat holati</h3>
      <p>
        {health.data?.ready
          ? "API va ma’lumotlar bazasi tayyor"
          : "Xizmat holati tekshirilmoqda yoki tayyor emas"}
      </p>
      <p>
        Administrator roli bolalarning shaxsiy ma’lumotlariga avtomatik kirish
        bermaydi. Institutsional boshqaruvning kengaytirilgan modullari ishlab
        chiqish rejasida.
      </p>
    </Card>
  );
}

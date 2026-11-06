import { useEffect, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BookOpen,
  BrainCircuit,
  Check,
  Upload,
  ArrowLeft,
  ArrowRight,
  Shield,
  LoaderCircle,
} from "lucide-react";
import {
  api,
  uploadPdf,
  downloadBook,
  type Row,
  type User,
} from "../../services/api";
import { Button } from "../../components/ui/button";
const input = (
  label: string,
  value: string | number,
  onChange: (v: string) => void,
  type = "text",
) => (
  <label className="field">
    <span>{label}</span>
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      required
    />
  </label>
);
function Panel({ children }: { children: ReactNode }) {
  return <section className="card">{children}</section>;
}
export function ConceptMap({ content }: { content: Row }) {
  const concepts: Row[] = content.concepts || [];
  const positions = concepts.map((_, i) => {
    const a = -Math.PI / 2 + (2 * Math.PI * i) / Math.max(concepts.length, 1);
    return { x: 400 + 280 * Math.cos(a), y: 280 + 195 * Math.sin(a) };
  });
  return (
    <div className="concept-map">
      <svg
        viewBox="0 0 800 560"
        role="img"
        aria-label="Kitobning tushunchalar xaritasi"
      >
        <title>{content.title}</title>
        <defs>
          <linearGradient id="map-center">
            <stop stopColor="#477BFF" />
            <stop offset="1" stopColor="#3055BB" />
          </linearGradient>
        </defs>
        {positions.map((p, i) => (
          <path
            key={i}
            d={`M400 280 Q${400 + (p.x - 400) * 0.65} 280 ${p.x} ${p.y}`}
            fill="none"
            stroke="#BCD0FF"
            strokeWidth="2"
          />
        ))}
        <rect
          x="305"
          y="240"
          width="190"
          height="80"
          rx="20"
          fill="url(#map-center)"
        />
        <text
          x="400"
          y="277"
          textAnchor="middle"
          fill="white"
          fontSize="15"
          fontWeight="700"
        >
          {String(content.title || "Kitob").slice(0, 24)}
        </text>
        <text x="400" y="300" textAnchor="middle" fill="#DDE8FF" fontSize="11">
          Tushunchalar xaritasi
        </text>
        {concepts.map((c, i) => {
          const p = positions[i];
          const lines =
            String(c.title)
              .match(/.{1,21}/g)
              ?.slice(0, 2) || [];
          return (
            <g key={c.id}>
              <title>
                {c.title}: {c.explanation}
              </title>
              <rect
                x={p.x - 87}
                y={p.y - 37}
                width="174"
                height="74"
                rx="16"
                fill="white"
                stroke="#CFDCF4"
              />
              {lines.map((line, j) => (
                <text
                  key={j}
                  x={p.x}
                  y={p.y - 9 + j * 17}
                  textAnchor="middle"
                  fill="#101C35"
                  fontSize="12"
                  fontWeight="600"
                >
                  {line}
                </text>
              ))}
              <text
                x={p.x}
                y={p.y + 26}
                textAnchor="middle"
                fill="#5E739C"
                fontSize="10"
              >
                {c.source_page}-sahifa
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
function FlashCard({ concept }: { concept: Row }) {
  const [flipped, set] = useState(false);
  return (
    <button
      className={`flash-card ${flipped ? "flipped" : ""}`}
      onClick={() => set(!flipped)}
      aria-expanded={flipped}
    >
      <small>
        {concept.source_page}-sahifa ·{" "}
        {flipped ? "Tushuntirish" : "Bosib tushuntirishni ko‘ring"}
      </small>
      <strong>{concept.title}</strong>
      {flipped && <p>{concept.explanation}</p>}
    </button>
  );
}
export function LessonVisual({ lesson }: { lesson: Row }) {
  const [tab, setTab] = useState("map");
  const c = lesson.content;
  return (
    <>
      <div
        className="reading-tabs"
        role="tablist"
        aria-label="Vizual dars ko‘rinishi"
      >
        {[
          ["map", "Xarita"],
          ["cards", "Kartalar"],
          ["sources", "Manbalar"],
        ].map(([id, label]) => (
          <button
            role="tab"
            aria-selected={tab === id}
            className={tab === id ? "selected" : ""}
            key={id}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>
      <h2>{c.title}</h2>
      <p>{c.summary}</p>
      {tab === "map" && <ConceptMap content={c} />}{" "}
      {tab === "cards" && (
        <div className="flash-grid">
          {c.concepts.map((concept: Row) => (
            <FlashCard key={concept.id} concept={concept} />
          ))}
        </div>
      )}
      {tab === "sources" &&
        c.concepts.map((concept: Row) => (
          <blockquote className="source-quote" key={concept.id}>
            <strong>{concept.source_page}-sahifa</strong>
            <p>{concept.source_quote}</p>
            <small>{concept.explanation}</small>
          </blockquote>
        ))}
      {tab === "map" && (c.connections || []).length > 0 && (
        <ul className="connection-list">
          {c.connections.map((e: Row, i: number) => (
            <li key={i}>
              {c.concepts.find((n: Row) => n.id === e.from_id)?.title} →{" "}
              {e.label} → {c.concepts.find((n: Row) => n.id === e.to_id)?.title}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
function Progress({ data }: { data: Row }) {
  return (
    <div className="reading-progress">
      <div>
        <span>O‘quvchi belgilagan sahifalar</span>
        <strong>{data.self_reported_percent}%</strong>
      </div>
      <progress max="100" value={data.self_reported_percent} />
      <div>
        <span>Testda tekshirilgan sahifalar</span>
        <strong>{data.checked_percent}%</strong>
      </div>
      <progress className="verified" max="100" value={data.checked_percent} />
      <p>{data.notice}</p>
    </div>
  );
}
export function BooksPage({ user, children }: { user: User; children: Row[] }) {
  const client = useQueryClient();
  const adult = user.role !== "STUDENT";
  const [bookId, setBook] = useState("");
  const [planId, setPlan] = useState("");
  const [lessonId, setLesson] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [start, setStart] = useState(1);
  const [end, setEnd] = useState(3);
  const [editing, setEditing] = useState(false);
  const [page, setPage] = useState(1);
  const [attempt, setAttempt] = useState<Row | null>(null);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [selectedChild, setChild] = useState("");
  const [classId, setClass] = useState("");
  const [reward, setReward] = useState(15);
  const [autoReward, setAutoReward] = useState(false);
  const books = useQuery({
    queryKey: ["books"],
    queryFn: () => api<Row[]>("books"),
  });
  const plans = useQuery({
    queryKey: ["reading-plans"],
    queryFn: () => api<Row[]>("reading/plans"),
  });
  const book = useQuery({
    queryKey: ["book", bookId],
    queryFn: () => api(`books/${bookId}`),
    enabled: !!bookId,
  });
  const lessons = useQuery({
    queryKey: ["book-lessons", bookId],
    queryFn: () => api<Row[]>(`books/${bookId}/lessons`),
    enabled: !!bookId,
  });
  const plan = useQuery({
    queryKey: ["reading-plan", planId],
    queryFn: () => api(`reading/plans/${planId}`),
    enabled: !!planId,
  });
  const lesson = useQuery({
    queryKey: ["reading-lesson", lessonId],
    queryFn: () => api(`reading/lessons/${lessonId}`),
    enabled: !!lessonId,
  });
  const source = useQuery({
    queryKey: ["book-page", bookId, page],
    queryFn: () => api(`books/${bookId}/pages/${page}`),
    enabled: !!bookId,
  });
  const history = useQuery({
    queryKey: ["reading-attempts", planId],
    queryFn: () => api<Row[]>(`reading/plans/${planId}/attempts`),
    enabled: !!planId && adult,
  });
  const classes = useQuery({
    queryKey: ["classrooms"],
    queryFn: () => api<Row[]>("classrooms"),
    enabled: user.role === "TEACHER",
  });
  const roster = useQuery({
    queryKey: ["roster", classId],
    queryFn: () => api<Row[]>(`classrooms/${classId}/students`),
    enabled: !!classId,
  });
  const owner = book.data?.owner_id === user.id;
  async function perform(fn: () => Promise<void>) {
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
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    setSeconds(0);
    const timer = setInterval(() => {
      if (document.visibilityState === "visible")
        setSeconds((v) => Math.min(v + 1, 86400));
    }, 1000);
    return () => clearInterval(timer);
  }, [bookId, page]);
  function openBook(id: string, selectedPlan?: Row) {
    setBook(id);
    setPlan(selectedPlan?.id || "");
    setLesson("");
    setAttempt(null);
    setEditing(false);
    setPage(selectedPlan?.start_page || 1);
    setStart(selectedPlan?.start_page || 1);
    setEnd(
      Math.min(
        selectedPlan?.end_page || 3,
        books.data?.find((b) => b.id === id)?.page_count || 3,
      ),
    );
  }
  const errors = [
    error,
    books.error?.message,
    plan.error?.message,
    lessons.error?.message,
    source.error?.message,
  ].filter(Boolean);
  const minPage = plan.data?.start_page || 1,
    maxPage = plan.data?.end_page || book.data?.page_count || 1;
  return (
    <div className="books-page">
      <div className="page-title">
        <div>
          <span className="eyebrow">AI O‘QISH LABORATORIYASI</span>
          <h1>
            Kitoblar va tushunish testi<span className="title-dot">.</span>
          </h1>
          <p>Manbali vizual dars. Halol baholash. Chegaralangan mukofot.</p>
        </div>
        {bookId && (
          <Button
            variant="outline"
            onClick={() => {
              setBook("");
              setPlan("");
              setLesson("");
              setAttempt(null);
            }}
          >
            <ArrowLeft size={16} />
            Kitoblarga
          </Button>
        )}
      </div>
      {busy && (
        <p role="status" className="reading-working">
          <LoaderCircle size={17} />
          Ishlanmoqda… PDF/OCR va AI uchun biroz vaqt kerak.
        </p>
      )}
      {errors.map((e, i) => (
        <div className="error" role="alert" key={i}>
          {e}
        </div>
      ))}
      {!bookId && (
        <>
          {adult && (
            <Panel>
              <h3>
                <Upload size={18} /> PDF kitob yuklash
              </h3>
              <form
                className="form-grid"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (file)
                    perform(async () => {
                      const b = await uploadPdf("books", title, file);
                      setTitle("");
                      openBook(b.id);
                      setEnd(Math.min(3, b.page_count));
                    });
                }}
              >
                {input("Kitob nomi", title, setTitle)}
                <label className="field">
                  <span>PDF kitob</span>
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    required
                  />
                </label>
                <small>
                  10 MB gacha · 300 sahifagacha. Skanerlangan sahifalar uchun
                  OCR alohida bajariladi.
                </small>
                <Button type="submit" disabled={busy || !file}>
                  Kitobni yuklash
                </Button>
              </form>
            </Panel>
          )}
          <h3>O‘qish topshiriqlari</h3>
          <div className="book-grid">
            {plans.data?.map((p) => (
              <button
                className="book-card"
                key={p.id}
                onClick={() => openBook(p.book_id, p)}
              >
                <span className="book-cover">
                  <BookOpen size={36} />
                </span>
                <strong>{p.book_title}</strong>
                <small>
                  {adult ? p.student_name + " · " : ""}
                  {p.start_page}–{p.end_page}-sahifalar
                </small>
                <span>
                  O‘qishni ochish <ArrowRight size={15} />
                </span>
              </button>
            ))}
          </div>
          {plans.data?.length === 0 && (
            <Panel>
              <p>
                Hali o‘qish topshirig‘i yo‘q. Ota-ona yoki o‘qituvchi kitob va
                sahifalarni biriktiradi.
              </p>
            </Panel>
          )}
          {adult && (
            <>
              <h3>Kitoblar kutubxonasi</h3>
              <div className="book-grid">
                {books.data?.map((b) => (
                  <button
                    className="book-card"
                    key={b.id}
                    onClick={() => openBook(b.id)}
                  >
                    <span className="book-cover">
                      <BookOpen size={34} />
                    </span>
                    <strong>{b.title}</strong>
                    <small>
                      {b.page_count} sahifa ·{" "}
                      {b.status === "READY"
                        ? "Matn ajratildi"
                        : b.status === "PARTIAL"
                          ? "Qisman matn"
                          : "OCR kerak"}
                    </small>
                  </button>
                ))}
              </div>
            </>
          )}
        </>
      )}
      {bookId && book.data && (
        <>
          <Panel>
            <div className="section-heading">
              <div>
                <h2>{book.data.title}</h2>
                <small>
                  {book.data.page_count} sahifa · {book.data.status}
                </small>
              </div>
              {owner && (
                <Button
                  variant="outline"
                  onClick={() =>
                    perform(() => downloadBook(bookId, book.data!.filename))
                  }
                >
                  Asl PDFni yuklash
                </Button>
              )}
            </div>
            {plan.data && (
              <>
                <p>
                  {plan.data.student_name} · {plan.data.start_page}–
                  {plan.data.end_page}-sahifalar
                </p>
                <Progress data={plan.data.progress} />
              </>
            )}
            {owner && (
              <>
                <div className="form-grid">
                  {input(
                    "Boshlanish sahifasi",
                    start,
                    (v) => setStart(Number(v)),
                    "number",
                  )}
                  {input(
                    "Tugash sahifasi",
                    end,
                    (v) => setEnd(Number(v)),
                    "number",
                  )}
                </div>
                <div className="actions">
                  <Button
                    disabled={busy}
                    onClick={() =>
                      perform(async () => {
                        const l = await api(
                          `books/${bookId}/generate-lesson`,
                          "POST",
                          { start_page: start, end_page: end },
                        );
                        setLesson(l.id);
                        setEditing(false);
                      })
                    }
                  >
                    <BrainCircuit size={17} />
                    AI dars va test yaratish
                  </Button>
                  <Button
                    variant="outline"
                    disabled={busy}
                    onClick={() => {
                      setLesson("");
                      setEditing(true);
                    }}
                  >
                    Qo‘lda dars tuzish
                  </Button>
                  <Button
                    variant="outline"
                    disabled={busy}
                    onClick={() =>
                      perform(async () => {
                        await api(`books/${bookId}/ocr`, "POST", {
                          start_page: start,
                          end_page: end,
                        });
                        setPage(start);
                      })
                    }
                  >
                    Tanlangan sahifalarda OCR
                  </Button>
                </div>
                <p className="reading-note">
                  AI bo‘limi 1–5 sahifa, OCR 1–3 sahifa bilan ishlaydi. AI
                  kaliti ulanmagan bo‘lsa xato ochiq ko‘rsatiladi. Javoblarni
                  tekshirmasdan dars e’lon qilinmaydi.
                </p>
              </>
            )}
          </Panel>
          {owner && editing && (
            <LessonEditor
              initial={lesson.data?.can_edit ? lesson.data.content : null}
              start={start}
              end={end}
              busy={busy}
              onSave={(content) =>
                perform(async () => {
                  const l = await api(
                    lessonId
                      ? `reading/lessons/${lessonId}`
                      : `books/${bookId}/lessons`,
                    lessonId ? "PUT" : "POST",
                    { start_page: start, end_page: end, content },
                  );
                  setLesson(l.id);
                  setEditing(false);
                })
              }
            />
          )}
          <div className="reading-layout">
            <Panel>
              <div className="section-heading">
                <h3>Kitob matni</h3>
                <span>{page}-sahifa</span>
              </div>
              <div className="reading-source">
                {source.isLoading
                  ? "Yuklanmoqda…"
                  : source.data?.text ||
                    "Bu sahifada matn ajratilmadi. Ota-ona OCR bajarishi mumkin."}
              </div>
              {source.data?.method?.startsWith("OCR") && (
                <p className="reading-note">
                  OCR matni xatoga ega bo‘lishi mumkin. Asl manbani
                  solishtiring.
                </p>
              )}
              <div className="actions">
                <Button
                  variant="outline"
                  disabled={page <= minPage}
                  onClick={() => setPage((v) => v - 1)}
                >
                  Oldingi sahifa
                </Button>
                <Button
                  variant="outline"
                  disabled={page >= maxPage}
                  onClick={() => setPage((v) => v + 1)}
                >
                  Keyingi sahifa
                </Button>
                {!adult && planId && (
                  <Button
                    disabled={busy}
                    onClick={() =>
                      perform(async () => {
                        await api(`reading/plans/${planId}/progress`, "POST", {
                          page_number: page,
                          reported_seconds: seconds,
                        });
                      })
                    }
                  >
                    Sahifani belgilash
                  </Button>
                )}
              </div>
              <p className="reading-note">
                Sahifani belgilash o‘qilganini avtomatik isbotlamaydi va mukofot
                bermaydi.
              </p>
            </Panel>
            <Panel>
              <h3>Vizual darslar</h3>
              {lessons.data?.length === 0 && (
                <p>Hozircha tasdiqlangan dars yo‘q.</p>
              )}
              <div className="lesson-list">
                {lessons.data?.map((l) => (
                  <button
                    key={l.id}
                    className={lessonId === l.id ? "selected" : ""}
                    onClick={() => {
                      setLesson(l.id);
                      setAttempt(null);
                      setEditing(false);
                    }}
                  >
                    <strong>{l.title}</strong>
                    <small>
                      {l.start_page}–{l.end_page}-sahifa ·{" "}
                      {l.status === "PUBLISHED" ? "Tasdiqlangan" : "Qoralama"}
                    </small>
                  </button>
                ))}
              </div>
              {owner && (
                <AssignForm
                  children={children}
                  teacher={user.role === "TEACHER"}
                  classes={classes.data || []}
                  classId={classId}
                  setClass={setClass}
                  roster={roster.data || []}
                  child={selectedChild}
                  setChild={setChild}
                  reward={reward}
                  setReward={setReward}
                  autoReward={autoReward}
                  setAutoReward={setAutoReward}
                  disabled={busy}
                  onAssign={() =>
                    perform(async () => {
                      const p = await api(`books/${bookId}/plans`, "POST", {
                        student_id: selectedChild,
                        classroom_id: user.role === "TEACHER" ? classId : null,
                        start_page: start,
                        end_page: end,
                        reward_minutes: user.role === "TEACHER" ? 0 : reward,
                        auto_reward:
                          user.role === "TEACHER" ? false : autoReward,
                      });
                      setPlan(p.id);
                      setPage(start);
                    })
                  }
                />
              )}
            </Panel>
          </div>
          {lesson.data && (
            <Panel>
              <div className="section-heading">
                <div>
                  <span className="badge">
                    {lesson.data.status === "PUBLISHED"
                      ? "Tasdiqlangan"
                      : "Kattalar tekshiruvi kerak"}
                  </span>
                </div>
                {owner && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setStart(lesson.data!.start_page);
                      setEnd(lesson.data!.end_page);
                      setEditing(true);
                    }}
                  >
                    Darsni tahrirlash
                  </Button>
                )}
              </div>
              <LessonVisual lesson={lesson.data} />
              {owner && lesson.data.status === "DRAFT" && (
                <Publish
                  lesson={lesson.data}
                  disabled={busy}
                  publish={() =>
                    perform(async () => {
                      await api(`reading/lessons/${lessonId}/publish`, "POST", {
                        expected_version: lesson.data!.version,
                        answer_key_validated: true,
                      });
                    })
                  }
                />
              )}{" "}
              {owner && (
                <details className="review-questions">
                  <summary>
                    Javob kaliti va manbalarni tekshirish (
                    {lesson.data.question_count} savol)
                  </summary>
                  {lesson.data.content.questions?.map((q: Row, i: number) => (
                    <article key={i}>
                      <strong>
                        {i + 1}. {q.prompt}
                      </strong>
                      <p>To‘g‘ri javob: {q.options[q.correct_index]}</p>
                      <p>{q.explanation}</p>
                      <blockquote>
                        {q.source_page}-sahifa: {q.source_quote}
                      </blockquote>
                    </article>
                  ))}
                </details>
              )}
              {!adult &&
                planId &&
                lesson.data.status === "PUBLISHED" &&
                !attempt && (
                  <Button
                    disabled={busy}
                    onClick={() =>
                      perform(async () => {
                        setAttempt(
                          await api(
                            `reading/plans/${planId}/lessons/${lessonId}/attempts`,
                            "POST",
                            {},
                          ),
                        );
                        setAnswers({});
                      })
                    }
                  >
                    Tushunish testini boshlash
                  </Button>
                )}
              {attempt && (
                <div className="reading-test">
                  {attempt.status === "ACTIVE" ? (
                    <>
                      <h3>Tushunish testi</h3>
                      {attempt.questions.map((q: Row, i: number) => (
                        <fieldset key={q.id}>
                          <legend>
                            {i + 1}. {q.prompt}
                          </legend>
                          {q.options.map((option: string, index: number) => (
                            <label key={index}>
                              <input
                                type="radio"
                                name={q.id}
                                checked={answers[q.id] === index}
                                onChange={() =>
                                  setAnswers((v) => ({ ...v, [q.id]: index }))
                                }
                              />
                              {option}
                            </label>
                          ))}
                        </fieldset>
                      ))}
                      <Button
                        disabled={
                          busy ||
                          Object.keys(answers).length !==
                            attempt.questions.length
                        }
                        onClick={() =>
                          perform(async () =>
                            setAttempt(
                              await api(
                                `reading/attempts/${attempt.id}/finish`,
                                "POST",
                                { answers },
                              ),
                            ),
                          )
                        }
                      >
                        Testni yakunlash
                      </Button>
                    </>
                  ) : (
                    <ReadingResult attempt={attempt} />
                  )}
                </div>
              )}
            </Panel>
          )}
          {adult && planId && history.data && (
            <Panel>
              <h3>O‘qish va test natijalari</h3>
              {history.data.length === 0 && <p>Hali yakunlangan test yo‘q.</p>}
              {history.data.map((a) => (
                <article className="submission" key={a.id}>
                  <ReadingResult attempt={a} />
                  {user.role === "PARENT" &&
                    a.result.passed &&
                    !["GRANTED","ALREADY_GRANTED"].includes(a.result.reward.state) && (
                      <Button
                        onClick={() =>
                          perform(async () => {
                            await api(
                              `reading/attempts/${a.id}/approve-reward`,
                              "POST",
                              {},
                            );
                          })
                        }
                      >
                        Mukofotni tasdiqlash
                      </Button>
                    )}
                </article>
              ))}
            </Panel>
          )}
        </>
      )}
    </div>
  );
}
function ReadingResult({ attempt }: { attempt: Row }) {
  const states: Row = {
    GRANTED: "Mukofot berildi",
    ALREADY_GRANTED: "Bu bo‘lim mukofoti avval berilgan",
    HUMAN_REQUIRED: "Ota-ona tasdig‘i kerak",
    BUDGET_REACHED: "Kunlik mukofot chegarasi",
    NOT_CONFIGURED: "Mukofot belgilanmagan",
    NOT_PASSED: "Qayta mashq qilish tavsiya etiladi",
  };
  return (
    <div className="reading-result" role="status">
      <strong>
        {attempt.result.percent}% — {attempt.result.correct}/
        {attempt.result.total}
      </strong>
      <p>
        {attempt.result.passed
          ? "Tushunish testi muvaffaqiyatli yakunlandi."
          : "Xatolarni ko‘rib chiqing va qayta mashq qiling."}
      </p>
      <p>
        {states[attempt.result.reward.state]} · {attempt.result.reward.minutes}{" "}
        daqiqa
      </p>
      {attempt.review?.map((q: Row) => (
        <p key={q.id}>
          {q.source_page}-sahifa: {q.explanation}
        </p>
      ))}
    </div>
  );
}
function Publish({
  lesson,
  disabled,
  publish,
}: {
  lesson: Row;
  disabled: boolean;
  publish: () => void;
}) {
  const [checked, set] = useState(false);
  useEffect(() => set(false), [lesson.id, lesson.version]);
  return (
    <div className="publish-panel">
      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => set(e.target.checked)}
        />
        Manbalar va barcha javob kalitlarini tekshirdim, tasdiqlayman.
      </label>
      <Button disabled={disabled || !checked} onClick={publish}>
        <Check size={17} />
        Darsni e’lon qilish
      </Button>
    </div>
  );
}
function AssignForm(p: {
  children: Row[];
  teacher: boolean;
  classes: Row[];
  classId: string;
  setClass: (s: string) => void;
  roster: Row[];
  child: string;
  setChild: (s: string) => void;
  reward: number;
  setReward: (v: number) => void;
  autoReward: boolean;
  setAutoReward: (v: boolean) => void;
  disabled: boolean;
  onAssign: () => void;
}) {
  return (
    <form
      className="reading-assign"
      onSubmit={(e) => {
        e.preventDefault();
        p.onAssign();
      }}
    >
      <h3>O‘qish uchun biriktirish</h3>
      {p.teacher && (
        <label className="field">
          <span>Sinf</span>
          <select
            value={p.classId}
            onChange={(e) => p.setClass(e.target.value)}
            required
          >
            <option value="">Tanlang</option>
            {p.classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
      )}
      <label className="field">
        <span>O‘quvchi</span>
        <select
          value={p.child}
          onChange={(e) => p.setChild(e.target.value)}
          required
        >
          <option value="">Tanlang</option>
          {(p.teacher ? p.roster : p.children).map((c) => (
            <option value={c.id} key={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </label>
      {!p.teacher && (
        <>
          {input(
            "Bo‘lim uchun mukofot (0–30 daqiqa)",
            p.reward,
            (v) => p.setReward(Number(v)),
            "number",
          )}
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={p.autoReward}
              onChange={(e) => p.setAutoReward(e.target.checked)}
            />
            Tasdiqlangan testdan keyin avtomatik mukofot
          </label>
          <p className="reading-note">
            Global avtopilot yoqilgan bo‘lishi kerak. Chegara va javob kaliti
            serverda tekshiriladi.
          </p>
        </>
      )}
      <Button disabled={p.disabled || !p.child} type="submit">
        Sahifalarni biriktirish
      </Button>
    </form>
  );
}
function LessonEditor({
  initial,
  start,
  end,
  busy,
  onSave,
}: {
  initial: Row | null;
  start: number;
  end: number;
  busy: boolean;
  onSave: (content: Row) => void;
}) {
  const blankQuestion = () => ({
    prompt: "",
    options: ["", ""],
    correct_index: 0,
    explanation: "",
    source_page: start,
    source_quote: "",
  });
  const [title, setTitle] = useState(initial?.title || "");
  const [summary, setSummary] = useState(initial?.summary || "");
  const [concepts, setConcepts] = useState<Row[]>(
    initial?.concepts || [
      {
        id: "c1",
        title: "",
        explanation: "",
        source_page: start,
        source_quote: "",
      },
    ],
  );
  const [questions, setQuestions] = useState<Row[]>(
    initial?.questions || [blankQuestion(), blankQuestion(), blankQuestion()],
  );
  const update = (
    kind: "concepts" | "questions",
    index: number,
    key: string,
    value: unknown,
  ) => {
    const set = kind === "concepts" ? setConcepts : setQuestions;
    set((old) =>
      old.map((item, i) => (i === index ? { ...item, [key]: value } : item)),
    );
  };
  return (
    <Panel>
      <h3>
        Dars muharriri · {start}–{end}-sahifa
      </h3>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSave({
            title,
            summary,
            concepts,
            connections:
              initial?.connections?.filter(
                (e: Row) =>
                  concepts.some((c) => c.id === e.from_id) &&
                  concepts.some((c) => c.id === e.to_id),
              ) || [],
            questions,
          });
        }}
      >
        {input("Dars nomi", title, setTitle)}
        <label className="field">
          <span>Qisqa tushuntirish</span>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            required
          />
        </label>
        <h3>Vizual tushunchalar</h3>
        {concepts.map((c, i) => (
          <div className="editor-section" key={i}>
            {input(`Tushuncha ${i + 1}`, c.title, (v) =>
              update("concepts", i, "title", v),
            )}
            <label className="field">
              <span>Tushuntirish</span>
              <textarea
                value={c.explanation}
                onChange={(e) =>
                  update("concepts", i, "explanation", e.target.value)
                }
                required
              />
            </label>
            {input(
              "Manba sahifasi",
              c.source_page,
              (v) => update("concepts", i, "source_page", Number(v)),
              "number",
            )}
            <label className="field">
              <span>Kitobdan aynan olingan iqtibos</span>
              <textarea
                value={c.source_quote}
                onChange={(e) =>
                  update("concepts", i, "source_quote", e.target.value)
                }
                required
              />
            </label>
          </div>
        ))}
        <Button
          type="button"
          variant="outline"
          disabled={concepts.length >= 8}
          onClick={() =>
            setConcepts((v) => [
              ...v,
              {
                id: "c" + (v.length + 1),
                title: "",
                explanation: "",
                source_page: start,
                source_quote: "",
              },
            ])
          }
        >
          Tushuncha qo‘shish
        </Button>
        <h3>Test savollari</h3>
        {questions.map((q, i) => (
          <div className="editor-section" key={i}>
            <h4>{i + 1}-savol</h4>
            {input(`Savol ${i + 1}`, q.prompt, (v) =>
              update("questions", i, "prompt", v),
            )}
            <label className="field">
              <span>Variantlar — har qatorda bittadan</span>
              <textarea
                value={q.options.join("\n")}
                onChange={(e) =>
                  update("questions", i, "options", e.target.value.split("\n"))
                }
                required
              />
            </label>
            <label className="field">
              <span>To‘g‘ri javob</span>
              <select
                value={q.correct_index}
                onChange={(e) =>
                  update(
                    "questions",
                    i,
                    "correct_index",
                    Number(e.target.value),
                  )
                }
              >
                {q.options.map((o: string, j: number) => (
                  <option value={j} key={j}>
                    {j + 1}. {o}
                  </option>
                ))}
              </select>
            </label>
            {input("Javob tushuntirishi", q.explanation, (v) =>
              update("questions", i, "explanation", v),
            )}
            {input(
              "Savol manba sahifasi",
              q.source_page,
              (v) => update("questions", i, "source_page", Number(v)),
              "number",
            )}
            <label className="field">
              <span>Savolning aniq manba iqtibosi</span>
              <textarea
                value={q.source_quote}
                onChange={(e) =>
                  update("questions", i, "source_quote", e.target.value)
                }
                required
              />
            </label>
            {questions.length > 3 && (
              <Button
                type="button"
                variant="danger"
                onClick={() => setQuestions((v) => v.filter((_, j) => j !== i))}
              >
                Savolni olib tashlash
              </Button>
            )}
          </div>
        ))}
        <div className="actions">
          <Button
            type="button"
            variant="outline"
            disabled={questions.length >= 10}
            onClick={() => setQuestions((v) => [...v, blankQuestion()])}
          >
            Savol qo‘shish
          </Button>
          <Button type="submit" disabled={busy}>
            Dars qoralamasini saqlash
          </Button>
        </div>
      </form>
    </Panel>
  );
}

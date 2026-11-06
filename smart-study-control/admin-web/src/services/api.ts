import { z } from "zod";
export const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string(),
  login: z.string().nullable().optional(),
  must_change_password: z.boolean().optional().default(false),
  role: z.enum(["STUDENT", "PARENT", "TEACHER", "SCHOOL_ADMIN", "SUPER_ADMIN"]),
});
const SessionSchema = z
  .object({
    access_token: z.string(),
    refresh_token: z.string(),
    user: UserSchema,
  })
  .passthrough();
export type User = z.infer<typeof UserSchema>;
export type Session = z.infer<typeof SessionSchema>;
export type Row = Record<string, any>;
const API = (
  import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"
).replace(/\/$/, "");
let session: Session | null = null;
let refreshing: Promise<void> | null = null;
let listener: ((value: Session | null) => void) | null = null;
export function subscribe(fn: typeof listener) {
  listener = fn;
  return () => {
    listener = null;
  };
}
export function getSession() {
  return session;
}
export function setSession(value: unknown) {
  session = value ? SessionSchema.parse(value) : null;
  listener?.(session);
}
async function refreshSession() {
  if (!refreshing)
    refreshing = (async () => {
      try {
        setSession(
          await api("auth/refresh", "POST", {
            refresh_token: session!.refresh_token,
          }),
        );
      } catch (e) {
        setSession(null);
        throw e;
      } finally {
        refreshing = null;
      }
    })();
  await refreshing;
}
async function authenticatedFetch(
  path: string,
  init: RequestInit = {},
  retried = false,
): Promise<Response> {
  const headers = new Headers(init.headers);
  if (session) headers.set("Authorization", `Bearer ${session.access_token}`);
  let response: Response;
  try {
    response = await fetch(`${API}/${path}`, { ...init, headers });
  } catch {
    throw new Error("Server bilan ulanish yo‘q. Qayta urinib ko‘ring.");
  }
  if (response.status === 401 && session && !retried) {
    await refreshSession();
    return authenticatedFetch(path, init, true);
  }
  return response;
}
export async function api<T = Row>(
  path: string,
  method = "GET",
  body?: unknown,
  retried = false,
  requestKey?: string,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (session) headers.Authorization = `Bearer ${session.access_token}`;
  if (
    method === "POST" &&
    (path.includes("/submit") ||
      path === "rewards/redeem" ||
      path.endsWith("/attempts"))
  )
    headers["Idempotency-Key"] = requestKey || crypto.randomUUID();
  let response: Response;
  try {
    response = await fetch(`${API}/${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error("Server bilan ulanish yo‘q. Qayta urinib ko‘ring.");
  }
  if (
    response.status === 401 &&
    session &&
    !path.startsWith("auth/") &&
    !retried
  ) {
    await refreshSession();
    return api<T>(path, method, body, true, headers["Idempotency-Key"]);
  }
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      data.error?.message || `So‘rov bajarilmadi (${response.status})`,
    );
  return data as T;
}
export async function logout() {
  try {
    if (session)
      await api("auth/logout", "POST", {
        refresh_token: session.refresh_token,
      });
  } finally {
    setSession(null);
  }
}
export async function downloadAttachment(id: string, name: string) {
  const response = await authenticatedFetch(`attachments/${id}`);
  if (!response.ok) throw new Error("Faylni ochish uchun qayta kiring.");
  const url = URL.createObjectURL(await response.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function uploadPdf(
  path: string,
  title: string,
  file: File,
): Promise<Row> {
  const form = new FormData();
  form.set("title", title);
  form.set("file", file);
  const response = await authenticatedFetch(path, {
    method: "POST",
    body: form,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error?.message || "PDF yuklanmadi");
  return data;
}
export async function downloadBook(id: string, name: string) {
  const response = await authenticatedFetch(`books/${id}/file`);
  if (!response.ok) throw new Error("Kitob fayliga ruxsat yo‘q");
  const url = URL.createObjectURL(await response.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

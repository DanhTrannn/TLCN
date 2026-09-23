"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { getRoleLabel, resolvePostLoginRedirect } from "@/lib/role-routes";

const DEMO_ACCOUNTS = [
  { role: "CEO / Admin", email: "admin@fashion.local", label: "CEO" },
  { role: "Kinh doanh", email: "sales@fashion.local", label: "Sales" },
  { role: "Marketing", email: "marketing@fashion.local", label: "Marketing" },
  { role: "Quản lý Store", email: "store_mgr@fashion.local", label: "Store" },
  { role: "Kho & COGS", email: "inventory@fashion.local", label: "Kho" },
  { role: "Vận hành", email: "operations@fashion.local", label: "Vận hành" },
  { role: "Kỹ thuật", email: "sysadmin@fashion.local", label: "SysAdmin" },
];

function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const rawReturnTo = params.get("returnTo");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function fillDemoAccount(demoEmail: string) {
    setEmail(demoEmail);
    setPassword("Password123!");
    setError(null);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user = await login(email.trim(), password);
      const targetUrl = resolvePostLoginRedirect(user.role, rawReturnTo);
      const roleLabel = getRoleLabel(user.role);
      setSuccessNotice(`Đăng nhập thành công! Đang chuyển hướng đến ${roleLabel}…`);
      router.push(targetUrl);
      router.refresh();
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Đăng nhập thất bại");
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto grid min-h-[calc(100vh-8rem)] max-w-5xl items-center gap-8 px-5 py-10 sm:px-6 lg:grid-cols-[0.9fr_1.1fr]">
      <section className="hidden rounded-[2.25rem] bg-ink p-10 text-paper shadow-lift lg:block">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent text-white">
          <Icon name="sparkles" />
        </span>
        <p className="mt-10 text-xs font-semibold uppercase tracking-[0.2em] text-paper/65">D&K Membership</p>
        <h1 className="mt-4 font-serif text-5xl leading-[1.05]">Trở lại với những lựa chọn của riêng bạn.</h1>
        <p className="mt-5 max-w-md leading-7 text-paper/65">
          Hệ thống tự động nhận diện vai trò nghiệp vụ (CEO, Kinh doanh, Marketing, Kho, Vận hành, Quản lý Cửa hàng) để điều hướng trực tiếp đến không gian làm việc tương ứng.
        </p>
      </section>

      <section className="surface-card p-6 sm:p-9">
        <p className="eyebrow">Tài khoản</p>
        <h2 className="mt-3 font-serif text-4xl tracking-[-0.035em]">Đăng nhập</h2>
        <p className="mt-3 text-sm leading-6 text-muted">Chào mừng bạn quay lại D&K Fashion.</p>

        {/* Demo Fast Login Pills */}
        <div className="mt-6 rounded-2xl border border-line bg-paper/60 p-4">
          <p className="text-xs font-semibold text-muted">Đăng nhập nhanh tài khoản mẫu theo vai trò:</p>
          <div className="mt-2.5 flex flex-wrap gap-1.5">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                className={`rounded-lg border px-2.5 py-1 text-xs font-medium transition ${
                  email === acc.email
                    ? "border-accent bg-accent text-white shadow-sm"
                    : "border-line bg-surface text-ink hover:border-accent/40 hover:bg-paper"
                }`}
                key={acc.email}
                onClick={() => fillDemoAccount(acc.email)}
                title={`${acc.role} (${acc.email})`}
                type="button"
              >
                {acc.label}
              </button>
            ))}
          </div>
        </div>

        <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="login-email">
            Email
            <input
              autoComplete="email"
              className="form-control"
              id="login-email"
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </label>
          <label className="field-label" htmlFor="login-password">
            Mật khẩu
            <input
              autoComplete="current-password"
              className="form-control"
              id="login-password"
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>

          {error ? <p aria-live="polite" className="feedback-error">{error}</p> : null}

          {successNotice ? (
            <div className="flex items-center gap-2.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-sm font-semibold text-emerald-700 dark:text-emerald-400 animate-pulse">
              <Icon name="check" size={18} />
              <span>{successNotice}</span>
            </div>
          ) : null}

          <button className="button-primary w-full" disabled={submitting} type="submit">
            {submitting ? "Đang chuyển hướng…" : "Đăng nhập"}
            {!submitting ? <Icon name="arrow-right" size={18} /> : null}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-muted">
          Chưa có tài khoản?{" "}
          <Link
            className="font-semibold text-accent hover:underline"
            href={`/register${rawReturnTo ? `?returnTo=${encodeURIComponent(rawReturnTo)}` : ""}`}
          >
            Đăng ký ngay
          </Link>
        </p>
      </section>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="page-shell">
          <div className="surface-card h-96 animate-pulse" />
        </main>
      }
    >
      <LoginForm />
    </Suspense>
  );
}

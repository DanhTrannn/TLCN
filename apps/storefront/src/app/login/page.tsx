"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const INTERNAL_PATHS = ["/", "/products", "/cart", "/checkout", "/orders", "/admin"];

function safeReturnTo(raw: string | null): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) return "/products";
  const base = raw.split("?")[0];
  if (INTERNAL_PATHS.some((path) => base === path || base.startsWith(`${path}/`))) return raw;
  return "/products";
}

function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const returnTo = safeReturnTo(params.get("returnTo"));
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email.trim(), password);
      router.push(returnTo);
      router.refresh();
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Đăng nhập thất bại");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto grid min-h-[calc(100vh-8rem)] max-w-5xl items-center gap-8 px-5 py-10 sm:px-6 lg:grid-cols-[0.9fr_1.1fr]">
      <section className="hidden rounded-[2.25rem] bg-ink p-10 text-paper shadow-lift lg:block">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent text-white"><Icon name="sparkles" /></span>
        <p className="mt-10 text-xs font-semibold uppercase tracking-[0.2em] text-paper/65">D&K Membership</p>
        <h1 className="mt-4 font-serif text-5xl leading-[1.05]">Trở lại với những lựa chọn của riêng bạn.</h1>
        <p className="mt-5 max-w-md leading-7 text-paper/65">Theo dõi đơn hàng, lưu sản phẩm yêu thích và checkout nhanh hơn.</p>
      </section>

      <section className="surface-card p-6 sm:p-9">
        <p className="eyebrow">Tài khoản</p>
        <h2 className="mt-3 font-serif text-4xl tracking-[-0.035em]">Đăng nhập</h2>
        <p className="mt-3 text-sm leading-6 text-muted">Chào mừng bạn quay lại D&K.</p>
        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="login-email">Email
            <input autoComplete="email" className="form-control" id="login-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className="field-label" htmlFor="login-password">Mật khẩu
            <input autoComplete="current-password" className="form-control" id="login-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          {error ? <p aria-live="polite" className="feedback-error">{error}</p> : null}
          <button className="button-primary w-full" type="submit" disabled={submitting}>
            {submitting ? "Đang xử lý…" : "Đăng nhập"}
            {!submitting ? <Icon name="arrow-right" size={18} /> : null}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-muted">Chưa có tài khoản? <Link className="font-semibold text-accent hover:underline" href={`/register?returnTo=${encodeURIComponent(returnTo)}`}>Đăng ký ngay</Link></p>
      </section>
    </main>
  );
}

export default function LoginPage() {
  return <Suspense fallback={<main className="page-shell"><div className="surface-card h-96 animate-pulse" /></main>}><LoginForm /></Suspense>;
}

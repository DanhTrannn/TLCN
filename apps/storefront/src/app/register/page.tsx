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

function RegisterForm() {
  const { register } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const returnTo = safeReturnTo(params.get("returnTo"));
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(email.trim(), password, displayName.trim());
      router.push(returnTo);
      router.refresh();
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Đăng ký thất bại");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto grid min-h-[calc(100vh-8rem)] max-w-5xl items-center gap-8 px-5 py-10 sm:px-6 lg:grid-cols-[0.9fr_1.1fr]">
      <section className="hidden rounded-[2.25rem] bg-moss p-10 text-paper shadow-lift lg:block">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-paper/10"><Icon name="heart" /></span>
        <p className="mt-10 text-xs font-semibold uppercase tracking-[0.2em] text-paper/60">D&K Membership</p>
        <h1 className="mt-4 font-serif text-5xl leading-[1.05]">Lưu lại những món đồ phù hợp với phong cách của bạn.</h1>
        <p className="mt-5 max-w-md leading-7 text-paper/70">Một tài khoản cho wishlist, giỏ hàng và toàn bộ hành trình đơn hàng.</p>
      </section>

      <section className="surface-card p-6 sm:p-9">
        <p className="eyebrow">Thành viên mới</p>
        <h2 className="mt-3 font-serif text-4xl tracking-[-0.035em]">Tạo tài khoản</h2>
        <p className="mt-3 text-sm leading-6 text-muted">Bắt đầu trải nghiệm mua sắm được cá nhân hóa.</p>
        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="register-name">Tên hiển thị
            <input autoComplete="name" className="form-control" id="register-name" type="text" value={displayName} onChange={(event) => setDisplayName(event.target.value)} required />
          </label>
          <label className="field-label" htmlFor="register-email">Email
            <input autoComplete="email" className="form-control" id="register-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className="field-label" htmlFor="register-password">Mật khẩu
            <input autoComplete="new-password" className="form-control" id="register-password" type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required />
            <span className="mt-2 block text-xs font-normal text-muted">Sử dụng tối thiểu 8 ký tự.</span>
          </label>
          {error ? <p aria-live="polite" className="feedback-error">{error}</p> : null}
          <button className="button-primary w-full" type="submit" disabled={submitting}>
            {submitting ? "Đang xử lý…" : "Tạo tài khoản"}
            {!submitting ? <Icon name="arrow-right" size={18} /> : null}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-muted">Đã có tài khoản? <Link className="font-semibold text-accent hover:underline" href={`/login?returnTo=${encodeURIComponent(returnTo)}`}>Đăng nhập</Link></p>
      </section>
    </main>
  );
}

export default function RegisterPage() {
  return <Suspense fallback={<main className="page-shell"><div className="surface-card h-96 animate-pulse" /></main>}><RegisterForm /></Suspense>;
}

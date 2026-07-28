"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const INTERNAL_PATHS = ["/", "/products", "/cart", "/checkout", "/orders", "/admin"];

function safeReturnTo(raw: string | null): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) return "/products";
  const base = raw.split("?")[0];
  if (INTERNAL_PATHS.some((p) => base === p || base.startsWith(`${p}/`))) return raw;
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
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Đăng ký thất bại");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto max-w-md px-6 py-14">
      <h1 className="text-3xl font-semibold">Đăng ký</h1>
      <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
        <label className="block text-sm">
          Tên hiển thị
          <input
            className="mt-1 w-full rounded-lg border border-ink/20 px-3 py-2"
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
          />
        </label>
        <label className="block text-sm">
          Email
          <input
            className="mt-1 w-full rounded-lg border border-ink/20 px-3 py-2"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="block text-sm">
          Mật khẩu (tối thiểu 8 ký tự)
          <input
            className="mt-1 w-full rounded-lg border border-ink/20 px-3 py-2"
            type="password"
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error ? <p className="text-sm text-accent">{error}</p> : null}
        <button
          className="w-full rounded-full bg-ink px-4 py-2 text-paper disabled:opacity-60"
          type="submit"
          disabled={submitting}
        >
          {submitting ? "Đang xử lý…" : "Đăng ký"}
        </button>
      </form>
      <p className="mt-6 text-sm text-ink/70">
        Đã có tài khoản?{" "}
        <Link className="text-accent" href={`/login?returnTo=${encodeURIComponent(returnTo)}`}>
          Đăng nhập
        </Link>
      </p>
    </main>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<main className="mx-auto max-w-md px-6 py-14" />}>
      <RegisterForm />
    </Suspense>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Icon } from "@/components/ui/Icon";

export function Footer() {
  const pathname = usePathname();
  if (pathname.startsWith("/admin")) return null;

  return (
    <footer className="mt-12 border-t border-white/10 bg-ink text-paper sm:mt-16">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-12 sm:px-6 md:grid-cols-[1.35fr_0.8fr_0.8fr] md:py-14">
        <div>
          <Link className="inline-flex items-center gap-3" href="/">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent text-xs font-bold tracking-[0.12em] text-white">D&K</span>
            <span className="font-serif text-xl font-semibold">D&K</span>
          </Link>
          <p className="mt-5 max-w-sm text-sm leading-7 text-paper/65">
            Trang phục nữ tối giản, dễ phối và vừa vặn với nhịp sống mỗi ngày.
          </p>
          <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-paper/65">
            <Icon name="shield" size={16} />
            Thanh toán và tồn kho minh bạch
          </div>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-paper/65">Mua sắm</p>
          <div className="mt-4 flex flex-col gap-1 text-sm text-paper/70">
            <Link className="min-h-11 rounded-lg px-2 py-2.5 transition hover:bg-white/5 hover:text-paper" href="/products">Sản phẩm</Link>
            <Link className="min-h-11 rounded-lg px-2 py-2.5 transition hover:bg-white/5 hover:text-paper" href="/wishlist">Yêu thích</Link>
            <Link className="min-h-11 rounded-lg px-2 py-2.5 transition hover:bg-white/5 hover:text-paper" href="/cart">Giỏ hàng</Link>
          </div>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-paper/65">Tài khoản</p>
          <div className="mt-4 flex flex-col gap-1 text-sm text-paper/70">
            <Link className="min-h-11 rounded-lg px-2 py-2.5 transition hover:bg-white/5 hover:text-paper" href="/orders">Đơn hàng</Link>
            <Link className="min-h-11 rounded-lg px-2 py-2.5 transition hover:bg-white/5 hover:text-paper" href="/login">Đăng nhập</Link>
            <Link className="min-h-11 rounded-lg px-2 py-2.5 transition hover:bg-white/5 hover:text-paper" href="/register">Đăng ký</Link>
          </div>
        </div>
      </div>
      <div className="border-t border-white/10 px-5 py-5 text-center text-xs text-paper/65 sm:px-6">
        © 2026 D&K · Phong cách riêng mỗi ngày.
      </div>
    </footer>
  );
}

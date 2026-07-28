import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-ink/10 bg-white/35">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-12 md:grid-cols-[1.2fr_0.8fr_0.8fr]">
        <div>
          <Link className="inline-flex items-center gap-3" href="/">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-ink text-xs font-bold tracking-wider text-paper">NÉT</span>
            <span className="font-semibold tracking-tight">NÉT Studio</span>
          </Link>
          <p className="mt-4 max-w-sm text-sm leading-6 text-ink/55">
            Trang phục nữ tối giản, dễ phối và vừa vặn với nhịp sống mỗi ngày.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink/45">Mua sắm</p>
          <div className="mt-4 flex flex-col gap-3 text-sm text-ink/65">
            <Link className="hover:text-accent" href="/products">Sản phẩm</Link>
            <Link className="hover:text-accent" href="/wishlist">Yêu thích</Link>
            <Link className="hover:text-accent" href="/cart">Giỏ hàng</Link>
          </div>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink/45">Tài khoản</p>
          <div className="mt-4 flex flex-col gap-3 text-sm text-ink/65">
            <Link className="hover:text-accent" href="/orders">Đơn hàng</Link>
            <Link className="hover:text-accent" href="/login">Đăng nhập</Link>
            <Link className="hover:text-accent" href="/register">Đăng ký</Link>
          </div>
        </div>
      </div>
      <div className="border-t border-ink/10 px-6 py-5 text-center text-xs text-ink/45">
        © 2026 NÉT Studio. Mỗi ngày một nét riêng.
      </div>
    </footer>
  );
}

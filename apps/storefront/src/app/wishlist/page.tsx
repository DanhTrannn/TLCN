"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd, getWishlist, removeWishlistProduct, type WishlistItem } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function WishlistPage() {
  const { customer, loading: authLoading } = useAuth();
  const [items, setItems] = useState<WishlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!customer) {
      setLoading(false);
      return;
    }
    getWishlist()
      .then((wishlist) => setItems(wishlist.items))
      .catch((requestError) => setError(requestError instanceof ApiError ? requestError.message : "Không tải được danh sách yêu thích"))
      .finally(() => setLoading(false));
  }, [authLoading, customer]);

  async function remove(item: WishlistItem) {
    if (!customer) return;
    setBusyId(item.product_public_id);
    setError(null);
    try {
      await removeWishlistProduct(item.product_public_id);
      setItems((previous) => previous.filter((current) => current.product_public_id !== item.product_public_id));
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Không xóa được sản phẩm yêu thích");
    } finally {
      setBusyId(null);
    }
  }

  if (authLoading || loading) {
    return <main className="page-shell"><div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{[0, 1, 2].map((item) => <div className="aspect-[4/5] animate-pulse rounded-3xl bg-sand/60" key={item} />)}</div></main>;
  }

  if (!customer) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-14 text-center sm:px-6">
        <section className="surface-card p-8 sm:p-12">
          <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10 text-accent"><Icon name="heart" size={25} /></span>
          <h1 className="mt-6 font-serif text-4xl">Danh sách yêu thích</h1>
          <p className="mt-3 text-muted">Đăng nhập để lưu lại những thiết kế bạn muốn xem sau.</p>
          <Link className="button-primary mt-7" href="/login?returnTo=%2Fwishlist">Đăng nhập</Link>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="eyebrow">Saved pieces</p><h1 className="page-heading mt-3">Sản phẩm yêu thích</h1><p className="mt-3 text-muted">Những lựa chọn bạn đã lưu cho lần mua sắm tiếp theo.</p></div>
        <p className="text-sm font-semibold text-muted">{items.length} sản phẩm</p>
      </header>
      {error ? <div className="feedback-error mt-6">{error}</div> : null}

      {items.length === 0 ? (
        <section className="surface-card mt-9 p-10 text-center sm:p-14">
          <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-paper text-moss"><Icon name="heart" size={24} /></span>
          <h2 className="mt-5 text-xl font-semibold">Chưa có sản phẩm được lưu</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">Chạm biểu tượng trái tim ở sản phẩm bạn yêu thích để tìm lại nhanh hơn.</p>
          <Link className="button-primary mt-6" href="/products">Khám phá sản phẩm <Icon name="arrow-right" size={17} /></Link>
        </section>
      ) : (
        <div className="mt-9 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <article key={item.product_public_id} className="group overflow-hidden rounded-3xl border border-line bg-surface shadow-sm transition hover:-translate-y-1 hover:shadow-soft">
              <Link href={`/products/${item.slug}`}>
                <div className="relative aspect-[4/5] overflow-hidden bg-sand/50">
                  {item.image_url ? (
                    <Image
                      alt={item.name}
                      className="object-cover transition duration-300 group-hover:scale-[1.025]"
                      fill
                      sizes="(min-width: 1024px) 30vw, (min-width: 640px) 45vw, 100vw"
                      src={item.image_url}
                    />
                  ) : <span className="flex h-full items-center justify-center text-muted">Chưa có ảnh</span>}
                </div>
                <div className="p-5">
                  <h2 className="font-serif text-xl">{item.name}</h2>
                  <p className="mt-2 font-semibold">{formatVnd(item.min_price_vnd)}</p>
                  {!item.is_available ? <p className="mt-3 text-xs font-semibold text-danger">Sản phẩm ngừng bán</p> : item.in_stock ? <p className="mt-3 text-xs font-semibold text-success">Sẵn hàng</p> : <p className="mt-3 text-xs font-semibold text-danger">Tạm hết hàng</p>}
                </div>
              </Link>
              <div className="border-t border-line p-3">
                <button className="button-ghost w-full text-danger hover:bg-danger/5 hover:text-danger" disabled={busyId === item.product_public_id} onClick={() => void remove(item)} type="button">
                  <Icon name="trash" size={17} />
                  {busyId === item.product_public_id ? "Đang xóa…" : "Xóa khỏi yêu thích"}
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}

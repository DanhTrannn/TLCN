"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  ApiError,
  formatVnd,
  getWishlist,
  removeWishlistProduct,
  type WishlistItem,
} from "@/lib/api";
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
      .catch((requestError) => {
        setError(
          requestError instanceof ApiError
            ? requestError.message
            : "Không tải được danh sách yêu thích"
        );
      })
      .finally(() => setLoading(false));
  }, [authLoading, customer]);

  async function remove(item: WishlistItem) {
    if (!customer) return;
    setBusyId(item.product_public_id);
    setError(null);
    try {
      await removeWishlistProduct(item.product_public_id);
      setItems((previous) =>
        previous.filter((current) => current.product_public_id !== item.product_public_id)
      );
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không xóa được sản phẩm yêu thích"
      );
    } finally {
      setBusyId(null);
    }
  }

  if (authLoading || loading) {
    return <main className="mx-auto max-w-6xl px-6 py-14"><p className="text-ink/60">Đang tải…</p></main>;
  }

  if (!customer) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-14 text-center">
        <h1 className="text-3xl font-semibold">Danh sách yêu thích</h1>
        <p className="mt-4 text-ink/60">Bạn cần đăng nhập để lưu sản phẩm yêu thích.</p>
        <Link className="mt-6 inline-block rounded-full bg-ink px-6 py-3 text-paper" href="/login?returnTo=%2Fwishlist">Đăng nhập</Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-14">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-accent">Wishlist</p>
      <h1 className="mt-3 text-4xl font-semibold">Sản phẩm yêu thích</h1>
      {error ? <p className="mt-6 text-sm text-accent">{error}</p> : null}
      {items.length === 0 ? (
        <div className="mt-10 rounded-3xl border border-ink/10 bg-white/60 p-10 text-center">
          <p className="text-ink/60">Danh sách yêu thích đang trống.</p>
          <Link className="mt-5 inline-block rounded-full bg-ink px-6 py-2 text-sm text-paper" href="/products">Khám phá sản phẩm</Link>
        </div>
      ) : (
        <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <article key={item.product_public_id} className="rounded-3xl border border-ink/10 bg-white/60 p-5">
              <Link href={`/products/${item.slug}`}>
                <div className="aspect-square overflow-hidden rounded-2xl bg-ink/5">
                  {item.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={item.image_url} alt={item.name} className="h-full w-full object-cover" />
                  ) : null}
                </div>
                <h2 className="mt-4 font-medium">{item.name}</h2>
                <p className="mt-1 text-sm text-ink/60">{formatVnd(item.min_price_vnd)}</p>
                {!item.is_available ? <p className="mt-1 text-xs text-accent">Sản phẩm ngừng bán</p> : item.in_stock ? null : <p className="mt-1 text-xs text-accent">Tạm hết hàng</p>}
              </Link>
              <button className="mt-4 w-full rounded-full border border-ink/20 px-4 py-2 text-sm disabled:opacity-50" disabled={busyId === item.product_public_id} onClick={() => void remove(item)} type="button">
                {busyId === item.product_public_id ? "Đang xóa…" : "Xóa khỏi yêu thích"}
              </button>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}

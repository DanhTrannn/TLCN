"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ProductReviews } from "@/components/ProductReviews";
import { Icon } from "@/components/ui/Icon";
import {
  ApiError,
  addWishlistProduct,
  formatVnd,
  getProduct,
  getWishlist,
  removeWishlistProduct,
  setCartItem,
  type ProductDetail,
  type Variant,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function ProductDetailPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;
  const router = useRouter();
  const { customer } = useAuth();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<string | null>(null);
  const [wishlisted, setWishlisted] = useState(false);
  const [wishlistBusy, setWishlistBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    if (!slug) return;
    getProduct(slug)
      .then((loadedProduct) => {
        setProduct(loadedProduct);
        const firstSellable = loadedProduct.variants.find((variant) => variant.in_stock) ?? loadedProduct.variants[0];
        setSelectedVariant(firstSellable?.public_id ?? null);
      })
      .catch(() => setError("Không tìm thấy sản phẩm"));
  }, [slug]);

  useEffect(() => {
    if (!customer || !product) {
      setWishlisted(false);
      return;
    }
    getWishlist()
      .then((wishlist) => setWishlisted(wishlist.items.some((item) => item.product_public_id === product.public_id)))
      .catch(() => undefined);
  }, [customer, product]);

  const variant: Variant | undefined = useMemo(
    () => product?.variants.find((item) => item.public_id === selectedVariant),
    [product, selectedVariant]
  );

  async function handleAddToCart() {
    if (!variant) return;
    if (!customer) {
      router.push(`/login?returnTo=${encodeURIComponent(`/products/${slug}`)}`);
      return;
    }
    setAdding(true);
    setMessage(null);
    setError(null);
    try {
      await setCartItem(variant.public_id, 1);
      setMessage("Sản phẩm đã được thêm vào giỏ hàng.");
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Không thêm được vào giỏ");
    } finally {
      setAdding(false);
    }
  }

  async function handleWishlist() {
    if (!product) return;
    if (!customer) {
      router.push(`/login?returnTo=${encodeURIComponent(`/products/${slug}`)}`);
      return;
    }
    setWishlistBusy(true);
    setError(null);
    try {
      if (wishlisted) {
        await removeWishlistProduct(product.public_id);
        setWishlisted(false);
      } else {
        await addWishlistProduct(product.public_id);
        setWishlisted(true);
      }
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Không cập nhật được danh sách yêu thích");
    } finally {
      setWishlistBusy(false);
    }
  }

  if (error && !product) {
    return <main className="page-shell"><div className="feedback-error">{error}</div></main>;
  }

  if (!product) {
    return <main className="page-shell"><div className="grid gap-7 md:grid-cols-2"><div className="aspect-[4/5] animate-pulse rounded-3xl bg-sand/60" /><div className="h-80 animate-pulse rounded-3xl bg-sand/50" /></div></main>;
  }

  return (
    <main className="page-shell">
      <nav aria-label="Breadcrumb" className="mb-6 flex items-center gap-2 text-sm text-muted">
        <Link className="min-h-11 content-center hover:text-accent" href="/products">Sản phẩm</Link>
        <Icon name="chevron-right" size={15} />
        <span className="truncate text-ink">{product.name}</span>
      </nav>

      <div className="grid gap-8 lg:grid-cols-[1.08fr_0.92fr] lg:gap-12">
        <section className="overflow-hidden rounded-[2rem] border border-line bg-surface p-3 shadow-soft" aria-label="Ảnh sản phẩm">
          <div className="relative aspect-[4/5] overflow-hidden rounded-[1.5rem] bg-sand/50">
            {product.image_url ? (
              <Image
                alt={product.name}
                className="object-cover"
                fill
                priority
                sizes="(min-width: 1024px) 52vw, 100vw"
                src={product.image_url}
              />
            ) : (
              <span className="flex h-full items-center justify-center text-muted">Sản phẩm chưa có ảnh</span>
            )}
          </div>
        </section>

        <section className="lg:py-3">
          <p className="eyebrow">{product.category_name}</p>
          <div className="mt-3 flex items-start justify-between gap-4">
            <h1 className="font-serif text-4xl leading-tight tracking-[-0.04em] sm:text-5xl">{product.name}</h1>
            <button
              aria-label={wishlisted ? "Xóa khỏi yêu thích" : "Thêm vào yêu thích"}
              className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full border bg-surface shadow-sm transition ${wishlisted ? "border-accent/30 text-accent" : "border-line text-muted hover:text-accent"}`}
              disabled={wishlistBusy}
              onClick={() => void handleWishlist()}
              type="button"
            >
              <Icon filled={wishlisted} name="heart" size={21} />
            </button>
          </div>
          <p className="mt-5 text-2xl font-semibold text-ink">{formatVnd(variant?.price_vnd ?? null)}</p>
          {product.description ? <p className="mt-5 leading-7 text-muted">{product.description}</p> : null}

          <div className="mt-8 border-t border-line pt-7">
            <div className="flex items-center justify-between gap-4">
              <h2 className="font-semibold">Chọn phiên bản</h2>
              <span className={`text-xs font-semibold ${variant?.in_stock ? "text-success" : "text-danger"}`}>
                {variant?.in_stock ? `Còn ${variant.stock_quantity} sản phẩm` : "Hết hàng"}
              </span>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
              {product.variants.map((item) => {
                const selected = item.public_id === selectedVariant;
                return (
                  <button
                    aria-pressed={selected}
                    key={item.public_id}
                    className={`min-h-12 rounded-xl border px-3 py-2 text-sm font-semibold transition ${selected ? "border-ink bg-ink text-paper shadow-sm" : "border-line bg-surface text-ink hover:border-ink/35"} ${item.in_stock ? "" : "opacity-50"}`}
                    onClick={() => setSelectedVariant(item.public_id)}
                    type="button"
                  >
                    {item.size_code} · {item.color_code}
                    <span className="mt-0.5 block text-[11px] font-normal">
                      {item.in_stock ? `Còn ${item.stock_quantity}` : "Tạm hết"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <button className="button-accent mt-7 w-full" disabled={adding || !variant || !variant.in_stock} onClick={() => void handleAddToCart()} type="button">
            <Icon name="bag" size={19} />
            {variant?.in_stock ? (adding ? "Đang thêm…" : "Thêm vào giỏ hàng") : "Phiên bản đã hết hàng"}
          </button>

          <div aria-live="polite" className="mt-4 space-y-3">
            {message ? <p className="feedback-success flex items-center gap-2"><Icon name="check" size={18} />{message}</p> : null}
            {error ? <p className="feedback-error">{error}</p> : null}
          </div>

          <div className="mt-7 grid gap-3 border-t border-line pt-6 sm:grid-cols-2">
            <div className="flex gap-3 rounded-2xl bg-surface p-4 shadow-sm"><Icon className="shrink-0 text-moss" name="truck" /><div><p className="text-sm font-semibold">Giao hàng rõ ràng</p><p className="mt-1 text-xs leading-5 text-muted">Miễn phí từ 500.000₫</p></div></div>
            <div className="flex gap-3 rounded-2xl bg-surface p-4 shadow-sm"><Icon className="shrink-0 text-moss" name="shield" /><div><p className="text-sm font-semibold">Tồn kho thực tế</p><p className="mt-1 text-xs leading-5 text-muted">Kiểm tra lại khi checkout</p></div></div>
          </div>
        </section>
      </div>

      <ProductReviews slug={product.slug} />
    </main>
  );
}

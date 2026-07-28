"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

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
        const firstSellable =
          loadedProduct.variants.find((variant) => variant.in_stock) ?? loadedProduct.variants[0];
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
      .then((wishlist) => {
        setWishlisted(
          wishlist.items.some((item) => item.product_public_id === product.public_id)
        );
      })
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
      setMessage("Đã thêm vào giỏ hàng");
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
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không cập nhật được danh sách yêu thích"
      );
    } finally {
      setWishlistBusy(false);
    }
  }

  if (error && !product) {
    return <main className="mx-auto max-w-4xl px-6 py-14"><p className="text-accent">{error}</p></main>;
  }

  if (!product) {
    return <main className="mx-auto max-w-4xl px-6 py-14"><p className="text-ink/60">Đang tải…</p></main>;
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-14">
      <div className="grid grid-cols-1 gap-10 md:grid-cols-2">
        <div className="aspect-square overflow-hidden rounded-3xl bg-ink/5">
          {product.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={product.image_url} alt={product.name} className="h-full w-full object-cover" />
          ) : null}
        </div>
        <div>
          <p className="text-sm uppercase tracking-widest text-ink/50">{product.category_name}</p>
          <div className="mt-2 flex items-start justify-between gap-4">
            <h1 className="text-3xl font-semibold">{product.name}</h1>
            <button
              aria-label={wishlisted ? "Xóa khỏi yêu thích" : "Thêm vào yêu thích"}
              className={`grid h-11 w-11 shrink-0 place-items-center rounded-full border text-2xl ${wishlisted ? "border-accent text-accent" : "border-ink/20"}`}
              disabled={wishlistBusy}
              onClick={() => void handleWishlist()}
              type="button"
            >
              {wishlisted ? "♥" : "♡"}
            </button>
          </div>
          <p className="mt-3 text-2xl">{formatVnd(variant?.price_vnd ?? null)}</p>
          {product.description ? <p className="mt-4 text-ink/70">{product.description}</p> : null}

          <div className="mt-6 space-y-2">
            <p className="text-sm font-medium">Phiên bản</p>
            <div className="flex flex-wrap gap-2">
              {product.variants.map((item) => (
                <button
                  key={item.public_id}
                  className={`rounded-lg border px-3 py-2 text-sm ${item.public_id === selectedVariant ? "border-ink bg-ink text-paper" : "border-ink/20"} ${item.in_stock ? "" : "opacity-50"}`}
                  onClick={() => setSelectedVariant(item.public_id)}
                  type="button"
                >
                  {item.size_code} / {item.color_code}{item.in_stock ? "" : " (hết)"}
                </button>
              ))}
            </div>
          </div>

          <button className="mt-8 w-full rounded-full bg-accent px-6 py-3 text-paper disabled:opacity-60" disabled={adding || !variant || !variant.in_stock} onClick={() => void handleAddToCart()} type="button">
            {variant?.in_stock ? (adding ? "Đang thêm…" : "Thêm vào giỏ") : "Hết hàng"}
          </button>

          {message ? <p className="mt-3 text-sm text-moss">{message}</p> : null}
          {error ? <p className="mt-3 text-sm text-accent">{error}</p> : null}
        </div>
      </div>
    </main>
  );
}

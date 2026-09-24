"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { formatVnd, getProduct, getProducts, type CartItem, type ProductListItem } from "@/lib/api";

interface CartCrossSellProps {
  cartItems: CartItem[];
  onAddToCart: (variantPublicId: string) => Promise<void>;
}

export function CartCrossSell({ cartItems, onAddToCart }: CartCrossSellProps) {
  const [suggestions, setSuggestions] = useState<ProductListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [addingSlug, setAddingSlug] = useState<string | null>(null);
  const [quickSizeMenu, setQuickSizeMenu] = useState<{
    slug: string;
    variants: Array<{ public_id: string; size_code: string; color_code: string; in_stock: boolean }>;
  } | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);

    getProducts({ inStock: true })
      .then((res) => {
        if (!active) return;
        const cartSlugs = new Set(cartItems.map((c) => c.slug));
        const filtered = res.items.filter((item) => !cartSlugs.has(item.slug));
        setSuggestions(filtered.slice(0, 4));
      })
      .catch(() => {
        if (active) setSuggestions([]);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [cartItems]);

  if (loading) {
    return (
      <div className="mt-8 rounded-2xl border border-line bg-paper/60 p-5">
        <div className="h-5 w-48 animate-pulse rounded bg-line mb-4" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="space-y-2">
              <div className="aspect-[4/5] w-full animate-pulse rounded-xl bg-line" />
              <div className="h-3 w-3/4 animate-pulse rounded bg-line" />
              <div className="h-3 w-1/2 animate-pulse rounded bg-line" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (suggestions.length === 0) return null;

  async function handleQuickAdd(item: ProductListItem) {
    setAddingSlug(item.slug);
    try {
      const detail = await getProduct(item.slug);
      const available = detail.variants.filter((v) => v.in_stock && v.stock_quantity > 0);
      if (available.length === 0) return;

      if (available.length === 1) {
        await onAddToCart(available[0].public_id);
      } else {
        // Show quick size picker
        setQuickSizeMenu({
          slug: item.slug,
          variants: available.map((v) => ({
            public_id: v.public_id,
            size_code: v.size_code,
            color_code: v.color_code,
            in_stock: v.in_stock,
          })),
        });
      }
    } finally {
      setAddingSlug(null);
    }
  }

  async function handleSelectVariant(variantPublicId: string) {
    setAddingSlug(quickSizeMenu?.slug ?? null);
    try {
      await onAddToCart(variantPublicId);
      setQuickSizeMenu(null);
    } finally {
      setAddingSlug(null);
    }
  }

  return (
    <section
      aria-label="Gợi ý phối đồ mua kèm"
      className="mt-8 rounded-2xl border border-line bg-paper/90 p-5 sm:p-6 shadow-sm"
    >
      <div className="flex items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent/10 text-accent">
              <Icon name="sparkles" size={13} />
            </span>
            <h3 className="font-semibold text-sm sm:text-base text-ink">
              Hoàn thiện phong cách (Complete the Look)
            </h3>
          </div>
          <p className="mt-0.5 text-xs text-muted">
            Những món đồ phối chuẩn form được các tín đồ D&K ưa chuộng
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        {suggestions.map((item) => {
          const isAdding = addingSlug === item.slug;
          const isPickingSize = quickSizeMenu?.slug === item.slug;

          return (
            <div
              key={item.public_id}
              className="group relative flex flex-col justify-between rounded-xl border border-line bg-paper p-2.5 transition hover:border-accent/40 hover:shadow-md"
            >
              <div>
                <Link className="block overflow-hidden rounded-lg" href={`/products/${item.slug}`}>
                  <div className="aspect-[4/5] w-full overflow-hidden bg-surface">
                    {item.image_url ? (
                      <img
                        alt={item.name}
                        className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                        src={item.image_url}
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-xs text-muted">
                        Chưa có ảnh
                      </div>
                    )}
                  </div>
                </Link>

                <h4 className="mt-2 text-xs font-semibold text-ink line-clamp-1 group-hover:text-accent transition">
                  <Link href={`/products/${item.slug}`}>{item.name}</Link>
                </h4>
                <p className="mt-0.5 text-xs font-medium text-ink">
                  {item.min_price_vnd ? formatVnd(item.min_price_vnd) : "Liên hệ"}
                </p>
              </div>

              {/* Action Button / Size Picker */}
              <div className="mt-2.5 pt-2 border-t border-line/60">
                {isPickingSize && quickSizeMenu ? (
                  <div className="space-y-1.5 animate-fade-in">
                    <div className="flex items-center justify-between text-[11px] font-semibold text-muted">
                      <span>Chọn Size:</span>
                      <button
                        className="text-muted hover:text-ink"
                        onClick={() => setQuickSizeMenu(null)}
                        type="button"
                      >
                        <Icon name="close" size={11} />
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {quickSizeMenu.variants.map((v) => (
                        <button
                          key={v.public_id}
                          className="flex-1 min-w-[32px] rounded border border-line bg-paper py-1 text-[10px] font-semibold text-ink hover:border-accent hover:bg-accent hover:text-paper transition"
                          onClick={() => void handleSelectVariant(v.public_id)}
                          type="button"
                        >
                          {v.size_code}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <button
                    className="w-full flex items-center justify-center gap-1.5 rounded-lg border border-line bg-paper py-1.5 text-xs font-semibold text-ink hover:border-accent hover:bg-accent hover:text-paper transition disabled:opacity-40"
                    disabled={isAdding}
                    onClick={() => void handleQuickAdd(item)}
                    type="button"
                  >
                    {isAdding ? (
                      <span className="h-3 w-3 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                    ) : (
                      <>
                        <Icon name="plus" size={13} />
                        <span>Thêm nhanh</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

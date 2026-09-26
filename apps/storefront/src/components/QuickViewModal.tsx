"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd, getProduct, type ProductDetail, type Variant } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useCartDrawer } from "@/lib/cart-context";
import { getColorMeta } from "@/lib/colors";

interface QuickViewModalProps {
  slug: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export function QuickViewModal({ slug, isOpen, onClose }: QuickViewModalProps) {
  const router = useRouter();
  const { customer } = useAuth();
  const { addItemAndOpen } = useCartDrawer();

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Close on Escape & prevent scroll
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  // Fetch product detail on slug change
  useEffect(() => {
    if (!isOpen || !slug) {
      setProduct(null);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    setQuantity(1);

    getProduct(slug)
      .then((data) => {
        setProduct(data);
        // Default to first in-stock variant or first variant
        const firstInStock = data.variants.find((v) => v.in_stock) || data.variants[0];
        if (firstInStock) {
          setSelectedColor(firstInStock.color_code);
          setSelectedSize(firstInStock.size_code);
        }
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Không tải được thông tin sản phẩm");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [isOpen, slug]);

  // Distinct colors
  const availableColors = useMemo(() => {
    if (!product) return [];
    return Array.from(new Set(product.variants.map((v) => v.color_code)));
  }, [product]);

  // Distinct sizes for the currently selected color
  const sizesForColor = useMemo(() => {
    if (!product) return [];
    const sizes = Array.from(new Set(product.variants.map((v) => v.size_code)));
    return sizes.map((size) => {
      const match = product.variants.find(
        (v) => v.color_code === selectedColor && v.size_code === size
      );
      return {
        size,
        inStock: match ? match.in_stock && match.stock_quantity > 0 : false,
        stockQuantity: match ? match.stock_quantity : 0,
      };
    });
  }, [product, selectedColor]);

  // Active resolved variant
  const currentVariant: Variant | undefined = useMemo(() => {
    if (!product) return undefined;
    return product.variants.find(
      (v) => v.color_code === selectedColor && v.size_code === selectedSize
    );
  }, [product, selectedColor, selectedSize]);

  // If selected size is not in stock for new color, auto-select first available size
  useEffect(() => {
    if (!selectedColor || sizesForColor.length === 0) return;
    const currentSizeAvailable = sizesForColor.some(
      (s) => s.size === selectedSize && s.inStock
    );
    if (!currentSizeAvailable) {
      const firstInStockSize = sizesForColor.find((s) => s.inStock);
      if (firstInStockSize) {
        setSelectedSize(firstInStockSize.size);
      }
    }
  }, [selectedColor, sizesForColor, selectedSize]);

  // Add to cart handler
  async function handleAddToCart() {
    if (!currentVariant) return;
    if (!customer) {
      onClose();
      router.push(`/login?returnTo=${encodeURIComponent(`/products/${slug}`)}`);
      return;
    }
    setAdding(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await addItemAndOpen(currentVariant.public_id, quantity);
      setSuccessMsg("Đã thêm vào giỏ hàng thành công!");
      setTimeout(() => {
        onClose();
      }, 800);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thêm được vào giỏ hàng");
    } finally {
      setAdding(false);
    }
  }

  if (!isOpen) return null;

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      role="dialog"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-ink/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-3xl overflow-hidden rounded-3xl border border-line bg-surface p-6 shadow-lift sm:p-8">
        <button
          aria-label="Đóng xem nhanh"
          className="absolute right-4 top-4 z-10 flex h-10 w-10 items-center justify-center rounded-full border border-line bg-paper/90 text-muted transition hover:bg-surface hover:text-ink shadow-2xs"
          onClick={onClose}
          type="button"
        >
          <Icon name="close" size={17} />
        </button>

        {loading ? (
          <div className="grid gap-6 sm:grid-cols-2">
            <div className="aspect-[4/5] animate-pulse rounded-2xl bg-sand/60" />
            <div className="space-y-4 py-2">
              <div className="h-4 w-24 animate-pulse rounded bg-sand/80" />
              <div className="h-8 w-3/4 animate-pulse rounded bg-sand/80" />
              <div className="h-6 w-1/3 animate-pulse rounded bg-sand/60" />
              <div className="h-20 animate-pulse rounded bg-sand/50" />
              <div className="h-12 animate-pulse rounded-xl bg-sand/70" />
            </div>
          </div>
        ) : error && !product ? (
          <div className="feedback-error my-8 text-center">{error}</div>
        ) : product ? (
          <div className="grid gap-6 sm:grid-cols-2 sm:gap-8">
            {/* Image Preview */}
            <div className="relative aspect-[4/5] overflow-hidden rounded-2xl bg-sand/40 border border-line/60">
              {product.image_url ? (
                <Image
                  alt={product.name}
                  className="object-cover"
                  fill
                  priority
                  sizes="(min-width: 640px) 400px, 100vw"
                  src={product.image_url}
                />
              ) : (
                <span className="flex h-full items-center justify-center text-sm text-muted">
                  Chưa có ảnh
                </span>
              )}
              <span
                className={`absolute left-3 top-3 inline-flex rounded-full px-3 py-1 text-xs font-semibold backdrop-blur-md shadow-2xs ${
                  currentVariant?.in_stock
                    ? "bg-emerald-950/80 text-emerald-300 border border-emerald-500/20"
                    : "bg-rose-950/80 text-rose-300 border border-rose-500/20"
                }`}
              >
                {currentVariant?.in_stock ? "Sẵn hàng" : "Hết hàng"}
              </span>
            </div>

            {/* Product Details & Actions */}
            <div className="flex flex-col justify-between py-1">
              <div>
                <p className="eyebrow">{product.category_name}</p>
                <h2 className="mt-1 font-serif text-2xl sm:text-3xl text-ink leading-tight">
                  {product.name}
                </h2>
                <p className="mt-2 text-xl font-semibold text-ink">
                  {formatVnd(currentVariant?.price_vnd ?? product.variants[0]?.price_vnd ?? 0)}
                </p>

                {/* Color Swatches */}
                {availableColors.length > 0 && (
                  <div className="mt-5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-ink">
                        Màu sắc:{" "}
                        <span className="font-normal text-muted">
                          {getColorMeta(selectedColor).label}
                        </span>
                      </span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2.5">
                      {availableColors.map((color) => {
                        const meta = getColorMeta(color);
                        const isSelected = selectedColor === color;
                        return (
                          <button
                            aria-label={`Màu ${meta.label}`}
                            className={`group relative flex h-8 w-8 items-center justify-center rounded-full border transition ${
                              isSelected
                                ? "ring-2 ring-accent ring-offset-2 border-transparent scale-105"
                                : "border-line hover:scale-105"
                            }`}
                            key={color}
                            onClick={() => setSelectedColor(color)}
                            style={{ backgroundColor: meta.hex }}
                            title={meta.label}
                            type="button"
                          >
                            {isSelected && (
                              <Icon
                                className={meta.isLight ? "text-ink" : "text-white"}
                                name="check"
                                size={13}
                              />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Size Pills */}
                {sizesForColor.length > 0 && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-ink">Kích cỡ</span>
                      {currentVariant && (
                        <span className="text-muted">
                          {currentVariant.in_stock
                            ? `Còn ${currentVariant.stock_quantity} sản phẩm`
                            : "Tạm hết hàng"}
                        </span>
                      )}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {sizesForColor.map(({ size, inStock }) => {
                        const isSelected = selectedSize === size;
                        return (
                          <button
                            aria-pressed={isSelected}
                            className={`min-h-10 min-w-11 rounded-xl border px-3 text-xs font-semibold transition ${
                              isSelected
                                ? "border-ink bg-ink text-paper shadow-2xs"
                                : inStock
                                ? "border-line bg-surface text-ink hover:border-ink/40"
                                : "border-line/60 bg-paper/50 text-muted/40 cursor-not-allowed line-through"
                            }`}
                            disabled={!inStock}
                            key={size}
                            onClick={() => setSelectedSize(size)}
                            type="button"
                          >
                            {size}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Quantity Stepper */}
                <div className="mt-5 flex items-center gap-4">
                  <span className="text-xs font-semibold text-ink">Số lượng:</span>
                  <div className="flex items-center rounded-xl border border-line bg-paper">
                    <button
                      aria-label="Giảm số lượng"
                      className="flex h-9 w-9 items-center justify-center text-muted transition hover:text-ink disabled:opacity-30"
                      disabled={quantity <= 1}
                      onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                      type="button"
                    >
                      <Icon name="minus" size={14} />
                    </button>
                    <span className="w-8 text-center text-sm font-semibold text-ink">
                      {quantity}
                    </span>
                    <button
                      aria-label="Tăng số lượng"
                      className="flex h-9 w-9 items-center justify-center text-muted transition hover:text-ink disabled:opacity-30"
                      disabled={
                        quantity >= (currentVariant?.stock_quantity ?? 1) ||
                        !currentVariant?.in_stock
                      }
                      onClick={() =>
                        setQuantity((q) =>
                          Math.min(currentVariant?.stock_quantity ?? 1, q + 1)
                        )
                      }
                      type="button"
                    >
                      <Icon name="plus" size={14} />
                    </button>
                  </div>
                </div>

                {error && <p className="feedback-error mt-3 text-xs">{error}</p>}
                {successMsg && (
                  <p className="feedback-success mt-3 text-xs flex items-center gap-1.5">
                    <Icon name="check" size={14} />
                    {successMsg}
                  </p>
                )}
              </div>

              {/* Action Buttons */}
              <div className="mt-6 pt-4 border-t border-line space-y-2.5">
                <button
                  className="button-accent w-full"
                  disabled={adding || !currentVariant || !currentVariant.in_stock}
                  onClick={() => void handleAddToCart()}
                  type="button"
                >
                  <Icon name="bag" size={18} />
                  {currentVariant?.in_stock
                    ? adding
                      ? "Đang thêm vào giỏ…"
                      : "Thêm vào giỏ hàng"
                    : "Phiên bản đã hết hàng"}
                </button>

                <div className="text-center">
                  <Link
                    className="inline-flex items-center gap-1 text-xs font-semibold text-accent hover:underline py-1"
                    href={`/products/${product.slug}`}
                    onClick={onClose}
                  >
                    Xem chi tiết sản phẩm đầy đủ
                    <Icon name="arrow-right" size={13} />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { formatVnd, getProduct, type CartItem, type ProductDetail, type Variant } from "@/lib/api";

interface VariantSwitcherModalProps {
  isOpen: boolean;
  item: CartItem | null;
  onClose: () => void;
  onSwitchVariant: (item: CartItem, newVariant: Variant) => Promise<void>;
}

export function VariantSwitcherModal({
  isOpen,
  item,
  onClose,
  onSwitchVariant,
}: VariantSwitcherModalProps) {
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string>("");
  const [selectedColor, setSelectedColor] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen || !item) {
      setProduct(null);
      return;
    }

    setSelectedSize(item.size_code);
    setSelectedColor(item.color_code);
    setLoading(true);
    setError(null);

    let active = true;
    getProduct(item.slug)
      .then((detail) => {
        if (!active) return;
        setProduct(detail);
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Không tải được danh sách phân loại");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [isOpen, item]);

  useEffect(() => {
    if (!isOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [isOpen, onClose]);

  const uniqueSizes = useMemo(() => {
    if (!product) return [];
    return Array.from(new Set(product.variants.map((v) => v.size_code)));
  }, [product]);

  const uniqueColors = useMemo(() => {
    if (!product) return [];
    return Array.from(new Set(product.variants.map((v) => v.color_code)));
  }, [product]);

  const matchedVariant = useMemo(() => {
    if (!product || !selectedSize || !selectedColor) return null;
    return (
      product.variants.find(
        (v) => v.size_code === selectedSize && v.color_code === selectedColor
      ) ?? null
    );
  }, [product, selectedSize, selectedColor]);

  if (!isOpen || !item) return null;

  const isCurrentVariant = matchedVariant?.public_id === item.variant_public_id;
  const canConfirm =
    matchedVariant !== null &&
    !isCurrentVariant &&
    matchedVariant.in_stock &&
    matchedVariant.stock_quantity > 0;

  async function handleConfirm() {
    if (!matchedVariant || !item || !canConfirm) return;
    setSubmitting(true);
    try {
      await onSwitchVariant(item, matchedVariant);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đổi phân loại thất bại");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/40 backdrop-blur-sm animate-fade-in"
      role="dialog"
    >
      <div
        ref={panelRef}
        className="w-full max-w-md rounded-2xl border border-line bg-paper p-5 sm:p-6 shadow-2xl transition-all"
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 border-b border-line pb-4">
          <div className="flex items-center gap-3">
            {item.image_url ? (
              <img
                alt={item.product_name}
                className="h-14 w-11 rounded-lg border border-line object-cover"
                src={item.image_url}
              />
            ) : null}
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-muted">
                Đổi phân loại sản phẩm
              </p>
              <h3 className="font-semibold text-sm sm:text-base text-ink line-clamp-1">
                {item.product_name}
              </h3>
              <p className="text-xs text-muted">
                Hiện tại: Size {item.size_code} / Màu {item.color_code}
              </p>
            </div>
          </div>
          <button
            aria-label="Đóng"
            className="flex h-8 w-8 items-center justify-center rounded-full text-muted hover:bg-surface hover:text-ink transition"
            onClick={onClose}
            type="button"
          >
            <Icon name="close" size={16} />
          </button>
        </div>

        {/* Content */}
        <div className="py-4 space-y-4">
          {loading ? (
            <div className="py-8 text-center text-xs text-muted">
              <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-line border-t-accent mb-2" />
              <p>Đang tải danh sách phân loại...</p>
            </div>
          ) : error ? (
            <div className="rounded-xl bg-danger/10 p-3 text-xs text-danger">{error}</div>
          ) : product ? (
            <>
              {/* Size Selector */}
              <div>
                <label className="block text-xs font-semibold text-ink mb-2">Chọn Size:</label>
                <div className="flex flex-wrap gap-2">
                  {uniqueSizes.map((size) => {
                    const isSelected = size === selectedSize;
                    // check if this size has any in-stock variant with selected color or in general
                    const hasStock = product.variants.some(
                      (v) => v.size_code === size && v.in_stock && v.stock_quantity > 0
                    );

                    return (
                      <button
                        key={size}
                        className={`min-w-[42px] px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                          isSelected
                            ? "border-accent bg-accent text-paper shadow-sm"
                            : hasStock
                            ? "border-line bg-paper text-ink hover:border-accent/40"
                            : "border-line/40 bg-surface/50 text-muted line-through opacity-60"
                        }`}
                        disabled={!hasStock}
                        onClick={() => setSelectedSize(size)}
                        type="button"
                      >
                        {size}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Color Selector */}
              <div>
                <label className="block text-xs font-semibold text-ink mb-2">Chọn Màu sắc:</label>
                <div className="flex flex-wrap gap-2">
                  {uniqueColors.map((color) => {
                    const isSelected = color === selectedColor;
                    const hasStock = product.variants.some(
                      (v) =>
                        v.color_code === color &&
                        v.size_code === selectedSize &&
                        v.in_stock &&
                        v.stock_quantity > 0
                    );

                    return (
                      <button
                        key={color}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                          isSelected
                            ? "border-accent bg-accent text-paper shadow-sm"
                            : hasStock
                            ? "border-line bg-paper text-ink hover:border-accent/40"
                            : "border-line/40 bg-surface/50 text-muted line-through opacity-60"
                        }`}
                        onClick={() => setSelectedColor(color)}
                        type="button"
                      >
                        {color}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Matched Variant Preview */}
              <div className="rounded-xl border border-line bg-surface/50 p-3 text-xs flex items-center justify-between">
                <div>
                  <span className="font-semibold text-ink">
                    {selectedSize} / {selectedColor}
                  </span>
                  <p className="text-muted">SKU: {matchedVariant?.sku ?? "N/A"}</p>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-ink">
                    {matchedVariant ? formatVnd(matchedVariant.price_vnd) : "---"}
                  </div>
                  {isCurrentVariant ? (
                    <span className="text-[11px] font-medium text-muted">Đang trong giỏ</span>
                  ) : matchedVariant?.in_stock && matchedVariant.stock_quantity > 0 ? (
                    <span className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                      Còn hàng ({matchedVariant.stock_quantity})
                    </span>
                  ) : (
                    <span className="text-[11px] font-medium text-danger">Hết hàng</span>
                  )}
                </div>
              </div>
            </>
          ) : null}
        </div>

        {/* Footer Actions */}
        <div className="border-t border-line pt-4 flex items-center justify-end gap-2.5">
          <button
            className="rounded-full border border-line px-4 py-2 text-xs font-semibold text-muted hover:border-ink hover:text-ink transition"
            disabled={submitting}
            onClick={onClose}
            type="button"
          >
            Hủy
          </button>
          <button
            className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-2 text-xs font-semibold text-paper shadow-sm hover:opacity-90 transition disabled:opacity-40"
            disabled={!canConfirm || submitting}
            onClick={() => void handleConfirm()}
            type="button"
          >
            {submitting ? (
              <>
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-paper border-t-transparent" />
                Đang đổi...
              </>
            ) : isCurrentVariant ? (
              "Phân loại hiện tại"
            ) : (
              "Xác nhận đổi phân loại"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

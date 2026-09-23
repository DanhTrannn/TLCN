"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

import { FreeShippingBar } from "@/components/FreeShippingBar";
import { Icon } from "@/components/ui/Icon";
import { addWishlistProduct, formatVnd } from "@/lib/api";
import { useCartDrawer } from "@/lib/cart-context";

export function MiniCartDrawer() {
  const {
    isOpen,
    closeDrawer,
    cart,
    itemCount,
    updateItemQuantity,
    removeItem,
  } = useCartDrawer();
  const [busyItem, setBusyItem] = useState<string | null>(null);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        closeDrawer();
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
  }, [isOpen, closeDrawer]);

  if (!isOpen) return null;

  async function handleQtyChange(variantId: string, currentQty: number, delta: number) {
    const nextQty = currentQty + delta;
    setBusyItem(variantId);
    try {
      if (nextQty <= 0) {
        await removeItem(variantId);
      } else {
        await updateItemQuantity(variantId, nextQty);
      }
    } finally {
      setBusyItem(null);
    }
  }

  async function handleRemove(variantId: string) {
    setBusyItem(variantId);
    try {
      await removeItem(variantId);
    } finally {
      setBusyItem(null);
    }
  }

  async function handleMoveToWishlist(item: {
    variant_public_id: string;
    product_public_id?: string | null;
  }) {
    if (!item.product_public_id) {
      await handleRemove(item.variant_public_id);
      return;
    }
    setBusyItem(item.variant_public_id);
    try {
      await addWishlistProduct(item.product_public_id);
      await removeItem(item.variant_public_id);
    } finally {
      setBusyItem(null);
    }
  }

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex justify-end"
      role="dialog"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-ink/50 backdrop-blur-sm transition-opacity duration-300"
        onClick={closeDrawer}
      />

      {/* Drawer Container */}
      <div className="relative flex h-full w-full max-w-md flex-col border-l border-line bg-surface shadow-2xl transition-transform duration-300 sm:max-w-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-line px-5 py-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <Icon name="bag" size={20} />
            <h2 className="font-serif text-xl sm:text-2xl text-ink">Giỏ hàng của bạn</h2>
            <span className="flex h-5 items-center justify-center rounded-full bg-accent/15 px-2 text-xs font-bold text-accent">
              {itemCount}
            </span>
          </div>
          <button
            aria-label="Đóng giỏ hàng"
            className="flex h-9 w-9 items-center justify-center rounded-full border border-line bg-paper text-muted transition hover:bg-surface hover:text-ink"
            onClick={closeDrawer}
            type="button"
          >
            <Icon name="close" size={16} />
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto px-5 py-4 sm:px-6 space-y-4">
          {/* Free Shipping Goal Bar */}
          <FreeShippingBar subtotalVnd={cart?.subtotal_vnd ?? 0} />

          {/* Cart Items List */}
          {!cart || cart.items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <span className="flex h-16 w-16 items-center justify-center rounded-3xl bg-paper text-muted">
                <Icon name="bag" size={32} />
              </span>
              <h3 className="mt-4 font-serif text-lg text-ink">Giỏ hàng đang trống</h3>
              <p className="mt-1 text-sm text-muted max-w-xs">
                Hãy khám phá những trang phục mới nhất của D&K và thêm vào giỏ nhé!
              </p>
              <Link
                className="button-primary mt-5 text-sm"
                href="/products"
                onClick={closeDrawer}
              >
                Khám phá bộ sưu tập
                <Icon name="arrow-right" size={16} />
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-line">
              {cart.items.map((item) => {
                const isItemBusy = busyItem === item.variant_public_id;
                return (
                  <div className="flex gap-4 py-4" key={item.variant_public_id}>
                    {/* Thumbnail */}
                    <div className="relative h-20 w-16 shrink-0 overflow-hidden rounded-xl border border-line bg-paper">
                      {item.image_url ? (
                        <Image
                          alt={item.product_name}
                          className="h-full w-full object-cover"
                          height={80}
                          src={item.image_url}
                          width={64}
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center text-muted">
                          <Icon name="package" size={20} />
                        </div>
                      )}
                    </div>

                    {/* Details */}
                    <div className="flex flex-1 flex-col justify-between">
                      <div>
                        <div className="flex items-start justify-between gap-2">
                          <h4 className="font-semibold text-sm text-ink line-clamp-1">
                            {item.product_name}
                          </h4>
                          <div className="flex items-center gap-1.5 shrink-0">
                            <button
                              aria-label="Lưu vào yêu thích"
                              className="text-muted hover:text-accent transition disabled:opacity-40"
                              disabled={isItemBusy}
                              onClick={() => void handleMoveToWishlist(item)}
                              title="Lưu vào yêu thích"
                              type="button"
                            >
                              <Icon name="heart" size={15} />
                            </button>
                            <button
                              aria-label={`Xóa ${item.product_name}`}
                              className="text-muted hover:text-danger transition disabled:opacity-40"
                              disabled={isItemBusy}
                              onClick={() => void handleRemove(item.variant_public_id)}
                              title="Xóa món này"
                              type="button"
                            >
                              <Icon name="trash" size={15} />
                            </button>
                          </div>
                        </div>
                        <p className="mt-0.5 text-xs text-muted">
                          Phân loại: {item.size_code} / {item.color_code}
                        </p>
                      </div>

                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-sm font-semibold text-accent">
                          {formatVnd(item.line_total_vnd)}
                        </span>

                        {/* Quantity Stepper */}
                        <div className="flex items-center rounded-lg border border-line bg-paper">
                          <button
                            aria-label="Giảm số lượng"
                            className="flex h-7 w-7 items-center justify-center text-xs font-semibold text-muted hover:text-ink disabled:opacity-30"
                            disabled={isItemBusy || item.quantity <= 1}
                            onClick={() =>
                              void handleQtyChange(item.variant_public_id, item.quantity, -1)
                            }
                            type="button"
                          >
                            -
                          </button>
                          <span className="w-7 text-center text-xs font-semibold tabular-nums">
                            {item.quantity}
                          </span>
                          <button
                            aria-label="Tăng số lượng"
                            className="flex h-7 w-7 items-center justify-center text-xs font-semibold text-muted hover:text-ink disabled:opacity-30"
                            disabled={isItemBusy}
                            onClick={() =>
                              void handleQtyChange(item.variant_public_id, item.quantity, 1)
                            }
                            type="button"
                          >
                            +
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer Summary & CTAs */}
        {cart && cart.items.length > 0 ? (
          <div className="border-t border-line bg-paper/50 p-5 sm:p-6 space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted">Tạm tính:</span>
                <span className="font-serif text-xl font-bold text-ink">
                  {formatVnd(cart.subtotal_vnd)}
                </span>
              </div>
              <p className="text-[11px] text-muted">
                Phí vận chuyển và mã giảm giá được áp dụng tại bước thanh toán.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Link
                className="button-secondary justify-center text-xs sm:text-sm px-3"
                href="/cart"
                onClick={closeDrawer}
              >
                Xem giỏ hàng
              </Link>
              <Link
                className="button-primary justify-center text-xs sm:text-sm px-3"
                href="/checkout"
                onClick={closeDrawer}
              >
                Thanh toán
                <Icon name="arrow-right" size={15} />
              </Link>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

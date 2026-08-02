"use client";

import { useEffect, useRef } from "react";

import { Icon } from "@/components/ui/Icon";
import { formatVnd } from "@/lib/api";
import type { AvailableCoupon } from "@/lib/commerce";
import { formatVietnamDateTime } from "@/lib/datetime";

interface CouponPickerModalProps {
  coupons: AvailableCoupon[];
  appliedCode: string | null;
  loading: boolean;
  busy: boolean;
  error: string | null;
  onClose: () => void;
  onRefresh: () => void;
  onSelect: (code: string) => void;
}

function discountLabel(coupon: AvailableCoupon) {
  return coupon.discount_type === "percentage"
    ? `Giảm ${coupon.discount_value}%`
    : `Giảm ${formatVnd(coupon.discount_value)}`;
}

export default function CouponPickerModal({
  coupons,
  appliedCode,
  loading,
  busy,
  error,
  onClose,
  onRefresh,
  onSelect,
}: CouponPickerModalProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [onClose]);


  function keepFocusInside(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key !== "Tab") return;
    const focusable = panelRef.current?.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    if (!focusable || focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return (
    <div
      aria-labelledby="coupon-picker-title"
      aria-modal="true"
      className="fixed inset-0 z-[60] flex items-end justify-center bg-ink/55 p-0 backdrop-blur-sm sm:items-center sm:p-6"
      onClick={onClose}
      role="dialog"
    >
      <div
        className="max-h-[90vh] w-full max-w-xl overflow-hidden rounded-t-3xl border border-line bg-surface shadow-lift sm:rounded-3xl"
        onClick={(event) => event.stopPropagation()}
        onKeyDown={keepFocusInside}
        ref={panelRef}
      >
        <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-5 sm:px-6">
          <div>
            <p className="eyebrow">Ưu đãi phù hợp</p>
            <h2 className="mt-2 font-serif text-3xl" id="coupon-picker-title">Chọn mã giảm giá</h2>
            <p className="mt-2 text-sm text-muted">Chỉ hiển thị coupon áp dụng được cho giỏ hàng hiện tại.</p>
          </div>
          <button
            aria-label="Đóng danh sách mã giảm giá"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-line bg-surface text-muted transition hover:bg-paper hover:text-ink"
            onClick={onClose}
            ref={closeButtonRef}
            type="button"
          >
            <Icon name="close" size={19} />
          </button>
        </div>

        <div className="max-h-[calc(90vh-9rem)] overflow-y-auto p-5 sm:p-6">
          {error ? (
            <div className="feedback-error mb-4">
              <p>{error}</p>
              <button className="mt-2 min-h-11 font-semibold underline underline-offset-4" onClick={onRefresh} type="button">Thử tải lại</button>
            </div>
          ) : null}

          {loading ? (
            <div className="space-y-3" aria-label="Đang tải coupon">{[0, 1, 2].map((item) => <div className="h-36 animate-pulse rounded-2xl bg-sand/60" key={item} />)}</div>
          ) : coupons.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line bg-paper p-8 text-center">
              <Icon className="mx-auto text-moss" name="ticket" size={25} />
              <p className="mt-4 font-semibold">Chưa có mã phù hợp</p>
              <p className="mt-2 text-sm leading-6 text-muted">Giá trị giỏ hàng hoặc giới hạn sử dụng chưa đáp ứng coupon nào.</p>
            </div>
          ) : (
            <ul className="space-y-3">
              {coupons.map((coupon, index) => {
                const selected = appliedCode === coupon.code;
                return (
                  <li className={`overflow-hidden rounded-2xl border bg-surface transition ${selected ? "border-moss ring-2 ring-moss/15" : "border-line hover:border-ink/25"}`} key={coupon.code}>
                    <div className="flex gap-4 p-4 sm:p-5">
                      <div className="flex w-24 shrink-0 flex-col items-center justify-center rounded-xl bg-moss/10 px-2 text-center text-sm font-semibold text-moss">
                        <Icon className="mb-2" name="ticket" size={20} />
                        {discountLabel(coupon)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-semibold tracking-wide">{coupon.code}</p>
                          {index === 0 ? <span className="rounded-full bg-accent/10 px-2.5 py-1 text-xs font-semibold text-accent">Tối ưu nhất</span> : null}
                          {selected ? <span className="rounded-full bg-success/10 px-2.5 py-1 text-xs font-semibold text-success">Đang dùng</span> : null}
                        </div>
                        <p className="mt-2 text-sm text-ink">Tiết kiệm <strong>{formatVnd(coupon.discount_amount_vnd)}</strong></p>
                        <p className="mt-2 text-xs leading-5 text-muted">Đơn tối thiểu {formatVnd(coupon.minimum_subtotal_vnd)}<br />Hết hạn {formatVietnamDateTime(coupon.ends_at)}</p>
                        {coupon.remaining_uses !== null && coupon.remaining_uses <= 20 ? <p className="mt-2 text-xs font-semibold text-danger">Chỉ còn {coupon.remaining_uses} lượt</p> : null}
                      </div>
                    </div>
                    <div className="border-t border-line bg-paper/60 p-3">
                      <button className={selected ? "button-secondary w-full" : "button-primary w-full"} disabled={busy || selected} onClick={() => onSelect(coupon.code)} type="button">
                        {selected ? <Icon name="check" size={17} /> : <Icon name="ticket" size={17} />}
                        {selected ? "Đã áp dụng" : busy ? "Đang áp dụng…" : "Dùng mã này"}
                      </button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

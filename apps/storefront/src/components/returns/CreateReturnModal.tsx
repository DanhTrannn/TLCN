"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd } from "@/lib/api";
import {
  createCustomerReturnRequest,
  type CommerceOrderDetail,
  type CommerceOrderItem,
  type CreateReturnRequestInput,
} from "@/lib/commerce";

const POPULAR_BANKS = [
  "Vietcombank",
  "Techcombank",
  "MB Bank",
  "ACB",
  "BIDV",
  "VietinBank",
  "TPBank",
  "VPBank",
  "Sacombank",
  "HDBank",
  "VIB",
  "Khác",
];

export interface CreateReturnModalProps {
  order: CommerceOrderDetail;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (returnCode: string) => void;
}

function computeProratedUnitPrice(
  item: CommerceOrderItem,
  order: CommerceOrderDetail
): number {
  if (order.subtotal_vnd > 0 && order.discount_amount_vnd > 0) {
    return Math.round(
      item.unit_price_vnd * (1 - order.discount_amount_vnd / order.subtotal_vnd)
    );
  }
  return item.unit_price_vnd;
}

export function CreateReturnModal({
  order,
  isOpen,
  onClose,
  onSuccess,
}: CreateReturnModalProps) {
  const router = useRouter();
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Selection state
  const [selectedItemIds, setSelectedItemIds] = useState<Record<number, boolean>>({});
  const [quantities, setQuantities] = useState<Record<number, number>>({});

  // Bank fields
  const [bankName, setBankName] = useState(POPULAR_BANKS[0]);
  const [customBankName, setCustomBankName] = useState("");
  const [bankAccountNumber, setBankAccountNumber] = useState("");
  const [bankAccountHolder, setBankAccountHolder] = useState("");

  // Reason & images
  const [customerReason, setCustomerReason] = useState("");
  const [imageUrlsText, setImageUrlsText] = useState("");

  // Loading & error
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize selected items and quantities when modal opens
  useEffect(() => {
    if (isOpen) {
      const initialSelected: Record<number, boolean> = {};
      const initialQtys: Record<number, number> = {};

      order.items.forEach((item, index) => {
        const id = item.order_item_id ?? index;
        initialSelected[id] = true;
        initialQtys[id] = item.quantity;
      });

      setSelectedItemIds(initialSelected);
      setQuantities(initialQtys);
      setError(null);
      setSubmitting(false);
    }
  }, [isOpen, order]);

  // Modal ESC & body overflow
  useEffect(() => {
    if (!isOpen) return;

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
  }, [isOpen, onClose]);

  // Keyboard focus trap
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

  // Calculate refund items and totals
  const { selectedCount, totalEstimatedRefund } = useMemo(() => {
    let count = 0;
    let totalRefund = 0;

    order.items.forEach((item, index) => {
      const id = item.order_item_id ?? index;
      if (selectedItemIds[id]) {
        const qty = quantities[id] || 1;
        const proratedPrice = computeProratedUnitPrice(item, order);
        count += 1;
        totalRefund += proratedPrice * qty;
      }
    });

    return { selectedCount: count, totalEstimatedRefund: totalRefund };
  }, [order, selectedItemIds, quantities]);

  if (!isOpen) return null;

  function toggleItem(id: number) {
    setSelectedItemIds((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  }

  function handleQuantityChange(id: number, maxQty: number, value: number) {
    const validQty = Math.max(1, Math.min(maxQty, value || 1));
    setQuantities((prev) => ({
      ...prev,
      [id]: validQty,
    }));
  }

  const effectiveBankName =
    bankName === "Khác" ? customBankName.trim() : bankName.trim();

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    // Validation
    const selectedEntries = order.items.filter((item, index) => {
      const id = item.order_item_id ?? index;
      return selectedItemIds[id];
    });

    if (selectedEntries.length === 0) {
      setError("Vui lòng chọn ít nhất một sản phẩm cần đổi / trả.");
      return;
    }

    if (!effectiveBankName || effectiveBankName.length < 2) {
      setError("Vui lòng chọn hoặc nhập tên ngân hàng nhận tiền hoàn.");
      return;
    }

    if (!bankAccountNumber.trim() || bankAccountNumber.trim().length < 4) {
      setError("Vui lòng nhập số tài khoản ngân hàng hợp lệ (tối thiểu 4 ký tự).");
      return;
    }

    if (!bankAccountHolder.trim() || bankAccountHolder.trim().length < 2) {
      setError("Vui lòng nhập tên chủ tài khoản ngân hàng.");
      return;
    }

    if (!customerReason.trim() || customerReason.trim().length < 5) {
      setError("Vui lòng nhập lý do đổi / trả hàng chi tiết hơn (tối thiểu 5 ký tự).");
      return;
    }

    const imageUrls = imageUrlsText
      .split(/[\n,]+/)
      .map((url) => url.trim())
      .filter((url) => url.length > 0);

    const payload: CreateReturnRequestInput = {
      customer_reason: customerReason.trim(),
      bank_name: effectiveBankName,
      bank_account_number: bankAccountNumber.trim(),
      bank_account_holder: bankAccountHolder.trim().toUpperCase(),
      image_urls: imageUrls.length > 0 ? imageUrls : undefined,
      items: selectedEntries.map((item, index) => {
        const id = item.order_item_id ?? index;
        return {
          order_item_id: item.order_item_id ?? 0,
          quantity: quantities[id] || 1,
        };
      }),
    };

    const idempotencyKey =
      typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `ret-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

    setSubmitting(true);

    try {
      const result = await createCustomerReturnRequest(
        order.order_number,
        payload,
        idempotencyKey
      );

      onClose();
      if (onSuccess) {
        onSuccess(result.return_code);
      }
      router.push(`/orders/returns/${result.return_code}`);
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError("Không gửi được yêu cầu đổi trả. Vui lòng thử lại sau.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      aria-labelledby={titleId}
      aria-modal="true"
      className="fixed inset-0 z-[60] flex items-end justify-center bg-ink/55 p-0 backdrop-blur-sm sm:items-center sm:p-6"
      onClick={onClose}
      role="dialog"
    >
      <div
        className="flex max-h-[92vh] w-full max-w-2xl flex-col overflow-hidden rounded-t-3xl border border-line bg-surface shadow-lift sm:rounded-3xl"
        onClick={(event) => event.stopPropagation()}
        onKeyDown={keepFocusInside}
        ref={panelRef}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4 sm:px-6">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-500/10 text-amber-600">
                <Icon name="rotate-ccw" size={17} />
              </span>
              <p className="eyebrow">Đổi / Trả hàng & Hoàn tiền</p>
            </div>
            <h2 className="mt-1 text-xl font-semibold sm:text-2xl" id={titleId}>
              Yêu cầu đổi / trả sản phẩm
            </h2>
            <p className="mt-1 text-xs text-muted sm:text-sm">
              Đơn hàng: <span className="font-mono font-medium text-ink">{order.order_number}</span>
            </p>
          </div>
          <button
            aria-label="Đóng cửa sổ yêu cầu đổi trả"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-line bg-surface text-muted transition hover:bg-paper hover:text-ink"
            onClick={onClose}
            ref={closeButtonRef}
            type="button"
          >
            <Icon name="close" size={18} />
          </button>
        </div>

        {/* Scrollable Form Content */}
        <form className="flex min-h-0 flex-1 flex-col" onSubmit={handleSubmit}>
          <div className="flex-1 space-y-6 overflow-y-auto p-5 sm:p-6">
            {error ? (
              <div className="feedback-error">
                <p>{error}</p>
              </div>
            ) : null}

            {/* Section 1: Item selection */}
            <div>
              <div className="flex items-center justify-between">
                <label className="field-label text-base font-semibold">
                  Chọn sản phẩm cần đổi / trả
                </label>
                <span className="text-xs text-muted">
                  Đã chọn {selectedCount}/{order.items.length} sản phẩm
                </span>
              </div>
              <p className="mt-1 text-xs text-muted">
                Tích chọn sản phẩm và điều chỉnh số lượng bạn muốn gửi trả về cửa hàng.
              </p>

              <div className="mt-3 space-y-3">
                {order.items.map((item, index) => {
                  const id = item.order_item_id ?? index;
                  const isSelected = !!selectedItemIds[id];
                  const currentQty = quantities[id] || 1;
                  const proratedPrice = computeProratedUnitPrice(item, order);
                  const isDiscounted = proratedPrice < item.unit_price_vnd;

                  return (
                    <div
                      className={`rounded-2xl border p-3.5 transition sm:p-4 ${
                        isSelected
                          ? "border-amber-500/40 bg-amber-500/5 ring-1 ring-amber-500/20"
                          : "border-line bg-paper/60 opacity-75"
                      }`}
                      key={item.public_id || id}
                    >
                      <div className="flex items-start gap-3">
                        <input
                          aria-label={`Chọn sản phẩm ${item.product_name}`}
                          checked={isSelected}
                          className="mt-1 h-5 w-5 rounded border-line text-accent accent-accent focus:ring-accent"
                          id={`item-checkbox-${id}`}
                          onChange={() => toggleItem(id)}
                          type="checkbox"
                        />

                        <div className="relative flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-sand text-muted sm:h-20 sm:w-20">
                          {item.image_url ? (
                            <Image
                              alt={item.product_name}
                              className="object-cover"
                              fill
                              sizes="80px"
                              src={item.image_url}
                            />
                          ) : (
                            <Icon name="package" size={20} />
                          )}
                        </div>

                        <div className="min-w-0 flex-1">
                          <label
                            className="cursor-pointer font-medium text-ink hover:underline"
                            htmlFor={`item-checkbox-${id}`}
                          >
                            {item.product_name}
                          </label>
                          <p className="mt-0.5 text-xs text-muted">
                            SKU: {item.sku} · {item.size_code}/{item.color_code}
                          </p>

                          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
                            <span className="text-muted">
                              Đơn giá mua: {formatVnd(item.unit_price_vnd)}
                            </span>
                            {isDiscounted ? (
                              <span className="font-medium text-emerald-600">
                                Giá sau khuyến mãi: {formatVnd(proratedPrice)}
                              </span>
                            ) : null}
                          </div>

                          {/* Quantity selector & line refund */}
                          {isSelected ? (
                            <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-line/60 pt-2.5">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-medium text-ink">Số lượng trả:</span>
                                <div className="flex items-center">
                                  <button
                                    className="flex h-8 w-8 items-center justify-center rounded-l-lg border border-line bg-surface text-ink transition hover:bg-paper disabled:opacity-40"
                                    disabled={currentQty <= 1}
                                    onClick={() => handleQuantityChange(id, item.quantity, currentQty - 1)}
                                    type="button"
                                  >
                                    -
                                  </button>
                                  <input
                                    aria-label="Số lượng đổi trả"
                                    className="h-8 w-12 border-y border-line bg-surface text-center text-xs font-semibold text-ink outline-none"
                                    max={item.quantity}
                                    min={1}
                                    onChange={(e) =>
                                      handleQuantityChange(
                                        id,
                                        item.quantity,
                                        parseInt(e.target.value, 10) || 1
                                      )
                                    }
                                    type="number"
                                    value={currentQty}
                                  />
                                  <button
                                    className="flex h-8 w-8 items-center justify-center rounded-r-lg border border-line bg-surface text-ink transition hover:bg-paper disabled:opacity-40"
                                    disabled={currentQty >= item.quantity}
                                    onClick={() => handleQuantityChange(id, item.quantity, currentQty + 1)}
                                    type="button"
                                  >
                                    +
                                  </button>
                                </div>
                                <span className="text-xs text-muted">(Tối đa: {item.quantity})</span>
                              </div>

                              <div className="text-right">
                                <span className="block text-[11px] text-muted">Hoàn trả ước tính</span>
                                <span className="font-semibold text-ink">
                                  {formatVnd(proratedPrice * currentQty)}
                                </span>
                              </div>
                            </div>
                          ) : null}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Section 2: Bank info for refund */}
            <div className="rounded-2xl border border-line bg-paper/40 p-4 sm:p-5">
              <h3 className="flex items-center gap-2 font-semibold text-ink">
                <Icon name="cash" size={17} />
                Thông tin tài khoản nhận tiền hoàn
              </h3>
              <p className="mt-1 text-xs text-muted">
                Số tiền hoàn sẽ được chuyển khoản trực tiếp vào tài khoản ngân hàng này sau khi hàng được kiểm tra đạt chuẩn.
              </p>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="field-label text-xs">
                    Ngân hàng <span className="text-danger">*</span>
                  </label>
                  <select
                    className="form-control"
                    onChange={(e) => setBankName(e.target.value)}
                    value={bankName}
                  >
                    {POPULAR_BANKS.map((b) => (
                      <option key={b} value={b}>
                        {b}
                      </option>
                    ))}
                  </select>
                </div>

                {bankName === "Khác" ? (
                  <div>
                    <label className="field-label text-xs">
                      Tên ngân hàng khác <span className="text-danger">*</span>
                    </label>
                    <input
                      className="form-control"
                      onChange={(e) => setCustomBankName(e.target.value)}
                      placeholder="VD: Shinhan Bank, KBank,..."
                      required
                      value={customBankName}
                    />
                  </div>
                ) : null}

                <div>
                  <label className="field-label text-xs">
                    Số tài khoản <span className="text-danger">*</span>
                  </label>
                  <input
                    className="form-control"
                    onChange={(e) => setBankAccountNumber(e.target.value)}
                    placeholder="VD: 0123456789"
                    required
                    value={bankAccountNumber}
                  />
                </div>

                <div className={bankName === "Khác" ? "sm:col-span-2" : ""}>
                  <label className="field-label text-xs">
                    Tên chủ tài khoản (In hoa không dấu) <span className="text-danger">*</span>
                  </label>
                  <input
                    className="form-control uppercase"
                    onChange={(e) => setBankAccountHolder(e.target.value.toUpperCase())}
                    placeholder="VD: NGUYEN VAN A"
                    required
                    value={bankAccountHolder}
                  />
                </div>
              </div>
            </div>

            {/* Section 3: Reason for return */}
            <div>
              <label className="field-label text-xs font-semibold">
                Lý do yêu cầu đổi / trả hàng <span className="text-danger">*</span>
              </label>
              <textarea
                className="form-control min-h-[90px] resize-y"
                maxLength={1000}
                onChange={(e) => setCustomerReason(e.target.value)}
                placeholder="Mô tả chi tiết lý do (sản phẩm không vừa kích cỡ, lỗi đường may, giao sai mẫu mã,... tối thiểu 5 ký tự)"
                required
                rows={3}
                value={customerReason}
              />
              <div className="mt-1 flex justify-between text-xs text-muted">
                <span>Tối thiểu 5 ký tự</span>
                <span>{customerReason.length}/1000</span>
              </div>
            </div>

            {/* Section 4: Images */}
            <div>
              <label className="field-label text-xs font-semibold">
                Đường dẫn hình ảnh minh chứng (tùy chọn)
              </label>
              <input
                className="form-control"
                onChange={(e) => setImageUrlsText(e.target.value)}
                placeholder="Nhập link ảnh (cách nhau bởi dấu phẩy hoặc xuống dòng)"
                value={imageUrlsText}
              />
              <p className="mt-1 text-xs text-muted">
                Cung cấp hình ảnh chụp thực tế sản phẩm lỗi giúp yêu cầu được duyệt nhanh chóng hơn.
              </p>
            </div>
          </div>

          {/* Footer with Summary and Submit Button */}
          <div className="border-t border-line bg-paper/60 px-5 py-4 sm:px-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <span className="text-xs text-muted">Tổng tiền hoàn ước tính:</span>
                <p className="text-xl font-bold text-ink">
                  {formatVnd(totalEstimatedRefund)}
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  className="button-secondary px-5"
                  disabled={submitting}
                  onClick={onClose}
                  type="button"
                >
                  Đóng
                </button>
                <button
                  className="button-primary px-6"
                  disabled={submitting || selectedCount === 0}
                  type="submit"
                >
                  <Icon name="rotate-ccw" size={17} />
                  {submitting ? "Đang gửi yêu cầu…" : "Gửi yêu cầu đổi trả"}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
export default CreateReturnModal;

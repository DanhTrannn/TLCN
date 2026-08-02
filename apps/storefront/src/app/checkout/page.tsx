"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import CouponPickerModal from "@/components/CouponPickerModal";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd, getCart, type Cart } from "@/lib/api";
import {
  checkoutWithCoupon,
  getAvailableCoupons,
  quoteCheckout,
  type AvailableCoupon,
  type CheckoutQuote,
} from "@/lib/commerce";
import { useAuth } from "@/lib/auth";

export default function CheckoutPage() {
  const { customer, loading: authLoading } = useAuth();
  const router = useRouter();
  const [cart, setCart] = useState<Cart | null>(null);
  const [quote, setQuote] = useState<CheckoutQuote | null>(null);
  const [couponCode, setCouponCode] = useState("");
  const [appliedCouponCode, setAppliedCouponCode] = useState<string | null>(null);
  const [couponBusy, setCouponBusy] = useState(false);
  const [availableCoupons, setAvailableCoupons] = useState<AvailableCoupon[]>([]);
  const [couponModalOpen, setCouponModalOpen] = useState(false);
  const [couponListLoading, setCouponListLoading] = useState(false);
  const [couponListError, setCouponListError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [receiverName, setReceiverName] = useState("");
  const [receiverPhone, setReceiverPhone] = useState("");
  const [address, setAddress] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [couponMessage, setCouponMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const idempotencyKey = useRef<string>("");

  const refreshAvailableCoupons = useCallback(async () => {
    setCouponListLoading(true);
    setCouponListError(null);
    try {
      const response = await getAvailableCoupons();
      setAvailableCoupons(response.items);
    } catch (requestError) {
      setCouponListError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không tải được danh sách mã giảm giá"
      );
    } finally {
      setCouponListLoading(false);
    }
  }, []);

  const closeCouponModal = useCallback(() => {
    setCouponModalOpen(false);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const loadedCart = await getCart();
      setCart(loadedCart);
      setQuote({
        coupon_code: null,
        discount_type: null,
        discount_value: null,
        subtotal_vnd: loadedCart.subtotal_vnd,
        discount_amount_vnd: 0,
        shipping_fee_vnd: loadedCart.shipping_fee_vnd,
        total_vnd: loadedCart.total_vnd,
      });
      void refreshAvailableCoupons();
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 401) {
        router.push("/login?returnTo=/checkout");
        return;
      }
      setError("Không tải được giỏ hàng");
    } finally {
      setLoading(false);
    }
  }, [refreshAvailableCoupons, router]);

  useEffect(() => {
    if (authLoading) return;
    if (!customer) {
      router.push("/login?returnTo=/checkout");
      return;
    }
    if (!idempotencyKey.current) {
      idempotencyKey.current = crypto.randomUUID();
    }
    void load();
  }, [authLoading, customer, load, router]);

  async function applyCoupon(selectedCode?: string) {
    const requestedCode = (selectedCode ?? couponCode).trim().toUpperCase();
    setCouponBusy(true);
    setError(null);
    setCouponMessage(null);
    setCouponListError(null);
    if (selectedCode) setCouponCode(requestedCode);
    try {
      const nextQuote = await quoteCheckout(requestedCode);
      setQuote(nextQuote);
      setAppliedCouponCode(nextQuote.coupon_code);
      setCouponCode(nextQuote.coupon_code ?? "");
      setCouponMessage(
        nextQuote.coupon_code
          ? `Đã áp dụng mã ${nextQuote.coupon_code}.`
          : "Đã bỏ mã giảm giá."
      );
      setCouponModalOpen(false);
    } catch (requestError) {
      const message =
        requestError instanceof ApiError
          ? requestError.message
          : "Không kiểm tra được mã giảm giá";
      setError(message);
      if (couponModalOpen) setCouponListError(message);
    } finally {
      setCouponBusy(false);
    }
  }

  function openCouponModal() {
    setCouponModalOpen(true);
    void refreshAvailableCoupons();
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const result = await checkoutWithCoupon(idempotencyKey.current, {
        receiver_name: receiverName.trim(),
        receiver_phone: receiverPhone.trim(),
        shipping_address_text: address.trim(),
        coupon_code: appliedCouponCode,
      });
      router.push(`/checkout/result/${encodeURIComponent(result.order_number)}`);
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Checkout không thành công"
      );
      setSubmitting(false);
    }
  }

  if (loading || authLoading) {
    return <main className="page-shell"><div className="surface-card h-80 animate-pulse" /></main>;
  }

  if (cart && cart.items.length === 0) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-14 text-center sm:px-6">
        <section className="surface-card p-10">
          <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-paper text-moss"><Icon name="bag" size={24} /></span>
          <h1 className="mt-5 font-serif text-4xl">Giỏ hàng đang trống</h1>
          <p className="mt-3 text-muted">Bạn cần chọn sản phẩm trước khi thanh toán.</p>
          <Link className="button-primary mt-6" href="/products">Khám phá sản phẩm</Link>
        </section>
      </main>
    );
  }

  if (cart && cart.items.some((item) => !item.in_stock)) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-14 text-center sm:px-6">
        <section className="surface-card p-10">
          <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-danger/10 text-danger"><Icon name="alert" size={25} /></span>
          <h1 className="mt-5 font-serif text-4xl">Cần kiểm tra lại giỏ hàng</h1>
          <p className="mx-auto mt-3 max-w-lg text-muted">Một số sản phẩm đã hết hàng hoặc ngừng bán. Hãy điều chỉnh giỏ hàng trước khi tiếp tục.</p>
          <Link className="button-primary mt-6" href="/cart">Quay lại giỏ hàng</Link>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <header>
        <p className="eyebrow">Secure checkout</p>
        <h1 className="page-heading mt-3">Thanh toán</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-muted sm:text-base">
          Kiểm tra thông tin giao hàng. Đơn được tạo sau khi thanh toán thành công và sẽ chờ cửa hàng xác nhận.
        </p>
      </header>

      <div className="mt-9 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_23rem]">
        <form className="space-y-6" id="checkout-form" onSubmit={handleSubmit}>
          <section className="surface-card p-5 sm:p-7">
            <div className="flex items-center gap-3 border-b border-line pb-5">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-moss/10 text-moss"><Icon name="truck" /></span>
              <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Bước 1</p><h2 className="font-semibold">Thông tin giao hàng</h2></div>
            </div>
            <div className="mt-6 grid gap-5 sm:grid-cols-2">
              <label className="field-label" htmlFor="receiver-name">Người nhận
                <input autoComplete="name" className="form-control" id="receiver-name" value={receiverName} onChange={(event) => setReceiverName(event.target.value)} required />
              </label>
              <label className="field-label" htmlFor="receiver-phone">Số điện thoại
                <input autoComplete="tel" className="form-control" id="receiver-phone" inputMode="tel" value={receiverPhone} onChange={(event) => setReceiverPhone(event.target.value)} required />
              </label>
              <label className="field-label sm:col-span-2" htmlFor="shipping-address">Địa chỉ giao hàng
                <textarea autoComplete="street-address" className="form-control min-h-28 resize-y" id="shipping-address" rows={3} value={address} onChange={(event) => setAddress(event.target.value)} required />
              </label>
            </div>
          </section>

          <section className="surface-card p-5 sm:p-7">
            <div className="flex flex-col gap-4 border-b border-line pb-5 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/10 text-accent"><Icon name="ticket" /></span>
                <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Bước 2</p><h2 className="font-semibold">Mã giảm giá</h2></div>
              </div>
              <button className="button-secondary px-4" onClick={openCouponModal} type="button">
                <Icon name="ticket" size={17} />
                Mã khả dụng {availableCoupons.length > 0 ? `(${availableCoupons.length})` : ""}
              </button>
            </div>
            <label className="field-label mt-5" htmlFor="coupon-code">Nhập mã coupon</label>
            <div className="mt-2 flex flex-col gap-2 sm:flex-row">
              <input
                className="form-control mt-0 min-w-0 flex-1 uppercase"
                id="coupon-code"
                maxLength={64}
                placeholder="Ví dụ: NETSALE"
                value={couponCode}
                onChange={(event) => { setCouponCode(event.target.value.toUpperCase()); setCouponMessage(null); }}
              />
              <button className="button-secondary shrink-0" disabled={couponBusy} onClick={() => void applyCoupon()} type="button">
                {couponBusy ? "Đang kiểm tra…" : couponCode.trim() ? "Áp dụng" : "Bỏ mã"}
              </button>
            </div>
            {couponMessage ? <p className="feedback-success mt-4" aria-live="polite">{couponMessage}</p> : null}
          </section>

          {error ? <p className="feedback-error" role="alert">{error}</p> : null}
          <button className="button-accent w-full sm:hidden" type="submit" disabled={submitting || couponBusy}>
            <Icon name="shield" size={18} />
            {submitting ? "Đang xử lý…" : "Thanh toán và tạo đơn"}
          </button>
        </form>

        <aside className="rounded-3xl bg-ink p-6 text-paper shadow-lift lg:sticky lg:top-24">
          <div className="flex items-center gap-3 border-b border-paper/15 pb-5">
            <Icon className="text-paper/70" name="receipt" />
            <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-paper/60">Đơn hàng</p><h2 className="font-semibold">Tóm tắt thanh toán</h2></div>
          </div>
          <ul className="mt-5 space-y-4 text-sm">
            {cart?.items.map((item) => (
              <li key={item.variant_public_id} className="flex justify-between gap-4">
                <span className="leading-5 text-paper/75">{item.product_name}<span className="block text-xs text-paper/65">{item.size_code} · {item.color_code} · SL {item.quantity}</span></span>
                <span className="shrink-0 font-medium">{formatVnd(item.line_total_vnd)}</span>
              </li>
            ))}
          </ul>
          <dl className="mt-5 space-y-3 border-t border-paper/15 pt-5 text-sm">
            <div className="flex justify-between text-paper/70"><dt>Tạm tính</dt><dd>{formatVnd(quote?.subtotal_vnd)}</dd></div>
            {quote && quote.discount_amount_vnd > 0 ? <div className="flex justify-between text-emerald-300"><dt>Giảm giá {quote.coupon_code ? `(${quote.coupon_code})` : ""}</dt><dd>−{formatVnd(quote.discount_amount_vnd)}</dd></div> : null}
            <div className="flex justify-between text-paper/70"><dt>Vận chuyển</dt><dd>{quote?.shipping_fee_vnd === 0 ? "Miễn phí" : formatVnd(quote?.shipping_fee_vnd)}</dd></div>
          </dl>
          <div className="mt-5 border-t border-paper/15 pt-5"><div className="flex items-end justify-between gap-4"><span className="text-sm text-paper/65">Tổng cộng</span><strong className="text-2xl">{formatVnd(quote?.total_vnd)}</strong></div></div>
          <button className="mt-6 hidden min-h-12 w-full items-center justify-center gap-2 rounded-full bg-paper px-5 text-sm font-semibold text-ink transition hover:bg-white disabled:opacity-50 sm:flex" type="submit" form="checkout-form" disabled={submitting || couponBusy}>
            <Icon name="shield" size={18} />
            {submitting ? "Đang xử lý…" : "Thanh toán và tạo đơn"}
          </button>
          <p className="mt-4 text-center text-xs leading-5 text-paper/60">Tồn kho được kiểm tra lại trước khi tạo đơn.</p>
        </aside>
      </div>

      {couponModalOpen ? (
        <CouponPickerModal appliedCode={appliedCouponCode} busy={couponBusy} coupons={availableCoupons} error={couponListError} loading={couponListLoading} onClose={closeCouponModal} onRefresh={() => void refreshAvailableCoupons()} onSelect={(code) => void applyCoupon(code)} />
      ) : null}
    </main>
  );
}

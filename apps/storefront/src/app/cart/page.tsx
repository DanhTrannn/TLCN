"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import CouponPickerModal from "@/components/CouponPickerModal";
import { CartCrossSell } from "@/components/CartCrossSell";
import { FreeShippingBar } from "@/components/FreeShippingBar";
import { VariantSwitcherModal } from "@/components/VariantSwitcherModal";
import { Icon } from "@/components/ui/Icon";
import {
  ApiError,
  addWishlistProduct,
  formatVnd,
  getCart,
  removeCartItem,
  setCartItem,
  type Cart,
  type CartItem,
  type Variant,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  getAvailableCoupons,
  quoteCheckout,
  type AvailableCoupon,
  type CheckoutQuote,
} from "@/lib/commerce";

export default function CartPage() {
  const { customer, loading: authLoading } = useAuth();
  const router = useRouter();
  const [cart, setCart] = useState<Cart | null>(null);
  const [quote, setQuote] = useState<CheckoutQuote | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyItem, setBusyItem] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [variantModalItem, setVariantModalItem] = useState<CartItem | null>(null);

  // Coupon state
  const [couponCode, setCouponCode] = useState("");
  const [appliedCouponCode, setAppliedCouponCode] = useState<string | null>(null);
  const [couponBusy, setCouponBusy] = useState(false);
  const [couponMessage, setCouponMessage] = useState<string | null>(null);
  const [availableCoupons, setAvailableCoupons] = useState<AvailableCoupon[]>([]);
  const [couponModalOpen, setCouponModalOpen] = useState(false);
  const [couponListLoading, setCouponListLoading] = useState(false);

  const refreshAvailableCoupons = useCallback(async () => {
    setCouponListLoading(true);
    try {
      const response = await getAvailableCoupons();
      setAvailableCoupons(response.items);
    } catch {
      // ignore
    } finally {
      setCouponListLoading(false);
    }
  }, []);

  const refresh = useCallback(
    async (recalculateCoupon: boolean = true) => {
      setLoading(true);
      try {
        const loadedCart = await getCart();
        setCart(loadedCart);
        setError(null);

        if (recalculateCoupon && appliedCouponCode) {
          try {
            const nextQuote = await quoteCheckout(appliedCouponCode);
            setQuote(nextQuote);
          } catch {
            setQuote({
              coupon_code: null,
              discount_type: null,
              discount_value: null,
              subtotal_vnd: loadedCart.subtotal_vnd,
              discount_amount_vnd: 0,
              shipping_fee_vnd: loadedCart.shipping_fee_vnd,
              total_vnd: loadedCart.total_vnd,
            });
            setAppliedCouponCode(null);
          }
        } else {
          setQuote({
            coupon_code: null,
            discount_type: null,
            discount_value: null,
            subtotal_vnd: loadedCart.subtotal_vnd,
            discount_amount_vnd: 0,
            shipping_fee_vnd: loadedCart.shipping_fee_vnd,
            total_vnd: loadedCart.total_vnd,
          });
        }
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          router.push("/login?returnTo=/cart");
          return;
        }
        setError("Không tải được giỏ hàng");
      } finally {
        setLoading(false);
      }
    },
    [appliedCouponCode, router]
  );

  useEffect(() => {
    if (authLoading) return;
    if (!customer) {
      router.push("/login?returnTo=/cart");
      return;
    }
    void refresh();
    void refreshAvailableCoupons();
  }, [authLoading, customer, refresh, refreshAvailableCoupons, router]);

  async function updateQuantity(variantPublicId: string, quantity: number) {
    if (quantity < 1) return;
    setBusyItem(variantPublicId);
    setError(null);
    try {
      const updated = await setCartItem(variantPublicId, quantity);
      setCart(updated);
      if (appliedCouponCode) {
        const nextQuote = await quoteCheckout(appliedCouponCode);
        setQuote(nextQuote);
      } else {
        setQuote((prev) =>
          prev
            ? {
                ...prev,
                subtotal_vnd: updated.subtotal_vnd,
                shipping_fee_vnd: updated.shipping_fee_vnd,
                total_vnd: updated.total_vnd,
              }
            : null
        );
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Cập nhật thất bại");
    } finally {
      setBusyItem(null);
    }
  }

  async function remove(variantPublicId: string) {
    setBusyItem(variantPublicId);
    setError(null);
    try {
      const updated = await removeCartItem(variantPublicId);
      setCart(updated);
      if (appliedCouponCode) {
        const nextQuote = await quoteCheckout(appliedCouponCode);
        setQuote(nextQuote);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Xóa thất bại");
    } finally {
      setBusyItem(null);
    }
  }

  async function moveToWishlist(item: {
    variant_public_id: string;
    product_public_id?: string | null;
    product_name: string;
  }) {
    if (!item.product_public_id) {
      await remove(item.variant_public_id);
      return;
    }
    setBusyItem(item.variant_public_id);
    setError(null);
    try {
      await addWishlistProduct(item.product_public_id);
      const updated = await removeCartItem(item.variant_public_id);
      setCart(updated);
      setActionNotice(`Đã chuyển "${item.product_name}" sang danh sách Yêu thích.`);
      setTimeout(() => setActionNotice(null), 4000);
      if (appliedCouponCode) {
        const nextQuote = await quoteCheckout(appliedCouponCode);
        setQuote(nextQuote);
      }
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Không chuyển được sang yêu thích"
      );
    } finally {
      setBusyItem(null);
    }
  }

  async function handleSwitchVariant(item: CartItem, newVariant: Variant) {
    setBusyItem(item.variant_public_id);
    setError(null);
    try {
      await setCartItem(item.variant_public_id, 0);
      const updated = await setCartItem(newVariant.public_id, item.quantity);
      setCart(updated);
      setActionNotice(`Đã đổi sang Size ${newVariant.size_code} / Màu ${newVariant.color_code}.`);
      setTimeout(() => setActionNotice(null), 4000);
      if (appliedCouponCode) {
        const nextQuote = await quoteCheckout(appliedCouponCode);
        setQuote(nextQuote);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Đổi phân loại thất bại");
      throw err;
    } finally {
      setBusyItem(null);
    }
  }

  async function handleQuickAddCrossSell(variantPublicId: string) {
    setError(null);
    try {
      const existing = cart?.items.find((i) => i.variant_public_id === variantPublicId);
      const nextQty = existing ? existing.quantity + 1 : 1;
      const updated = await setCartItem(variantPublicId, nextQty);
      setCart(updated);
      setActionNotice("Đã thêm sản phẩm phối vào giỏ hàng.");
      setTimeout(() => setActionNotice(null), 3000);
      if (appliedCouponCode) {
        const nextQuote = await quoteCheckout(appliedCouponCode);
        setQuote(nextQuote);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Thêm vào giỏ thất bại");
    }
  }

  async function handleApplyCoupon(codeToApply?: string) {
    const code = (codeToApply ?? couponCode).trim().toUpperCase();
    if (!code) {
      // Clear coupon
      setAppliedCouponCode(null);
      setCouponCode("");
      setCouponMessage(null);
      if (cart) {
        setQuote({
          coupon_code: null,
          discount_type: null,
          discount_value: null,
          subtotal_vnd: cart.subtotal_vnd,
          discount_amount_vnd: 0,
          shipping_fee_vnd: cart.shipping_fee_vnd,
          total_vnd: cart.total_vnd,
        });
      }
      return;
    }

    setCouponBusy(true);
    setCouponMessage(null);
    setError(null);
    try {
      const nextQuote = await quoteCheckout(code);
      setQuote(nextQuote);
      setAppliedCouponCode(nextQuote.coupon_code);
      setCouponCode(nextQuote.coupon_code ?? "");
      setCouponMessage(
        nextQuote.coupon_code
          ? `Áp dụng thành công mã ${nextQuote.coupon_code}! Tiết kiệm ${formatVnd(nextQuote.discount_amount_vnd)}.`
          : "Mã giảm giá không khả dụng."
      );
      setCouponModalOpen(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Mã ưu đãi không hợp lệ");
    } finally {
      setCouponBusy(false);
    }
  }

  if (loading || authLoading) {
    return (
      <main className="mx-auto max-w-6xl px-5 py-12 sm:px-6 sm:py-16">
        <div className="surface-card p-10 animate-pulse text-muted">
          Đang tải giỏ hàng của bạn…
        </div>
      </main>
    );
  }

  const items = cart?.items ?? [];
  const subtotal = quote ? quote.subtotal_vnd : cart?.subtotal_vnd ?? 0;
  const discountAmount = quote?.discount_amount_vnd ?? 0;
  const shippingFee = quote ? quote.shipping_fee_vnd : cart?.shipping_fee_vnd ?? 0;
  const totalAmount = quote ? quote.total_vnd : cart?.total_vnd ?? 0;
  const freeShippingThreshold = cart?.free_shipping_threshold_vnd ?? 500000;
  const canCheckout = items.length > 0 && items.every((item) => item.in_stock);

  return (
    <main className="mx-auto max-w-6xl px-5 py-10 sm:px-6 sm:py-16">
      {/* Header */}
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between border-b border-line pb-6">
        <div>
          <p className="eyebrow">D&K Cart</p>
          <div className="mt-1 flex items-center gap-3">
            <h1 className="font-serif text-3xl sm:text-4xl text-ink">Giỏ hàng của bạn</h1>
            <span className="flex h-6 items-center justify-center rounded-full bg-accent/15 px-2.5 text-xs font-bold text-accent">
              {items.length} món
            </span>
          </div>
        </div>
        {items.length > 0 ? (
          <Link
            className="inline-flex items-center gap-2 text-sm font-semibold text-moss hover:text-accent transition"
            href="/products"
          >
            <span>+ Tiếp tục mua sắm</span>
          </Link>
        ) : null}
      </header>

      {/* Alerts */}
      {actionNotice ? (
        <div className="mt-6 flex items-center gap-2.5 rounded-2xl border border-emerald-500/25 bg-emerald-500/10 p-4 text-sm font-medium text-emerald-800 dark:text-emerald-300">
          <Icon name="check" size={17} />
          <span>{actionNotice}</span>
        </div>
      ) : null}

      {error ? (
        <div className="mt-6 flex items-center gap-2.5 rounded-2xl border border-danger/30 bg-danger/10 p-4 text-sm font-medium text-danger">
          <Icon name="alert" size={17} />
          <span>{error}</span>
        </div>
      ) : null}

      {/* Empty State */}
      {items.length === 0 ? (
        <section className="mt-10 rounded-3xl border border-line bg-surface p-12 text-center shadow-soft sm:p-16">
          <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-paper text-muted">
            <Icon name="bag" size={30} />
          </span>
          <h2 className="mt-5 font-serif text-2xl text-ink">Giỏ hàng của bạn đang trống</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">
            Khám phá những thiết kế thời trang nữ mới nhất từ D&K và thêm vào giỏ nhé.
          </p>
          <Link className="button-primary mt-6 text-sm" href="/products">
            Khám phá sản phẩm
            <Icon name="arrow-right" size={16} />
          </Link>
        </section>
      ) : (
        <div className="mt-8 space-y-6">
          {/* Prominent Free Shipping Progress Goal */}
          <FreeShippingBar
            subtotalVnd={subtotal}
            thresholdVnd={freeShippingThreshold}
          />

          {/* Main Grid: Flat Product List + Light Summary Card */}
          <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_23rem]">
            {/* Left: Minimalist Flat Product List */}
            <section className="surface-card p-6 sm:p-8">
              <div className="flex items-center justify-between border-b border-line pb-4">
                <h2 className="font-serif text-xl text-ink">Danh sách sản phẩm</h2>
                <span className="text-xs font-semibold text-muted">
                  {items.reduce((sum, it) => sum + it.quantity, 0)} sản phẩm
                </span>
              </div>

              <div className="divide-y divide-line">
                {items.map((item) => {
                  const isBusy = busyItem === item.variant_public_id;
                  return (
                    <article
                      className="flex flex-col gap-4 py-6 sm:flex-row sm:items-center sm:justify-between transition-colors"
                      key={item.variant_public_id}
                    >
                      {/* Left: Image & Info */}
                      <div className="flex items-start gap-4 sm:gap-5 min-w-0 flex-1">
                        <Link
                          className="relative h-28 w-20 shrink-0 overflow-hidden rounded-2xl border border-line bg-paper group"
                          href={`/products/${item.slug}`}
                        >
                          {item.image_url ? (
                            <Image
                              alt={item.product_name}
                              className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
                              height={112}
                              src={item.image_url}
                              width={80}
                            />
                          ) : (
                            <div className="flex h-full w-full items-center justify-center text-muted">
                              <Icon name="package" size={24} />
                            </div>
                          )}
                        </Link>

                        <div className="min-w-0 flex-1">
                          <Link
                            className="font-serif font-semibold text-base sm:text-lg text-ink hover:text-accent transition line-clamp-1"
                            href={`/products/${item.slug}`}
                          >
                            {item.product_name}
                          </Link>
                          <p className="mt-0.5 text-xs text-muted">SKU: {item.sku}</p>

                          <div className="mt-2.5 flex flex-wrap items-center gap-2">
                            <button
                              aria-label={`Đổi phân loại cho ${item.product_name}`}
                              className="group inline-flex items-center gap-1.5 rounded-full border border-line bg-paper px-2.5 py-1 text-xs font-medium text-ink/80 hover:border-accent hover:text-accent transition shadow-2xs"
                              disabled={isBusy}
                              onClick={() => setVariantModalItem(item)}
                              title="Bấm để đổi Size hoặc Màu khác"
                              type="button"
                            >
                              <span>Size {item.size_code}</span>
                              <span className="text-muted/60 font-semibold">/</span>
                              <span>Màu {item.color_code}</span>
                              <span className="text-[10px] text-muted group-hover:text-accent font-bold">▾</span>
                            </button>
                            <span
                              className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                                item.in_stock
                                  ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                                  : "bg-danger/10 text-danger"
                              }`}
                            >
                              {item.in_stock ? "Còn hàng" : "Hết hàng"}
                            </span>
                          </div>

                          <p className="mt-2 text-xs text-muted">
                            Đơn giá: {formatVnd(item.unit_price_vnd)}
                          </p>
                        </div>
                      </div>

                      {/* Right: Quantity Stepper & Subtotal */}
                      <div className="flex items-center justify-between sm:flex-col sm:items-end sm:justify-center gap-3 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-line">
                        <span className="font-semibold text-base sm:text-lg text-ink">
                          {formatVnd(item.line_total_vnd)}
                        </span>

                        {/* Compact Stepper */}
                        <div className="flex items-center gap-3">
                          <div className="flex items-center rounded-full border border-line bg-paper p-0.5 shadow-sm">
                            <button
                              aria-label="Giảm số lượng"
                              className="flex h-8 w-8 items-center justify-center rounded-full text-muted hover:bg-surface hover:text-ink transition disabled:opacity-30"
                              disabled={isBusy || item.quantity <= 1}
                              onClick={() =>
                                void updateQuantity(item.variant_public_id, item.quantity - 1)
                              }
                              type="button"
                            >
                              -
                            </button>
                            <span className="w-8 text-center text-xs font-semibold tabular-nums text-ink">
                              {item.quantity}
                            </span>
                            <button
                              aria-label="Tăng số lượng"
                              className="flex h-8 w-8 items-center justify-center rounded-full text-muted hover:bg-surface hover:text-ink transition disabled:opacity-30"
                              disabled={isBusy}
                              onClick={() =>
                                void updateQuantity(item.variant_public_id, item.quantity + 1)
                              }
                              type="button"
                            >
                              +
                            </button>
                          </div>

                          {/* Quick Actions: Move to Wishlist & Remove */}
                          <div className="flex items-center gap-1">
                            <button
                              aria-label="Lưu vào yêu thích"
                              className="flex h-8 w-8 items-center justify-center rounded-full border border-line bg-paper text-muted hover:border-accent/40 hover:text-accent transition disabled:opacity-40"
                              disabled={isBusy}
                              onClick={() => void moveToWishlist(item)}
                              title="Lưu vào yêu thích để mua sau"
                              type="button"
                            >
                              <Icon name="heart" size={15} />
                            </button>
                            <button
                              aria-label="Xóa khỏi giỏ"
                              className="flex h-8 w-8 items-center justify-center rounded-full border border-line bg-paper text-muted hover:border-danger/40 hover:text-danger transition disabled:opacity-40"
                              disabled={isBusy}
                              onClick={() => void remove(item.variant_public_id)}
                              title="Xóa món này"
                              type="button"
                            >
                              <Icon name="trash" size={15} />
                            </button>
                          </div>
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>

            {/* Right: Elegant Light Summary Card */}
            <aside className="surface-card p-6 sm:p-7 shadow-soft space-y-6 lg:sticky lg:top-24">
              <div>
                <p className="eyebrow">Tóm tắt đơn hàng</p>
                <h2 className="mt-1 font-serif text-2xl text-ink">Thanh toán</h2>
              </div>

              {/* Coupon Box Directly in Cart */}
              <div className="rounded-2xl border border-line bg-paper/60 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted">
                    <Icon name="ticket" size={14} />
                    Mã ưu đãi (Coupon)
                  </span>
                  {availableCoupons.length > 0 ? (
                    <button
                      className="text-xs font-semibold text-accent hover:underline"
                      onClick={() => setCouponModalOpen(true)}
                      type="button"
                    >
                      Chọn mã ({availableCoupons.length})
                    </button>
                  ) : null}
                </div>

                {appliedCouponCode ? (
                  <div className="flex items-center justify-between rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs font-medium text-emerald-800 dark:text-emerald-300">
                    <span className="flex items-center gap-1.5">
                      <Icon name="check" size={14} />
                      Đã áp dụng: <strong>{appliedCouponCode}</strong>
                    </span>
                    <button
                      aria-label="Bỏ mã"
                      className="text-muted hover:text-danger transition"
                      onClick={() => void handleApplyCoupon("")}
                      type="button"
                    >
                      <Icon name="close" size={14} />
                    </button>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <input
                      className="form-control text-xs uppercase"
                      onChange={(e) => setCouponCode(e.target.value)}
                      placeholder="Nhập mã giảm giá…"
                      type="text"
                      value={couponCode}
                    />
                    <button
                      className="button-secondary text-xs px-3 shrink-0"
                      disabled={couponBusy || !couponCode.trim()}
                      onClick={() => void handleApplyCoupon()}
                      type="button"
                    >
                      {couponBusy ? "…" : "Áp dụng"}
                    </button>
                  </div>
                )}

                {couponMessage ? (
                  <p className="text-xs font-medium text-emerald-700 dark:text-emerald-400">
                    {couponMessage}
                  </p>
                ) : null}
              </div>

              {/* Financial Calculation Lines */}
              <dl className="space-y-3 text-sm border-t border-line pt-4">
                <div className="flex items-center justify-between text-muted">
                  <dt>Tạm tính:</dt>
                  <dd className="font-semibold text-ink">{formatVnd(subtotal)}</dd>
                </div>

                {discountAmount > 0 ? (
                  <div className="flex items-center justify-between text-emerald-600 dark:text-emerald-400 font-medium">
                    <dt className="flex items-center gap-1">
                      <Icon name="ticket" size={14} />
                      Giảm giá voucher:
                    </dt>
                    <dd className="font-semibold">- {formatVnd(discountAmount)}</dd>
                  </div>
                ) : null}

                <div className="flex items-center justify-between text-muted">
                  <dt>Phí vận chuyển:</dt>
                  <dd className="font-semibold text-ink">
                    {shippingFee === 0 ? (
                      <span className="text-emerald-600 dark:text-emerald-400">Miễn phí</span>
                    ) : (
                      formatVnd(shippingFee)
                    )}
                  </dd>
                </div>

                <div className="border-t border-line pt-3 flex items-baseline justify-between">
                  <dt className="font-serif text-base text-ink font-semibold">Tổng thanh toán:</dt>
                  <dd className="font-serif text-2xl font-bold text-accent">
                    {formatVnd(totalAmount)}
                  </dd>
                </div>
                <p className="text-[11px] text-right text-muted">Đã bao gồm thuế GTGT & phí đóng gói</p>
              </dl>

              {/* Primary Checkout CTA */}
              {canCheckout ? (
                <Link
                  className="button-primary w-full py-3.5 flex items-center justify-center gap-2 text-sm font-semibold shadow-md hover:shadow-lg transition"
                  href={`/checkout${appliedCouponCode ? `?coupon=${encodeURIComponent(appliedCouponCode)}` : ""}`}
                >
                  <span>Tiến hành thanh toán</span>
                  <Icon name="arrow-right" size={17} />
                </Link>
              ) : (
                <div className="rounded-2xl border border-danger/30 bg-danger/10 p-3.5 text-xs text-danger leading-relaxed">
                  Một số sản phẩm trong giỏ đã hết hàng. Vui lòng điều chỉnh số lượng trước khi thanh toán.
                </div>
              )}

              {/* Trust Badges */}
              <div className="border-t border-line pt-4 space-y-2.5 text-xs text-muted">
                <div className="flex items-center gap-2">
                  <Icon className="text-moss shrink-0" name="rotate-ccw" size={15} />
                  <span>Hỗ trợ đổi size miễn phí trong <strong>7 ngày</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <Icon className="text-moss shrink-0" name="package" size={15} />
                  <span>Được <strong>đồng kiểm</strong> khi nhận hàng toàn quốc</span>
                </div>
                <div className="flex items-center gap-2">
                  <Icon className="text-moss shrink-0" name="shield" size={15} />
                  <span>Thanh toán an toàn bảo mật qua <strong>VietQR / COD</strong></span>
                </div>
              </div>
            </aside>
          </div>

          {/* Complete the Look Cross-Sell */}
          <CartCrossSell
            cartItems={items}
            onAddToCart={handleQuickAddCrossSell}
          />
        </div>
      )}

      {/* Coupon Picker Modal */}
      {couponModalOpen ? (
        <CouponPickerModal
          appliedCode={appliedCouponCode}
          busy={couponBusy}
          coupons={availableCoupons}
          error={null}
          loading={couponListLoading}
          onClose={() => setCouponModalOpen(false)}
          onRefresh={refreshAvailableCoupons}
          onSelect={(code) => void handleApplyCoupon(code)}
        />
      ) : null}

      {/* Variant Switcher Modal */}
      {variantModalItem ? (
        <VariantSwitcherModal
          isOpen={Boolean(variantModalItem)}
          item={variantModalItem}
          onClose={() => setVariantModalItem(null)}
          onSwitchVariant={handleSwitchVariant}
        />
      ) : null}
    </main>
  );
}

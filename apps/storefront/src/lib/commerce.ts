import { apiFetch } from "./api-client";
import { publicConfig } from "./config";

export interface AvailableCoupon {
  code: string;
  discount_type: "percentage" | "fixed_amount";
  discount_value: number;
  minimum_subtotal_vnd: number;
  discount_amount_vnd: number;
  ends_at: string;
  remaining_uses: number | null;
}

export interface AvailableCouponList {
  subtotal_vnd: number;
  items: AvailableCoupon[];
}

export interface CheckoutQuote {
  coupon_code: string | null;
  discount_type: "percentage" | "fixed_amount" | null;
  discount_value: number | null;
  subtotal_vnd: number;
  discount_amount_vnd: number;
  shipping_fee_vnd: number;
  total_vnd: number;
}

export interface CheckoutResult {
  order_number: string;
  status: string;
  payment_status: string;
  failure_code: string | null;
  coupon_code: string | null;
  subtotal_vnd: number;
  discount_amount_vnd: number;
  shipping_fee_vnd: number;
  total_vnd: number;
}

export interface OrderItemReview {
  public_id: string;
  rating: number;
  content: string | null;
  status: "approved" | "rejected";
  moderation_reason: string | null;
}

export interface CommerceOrderItem {
  public_id: string;
  product_public_id: string;
  image_url: string | null;
  product_name: string;
  sku: string;
  size_code: string;
  color_code: string;
  unit_price_vnd: number;
  quantity: number;
  line_total_vnd: number;
  review: OrderItemReview | null;
}

export interface CommerceOrderDetail {
  order_number: string;
  status: string;
  currency_code: string;
  subtotal_vnd: number;
  coupon_code: string | null;
  discount_amount_vnd: number;
  shipping_fee_vnd: number;
  total_vnd: number;
  receiver_name: string;
  receiver_phone: string;
  shipping_address_text: string;
  created_at: string;
  paid_at: string | null;
  confirmed_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  items: CommerceOrderItem[];
  payment: {
    payment_reference: string;
    status: string;
    amount_vnd: number;
    failure_code: string | null;
    attempted_at: string;
  } | null;
  refund: {
    public_id: string;
    status: string;
    amount_vnd: number;
    reason: string;
    created_at: string;
    completed_at: string | null;
  } | null;
  status_history: Array<{
    from_status: string | null;
    to_status: string;
    transition_source: string;
    reason: string | null;
    transitioned_at: string;
  }>;
}

export interface OrderTransition {
  order_number: string;
  status: string;
  refunded_amount_vnd: number | null;
}

export interface ProductReview {
  public_id: string;
  rating: number;
  content: string | null;
  customer_name: string;
  created_at: string;
}

export interface ReviewList {
  items: ProductReview[];
  total: number;
  average_rating: number | null;
}

export interface AdminReview {
  public_id: string;
  order_number: string;
  product_name: string;
  customer_name: string;
  rating: number;
  content: string | null;
  status: "approved" | "rejected";
  moderation_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminCoupon {
  public_id: string;
  code: string;
  discount_type: "percentage" | "fixed_amount";
  discount_value: number;
  minimum_subtotal_vnd: number;
  starts_at: string;
  ends_at: string;
  is_active: boolean;
  archived_at: string | null;
  archive_reason: string | null;
  total_usage_limit: number | null;
  per_customer_usage_limit: number | null;
  used_count: number;
  created_at: string;
  updated_at: string;
}

const CSRF_COOKIE = publicConfig.csrfCookieName;

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

function mutationHeaders(idempotencyKey?: string): HeadersInit {
  const csrfToken = readCookie(CSRF_COOKIE);
  return {
    ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
    ...(idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {}),
  };
}

export function getAvailableCoupons() {
  return apiFetch<AvailableCouponList>("/api/v1/coupons/available");
}

export function quoteCheckout(couponCode?: string) {
  return apiFetch<CheckoutQuote>("/api/v1/checkout/quote", {
    method: "POST",
    body: JSON.stringify({ coupon_code: couponCode?.trim() || null }),
  });
}

export function checkoutWithCoupon(
  idempotencyKey: string,
  input: {
    receiver_name: string;
    receiver_phone: string;
    shipping_address_text: string;
    coupon_code?: string | null;
  }
) {
  return apiFetch<CheckoutResult>("/api/v1/checkout", {
    method: "POST",
    headers: mutationHeaders(idempotencyKey),
    body: JSON.stringify(input),
  });
}

export function getCommerceOrder(orderNumber: string) {
  return apiFetch<CommerceOrderDetail>(
    `/api/v1/orders/${encodeURIComponent(orderNumber)}`
  );
}

export function getAdminCommerceOrder(orderNumber: string) {
  return apiFetch<CommerceOrderDetail>(
    `/api/v1/admin/orders/${encodeURIComponent(orderNumber)}`
  );
}

export function cancelCustomerOrder(orderNumber: string, reason: string) {
  return apiFetch<OrderTransition>(
    `/api/v1/orders/${encodeURIComponent(orderNumber)}/cancel`,
    {
      method: "POST",
      headers: mutationHeaders(crypto.randomUUID()),
      body: JSON.stringify({ reason }),
    }
  );
}

export function completeCustomerOrder(orderNumber: string) {
  return apiFetch<OrderTransition>(
    `/api/v1/orders/${encodeURIComponent(orderNumber)}/complete`,
    {
      method: "POST",
      headers: mutationHeaders(crypto.randomUUID()),
    }
  );
}

export function confirmAdminOrder(orderNumber: string) {
  return apiFetch<OrderTransition>(
    `/api/v1/admin/orders/${encodeURIComponent(orderNumber)}/confirm`,
    {
      method: "POST",
      headers: mutationHeaders(crypto.randomUUID()),
    }
  );
}

export function cancelAdminOrder(orderNumber: string, reason: string) {
  return apiFetch<OrderTransition>(
    `/api/v1/admin/orders/${encodeURIComponent(orderNumber)}/cancel`,
    {
      method: "POST",
      headers: mutationHeaders(crypto.randomUUID()),
      body: JSON.stringify({ reason }),
    }
  );
}

export function createOrderItemReview(
  orderNumber: string,
  orderItemPublicId: string,
  input: { rating: number; content?: string | null }
) {
  return apiFetch<OrderItemReview>(
    `/api/v1/orders/${encodeURIComponent(orderNumber)}/items/${encodeURIComponent(orderItemPublicId)}/review`,
    {
      method: "POST",
      headers: mutationHeaders(),
      body: JSON.stringify(input),
    }
  );
}

export function getProductReviews(slug: string) {
  return apiFetch<ReviewList>(
    `/api/v1/products/${encodeURIComponent(slug)}/reviews`
  );
}

export function getAdminReviews(status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<AdminReview[]>(`/api/v1/admin/reviews${query}`);
}

export function moderateAdminReview(
  publicId: string,
  input: { status: "approved" | "rejected"; reason?: string | null }
) {
  return apiFetch<OrderItemReview>(
    `/api/v1/admin/reviews/${encodeURIComponent(publicId)}`,
    {
      method: "PATCH",
      headers: mutationHeaders(),
      body: JSON.stringify(input),
    }
  );
}

export function getAdminCoupons() {
  return apiFetch<AdminCoupon[]>("/api/v1/admin/coupons");
}

export function createAdminCoupon(input: {
  code: string;
  discount_type: "percentage" | "fixed_amount";
  discount_value: number;
  minimum_subtotal_vnd: number;
  starts_at: string;
  ends_at: string;
  total_usage_limit: number | null;
  per_customer_usage_limit: number | null;
}) {
  return apiFetch<AdminCoupon>("/api/v1/admin/coupons", {
    method: "POST",
    headers: mutationHeaders(),
    body: JSON.stringify(input),
  });
}

export function setAdminCouponActive(publicId: string, isActive: boolean) {
  return apiFetch<void>(
    `/api/v1/admin/coupons/${encodeURIComponent(publicId)}`,
    {
      method: "PATCH",
      headers: mutationHeaders(),
      body: JSON.stringify({ is_active: isActive }),
    }
  );
}

export function archiveAdminCoupon(publicId: string, reason: string) {
  return apiFetch<void>(
    `/api/v1/admin/coupons/${encodeURIComponent(publicId)}`,
    {
      method: "DELETE",
      headers: mutationHeaders(),
      body: JSON.stringify({ reason }),
    }
  );
}

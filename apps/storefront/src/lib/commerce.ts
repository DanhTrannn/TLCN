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
  payment_method?: string | null;
}

export interface DeliveryStaff {
  staff_id: number;
  public_id: string;
  full_name: string;
  phone: string;
  vehicle_plate: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ShipmentDetail {
  shipment_id: number;
  shipment_code: string;
  order_id: number;
  order_number: string;
  delivery_staff_id: number | null;
  delivery_staff_name: string | null;
  delivery_staff_phone: string | null;
  vehicle_plate?: string | null;
  status: string;
  attempt_count: number;
  dispatched_at: string | null;
  delivered_at: string | null;
  failed_at: string | null;
  cod_amount_vnd: number;
  cod_collected_vnd: number;
  failure_reason: string | null;
  notes: string | null;
  created_at?: string | null;
}

export interface OrderItemReview {
  public_id: string;
  rating: number;
  content: string | null;
  status: "approved" | "rejected";
  moderation_reason: string | null;
}

export interface CommerceOrderItem {
  order_item_id?: number;
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
  payment_method?: string | null;
  items: CommerceOrderItem[];
  payment: {
    payment_reference: string;
    status: string;
    amount_vnd: number;
    failure_code: string | null;
    attempted_at: string;
  } | null;
  refund?: {
    public_id?: string;
    status: string;
    amount_vnd: number;
    reason?: string;
    created_at?: string;
    completed_at?: string | null;
  } | null;
  active_return?: ReturnRequestSummary | null;
  status_history: Array<{
    from_status: string | null;
    to_status: string;
    transition_source: string;
    reason: string | null;
    transitioned_at: string;
  }>;
  shipment?: ShipmentDetail | null;
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
    payment_method?: "vietqr" | "cod";
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

export function dispatchAdminOrder(
  orderNumber: string,
  deliveryStaffId: number,
  notes?: string
) {
  return apiFetch<OrderTransition>(
    `/api/v1/admin/orders/${encodeURIComponent(orderNumber)}/dispatch`,
    {
      method: "POST",
      headers: mutationHeaders(crypto.randomUUID()),
      body: JSON.stringify({
        delivery_staff_id: deliveryStaffId,
        notes: notes ?? null,
      }),
    }
  );
}

export function deliverAdminOrder(orderNumber: string) {
  return apiFetch<OrderTransition>(
    `/api/v1/admin/orders/${encodeURIComponent(orderNumber)}/deliver`,
    {
      method: "POST",
      headers: mutationHeaders(crypto.randomUUID()),
    }
  );
}

export function failDeliveryAdminOrder(orderNumber: string, reason: string) {
  return apiFetch<OrderTransition>(
    `/api/v1/admin/orders/${encodeURIComponent(orderNumber)}/failed-delivery`,
    {
      method: "POST",
      headers: mutationHeaders(crypto.randomUUID()),
      body: JSON.stringify({ reason }),
    }
  );
}

export function completeAdminOrder(orderNumber: string) {
  return apiFetch<OrderTransition>(
    `/api/v1/admin/orders/${encodeURIComponent(orderNumber)}/complete`,
    {
      method: "POST",
      headers: mutationHeaders(crypto.randomUUID()),
    }
  );
}

export function getDeliveryStaffList() {
  return apiFetch<DeliveryStaff[]>("/api/v1/admin/delivery-staff");
}

export function createDeliveryStaff(input: {
  full_name: string;
  phone: string;
  vehicle_plate?: string | null;
}) {
  return apiFetch<DeliveryStaff>("/api/v1/admin/delivery-staff", {
    method: "POST",
    headers: mutationHeaders(),
    body: JSON.stringify(input),
  });
}

export function patchDeliveryStaff(
  staffId: number,
  input: {
    full_name?: string;
    phone?: string;
    vehicle_plate?: string | null;
    is_active?: boolean;
  }
) {
  return apiFetch<void>(
    `/api/v1/admin/delivery-staff/${encodeURIComponent(staffId)}`,
    {
      method: "PATCH",
      headers: mutationHeaders(),
      body: JSON.stringify(input),
    }
  );
}

export function getShipmentsList(status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<ShipmentDetail[]>(`/api/v1/admin/shipments${query}`);
}

export function getShipmentByOrderNumber(orderNumber: string) {
  return apiFetch<ShipmentDetail>(
    `/api/v1/admin/shipments/${encodeURIComponent(orderNumber)}`
  );
}

export function confirmStoreOrder(orderNumber: string) {
  return apiFetch<OrderTransition>(
    `/api/v1/admin/store/orders/${encodeURIComponent(orderNumber)}/confirm`,
    {
      method: "POST",
      headers: mutationHeaders(crypto.randomUUID()),
    }
  );
}

export function cancelStoreOrder(orderNumber: string, reason: string) {
  return apiFetch<OrderTransition>(
    `/api/v1/admin/store/orders/${encodeURIComponent(orderNumber)}/cancel`,
    {
      method: "POST",
      headers: mutationHeaders(crypto.randomUUID()),
      body: JSON.stringify({ reason }),
    }
  );
}

export function getStoreOrderDetail(orderNumber: string) {
  return apiFetch<CommerceOrderDetail>(
    `/api/v1/admin/store/orders/${encodeURIComponent(orderNumber)}`
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

export interface ReturnItemDetail {
  return_item_id: number;
  order_item_id: number;
  variant_id: number;
  product_name?: string | null;
  variant_title?: string | null;
  sku?: string | null;
  quantity: number;
  refund_amount_vnd: number;
  inspection_status: "pending" | "passed" | "failed";
}

export interface ReturnRequestDetail {
  return_id: number;
  return_code: string;
  order_id: number;
  order_number: string;
  customer_name?: string | null;
  customer_phone?: string | null;
  customer_email?: string | null;
  action_type: string;
  status: "pending_review" | "approved" | "rejected" | "goods_received" | "completed" | "cancelled";
  customer_reason: string;
  admin_note?: string | null;
  image_urls?: string[];
  bank_info?: {
    bank_name: string;
    bank_account_number: string;
    bank_account_holder: string;
  } | null;
  total_refund_amount_vnd: number;
  created_at: string;
  reviewed_at?: string | null;
  resolved_at?: string | null;
  items: ReturnItemDetail[];
}

export interface ReturnRequestSummary {
  return_id?: number;
  return_code: string;
  order_number?: string;
  action_type: string;
  status: "pending_review" | "approved" | "rejected" | "goods_received" | "completed" | "cancelled";
  total_items_count?: number;
  total_refund_amount_vnd: number;
  created_at: string;
}

export interface ReturnRequestList {
  items: ReturnRequestSummary[];
  total: number;
}

export interface AdminReturnList {
  items: ReturnRequestDetail[];
  total: number;
}

export interface CreateReturnItemInput {
  order_item_id: number;
  quantity: number;
}

export interface CreateReturnRequestInput {
  customer_reason: string;
  bank_name: string;
  bank_account_number: string;
  bank_account_holder: string;
  image_urls?: string[];
  items: CreateReturnItemInput[];
}

export interface AdminInspectItemInput {
  return_item_id: number;
  inspection_status: "passed" | "failed";
}

export interface AdminInspectAndResolveInput {
  items: AdminInspectItemInput[];
  admin_note?: string | null;
}

export function createCustomerReturnRequest(
  orderNumber: string,
  input: CreateReturnRequestInput,
  idempotencyKey: string
) {
  return apiFetch<ReturnRequestDetail>(
    `/api/v1/orders/${encodeURIComponent(orderNumber)}/returns`,
    {
      method: "POST",
      headers: mutationHeaders(idempotencyKey),
      body: JSON.stringify(input),
    }
  );
}

export function getCustomerReturnsList() {
  return apiFetch<ReturnRequestList>("/api/v1/returns");
}

export function getCustomerReturnDetail(returnCode: string) {
  return apiFetch<ReturnRequestDetail>(
    `/api/v1/returns/${encodeURIComponent(returnCode)}`
  );
}

export function cancelCustomerReturnRequest(returnCode: string) {
  return apiFetch<ReturnRequestDetail>(
    `/api/v1/returns/${encodeURIComponent(returnCode)}/cancel`,
    {
      method: "POST",
      headers: mutationHeaders(),
    }
  );
}

export function getAdminReturnsList(params?: {
  status?: string;
  search?: string;
  limit?: number;
  offset?: number;
}) {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set("status", params.status);
  if (params?.search) searchParams.set("search", params.search);
  if (params?.limit !== undefined) searchParams.set("limit", String(params.limit));
  if (params?.offset !== undefined) searchParams.set("offset", String(params.offset));
  const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return apiFetch<AdminReturnList>(`/api/v1/admin/returns${query}`);
}

export function getAdminReturnDetail(returnCode: string) {
  return apiFetch<ReturnRequestDetail>(
    `/api/v1/admin/returns/${encodeURIComponent(returnCode)}`
  );
}

export function reviewAdminReturn(
  returnCode: string,
  action: "approved" | "rejected",
  admin_note?: string
) {
  return apiFetch<ReturnRequestDetail>(
    `/api/v1/admin/returns/${encodeURIComponent(returnCode)}/review`,
    {
      method: "POST",
      headers: mutationHeaders(),
      body: JSON.stringify({ action, admin_note: admin_note ?? null }),
    }
  );
}

export function receiveAdminReturn(returnCode: string) {
  return apiFetch<ReturnRequestDetail>(
    `/api/v1/admin/returns/${encodeURIComponent(returnCode)}/receive`,
    {
      method: "POST",
      headers: mutationHeaders(),
    }
  );
}

export function inspectAndResolveAdminReturn(
  returnCode: string,
  input: AdminInspectAndResolveInput,
  idempotencyKey: string
) {
  return apiFetch<ReturnRequestDetail>(
    `/api/v1/admin/returns/${encodeURIComponent(returnCode)}/inspect-and-resolve`,
    {
      method: "POST",
      headers: mutationHeaders(idempotencyKey),
      body: JSON.stringify(input),
    }
  );
}

export interface AdminProductVariant {
  variant_id?: number;
  public_id: string;
  sku: string;
  size_code: string;
  color_code: string;
  price_vnd: number;
  cost_price_vnd?: number;
  is_active?: boolean;
  on_hand?: number;
}

export interface InboundReceiptItemDetail {
  item_id: number;
  variant_id: number;
  product_name: string;
  sku: string;
  size_code: string;
  color_code: string;
  quantity: number;
  unit_cost_vnd: number;
  total_cost_vnd: number;
  previous_cost_price_vnd: number;
  new_cost_price_vnd: number;
}

export interface InboundReceiptDetail {
  receipt_id: number;
  receipt_code: string;
  batch_name: string;
  status: string;
  total_items_count: number;
  total_cost_vnd: number;
  notes?: string | null;
  created_by_name?: string | null;
  created_at: string;
  items: InboundReceiptItemDetail[];
}

export interface InboundReceiptSummary {
  receipt_id: number;
  receipt_code: string;
  batch_name: string;
  status: string;
  total_items_count: number;
  total_cost_vnd: number;
  created_by_name?: string | null;
  created_at: string;
}

export interface InboundReceiptListResponse {
  items: InboundReceiptSummary[];
  total: number;
  total_items_count?: number;
  total_cost_vnd?: number;
}

export interface CreateInboundReceiptItemInput {
  variant_id: number;
  quantity: number;
  unit_cost_vnd: number;
}

export interface CreateInboundReceiptInput {
  batch_name: string;
  notes?: string | null;
  items: CreateInboundReceiptItemInput[];
}

export function getAdminInboundReceipts(params?: {
  search?: string;
  limit?: number;
  offset?: number;
}) {
  const searchParams = new URLSearchParams();
  if (params?.search) searchParams.set("search", params.search);
  if (params?.limit !== undefined) searchParams.set("limit", String(params.limit));
  if (params?.offset !== undefined) searchParams.set("offset", String(params.offset));
  const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
  return apiFetch<InboundReceiptListResponse>(`/api/v1/admin/inbound/receipts${query}`);
}

export function getAdminInboundReceiptDetail(receiptCode: string) {
  return apiFetch<InboundReceiptDetail>(
    `/api/v1/admin/inbound/receipts/${encodeURIComponent(receiptCode)}`
  );
}

export function createAdminInboundReceipt(
  input: CreateInboundReceiptInput,
  idempotencyKey: string
) {
  return apiFetch<InboundReceiptDetail>("/api/v1/admin/inbound/receipts", {
    method: "POST",
    headers: mutationHeaders(idempotencyKey),
    body: JSON.stringify(input),
  });
}

export interface AdminOverview {
  active_products: number;
  active_variants: number;
  low_stock_variants: number;
  customers: number;
  paid_orders: number;
  confirmed_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  total_reviews: number;
  active_coupons: number;
  gross_revenue_vnd: number;
  refunded_amount_vnd: number;
  net_revenue_vnd: number;
  cogs_vnd?: number;
  gross_profit_vnd?: number;
  gross_margin_percent?: number;
  boom_orders_count?: number;
  return_orders_count?: number;
}

export interface ExecutiveMetricsResponse {
  role: "executive";
  gmv_vnd: number;
  net_revenue_vnd: number;
  cogs_vnd: number;
  gross_profit_vnd: number;
  gross_margin_percent: number;
  total_orders: number;
  aov_vnd: number;
  boom_rate_percent: number;
  return_rate_percent: number;
}

export interface StoreContribution {
  store_id: number | null;
  store_name: string;
  revenue_vnd: number;
  order_count: number;
}

export interface TopProductMetric {
  product_id: number;
  product_name: string;
  units_sold: number;
  revenue_vnd: number;
}

export interface CategoryShareMetric {
  category_id: number;
  category_name: string;
  revenue_vnd: number;
  share_percent: number;
}

export interface SalesMetricsResponse {
  role: "sales";
  store_contributions: StoreContribution[];
  top_selling_products: TopProductMetric[];
  category_shares: CategoryShareMetric[];
}

export interface FunnelStep {
  step_name: string;
  count: number;
  conversion_rate_percent: number;
}

export interface MarketingMetricsResponse {
  role: "marketing";
  funnel_steps: FunnelStep[];
  conversion_rate_percent: number;
  total_visitors: number;
  total_purchases: number;
}

export interface StoreMetricsResponse {
  role: "store";
  store_id: number | null;
  store_name: string | null;
  store_revenue_today_vnd: number;
  store_orders_count: number;
  target_achievement_percent: number;
  low_stock_at_store_count: number;
}

export interface InventoryMetricsResponse {
  role: "inventory";
  total_inventory_value_vnd: number;
  warehouse_stock_units: number;
  store_stock_units: number;
  inbound_batches_count: number;
  stockout_count: number;
}

export interface OperationsMetricsResponse {
  role: "operations";
  pending_fulfillment_count: number;
  shipping_sla_violations_count: number;
  boom_orders_count: number;
  return_requests_count: number;
}

export interface ReconciliationVariance {
  metric_name: string;
  oltp_value: number;
  lakehouse_value: number;
  variance_percent: number;
}

export interface SystemMetricsResponse {
  role: "system";
  pipeline_status: string;
  data_freshness_sla_minutes: number;
  reconciliation_variance: ReconciliationVariance[];
}

export type RoleMetricsResponse =
  | ExecutiveMetricsResponse
  | SalesMetricsResponse
  | MarketingMetricsResponse
  | StoreMetricsResponse
  | InventoryMetricsResponse
  | OperationsMetricsResponse
  | SystemMetricsResponse;

export interface DailySalesTrendPoint {
  date: string;
  revenue_vnd: number;
  cogs_vnd: number;
  profit_vnd: number;
  orders_count: number;
}

export interface SalesTrendResponse {
  days: number;
  points: DailySalesTrendPoint[];
}

export interface SupersetConfigResponse {
  superset_url: string;
  enabled: boolean;
  guest_token_enabled: boolean;
}

export function getAdminRoleMetrics<T = RoleMetricsResponse>(role: string, storeId?: number): Promise<T> {
  const params = new URLSearchParams({ target_role: role });
  if (storeId !== undefined && storeId !== null) {
    params.set("store_id", String(storeId));
  }
  return apiFetch<T>(`/api/v1/admin/analytics/role-metrics?${params.toString()}`);
}

export function getAdminSalesTrend(days: number = 30): Promise<SalesTrendResponse> {
  return apiFetch<SalesTrendResponse>(`/api/v1/admin/analytics/sales-trend?days=${encodeURIComponent(days)}`);
}

export function getSupersetConfig(): Promise<SupersetConfigResponse> {
  return apiFetch<SupersetConfigResponse>("/api/v1/admin/analytics/superset-config");
}

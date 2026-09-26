import { ApiError, apiFetch } from "./api-client";
import type { DeliveryStaff, ReturnRequestSummary, ShipmentDetail } from "./commerce";
import { publicConfig } from "./config";

export { ApiError };

export interface Customer {
  public_id: string;
  display_name: string;
  email: string;
  role:
    | "customer"
    | "admin"
    | "store_manager"
    | "sales_manager"
    | "marketing_manager"
    | "inventory_manager"
    | "operations_manager"
    | "system_admin"
    | (string & {});
  store_id?: number | null;
  store_name?: string | null;
  is_cod_blocked?: boolean;
  boom_count?: number;
}

export interface Category {
  public_id: string;
  code: string;
  name: string;
  parent_code: string | null;
}

export interface ProductListItem {
  public_id: string;
  slug: string;
  name: string;
  image_url: string | null;
  category_code: string;
  min_price_vnd: number | null;
  in_stock: boolean;
}

export interface ProductListResponse {
  items: ProductListItem[];
  next_cursor: string | null;
}

export interface CatalogFacets {
  sizes: string[];
  colors: string[];
  min_price_vnd: number | null;
  max_price_vnd: number | null;
}

export type ProductSort = "newest" | "price_asc" | "price_desc";

export interface Variant {
  public_id: string;
  sku: string;
  size_code: string;
  color_code: string;
  price_vnd: number;
  cost_price_vnd?: number;
  stock_quantity: number;
  in_stock: boolean;
}

export interface ProductDetail {
  public_id: string;
  slug: string;
  name: string;
  description: string | null;
  image_url: string | null;
  category_code: string;
  category_name: string;
  variants: Variant[];
}

export interface WishlistItem {
  product_public_id: string;
  slug: string;
  name: string;
  image_url: string | null;
  category_code: string;
  min_price_vnd: number | null;
  in_stock: boolean;
  is_available: boolean;
  first_added_at: string;
  last_added_at: string;
}

export interface Wishlist {
  items: WishlistItem[];
}

export interface CartItem {
  variant_public_id: string;
  product_public_id?: string | null;
  product_name: string;
  slug: string;
  sku: string;
  size_code: string;
  color_code: string;
  image_url: string | null;
  unit_price_vnd: number;
  quantity: number;
  line_total_vnd: number;
  in_stock: boolean;
}

export interface Cart {
  public_id: string | null;
  items: CartItem[];
  subtotal_vnd: number;
  shipping_fee_vnd: number;
  free_shipping_threshold_vnd: number;
  total_vnd: number;
}

export interface CheckoutResult {
  order_number: string;
  status: string;
  payment_status: string;
  failure_code: string | null;
  subtotal_vnd: number;
  shipping_fee_vnd: number;
  total_vnd: number;
  payment_method?: string | null;
}

export interface OrderListPreviewItem {
  product_name: string;
  image_url: string | null;
  sku: string;
  size_code: string;
  color_code: string;
  quantity: number;
  line_total_vnd: number;
}

export interface OrderListItem {
  order_number: string;
  status: string;
  total_vnd: number;
  item_count: number;
  created_at: string;
  preview_items: OrderListPreviewItem[];
}

export interface OrderListResponse {
  items: OrderListItem[];
  next_cursor: string | null;
}

export interface OrderItem {
  product_name: string;
  sku: string;
  size_code: string;
  color_code: string;
  unit_price_vnd: number;
  quantity: number;
  line_total_vnd: number;
}

export interface OrderPayment {
  payment_reference: string;
  status: string;
  amount_vnd: number;
  failure_code: string | null;
  attempted_at: string;
}

export interface OrderStatusHistoryEntry {
  from_status: string | null;
  to_status: string;
  transition_source: string;
  transitioned_at: string;
}

export interface OrderDetail {
  order_number: string;
  status: string;
  currency_code: string;
  subtotal_vnd: number;
  shipping_fee_vnd: number;
  total_vnd: number;
  receiver_name: string;
  receiver_phone: string;
  shipping_address_text: string;
  created_at: string;
  paid_at: string | null;
  completed_at: string | null;
  payment_method?: string | null;
  items: OrderItem[];
  payment: OrderPayment | null;
  refund?: {
    public_id?: string;
    status: string;
    amount_vnd: number;
    reason?: string;
    created_at?: string;
    completed_at?: string | null;
  } | null;
  active_return?: ReturnRequestSummary | null;
  status_history: OrderStatusHistoryEntry[];
  shipment?: ShipmentDetail | null;
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

export interface AdminVariant {
  variant_id?: number;
  public_id: string;
  sku: string;
  size_code: string;
  color_code: string;
  price_vnd: number;
  cost_price_vnd?: number;
  is_active: boolean;
  on_hand: number;
}

export interface AdminProduct {
  public_id: string;
  category_code: string;
  slug: string;
  name: string;
  description: string | null;
  image_url: string | null;
  is_active: boolean;
  archived_at: string | null;
  archive_reason: string | null;
  variants: AdminVariant[];
}

export interface AdminOrder {
  order_number: string;
  customer_name: string;
  customer_email: string;
  status: string;
  total_vnd: number;
  item_count: number;
  created_at: string;
  channel: string;
  payment_method?: string;
}

export interface AdminCustomer {
  public_id: string;
  display_name: string;
  email: string;
  status: "active" | "inactive";
  role: "customer" | "admin" | "store_manager";
  created_at: string;
}

export interface CreateAdminProductInput {
  category_code: string;
  slug: string;
  name: string;
  description?: string | null;
  image_url?: string | null;
  variants: Array<{
    sku: string;
    size_code: string;
    color_code: string;
    price_vnd: number;
    opening_on_hand: number;
  }>;
}

const CSRF_COOKIE = publicConfig.csrfCookieName;

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

function csrfHeaders(extra?: HeadersInit): HeadersInit {
  const token = readCookie(CSRF_COOKIE);
  return { ...(token ? { "X-CSRF-Token": token } : {}), ...extra };
}

export function register(input: { email: string; password: string; display_name: string }) {
  return apiFetch<Customer>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function login(input: { email: string; password: string }) {
  return apiFetch<Customer>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function logout(): Promise<void> {
  await apiFetch<void>("/api/v1/auth/logout", {
    method: "POST",
    headers: csrfHeaders(),
  });
}

export function getMe() {
  return apiFetch<Customer>("/api/v1/auth/me");
}

export function getCategories() {
  return apiFetch<Category[]>("/api/v1/categories");
}

export interface ProductQuery {
  category?: string;
  q?: string;
  sizes?: string[];
  colors?: string[];
  minPrice?: number;
  maxPrice?: number;
  inStock?: boolean;
  sort?: ProductSort;
  cursor?: string;
}

export function getCatalogFacets() {
  return apiFetch<CatalogFacets>("/api/v1/catalog/facets");
}

export function getProducts(params?: ProductQuery) {
  const query = new URLSearchParams();
  if (params?.category) query.set("category", params.category);
  if (params?.q) query.set("q", params.q);
  params?.sizes?.forEach((value) => query.append("size", value));
  params?.colors?.forEach((value) => query.append("color", value));
  if (params?.minPrice !== undefined) query.set("min_price", String(params.minPrice));
  if (params?.maxPrice !== undefined) query.set("max_price", String(params.maxPrice));
  if (params?.inStock) query.set("in_stock", "true");
  if (params?.sort) query.set("sort", params.sort);
  if (params?.cursor) query.set("cursor", params.cursor);
  const qs = query.toString();
  return apiFetch<ProductListResponse>(`/api/v1/products${qs ? `?${qs}` : ""}`);
}

export function getProduct(slug: string) {
  return apiFetch<ProductDetail>(`/api/v1/products/${encodeURIComponent(slug)}`);
}

export function getWishlist() {
  return apiFetch<Wishlist>("/api/v1/wishlist");
}

export function addWishlistProduct(productPublicId: string) {
  return apiFetch<void>(`/api/v1/wishlist/products/${encodeURIComponent(productPublicId)}`, {
    method: "PUT",
    headers: csrfHeaders(),
  });
}

export function removeWishlistProduct(productPublicId: string) {
  return apiFetch<void>(`/api/v1/wishlist/products/${encodeURIComponent(productPublicId)}`, {
    method: "DELETE",
    headers: csrfHeaders(),
  });
}

export function getCart() {
  return apiFetch<Cart>("/api/v1/cart");
}

export function setCartItem(variantPublicId: string, quantity: number) {
  return apiFetch<Cart>(`/api/v1/cart/items/${encodeURIComponent(variantPublicId)}`, {
    method: "PUT",
    headers: csrfHeaders(),
    body: JSON.stringify({ quantity }),
  });
}

export function removeCartItem(variantPublicId: string) {
  return apiFetch<Cart>(`/api/v1/cart/items/${encodeURIComponent(variantPublicId)}`, {
    method: "DELETE",
    headers: csrfHeaders(),
  });
}

export function checkout(
  idempotencyKey: string,
  input: {
    receiver_name: string;
    receiver_phone: string;
    shipping_address_text: string;
    payment_method?: "vietqr" | "cod";
  }
) {
  return apiFetch<CheckoutResult>("/api/v1/checkout", {
    method: "POST",
    headers: csrfHeaders({ "Idempotency-Key": idempotencyKey }),
    body: JSON.stringify(input),
  });
}

export function getOrders(cursor?: string) {
  const qs = cursor ? `?cursor=${encodeURIComponent(cursor)}` : "";
  return apiFetch<OrderListResponse>(`/api/v1/orders${qs}`);
}

export function getOrder(orderNumber: string) {
  return apiFetch<OrderDetail>(`/api/v1/orders/${encodeURIComponent(orderNumber)}`);
}

export function getAdminOverview() {
  return apiFetch<AdminOverview>("/api/v1/admin/overview");
}

export function getAdminProducts(search?: string) {
  const query = search?.trim() ? `?search=${encodeURIComponent(search.trim())}` : "";
  return apiFetch<AdminProduct[]>(`/api/v1/admin/products${query}`);
}

export function createAdminProduct(input: CreateAdminProductInput) {
  return apiFetch<AdminProduct>("/api/v1/admin/products", {
    method: "POST",
    headers: csrfHeaders(),
    body: JSON.stringify(input),
  });
}

export function updateAdminProduct(
  publicId: string,
  input: Partial<Pick<AdminProduct, "category_code" | "name" | "description" | "image_url" | "is_active">>
) {
  return apiFetch<void>(`/api/v1/admin/products/${encodeURIComponent(publicId)}`, {
    method: "PATCH",
    headers: csrfHeaders(),
    body: JSON.stringify(input),
  });
}

export function archiveAdminProduct(publicId: string, reason: string) {
  return apiFetch<void>(`/api/v1/admin/products/${encodeURIComponent(publicId)}`, {
    method: "DELETE",
    headers: csrfHeaders(),
    body: JSON.stringify({ reason }),
  });
}

export function updateAdminVariant(
  publicId: string,
  input: { price_vnd?: number; is_active?: boolean }
) {
  return apiFetch<void>(`/api/v1/admin/variants/${encodeURIComponent(publicId)}`, {
    method: "PATCH",
    headers: csrfHeaders(),
    body: JSON.stringify(input),
  });
}

export function getAdminOrders(status?: string, channel?: string) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (channel) params.set("channel", channel);
  const query = params.toString() ? `?${params.toString()}` : "";
  return apiFetch<AdminOrder[]>(`/api/v1/admin/orders${query}`);
}

export function getAdminOrder(orderNumber: string) {
  return apiFetch<OrderDetail>(`/api/v1/admin/orders/${encodeURIComponent(orderNumber)}`);
}

export function getAdminCustomers() {
  return apiFetch<AdminCustomer[]>("/api/v1/admin/customers");
}

export function updateAdminCustomer(publicId: string, status: "active" | "inactive") {
  return apiFetch<void>(`/api/v1/admin/customers/${encodeURIComponent(publicId)}`, {
    method: "PATCH",
    headers: csrfHeaders(),
    body: JSON.stringify({ status }),
  });
}

export interface CityOption {
  code: string;
  name: string;
  store_count: number;
}

export async function getCities(): Promise<CityOption[]> {
  return apiFetch<CityOption[]>("/api/v1/locations/cities");
}

export interface StoreStock {
  store_code: string;
  store_name: string;
  variant_public_id: string;
  sku: string;
  size_code: string;
  color_code: string;
  price_vnd: number;
  on_hand: number;
}

export interface VariantAvailability {
  variant_public_id: string;
  sku: string;
  size_code: string;
  color_code: string;
  price_vnd: number;
  total_on_hand: number;
  in_stock: boolean;
  stores: StoreStock[];
}

export interface ProductAvailability {
  product_slug: string;
  product_name: string;
  variants: VariantAvailability[];
}

export async function getProductAvailability(slug: string, cityCode: string): Promise<ProductAvailability> {
  return apiFetch<ProductAvailability>(
    `/api/v1/catalog/products/${encodeURIComponent(slug)}/availability?city_code=${encodeURIComponent(cityCode)}`
  );
}

export function formatVnd(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return "—";
  return new Intl.NumberFormat("vi-VN").format(amount) + "₫";
}

const compactVndFormatter = new Intl.NumberFormat("vi-VN", {
  maximumFractionDigits: 1,
});

export function formatMetricVnd(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return "—";
  const absoluteAmount = Math.abs(amount);
  if (absoluteAmount >= 1_000_000_000_000) {
    return `${compactVndFormatter.format(amount / 1_000_000_000_000)} nghìn tỷ ₫`;
  }
  if (absoluteAmount >= 1_000_000_000) {
    return `${compactVndFormatter.format(amount / 1_000_000_000)} tỷ ₫`;
  }
  if (absoluteAmount >= 1_000_000) {
    return `${compactVndFormatter.format(amount / 1_000_000)} triệu ₫`;
  }
  return formatVnd(amount);
}

export type {
  AdminInspectAndResolveInput,
  AdminInspectItemInput,
  AdminProductVariant,
  AdminReturnList,
  CategoryShareMetric,
  CreateInboundReceiptInput,
  CreateInboundReceiptItemInput,
  CreateReturnItemInput,
  CreateReturnRequestInput,
  DailySalesTrendPoint,
  DeliveryStaff,
  ExecutiveMetricsResponse,
  FunnelStep,
  InboundReceiptDetail,
  InboundReceiptItemDetail,
  InboundReceiptListResponse,
  InboundReceiptSummary,
  InventoryMetricsResponse,
  MarketingMetricsResponse,
  OperationsMetricsResponse,
  ReconciliationVariance,
  ReturnItemDetail,
  ReturnRequestDetail,
  ReturnRequestList,
  ReturnRequestSummary,
  RoleMetricsResponse,
  SalesMetricsResponse,
  SalesTrendResponse,
  ShipmentDetail,
  StoreContribution,
  StoreMetricsResponse,
  SystemMetricsResponse,
  TopProductMetric,
} from "./commerce";
export {
  getDeliveryStaffList,
  createDeliveryStaff,
  patchDeliveryStaff,
  getShipmentsList,
  getShipmentByOrderNumber,
  dispatchAdminOrder,
  deliverAdminOrder,
  failDeliveryAdminOrder,
  completeAdminOrder,
  createCustomerReturnRequest,
  getCustomerReturnsList,
  getCustomerReturnDetail,
  cancelCustomerReturnRequest,
  getAdminReturnsList,
  getAdminReturnDetail,
  reviewAdminReturn,
  receiveAdminReturn,
  inspectAndResolveAdminReturn,
  getAdminInboundReceipts,
  getAdminInboundReceiptDetail,
  createAdminInboundReceipt,
  getAdminRoleMetrics,
  getAdminSalesTrend,
} from "./commerce";


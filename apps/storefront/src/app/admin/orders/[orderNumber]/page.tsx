"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AdminModal } from "@/components/admin/AdminModal";
import {
  OrderStatusBadge,
  ShipmentStatusBadge,
  orderStatusShortLabel,
} from "@/components/OrderStatusBadge";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd } from "@/lib/api";
import {
  cancelAdminOrder,
  completeAdminOrder,
  confirmAdminOrder,
  deliverAdminOrder,
  dispatchAdminOrder,
  failDeliveryAdminOrder,
  getAdminCommerceOrder,
  getDeliveryStaffList,
  getShipmentByOrderNumber,
  type CommerceOrderDetail,
  type DeliveryStaff,
  type ShipmentDetail,
} from "@/lib/commerce";
import { formatVietnamDateTime } from "@/lib/datetime";

export default function AdminOrderDetailPage() {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const [order, setOrder] = useState<CommerceOrderDetail | null>(null);
  const [shipment, setShipment] = useState<ShipmentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Modals state
  const [isCancelOpen, setIsCancelOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("Cửa hàng không thể xử lý đơn");

  const [isDispatchOpen, setIsDispatchOpen] = useState(false);
  const [staffList, setStaffList] = useState<DeliveryStaff[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);
  const [staffError, setStaffError] = useState<string | null>(null);
  const [selectedStaffId, setSelectedStaffId] = useState<number | null>(null);
  const [dispatchNotes, setDispatchNotes] = useState("");

  const [isBoomOpen, setIsBoomOpen] = useState(false);
  const [boomReason, setBoomReason] = useState("Khách không nghe máy / từ chối nhận hàng");

  const load = useCallback(async () => {
    if (!orderNumber) return;
    setError(null);
    try {
      const orderData = await getAdminCommerceOrder(orderNumber);
      setOrder(orderData);
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không tải được đơn hàng"
      );
      return;
    }

    try {
      const shipmentData = await getShipmentByOrderNumber(orderNumber);
      setShipment(shipmentData);
    } catch {
      // 404 is normal if order is not yet dispatched
      setShipment(null);
    }
  }, [orderNumber]);

  useEffect(() => {
    void load();
  }, [load]);

  async function mutate(action: () => Promise<unknown>, fallbackMessage: string) {
    setBusy(true);
    setActionError(null);
    try {
      await action();
      await load();
    } catch (requestError) {
      setActionError(
        requestError instanceof ApiError
          ? requestError.message
          : fallbackMessage
      );
    } finally {
      setBusy(false);
    }
  }

  function handleConfirm() {
    if (!order) return;
    void mutate(
      () => confirmAdminOrder(order.order_number),
      "Không xác nhận được đơn hàng"
    );
  }

  function submitCancel() {
    if (!order || cancelReason.trim().length < 3) return;
    void mutate(
      async () => {
        await cancelAdminOrder(order.order_number, cancelReason.trim());
        setIsCancelOpen(false);
      },
      "Không hủy được đơn hàng"
    );
  }

  async function openDispatchModal() {
    setIsDispatchOpen(true);
    setDispatchNotes("");
    if (staffList.length === 0) {
      setLoadingStaff(true);
      setStaffError(null);
      try {
        const staff = await getDeliveryStaffList();
        setStaffList(staff);
        const active = staff.filter((s) => s.is_active);
        if (active.length > 0) {
          setSelectedStaffId(active[0].staff_id);
        } else {
          setSelectedStaffId(null);
        }
      } catch (err) {
        setStaffError(
          err instanceof ApiError
            ? err.message
            : "Không tải được danh sách nhân viên giao hàng"
        );
      } finally {
        setLoadingStaff(false);
      }
    } else {
      const active = staffList.filter((s) => s.is_active);
      if (
        active.length > 0 &&
        (!selectedStaffId || !active.some((s) => s.staff_id === selectedStaffId))
      ) {
        setSelectedStaffId(active[0].staff_id);
      }
    }
  }

  function submitDispatch() {
    if (!order || !selectedStaffId) return;
    void mutate(
      async () => {
        await dispatchAdminOrder(
          order.order_number,
          selectedStaffId,
          dispatchNotes.trim() || undefined
        );
        setIsDispatchOpen(false);
      },
      "Không xuất kho được đơn hàng"
    );
  }

  function handleDeliver() {
    if (!order) return;
    void mutate(
      () => deliverAdminOrder(order.order_number),
      "Không cập nhật được trạng thái giao thành công"
    );
  }

  function submitBoom() {
    if (!order || boomReason.trim().length === 0) return;
    void mutate(
      async () => {
        await failDeliveryAdminOrder(order.order_number, boomReason.trim());
        setIsBoomOpen(false);
      },
      "Không cập nhật được trạng thái giao thất bại"
    );
  }

  function handleComplete() {
    if (!order) return;
    void mutate(
      () => completeAdminOrder(order.order_number),
      "Không hoàn tất được đơn hàng"
    );
  }

  if (error) return <div className="feedback-error">{error}</div>;
  if (!order) return <div className="h-80 animate-pulse rounded-2xl bg-sand/60" />;

  const activeStaff = staffList.filter((s) => s.is_active);

  return (
    <section>
      <Link className="button-ghost -ml-3" href="/admin/orders">
        <Icon className="rotate-180" name="arrow-right" size={17} />
        Danh sách đơn
      </Link>

      <header className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="eyebrow">Order detail</p>
          <h1 className="admin-heading mt-2 break-all">{order.order_number}</h1>
          <p className="mt-2 text-sm text-muted">
            Tạo lúc {formatVietnamDateTime(order.created_at)}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <OrderStatusBadge status={order.status} />

          {order.status === "paid" ? (
            <>
              <button
                className="button-secondary px-4 text-danger"
                disabled={busy}
                onClick={() => {
                  setCancelReason("Cửa hàng không thể xử lý đơn");
                  setIsCancelOpen(true);
                }}
                type="button"
              >
                Hủy đơn
              </button>
              <button
                className="button-primary px-4"
                disabled={busy}
                onClick={handleConfirm}
                type="button"
              >
                <Icon name="check" size={16} />
                Xác nhận đơn
              </button>
            </>
          ) : null}

          {order.status === "confirmed" ? (
            <button
              className="button-primary px-4"
              disabled={busy}
              onClick={() => void openDispatchModal()}
              type="button"
            >
              <Icon name="truck" size={16} />
              Giao hàng
            </button>
          ) : null}

          {order.status === "shipping" ? (
            <>
              <button
                className="button-secondary px-4 text-danger"
                disabled={busy}
                onClick={() => {
                  setBoomReason("Khách không nghe máy / từ chối nhận hàng");
                  setIsBoomOpen(true);
                }}
                type="button"
              >
                <Icon name="alert" size={16} />
                Báo Boom hàng
              </button>
              <button
                className="button-primary px-4"
                disabled={busy}
                onClick={handleDeliver}
                type="button"
              >
                <Icon name="check" size={16} />
                Giao thành công
              </button>
            </>
          ) : null}

          {order.status === "delivered" ? (
            <button
              className="button-primary px-4"
              disabled={busy}
              onClick={handleComplete}
              type="button"
            >
              <Icon name="check" size={16} />
              Hoàn tất đơn
            </button>
          ) : null}
        </div>
      </header>

      {actionError ? <div className="feedback-error mt-5">{actionError}</div> : null}

      <div className="mt-6 grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="space-y-5">
          <article className="admin-panel">
            <div className="flex items-center justify-between border-b border-line pb-4">
              <div className="flex items-center gap-3">
                <Icon className="text-moss" name="package" />
                <h2 className="font-semibold">Sản phẩm</h2>
              </div>
              <span className="text-sm text-muted">{order.items.length} dòng</span>
            </div>
            <ul className="mt-2 divide-y divide-line">
              {order.items.map((item) => (
                <li
                  className="flex items-center justify-between gap-4 py-4 text-sm"
                  key={item.public_id}
                >
                  <span className="flex min-w-0 items-center gap-3">
                    <span className="relative flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-sand text-muted">
                      {item.image_url ? (
                        <Image
                          alt={item.product_name}
                          className="object-cover"
                          fill
                          sizes="56px"
                          src={item.image_url}
                        />
                      ) : (
                        <Icon name="package" size={18} />
                      )}
                    </span>
                    <span className="min-w-0">
                      <strong className="font-semibold">{item.product_name}</strong>
                      <span className="mt-1 block text-xs text-muted">
                        {item.sku} · {item.size_code}/{item.color_code} · SL {item.quantity}
                      </span>
                    </span>
                  </span>
                  <span className="shrink-0 font-semibold">{formatVnd(item.line_total_vnd)}</span>
                </li>
              ))}
            </ul>
            <dl className="ml-auto mt-3 max-w-sm space-y-2 border-t border-line pt-4 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted">Tạm tính</dt>
                <dd>{formatVnd(order.subtotal_vnd)}</dd>
              </div>
              {order.discount_amount_vnd > 0 ? (
                <div className="flex justify-between text-success">
                  <dt>Giảm giá {order.coupon_code}</dt>
                  <dd>−{formatVnd(order.discount_amount_vnd)}</dd>
                </div>
              ) : null}
              <div className="flex justify-between">
                <dt className="text-muted">Vận chuyển</dt>
                <dd>{formatVnd(order.shipping_fee_vnd)}</dd>
              </div>
              <div className="flex justify-between border-t border-line pt-3 text-lg font-semibold">
                <dt>Tổng</dt>
                <dd>{formatVnd(order.total_vnd)}</dd>
              </div>
            </dl>
          </article>

          <article className="admin-panel">
            <div className="flex items-center gap-3">
              <Icon className="text-moss" name="receipt" />
              <h2 className="font-semibold">Lịch sử trạng thái</h2>
            </div>
            <ol className="mt-5 space-y-4">
              {order.status_history.map((history, index) => (
                <li
                  className="grid grid-cols-[1.5rem_minmax(0,1fr)] gap-3"
                  key={`${history.transitioned_at}-${index}`}
                >
                  <span className="mt-1 flex h-6 w-6 items-center justify-center rounded-full bg-moss text-white">
                    <Icon name="check" size={13} />
                  </span>
                  <div className="rounded-xl border border-line bg-paper p-3">
                    <div className="flex flex-wrap justify-between gap-2">
                      <strong className="text-sm">
                        {orderStatusShortLabel(history.to_status)}
                      </strong>
                      <time className="text-xs text-muted">
                        {formatVietnamDateTime(history.transitioned_at)}
                      </time>
                    </div>
                    {history.reason ? (
                      <p className="mt-2 text-sm text-muted">{history.reason}</p>
                    ) : null}
                  </div>
                </li>
              ))}
            </ol>
          </article>
        </div>

        <aside className="space-y-5 xl:sticky xl:top-24">
          {/* Card Thông tin Vận chuyển */}
          {shipment ? (
            <article className="admin-panel">
              <div className="flex items-center justify-between border-b border-line pb-3">
                <div className="flex items-center gap-3">
                  <Icon className="text-moss" name="truck" />
                  <h2 className="font-semibold">Thông tin Vận chuyển</h2>
                </div>
                <ShipmentStatusBadge status={shipment.status} />
              </div>
              <div className="mt-4 space-y-3 text-sm">
                <div>
                  <p className="text-xs text-muted">Mã vận đơn</p>
                  <p className="font-mono font-semibold">{shipment.shipment_code}</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Shipper phụ trách</p>
                  <p className="font-medium text-ink">
                    {shipment.delivery_staff_name || "Chưa gán"}
                  </p>
                  {shipment.delivery_staff_phone ? (
                    <p className="text-xs text-muted">
                      SĐT:{" "}
                      <a
                        className="text-accent hover:underline"
                        href={`tel:${shipment.delivery_staff_phone}`}
                      >
                        {shipment.delivery_staff_phone}
                      </a>
                    </p>
                  ) : null}
                  {shipment.vehicle_plate ? (
                    <p className="text-xs text-muted">Biển số xe: {shipment.vehicle_plate}</p>
                  ) : null}
                </div>
                <div>
                  <p className="text-xs text-muted">Tiền COD</p>
                  <p className="font-semibold">
                    {formatVnd(shipment.cod_amount_vnd)}
                    {shipment.cod_collected_vnd > 0 ? (
                      <span className="ml-2 text-xs font-normal text-success">
                        (Đã thu: {formatVnd(shipment.cod_collected_vnd)})
                      </span>
                    ) : null}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted">Số lần giao hàng</p>
                  <p className="font-medium">{shipment.attempt_count} lần</p>
                </div>
                {shipment.dispatched_at ? (
                  <div>
                    <p className="text-xs text-muted">Thời gian xuất kho</p>
                    <p className="text-xs">{formatVietnamDateTime(shipment.dispatched_at)}</p>
                  </div>
                ) : null}
                {shipment.delivered_at ? (
                  <div>
                    <p className="text-xs text-muted">Thời gian giao thành công</p>
                    <p className="text-xs text-success">
                      {formatVietnamDateTime(shipment.delivered_at)}
                    </p>
                  </div>
                ) : null}
                {shipment.failed_at ? (
                  <div>
                    <p className="text-xs text-muted">Thời gian giao thất bại</p>
                    <p className="text-xs text-danger">
                      {formatVietnamDateTime(shipment.failed_at)}
                    </p>
                  </div>
                ) : null}
                {shipment.failure_reason ? (
                  <div className="rounded-xl border border-danger/20 bg-danger/5 p-3 text-xs text-danger">
                    <p className="font-semibold">Lý do thất bại:</p>
                    <p className="mt-1">{shipment.failure_reason}</p>
                  </div>
                ) : null}
                {shipment.notes ? (
                  <div className="rounded-xl border border-line bg-paper p-3 text-xs text-muted">
                    <p className="font-medium text-ink">Ghi chú giao hàng:</p>
                    <p className="mt-1">{shipment.notes}</p>
                  </div>
                ) : null}
              </div>
            </article>
          ) : order.status === "confirmed" ? (
            <article className="admin-panel">
              <div className="flex items-center gap-3 border-b border-line pb-3">
                <Icon className="text-muted" name="truck" />
                <h2 className="font-semibold">Thông tin Vận chuyển</h2>
              </div>
              <p className="mt-3 text-sm text-muted">
                Đơn hàng đã được xác nhận và đang chờ xuất kho. Bấm &ldquo;Giao hàng&rdquo; ở trên
                để chỉ định shipper.
              </p>
            </article>
          ) : null}

          {/* Card Giao hàng */}
          <article className="admin-panel">
            <div className="flex items-center gap-3">
              <Icon className="text-moss" name="truck" />
              <h2 className="font-semibold">Địa chỉ nhận hàng</h2>
            </div>
            <p className="mt-4 font-semibold">{order.receiver_name}</p>
            <p className="mt-1 text-sm text-muted">{order.receiver_phone}</p>
            <p className="mt-3 text-sm leading-6 text-muted">{order.shipping_address_text}</p>
          </article>

          {/* Card Thanh toán */}
          {order.payment ? (
            <article className="admin-panel">
              <div className="flex items-center gap-3">
                <Icon className="text-moss" name="shield" />
                <h2 className="font-semibold">Thanh toán</h2>
              </div>
              <p className="mt-4 break-all text-sm font-semibold">
                {order.payment.payment_reference}
              </p>
              <p className="mt-2 text-sm text-muted">
                {order.payment.status} · {formatVnd(order.payment.amount_vnd)}
              </p>
              {order.payment_method ? (
                <p className="mt-1 text-xs text-muted">
                  Hình thức:{" "}
                  {order.payment_method === "cod"
                    ? "Thanh toán khi nhận hàng (COD)"
                    : "Chuyển khoản VietQR"}
                </p>
              ) : null}
              {order.refund ? (
                <p className="feedback-error mt-4">
                  Đã hoàn {formatVnd(order.refund.amount_vnd)} · {order.refund.reason}
                </p>
              ) : null}
            </article>
          ) : null}
        </aside>
      </div>

      {/* Cancel Order Modal */}
      <AdminModal
        busy={busy}
        description={`Thao tác hủy đơn ${order.order_number} sẽ hoàn tiền và cập nhật tồn kho theo trạng thái thực tế.`}
        onClose={() => setIsCancelOpen(false)}
        open={isCancelOpen}
        title={`Hủy đơn hàng ${order.order_number}`}
      >
        <label className="field-label" htmlFor="admin-detail-cancel-reason">
          Lý do hủy <span className="text-danger">*</span>
          <input
            autoFocus
            className="form-control"
            id="admin-detail-cancel-reason"
            maxLength={500}
            onChange={(event) => setCancelReason(event.target.value)}
            value={cancelReason}
          />
        </label>
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="button-ghost"
            disabled={busy}
            onClick={() => setIsCancelOpen(false)}
            type="button"
          >
            Bỏ qua
          </button>
          <button
            className="button-accent"
            disabled={cancelReason.trim().length < 3 || busy}
            onClick={submitCancel}
            type="button"
          >
            {busy ? "Đang hủy…" : "Xác nhận hủy"}
          </button>
        </div>
      </AdminModal>

      {/* Dispatch Order Modal */}
      <AdminModal
        busy={busy}
        description={`Chỉ định nhân viên giao hàng xuất kho cho đơn ${order.order_number}.`}
        onClose={() => setIsDispatchOpen(false)}
        open={isDispatchOpen}
        title={`Xuất kho & Giao hàng: ${order.order_number}`}
      >
        {loadingStaff ? (
          <div className="py-8 text-center text-sm text-muted">Đang tải danh sách shipper…</div>
        ) : staffError ? (
          <div className="feedback-error">{staffError}</div>
        ) : activeStaff.length === 0 ? (
          <div className="rounded-2xl border border-warning/20 bg-warning/5 p-4 text-sm text-warning">
            <p className="font-semibold">Chưa có shipper nào đang hoạt động</p>
            <p className="mt-1 text-muted">
              Vui lòng tạo hoặc kích hoạt nhân viên giao hàng tại trang{" "}
              <Link className="font-medium text-ink underline" href="/admin/logistics">
                Quản lý Vận chuyển
              </Link>
              .
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <label className="field-label" htmlFor="admin-detail-dispatch-staff">
              Nhân viên giao hàng <span className="text-danger">*</span>
              <select
                className="admin-input"
                id="admin-detail-dispatch-staff"
                onChange={(e) => setSelectedStaffId(Number(e.target.value))}
                value={selectedStaffId ?? ""}
              >
                {activeStaff.map((staff) => (
                  <option key={staff.staff_id} value={staff.staff_id}>
                    {staff.full_name} ({staff.phone}) {staff.vehicle_plate ? `· ${staff.vehicle_plate}` : ""}
                  </option>
                ))}
              </select>
            </label>
            <label className="field-label" htmlFor="admin-detail-dispatch-notes">
              Ghi chú giao hàng (không bắt buộc)
              <textarea
                className="form-control"
                id="admin-detail-dispatch-notes"
                maxLength={500}
                onChange={(e) => setDispatchNotes(e.target.value)}
                placeholder="Ví dụ: Giao giờ hành chính, gọi trước khi đến..."
                rows={3}
                value={dispatchNotes}
              />
            </label>
          </div>
        )}
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="button-ghost"
            disabled={busy}
            onClick={() => setIsDispatchOpen(false)}
            type="button"
          >
            Bỏ qua
          </button>
          <button
            className="button-primary"
            disabled={!selectedStaffId || busy || activeStaff.length === 0}
            onClick={submitDispatch}
            type="button"
          >
            <Icon name="truck" size={16} />
            {busy ? "Đang xuất kho…" : "Xác nhận giao hàng"}
          </button>
        </div>
      </AdminModal>

      {/* Boom / Failed Delivery Modal */}
      <AdminModal
        busy={busy}
        description={`Ghi nhận giao thất bại cho đơn ${order.order_number}. Hệ thống sẽ cập nhật trạng thái đơn sang "Giao thất bại" và tăng bộ đếm boom nếu thanh toán COD.`}
        onClose={() => setIsBoomOpen(false)}
        open={isBoomOpen}
        title={`Báo Boom hàng: ${order.order_number}`}
      >
        <label className="field-label" htmlFor="admin-detail-boom-reason">
          Lý do giao hàng thất bại <span className="text-danger">*</span>
          <input
            autoFocus
            className="form-control"
            id="admin-detail-boom-reason"
            maxLength={255}
            onChange={(e) => setBoomReason(e.target.value)}
            placeholder="Ví dụ: Khách không nghe máy, từ chối nhận hàng..."
            value={boomReason}
          />
        </label>
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="button-ghost"
            disabled={busy}
            onClick={() => setIsBoomOpen(false)}
            type="button"
          >
            Bỏ qua
          </button>
          <button
            className="button-accent"
            disabled={boomReason.trim().length === 0 || busy}
            onClick={submitBoom}
            type="button"
          >
            <Icon name="alert" size={16} />
            {busy ? "Đang cập nhật…" : "Xác nhận Boom hàng"}
          </button>
        </div>
      </AdminModal>
    </section>
  );
}

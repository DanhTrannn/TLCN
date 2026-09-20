"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AdminModal } from "@/components/admin/AdminModal";
import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { Icon } from "@/components/ui/Icon";
import {
  ApiError,
  formatVnd,
  getAdminOrders,
  type AdminOrder,
} from "@/lib/api";
import {
  cancelAdminOrder,
  completeAdminOrder,
  confirmAdminOrder,
  deliverAdminOrder,
  dispatchAdminOrder,
  failDeliveryAdminOrder,
  getDeliveryStaffList,
  type DeliveryStaff,
} from "@/lib/commerce";
import { formatVietnamDateTime } from "@/lib/datetime";

export default function AdminOrdersPage() {
  const [status, setStatus] = useState("");
  const [channelFilter, setChannelFilter] = useState<string>("all");
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyOrder, setBusyOrder] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Cancel modal state
  const [cancellingOrder, setCancellingOrder] = useState<string | null>(null);
  const [cancelReason, setCancelReason] = useState("Cửa hàng không thể xử lý đơn");

  // Dispatch modal state
  const [dispatchingOrder, setDispatchingOrder] = useState<string | null>(null);
  const [staffList, setStaffList] = useState<DeliveryStaff[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);
  const [staffError, setStaffError] = useState<string | null>(null);
  const [selectedStaffId, setSelectedStaffId] = useState<number | null>(null);
  const [dispatchNotes, setDispatchNotes] = useState("");

  // Boom modal state
  const [boomingOrder, setBoomingOrder] = useState<string | null>(null);
  const [boomReason, setBoomReason] = useState("Khách không nghe máy / từ chối nhận hàng");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setOrders(
        await getAdminOrders(
          status || undefined,
          channelFilter === "all" ? undefined : channelFilter
        )
      );
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không tải được đơn hàng"
      );
    } finally {
      setLoading(false);
    }
  }, [status, channelFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  async function mutate(
    orderNumber: string,
    action: () => Promise<unknown>,
    fallbackMessage: string
  ) {
    setBusyOrder(orderNumber);
    setError(null);
    try {
      await action();
      await load();
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : fallbackMessage
      );
    } finally {
      setBusyOrder(null);
    }
  }

  function handleOpenCancel(orderNumber: string) {
    setCancellingOrder(orderNumber);
    setCancelReason("Cửa hàng không thể xử lý đơn");
  }

  function submitCancel() {
    if (!cancellingOrder || cancelReason.trim().length < 3) return;
    const target = cancellingOrder;
    void mutate(
      target,
      async () => {
        await cancelAdminOrder(target, cancelReason.trim());
        setCancellingOrder(null);
      },
      "Không hủy được đơn hàng"
    );
  }

  async function handleOpenDispatch(orderNumber: string) {
    setDispatchingOrder(orderNumber);
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
      } catch (staffErr) {
        setStaffError(
          staffErr instanceof ApiError
            ? staffErr.message
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
    if (!dispatchingOrder || !selectedStaffId) return;
    const target = dispatchingOrder;
    void mutate(
      target,
      async () => {
        await dispatchAdminOrder(
          target,
          selectedStaffId,
          dispatchNotes.trim() || undefined
        );
        setDispatchingOrder(null);
      },
      "Không xuất kho được đơn hàng"
    );
  }

  function handleOpenBoom(orderNumber: string) {
    setBoomingOrder(orderNumber);
    setBoomReason("Khách không nghe máy / từ chối nhận hàng");
  }

  function submitBoom() {
    if (!boomingOrder || boomReason.trim().length === 0) return;
    const target = boomingOrder;
    void mutate(
      target,
      async () => {
        await failDeliveryAdminOrder(target, boomReason.trim());
        setBoomingOrder(null);
      },
      "Không cập nhật được trạng thái giao thất bại"
    );
  }

  function handleConfirm(orderNumber: string) {
    void mutate(
      orderNumber,
      () => confirmAdminOrder(orderNumber),
      "Không xác nhận được đơn hàng"
    );
  }

  function handleDeliver(orderNumber: string) {
    void mutate(
      orderNumber,
      () => deliverAdminOrder(orderNumber),
      "Không cập nhật được trạng thái giao thành công"
    );
  }

  function handleComplete(orderNumber: string) {
    void mutate(
      orderNumber,
      () => completeAdminOrder(orderNumber),
      "Không hoàn tất được đơn hàng"
    );
  }

  const activeStaff = staffList.filter((s) => s.is_active);

  return (
    <section>
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Order operations</p>
          <h1 className="admin-heading mt-2">Đơn hàng</h1>
          <p className="mt-2 text-sm leading-6 text-muted">
            Quản lý vòng đời đơn hàng: xác nhận, điều phối giao hàng, xử lý boom và hoàn tất đơn.
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <label className="field-label min-w-56" htmlFor="admin-order-status">
            Trạng thái
            <select
              className="admin-input"
              id="admin-order-status"
              onChange={(event) => setStatus(event.target.value)}
              value={status}
            >
              <option value="">Tất cả</option>
              <option value="paid">Chờ xác nhận (paid)</option>
              <option value="confirmed">Đã xác nhận · Chờ xuất kho (confirmed)</option>
              <option value="shipping">Đang giao hàng (shipping)</option>
              <option value="delivered">Đã giao hàng · Chờ hoàn tất (delivered)</option>
              <option value="failed_delivery">Giao thất bại / Boom (failed_delivery)</option>
              <option value="completed">Hoàn tất (completed)</option>
              <option value="cancelled">Đã hủy (cancelled)</option>
              <option value="payment_failed">Thanh toán lỗi (payment_failed)</option>
            </select>
          </label>
          <label className="field-label min-w-36" htmlFor="admin-order-channel">
            Kênh
            <select
              className="admin-input"
              id="admin-order-channel"
              onChange={(event) => setChannelFilter(event.target.value)}
              value={channelFilter}
            >
              <option value="all">Tất cả</option>
              <option value="online">Online</option>
              <option value="pos">POS</option>
            </select>
          </label>
        </div>
      </header>

      {error ? <div className="feedback-error mt-5">{error}</div> : null}

      {loading ? (
        <div className="mt-6 h-72 animate-pulse rounded-2xl bg-sand/60" />
      ) : (
        <div className="admin-table-shell mt-6">
          <table>
            <thead>
              <tr>
                <th>Đơn hàng</th>
                <th>Khách hàng</th>
                <th>Kênh</th>
                <th>Tổng tiền</th>
                <th>Trạng thái</th>
                <th className="text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => {
                const isBusy = busyOrder === order.order_number;

                return (
                  <tr key={order.order_number}>
                    <td>
                      <Link
                        className="font-semibold hover:text-accent"
                        href={`/admin/orders/${order.order_number}`}
                      >
                        {order.order_number}
                      </Link>
                      <p className="mt-1 text-xs text-muted">
                        {formatVietnamDateTime(order.created_at)} · {order.item_count} món
                      </p>
                    </td>
                    <td>
                      <p className="font-medium">{order.customer_name}</p>
                      <p className="text-xs text-muted">{order.customer_email}</p>
                    </td>
                    <td>
                      <span className="text-sm">
                        {order.channel === "pos" ? "POS" : "Online"}
                      </span>
                    </td>
                    <td className="font-semibold">{formatVnd(order.total_vnd)}</td>
                    <td>
                      <OrderStatusBadge status={order.status} />
                    </td>
                    <td>
                      <div className="flex flex-wrap items-center justify-end gap-2">
                        {order.status === "paid" ? (
                          <>
                            <button
                              className="button-secondary px-3 py-1.5 text-xs text-danger"
                              disabled={isBusy}
                              onClick={() => handleOpenCancel(order.order_number)}
                              type="button"
                            >
                              Hủy
                            </button>
                            <button
                              className="button-primary px-3 py-1.5 text-xs"
                              disabled={isBusy}
                              onClick={() => handleConfirm(order.order_number)}
                              type="button"
                            >
                              <Icon name="check" size={14} />
                              Xác nhận
                            </button>
                          </>
                        ) : null}

                        {order.status === "confirmed" ? (
                          <button
                            className="button-primary px-3 py-1.5 text-xs"
                            disabled={isBusy}
                            onClick={() => void handleOpenDispatch(order.order_number)}
                            type="button"
                          >
                            <Icon name="truck" size={14} />
                            Giao hàng
                          </button>
                        ) : null}

                        {order.status === "shipping" ? (
                          <>
                            <button
                              className="button-secondary px-3 py-1.5 text-xs text-danger"
                              disabled={isBusy}
                              onClick={() => handleOpenBoom(order.order_number)}
                              type="button"
                            >
                              <Icon name="alert" size={14} />
                              Báo Boom hàng
                            </button>
                            <button
                              className="button-primary px-3 py-1.5 text-xs"
                              disabled={isBusy}
                              onClick={() => handleDeliver(order.order_number)}
                              type="button"
                            >
                              <Icon name="check" size={14} />
                              Giao thành công
                            </button>
                          </>
                        ) : null}

                        {order.status === "delivered" ? (
                          <button
                            className="button-primary px-3 py-1.5 text-xs"
                            disabled={isBusy}
                            onClick={() => handleComplete(order.order_number)}
                            type="button"
                          >
                            <Icon name="check" size={14} />
                            Hoàn tất đơn
                          </button>
                        ) : null}

                        <Link
                          className="button-secondary px-3 py-1.5 text-xs"
                          href={`/admin/orders/${order.order_number}`}
                        >
                          Chi tiết
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {orders.length === 0 ? (
            <div className="p-10 text-center">
              <Icon className="mx-auto text-moss" name="receipt" size={24} />
              <p className="mt-3 text-muted">Không có đơn hàng phù hợp.</p>
            </div>
          ) : null}
        </div>
      )}

      {/* Cancel Order Modal */}
      <AdminModal
        busy={busyOrder === cancellingOrder}
        description={`Thao tác hủy đơn ${cancellingOrder} sẽ hoàn tiền và cập nhật tồn kho theo trạng thái thực tế.`}
        onClose={() => setCancellingOrder(null)}
        open={Boolean(cancellingOrder)}
        title={`Hủy đơn hàng ${cancellingOrder}`}
      >
        <label className="field-label" htmlFor="admin-cancel-reason">
          Lý do hủy <span className="text-danger">*</span>
          <input
            autoFocus
            className="form-control"
            id="admin-cancel-reason"
            maxLength={500}
            onChange={(event) => setCancelReason(event.target.value)}
            value={cancelReason}
          />
        </label>
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="button-ghost"
            disabled={busyOrder === cancellingOrder}
            onClick={() => setCancellingOrder(null)}
            type="button"
          >
            Bỏ qua
          </button>
          <button
            className="button-accent"
            disabled={cancelReason.trim().length < 3 || busyOrder === cancellingOrder}
            onClick={submitCancel}
            type="button"
          >
            {busyOrder === cancellingOrder ? "Đang hủy…" : "Xác nhận hủy"}
          </button>
        </div>
      </AdminModal>

      {/* Dispatch Order Modal */}
      <AdminModal
        busy={busyOrder === dispatchingOrder}
        description={`Chỉ định nhân viên giao hàng xuất kho cho đơn ${dispatchingOrder}. Đơn hàng sẽ chuyển sang trạng thái "Đang giao hàng".`}
        onClose={() => setDispatchingOrder(null)}
        open={Boolean(dispatchingOrder)}
        title={`Xuất kho & Giao hàng: ${dispatchingOrder}`}
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
            <label className="field-label" htmlFor="dispatch-staff-select">
              Nhân viên giao hàng <span className="text-danger">*</span>
              <select
                className="admin-input"
                id="dispatch-staff-select"
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
            <label className="field-label" htmlFor="dispatch-notes">
              Ghi chú giao hàng (không bắt buộc)
              <textarea
                className="form-control"
                id="dispatch-notes"
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
            disabled={busyOrder === dispatchingOrder}
            onClick={() => setDispatchingOrder(null)}
            type="button"
          >
            Bỏ qua
          </button>
          <button
            className="button-primary"
            disabled={
              !selectedStaffId ||
              busyOrder === dispatchingOrder ||
              activeStaff.length === 0
            }
            onClick={submitDispatch}
            type="button"
          >
            <Icon name="truck" size={16} />
            {busyOrder === dispatchingOrder ? "Đang xuất kho…" : "Xác nhận giao hàng"}
          </button>
        </div>
      </AdminModal>

      {/* Boom / Failed Delivery Modal */}
      <AdminModal
        busy={busyOrder === boomingOrder}
        description={`Ghi nhận giao thất bại cho đơn ${boomingOrder}. Hệ thống sẽ cập nhật trạng thái đơn sang "Giao thất bại" và tăng bộ đếm boom nếu thanh toán COD.`}
        onClose={() => setBoomingOrder(null)}
        open={Boolean(boomingOrder)}
        title={`Báo Boom hàng: ${boomingOrder}`}
      >
        <label className="field-label" htmlFor="boom-reason">
          Lý do giao hàng thất bại <span className="text-danger">*</span>
          <input
            autoFocus
            className="form-control"
            id="boom-reason"
            maxLength={255}
            onChange={(e) => setBoomReason(e.target.value)}
            placeholder="Ví dụ: Khách không nghe máy, từ chối nhận hàng..."
            value={boomReason}
          />
        </label>
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="button-ghost"
            disabled={busyOrder === boomingOrder}
            onClick={() => setBoomingOrder(null)}
            type="button"
          >
            Bỏ qua
          </button>
          <button
            className="button-accent"
            disabled={boomReason.trim().length === 0 || busyOrder === boomingOrder}
            onClick={submitBoom}
            type="button"
          >
            <Icon name="alert" size={16} />
            {busyOrder === boomingOrder ? "Đang cập nhật…" : "Xác nhận Boom hàng"}
          </button>
        </div>
      </AdminModal>
    </section>
  );
}

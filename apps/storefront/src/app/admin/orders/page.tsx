"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd, getAdminOrders, type AdminOrder } from "@/lib/api";
import { cancelAdminOrder, confirmAdminOrder } from "@/lib/commerce";
import { formatVietnamDateTime } from "@/lib/datetime";

export default function AdminOrdersPage() {
  const [status, setStatus] = useState("");
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyOrder, setBusyOrder] = useState<string | null>(null);
  const [cancellingOrder, setCancellingOrder] = useState<string | null>(null);
  const [cancelReason, setCancelReason] = useState("Cửa hàng không thể xử lý đơn");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setOrders(await getAdminOrders(status || undefined));
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Không tải được đơn hàng");
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => { void load(); }, [load]);

  async function mutate(orderNumber: string, action: () => Promise<unknown>, fallbackMessage: string) {
    setBusyOrder(orderNumber);
    setError(null);
    try {
      await action();
      setCancellingOrder(null);
      await load();
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : fallbackMessage);
    } finally {
      setBusyOrder(null);
    }
  }

  function submitCancel() {
    if (!cancellingOrder || cancelReason.trim().length < 3) return;
    void mutate(cancellingOrder, () => cancelAdminOrder(cancellingOrder, cancelReason.trim()), "Không hủy được đơn hàng");
  }

  return (
    <section>
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="eyebrow">Order operations</p><h1 className="admin-heading mt-2">Đơn hàng</h1><p className="mt-2 text-sm leading-6 text-muted">Xác nhận đơn đã thanh toán; khách hàng sẽ hoàn tất sau khi nhận hàng.</p></div>
        <label className="field-label min-w-52" htmlFor="admin-order-status">Trạng thái
          <select className="admin-input" id="admin-order-status" onChange={(event) => setStatus(event.target.value)} value={status}>
            <option value="">Tất cả</option><option value="paid">Chờ xác nhận</option><option value="payment_failed">Thanh toán lỗi</option><option value="confirmed">Đã xác nhận</option><option value="completed">Hoàn tất</option><option value="cancelled">Đã hủy</option>
          </select>
        </label>
      </header>

      {error ? <div className="feedback-error mt-5">{error}</div> : null}
      {cancellingOrder ? (
        <section className="mt-5 rounded-2xl border border-danger/20 bg-danger/5 p-5">
          <div className="flex items-center gap-3"><Icon className="text-danger" name="alert" /><div><h2 className="font-semibold">Hủy đơn {cancellingOrder}</h2><p className="text-sm text-muted">Thao tác sẽ hoàn tiền và cập nhật tồn kho theo trạng thái thực tế.</p></div></div>
          <label className="field-label mt-4" htmlFor="admin-cancel-reason">Lý do hủy<input autoFocus className="form-control" id="admin-cancel-reason" maxLength={500} onChange={(event) => setCancelReason(event.target.value)} value={cancelReason} /></label>
          <div className="mt-4 flex justify-end gap-2"><button className="button-ghost" onClick={() => setCancellingOrder(null)} type="button">Bỏ qua</button><button className="button-accent" disabled={cancelReason.trim().length < 3 || busyOrder === cancellingOrder} onClick={submitCancel} type="button">Xác nhận hủy</button></div>
        </section>
      ) : null}

      {loading ? (
        <div className="mt-6 h-72 animate-pulse rounded-2xl bg-sand/60" />
      ) : (
        <div className="admin-table-shell mt-6">
          <table>
            <thead><tr><th>Đơn hàng</th><th>Khách hàng</th><th>Tổng tiền</th><th>Trạng thái</th><th>Thao tác</th></tr></thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.order_number}>
                  <td><Link className="font-semibold hover:text-accent" href={`/admin/orders/${order.order_number}`}>{order.order_number}</Link><p className="mt-1 text-xs text-muted">{formatVietnamDateTime(order.created_at)} · {order.item_count} món</p></td>
                  <td><p className="font-medium">{order.customer_name}</p><p className="text-xs text-muted">{order.customer_email}</p></td>
                  <td className="font-semibold">{formatVnd(order.total_vnd)}</td>
                  <td><OrderStatusBadge status={order.status} /></td>
                  <td>
                    <div className="flex justify-end gap-2">
                      {order.status === "paid" ? <><button className="button-secondary px-4 text-danger" disabled={busyOrder === order.order_number} onClick={() => { setCancellingOrder(order.order_number); setCancelReason("Cửa hàng không thể xử lý đơn"); }} type="button">Hủy</button><button className="button-primary px-4" disabled={busyOrder === order.order_number} onClick={() => void mutate(order.order_number, () => confirmAdminOrder(order.order_number), "Không xác nhận được đơn hàng")} type="button"><Icon name="check" size={16} />Xác nhận</button></> : null}
                      {order.status !== "paid" ? <Link className="button-secondary px-4" href={`/admin/orders/${order.order_number}`}>Chi tiết</Link> : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {orders.length === 0 ? <div className="p-10 text-center"><Icon className="mx-auto text-moss" name="receipt" size={24} /><p className="mt-3 text-muted">Không có đơn hàng phù hợp.</p></div> : null}
        </div>
      )}
    </section>
  );
}

"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd } from "@/lib/api";
import { cancelStoreOrder, confirmStoreOrder } from "@/lib/commerce";
import { exportToCsv } from "@/lib/csv-export";
import { formatVietnamDateTime } from "@/lib/datetime";
import { apiFetch } from "@/lib/api-client";

interface StoreOrder {
  order_number: string;
  customer_name: string;
  customer_email: string;
  status: string;
  total_vnd: number;
  item_count: number;
  channel: string;
  created_at: string;
}

export default function StoreOrdersPage() {
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [orders, setOrders] = useState<StoreOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyOrder, setBusyOrder] = useState<string | null>(null);
  const [cancellingOrder, setCancellingOrder] = useState<string | null>(null);
  const [cancelReason, setCancelReason] = useState("Cửa hàng không thể xử lý đơn");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      const data = await apiFetch<StoreOrder[]>(`/api/v1/admin/store/orders?${params}`);
      setOrders(data);
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
    void mutate(cancellingOrder, () => cancelStoreOrder(cancellingOrder, cancelReason.trim()), "Không hủy được đơn hàng");
  }

  const filteredOrders = useMemo(() => {
    if (!search.trim()) return orders;
    const q = search.trim().toLowerCase();
    return orders.filter(
      (o) =>
        o.order_number.toLowerCase().includes(q) ||
        o.customer_name.toLowerCase().includes(q) ||
        o.customer_email.toLowerCase().includes(q)
    );
  }, [orders, search]);

  function handleExportCsv() {
    exportToCsv(
      `don_hang_cua_hang_${new Date().toISOString().slice(0, 10)}`,
      [
        "Mã đơn hàng",
        "Khách hàng",
        "Email",
        "Kênh",
        "Trạng thái",
        "Số món",
        "Tổng tiền (VNĐ)",
        "Ngày tạo",
      ],
      filteredOrders.map((o) => [
        o.order_number,
        o.customer_name,
        o.customer_email,
        o.channel || "pos",
        o.status,
        o.item_count,
        o.total_vnd,
        formatVietnamDateTime(o.created_at),
      ])
    );
  }

  return (
    <section>
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="admin-heading">Đơn hàng cửa hàng</h1>
          <p className="mt-2 text-sm leading-6 text-muted">Xác nhận đơn đã thanh toán; khách hàng sẽ hoàn tất sau khi nhận hàng.</p>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <div className="relative min-w-56">
            <span className="field-label">Tìm kiếm</span>
            <div className="relative mt-1">
              <Icon className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" name="search" size={15} />
              <input
                className="admin-input pl-9"
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Mã đơn, tên, email..."
                value={search}
              />
            </div>
          </div>
          <label className="field-label min-w-44" htmlFor="store-order-status">Trạng thái
            <select className="admin-input" id="store-order-status" onChange={(event) => setStatus(event.target.value)} value={status}>
              <option value="">Tất cả</option>
              <option value="paid">Chờ xác nhận</option>
              <option value="payment_failed">Thanh toán lỗi</option>
              <option value="confirmed">Đã xác nhận</option>
              <option value="completed">Hoàn tất</option>
              <option value="cancelled">Đã hủy</option>
            </select>
          </label>
          <button
            className="button-secondary inline-flex items-center gap-1.5 h-11 px-3.5 text-xs font-semibold"
            disabled={filteredOrders.length === 0}
            onClick={handleExportCsv}
            title="Xuất file CSV"
            type="button"
          >
            <Icon name="receipt" size={16} />
            <span>Xuất CSV</span>
          </button>
        </div>
      </header>

      {error ? <div className="feedback-error mt-5">{error}</div> : null}
      {cancellingOrder ? (
        <section className="mt-5 rounded-2xl border border-danger/20 bg-danger/5 p-5">
          <div className="flex items-center gap-3">
            <Icon className="text-danger" name="alert" />
            <div>
              <h2 className="font-semibold">Hủy đơn {cancellingOrder}</h2>
              <p className="text-sm text-muted">Thao tác sẽ hoàn tiền và cập nhật tồn kho theo trạng thái thực tế.</p>
            </div>
          </div>
          <label className="field-label mt-4" htmlFor="store-cancel-reason">Lý do hủy
            <input autoFocus className="form-control" id="store-cancel-reason" maxLength={500} onChange={(event) => setCancelReason(event.target.value)} value={cancelReason} />
          </label>
          <div className="mt-4 flex justify-end gap-2">
            <button className="button-ghost" onClick={() => setCancellingOrder(null)} type="button">Bỏ qua</button>
            <button className="button-accent" disabled={cancelReason.trim().length < 3 || busyOrder === cancellingOrder} onClick={submitCancel} type="button">Xác nhận hủy</button>
          </div>
        </section>
      ) : null}

      {loading ? (
        <div className="mt-6 h-72 animate-pulse rounded-2xl bg-sand/60" />
      ) : filteredOrders.length === 0 ? (
        <div className="admin-panel mt-6 text-center text-muted">
          <Icon className="mx-auto text-muted mb-2" name="receipt" size={24} />
          <p>{search ? "Không tìm thấy đơn hàng nào phù hợp với tìm kiếm." : "Chưa có đơn hàng nào."}</p>
        </div>
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
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.map((order) => (
                <tr key={order.order_number}>
                  <td>
                    <Link className="font-semibold hover:text-accent" href={`/store/orders/${order.order_number}`}>{order.order_number}</Link>
                    <p className="mt-1 text-xs text-muted">{formatVietnamDateTime(order.created_at)} · {order.item_count} món</p>
                  </td>
                  <td>
                    <p className="font-medium">{order.customer_name}</p>
                    <p className="text-xs text-muted">{order.customer_email}</p>
                  </td>
                  <td><span className="text-sm">{order.channel === "pos" ? "POS" : "Online"}</span></td>
                  <td className="font-semibold">{formatVnd(order.total_vnd)}</td>
                  <td><OrderStatusBadge status={order.status} /></td>
                  <td>
                    <div className="flex justify-end gap-2">
                      {order.status === "paid" ? (
                        <>
                          <button className="button-secondary px-4 text-danger" disabled={busyOrder === order.order_number} onClick={() => { setCancellingOrder(order.order_number); setCancelReason("Cửa hàng không thể xử lý đơn"); }} type="button">Hủy</button>
                          <button className="button-primary px-4" disabled={busyOrder === order.order_number} onClick={() => void mutate(order.order_number, () => confirmStoreOrder(order.order_number), "Không xác nhận được đơn hàng")} type="button"><Icon name="check" size={16} />Xác nhận</button>
                        </>
                      ) : null}
                      {order.status !== "paid" ? (
                        <Link className="button-secondary px-4" href={`/store/orders/${order.order_number}`}>Chi tiết</Link>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
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
    </section>
  );
}

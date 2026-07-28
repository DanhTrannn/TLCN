"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ApiError, completeAdminOrder, formatVnd, getAdminOrders, type AdminOrder } from "@/lib/api";

const labels: Record<string, string> = { paid: "Đã thanh toán", payment_failed: "Thanh toán lỗi", completed: "Hoàn tất" };

export default function AdminOrdersPage() {
  const [status, setStatus] = useState("");
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyOrder, setBusyOrder] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setOrders(await getAdminOrders(status || undefined)); }
    catch (err) { setError(err instanceof ApiError ? err.message : "Không tải được đơn hàng"); }
    finally { setLoading(false); }
  }, [status]);

  useEffect(() => { void load(); }, [load]);

  async function complete(orderNumber: string) {
    setBusyOrder(orderNumber); setError(null);
    try { await completeAdminOrder(orderNumber); await load(); }
    catch (err) { setError(err instanceof ApiError ? err.message : "Không hoàn tất được đơn hàng"); }
    finally { setBusyOrder(null); }
  }

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div><h2 className="text-xl font-semibold">Đơn hàng</h2><p className="mt-1 text-sm text-ink/60">Theo dõi và xác nhận hoàn tất đơn đã thanh toán.</p></div>
        <label className="text-sm">Trạng thái<select className="admin-input min-w-48" onChange={(e) => setStatus(e.target.value)} value={status}><option value="">Tất cả</option><option value="paid">Đã thanh toán</option><option value="payment_failed">Thanh toán lỗi</option><option value="completed">Hoàn tất</option></select></label>
      </div>
      {error ? <p className="mt-5 text-sm text-accent">{error}</p> : null}
      {loading ? <p className="mt-8 text-ink/60">Đang tải…</p> : (
        <div className="mt-6 overflow-x-auto rounded-3xl border border-ink/10 bg-white/70">
          <table className="min-w-full text-left text-sm"><thead className="border-b border-ink/10 text-ink/55"><tr><th className="p-4">Đơn hàng</th><th className="p-4">Khách hàng</th><th className="p-4">Tổng tiền</th><th className="p-4">Trạng thái</th><th className="p-4"></th></tr></thead><tbody className="divide-y divide-ink/10">{orders.map((order) => <tr key={order.order_number}><td className="p-4"><Link className="font-medium hover:text-accent" href={`/admin/orders/${order.order_number}`}>{order.order_number}</Link><p className="text-xs text-ink/50">{new Date(order.created_at).toLocaleString("vi-VN")} · {order.item_count} món</p></td><td className="p-4">{order.customer_name}<p className="text-xs text-ink/50">{order.customer_email}</p></td><td className="p-4 font-medium">{formatVnd(order.total_vnd)}</td><td className="p-4">{labels[order.status] ?? order.status}</td><td className="p-4 text-right">{order.status === "paid" ? <button className="rounded-full bg-ink px-4 py-2 text-xs text-paper disabled:opacity-50" disabled={busyOrder === order.order_number} onClick={() => complete(order.order_number)} type="button">{busyOrder === order.order_number ? "Đang xử lý…" : "Hoàn tất"}</button> : null}</td></tr>)}</tbody></table>
          {orders.length === 0 ? <p className="p-8 text-center text-ink/55">Không có đơn hàng phù hợp.</p> : null}
        </div>
      )}
    </section>
  );
}

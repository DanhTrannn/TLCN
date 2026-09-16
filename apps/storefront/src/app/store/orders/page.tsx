"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/api";
import { formatVietnamDateTime } from "@/lib/datetime";
import { OrderStatusBadge } from "@/components/OrderStatusBadge";

interface StoreOrder {
  order_number: string;
  customer_name: string;
  status: string;
  total_vnd: number;
  item_count: number;
  channel: string;
  created_at: string;
}

export default function StoreOrdersPage() {
  const [orders, setOrders] = useState<StoreOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");

  useEffect(() => {
    const params = new URLSearchParams();
    if (statusFilter) params.set("status", statusFilter);
    apiFetch<StoreOrder[]>(`/api/v1/admin/store/orders?${params}`)
      .then(setOrders)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [statusFilter]);

  return (
    <div>
      <h1 className="admin-heading">Đơn hàng cửa hàng</h1>

      <div className="mt-4 flex flex-wrap gap-2">
        {["", "paid", "confirmed", "completed", "cancelled"].map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setLoading(true); }}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
              statusFilter === s ? "bg-ink text-paper" : "bg-surface text-muted hover:text-ink"
            }`}
          >
            {s || "Tất cả"}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="admin-panel mt-4 animate-pulse text-muted">Đang tải…</div>
      ) : orders.length === 0 ? (
        <div className="admin-panel mt-4 text-muted">Chưa có đơn hàng.</div>
      ) : (
        <div className="mt-4 space-y-3">
          {orders.map((order) => (
            <Link
              key={order.order_number}
              href={`/store/orders/${order.order_number}`}
              className="admin-row flex items-center justify-between gap-4"
            >
              <div className="min-w-0">
                <p className="text-sm font-semibold text-ink">#{order.order_number}</p>
                <p className="text-xs text-muted">{order.customer_name}</p>
              </div>
              <div className="flex items-center gap-3">
                <OrderStatusBadge status={order.status} />
                <span className="text-sm font-semibold text-ink whitespace-nowrap">{formatVnd(order.total_vnd)}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

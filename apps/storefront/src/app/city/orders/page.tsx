"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { OrderStatusBadge } from "@/components/OrderStatusBadge";
import { Icon } from "@/components/ui/Icon";
import { apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/api";
import { formatVietnamDateTime } from "@/lib/datetime";

interface CityOrder {
  order_number: string;
  store_name: string;
  customer_name: string;
  status: string;
  total_vnd: number;
  item_count: number;
  channel: string;
  created_at: string;
}

const STATUS_FILTERS = [
  { value: "", label: "Tất cả" },
  { value: "paid", label: "Chờ xác nhận" },
  { value: "confirmed", label: "Đã xác nhận" },
  { value: "completed", label: "Hoàn tất" },
  { value: "cancelled", label: "Đã hủy" },
];

export default function CityOrdersPage() {
  const [orders, setOrders] = useState<CityOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      const data = await apiFetch<CityOrder[]>(`/api/v1/admin/city/orders?${params}`);
      setOrders(data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { void load(); }, [load]);

  return (
    <section>
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Order operations</p>
          <h1 className="admin-heading mt-2">Đơn hàng thành phố</h1>
          <p className="mt-2 text-sm leading-6 text-muted">Xem đơn hàng từ tất cả cửa hàng trong thành phố.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => { setStatusFilter(f.value); }}
              className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                statusFilter === f.value ? "bg-ink text-paper" : "bg-surface text-muted hover:text-ink"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </header>

      {loading ? (
        <div className="mt-6 h-72 animate-pulse rounded-2xl bg-sand/60" />
      ) : (
        <div className="admin-table-shell mt-6">
          <table>
            <thead>
              <tr>
                <th>Đơn hàng</th>
                <th>Khách hàng</th>
                <th>Cửa hàng</th>
                <th>Kênh</th>
                <th>Tổng tiền</th>
                <th>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.order_number}>
                  <td>
                    <p className="font-semibold">#{order.order_number}</p>
                    <p className="mt-1 text-xs text-muted">{formatVietnamDateTime(order.created_at)} · {order.item_count} món</p>
                  </td>
                  <td>
                    <p className="font-medium">{order.customer_name}</p>
                  </td>
                  <td>
                    <p className="text-sm">{order.store_name}</p>
                  </td>
                  <td>
                    <span
                      className={`inline-flex w-fit items-center rounded-full border px-3 py-1 text-xs font-semibold ${
                        order.channel === "pos"
                          ? "border-accent/25 bg-accent/10 text-accent"
                          : "border-line bg-paper text-muted"
                      }`}
                    >
                      {order.channel === "pos" ? "POS" : "Online"}
                    </span>
                  </td>
                  <td className="font-semibold">{formatVnd(order.total_vnd)}</td>
                  <td><OrderStatusBadge status={order.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          {orders.length === 0 && (
            <div className="p-10 text-center">
              <Icon className="mx-auto text-moss" name="receipt" size={24} />
              <p className="mt-3 text-muted">Không có đơn hàng phù hợp.</p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/api";

interface DashboardData {
  city_name: string;
  total_stores: number;
  active_stores: number;
  total_orders: number;
  completed_orders: number;
  total_revenue_vnd: number;
  total_staff: number;
  low_stock_items: number;
}

export default function CityDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<DashboardData>("/admin/city/dashboard")
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="admin-panel animate-pulse text-muted">Đang tải…</div>;
  }

  if (!data) {
    return <div className="admin-panel text-muted">Không thể tải dữ liệu.</div>;
  }

  const stats = [
    { label: "Tổng cửa hàng", value: data.total_stores, icon: "store" as const },
    { label: "Cửa hàng hoạt động", value: data.active_stores, icon: "check" as const },
    { label: "Tổng đơn hàng", value: data.total_orders, icon: "receipt" as const },
    { label: "Đơn hoàn thành", value: data.completed_orders, icon: "check" as const },
    { label: "Tổng doanh thu", value: formatVnd(data.total_revenue_vnd), icon: "sparkles" as const },
    { label: "Nhân viên", value: data.total_staff, icon: "users" as const },
    { label: "Tồn kho thấp", value: data.low_stock_items, icon: "alert" as const },
  ];

  return (
    <div>
      <h1 className="admin-heading">Tổng quan thành phố</h1>
      <p className="mt-1 text-sm text-muted">{data.city_name}</p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat) => (
          <div key={stat.label} className="surface-card p-5">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">{stat.label}</p>
            <p className="mt-2 text-2xl font-bold text-ink">{stat.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

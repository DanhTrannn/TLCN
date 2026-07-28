"use client";

import { useEffect, useState } from "react";

import { ApiError, formatVnd, getAdminOverview, type AdminOverview } from "@/lib/api";

const cards: Array<[keyof AdminOverview, string, (value: number) => string]> = [
  ["active_products", "Sản phẩm đang bán", String],
  ["active_variants", "Biến thể đang bán", String],
  ["low_stock_variants", "Biến thể sắp hết", String],
  ["customers", "Khách hàng", String],
  ["paid_orders", "Đơn đã thanh toán", String],
  ["recognized_revenue_vnd", "Doanh thu ghi nhận", formatVnd],
];

export default function AdminOverviewPage() {
  const [data, setData] = useState<AdminOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAdminOverview()
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Không tải được tổng quan"));
  }, []);

  if (error) return <p className="text-accent">{error}</p>;
  if (!data) return <p className="text-ink/60">Đang tải dữ liệu…</p>;

  return (
    <section>
      <h2 className="text-xl font-semibold">Tình trạng vận hành</h2>
      <p className="mt-1 text-sm text-ink/60">Số liệu trực tiếp từ OLTP, chỉ dùng cho vận hành nhẹ.</p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map(([key, label, formatter]) => (
          <article className="rounded-3xl border border-ink/10 bg-white/70 p-6" key={key}>
            <p className="text-sm text-ink/60">{label}</p>
            <p className="mt-3 text-3xl font-semibold">{formatter(data[key])}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
